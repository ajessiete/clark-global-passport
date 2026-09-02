let deferredInstallPrompt = null;

function updateConnectionBadge() {
  const badge = document.getElementById("connection-status");
  if (!badge) return;
  if (navigator.onLine) {
    badge.textContent = "Online";
    badge.classList.remove("offline");
    badge.classList.add("online");
  } else {
    badge.textContent = "Offline";
    badge.classList.remove("online");
    badge.classList.add("offline");
  }
}

window.addEventListener("online", updateConnectionBadge);
window.addEventListener("offline", updateConnectionBadge);
document.addEventListener("DOMContentLoaded", updateConnectionBadge);

window.addEventListener("beforeinstallprompt", event => {
  event.preventDefault();
  deferredInstallPrompt = event;
  const button = document.getElementById("install-app-button");
  if (button) button.hidden = false;
});

window.addEventListener("appinstalled", () => {
  const button = document.getElementById("install-app-button");
  if (button) button.hidden = true;
  deferredInstallPrompt = null;
});

document.addEventListener("DOMContentLoaded", () => {
  const button = document.getElementById("install-app-button");
  if (button) {
    button.addEventListener("click", async () => {
      if (!deferredInstallPrompt) return;
      deferredInstallPrompt.prompt();
      await deferredInstallPrompt.userChoice;
      deferredInstallPrompt = null;
      button.hidden = true;
    });
  }

  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js?v=10.5").catch(err => {
      console.warn("Service worker registration failed:", err);
    });
  }
});
