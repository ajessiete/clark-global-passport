document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".delete-own-account-form").forEach((form) => {
        form.addEventListener("submit", (event) => {
            event.preventDefault();

            const email = form.dataset.email || "";

            const first = window.confirm(
                "Permanently delete your Clark Global Passport account?\n\n" +
                "Your account and associated data will be removed. This cannot be undone."
            );

            if (!first) return;

            const typed = window.prompt(
                "Final confirmation:\n\nType your account email exactly to permanently delete your account:\n" +
                email
            );

            if (typed === null) return;

            if (typed.trim().toLowerCase() !== email.trim().toLowerCase()) {
                window.alert("The email did not match. Your account was not deleted.");
                return;
            }

            form.querySelector('input[name="typed_email"]').value = typed.trim();
            form.querySelector('input[name="final_confirmation"]').value = "DELETE";
            form.submit();
        });
    });
});
