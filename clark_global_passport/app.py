from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, make_response, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text as sql_text
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from html.parser import HTMLParser
import csv
import io
import os

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-me")
database_url = os.environ.get("DATABASE_URL", "sqlite:///clark_global_passport.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

COMPETENCIES = [
    "Academic English",
    "Communication",
    "Critical Thinking",
    "Research",
    "Self-Management",
    "Global Awareness",
]

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    first_name = db.Column(db.String(80), nullable=True)
    last_name = db.Column(db.String(80), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")
    year_level = db.Column(db.Integer, nullable=True)
    is_transfer = db.Column(db.Boolean, default=False)
    account_status = db.Column(db.String(30), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    adviser_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    reflections = db.relationship("Reflection", backref="student", lazy=True, cascade="all, delete-orphan")
    projects = db.relationship("Project", backref="student", lazy=True, cascade="all, delete-orphan")
    portfolio_items = db.relationship("PortfolioItem", backref="student", lazy=True, cascade="all, delete-orphan")
    future_goals = db.relationship("FutureGoal", backref="student", lazy=True, cascade="all, delete-orphan")
    competency_scores = db.relationship("CompetencyScore", backref="student", lazy=True, cascade="all, delete-orphan")

class StudentAcademicProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False)
    eiken_level = db.Column(db.String(30), default="")
    student_number = db.Column(db.String(50), default="")
    homeroom = db.Column(db.String(80), default="")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CompetencyScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    competency = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Integer, default=1)

class Reflection(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(180), nullable=False)
    experience = db.Column(db.Text, nullable=False)
    contribution = db.Column(db.Text, nullable=False)
    challenge = db.Column(db.Text, nullable=False)
    learning = db.Column(db.Text, nullable=False)
    next_step = db.Column(db.Text, nullable=False)
    competency = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(180), nullable=False)
    question = db.Column(db.Text, nullable=False)
    stage = db.Column(db.String(50), default="Question")
    description = db.Column(db.Text, default="")
    next_action = db.Column(db.Text, default="")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class PortfolioItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(180), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    evidence = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



