document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".direct-promote-form").forEach((form) => {
        form.addEventListener("submit", (event) => {
            const student = form.dataset.student || "this student";
            const currentYear = form.dataset.currentYear || "";
            const nextYear = form.dataset.nextYear || "";

            const confirmed = window.confirm(
                `Promote ${student} from Year ${currentYear} to Year ${nextYear}?\n\n` +
                "This does not erase unfinished goals. Any incomplete earlier-year milestones will carry forward."
            );

            if (!confirmed) {
                event.preventDefault();
            }
        });
    });
});
