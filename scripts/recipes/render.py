"""Рисует картинки рецептов крафта для вики в стиле интерфейса Minecraft.

Запуск из корня репозитория:  python3 scripts/recipes/render.py
Картинки появятся в src/assets/recipes/<имя>.png.

Текстуры лежат в scripts/recipes/textures: ванильные взяты из клиента 26.3,
наши из модов (minehouse-landing/*-mod/src/main/resources/assets).
Файл с префиксом block_ это текстура блока. Предметы описаны в ITEMS ниже:
плоский предмет это одна текстура, блок рисуется кубиком из трёх граней.

Чтобы добавить рецепт, допиши его в RECIPES (и предметы в ITEMS) и запусти скрипт.
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
TEX = ROOT / "textures"
OUT = ROOT.parent.parent / "src" / "assets" / "recipes"

S = 4  # масштаб: 1 пиксель интерфейса = 4 пикселя картинки

# --- предметы --------------------------------------------------------------

# flat: имя файла текстуры. cube: (верх, бок, перед) или одна текстура на всё,
# бок можно задать списком слоёв (текстура + наложение).
ITEMS = {
    "iron_ingot": {"flat": "iron_ingot"},
    "clock": {"flat": "clock_00"},
    "compass": {"flat": "compass_00"},
    "copper_ingot": {"flat": "copper_ingot"},
    "stick": {"flat": "stick"},
    "feather": {"flat": "feather"},
    "paper": {"flat": "paper"},
    "book": {"flat": "book"},
    "written_book": {"flat": "written_book"},
    "black_dye": {"flat": "black_dye"},
    "coal": {"flat": "coal"},
    "charcoal": {"flat": "charcoal"},
    "honeycomb": {"flat": "honeycomb"},
    "ward_template": {"flat": "ward_armor_trim_smithing_template"},
    "waxed_ward_template": {"flat": "ward_armor_trim_smithing_template", "glint": True},
    "powered_rail": {"flat": "block_powered_rail"},
    "rail": {"flat": "block_rail"},
    "glass_pane": {"flat": "block_glass"},
    "white_wool": {"cube": "block_white_wool"},
    "magnifier": {"flat": "magnifier"},
    "metro_station": {
        "cube": (
            "block_metro_station_top",
            ["block_metro_station_side", "block_metro_station_sign_none"],
            ["block_metro_station_side", "block_metro_station_sign_none"],
        )
    },
    "metro_junction": {
        "cube": (
            "block_metro_station_top",
            ["block_metro_station_side", "block_metro_junction_sign"],
            ["block_metro_station_side", "block_metro_junction_sign"],
        )
    },
    "cloud": {"cube": ("block_cloud_top", "block_cloud_side", "block_cloud_side")},
    "magic_leaf": {"flat": "magic_leaf"},
    "magic_leaf_block": {"cube": "block_magic_leaf_block"},
    "magic_papirosa": {"flat": "magic_papirosa"},
}

# --- рецепты ---------------------------------------------------------------
# shaped: pattern + key, shapeless: ingredients, smithing: template/base/addition.
# Ингредиент может быть списком: тогда в слоте показывается первый вариант.

RECIPES = {
    "metro_station": {
        "shaped": ["III", "ICI", "IRI"],
        "key": {"I": "iron_ingot", "C": "clock", "R": "powered_rail"},
        "result": "metro_station",
    },
    "metro_junction": {
        "shaped": ["III", "ICI", "IRI"],
        "key": {"I": "iron_ingot", "C": "compass", "R": "rail"},
        "result": "metro_junction",
    },
    "magnifier": {
        "shaped": [" C ", "CGC", "SC "],
        "key": {"C": "copper_ingot", "G": "glass_pane", "S": "stick"},
        "result": "magnifier",
    },
    "cloud": {
        "shaped": [" W ", "WFW", " W "],
        "key": {"W": "white_wool", "F": "feather"},
        "result": ("cloud", 4),
    },
    "black_dye_from_coal": {"shapeless": ["coal"], "result": "black_dye"},
    "black_dye_from_charcoal": {"shapeless": ["charcoal"], "result": "black_dye"},
    "guide_book": {"shapeless": ["book", "paper"], "result": "written_book"},
    "waxed_template": {
        "smithing": ("ward_template", "honeycomb", None),
        "result": "waxed_ward_template",
    },
    "magic_leaf_block": {
        "shaped": ["LLL", "LLL", "LLL"],
        "key": {"L": "magic_leaf"},
        "result": "magic_leaf_block",
    },
    "magic_leaf_from_block": {
        "shapeless": ["magic_leaf_block"],
        "result": ("magic_leaf", 9),
    },
    "magic_papirosa": {
        "shapeless": ["magic_leaf", "magic_leaf", "paper"],
        "result": "magic_papirosa",
    },
}

# --- рисование -------------------------------------------------------------

BG = (198, 198, 198, 255)
LIGHT = (255, 255, 255, 255)
DARK = (85, 85, 85, 255)
SLOT = (139, 139, 139, 255)
SLOT_DARK = (55, 55, 55, 255)
BORDER = (0, 0, 0, 255)


def tex(name: str) -> Image.Image:
    return Image.open(TEX / f"{name}.png").convert("RGBA")


def layered(spec) -> Image.Image:
    if isinstance(spec, str):
        return tex(spec)
    base = tex(spec[0])
    for over in spec[1:]:
        base.alpha_composite(tex(over))
    return base


def shade(img: Image.Image, k: float) -> Image.Image:
    r, g, b, a = img.split()
    r, g, b = (c.point(lambda v: int(v * k)) for c in (r, g, b))
    return Image.merge("RGBA", (r, g, b, a))


def face(img: Image.Image, size, origin, du, dv) -> Image.Image:
    """Кладёт текстуру 16x16 на параллелограмм origin + u*du + v*dv (u, v от 0 до 1)."""
    n = 256
    src = img.resize((n, n), Image.NEAREST)
    (ox, oy), (ax, ay), (bx, by) = origin, du, dv
    det = ax * by - bx * ay
    # обратное преобразование: (x, y) -> (u, v) * n
    ia, ib = by / det * n, -bx / det * n
    ic, id_ = -ay / det * n, ax / det * n
    data = (ia, ib, -(ia * ox + ib * oy), ic, id_, -(ic * ox + id_ * oy))
    out = src.transform(size, Image.AFFINE, data, resample=Image.NEAREST)
    mask = Image.new("L", size, 0)
    pts = [origin, (ox + ax, oy + ay), (ox + ax + bx, oy + ay + by), (ox + bx, oy + by)]
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    res = Image.new("RGBA", size, (0, 0, 0, 0))
    res.paste(out, (0, 0), Image.composite(out.getchannel("A"), mask, mask))
    return res


def cube(spec) -> Image.Image:
    if isinstance(spec, str):
        spec = (spec, spec, spec)
    top, left, right = (layered(s) for s in spec)
    px = 16 * S
    s = 7.6 * S  # длина ребра в изометрии, кубик помещается в слот 16x16
    w = 2 * s * math.cos(math.radians(30))
    x0, y0 = (px - w) / 2, (px - 2 * s) / 2
    size = (px, px)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    img.alpha_composite(face(top, size, (x0 + w / 2, y0), (w / 2, s / 2), (-w / 2, s / 2)))
    img.alpha_composite(
        face(shade(left, 0.8), size, (x0, y0 + s / 2), (w / 2, s / 2), (0, s))
    )
    img.alpha_composite(
        face(shade(right, 0.6), size, (x0 + w / 2, y0 + s), (w / 2, -s / 2), (0, s))
    )
    return img


def glint(img: Image.Image) -> Image.Image:
    """Фиолетовый отблеск зачарованного предмета, только по непрозрачным пикселям."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    for k in range(-img.width, img.width * 2, 10 * S):
        d.line([(k, 0), (k + img.width, img.height)], fill=(170, 90, 255, 110), width=3 * S)
    mask = img.getchannel("A")
    out = img.copy()
    out.alpha_composite(Image.composite(overlay, Image.new("RGBA", img.size), mask))
    return out


