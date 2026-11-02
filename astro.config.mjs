// @ts-check
import { defineConfig } from "astro/config"
import starlight from "@astrojs/starlight"

export default defineConfig({
  site: "https://wiki.minehouse.pro",
  integrations: [
    starlight({
      title: "MineHouse Вики",
      description: "Вики Vanilla+ сервера MineHouse: как зайти, правила, особенности, моды.",
      logo: { src: "./src/assets/logo.png", alt: "MineHouse" },
      favicon: "/favicon.png",
      locales: { root: { label: "Русский", lang: "ru" } },
      social: [
        { icon: "discord", label: "Discord", href: "https://discord.gg/gCYGxDzaCb" },
        { icon: "github", label: "GitHub", href: "https://github.com/P5ina/minehouse-wiki" },
      ],
      editLink: { baseUrl: "https://github.com/P5ina/minehouse-wiki/edit/main/" },
      lastUpdated: true,
      customCss: ["./src/styles/theme.css"],
      sidebar: [
        { label: "На сайт MineHouse", link: "https://minehouse.pro", attrs: { target: "_self" } },
        {
          label: "Начало",
          items: ["join", "rules", "faq"],
        },
        {
          label: "Игра на сервере",
          items: ["features", "chat", "mods"],
        },
        { label: "Как править вики", link: "/contributing/" },
      ],
    }),
  ],
})