class EssayWorkshopProgress(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    workshop_key = db.Column(db.String(80), nullable=False)
    content = db.Column(db.Text, default="")
    completed = db.Column(db.Boolean, default=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.UniqueConstraint("student_id", "workshop_key",
                            name="uq_essay_workshop_student_key"),
    )


class EssaySubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    stage = db.Column(db.String(80), nullable=False)
    title = db.Column(db.String(180), nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(40), default="Pending Review")
    version = db.Column(db.Integer, default=1)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

class EssayFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    submission_id = db.Column(db.Integer, db.ForeignKey("essay_submission.id"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    decision = db.Column(db.String(40), default="Comment")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ConsultationEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    adviser_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    consultation_date = db.Column(db.String(30), default="")
    topic = db.Column(db.String(160), nullable=False)
    discussion = db.Column(db.Text, nullable=False)
    action_items = db.Column(db.Text, default="")
    next_meeting = db.Column(db.String(30), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Year3Milestone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    milestone = db.Column(db.String(160), nullable=False)
    status = db.Column(db.String(30), default="Not Started")
    note = db.Column(db.Text, default="")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DETRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    record_type = db.Column(db.String(30), nullable=False, default="practice")
    score = db.Column(db.Integer, nullable=True)
    literacy = db.Column(db.Integer, nullable=True)
    comprehension = db.Column(db.Integer, nullable=True)
    conversation = db.Column(db.Integer, nullable=True)
    production = db.Column(db.Integer, nullable=True)
    reflection = db.Column(db.Text, default="")
    test_date = db.Column(db.String(30), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class UniversityOption(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    university = db.Column(db.String(200), nullable=False)
    country = db.Column(db.String(100), default="")
    program = db.Column(db.String(200), default="")
    deadline = db.Column(db.String(50), default="")
    det_requirement = db.Column(db.String(50), default="")
    tuition_note = db.Column(db.String(120), default="")
    status = db.Column(db.String(50), default="Researching")
    fit_reason = db.Column(db.Text, default="")
    applied = db.Column(db.Boolean, default=False)
    submitted_date = db.Column(db.String(50), default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)




class PromotionRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    current_year = db.Column(db.Integer, nullable=False)
    requested_year = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text, default="")
    status = db.Column(db.String(30), default="Pending")
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    teacher_comment = db.Column(db.Text, default="")

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    activity_type = db.Column(db.String(80), nullable=False)
    title = db.Column(db.String(220), nullable=False)
    detail = db.Column(db.Text, default="")
    icon = db.Column(db.String(10), default="🔔")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class YearMilestone(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    year_level = db.Column(db.Integer, nullable=False)
    milestone_key = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="not_started")
    completed_at = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint("student_id", "year_level", "milestone_key",
                                          name="uq_year_milestone_student_year_key"),)


class SystemMigration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(120), unique=True, nullable=False)
    applied_at = db.Column(db.DateTime, default=datetime.utcnow)

class AdminAuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    actor_name = db.Column(db.String(120), default="")
    action = db.Column(db.String(80), nullable=False)
    target_name = db.Column(db.String(120), default="")
    target_email = db.Column(db.String(120), default="")
    detail = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TeacherNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category = db.Column(db.String(80), default="General")
    note = db.Column(db.Text, nullable=False)
    next_goal = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class FutureGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    university_interest = db.Column(db.String(200), default="")
    field_interest = db.Column(db.String(200), default="")
    career_interest = db.Column(db.String(200), default="")
    personal_statement_ideas = db.Column(db.Text, default="")
    next_step = db.Column(db.Text, default="")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)



EIKEN_LEVELS = [
    "",
    "5",
    "4",
    "3",
    "Pre-2",
    "Pre-2 Plus",
    "2",
    "Pre-1",
    "1",
]

def get_academic_profile(student_id):
    profile = StudentAcademicProfile.query.filter_by(student_id=student_id).first()
    if not profile:
        profile = StudentAcademicProfile(student_id=student_id)
        db.session.add(profile)
        db.session.flush()
    return profile

def student_last_activity(student_id):
    return ActivityLog.query.filter_by(student_id=student_id).order_by(ActivityLog.created_at.desc()).first()

ESSAY_STAGES = [
    "Story Bank",
    "Choose One Story",
    "Build the Core",
    "Draft 1",
    "Draft 2",
    "Polished Version",
    "Final Version",
]

YEAR3_MILESTONES = [
    "Final university list confirmed",
    "Official DET score recorded",
    "Final personal essay approved",
    "Transcripts / school documents prepared",
    "Recommendation letters requested",
    "Application forms in progress",
    "At least one overseas application submitted",
    "Interview / scholarship / visa preparation",
]

def get_essay_stage_state(student_id):
    submissions = EssaySubmission.query.filter_by(student_id=student_id).order_by(
        EssaySubmission.submitted_at.asc()
    ).all()

    latest_by_stage = {}
    for item in submissions:
        latest_by_stage[item.stage] = item

    unlocked_index = 0
    for i, stage in enumerate(ESSAY_STAGES):
        latest = latest_by_stage.get(stage)
        if latest and latest.status == "Approved":
            unlocked_index = min(i + 1, len(ESSAY_STAGES) - 1)
            continue
        unlocked_index = i
        break
    else:
        unlocked_index = len(ESSAY_STAGES) - 1

    # If every stage is approved, keep Final Version as the displayed current stage.
    all_approved = all(
        latest_by_stage.get(stage) and latest_by_stage[stage].status == "Approved"
        for stage in ESSAY_STAGES
    )
    if all_approved:
        unlocked_index = len(ESSAY_STAGES) - 1

    return submissions, latest_by_stage, unlocked_index, all_approved

def ensure_year3_milestones(student_id):
    existing = {m.milestone for m in Year3Milestone.query.filter_by(student_id=student_id).all()}
    changed = False
    for name in YEAR3_MILESTONES:
        if name not in existing:
            db.session.add(Year3Milestone(student_id=student_id, milestone=name))
            changed = True
    if changed:
        db.session.commit()
    return Year3Milestone.query.filter_by(student_id=student_id).order_by(Year3Milestone.id.asc()).all()

class RichTextSanitizer(HTMLParser):
    allowed_tags = {"p", "br", "strong", "b", "em", "i", "u", "ul", "ol", "li", "blockquote", "h2", "h3", "div"}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
    def handle_starttag(self, tag, attrs):
        if tag in self.allowed_tags:
            self.parts.append(f"<{tag}>")
    def handle_endtag(self, tag):
        if tag in self.allowed_tags and tag != "br":
            self.parts.append(f"</{tag}>")
    def handle_data(self, data):
        from markupsafe import escape
        self.parts.append(str(escape(data)))
    def get_html(self):
        return "".join(self.parts)

def sanitize_rich_text(value):
    sanitizer = RichTextSanitizer()
    sanitizer.feed(value or "")
    return sanitizer.get_html().strip()

ESSAY_WRITESHOPS = [
    {
        "key": "hooks",
        "number": 1,
        "title": "Writing Effective Hooks",
        "subtitle": "Start with curiosity, not drama.",
        "en": [
            "A hook is the opening line of your essay. Its job is not to sound dramatic. Its job is to make the reader curious enough to continue.",
            "Strong hooks are usually specific. They can begin with a small moment, an unusual detail, a surprising contrast, or a line of dialogue that leads naturally into your story.",
            "Avoid very broad openings such as “Everyone has challenges in life.” A personal essay becomes memorable when the first line already sounds like it belongs to you."
        ],
        "ja": [
            "フック（hook）とは、エッセイの最初の一文です。大げさに書くことが目的ではなく、読み手に「この先を読みたい」と思わせることが目的です。",
            "効果的なフックは、具体的であることが多いです。小さな出来事、印象的な細部、意外な対比、会話の一言などから始めることができます。",
            "「人生には誰にでも困難があります」のような一般的すぎる書き出しは避けましょう。最初の一文から、あなた自身の声が感じられることが大切です。"
        ],
        "example_weak": "Everyone has challenges in life.",
        "example_strong": "I was eleven when I learned that being the loudest person in the room did not mean I was the most confident.",
        "prompt": "Write three possible hooks for one experience from your Story Bank. Then choose the strongest one and explain why it makes you want to keep reading."
    },
    {
        "key": "introductions",
        "number": 2,
        "title": "Building a Strong Introduction",
        "subtitle": "Give the reader a clear doorway into your story.",
        "en": [
            "An introduction should do more than introduce a topic. It should place the reader inside a situation and establish what matters.",
            "After your hook, give just enough context to understand the moment. Do not explain your entire life story at once. Let the essay unfold.",
            "By the end of the introduction, the reader should sense the question, tension, change, or idea that the essay will explore."
        ],
        "ja": [
            "導入部分は、単にテーマを紹介するだけではありません。読み手を具体的な場面に入れ、その経験の何が重要なのかを示します。",
            "フックの後には、その場面を理解するために必要な情報だけを加えましょう。最初から人生全体を説明する必要はありません。",
            "導入の終わりまでに、このエッセイがどんな問い・葛藤・変化・考えを扱うのかが自然に伝わると効果的です。"
        ],
        "example_weak": "This essay is about my experience joining a club.",
        "example_strong": "On my first day in the debate room, I wrote my opening sentence three times and still could not make myself stand up.",
        "prompt": "Write a 3–5 sentence introduction that begins with a hook, gives necessary context, and hints at what changed or mattered."
    },
    {
        "key": "specific_details",
        "number": 3,
        "title": "Show, Don’t Just Tell",
        "subtitle": "Turn general statements into scenes the reader can picture.",
        "en": [
            "Personal essays become stronger when the reader can see what happened. Instead of only naming an emotion, show the actions, details, or thoughts that reveal it.",
            "Specific details do not need to be long. One precise detail can be more powerful than several vague sentences.",
            "Choose details that support the meaning of the story. Description should serve the essay, not decorate it."
        ],
        "ja": [
            "パーソナルエッセイでは、読み手が出来事を想像できるように書くことが大切です。感情を言葉で説明するだけでなく、その感情が伝わる行動・細部・考えを示しましょう。",
            "具体的な描写は長くなくても構いません。一つの正確な細部が、何文もの曖昧な説明より強く伝わることがあります。",
            "描写は飾りではなく、物語の意味を支えるために使いましょう。"
        ],
        "example_weak": "I was very nervous before the presentation.",
        "example_strong": "I kept folding the corner of my cue card until the paper had turned soft between my fingers.",
        "prompt": "Choose one general sentence from your story and rewrite it using actions, sensory details, thoughts, or dialogue."
    },
    {
        "key": "examples",
        "number": 4,
        "title": "Using Specific Examples",
        "subtitle": "Prove your point through one meaningful experience.",
        "en": [
            "A strong personal essay does not simply claim that you are hardworking, curious, kind, or resilient. It gives the reader evidence.",
            "Choose one or two experiences that reveal the quality naturally. Explain what you did, what was difficult, and what happened because of your choices.",
            "The example should move the essay forward instead of becoming a list of achievements."
        ],
        "ja": [
            "良いパーソナルエッセイは、「私は努力家です」「好奇心があります」と主張するだけではありません。そのことが伝わる具体的な経験を示します。",
            "一つか二つの経験を選び、何をしたのか、何が難しかったのか、自分の行動によって何が起きたのかを書きましょう。",
            "実績の羅列ではなく、エッセイの流れや意味を深める例にすることが大切です。"
        ],
        "example_weak": "I am a good leader because I joined many activities.",
        "example_strong": "When two members stopped speaking during our project, I changed our weekly meeting into ten-minute individual check-ins before asking the group to decide together.",
        "prompt": "Write one paragraph using a specific experience as evidence for a quality, value, or skill you want the reader to understand about you."
    },
    {
        "key": "reflection",
        "number": 5,
        "title": "Reflection & Meaning",
        "subtitle": "Explain why the experience matters now.",
        "en": [
            "Reflection is what turns a story into a personal essay. After describing what happened, ask what you understood differently because of it.",
            "Avoid ending reflection with only “I learned to never give up.” Push one step further: What changed in how you think, act, choose, or understand other people?",
            "Good reflection connects the past experience to the person you are becoming."
        ],
        "ja": [
            "振り返り（reflection）は、単なる出来事の説明をパーソナルエッセイに変える重要な部分です。経験の後、自分の考え方がどう変わったのかを考えましょう。",
            "「諦めないことを学びました」だけで終わらせず、考え方・行動・選択・他者への理解が具体的にどう変わったのかまで掘り下げます。",
            "良い振り返りは、過去の経験と、今の自分・これからの自分をつなげます。"
        ],
        "example_weak": "This experience taught me to be confident.",
        "example_strong": "I still get nervous before speaking, but I no longer treat nervousness as proof that I am unprepared. Now I see it as evidence that the moment matters to me.",
        "prompt": "Write 4–6 sentences explaining what your experience changed in the way you think, act, or understand yourself."
    },
    {
        "key": "transitions",
        "number": 6,
        "title": "Connecting Ideas",
        "subtitle": "Help the reader follow your thinking.",
        "en": [
            "Transitions are not only words such as however, therefore, or furthermore. A good transition shows how one idea grows from the previous one.",
            "Repeat a key image, question, or idea when useful. You can also use time, contrast, cause and effect, or a change in perspective to move between paragraphs.",
            "The goal is for the essay to feel like one developing thought rather than separate blocks."
        ],
        "ja": [
            "トランジション（つなぎ）は、however や therefore のような接続語だけではありません。前の考えから次の考えへ、どのようにつながっているかを示すことが大切です。",
            "必要に応じて、重要なイメージ・問い・キーワードを繰り返したり、時間の変化、対比、原因と結果、視点の変化を使ったりできます。",
            "段落がバラバラに見えるのではなく、一つの考えが発展していくように読めることが目標です。"
        ],
        "example_weak": "Furthermore, I learned another important lesson.",
        "example_strong": "The same silence that frightened me in the debate room later became the space I learned to use before answering.",
        "prompt": "Write two connected paragraphs. Make the second paragraph feel like a natural continuation rather than a completely new topic."
    },
    {
        "key": "conclusions",
        "number": 7,
        "title": "Writing Strong Conclusions",
        "subtitle": "End with movement, not a summary.",
        "en": [
            "A conclusion should not simply repeat the introduction. It should show where the experience has taken you.",
            "Return to an image, question, or idea from earlier in the essay, but let it mean something new after everything the reader has learned.",
            "A strong ending can point toward the future without making an exaggerated promise about changing the world."
        ],
        "ja": [
            "結論では、導入をそのまま繰り返す必要はありません。その経験によって自分がどこまで進んだのかを示しましょう。",
            "エッセイの前半に出てきたイメージ・問い・考えに戻り、読み手がここまで読んだからこそ新しい意味を感じられる形にすると効果的です。",
            "将来につなげることもできますが、「世界を変えたい」のような大げさな約束をする必要はありません。"
        ],
        "example_weak": "In conclusion, this experience made me who I am today.",
        "example_strong": "I still keep that creased cue card in my desk—not because the speech was perfect, but because it was the first time I stood up before I felt ready.",
        "prompt": "Write two possible conclusions for your story. Try one that returns to an image from the beginning and one that looks forward."
    },
    {
        "key": "editing",
        "number": 8,
        "title": "Editing & Polishing",
        "subtitle": "Make every sentence earn its place.",
        "en": [
            "Editing is more than fixing grammar. First revise for meaning: Is the story clear? Is every paragraph necessary? Does the reflection go deep enough?",
            "Then revise sentences. Remove repeated ideas, vague words, and unnecessary introductions such as “I think that.” Choose verbs and details that are precise.",
            "Finally, proofread grammar, spelling, punctuation, and formatting. Reading the essay aloud often reveals awkward sentences."
        ],
        "ja": [
            "編集（editing）は文法ミスを直すだけではありません。まず内容を見直します。物語は分かりやすいか、各段落は必要か、振り返りは十分に深いかを確認しましょう。",
            "次に文を整えます。重複した考え、曖昧な表現、「I think that」のような不要な前置きを減らし、より正確な動詞や細部を選びます。",
            "最後に文法・スペル・句読点・形式を確認します。声に出して読むと、不自然な文に気づきやすくなります。"
        ],
        "example_weak": "I really truly realized that this was actually very important to me.",
        "example_strong": "I realized why the moment mattered to me.",
        "prompt": "Paste or write one paragraph from your essay. Revise it for clarity, precision, and unnecessary words."
    },
]

def get_writeshop(key):
    return next((item for item in ESSAY_WRITESHOPS if item["key"] == key), None)

def sync_essay_training_milestone(student):
    if not student or student.role != "student":
        return
    ensure_year_milestones(student)
    required = {w["key"] for w in ESSAY_WRITESHOPS}
    completed = {
        row.workshop_key for row in EssayWorkshopProgress.query.filter_by(
            student_id=student.id, completed=True
        ).all()
    }
    milestone = YearMilestone.query.filter_by(
        student_id=student.id, year_level=1, milestone_key="essay_training"
    ).first()
    if milestone:
        milestone.status = "complete" if required.issubset(completed) else (
            "in_progress" if completed else "not_started"
        )
        milestone.completed_at = datetime.utcnow() if milestone.status == "complete" else None
        db.session.commit()


YEAR_PATHWAYS = {
    1: {
        "label": "FOUNDATION",
        "title": "Build Your Story & English",
        "mission": "Learn how to express who you are while building the English skills needed for overseas university study.",
        "goal": "Finish a strong first personal essay draft and build a DET study routine.",
        "steps": [
            {"key": "identity", "title": "Discover Your Story", "icon": "01", "desc": "Identify experiences, values, challenges, and interests that make you unique.", "action": "Write your Story Bank"},
            {"key": "essay_basics", "title": "Learn Essay Basics", "icon": "02", "desc": "Practice hooks, structure, examples, reflection, and clear endings.", "action": "Complete Essay Training"},
            {"key": "first_draft", "title": "Write Your First Draft", "icon": "03", "desc": "Turn one meaningful experience into a university-style personal essay.", "action": "Create Draft 1"},
            {"key": "det_start", "title": "Start DET Training", "icon": "04", "desc": "Learn the Duolingo English Test format and identify your current strengths and weaknesses.", "action": "Start DET Prep"},
            {"key": "routine", "title": "Build Your Routine", "icon": "05", "desc": "Set weekly English targets for reading, listening, speaking, and writing.", "action": "Set Weekly Goals"},
        ],
    },
    2: {
        "label": "PREPARATION",
        "title": "Test, Polish & Explore",
        "mission": "Turn your foundation into evidence: take the DET, polish your essay, and discover universities that fit you.",
        "goal": "Take the DET, complete a polished essay, and create a university shortlist.",
        "steps": [
            {"key": "det_ready", "title": "DET Readiness", "icon": "01", "desc": "Use practice results to decide when you are ready for the real test.", "action": "Check Readiness"},
            {"key": "det_take", "title": "Take the DET", "icon": "02", "desc": "Take the official Duolingo English Test and record your result.", "action": "Record DET Score"},
            {"key": "essay_polish", "title": "Polish Your Essay", "icon": "03", "desc": "Revise your Year 1 draft for clarity, voice, evidence, and stronger reflection.", "action": "Build Final Essay"},
            {"key": "uni_research", "title": "Explore Universities", "icon": "04", "desc": "Compare countries, majors, tuition, entry requirements, and student life.", "action": "Research Universities"},
            {"key": "shortlist", "title": "Create Your Shortlist", "icon": "05", "desc": "Choose realistic universities you could seriously apply to in Year 3.", "action": "Build My Shortlist"},
        ],
    },
    3: {
        "label": "APPLICATION",
        "title": "Apply & Move Forward",
        "mission": "Turn your preparation into real applications and take the next step beyond Clark.",
        "goal": "Submit at least one overseas university application.",
        "steps": [
            {"key": "final_list", "title": "Confirm Your Universities", "icon": "01", "desc": "Choose your final application destinations and check every requirement.", "action": "Confirm List"},
            {"key": "requirements", "title": "Prepare Documents", "icon": "02", "desc": "Track essays, transcripts, recommendations, test scores, and deadlines.", "action": "Check Requirements"},
            {"key": "application", "title": "Build Applications", "icon": "03", "desc": "Complete each application carefully and keep evidence of progress.", "action": "Start Applying"},
            {"key": "submit", "title": "Submit Overseas", "icon": "04", "desc": "Reach the Clark International Course goal: at least one overseas university application.", "action": "Record Submission"},
            {"key": "next", "title": "Prepare for What Comes Next", "icon": "05", "desc": "Plan interviews, offers, scholarships, visas, and your transition after graduation.", "action": "Plan Next Steps"},
        ],
    },
}

def get_year_pathway(year_level):
    return YEAR_PATHWAYS.get(year_level, YEAR_PATHWAYS[1])


def log_activity(student_id, activity_type, title, detail="", icon="🔔", actor_id=None):
    entry = ActivityLog(
        student_id=student_id,
        actor_id=actor_id,
        activity_type=activity_type,
        title=title,
        detail=detail,
        icon=icon,
    )
    db.session.add(entry)

def current_user():
    if "user_id" not in session:
        return None
    return db.session.get(User, session["user_id"])

def require_login():
    if not current_user():
        return redirect(url_for("login"))

def get_scores(student):
    scores = {c: 1 for c in COMPETENCIES}
    for row in student.competency_scores:
        scores[row.competency] = row.score
    return scores

@app.context_processor
def inject_globals():
    return {
        "current_user": current_user(),
        "COMPETENCIES": COMPETENCIES
    }



@app.route("/sw.js")
def service_worker():
    response = make_response(send_from_directory(app.static_folder, "sw.js"))
    response.headers["Content-Type"] = "application/javascript"
    response.headers["Service-Worker-Allowed"] = "/"
    response.headers["Cache-Control"] = "no-cache"
    return response

@app.route("/offline")
def offline():
    return render_template("offline.html")

@app.route("/health")
def health():
    return {"status": "ok"}, 200

@app.route("/")
def index():
    if current_user():
        if current_user().role == "teacher":
            return redirect(url_for("teacher_dashboard"))
        return redirect(url_for("student_dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        name = f"{first_name} {last_name}".strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role", "student")
        is_transfer = request.form.get("is_transfer") == "on"

        if not first_name or not last_name or not email or not password:
            flash("Please complete all required fields.", "error")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("register"))

        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "error")
            return redirect(url_for("register"))

        if role not in ["student", "teacher"]:
            flash("Invalid account type.", "error")
            return redirect(url_for("register"))

        if role == "student":
            try:
                year_level = int(request.form.get("year_level", "1"))
            except ValueError:
                year_level = 1

            if year_level not in [1, 2, 3]:
                year_level = 1

            account_status = "active"
        else:
            year_level = None
            is_transfer = False
            # The first teacher can bootstrap a fresh installation.
            # Later teacher accounts require approval from an active teacher.
            active_teacher_exists = User.query.filter_by(role="teacher", account_status="active").first() is not None
            account_status = "pending" if active_teacher_exists else "active"

        new_user = User(
            name=name,
            first_name=first_name,
            last_name=last_name,
            email=email,
            role=role,
            year_level=year_level,
            is_transfer=is_transfer,
            account_status=account_status,
        )
        new_user.password_hash = generate_password_hash(password)
        db.session.add(new_user)
        db.session.flush()

        if role == "student":
            db.session.add(StudentAcademicProfile(student_id=new_user.id))
            for competency in COMPETENCIES:
                db.session.add(
                    CompetencyScore(
                        student_id=new_user.id,
                        competency=competency,
                        score=1,
                    )
                )
            log_activity(
                new_user.id,
                "Account Created",
                "Student account created",
                f"Joined as Year {year_level}" + (" • Transfer student" if is_transfer else ""),
                "👤",
                new_user.id,
            )

        db.session.commit()

        if role == "teacher":
            if account_status == "active":
                flash("Teacher account created. You can now sign in.", "success")
            else:
                flash("Teacher account created. An existing teacher must approve it before you can sign in.", "success")
        else:
            flash("Account created. You can now sign in.", "success")

        return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            if getattr(user, "account_status", "active") != "active":
                flash("Your account is waiting for teacher approval.", "error")
                return redirect(url_for("login"))
            session["user_id"] = user.id
            return redirect(url_for("index"))
        flash("Incorrect email or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/student")
def student_dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    if user.role != "student":
        return redirect(url_for("teacher_dashboard"))

    scores = get_scores(user)
    reflections = Reflection.query.filter_by(student_id=user.id).order_by(Reflection.created_at.desc()).limit(3).all()
    projects = Project.query.filter_by(student_id=user.id).order_by(Project.updated_at.desc()).all()
    portfolio_count = PortfolioItem.query.filter_by(student_id=user.id).count()
    pathway = get_year_pathway(user.year_level or 1)
    year_progress, carried_over_milestones, all_year_progress = build_year_progress(user)
    return render_template(
        "student_dashboard.html",
        student=user,
        year_progress=year_progress,
        carried_over_milestones=carried_over_milestones,
        all_year_progress=all_year_progress,
        scores=scores,
        reflections=reflections,
        projects=projects,
        portfolio_count=portfolio_count,
        pathway=pathway,
        pending_promotion=PromotionRequest.query.filter_by(student_id=user.id, status="Pending").first(),
        last_promotion=PromotionRequest.query.filter_by(student_id=user.id).order_by(PromotionRequest.requested_at.desc()).first(),
        adviser=db.session.get(User, user.adviser_id) if user.adviser_id else None,
        consultations=ConsultationEntry.query.filter_by(student_id=user.id).order_by(ConsultationEntry.created_at.desc()).limit(3).all() if user.year_level == 3 else [],
        milestones=ensure_year3_milestones(user.id) if user.year_level == 3 else [],
    )

@app.route("/teacher/student/<int:student_id>/year-progress/<int:year>/<milestone_key>", methods=["POST"])
def teacher_update_year_milestone(student_id, year, milestone_key):
    teacher = current_user()
    if not teacher or teacher.role != "teacher":
        return redirect(url_for("login"))

    student = User.query.filter_by(id=student_id, role="student").first_or_404()
    current_year = max(1, min(int(student.year_level or 1), 3))
    valid = YEAR_MILESTONE_DEFINITIONS.get(year)

    if not valid or year > current_year or milestone_key not in {k for k, _ in valid["milestones"]}:
        flash("That milestone is not available.", "error")
        return redirect(url_for("teacher_student", student_id=student.id))

    ensure_year_milestones(student)
    milestone = YearMilestone.query.filter_by(
        student_id=student.id,
        year_level=year,
        milestone_key=milestone_key
    ).first_or_404()

    status = request.form.get("status", "not_started")
    if status not in {"not_started", "in_progress", "complete"}:
        status = "not_started"

    milestone.status = status
    milestone.completed_at = datetime.utcnow() if status == "complete" else None
    milestone.updated_at = datetime.utcnow()
    db.session.commit()

    flash("Student year progress updated.", "success")
    return redirect(url_for("teacher_student", student_id=student.id))


@app.route("/reflections", methods=["GET", "POST"])
def reflections():
    user = current_user()
    if not user or user.role != "student":
        return redirect(url_for("login"))

    if request.method == "POST":
        reflection = Reflection(
            student_id=user.id,
            title=request.form["title"],
            experience=request.form["experience"],
            contribution=request.form["contribution"],
            challenge=request.form["challenge"],
            learning=request.form["learning"],
            next_step=request.form["next_step"],
            competency=request.form["competency"],
        )
        db.session.add(reflection)
        log_activity(
            user.id,
            "Reflection",
            reflection.title,
            f"New reflection • {reflection.competency}",
            "💭",
            user.id,
        )

        score = CompetencyScore.query.filter_by(
            student_id=user.id, competency=reflection.competency
        ).first()
        if not score:
            score = CompetencyScore(student_id=user.id, competency=reflection.competency, score=1)
            db.session.add(score)
        score.score = min(10, score.score + 1)

        db.session.commit()
        flash("Reflection saved. Your competency growth has been updated.", "success")
        return redirect(url_for("reflections"))

    items = Reflection.query.filter_by(student_id=user.id).order_by(Reflection.created_at.desc()).all()
    return render_template("reflections.html", items=items)

@app.route("/projects", methods=["GET", "POST"])
def projects():
    user = current_user()
    if not user or user.role != "student":
        return redirect(url_for("login"))

    if request.method == "POST":
        item = Project(
            student_id=user.id,
            title=request.form["title"],
            question=request.form["question"],
            stage=request.form["stage"],
            description=request.form["description"],
            next_action=request.form["next_action"],
        )
        db.session.add(item)
        log_activity(
            user.id,
            "Project",
            item.title,
            f"Started project • Stage: {item.stage}",
            "🧭",
            user.id,
        )
        db.session.commit()
        flash("Project added.", "success")
        return redirect(url_for("projects"))

    items = Project.query.filter_by(student_id=user.id).order_by(Project.updated_at.desc()).all()
    return render_template("projects.html", items=items)

@app.route("/projects/<int:project_id>/update", methods=["POST"])
def update_project(project_id):
    user = current_user()
    if not user or user.role != "student":
        return redirect(url_for("login"))

    item = Project.query.filter_by(id=project_id, student_id=user.id).first_or_404()
    old_stage = item.stage
    item.stage = request.form["stage"]
    item.description = request.form["description"]
    item.next_action = request.form["next_action"]
    detail = f"Stage: {old_stage} → {item.stage}" if old_stage != item.stage else f"Updated project details • Stage: {item.stage}"
    log_activity(user.id, "Project Updated", item.title, detail, "🧭", user.id)
    db.session.commit()
    flash("Project updated.", "success")
    return redirect(url_for("projects"))

@app.route("/portfolio", methods=["GET", "POST"])
def portfolio():
    user = current_user()
    if not user or user.role != "student":
        return redirect(url_for("login"))

    if request.method == "POST":
        item = PortfolioItem(
            student_id=user.id,
            title=request.form["title"],
            category=request.form["category"],
            description=request.form["description"],
            evidence=request.form["evidence"],
        )
        db.session.add(item)
        log_activity(
            user.id,
            "Portfolio",
            item.title,
            f"Added evidence • {item.category}",
            "📁",
            user.id,
        )
        db.session.commit()
        flash("Portfolio item added.", "success")
        return redirect(url_for("portfolio"))

    items = PortfolioItem.query.filter_by(student_id=user.id).order_by(PortfolioItem.created_at.desc()).all()
    return render_template("portfolio.html", items=items)

@app.route("/future", methods=["GET", "POST"])
def future():
    user = current_user()
    if not user or user.role != "student":
        return redirect(url_for("login"))

    goal = FutureGoal.query.filter_by(student_id=user.id).first()
    if request.method == "POST":
        if not goal:
            goal = FutureGoal(student_id=user.id)
            db.session.add(goal)
        goal.university_interest = request.form["university_interest"]
        goal.field_interest = request.form["field_interest"]
        goal.career_interest = request.form["career_interest"]
        goal.personal_statement_ideas = request.form["personal_statement_ideas"]
        goal.next_step = request.form["next_step"]
        log_activity(
            user.id,
            "Future Plan",
            "Updated future plan",
            goal.next_step or "University/career plan updated",
            "🎯",
            user.id,
        )
        db.session.commit()
        flash("Future plan saved.", "success")
        return redirect(url_for("future"))

    return render_template("future.html", goal=goal)



@app.route("/student/promotion-request", methods=["POST"])
def request_promotion():
    user = current_user()
    if not user or user.role != "student":
        return redirect(url_for("login"))

    if not user.year_level or user.year_level >= 3:
        flash("Year 3 is the highest year level in this pathway.", "error")
        return redirect(url_for("student_dashboard"))

    existing = PromotionRequest.query.filter_by(
        student_id=user.id,
        status="Pending"
    ).first()

    if existing:
        flash("You already have a pending promotion request.", "error")
        return redirect(url_for("student_dashboard"))

    req = PromotionRequest(
        student_id=user.id,
        current_year=user.year_level,
        requested_year=user.year_level + 1,
        reason=request.form.get("reason", "").strip(),
        status="Pending",
    )
    db.session.add(req)
    log_activity(
        user.id,
        "Promotion Request",
        f"Requested Year {user.year_level + 1}",
        f"Year {user.year_level} → Year {user.year_level + 1}",
        "⬆️",
        user.id,
    )
    db.session.commit()
    flash("Your promotion request was sent to the teachers.", "success")
    return redirect(url_for("student_dashboard"))

@app.route("/pathway")
def pathway():
    user = current_user()
    if not user or user.role != "student":
        return redirect(url_for("login"))
    return render_template("pathway.html", student=user, pathway=get_year_pathway(user.year_level or 1))

@app.route("/essay-writeshops")
def essay_writeshops():
    user = current_user()
    if not user or user.role != "student":
        return redirect(url_for("login"))

    progress_rows = EssayWorkshopProgress.query.filter_by(student_id=user.id).all()
    progress_map = {row.workshop_key: row for row in progress_rows}
    completed_count = sum(1 for row in progress_rows if row.completed)
    total = len(ESSAY_WRITESHOPS)
    percent = round(completed_count / total * 100) if total else 0

    return render_template(
        "essay_writeshops.html",
        workshops=ESSAY_WRITESHOPS,
        progress_map=progress_map,
        completed_count=completed_count,
        total=total,
        percent=percent,
    )

@app.route("/essay-writeshops/<workshop_key>", methods=["GET", "POST"])
def essay_writeshop(workshop_key):
    user = current_user()
    if not user or user.role != "student":
        return redirect(url_for("login"))

    workshop = get_writeshop(workshop_key)
    if not workshop:
        return redirect(url_for("essay_writeshops"))

    progress = EssayWorkshopProgress.query.filter_by(
        student_id=user.id, workshop_key=workshop_key
    ).first()
    if not progress:
        progress = EssayWorkshopProgress(student_id=user.id, workshop_key=workshop_key)
        db.session.add(progress)
        db.session.commit()

    if request.method == "POST":
        raw_content = request.form.get("content", "")
        clean_content = sanitize_rich_text(raw_content)
        action = request.form.get("action", "save")

        # Require actual writing before a workshop can be completed.
        plain_text = re.sub(r"<[^>]+>", " ", clean_content)
        plain_text = re.sub(r"\s+", " ", plain_text).strip()

        progress.content = clean_content
        progress.updated_at = datetime.utcnow()

        if action == "complete":
            if len(plain_text.split()) < 10:
                flash("Write a little more before marking this writeshop complete.", "error")
                db.session.commit()
                return redirect(url_for("essay_writeshop", workshop_key=workshop_key))
            progress.completed = True
            progress.completed_at = datetime.utcnow()
            log_activity(
                user.id,
                "Essay Writeshop",
                f"Completed: {workshop['title']}",
                "Independent essay training completed.",
                "📝",
                user.id,
            )
            flash("Writeshop completed.", "success")
        else:
            flash("Writeshop draft saved.", "success")

        db.session.commit()
        sync_essay_training_milestone(user)
        return redirect(url_for("essay_writeshop", workshop_key=workshop_key))

    return render_template(
        "essay_writeshop.html",
        workshop=workshop,
        progress=progress,
        workshops=ESSAY_WRITESHOPS,
    )


@app.route("/essay-lab", methods=["GET", "POST"])
def essay_lab():
    user = current_user()
    if not user or user.role != "student":
        return redirect(url_for("login"))

    submissions, latest_by_stage, unlocked_index, all_approved = get_essay_stage_state(user.id)
    current_stage = ESSAY_STAGES[unlocked_index]
    current_latest = latest_by_stage.get(current_stage)

    if request.method == "POST":
        stage = request.form.get("stage", current_stage)

        # Students may only work on the currently unlocked stage.
        if stage != current_stage:
            flash("That essay task is still locked. Complete the current task first.", "error")
            return redirect(url_for("essay_lab"))

        if current_latest and current_latest.status == "Pending Review":
            flash("This task is already waiting for teacher review.", "error")
            return redirect(url_for("essay_lab"))

        title = request.form.get("title", stage).strip() or stage
        content = sanitize_rich_text(request.form.get("content", ""))
        plain_content = re.sub(r"<[^>]+>", " ", content).strip()
        if not plain_content:
            flash("Please add your work before submitting.", "error")
            return redirect(url_for("essay_lab"))

        previous_versions = EssaySubmission.query.filter_by(
            student_id=user.id,
            stage=stage
        ).count()

        submission = EssaySubmission(
            student_id=user.id,
            stage=stage,
            title=title,
            content=content,
            status="Pending Review",
            version=previous_versions + 1,
        )
        db.session.add(submission)
        log_activity(
            user.id,
            "Essay Submitted",
            f"{stage} — Version {submission.version}",
            "Waiting for teacher review",
            "✍️",
            user.id,
        )
        db.session.commit()
        flash("Essay task submitted for teacher review.", "success")
        return redirect(url_for("essay_lab"))

    return render_template(
        "essay_lab.html",
        student=user,
        stages=ESSAY_STAGES,
        submissions=submissions,
        latest_by_stage=latest_by_stage,
        unlocked_index=unlocked_index,
        current_stage=current_stage,
        current_latest=current_latest,
        all_approved=all_approved,
    )

@app.route("/essay/submission/<int:submission_id>")
def essay_submission_view(submission_id):
    user = current_user()
    if not user:
        return redirect(url_for("login"))

    submission = EssaySubmission.query.get_or_404(submission_id)
    if user.role == "student" and submission.student_id != user.id:
        return redirect(url_for("student_dashboard"))

    student = db.session.get(User, submission.student_id)
    feedback = EssayFeedback.query.filter_by(submission_id=submission.id).order_by(EssayFeedback.created_at.asc()).all()
    return render_template(
        "essay_submission.html",
        submission=submission,
        student=student,
        feedback=feedback,
        viewer=user,
        display_content=sanitize_rich_text(submission.content),
    )

@app.route("/teacher/essay/<int:submission_id>/review", methods=["POST"])
def teacher_review_essay(submission_id):
    teacher = current_user()
    if not teacher or teacher.role != "teacher":
        return redirect(url_for("login"))

    submission = EssaySubmission.query.get_or_404(submission_id)
    student = db.session.get(User, submission.student_id)
    decision = request.form.get("decision", "Comment")
    comment = request.form.get("comment", "").strip()

    if not comment and decision in ["Approve", "Request Resubmission"]:
        flash("Please leave feedback with your decision.", "error")
        return redirect(url_for("essay_submission_view", submission_id=submission.id))

    feedback = EssayFeedback(
        submission_id=submission.id,
        teacher_id=teacher.id,
        comment=comment or "Teacher reviewed this submission.",
        decision=decision,
    )
    db.session.add(feedback)

    if decision == "Approve":
        submission.status = "Approved"
        submission.reviewed_at = datetime.utcnow()
        submission.reviewed_by = teacher.id
        activity_title = f"{submission.stage} approved"
        detail = "Next essay task unlocked."
        icon = "✅"
    elif decision == "Request Resubmission":
        submission.status = "Resubmission Requested"
        submission.reviewed_at = datetime.utcnow()
        submission.reviewed_by = teacher.id
        activity_title = f"Resubmission requested: {submission.stage}"
        detail = comment
        icon = "🔁"
    else:
        activity_title = f"Teacher feedback: {submission.stage}"
        detail = comment
        icon = "💬"

    log_activity(student.id, "Essay Review", activity_title, detail, icon, teacher.id)
    db.session.commit()
    flash("Essay feedback saved.", "success")
    return redirect(url_for("essay_submission_view", submission_id=submission.id))


@app.route("/det-prep", methods=["GET", "POST"])
def det_prep():
    user = current_user()
    if not user or user.role != "student":
        return redirect(url_for("login"))

    if request.method == "POST":
        def num(name):
            val = request.form.get(name, "").strip()
            return int(val) if val.isdigit() else None

        record = DETRecord(
            student_id=user.id,
            record_type=request.form.get("record_type", "practice"),
            score=num("score"),
            literacy=num("literacy"),
            comprehension=num("comprehension"),
            conversation=num("conversation"),
            production=num("production"),
            reflection=request.form.get("reflection", ""),
            test_date=request.form.get("test_date", ""),
        )
        db.session.add(record)
        score_text = record.score if record.score is not None else "—"
        log_activity(
            user.id,
            "DET",
            f"{record.record_type.title()} DET record",
            f"Score: {score_text}",
            "🎧",
            user.id,
        )
        db.session.commit()
        flash("DET progress saved.", "success")
        return redirect(url_for("det_prep"))

    records = DETRecord.query.filter_by(student_id=user.id).order_by(DETRecord.created_at.desc()).all()
    return render_template("det_prep.html", student=user, records=records)

@app.route("/universities", methods=["GET", "POST"])
def universities():
    user = current_user()
    if not user or user.role != "student":
        return redirect(url_for("login"))

    if request.method == "POST":
        item = UniversityOption(
            student_id=user.id,
            university=request.form["university"],
            country=request.form.get("country", ""),
            program=request.form.get("program", ""),
            deadline=request.form.get("deadline", ""),
            det_requirement=request.form.get("det_requirement", ""),
            tuition_note=request.form.get("tuition_note", ""),
            status=request.form.get("status", "Researching"),
            fit_reason=request.form.get("fit_reason", ""),
        )
        db.session.add(item)
        log_activity(
            user.id,
            "University",
            item.university,
            f"Added to university list • {item.status}",
            "🌍",
            user.id,
        )
        db.session.commit()
        flash("University added to your research list.", "success")
        return redirect(url_for("universities"))

    items = UniversityOption.query.filter_by(student_id=user.id).order_by(UniversityOption.created_at.desc()).all()
    return render_template("universities.html", student=user, items=items)


@app.route("/universities/<int:item_id>/update", methods=["POST"])
def update_university(item_id):
    user = current_user()
    if not user or user.role != "student":
        return redirect(url_for("login"))

    item = UniversityOption.query.filter_by(id=item_id, student_id=user.id).first_or_404()

    old_status = item.status
    old_deadline = item.deadline
    old_det = item.det_requirement
    old_program = item.program

    item.country = request.form.get("country", item.country)
    item.program = request.form.get("program", item.program)
    item.deadline = request.form.get("deadline", item.deadline)
    item.det_requirement = request.form.get("det_requirement", item.det_requirement)
    item.tuition_note = request.form.get("tuition_note", item.tuition_note)
    item.status = request.form.get("status", item.status)
    item.fit_reason = request.form.get("fit_reason", item.fit_reason)

    changes = []
    if old_status != item.status:
        changes.append(f"Status: {old_status} → {item.status}")
    if old_deadline != item.deadline:
        changes.append("Deadline updated")
    if old_det != item.det_requirement:
        changes.append("DET requirement updated")
    if old_program != item.program:
        changes.append("Program updated")

    detail = " • ".join(changes) if changes else "University details updated"

    log_activity(
        user.id,
        "University Updated",
        item.university,
        detail,
        "🌍",
        user.id,
    )

    db.session.commit()
    flash("University updated.", "success")
    return redirect(url_for("universities"))

@app.route("/universities/<int:item_id>/apply", methods=["POST"])
def mark_applied(item_id):
    user = current_user()
    if not user or user.role != "student":
        return redirect(url_for("login"))

    item = UniversityOption.query.filter_by(id=item_id, student_id=user.id).first_or_404()
    old_status = item.status
    item.applied = True
    item.status = "Submitted"
    item.submitted_date = request.form.get("submitted_date", "")
    log_activity(
        user.id,
        "Application Submitted",
        item.university,
        f"{old_status} → Submitted" + (f" • {item.submitted_date}" if item.submitted_date else ""),
        "✅",
        user.id,
    )
    db.session.commit()
    flash("Application submission recorded. Great work!", "success")
    return redirect(url_for("universities"))


def build_recent_updates(limit=5):
    entries = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(limit).all()
    updates = []
    for item in entries:
        student = db.session.get(User, item.student_id)
        if student:
            updates.append({
                "time": item.created_at,
                "type": item.activity_type,
                "student": student,
                "title": item.title,
                "detail": item.detail,
                "icon": item.icon,
            })
    return updates


@app.route("/teacher/activity")
def teacher_activity():
    teacher = current_user()
    if not teacher or teacher.role != "teacher":
        return redirect(url_for("login"))

    page = max(1, request.args.get("page", 1, type=int))
    per_page = 5
    total = ActivityLog.query.count()
    entries = ActivityLog.query.order_by(ActivityLog.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    updates = []
    for item in entries:
        student = db.session.get(User, item.student_id)
        if student:
            updates.append({
                "time": item.created_at,
                "type": item.activity_type,
                "student": student,
                "title": item.title,
                "detail": item.detail,
                "icon": item.icon,
            })

    total_pages = max(1, (total + per_page - 1) // per_page)
    return render_template(
        "teacher_activity.html",
        updates=updates,
        page=page,
        total_pages=total_pages,
        total=total,
    )

@app.route("/teacher")
def teacher_dashboard():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    if user.role != "teacher":
        return redirect(url_for("student_dashboard"))

    students = User.query.filter_by(role="student").order_by(User.year_level, User.name).all()
    rows = []
    attention = []

    for student in students:
        essays = EssaySubmission.query.filter_by(student_id=student.id).order_by(EssaySubmission.submitted_at.desc()).all()
        latest_essay = essays[0] if essays else None

        det_records = DETRecord.query.filter_by(student_id=student.id).order_by(DETRecord.created_at.desc()).all()
        official_det = next((r for r in det_records if r.record_type.lower() == "official"), None)
        latest_det = det_records[0] if det_records else None

        universities = UniversityOption.query.filter_by(student_id=student.id).order_by(UniversityOption.created_at.desc()).all()
        researched_count = len(universities)
        shortlisted_count = sum(1 for u in universities if u.status in ["Shortlisted", "Applying", "Submitted"])
        applied_count = sum(1 for u in universities if u.applied)

        year = student.year_level or 1
        current_stage = get_year_pathway(year)["label"].title()

        flags = []
        if year == 1:
            if not latest_essay:
                flags.append("No essay work yet")
            if not latest_det:
                flags.append("No DET practice yet")
        elif year == 2:
            if not official_det:
                flags.append("No official DET recorded")
            if researched_count < 3:
                flags.append("Fewer than 3 universities researched")
            if not latest_essay or latest_essay.stage not in ["Polished Version", "Final Version"] or latest_essay.status != "Approved":
                flags.append("Essay not yet polished/approved")
        elif year == 3:
            if applied_count < 1:
                flags.append("No overseas application submitted")
            if shortlisted_count < 1:
                flags.append("No university shortlist")
            if not official_det:
                flags.append("No official DET recorded")

        for flag in flags:
            attention.append({
                "student": student,
                "message": flag,
                "severity": "high" if (year == 3 and "application" in flag.lower()) else "medium",
            })

        rows.append({
            "student": student,
            "scores": get_scores(student),
            "current_stage": current_stage,
            "latest_essay": latest_essay,
            "latest_det": latest_det,
            "official_det": official_det,
            "researched_count": researched_count,
            "shortlisted_count": shortlisted_count,
            "applied_count": applied_count,
            "flags": flags,
        })

    pending_promotions = PromotionRequest.query.filter_by(status="Pending").order_by(PromotionRequest.requested_at.asc()).all()
    pending_teachers = User.query.filter_by(role="teacher", account_status="pending").order_by(User.created_at.asc()).all()
    pending_essays = EssaySubmission.query.filter_by(status="Pending Review").order_by(EssaySubmission.submitted_at.asc()).all()

    return render_template(
        "teacher_dashboard.html",
        rows=rows,
        attention=attention,
        recent_updates=build_recent_updates(5),
        pending_promotions=pending_promotions,
        pending_teachers=pending_teachers,
        pending_essays=pending_essays,
    )


@app.route("/teacher/students")
def teacher_students():
    user = current_user()
    if not user or user.role != "teacher":
        return redirect(url_for("login"))

    students = User.query.filter_by(role="student").order_by(User.name.asc()).all()
    teachers = User.query.filter_by(role="teacher", account_status="active").order_by(User.name.asc()).all()
    rows = []

    for student in students:
        profile = get_academic_profile(student.id)
        adviser = db.session.get(User, student.adviser_id) if student.adviser_id else None

        essays = EssaySubmission.query.filter_by(student_id=student.id).order_by(EssaySubmission.submitted_at.desc()).all()
        latest_essay = essays[0] if essays else None

        det_records = DETRecord.query.filter_by(student_id=student.id).order_by(DETRecord.created_at.desc()).all()
        official_det = next((r for r in det_records if (r.record_type or "").lower() == "official"), None)
        latest_det = det_records[0] if det_records else None

        universities = UniversityOption.query.filter_by(student_id=student.id).all()
        applied_count = sum(1 for u in universities if u.applied or u.status == "Submitted")
        latest_activity = student_last_activity(student.id)

        rows.append({
            "student": student,
            "profile": profile,
            "adviser": adviser,
            "latest_essay": latest_essay,
            "official_det": official_det,
            "latest_det": latest_det,
            "university_count": len(universities),
            "applied_count": applied_count,
            "latest_activity": latest_activity,
        })

    db.session.commit()
    return render_template(
        "teacher_students.html",
        rows=rows,
        teachers=teachers,
        eiken_levels=EIKEN_LEVELS,
    )



@app.route("/teacher/students/<int:student_id>/archive", methods=["POST"])
def teacher_student_archive(student_id):
    user = current_user()
    if not user or user.role != "teacher":
        return redirect(url_for("login"))

    student = User.query.filter_by(id=student_id, role="student").first_or_404()
    if student.account_status == "archived":
        flash(f"{student.name} is already archived.", "info")
        return redirect(url_for("teacher_students"))

    student.account_status = "archived"
    db.session.add(AdminAuditLog(
        actor_id=user.id,
        actor_name=user.name,
        action="Archive Student",
        target_name=student.name,
        target_email=student.email,
        detail="Student account archived from Student Overview."
    ))
    db.session.commit()
    flash(f"{student.name} was archived. Their records were kept.", "success")
    return redirect(url_for("teacher_students"))


@app.route("/teacher/students/<int:student_id>/restore", methods=["POST"])
def teacher_student_restore(student_id):
    user = current_user()
    if not user or user.role != "teacher":
        return redirect(url_for("login"))

    student = User.query.filter_by(id=student_id, role="student").first_or_404()
    student.account_status = "active"
    db.session.add(AdminAuditLog(
        actor_id=user.id,
        actor_name=user.name,
        action="Restore Student",
        target_name=student.name,
        target_email=student.email,
        detail="Archived student account restored."
    ))
    db.session.commit()
    flash(f"{student.name} was restored to the active roster.", "success")
    return redirect(url_for("teacher_students"))


def delete_user_account_records(target_user):
    """Delete a user's account and records while respecting cross-user foreign keys."""
    if target_user.role == "student":
        submission_ids = [
            row[0] for row in
            db.session.query(EssaySubmission.id).filter(
                EssaySubmission.student_id == target_user.id
            ).all()
        ]
        if submission_ids:
            EssayFeedback.query.filter(
                EssayFeedback.submission_id.in_(submission_ids)
            ).delete(synchronize_session=False)

        for model in [
            StudentAcademicProfile,
            EssayWorkshopProgress,
            YearMilestone,
            CompetencyScore,
            Reflection,
            Project,
            PortfolioItem,
            EssaySubmission,
            ConsultationEntry,
            Year3Milestone,
            DETRecord,
            UniversityOption,
            PromotionRequest,
            ActivityLog,
            TeacherNote,
            FutureGoal,
        ]:
            model.query.filter_by(student_id=target_user.id).delete(
                synchronize_session=False
            )

    elif target_user.role == "teacher":
        # Detach students assigned to this teacher.
        User.query.filter_by(adviser_id=target_user.id).update(
            {"adviser_id": None},
            synchronize_session=False,
        )

        # Keep student-owned history but remove/detach teacher references.
        EssayFeedback.query.filter_by(teacher_id=target_user.id).delete(
            synchronize_session=False
        )
        TeacherNote.query.filter_by(teacher_id=target_user.id).delete(
            synchronize_session=False
        )
        ConsultationEntry.query.filter_by(adviser_id=target_user.id).delete(
            synchronize_session=False
        )
        EssaySubmission.query.filter_by(reviewed_by=target_user.id).update(
            {"reviewed_by": None},
            synchronize_session=False
        )
        PromotionRequest.query.filter_by(reviewed_by=target_user.id).update(
            {"reviewed_by": None},
            synchronize_session=False
        )
        ActivityLog.query.filter_by(actor_id=target_user.id).update(
            {"actor_id": None},
            synchronize_session=False
        )
        AdminAuditLog.query.filter_by(actor_id=target_user.id).update(
            {"actor_id": None},
            synchronize_session=False
        )

    db.session.delete(target_user)


@app.route("/account/delete", methods=["POST"])
def delete_own_account():
    user = current_user()
    if not user:
        return redirect(url_for("login"))
    if user.role != "teacher":
        flash("Only teacher accounts can be deleted from the dashboard.", "error")
        return redirect(url_for("student_dashboard"))

    typed_email = request.form.get("typed_email", "").strip().lower()
    final_confirmation = request.form.get("final_confirmation", "")

    if final_confirmation != "DELETE" or typed_email != user.email.lower():
        flash("Your account was not deleted. The final confirmation did not match.", "error")
        destination = "teacher_dashboard" if user.role == "teacher" else "student_dashboard"
        return redirect(url_for(destination))

    target_role = user.role
    delete_user_account_records(user)
    db.session.flush()

    # Avoid leaving pending teachers permanently locked out if the last
    # active teacher deletes their own account.
    if target_role == "teacher":
        active_teacher_exists = User.query.filter_by(
            role="teacher",
            account_status="active"
        ).first()
        if not active_teacher_exists:
            pending_teacher = User.query.filter_by(
                role="teacher",
                account_status="pending"
            ).order_by(User.created_at.asc(), User.id.asc()).first()
            if pending_teacher:
                pending_teacher.account_status = "active"

    db.session.commit()
    session.clear()
    flash("Your Clark Global Passport account was permanently deleted.", "success")
    return redirect(url_for("login"))


@app.route("/teacher/students/<int:student_id>/delete", methods=["POST"])
def teacher_student_delete(student_id):
    user = current_user()
    if not user or user.role != "teacher":
        return redirect(url_for("login"))

    student = User.query.filter_by(id=student_id, role="student").first_or_404()

    typed_name = request.form.get("typed_name", "").strip()
    final_confirmation = request.form.get("final_confirmation", "")

    if final_confirmation != "DELETE" or typed_name != student.name:
        flash("Student was not deleted. The final confirmation did not match.", "error")
        return redirect(url_for("teacher_students"))

    target_name = student.name
    target_email = student.email

    # Keep an audit record that does not depend on the student record surviving.
    audit = AdminAuditLog(
        actor_id=user.id,
        actor_name=user.name,
        action="Delete Student",
        target_name=target_name,
        target_email=target_email,
        detail="Student account and associated Clark Global Passport records permanently deleted."
    )
    db.session.add(audit)
    db.session.flush()

    # Feedback depends on essay submissions, so remove it first.
    submission_ids = [
        row[0] for row in
        db.session.query(EssaySubmission.id).filter(EssaySubmission.student_id == student.id).all()
    ]
    if submission_ids:
        EssayFeedback.query.filter(EssayFeedback.submission_id.in_(submission_ids)).delete(synchronize_session=False)

    # Remove all records owned by this student.
    for model in [
        StudentAcademicProfile,
        CompetencyScore,
        Reflection,
        Project,
        PortfolioItem,
        EssaySubmission,
        ConsultationEntry,
        Year3Milestone,
        DETRecord,
        UniversityOption,
        PromotionRequest,
        ActivityLog,
        TeacherNote,
        FutureGoal,
    ]:
        model.query.filter_by(student_id=student.id).delete(synchronize_session=False)

    db.session.delete(student)
    db.session.commit()

    flash(f"{target_name} was permanently deleted.", "success")
    return redirect(url_for("teacher_students"))


@app.route("/teacher/students/<int:student_id>/quick-update", methods=["POST"])
def teacher_student_quick_update(student_id):
    user = current_user()
    if not user or user.role != "teacher":
        return redirect(url_for("login"))

    student = User.query.filter_by(id=student_id, role="student").first_or_404()
    profile = get_academic_profile(student.id)

    eiken_level = request.form.get("eiken_level", "").strip()
    if eiken_level not in EIKEN_LEVELS:
        eiken_level = ""
    profile.eiken_level = eiken_level

    adviser_raw = request.form.get("adviser_id", "").strip()
    if adviser_raw:
        try:
            adviser_id = int(adviser_raw)
        except ValueError:
            adviser_id = None
        adviser = User.query.filter_by(id=adviser_id, role="teacher", account_status="active").first() if adviser_id else None
        student.adviser_id = adviser.id if adviser else None
    else:
        student.adviser_id = None

    year_raw = request.form.get("year_level", "").strip()
    try:
        year_level = int(year_raw)
    except ValueError:
        year_level = student.year_level or 1
    if year_level in [1, 2, 3]:
        student.year_level = year_level

    profile.updated_at = datetime.utcnow()
    db.session.commit()
    flash(f"{student.name}'s overview details were updated.", "success")
    return redirect(url_for("teacher_students"))


@app.route("/teacher/students/export.csv")
def teacher_students_export():
    user = current_user()
    if not user or user.role != "teacher":
        return redirect(url_for("login"))

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Student",
        "Email",
        "Year",
        "Adviser",
        "EIKEN",
        "DET",
        "DET Type",
        "Essay Stage",
        "Essay Status",
        "Universities Researched",
        "Applications Submitted",
        "Account Status",
        "Last Activity",
    ])

    students = User.query.filter_by(role="student").order_by(User.name.asc()).all()
    for student in students:
        profile = get_academic_profile(student.id)
        adviser = db.session.get(User, student.adviser_id) if student.adviser_id else None
        latest_essay = EssaySubmission.query.filter_by(student_id=student.id).order_by(EssaySubmission.submitted_at.desc()).first()
        det_records = DETRecord.query.filter_by(student_id=student.id).order_by(DETRecord.created_at.desc()).all()
        official_det = next((r for r in det_records if (r.record_type or "").lower() == "official"), None)
        latest_det = official_det or (det_records[0] if det_records else None)
        universities = UniversityOption.query.filter_by(student_id=student.id).all()
        applied_count = sum(1 for u in universities if u.applied or u.status == "Submitted")
        latest_activity = student_last_activity(student.id)

        writer.writerow([
            student.name,
            student.email,
            student.year_level or "",
            adviser.name if adviser else "",
            profile.eiken_level or "",
            latest_det.score if latest_det and latest_det.score is not None else "",
            latest_det.record_type if latest_det else "",
            latest_essay.stage if latest_essay else "",
            latest_essay.status if latest_essay else "",
            len(universities),
            applied_count,
            student.account_status,
            latest_activity.created_at.strftime("%Y-%m-%d %H:%M") if latest_activity else "",
        ])

    db.session.commit()
    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=clark_global_student_overview.csv"
    return response


@app.route("/teacher/student/<int:student_id>")
def teacher_student(student_id):
    user = current_user()
    if not user or user.role != "teacher":
        return redirect(url_for("login"))

    student = User.query.filter_by(id=student_id, role="student").first_or_404()
    essays = EssaySubmission.query.filter_by(student_id=student.id).order_by(EssaySubmission.submitted_at.desc()).all()
    det_records = DETRecord.query.filter_by(student_id=student.id).order_by(DETRecord.created_at.desc()).all()
    universities = UniversityOption.query.filter_by(student_id=student.id).order_by(UniversityOption.created_at.desc()).all()
    notes = TeacherNote.query.filter_by(student_id=student.id).order_by(TeacherNote.created_at.desc()).all()
    teachers = User.query.filter_by(role="teacher", account_status="active").order_by(User.name.asc()).all()
    adviser = db.session.get(User, student.adviser_id) if student.adviser_id else None
    consultations = ConsultationEntry.query.filter_by(student_id=student.id).order_by(ConsultationEntry.created_at.desc()).all()
    milestones = ensure_year3_milestones(student.id) if student.year_level == 3 else []
    year_progress, carried_over_milestones, all_year_progress = build_year_progress(student)

    return render_template(
        "teacher_student.html",
        student=student,
        year_progress=year_progress,
        carried_over_milestones=carried_over_milestones,
        all_year_progress=all_year_progress,
        academic_profile=get_academic_profile(student.id),
        eiken_levels=EIKEN_LEVELS,
        scores=get_scores(student),
        pathway=get_year_pathway(student.year_level or 1),
        essays=essays,
        det_records=det_records,
        universities=universities,
        notes=notes,
        teachers=teachers,
        adviser=adviser,
        consultations=consultations,
        milestones=milestones,
        reflections=Reflection.query.filter_by(student_id=student.id).order_by(Reflection.created_at.desc()).all(),
        projects=Project.query.filter_by(student_id=student.id).order_by(Project.updated_at.desc()).all(),
        portfolio_items=PortfolioItem.query.filter_by(student_id=student.id).filter(PortfolioItem.category != "Personal Essay").order_by(PortfolioItem.created_at.desc()).all(),
        goal=FutureGoal.query.filter_by(student_id=student.id).first(),
    )




@app.route("/teacher/account/<int:user_id>/<action>", methods=["POST"])
def review_teacher_account(user_id, action):
    teacher = current_user()
    if not teacher or teacher.role != "teacher":
        return redirect(url_for("login"))

    target = User.query.filter_by(id=user_id, role="teacher").first_or_404()

    if target.account_status != "pending":
        flash("This teacher account has already been reviewed.", "error")
        return redirect(url_for("teacher_dashboard"))

    if action == "approve":
        target.account_status = "active"
        flash(f"Teacher account for {target.name} approved.", "success")
    elif action == "reject":
        target.account_status = "rejected"
        flash(f"Teacher account for {target.name} rejected.", "success")
    else:
        flash("Invalid action.", "error")
        return redirect(url_for("teacher_dashboard"))

    db.session.commit()
    return redirect(url_for("teacher_dashboard"))

@app.route("/teacher/student/<int:student_id>/promote", methods=["POST"])
def teacher_direct_promote_student(student_id):
    teacher = current_user()
    if not teacher or teacher.role != "teacher":
        return redirect(url_for("login"))

    student = User.query.filter_by(id=student_id, role="student").first_or_404()
    current_year = int(student.year_level or 1)

    if current_year >= 3:
        flash("Year 3 students cannot be promoted further.", "error")
        return redirect(url_for("teacher_student", student_id=student.id))

    requested_year = current_year + 1

    # Close any still-pending request for the same move so the dashboard
    # does not continue showing it after a teacher promotes directly.
    pending = PromotionRequest.query.filter_by(
        student_id=student.id,
        status="Pending"
    ).order_by(PromotionRequest.requested_at.desc()).first()
    if pending:
        pending.status = "Approved"
        pending.requested_year = requested_year
        pending.teacher_comment = "Teacher promoted student directly."
        pending.reviewed_by = teacher.id
        pending.reviewed_at = datetime.utcnow()

    student.year_level = requested_year
    ensure_year_milestones(student)

    log_activity(
        student.id,
        "Teacher Promotion",
        f"Promoted to Year {requested_year}",
        f"{teacher.name} moved the student from Year {current_year} to Year {requested_year}. "
        "Any unfinished earlier-year passport goals are carried forward.",
        "⬆️",
        teacher.id,
    )

    db.session.add(AdminAuditLog(
        actor_id=teacher.id,
        actor_name=teacher.name,
        action="Direct Student Promotion",
        target_name=student.name,
        target_email=student.email,
        detail=f"Year {current_year} → Year {requested_year}"
    ))

    db.session.commit()
    flash(f"{student.name} is now Year {requested_year}. Unfinished earlier goals were carried forward.", "success")
    return redirect(url_for("teacher_student", student_id=student.id))


@app.route("/teacher/promotion/<int:request_id>/<action>", methods=["POST"])
def review_promotion(request_id, action):
    teacher = current_user()
    if not teacher or teacher.role != "teacher":
        return redirect(url_for("login"))

    req = PromotionRequest.query.get_or_404(request_id)

    if req.status != "Pending":
        flash("This promotion request has already been reviewed.", "error")
        return redirect(url_for("teacher_dashboard"))

    student = db.session.get(User, req.student_id)
    if not student:
        flash("Student account not found.", "error")
        return redirect(url_for("teacher_dashboard"))

    comment = request.form.get("teacher_comment", "").strip()

    if action == "approve":
        student.year_level = req.requested_year
        req.status = "Approved"
        req.teacher_comment = comment
        req.reviewed_by = teacher.id
        req.reviewed_at = datetime.utcnow()

        log_activity(
            student.id,
            "Promotion Approved",
            f"Promoted to Year {student.year_level}",
            f"Teacher approved Year {req.current_year} → Year {req.requested_year}",
            "✅",
            teacher.id,
        )
        flash(f"{student.name} is now Year {student.year_level}.", "success")

    elif action == "reject":
        req.status = "Rejected"
        req.teacher_comment = comment
        req.reviewed_by = teacher.id
        req.reviewed_at = datetime.utcnow()

        log_activity(
            student.id,
            "Promotion Request",
            f"Year {req.requested_year} request not approved",
            comment or "Teacher requested that the student remain in the current year.",
            "↩️",
            teacher.id,
        )
        flash("Promotion request rejected.", "success")
    else:
        flash("Invalid action.", "error")
        return redirect(url_for("teacher_dashboard"))

    db.session.commit()
    return redirect(url_for("teacher_dashboard"))



@app.route("/teacher/student/<int:student_id>/academic-profile", methods=["POST"])
def update_academic_profile(student_id):
    user = current_user()
    if not user or user.role != "teacher":
        return redirect(url_for("login"))

    student = User.query.filter_by(id=student_id, role="student").first_or_404()
    profile = get_academic_profile(student.id)
    eiken_level = request.form.get("eiken_level", "").strip()
    profile.eiken_level = eiken_level if eiken_level in EIKEN_LEVELS else ""
    profile.student_number = request.form.get("student_number", "").strip()[:50]
    profile.homeroom = request.form.get("homeroom", "").strip()[:80]
    profile.updated_at = datetime.utcnow()
    db.session.commit()
    flash("Student academic profile updated.", "success")
    return redirect(url_for("teacher_student", student_id=student.id))


@app.route("/teacher/student/<int:student_id>/adviser", methods=["POST"])
def assign_adviser(student_id):
    teacher = current_user()
    if not teacher or teacher.role != "teacher":
        return redirect(url_for("login"))

    student = User.query.filter_by(id=student_id, role="student").first_or_404()
    adviser_id = request.form.get("adviser_id", type=int)
    adviser = User.query.filter_by(id=adviser_id, role="teacher", account_status="active").first() if adviser_id else None

    student.adviser_id = adviser.id if adviser else None
    log_activity(
        student.id,
        "Adviser Assignment",
        "Year 3 adviser updated",
        adviser.name if adviser else "No adviser assigned",
        "👥",
        teacher.id,
    )
    db.session.commit()
    flash("Adviser assignment updated.", "success")
    return redirect(url_for("teacher_student", student_id=student.id))

@app.route("/teacher/student/<int:student_id>/consultation", methods=["POST"])
def add_consultation(student_id):
    teacher = current_user()
    if not teacher or teacher.role != "teacher":
        return redirect(url_for("login"))

    student = User.query.filter_by(id=student_id, role="student").first_or_404()
    entry = ConsultationEntry(
        student_id=student.id,
        adviser_id=teacher.id,
        consultation_date=request.form.get("consultation_date", ""),
        topic=request.form.get("topic", "").strip(),
        discussion=request.form.get("discussion", "").strip(),
        action_items=request.form.get("action_items", "").strip(),
        next_meeting=request.form.get("next_meeting", ""),
    )

    if not entry.topic or not entry.discussion:
        flash("Please enter the consultation topic and discussion notes.", "error")
        return redirect(url_for("teacher_student", student_id=student.id))

    db.session.add(entry)
    log_activity(
        student.id,
        "Consultation",
        entry.topic,
        entry.action_items or "Consultation notes added",
        "🗣️",
        teacher.id,
    )
    db.session.commit()
    flash("Consultation entry saved.", "success")
    return redirect(url_for("teacher_student", student_id=student.id))

@app.route("/teacher/student/<int:student_id>/year3-progress/<int:milestone_id>", methods=["POST"])
def update_year3_progress(student_id, milestone_id):
    teacher = current_user()
    if not teacher or teacher.role != "teacher":
        return redirect(url_for("login"))

    student = User.query.filter_by(id=student_id, role="student").first_or_404()
    milestone = Year3Milestone.query.filter_by(id=milestone_id, student_id=student.id).first_or_404()
    old_status = milestone.status
    milestone.status = request.form.get("status", milestone.status)
    milestone.note = request.form.get("note", "").strip()

    log_activity(
        student.id,
        "Year 3 Progress",
        milestone.milestone,
        f"{old_status} → {milestone.status}",
        "📍",
        teacher.id,
    )
    db.session.commit()
    flash("Year 3 progress updated.", "success")
    return redirect(url_for("teacher_student", student_id=student.id))

@app.route("/teacher/student/<int:student_id>/note", methods=["POST"])
def teacher_add_note(student_id):
    user = current_user()
    if not user or user.role != "teacher":
        return redirect(url_for("login"))

    student = User.query.filter_by(id=student_id, role="student").first_or_404()
    note = TeacherNote(
        student_id=student.id,
        teacher_id=user.id,
        category=request.form.get("category", "General"),
        note=request.form["note"],
        next_goal=request.form.get("next_goal", ""),
    )
    db.session.add(note)
    log_activity(
        student.id,
        "Adviser Note",
        note.category,
        note.next_goal or note.note[:120],
        "📝",
        user.id,
    )
    db.session.commit()
    flash("Teacher note saved.", "success")
    return redirect(url_for("teacher_student", student_id=student.id))

@app.route("/teacher/student/<int:student_id>/competency", methods=["POST"])
def teacher_update_competency(student_id):
    user = current_user()
    if not user or user.role != "teacher":
        return redirect(url_for("login"))

    student = User.query.filter_by(id=student_id, role="student").first_or_404()
    competency = request.form["competency"]
    score_value = max(1, min(10, int(request.form["score"])))

    row = CompetencyScore.query.filter_by(student_id=student.id, competency=competency).first()
    if not row:
        row = CompetencyScore(student_id=student.id, competency=competency)
        db.session.add(row)
    old_score = row.score
    row.score = score_value
    log_activity(
        student.id,
        "Teacher Update",
        competency,
        f"Competency score: {old_score} → {score_value}",
        "📊",
        user.id,
    )
    db.session.commit()
    flash("Competency score updated.", "success")
    return redirect(url_for("teacher_student", student_id=student.id))


YEAR_MILESTONE_DEFINITIONS = {
    1: {"title": "Foundation", "goal": "Build your story and English foundation.", "milestones": [
        ("first_reflection", "Complete your first reflection"),
        ("story_bank", "Create your Story Bank"),
        ("essay_training", "Complete the Essay Writeshops"),
        ("first_essay_draft", "Finish your first personal essay draft"),
        ("det_routine", "Build a DET study routine"),
        ("global_activity", "Join at least one school or global activity"),
        ("first_portfolio", "Add your first portfolio item"),
        ("inquiry_project", "Complete an inquiry or PBL project"),
        ("year_reflection", "Complete your end-of-year reflection"),
    ]},
    2: {"title": "Exploration", "goal": "Explore your interests and build meaningful experiences.", "milestones": [
        ("inquiry_project", "Complete an inquiry or PBL project"),
        ("active_role", "Take an active or leadership role in an activity"),
        ("portfolio_update", "Update your portfolio with Year 2 evidence"),
        ("major_career_research", "Research possible majors or career paths"),
        ("university_shortlist", "Build an initial university shortlist"),
        ("essay_development", "Develop your personal essay further"),
        ("det_progress", "Record and reflect on your DET progress"),
        ("year_reflection", "Complete your end-of-year reflection"),
    ]},
    3: {"title": "Launch", "goal": "Prepare, complete, and submit your overseas university applications.", "milestones": [
        ("university_list", "Confirm your final university list"),
        ("official_det", "Record your official DET score"),
        ("final_essay", "Get your final personal essay approved"),
        ("school_documents", "Prepare transcripts and school documents"),
        ("recommendations", "Request recommendation letters"),
        ("applications_progress", "Complete application forms"),
        ("application_submitted", "Submit at least one overseas application"),
        ("next_steps", "Prepare for interviews, scholarships, or visa steps"),
    ]},
}

def ensure_year_milestones(student):
    if not student or student.role != "student":
        return
    current_year = max(1, min(int(student.year_level or 1), 3))
    existing = {(r.year_level, r.milestone_key) for r in
                YearMilestone.query.filter_by(student_id=student.id).all()}
    changed = False
    for year in range(1, current_year + 1):
        for key, _ in YEAR_MILESTONE_DEFINITIONS[year]["milestones"]:
            if (year, key) not in existing:
                db.session.add(YearMilestone(student_id=student.id, year_level=year,
                                             milestone_key=key, status="not_started"))
                changed = True
    if changed:
        db.session.commit()

def build_year_progress(student):
    ensure_year_milestones(student)
    current_year = max(1, min(int(student.year_level or 1), 3))
    rows = YearMilestone.query.filter_by(student_id=student.id).all()
    row_map = {(r.year_level, r.milestone_key): r for r in rows}
    years = []
    for year in range(1, current_year + 1):
        definition = YEAR_MILESTONE_DEFINITIONS[year]
        items = []
        for key, label in definition["milestones"]:
            row = row_map.get((year, key))
            items.append({"key": key, "label": label,
                          "status": row.status if row else "not_started"})
        complete = sum(i["status"] == "complete" for i in items)
        years.append({"year": year, "title": definition["title"], "goal": definition["goal"],
                      "milestones": items, "complete": complete, "total": len(items),
                      "percent": round(complete / len(items) * 100) if items else 0})
    current = years[-1]
    carried = []
    for yd in years[:-1]:
        for item in yd["milestones"]:
            if item["status"] != "complete":
                carried.append({**item, "from_year": yd["year"], "from_title": yd["title"]})
    return current, carried, years


def ensure_user_name_columns():
    """Add first_name and last_name to existing databases without requiring Alembic."""
    inspector = inspect(db.engine)
    columns = {column["name"] for column in inspector.get_columns("user")}

    if "first_name" not in columns:
        db.session.execute(sql_text('ALTER TABLE "user" ADD COLUMN first_name VARCHAR(80)'))
    if "last_name" not in columns:
        db.session.execute(sql_text('ALTER TABLE "user" ADD COLUMN last_name VARCHAR(80)'))

    db.session.commit()

    # Best-effort backfill for older accounts that only have a combined name.
    users = User.query.filter(
        (User.first_name.is_(None)) | (User.last_name.is_(None))
    ).all()
    changed = False
    for user in users:
        parts = (user.name or "").strip().split()
        if not user.first_name:
            user.first_name = parts[0] if parts else ""
            changed = True
        if not user.last_name:
            user.last_name = " ".join(parts[1:]) if len(parts) > 1 else ""
            changed = True
    if changed:
        db.session.commit()


def reset_all_students_once():
    """One-time v10.1.3 reset: remove every student account and student-linked record."""
    migration_key = "v10.1.3_reset_all_students"
    if SystemMigration.query.filter_by(key=migration_key).first():
        return

    student_ids = [
        row[0] for row in db.session.query(User.id).filter(User.role == "student").all()
    ]

    if student_ids:
        submission_ids = [
            row[0] for row in
            db.session.query(EssaySubmission.id).filter(EssaySubmission.student_id.in_(student_ids)).all()
        ]

        if submission_ids:
            EssayFeedback.query.filter(
                EssayFeedback.submission_id.in_(submission_ids)
            ).delete(synchronize_session=False)

        for model in [
            StudentAcademicProfile,
            EssayWorkshopProgress,
            YearMilestone,
            CompetencyScore,
            Reflection,
            Project,
            PortfolioItem,
            EssaySubmission,
            ConsultationEntry,
            Year3Milestone,
            DETRecord,
            UniversityOption,
            PromotionRequest,
            ActivityLog,
            TeacherNote,
            FutureGoal,
        ]:
            model.query.filter(model.student_id.in_(student_ids)).delete(synchronize_session=False)

        User.query.filter(User.id.in_(student_ids)).delete(synchronize_session=False)

    db.session.add(SystemMigration(key=migration_key))
    db.session.commit()


def remove_legacy_demo_accounts_and_bootstrap():
    """Remove legacy demo accounts and make sure a real installation can be bootstrapped."""

    # Legacy fake students from earlier prototype versions.
    demo_student_emails = ["yuki@clark.local", "haruto@clark.local"]
    demo_students = User.query.filter(
        User.email.in_(demo_student_emails),
        User.role == "student"
    ).all()

    if demo_students:
        ids = [student.id for student in demo_students]

        submission_ids = [
            row[0] for row in
            db.session.query(EssaySubmission.id).filter(EssaySubmission.student_id.in_(ids)).all()
        ]
        if submission_ids:
            EssayFeedback.query.filter(
                EssayFeedback.submission_id.in_(submission_ids)
            ).delete(synchronize_session=False)

        for model in [
            CompetencyScore,
            Reflection,
            Project,
            PortfolioItem,
            EssaySubmission,
            ConsultationEntry,
            Year3Milestone,
            DETRecord,
            UniversityOption,
            PromotionRequest,
            ActivityLog,
            TeacherNote,
            FutureGoal,
            StudentAcademicProfile,
        ]:
            model.query.filter(model.student_id.in_(ids)).delete(synchronize_session=False)

        User.query.filter(User.id.in_(ids)).delete(synchronize_session=False)

    # Remove the legacy demo teacher that previously blocked first-real-teacher bootstrap.
    demo_teacher = User.query.filter_by(
        email="teacher@clark.local",
        role="teacher"
    ).first()

    if demo_teacher:
        # Detach any adviser references first.
        User.query.filter_by(adviser_id=demo_teacher.id).update(
            {"adviser_id": None},
            synchronize_session=False
        )

        # Preserve audit logs but detach their FK if necessary.
        AdminAuditLog.query.filter_by(actor_id=demo_teacher.id).update(
            {"actor_id": None},
            synchronize_session=False
        )

        # Remove teacher-owned feedback/notes/consultations where required.
        EssayFeedback.query.filter_by(teacher_id=demo_teacher.id).delete(
            synchronize_session=False
        )
        TeacherNote.query.filter_by(teacher_id=demo_teacher.id).delete(
            synchronize_session=False
        )
        ConsultationEntry.query.filter_by(adviser_id=demo_teacher.id).delete(
            synchronize_session=False
        )

        db.session.delete(demo_teacher)

    db.session.flush()

    # If no real teacher is active, activate the earliest pending real teacher.
    active_real_teacher = User.query.filter(
        User.role == "teacher",
        User.account_status == "active",
        User.email != "teacher@clark.local"
    ).first()

    if not active_real_teacher:
        first_pending_teacher = User.query.filter(
            User.role == "teacher",
            User.account_status == "pending",
            User.email != "teacher@clark.local"
        ).order_by(User.created_at.asc(), User.id.asc()).first()

        if first_pending_teacher:
            first_pending_teacher.account_status = "active"

    db.session.commit()


with app.app_context():
    db.create_all()
    ensure_user_name_columns()
    reset_all_students_once()
    remove_legacy_demo_accounts_and_bootstrap()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
