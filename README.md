# MineHouse Вики

Вики сервера MineHouse: https://wiki.minehouse.pro. Сделана на [Starlight](https://starlight.astro.build/).

Страницы лежат в `src/content/docs/` обычными Markdown-файлами, меню настраивается в `astro.config.mjs`. Как предложить правку, написано на странице [Как править вики](https://wiki.minehouse.pro/contributing/).

## Локально

```sh
pnpm install
pnpm dev     # http://localhost:4321
pnpm build   # проверка, что всё собирается
```

Сайт собирается и выкладывается Vercel автоматически: `main` уходит на wiki.minehouse.pro, у каждого pull request есть своя ссылка на предпросмотр.