def item_icon(name: str) -> Image.Image:
    spec = ITEMS[name]
    if "cube" in spec:
        img = cube(spec["cube"])
    else:
        img = tex(spec["flat"]).resize((16 * S, 16 * S), Image.NEAREST)
    if spec.get("glint"):
        img = glint(img)
    return img


def font(px: int):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ):
        if Path(path).exists():
            return ImageFont.truetype(path, px)
    return ImageFont.load_default()


def draw_slot(canvas: Image.Image, x: int, y: int, big: bool = False):
    """Слот как в интерфейсе: 18x18 с тёмной рамкой сверху-слева и светлой снизу-справа."""
    d = ImageDraw.Draw(canvas)
    n = 26 if big else 18
    d.rectangle([x * S, y * S, (x + n) * S - 1, (y + n) * S - 1], fill=SLOT)
    d.rectangle([x * S, y * S, (x + n - 1) * S - 1, (y + 1) * S - 1], fill=SLOT_DARK)
    d.rectangle([x * S, y * S, (x + 1) * S - 1, (y + n - 1) * S - 1], fill=SLOT_DARK)
    d.rectangle([(x + 1) * S, (y + n - 1) * S, (x + n) * S - 1, (y + n) * S - 1], fill=LIGHT)
    d.rectangle([(x + n - 1) * S, (y + 1) * S, (x + n) * S - 1, (y + n) * S - 1], fill=LIGHT)


