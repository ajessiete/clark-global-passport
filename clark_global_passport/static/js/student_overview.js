document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("student-overview-table");
  if (!table) return;

  const tbody = table.querySelector("tbody");
  const search = document.getElementById("student-search");
  const year = document.getElementById("year-filter");
  const adviser = document.getElementById("adviser-filter");
  const eiken = document.getElementById("eiken-filter");
  const clear = document.getElementById("clear-roster-filters");
  const count = document.getElementById("visible-student-count");
  const empty = document.getElementById("no-filter-results");
  let sortKey = "name";
  let sortDirection = 1;

  function rows() {
    return Array.from(tbody.querySelectorAll("tr[data-name]"));
  }

  function compare(a, b, key) {
    let av = a.dataset[key] ?? "";
    let bv = b.dataset[key] ?? "";

    if (["year", "det", "universities", "applications", "activity"].includes(key)) {
      av = Number(av);
      bv = Number(bv);
      return (av - bv) * sortDirection;
    }

    return av.localeCompare(bv, undefined, { numeric: true, sensitivity: "base" }) * sortDirection;
  }

  function apply() {
    const q = (search.value || "").trim().toLowerCase();
    let visible = 0;

    rows().forEach(row => {
      const matchesSearch = !q || row.dataset.name.includes(q) || row.dataset.email.includes(q);
      const matchesYear = !year.value || row.dataset.year === year.value;
      const matchesAdviser = !adviser.value || row.dataset.adviserId === adviser.value;
      const matchesEiken = !eiken.value || row.dataset.eiken === eiken.value;
      const show = matchesSearch && matchesYear && matchesAdviser && matchesEiken;
      row.hidden = !show;
      if (show) visible += 1;
    });

    rows().sort((a, b) => compare(a, b, sortKey)).forEach(row => tbody.appendChild(row));
    count.textContent = String(visible);
    empty.hidden = visible !== 0;
  }

  [search, year, adviser, eiken].forEach(control => {
    control.addEventListener(control === search ? "input" : "change", apply);
  });

  clear.addEventListener("click", () => {
    search.value = "";
    year.value = "";
    adviser.value = "";
    eiken.value = "";
    apply();
  });

  table.querySelectorAll(".sort-heading").forEach(button => {
    button.addEventListener("click", () => {
      const nextKey = button.dataset.sort;
      if (sortKey === nextKey) {
        sortDirection *= -1;
      } else {
        sortKey = nextKey;
        sortDirection = 1;
      }

      table.querySelectorAll(".sort-heading").forEach(other => {
        const arrow = other.querySelector("span");
        if (arrow) arrow.textContent = "↕";
        other.classList.remove("active-sort");
      });
      button.classList.add("active-sort");
      const arrow = button.querySelector("span");
      if (arrow) arrow.textContent = sortDirection === 1 ? "↑" : "↓";
      apply();
    });
  });

  apply();
});
