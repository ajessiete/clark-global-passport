function richPlainText(editor) {
  return (editor.innerText || "").replace(/\s+/g, " ").trim();
}

function updateRichEditor(form) {
  const editor = form.querySelector(".rich-editor");
  const hidden = form.querySelector(".rich-editor-input");
  const count = form.querySelector(".editor-word-count");
  if (!editor || !hidden) return;
  hidden.value = editor.innerHTML;
  const words = richPlainText(editor);
  if (count) count.textContent = words ? words.split(" ").length : 0;
}

function richDraftKey(form) {
  return "clark-global-rich-draft:" + (form.dataset.draftKey || window.location.pathname);
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-language-tabs]").forEach(group => {
    const buttons = group.querySelectorAll("[data-lang]");
    const card = group.closest(".lesson-card");
    buttons.forEach(button => button.addEventListener("click", () => {
      buttons.forEach(b => b.classList.toggle("active", b === button));
      card.querySelectorAll("[data-language-panel]").forEach(panel => {
        panel.hidden = panel.dataset.languagePanel !== button.dataset.lang;
      });
    }));
  });

  document.querySelectorAll(".rich-editor-form").forEach(form => {
    const editor = form.querySelector(".rich-editor");
    if (!editor) return;
    const status = form.querySelector(".editor-save-status");
    const key = richDraftKey(form);

    // Only restore a local draft when the server editor is otherwise empty.
    try {
      const saved = localStorage.getItem(key);
      if (saved && !richPlainText(editor)) {
        editor.innerHTML = saved;
        if (status) status.textContent = "Draft restored from this device.";
      }
    } catch (e) {}

    form.querySelectorAll("[data-command]").forEach(button => {
      button.addEventListener("click", () => {
        editor.focus();
        document.execCommand(button.dataset.command, false, null);
        updateRichEditor(form);
      });
    });

    let timer = null;
    editor.addEventListener("input", () => {
      updateRichEditor(form);
      clearTimeout(timer);
      timer = setTimeout(() => {
        try {
          localStorage.setItem(key, editor.innerHTML);
          if (status) status.textContent = navigator.onLine
            ? "Draft saved on this device."
            : "Offline draft saved on this device.";
        } catch (e) {}
      }, 350);
    });

    form.addEventListener("submit", (event) => {
      updateRichEditor(form);
      if (!richPlainText(editor)) {
        event.preventDefault();
        editor.focus();
        if (status) status.textContent = "Please write something before submitting.";
        return;
      }
      if (navigator.onLine) {
        setTimeout(() => {
          try { localStorage.removeItem(key); } catch (e) {}
        }, 1000);
      }
    });

    updateRichEditor(form);
  });
});
