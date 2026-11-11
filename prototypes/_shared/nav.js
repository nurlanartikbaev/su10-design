// Верхняя панель прототипа: назад в меню, переключатель Телефон / Десктоп, макет, тема.
// Подключение (после ../manifest.js):  <script src="../_shared/nav.js" defer></script>
(function () {
  const ROOT = new URL("../../", document.currentScript.src); // корень репозитория
  const THEME_KEY = "su10-theme";
  const root = document.documentElement;

  // тема общая для всех страниц
  try { const t = localStorage.getItem(THEME_KEY); if (t) root.dataset.theme = t; } catch (e) {}
  const isDark = () => (root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches);

  const here = location.pathname.endsWith("/") ? location.pathname + "index.html" : location.pathname;
  const feature = (window.SU10_FEATURES || []).find(f => f.views.some(v => here.endsWith(v.path)));
  const current = feature && feature.views.find(v => here.endsWith(v.path));

  const css = `
    .su10-bar { position: fixed; inset: 0 0 auto 0; z-index: 1000; height: 56px; display: flex; align-items: center; gap: 12px;
      padding: 0 16px; font-family: var(--su10-typo-family-inter);
      background: var(--su10-color-semantic-surface-2-layer); border-bottom: 1px solid var(--su10-color-semantic-border-secondary); }
    .su10-bar a, .su10-bar button { font: inherit; color: inherit; text-decoration: none; background: none; border: 0; cursor: pointer; }
    .su10-bar .back { display: flex; align-items: center; gap: 6px; padding: 8px 12px; border-radius: var(--su10-radius-border-radius-200); color: var(--su10-color-semantic-text-secondary); }
    .su10-bar .back:hover, .su10-bar .link:hover { background: var(--su10-color-component-button-tertiary-hover); color: var(--su10-color-semantic-text-primary); }
    .su10-bar .title { flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .su10-bar .seg { display: flex; padding: 2px; border-radius: var(--su10-radius-border-radius-300); background: var(--su10-color-semantic-surface-elevated); }
    .su10-bar .seg a { padding: 6px 12px; border-radius: var(--su10-radius-border-radius-200); color: var(--su10-color-semantic-text-secondary); }
    .su10-bar .seg a:hover { background: var(--su10-color-component-segmented-control-surface-hover); }
    .su10-bar .seg a[aria-current="page"] { background: var(--su10-color-component-segmented-control-surface-selected); color: var(--su10-color-semantic-text-primary);
      box-shadow: inset 0 0 0 1px var(--su10-color-component-segmented-control-border-selected); }
    .su10-bar .link { padding: 8px 12px; border-radius: var(--su10-radius-border-radius-200); color: var(--su10-color-semantic-text-info-static); }
    .su10-bar > * { white-space: nowrap; }
    @media (max-width: 560px) { .su10-bar .title, .su10-bar .figma { display: none; } .su10-bar .seg { margin-left: auto; } }
    @media (max-width: 420px) { .su10-bar { gap: 4px; padding: 0 8px; } .su10-bar .back, .su10-bar .link, .su10-bar .seg a { padding: 6px 8px; } }`;
  const style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  const bar = document.createElement("nav");
  bar.className = "su10-bar su10-text-b3-medium";
  bar.setAttribute("aria-label", "Прототипы");
  bar.innerHTML = `
    <a class="back" href="${ROOT}index.html"><span aria-hidden="true">←</span>Меню</a>
    <span class="title su10-text-b2-semibold">${feature ? feature.title : ""}</span>
    ${feature && feature.views.length > 1 ? `<div class="seg" role="group" aria-label="Версия">${feature.views
      .map(v => `<a href="${ROOT}${v.path}"${v === current ? ' aria-current="page"' : ""}>${v.label}</a>`).join("")}</div>` : ""}
    ${feature ? `<a class="link figma" href="${window.SU10_FIGMA}${feature.node}" target="_blank" rel="noopener">Макет</a>` : ""}
    <button class="link" type="button" id="su10-theme"></button>`;
  document.body.prepend(bar);

  // сдвигаем страницу под панель
  const pad = parseFloat(getComputedStyle(document.body).paddingTop) || 0;
  document.body.style.paddingTop = pad + 56 + "px";

  const btn = bar.querySelector("#su10-theme");
  const label = () => (btn.textContent = isDark() ? "Светлая тема" : "Тёмная тема");
  btn.addEventListener("click", () => {
    root.dataset.theme = isDark() ? "light" : "dark";
    try { localStorage.setItem(THEME_KEY, root.dataset.theme); } catch (e) {}
    label();
  });
  label();
})();
