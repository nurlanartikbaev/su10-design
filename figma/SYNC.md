# Сверка с Figma

Инструкция для Claude. Её же используют как промпт еженедельной задачи.

## Из Figma в репозиторий

1. `create_session` по fileKey `TLPll8pMMVWpHbJdWm6QVe`.
2. Выгрузить переменные: `figma/export-variables.js` через `use_figma` для каждой коллекции:
   `Colors`, `Spacing`, `Platform` — одним вызовом; `Theme` — двумя (`FROM=0, TO=190` и `FROM=190, TO=1000`),
   потому что ответ `use_figma` ограничен 48 КБ. Поле `tsv` записать в `figma/snapshot/<Коллекция>.tsv`, части склеить по порядку.
3. Выгрузить стили: `figma/export-styles.js` → `figma/snapshot/styles.tsv`.
4. Проверить перенос: `figma/checksum.js` через `use_figma` и `python3 scripts/checksum.py`.
   Суммы файлов должны совпасть. Если нет — `--rows` покажет строку с ошибкой; исправить и повторить.
5. `python3 scripts/tokens.py diff`.
   - Нет расхождений — сообщить «Figma совпадает» и закончить.
   - Есть — показать таблицу и спросить: принять (`import` + `build`) или вернуть Figma (`push`).
   Решение принимает человек. Сам Claude ничего не принимает и не пушит.

## Из репозитория в Figma

1. `python3 scripts/tokens.py push` → `figma/push.generated.js`.
2. Показать человеку, что изменится, и получить «да».
3. Запустить `figma/push.generated.js` через `use_figma`. Проверить `errors` в ответе.
4. Снова выгрузить снимок (шаги 2–4 выше) и убедиться, что `diff` пуст.
