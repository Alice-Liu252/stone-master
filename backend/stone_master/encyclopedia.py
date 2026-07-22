"""AI 石頭百科 (docs/GDD.md 第 5 章) — structured lookup + simple Q&A.

Ties the fantasy scan/generation pipeline (vision.py, generation.py) back
to real geology content, so a scanned stone can answer "這是什麼石頭？"
with the actual entry from docs/species/ENCYCLOPEDIA_SAMPLE.md, not just a
made-up rock_type bucket.

This is a prototype stand-in for the RAG + LLM system described in
docs/TECHNICAL_ARCHITECTURE.md section 5: fixed template answers over a
small hand-written knowledge base, not real natural-language generation.
It's still grounded-only by construction (answers are built entirely from
the structured fields below, nothing is invented at query time), which is
the one non-negotiable property carried over from the real design.

SPECIES here must stay in sync with docs/species/ENCYCLOPEDIA_SAMPLE.md —
if you add an entry to one, add it to the other.
"""
from __future__ import annotations

import random
from typing import Optional

# rock_type values must match the buckets produced by
# generation._rock_type_hint(): igneous / sedimentary / metamorphic / mineral
SPECIES = [
    {
        "id": "quartz",
        "rock_type": "mineral",
        "name_zh": "石英",
        "name_en": "Quartz",
        "sci_name": "Quartz (SiO2)",
        "color": "無色、白、煙灰、粉紫等，依雜質而異",
        "texture": "玻璃光澤，貝殼狀斷口",
        "hardness": "莫氏 7",
        "density": "2.65 g/cm3",
        "luster": "玻璃光澤",
        "composition": "二氧化矽 SiO2",
        "formation": "火成岩結晶、熱液礦脈、變質作用皆可生成",
        "era": "各地質年代皆有生成",
        "world_locations": "巴西、馬達加斯加、美國阿肯色州",
        "taiwan_locations": "花蓮、南投等地溪床常見",
        "collection_value": "中等，透明無瑕者價值較高",
        "uses": "玻璃製造、電子工業（壓電石英）、飾品",
        "fun_fact": "沙子的主要成分就是石英顆粒；早期水晶收音機正是利用石英的壓電效應",
    },
    {
        "id": "amethyst",
        "rock_type": "mineral",
        "name_zh": "紫水晶",
        "name_en": "Amethyst",
        "sci_name": "Amethyst（石英變種，SiO2 含微量鐵）",
        "color": "紫色，濃淡因鐵離子含量與天然輻射而異",
        "texture": "柱狀結晶，常見於晶洞內壁",
        "hardness": "莫氏 7",
        "density": "2.65 g/cm3",
        "luster": "玻璃光澤",
        "composition": "SiO2 含微量 Fe",
        "formation": "火山岩晶洞（geode）中低溫熱液緩慢結晶",
        "era": "各地質年代皆有",
        "world_locations": "巴西、烏拉圭、尚比亞",
        "taiwan_locations": "天然大型礦床罕見，市面多為進口",
        "collection_value": "高，色澤濃郁均勻者尤佳",
        "uses": "珠寶飾品、擺飾",
        "fun_fact": "曾被歐洲皇室視為與紅寶石同等珍貴的寶石，直到 19 世紀巴西發現大量礦床後價值才下降",
    },
    {
        "id": "granite",
        "rock_type": "igneous",
        "name_zh": "花崗岩",
        "name_en": "Granite",
        "sci_name": "Granite",
        "color": "灰、粉紅、白等顆粒狀斑駁色澤",
        "texture": "粗粒結晶，礦物顆粒明顯可見",
        "hardness": "6~7",
        "density": "2.65~2.75 g/cm3",
        "luster": "顆粒晶面反光",
        "composition": "石英、長石、雲母",
        "formation": "岩漿在地底深處緩慢冷卻結晶而成",
        "era": "各地質年代",
        "world_locations": "中國、印度、巴西、北歐",
        "taiwan_locations": "台灣本島露頭少見，金門、馬祖為典型花崗岩地質",
        "collection_value": "一般，多作建材用途",
        "uses": "建材、紀念碑、廚房檯面",
        "fun_fact": "金門是花崗岩地質，與台灣本島以變質岩、沉積岩為主明顯不同，是辨認「金門石」的特徵",
    },
    {
        "id": "basalt",
        "rock_type": "igneous",
        "name_zh": "玄武岩",
        "name_en": "Basalt",
        "sci_name": "Basalt",
        "color": "黑至深灰",
        "texture": "細粒緻密，常見氣孔構造",
        "hardness": "約 6",
        "density": "2.9~3.0 g/cm3",
        "luster": "暗淡至微光",
        "composition": "富含輝石、橄欖石、斜長石",
        "formation": "岩漿噴出地表快速冷卻凝固",
        "era": "火山活動時期，各地質年代皆有",
        "world_locations": "冰島、夏威夷、印度德干高原",
        "taiwan_locations": "澎湖群島（著名柱狀玄武岩景觀）、基隆嶼",
        "collection_value": "一般，具完整柱狀節理的標本具展示價值",
        "uses": "建材、道路鋪面、澎湖傳統石滬與石牆",
        "fun_fact": "玄武岩冷卻收縮時常形成六角形柱狀節理，澎湖與愛爾蘭「巨人堤道」都是世界知名景觀",
    },
    {
        "id": "obsidian",
        "rock_type": "igneous",
        "name_zh": "黑曜岩",
        "name_en": "Obsidian",
        "sci_name": "Obsidian",
        "color": "黑色，偶見紅棕、條紋",
        "texture": "均質無結晶構造，斷口平滑鋒利",
        "hardness": "5~5.5",
        "density": "約 2.4 g/cm3",
        "luster": "玻璃光澤",
        "composition": "富含 SiO2 的火山玻璃，非晶質",
        "formation": "高黏度熔岩快速冷卻，礦物來不及結晶",
        "era": "多見於年輕火山地質年代",
        "world_locations": "美國黃石公園、冰島、墨西哥、日本",
        "taiwan_locations": "天然產地罕見，市面多為進口或人工玻璃仿製品",
        "collection_value": "中等，斷口完整鋒利者具工藝與收藏價值",
        "uses": "史前石器工具、裝飾品、刀刃",
        "fun_fact": "斷口極為鋒利，史前人類曾用來製作切割工具，銳利度可媲美現代手術刀",
    },
    {
        "id": "marble",
        "rock_type": "metamorphic",
        "name_zh": "大理岩",
        "name_en": "Marble",
        "sci_name": "Marble",
        "color": "白、灰，常帶各色雜質紋理",
        "texture": "細至中粒結晶，拋光後呈現柔和光澤",
        "hardness": "3~4",
        "density": "2.6~2.85 g/cm3",
        "luster": "拋光後呈亮麗光澤",
        "composition": "主要為方解石 CaCO3，由石灰岩變質而成",
        "formation": "石灰岩經高溫高壓變質作用重結晶",
        "era": "台灣大理岩主要形成於中新世",
        "world_locations": "義大利卡拉拉、希臘",
        "taiwan_locations": "花蓮太魯閣峽谷，為全球知名大理岩地形代表",
        "collection_value": "一般，特殊紋理或稀有色澤標本較具價值",
        "uses": "建材、雕刻藝術、太魯閣石雕工藝",
        "fun_fact": "太魯閣峽谷的絕壁景觀，以及砂卡礑溪清澈的藍綠色溪水，都與大理岩地質密切相關",
    },
    {
        "id": "serpentinite",
        "rock_type": "metamorphic",
        "name_zh": "蛇紋岩",
        "name_en": "Serpentinite",
        "sci_name": "Serpentinite",
        "color": "墨綠、暗綠帶斑紋，似蛇皮",
        "texture": "蠟狀質地，常見滑感表面",
        "hardness": "2.5~4",
        "density": "2.5~2.7 g/cm3",
        "luster": "蠟狀至油脂光澤",
        "composition": "蛇紋石群礦物，由橄欖岩經水化變質而成",
        "formation": "地函橄欖岩經海水熱液蝕變作用生成",
        "era": "與中央山脈東側地質帶相關",
        "world_locations": "美國加州、義大利、日本",
        "taiwan_locations": "花蓮豐田、卓溪一帶為主要產地",
        "collection_value": "高——1990 年代票選為台灣「省石」，優質標本具收藏價值",
        "uses": "建材、玉石加工（豐田玉即與蛇紋岩相關）、觀賞石",
        "fun_fact": "因表面紋理酷似蛇皮而得名，是唯一被官方票選為台灣代表岩石的種類",
    },
    {
        "id": "slate",
        "rock_type": "metamorphic",
        "name_zh": "板岩",
        "name_en": "Slate",
        "sci_name": "Slate",
        "color": "灰黑、深灰",
        "texture": "具明顯劈理，可剝成薄片",
        "hardness": "3~4",
        "density": "2.7~2.8 g/cm3",
        "luster": "絹絲至暗淡光澤",
        "composition": "由頁岩（泥岩）經低度變質作用而成",
        "formation": "頁岩受區域變質作用，礦物定向排列產生劈理",
        "era": "台灣板岩主要分布於中央山脈變質岩帶",
        "world_locations": "英國威爾斯、中國",
        "taiwan_locations": "太魯閣、能高越嶺一帶廣泛分布",
        "collection_value": "一般，具明顯劈理或化石痕跡者較特別",
        "uses": "建材（石板屋屋頂）、傳統原住民石板屋建材",
        "fun_fact": "排灣族、魯凱族傳統石板屋大量使用當地板岩堆砌而成，是重要的文化資產",
    },
    {
        "id": "conglomerate",
        "rock_type": "sedimentary",
        "name_zh": "礫岩",
        "name_en": "Conglomerate",
        "sci_name": "Conglomerate",
        "color": "混合色，依所含礫石種類而異",
        "texture": "大小不一的圓形礫石膠結而成，表面粗糙",
        "hardness": "依膠結物與礫石成分而異，約 3~7",
        "density": "約 2.3~2.7 g/cm3",
        "luster": "無特定光澤",
        "composition": "磨圓礫石＋碳酸鈣或矽質膠結物",
        "formation": "河流、海濱等高能量環境搬運磨圓的碎屑沉積膠結而成",
        "era": "台灣北海岸礫岩多形成於中新世",
        "world_locations": "全球河流沖積地形皆可見",
        "taiwan_locations": "野柳、南雅奇岩海岸地形",
        "collection_value": "一般，內含特殊化石或礦物者較有價值",
        "uses": "建材、地質教育觀察",
        "fun_fact": "野柳知名的「女王頭」正是礫岩經海浪與風化長期侵蝕形成的蕈狀岩，且侵蝕仍在持續，頸部逐年變細",
    },
    {
        "id": "hokutolite",
        "rock_type": "mineral",
        "name_zh": "北投石",
        "name_en": "Hokutolite",
        "sci_name": "Hokutolite（硫酸鉛鋇礦系列）",
        "color": "灰白至黃褐色，常見同心圓層狀構造",
        "texture": "層狀包覆於礫石表面",
        "hardness": "3~3.5",
        "density": "約 4.4~4.7 g/cm3（含鉛、鋇，密度偏高）",
        "luster": "絲絹至珍珠光澤",
        "composition": "硫酸鉛鋇礦物，含微量放射性元素鐳",
        "formation": "溫泉水中的鉛、鋇離子與硫酸根結合，層層沉積包覆於溫泉水道礫石表面",
        "era": "現代溫泉沉積作用，持續形成中",
        "world_locations": "全球僅台灣北投與日本秋田縣玉川溫泉兩處發現",
        "taiwan_locations": "台北市北投溫泉區（北投溪）",
        "collection_value": "極高——全球稀有、產地僅兩處，具放射性需妥善保存管理，是台灣礦物界珍寶",
        "uses": "礦物學研究、地質教育展示，因具放射性不作一般飾品配戴",
        "fun_fact": "1905 年由日本學者岡本要八郎在北投溪發現，是唯一以台灣地名命名的礦物",
    },
]

