function draftKey(form) {
  return "clark-global-draft:" + (form.dataset.draftKey || window.location.pathname);
}

function collectDraft(form) {
  const data = {};
  form.querySelectorAll("input[name], textarea[name], select[name]").forEach(el => {
    if (el.type === "password" || el.type === "hidden" || el.type === "submit") return;
    if (el.type === "checkbox" || el.type === "radio") {
      data[el.name] = el.checked;
    } else {
      data[el.name] = el.value;
    }
  });
  return data;
}

function restoreDraft(form, data) {
  Object.entries(data).forEach(([name, value]) => {
    const elements = form.querySelectorAll(`[name="${CSS.escape(name)}"]`);
    elements.forEach(el => {
      if (el.type === "checkbox" || el.type === "radio") {
        el.checked = Boolean(value);
      } else if (!el.value) {
        el.value = value;
      }
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("form[data-local-draft='true']").forEach(form => {
    const key = draftKey(form);
    const notice = form.querySelector(".draft-status");

    try {
      const saved = localStorage.getItem(key);
      if (saved) {
        restoreDraft(form, JSON.parse(saved));
        if (notice) notice.textContent = "Draft restored from this device.";
      }
    } catch (e) {}

    let timer = null;
    form.addEventListener("input", () => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        try {
          localStorage.setItem(key, JSON.stringify(collectDraft(form)));
          if (notice) notice.textContent = navigator.onLine
            ? "Draft saved on this device."
            : "Offline draft saved on this device.";
        } catch (e) {}
      }, 350);
    });

    form.addEventListener("submit", () => {
      // Do not clear immediately if offline; a failed POST must keep the draft.
      if (navigator.onLine) {
        setTimeout(() => {
          try { localStorage.removeItem(key); } catch (e) {}
        }, 1000);
      }
    });
  });
});
