"""Irad's Latin spelling of real place names, shared by the place and nature builds"""
import re

CYR = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "j", "з": "z", "и": "i", "й": "y", "к": "k",
       "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts",
       "ч": "ch", "ш": "sh", "щ": "shch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
       # Kyrgyz and Kazakh letters
       "ө": "ö", "ү": "ü", "ң": "ng", "қ": "k", "ғ": "g", "ұ": "u", "і": "i", "ә": "a", "һ": "h",
       # Uzbek Cyrillic
       "ў": "o", "ҳ": "h"}
DROP_WORDS = {"ауылы", "аулы", "ауыл", "село", "селосу", "айылы", "кишлак", "qishlog'i", "qishlogi", "posyolok", "поселок", "посёлок",
              "имени", "станция", "разъезд"}


def latin(s):
    """a native-script place name in Irad's Latin spelling"""
    if not s: return ""
    words = [w for w in re.split(r"(\s+)", s.strip()) if w.lower().strip() not in DROP_WORDS]
    s = "".join(words).strip()
    if re.search(r"[Ѐ-ӿ]", s):
        out = []
        for i, ch in enumerate(s):
            lo = ch.lower(); t = CYR.get(lo)
            if t is None: out.append(ch); continue
            if lo == "е" and (i == 0 or s[i - 1] in " -"): t = "e"
            out.append(t.capitalize() if ch != lo else t)
        s = "".join(out)
    else:   # Uzbek Latin and the Turkish-style spellings in OSM
        s = (s.replace("o‘", "o").replace("g‘", "g").replace("oʻ", "o").replace("gʻ", "g").replace("O‘", "O").replace("Oʻ", "O")
             .replace("G‘", "G").replace("Gʻ", "G").replace("'", "").replace("’", "").replace("ʼ", "")
             .replace("ş", "sh").replace("Ş", "Sh").replace("ç", "ch").replace("Ç", "Ch").replace("ı", "y").replace("ğ", "g"))
        s = re.sub(r"(?<![sScC])h", "h", s)
        s = s.replace("x", "kh").replace("X", "Kh").replace("q", "k").replace("Q", "K")
    s = s.replace("ngg", "ng").replace("Ngg", "Ng")
    s = re.sub(r"\s+", " ", s).strip(" -")
    s = "-".join(w[:1].upper() + w[1:] for w in s.split("-"))
    return " ".join(w[:1].upper() + w[1:] for w in s.split(" "))


# the generic word in a natural feature's name, in the languages OSM uses here -> what Irad's maps write instead
W = r"(?:^|(?<=\s))(?:{})(?=\s|$)"
GENERIC = [
    (W.format(r"водохранилище|водохр\.?|суу сактагычы|су қоймасы|suv ombori|sub ombori|suv omborlari|сув омбори|бөгені|bögeni"), "Reservoir"),
    (W.format(r"магистральный канал|канал|каналы|kanali|kanal|арнасы"), "Canal"),
    (W.format(r"ледник|мөңгүсү|мұздығы|muzligi"), "Glacier"),
    (W.format(r"река|р\.|өзөнү|өзөн|өзені|өзен|daryosi|дарёси|сай|say|арык|aryk|ариқ"), ""),
    (W.format(r"озеро|оз\.|көлү|көлі|ko'li|koʻli|ko‘li"), ""),
    (W.format(r"перевал|пер\.|ашуусу|асуы|dovoni|довони"), ""),
    (W.format(r"гора|г\.|пик|чокусу|шыңы|шоқысы|тауы|tog'i|togʻi|tog‘i|cho'qqisi|чўққиси|противоселевое|деривационный"), ""),
]
EN_WORDS = [(r"Нижн\w*", "Lower"), (r"Верхн\w*", "Upper"), (r"Северн\w*", "North"), (r"Южн\w*", "South"), (r"Больш\w*", "Great"),
            (r"Мал(ый|ое|ая|ые)", "Little"), (r"Средн\w*", "Middle"), (r"Западн\w*", "West"), (r"Восточн\w*", "East"), (r"Нов(ый|ое|ая)", "New"),
            (r"Стар(ый|ое|ая)", "Old"), (r"Левый|Левая|Левое", "Left"), (r"Правый|Правая|Правое", "Right"),
            (r"Quyi|Қуйи|Куйи", "Lower"), (r"Yuqori|Юқори", "Upper"), (r"Shimoliy|Шимолий", "North"), (r"Janubiy|Жанубий", "South")]