def put_item(canvas: Image.Image, item, x: int, y: int, big: bool = False):
    if item is None:
        return
    count = 1
    if isinstance(item, tuple):
        item, count = item
    if isinstance(item, list):
        item = item[0]
    off = 5 if big else 1
    icon = item_icon(item)
    canvas.alpha_composite(icon, ((x + off) * S, (y + off) * S))
    if count > 1:
        d = ImageDraw.Draw(canvas)
        f = font(9 * S)
        text = str(count)
        right, bottom = (x + off + 17) * S, (y + off + 17) * S
        tw = d.textlength(text, font=f)
        pos = (right - tw - 1 * S, bottom - 10 * S)
        d.text((pos[0] + S, pos[1] + S), text, font=f, fill=(63, 63, 63, 255))
        d.text(pos, text, font=f, fill=(255, 255, 255, 255))


def panel(w: int, h: int) -> Image.Image:
    img = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([S, S, (w - 1) * S - 1, (h - 1) * S - 1], fill=BG)
    # чёрная рамка со скруглёнными углами
    d.rectangle([2 * S, 0, (w - 2) * S - 1, S - 1], fill=BORDER)
    d.rectangle([2 * S, (h - 1) * S, (w - 2) * S - 1, h * S - 1], fill=BORDER)
    d.rectangle([0, 2 * S, S - 1, (h - 2) * S - 1], fill=BORDER)
    d.rectangle([(w - 1) * S, 2 * S, w * S - 1, (h - 2) * S - 1], fill=BORDER)
    for cx, cy in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)):
        d.rectangle([cx * S, cy * S, (cx + 1) * S - 1, (cy + 1) * S - 1], fill=BORDER)
    # светлая кромка сверху-слева, тёмная снизу-справа
    d.rectangle([2 * S, S, (w - 3) * S - 1, 3 * S - 1], fill=LIGHT)
    d.rectangle([S, 2 * S, 3 * S - 1, (h - 3) * S - 1], fill=LIGHT)
    d.rectangle([3 * S, (h - 3) * S, (w - 2) * S - 1, (h - 1) * S - 1], fill=DARK)
    d.rectangle([(w - 3) * S, 3 * S, (w - 1) * S - 1, (h - 2) * S - 1], fill=DARK)
    return img


def arrow(canvas: Image.Image, x: int, y: int):
    d = ImageDraw.Draw(canvas)
    c = (139, 139, 139, 255)
    d.rectangle([x * S, (y + 6) * S, (x + 15) * S - 1, (y + 10) * S - 1], fill=c)
    for i in range(8):
        d.rectangle(
            [(x + 15 + i) * S, (y + i) * S, (x + 16 + i) * S - 1, (y + 16 - i) * S - 1],
            fill=c,
        )


def render(recipe: dict) -> Image.Image:
    if "smithing" in recipe:
        w, h = 130, 40
        img = panel(w, h)
        for i, it in enumerate(recipe["smithing"]):
            draw_slot(img, 8 + i * 18, 11)
            put_item(img, it, 8 + i * 18, 11)
        arrow(img, 70, 12)
        draw_slot(img, 98, 7, big=True)
        put_item(img, recipe["result"], 98, 7, big=True)
        return img

    w, h = 130, 70
    img = panel(w, h)
    grid = [[None] * 3 for _ in range(3)]
    if "shaped" in recipe:
        for r, row in enumerate(recipe["shaped"]):
            for c, ch in enumerate(row):
                if ch != " ":
                    grid[r][c] = recipe["key"][ch]
    else:
        for i, it in enumerate(recipe["shapeless"]):
            grid[i // 3][i % 3] = it
    for r in range(3):
        for c in range(3):
            draw_slot(img, 8 + c * 18, 8 + r * 18)
            put_item(img, grid[r][c], 8 + c * 18, 8 + r * 18)
    arrow(img, 70, 27)
    draw_slot(img, 98, 22, big=True)
    put_item(img, recipe["result"], 98, 22, big=True)
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, recipe in RECIPES.items():
        render(recipe).save(OUT / f"{name}.png", optimize=True)
        print("ok", name)


if __name__ == "__main__":
    main()
