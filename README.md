# su10-design

Источник правды дизайн-системы SU10: токены, CSS и кликабельные прототипы.

Прототипы онлайн: https://nurlanartikbaev.github.io/su10-design/
Figma и Claude — копии этого репозитория.

## Правило

Токен меняют **здесь**, в `tokens/`. Figma догоняет через `push`.
Если токен поменяли в Figma, это предложение: его принимают через `diff` и `import` или откатывают через `push`.

## Структура

| Папка | Что внутри | Правят руками |
|---|---|---|
| `tokens/` | Токены в формате W3C DTCG: `Colors`, `Spacing`, `Platform` (Mobile/Desktop), `Theme` (Light/Dark), `styles` | да |
| `dist/tokens.css` | CSS-переменные и текстовые классы для прототипов и кода | нет, собирает `build` |
| `figma/snapshot/` | Последний снимок переменных и стилей из Figma (TSV) | нет, приходит из Figma |
| `figma/*.js` | Скрипты для `use_figma`: выгрузка, контрольные суммы, push | нет |
| `prototypes/` | Кликабельные прототипы фич | да |
| `scripts/` | `tokens.py`, `checksum.py` (Python 3.9+, без зависимостей) | нет |

## Команды

```bash
python3 scripts/tokens.py build    # tokens → dist/tokens.css
python3 scripts/tokens.py diff     # чем Figma отличается от репозитория
python3 scripts/tokens.py import   # принять Figma: снимок → tokens
python3 scripts/tokens.py push     # репозиторий → Figma: figma/push.generated.js
python3 scripts/tokens.py check    # tokens совпадают со снимком
```

## Синхронизация с Figma

Файл: **SU10 Design System**, fileKey `TLPll8pMMVWpHbJdWm6QVe`.

**Из Figma (раз в неделю или по запросу):** Claude выгружает снимок, сверяет контрольные суммы
и показывает `diff`. Пошагово — в [figma/SYNC.md](figma/SYNC.md).

**В Figma (по запросу):** `push` пишет `figma/push.generated.js`, Claude запускает его через `use_figma`.
Скрипт меняет и создаёт переменные, но не удаляет их и не трогает стили.

## Прототипы

Главное меню — [index.html](index.html) в корне. В нём все фичи Ready for dev: готовые открываются
в версии «Телефон» или «Десктоп», остальные ведут на макет. Внутри прототипа панель сверху
переключает версии, ведёт назад в меню и меняет тему для всех страниц.

Список фич — [prototypes/manifest.js](prototypes/manifest.js). Готовый прототип: допишите ему `views`,
и он переедет в «Готово». Панель подключается двумя строками в `<head>`:

```html
<script src="../manifest.js"></script>
<script src="../_shared/nav.js" defer></script>
```

| Прототип | Источник в Figma (Redesign Student) | Что есть |
|---|---|---|
| [onboarding](prototypes/onboarding/) | Onboarding for Redesign, секция 198:46719 | Телефон А1–А6 (`index.html`) и десктоп Б1–Б6 (`desktop.html`), светлая и тёмная тема |

Новый прототип:

1. Скопируйте `prototypes/_template` в `prototypes/<фича>`.
2. Соберите экраны на переменных `--su10-*` и классах `.su10-text-*`.
3. Добавьте фичу в `prototypes/manifest.js` и подключите панель.
4. Запустите локально и откройте меню `http://localhost:8040/`:

```bash
python3 -m http.server 8040
```

Переходы между экранами: кнопка с `data-go="id"` показывает секцию с этим `id`.
Тема: `data-theme="dark"` или `"light"` на `<html>`; без атрибута — по системе.

## Решения, которые надо подтвердить

- **Desktop с 1024px.** В Figma у Platform два режима без брейкпоинта. Меняется в `DESKTOP_MIN_WIDTH` в `scripts/tokens.py`.
- **Градиенты идут сверху вниз (180°).** Направление из Figma не выгружается.
- **Опечатки в именах Figma:** `color/semantic/icon/tertuary-black-static`,
  `color/component/mobile-tabbar-v2/backgraund-gradient-*`. Переименовывать — одновременно в Figma и в `tokens/`.