# a Russian name (a mountaineers' pass, a surname, an adjective) rather than a local one: Irad's maps leave those unnamed
RUSSIAN = re.compile(r"(yy|iy|yi|aya|oye|ogo|ego|ykh|ikh|ova|eva|ovo|nyy|noe|noy|enko|ets|ka|ina)(?=\s|$)|(?<![\w-])(Pik|Pravda|Sovet|Olimp|Tsentral|Novo|Desyat|Pyat|Turist|"
                     r"Komarov|Orlov|Gelios|Parus|Gemera|Ira|Pikgora|Uzlov|Ekstremal|Zelyon|Krasn|Skaln|Zaprometov|Zamanchiv|Musin|Roman|Bogotkov|"
                     r"Tashmetro\w*|Chimkent\w*|Solnechn|Nezavisim\w*|Georgiev|Betonn|Prud|Kazakhstan|Pervomay|Ozern|Svetl|Granitn|Vodnik|Syurpriz|Igry|"
                     r"Troyk|Karnizn|Osypn|Kul|Kyol|Levy|Kolets|Stalin|Gorkiy|Lermontov|Pushkin|Chekhov|Tolst\w*|Vershin\w*|Lednik\w*|Snezhn\w*|Kazak\w*|Assamble\w*|Pingvin|Igla|Novosibirsk|Vodnikov|Bersk|Ilyuyata|Edipamasyeti|Ashuu|Bel|Too)(?![\w-])|\b[A-Z]\.|^\w\w?$")
# well-known features whose Irad name is not the transliteration of the OSM name
NATURE_NAMES = {"syrdarya": "Syr Darya", "sirdaryo": "Syr Darya", "syrdariya": "Syr Darya", "norin": "Naryn",
                "chüy": "Chu", "shu": "Chu", "kirov reservoir": "Kyzyl-Adyr Reservoir", "toktogul reservoir": "Toktogul Reservoir",
                "koradaryo": "Kara-Darya", "karadarya": "Kara-Darya", "kara-daryo": "Kara-Darya", "chirchik": "Chirchik", "ülken shu canal": "Great Chu Canal", "chong chüy canal": "Great Chu Canal",
                "great chuy canal": "Great Chu Canal", "great talas canal": "Great Talas Canal",
                "uzun-akhmat": "Uzun-Akmat"}   # the lore's spellings
NO_NAME = re.compile(r"\d|№|имени|ветвь|сброс|коллектор|Советск|Ленин|Киров(?!ск)|Фрунзе|Калинин|Комсомол|Пионер|милици|"
                     r"Место|Строя|Пруд|дамба|отстойник|накопител|хвост|бассейн|карьер|котлован|очистн|рыбхоз|пляж", re.I)
ACRONYM = re.compile(r"\b(ДС|ГК|КНС|ТОО|ГЭС|БДР|ГРЭС|ТЭЦ)\b")


def nature_name(pr):
    """the Iradi Latin name of a river, lake, peak or pass from its OSM tags, or None when it has no usable one"""
    raw = pr.get("name") or pr.get("name_ky") or pr.get("name_kk") or pr.get("name_ru") or ""
    if any(R.search(t) for R in (NO_NAME, ACRONYM) for t in (raw, pr.get("name_ru") or "")): return None
    en = pr.get("name_en") or ""
    if not re.search(r"[Ѐ-ӿ]", raw) and re.fullmatch(r"[A-Za-z \-]+", en) and re.search(r"\b(North|South|East|West|Great|Big|Upper|Lower|Canal|Reservoir)\b", en):
        en = re.sub(r"\s+(River|Lake)$", "", en).replace("Big ", "Great ").strip()       # Uzbek canals: their English names
        return re.sub(r"^Lake (?=.*Reservoir)", "", en)
    parts = [q.strip() for q in re.split(r"\s+-\s+|/|;|\(", raw) if re.search(r"[A-Za-zЀ-ӿ]", q)]
    if not parts: return None
    s = next((q for q in parts if re.search(r"[Ѐ-ӿ]", q)), parts[0]).strip(" )")
    if not re.search(r"[Ѐ-ӿ]", s) and pr.get("name_ru") and re.search(r"[Ѐ-ӿ]", pr["name_ru"]): s = re.split(r"\s+-\s+|/|\(", pr["name_ru"])[0]
    suffix = ""
    for pat, rep in GENERIC:
        if re.search(pat, s, re.I):
            s = re.sub(pat, "", s, flags=re.I); suffix = suffix or rep
    pre = []
    for pat, rep in EN_WORDS:
        if re.search(r"(^|\s)" + pat + r"(\s|$)", s): s = re.sub(r"(^|\s)" + pat + r"(?=\s|$)", " ", s); pre.append(rep)
    s = re.sub(r"(ск|цк)(ий|ое|ая|ие|ый)(?=\s|$)", "", s)          # Паркентский канал -> Parkent Canal
    s = re.sub(r"\s+", " ", s).strip(" -.,")
    if not s: return None
    s = re.sub(r"(^|[\s-])Dj", r"\1J", latin(s))                     # Джал -> Jal, as Kyrgyz writes it
    if s.lower() in NATURE_NAMES: s = NATURE_NAMES[s.lower()]
    if RUSSIAN.search(s) and s.lower() not in NATURE_NAMES.values(): return None
    if len(s.split()) > 3 or re.search(r"[A-Z]{2,}|(^|\s)[A-Z](\s|$)", s): return None              # a description, not a name
    s = re.sub(r"\s+(I|II|III|IV|V)$", "", s)
    s = re.sub(r"sk$", "", s) if suffix == "Reservoir" else s
    full = " ".join(pre + [s] + ([suffix] if suffix and not s.endswith(suffix) else []))
    return NATURE_NAMES.get(full.lower(), full)
