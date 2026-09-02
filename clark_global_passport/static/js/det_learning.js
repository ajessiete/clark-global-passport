document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".reveal-vocab").forEach(button => {
    button.addEventListener("click", () => {
      const card = button.closest(".vocab-study-card");
      const answer = card.querySelector(".vocab-answer");
      answer.hidden = false;
      button.hidden = true;
    });
  });
});
