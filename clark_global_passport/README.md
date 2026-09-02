# Clark Global Learning Passport

A local/offline Flask prototype for Clark International Course.

## What this prototype includes

- Student login
- Teacher login
- Global competency dashboard
- Reflection journal
- Inquiry / Global Challenge project tracker
- Portfolio
- Future / university direction page
- Teacher dashboard
- Individual student learning journey
- SQLite local database
- Demo data

## Demo accounts

Student
- Email: yuki@clark.local
- Password: student123

Teacher
- Email: teacher@clark.local
- Password: teacher123

## How to run in PyCharm

1. Extract this folder.
2. Open PyCharm.
3. Choose **Open** and select the `clark_global_passport` folder.
4. Make sure Python 3.11 or newer is selected.
5. Open the Terminal inside PyCharm.
6. Run:

   python -m pip install -r requirements.txt

7. Then run:

   python app.py

8. Open your browser:

   http://127.0.0.1:5000

The database is created automatically the first time the app runs.

## Important for real school use

This prototype is designed for local demonstration only. Before using real student data:
- change the SECRET_KEY
- add proper account administration
- add access controls and password reset
- add backup/export capability
- create a school-approved privacy/data retention policy
- consider encryption and managed deployment
- obtain school/IT approval

Do not use real student personal information in this prototype until those safeguards are added.


## 3-Year University Preparation Pathway

### Year 1 — Foundation
- Personal Essay Training
- Story Bank
- First essay draft
- DET introduction and practice routine

### Year 2 — Preparation
- DET readiness and official test
- Polished/final personal essay
- University research
- Shortlist creation

### Year 3 — Application
- Confirm university list
- Prepare requirements
- Submit applications
- Goal: at least one overseas university application

New modules:
- My Pathway
- Essay Lab
- DET Mission
- University Explorer


## Teacher Dashboard v3
Teacher view now includes:
- year/stage overview
- latest essay stage
- DET practice/official results
- university research count
- shortlist count
- Year 3 overseas application goal
- automatic attention flags
- adviser notes and next-goal setting
- detailed student adviser view


## Teacher UX v4
- Back buttons on major subpages
- Recent Updates feed on Teacher Dashboard
- Feed includes essays, DET entries, university activity, applications, reflections, portfolio items, and adviser notes


## Activity Log v5
This version uses a real ActivityLog database table rather than rebuilding recent activity from current records.

Logged events include:
- essay saves/stage progression
- DET entries
- university additions and edits
- university status changes
- application submissions
- reflections
- project creation and stage changes
- portfolio additions
- future-plan changes
- teacher adviser notes
- teacher competency score changes

University records can now be edited so progression such as Researching → Interested → Shortlisted → Applying → Submitted appears in the teacher activity feed.


## Registration & Promotion v6

### Registration
- Students can register directly.
- Students choose Year 1, Year 2, or Year 3.
- Transfer students can mark themselves as transfer students and enter the appropriate year.
- New teacher accounts are created as pending and require approval from an existing active teacher.

### Promotion workflow
- Year 1 students can request promotion to Year 2.
- Year 2 students can request promotion to Year 3.
- Students remain in their current year until a teacher approves.
- Teachers can approve or reject the request and leave a comment.
- Approval automatically changes the student's year level and therefore their pathway/dashboard.
- Year 3 students do not see a promotion request option.

### Activity
- Promotion requests and approvals are recorded in the activity log.


## Adviser & Approval Workflow v7

### Essay workflow
- Essay tasks are sequential and teacher-gated.
- Students can only work on the currently unlocked essay stage.
- A submission becomes Pending Review.
- Teachers can add comments, approve, or request resubmission.
- Approval unlocks the next essay task.
- A grade promotion does not automatically complete or skip unfinished essay tasks.
- Resubmissions create a new version, preserving old outputs.
- Every submission can be opened as a full-page record in a new browser tab.

### Teacher activity
- Teacher dashboard shows only 5 recent activity items.
- “See all activity” opens a paginated activity log with 5 items per page.