_BY_ID = {entry["id"]: entry for entry in SPECIES}
_BY_ROCK_TYPE: dict = {}
for _entry in SPECIES:
    _BY_ROCK_TYPE.setdefault(_entry["rock_type"], []).append(_entry)


def get_by_id(encyclopedia_id: str) -> Optional[dict]:
    return _BY_ID.get(encyclopedia_id)


def match_entry(rock_type: str, seed: str) -> dict:
    """Deterministically pick one real-world species for a scanned stone's
    rock_type bucket. Same fingerprint -> same encyclopedia entry, same
    reasoning as generation.generate_species()."""
    candidates = _BY_ROCK_TYPE.get(rock_type) or SPECIES
    rng = random.Random(seed + ":encyclopedia")
    return rng.choice(candidates)


# Canonical questions from docs/GDD.md 5.2 -> keyword triggers for the toy
# intent matcher in answer_question(). Real system replaces this with the
# RAG pipeline in docs/TECHNICAL_ARCHITECTURE.md section 5.
_INTENT_KEYWORDS = {
    "formation": ["形成", "怎麼來", "怎麼生成"],
    "location": ["哪裡", "產地", "找到", "在哪"],
    "collection": ["收藏", "保存", "怎麼放"],
    "feature": ["特色", "特別", "趣味", "有趣"],
}


