const q = (selector, scope = document) => scope.querySelector(selector);
const qa = (selector, scope = document) => [...scope.querySelectorAll(selector)];

const search = q("#siteSearch");
if (search) {
  search.addEventListener("input", () => {
    const term = search.value.trim().toLowerCase();
    qa("[data-search]").forEach((card) => {
      card.hidden = term && !card.dataset.search.toLowerCase().includes(term);
    });
    const visible = qa("[data-search]:not([hidden])").length;
    const count = q("#resultCount");
    if (count) count.textContent = term ? `找到 ${visible} 个项目` : "浏览全部精选项目";
  });
}

qa("[data-filter]").forEach((button) => {
  button.addEventListener("click", () => {
    const category = button.dataset.filter;
    qa("[data-filter]").forEach((item) => item.classList.toggle("active", item === button));
    qa("[data-category]").forEach((card) => {
      card.hidden = category !== "all" && card.dataset.category !== category;
    });
  });
});

const menu = q("#menuButton");
if (menu) menu.addEventListener("click", () => q("#mobileNav").classList.toggle("open"));