### Year 3 advising
- Active teachers can be assigned as a student’s Year 3 adviser.
- Teachers can record consultation date, topic, discussion, action items, and next meeting.
- Consultation history is preserved.
- Year 3 students and teachers see an eight-step progress tracker.


## Online Deployment v8

v8 is prepared for a free online prototype deployment.

Changes:
- environment-based `SECRET_KEY`
- `DATABASE_URL` support
- PostgreSQL support
- SQLite fallback for local development
- Gunicorn production server
- `Procfile`
- `render.yaml`
- `/health` endpoint
- `.gitignore`
- `.env.example`
- `DEPLOY_FREE.md`

The same codebase can now be used locally in PyCharm and online.


## Progressive Web App v9

v9 adds installable PWA behavior without caching sensitive authenticated school data.

Features:
- installable app manifest
- home-screen / desktop app icons
- root-scoped service worker
- online / offline indicator
- install button when supported by the browser
- offline fallback screen
- local automatic drafts for Essay Lab
- local automatic drafts for new Reflections
- network-first navigation
- static assets cached for faster loading
- teacher dashboards, adviser notes, consultations, and authenticated HTML are not stored in the PWA cache

Offline drafts are stored in the browser's localStorage on that device. They are not submitted to the server until the user is online and submits the form.


## v10 — Student Overview

Teacher-side roster management now includes:

- Student Overview page at `/teacher/students`
- spreadsheet-style full student list
- instant search by name or email
- filter by year level
- filter by assigned adviser/teacher
- filter by EIKEN level
- sortable Student, Year, Adviser, EIKEN, DET, Essay, Universities, Applications, and Last Activity columns
- quick edit for Year, Adviser, and EIKEN
- CSV export
- EIKEN/student number/homeroom academic profile fields
- legacy Yuki/Haruto demo student accounts are removed automatically
- fresh databases no longer create fake student accounts
- first teacher account on a completely fresh database becomes active so the system can be bootstrapped
- the old public demo-credentials box has been removed from the login page


## v10.1 — Student Archive & Safe Delete

Student Overview now includes safer account lifecycle controls:

- Archive student: keeps all records but removes the student from the default active roster
- Restore archived student
- Account-status filter: Active / Archived / All
- Permanent Delete button
- First confirmation popup explains what will be deleted
- Second confirmation popup requires the teacher to type the student's exact name
- Server rejects deletion unless the exact name and final DELETE confirmation are submitted
- Permanent deletion removes the student's associated app records
- AdminAuditLog keeps the deleting/archiving teacher, action, target name/email snapshot, and timestamp

For real school deployment, CSRF protection and a formal retention/deletion policy should still be added before using permanent delete with real student data.


## v10.1.1 — PWA cache fix

Fixes Student Overview actions being served from an older cached JavaScript file.
- service worker cache version bumped
- JS/CSS now use network-first caching
- Student Overview JavaScript explicitly cache-busted
- shared PWA JavaScript/CSS explicitly cache-busted
- service worker registration URL versioned


## v10.1.2 — Teacher bootstrap fix

Fixes the case where the legacy `teacher@clark.local` demo account caused the first real teacher registration to remain pending.

On startup:
- removes the legacy demo teacher account
- removes the old fake student accounts if still present
- detaches demo-teacher adviser references safely
- if there is no active real teacher, activates the earliest pending real teacher
- once a real active teacher exists, later teacher registrations still require approval


## v10.1.3 — Clean Student Reset

This release performs a one-time reset of all student data so the live Student Overview starts at 0 students.

On first startup after deploying v10.1.3:
- deletes every student user account
- deletes all student-linked essays and feedback
- deletes reflections, projects, portfolio items, DET records, university options, consultation entries, milestones, notes, activity logs, competency scores, promotion requests, future goals, and academic profiles
- preserves teacher accounts
- records a one-time migration marker so the reset does not repeat on later restarts

New students created after this reset are not deleted.