def _detect_intent(question: str) -> str:
    for intent, keywords in _INTENT_KEYWORDS.items():
        if any(kw in question for kw in keywords):
            return intent
    return "what"  # default: "這是什麼石頭？"


def answer_question(entry: dict, question: str) -> str:
    """Template-based answer, entirely grounded in `entry` — never invents
    facts beyond what's in the SPECIES table above."""
    intent = _detect_intent(question)

    if intent == "formation":
        return f"{entry['name_zh']}的形成方式：{entry['formation']}（地質年代：{entry['era']}）"

    if intent == "location":
        return (
            f"{entry['name_zh']}的世界產地：{entry['world_locations']}；"
            f"台灣產地：{entry['taiwan_locations']}"
        )

    if intent == "collection":
        return (
            f"{entry['name_zh']}的收藏價值：{entry['collection_value']}。"
            f"硬度為 {entry['hardness']}，保存時可以此判斷是否容易刮傷或碰損。"
        )

    if intent == "feature":
        return f"{entry['name_zh']}最特別的地方：{entry['fun_fact']}"

    return (
        f"這是「{entry['name_zh']}（{entry['name_en']}）」，學名 {entry['sci_name']}。"
        f"顏色：{entry['color']}；光澤：{entry['luster']}；硬度：{entry['hardness']}；"
        f"主要成分：{entry['composition']}。"
    )


CANONICAL_QUESTIONS = [
    "這是什麼石頭？",
    "如何形成？",
    "哪裡可以找到？",
    "如何收藏？",
    "有什麼特色？",
]
