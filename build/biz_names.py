"""Iradi names, chains, cuisines and prices for the businesses made by build/make_businesses.py.

Every name is invented: nothing is taken from the donor city's real businesses. The lore's own businesses and brands
(canon.md) come first: Talasbank and its 28 branches, the Transoxiana Microfinance Fund, NurGaz fuel, KFC Irad, the
five Talas eateries that deliver through Tulpar, the International Diplomatic Hotel. Chains not in the lore are kept
few and listed in INVENTED so the lore can pick them up.

Spelling follows the map's Iradi data: Latin with ch/sh/zh, ı, ö, ü (Köhne Diz, Juma Mechiti, Altyn Munara).
Russian forms are transliterated; English forms are what an English-language sign or guide would say.
"""
import hashlib, re

def h01(*xs):
    return int(hashlib.md5("|".join(map(str, xs)).encode()).hexdigest()[:12], 16) / 16 ** 12
def pick(seq, *key): return seq[int(h01(*key) * len(seq))]

# chains and brands the lore does not have yet (for the lore to adopt, or for the user to rename)
INVENTED = {
    "Bereke": "supermarket chain (bereke: plenty)",
    "Jıldız Market": "supermarket chain (jıldız: star)",
    "Shıpa": "pharmacy chain (shıpa: cure)",
    "Chüy Kommertsiyalık Banky": "commercial bank (Chuy Commercial Bank)",
    "Ak Bata Bank": "commercial bank",
}

# ---------- per-city flavour (set by make_businesses.py; the defaults are Talas) ----------
FLAVOR = {}
def fl(k, d): return FLAVOR.get(k, d)

# ---------- stems ----------
PEOPLE = ["Aibek", "Aigül", "Altynai", "Asel", "Azamat", "Baktygül", "Bermet", "Chynara", "Daniyar", "Elnura", "Ermek",
          "Gülnara", "Gülzat", "Jyldyz", "Kanat", "Kanykei", "Meerim", "Nurlan", "Nurbek", "Saltanat", "Samat", "Talant", "Tilek",
          "Ulan", "Zarina", "Yuhanna", "Mariyam", "Ilyas", "Dilnoza", "Farrukh", "Sherzod", "Zulfiya", "Rustam", "Timur", "Oksana",
          "Natasha", "Svetlana", "Vitaliy", "Sergei", "Larisa", "Marina", "Young-Ja", "Min-Su", "Kim", "Pak", "Lupita", "Rosario"]
WORDS = [("Altyn", "Gold"), ("Bereket", "Plenty"), ("Dostuk", "Friendship"), ("Jıldız", "Star"), ("Ay", "Moon"), ("Kün", "Sun"),
         ("Navat", "Navat"), ("Ak Bata", "Blessing"), ("Bulak", "Spring"), ("Tash", "Stone"), ("Jaz", "Spring"), ("Küz", "Autumn"),
         ("Bagym", "My Garden"), ("Gülzar", "Rose Garden"), ("Sayakat", "Journey"), ("Kerege", "Kerege"), ("Tündük", "Tündük"),
         ("Ordo", "Ordo"), ("Kök-Bel", "Kök-Bel"), ("Kara-Suu", "Kara-Suu"), ("Urmaral", "Urmaral"), ("Semiz", "Semiz"),
         ("Talas", "Talas"), ("Jibek Jolu", "Silk Road"), ("Samarkand", "Samarkand"), ("Bukhara", "Bukhara"), ("Kashkar", "Kashgar"),
         ("Sarchashma", "Sarchashma"), ("Misgaron", "Misgaron"), ("Shahr-i Kabud", "Shahr-i Kabud"), ("Alatoo", "Alatau"),
         ("Bayterek", "Poplar"), ("Archa", "Juniper"), ("Erkin", "Liberty"), ("Kut", "Fortune"), ("Merey", "Merey"), ("Nur", "Nur")]
RU_WORDS = ["Уют", "Встреча", "Огонёк", "Берёзка", "Ромашка", "Весна", "Радуга", "Удача", "Изюминка", "Каприз", "Восток", "Старый город",
            "Друзья", "Сказка", "Шанс", "Глобус", "Престиж", "Империя", "Достык"]


# ---------- transliteration Latin Iradi -> Cyrillic ----------
DI = [("shch", "щ"), ("ch", "ч"), ("sh", "ш"), ("zh", "ж"), ("kh", "х"), ("ts", "ц"), ("yu", "ю"), ("ya", "я"), ("yo", "ё"), ("ye", "е")]
MONO = {"a": "а", "b": "б", "c": "к", "d": "д", "e": "е", "f": "ф", "g": "г", "h": "х", "i": "и", "ı": "ы", "j": "ж", "k": "к", "l": "л",
        "m": "м", "n": "н", "ñ": "н", "o": "о", "ö": "о", "p": "п", "q": "к", "r": "р", "s": "с", "t": "т", "u": "у", "ü": "у", "v": "в",
        "w": "в", "x": "х", "y": "ы", "z": "з", "ç": "ч", "ş": "ш", "ä": "ә"}
def cyr(s):
    """lower-case Cyrillic for a Latin Iradi word"""
    out, i, low = [], 0, s.lower()
    while i < len(low):
        for a_, b_ in DI:
            if low.startswith(a_, i):
                out.append(b_); i += len(a_); break
        else:
            ch = low[i]; prev = low[i - 1] if i else ""
            if ch == "y" and (not prev or prev in "aeiouöüı") and i + 1 < len(low) and low[i + 1] in "aeiou": out.append("й")
            elif ch == "y" and prev in "aeiouöüı": out.append("й")
            elif ch == "e" and not prev.isalpha(): out.append("э")
            elif ch == "i" and prev in "aeouı": out.append("й")             # Aibek, Kanykei -> Айбек, Каныкей
            elif ch == "l" and prev == "ü" and (i + 1 == len(low) or low[i + 1] not in "aeiouöüı"): out.append("ль")   # Aigül -> Айгуль
            else: out.append(MONO.get(ch, ch))
            i += 1
    return "".join(out)
RU_FIXED = {"Young-Ja": "Ён Джа", "Min-Su": "Мин Су", "Kim": "Ким", "Pak": "Пак", "Lupita": "Лупита", "Rosario": "Росарио",
            "Natasha": "Наташа", "Svetlana": "Светлана", "Sergei": "Сергей", "Vitaliy": "Виталий", "Oksana": "Оксана", "Larisa": "Лариса",
            "Marina": "Марина", "Mariyam": "Марьям", "Ilyas": "Ильяс", "Daniyar": "Данияр"}
def cyr_name(s):
    if s in RU_FIXED: return RU_FIXED[s]
    # keep the capitalisation word by word
    return " ".join("-".join(cyr(p).capitalize() if p[:1].isupper() else cyr(p) for p in w.split("-")) for w in s.split(" "))


# ---------- cuisine ----------
CUISINE_MIX = [("iradi", 40), ("russian", 10), ("uzbek", 10), ("koryo", 8), ("chinese", 6), ("turkish", 6), ("georgian", 3),
               ("european", 6), ("pizza", 5), ("american", 4), ("mexican", 2)]
def cuisine_for(b, area):
    c = (b.get("cuisine") or "").lower()
    if area == "semiz" and h01(b["id"], "mx") < 0.75: return "mexican"
    if area == "expat" and h01(b["id"], "ex") < 0.4: return pick(["european", "american", "pizza", "sushi", "coffee", "steakhouse"], b["id"], "exk")
    if area == "base" and h01(b["id"], "us") < 0.45: return pick(["american", "steakhouse", "barbecue", "burger"], b["id"], "usk")
    m = {"regional": "iradi", "local": "iradi", "kyrgyz": "iradi", "kazakh": "iradi", "uzbek": "uzbek", "russian": "russian",
         "korean": "koryo", "chinese": "chinese", "turkish": "turkish", "kebab": "turkish", "georgian": "georgian", "italian": "european",
         "international": "european", "japanese": "sushi", "sushi": "sushi", "pizza": "pizza", "burger": "burger", "chicken": "chicken",
         "coffee_shop": "coffee", "dessert": "dessert", "indian": "indian", "asian": "chinese", "steak_house": "steakhouse", "tea": "tea"}
    if c in m: return m[c]
    if c in CUISINE_LABEL: return c
    mix = fl("cuisine_mix", CUISINE_MIX)
    tot = sum(w for _, w in mix); r = h01(b["id"], "cu") * tot
    for k, w in mix:
        r -= w
        if r < 0: return k
    return "iradi"

CUISINE_LABEL = {"iradi": ("Iradi", "Iradi", "ирадская кухня"), "russian": ("Russian", "Orus", "русская кухня"),
                 "uzbek": ("Uzbek", "Özbek", "узбекская кухня"), "koryo": ("Koryo-saram", "Koryo", "корё-сарам"),
                 "chinese": ("Chinese", "Kıtay", "китайская кухня"), "turkish": ("Turkish", "Türk", "турецкая кухня"),
                 "georgian": ("Georgian", "Gruzin", "грузинская кухня"), "european": ("European", "Evropa", "европейская кухня"),
                 "pizza": ("Pizza", "Pitstsa", "пицца"), "american": ("American", "Amerika", "американская кухня"),
                 "mexican": ("Mexican", "Meksika", "мексиканская кухня"), "steakhouse": ("Steakhouse", "Steykhaus", "стейк-хаус"),
                 "barbecue": ("Barbecue", "Barbekyu", "барбекю"), "burger": ("Burgers", "Burger", "бургеры"), "chicken": ("Chicken", "Tooh", "курица"),
                 "coffee": ("Coffee", "Kofe", "кофейня"), "dessert": ("Desserts", "Desert", "десерты"), "sushi": ("Sushi", "Sushi", "суши"),
                 "indian": ("Indian", "Indiya", "индийская кухня"), "tea": ("Tea", "Chay", "чай"), "shashlyk": ("Shashlyk", "Shashlık", "шашлык")}


# ---------- names by kind ----------
def stem(b, tag):
    """a name stem: (iradi, english, russian)"""
    r = h01(b["id"], tag); p_, ru_ = fl("people_share", 0.38), fl("ru_share", 0.15)
    if r < p_:
        n = pick(PEOPLE + fl("people_extra", []), b["id"], tag, "p"); return n, n, cyr_name(n)
    if r < 1 - ru_:
        ir, en = pick(WORDS + fl("words_extra", []), b["id"], tag, "w"); return ir, en, cyr_name(ir)
    ru = pick(RU_WORDS, b["id"], tag, "r"); return translit_ru(ru), translit_ru(ru), ru

RU_LAT = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "yo", "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l",
          "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh",
          "щ": "shch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya"}
def translit_ru(s):
    return "".join((RU_LAT.get(c.lower(), c).capitalize() if c.isupper() else RU_LAT.get(c, c)) for c in s)

MEX = ["El Charro", "La Colonia", "Los Compadres", "Guadalupe", "Don Chuy", "El Norteño", "La Güera", "Doña Lupe", "El Sinaloense",
       "Los Arcos", "La Michoacana", "El Rancho", "Las Palmas", "San Judas", "La Jefa"]
US = ["Prairie", "Big Sky", "Liberty", "Frontier", "Homestead", "Silverado", "Copperhead", "Red Barn", "Blue Ridge", "Eagle",
      "Cottonwood", "Mesa", "Sundown", "Crossroads", "Thunderbird"]
CN = ["Dunhuang", "Kaifeng", "Lanzhou", "Shanghai", "Harbin", "Xi'an", "Kashgar Noodle", "Dungan", "Hui Hui", "Lotus", "Bamboo", "Panda", "Silk Lantern", "Turfan", "Urumchi", "Changan", "Golden Dragon", "Jade Garden", "Red Lantern", "Peking"]
KR = ["Arirang", "Koryo", "Seoul", "Pusan", "Mugunghwa", "Hanok", "Ussuri", "Wonsan", "Chonan", "Kuksi House", "Morkovcha", "Hanbat", "Sorabol", "Chosŏn", "Vladivostok", "Nakhodka"]
TR = ["Istanbul", "Anadolu", "Bosfor", "Kapadokya", "Antalya", "Sultan", "Lale", "Konya", "Bursa", "Efes", "Galata", "Izmir", "Trabzon", "Ottoman", "Saray"]
GE = ["Tbilisi", "Kazbek", "Mtskheta", "Khachapuri House", "Suliko"]

RU_FIXED.update(dict(zip(CN, ["Дуньхуан", "Кайфын", "Ланьчжоу", "Шанхай", "Харбин", "Сиань", "Кашгарская лапша", "Дунган", "Хуэй-Хуэй", "Лотос", "Бамбук",
                              "Панда", "Шёлковый фонарь", "Турфан", "Урумчи", "Чанъань", "Золотой дракон", "Нефритовый сад", "Красный фонарь", "Пекин"])))
RU_FIXED.update(dict(zip(KR, ["Ариран", "Корё", "Сеул", "Пусан", "Мугунхва", "Ханок", "Уссури", "Вонсан", "Чхонан", "Кукси", "Морковча", "Ханбат",
                              "Сорабол", "Чосон", "Владивосток", "Находка"])))
RU_FIXED.update(dict(zip(TR, ["Стамбул", "Анадолу", "Босфор", "Каппадокия", "Анталья", "Султан", "Лале", "Конья", "Бурса", "Эфес", "Галата", "Измир",
                              "Трабзон", "Османлы", "Сарай"])))
RU_FIXED.update(dict(zip(GE, ["Тбилиси", "Казбек", "Мцхета", "Хачапурная", "Сулико"])))
RU_FIXED.update(dict(zip(MEX, ["Эль Чарро", "Ла Колония", "Лос Компадрес", "Гуадалупе", "Дон Чуй", "Эль Норteньо".replace("te", "те"), "Ла Гуэра",
                               "Донья Лупе", "Эль Синалоэнсе", "Лос Аркос", "Ла Мичоакана", "Эль Ранчо", "Лас Пальмас", "Сан-Худас", "Ла Хефа"])))
assert all(len(x) == len(set(x)) for x in (CN, KR, TR, GE, MEX))

def set_names(b, ir, en, ru):
    b["name"], b["name_ir"], b["name_en"], b["name_ru"] = ir, ir, en, ru


def name_food(b, area):
    k = b["kind"]; cu = b.get("cuisine")
    s_ir, s_en, s_ru = stem(b, "n")
    if k == "chaikhana":
        return set_names(b, f"Chaykhana {s_ir}", f"Chaikhana {s_en}", f"Чайхана «{s_ru}»")
    if cu == "mexican":
        n = pick(MEX, b["id"], "mx")
        kind = pick(["Taquería", "Cocina", "Taquería"], b["id"], "mxk") if k != "bakery" else "Tortillería" if b.get("sub") == "tortilleria" else "Panadería"
        return set_names(b, f"{kind} {n}", f"{kind} {n}", f"{'Такерия' if kind == 'Taquería' else 'Тортильерия' if kind == 'Tortillería' else 'Кухня' if kind == 'Cocina' else 'Панадерия'} «{cyr_name(n)}»")
    if cu in ("american", "steakhouse", "barbecue", "burger") or (k == "fast-food" and area == "base"):
        n = pick(US, b["id"], "us"); suf = {"steakhouse": "Steakhouse", "barbecue": "BBQ", "burger": "Burgers"}.get(cu, pick(["Diner", "Grill", "Café", "Diner"], b["id"], "usd"))
        return set_names(b, f"{n} {suf}", f"{n} {suf}", f"{n} {suf}")
    if k == "bakery":
        f_ = pick(["nan", "tandyr", "ru", "konditer"], b["id"], "bk")
        if f_ == "nan": return set_names(b, f"Nan {s_ir}", f"{s_en} Bread", f"Хлеб «{s_ru}»")
        if f_ == "tandyr": return set_names(b, f"Tandyr {s_ir}", f"{s_en} Tandyr", f"Тандыр «{s_ru}»")
        if f_ == "konditer": return set_names(b, f"Konditerskaya {s_ir}", f"{s_en} Patisserie", f"Кондитерская «{s_ru}»")
        return set_names(b, f"Pekarnya {s_ir}", f"{s_en} Bakery", f"Пекарня «{s_ru}»")
    if k == "bar":
        if h01(b["id"], "pub") < 0.4:
            n = pick(["The Quarter", "The Old Bridge", "The Foundry", "The Signal", "The Caravan", "The Notch", "The Lantern", "The Depot",
                      "The Rail", "The Copper Kettle", "The Bunker", "The Hangar"], b["id"], "pn")
            return set_names(b, n, n, n)
        return set_names(b, f"Bar {s_ir}", f"{s_en} Bar", f"Бар «{s_ru}»")
    if k == "fast-food":
        f_ = pick(["samsa", "shawarma", "lagman", "pizza", "doner", "chicken", "burger"], b["id"], "ff")
        if cu == "pizza": f_ = "pizza"
        if cu == "chicken": f_ = "chicken"
        lab = {"samsa": ("Samsa", "Samsa", "Самса"), "shawarma": ("Shaurma", "Shawarma", "Шаурма"), "lagman": ("Lagman-üy", "Lagman House", "Лагман-хаус"),
               "pizza": ("Pitstsa", "Pizza", "Пицца"), "doner": ("Döner", "Döner", "Дёнер"), "chicken": ("Tooh", "Chicken", "Курочка"),
               "burger": ("Burger", "Burger", "Бургер")}[f_]
        return set_names(b, f"{lab[0]} {s_ir}", f"{s_en} {lab[1]}", f"{lab[2]} «{s_ru}»")
    # restaurants and cafés
    if cu == "chinese":
        n = pick(CN, b["id"], "cn"); w = pick([("Restoran", "Restaurant", "Ресторан"), ("Kafe", "Café", "Кафе"), ("Ashkana", "Noodle House", "Лапшичная")], b["id"], "cnw")
        return set_names(b, f"{w[0]} {n}", f"{n} {w[1]}", f"{w[2]} «{cyr_name(n)}»")
    if cu == "koryo":
        n = pick(KR, b["id"], "kr"); w = pick([("Kafe", "Café", "Кафе"), ("Restoran", "Restaurant", "Ресторан")], b["id"], "krw")
        return set_names(b, f"{w[0]} {n}", f"{n} {w[1]}", f"{w[2]} «{cyr_name(n)}»")
    if cu == "turkish": n = pick(TR, b["id"], "tr"); return set_names(b, f"{n} Kebap", f"{n} Kebab", f"{cyr_name(n)} Кебаб")
    if cu == "georgian": n = pick(GE, b["id"], "ge"); return set_names(b, f"Restoran {n}", f"{n}", f"Ресторан «{cyr_name(n)}»")
    if cu == "pizza": return set_names(b, f"{s_ir} Pizza", f"{s_en} Pizza", f"Пицца «{s_ru}»")
    if cu == "sushi": return set_names(b, f"{s_ir} Sushi", f"{s_en} Sushi", f"Суши «{s_ru}»")
    if cu == "coffee":
        return set_names(b, f"{s_en} Coffee", f"{s_en} Coffee", f"{s_en} Coffee")
    if k == "cafe" and h01(b["id"], "stol") < fl("stolovaya", 0):
        b["sub_label"] = ("Canteen", "Stolovaya", "Столовая")
        if h01(b["id"], "stn") < 0.4:
            n = 1 + int(h01(b["id"], "stno") * 40); return set_names(b, f"{n}-Stolovaya", f"Canteen No. {n}", f"Столовая № {n}")
        return set_names(b, f"Stolovaya {s_ir}", f"{s_en} Canteen", f"Столовая «{s_ru}»")
    if k == "restaurant" and h01(b["id"], "toy") < fl("banquet", 0):
        b["sub_label"] = ("Banquet hall", "Toikana", "Банкетный зал")
        return set_names(b, f"Toikana {s_ir}", f"{s_en} Banquet Hall", f"Банкетный зал «{s_ru}»")
    if k == "cafe": return set_names(b, f"Kafe {s_ir}", f"{s_en} Café", f"Кафе «{s_ru}»")
    return set_names(b, f"Restoran {s_ir}", f"{s_en} Restaurant", f"Ресторан «{s_ru}»")


SHOP_SUB = {   # sub-type: (iradi word, english word, russian word)
    "clothes": ("Kiyim", "Clothing", "Одежда"), "shoes": ("But kiyim", "Shoes", "Обувь"), "mobile_phone": ("Mobil", "Mobile", "Мобильные телефоны"),
    "electronics": ("Elektronika", "Electronics", "Электроника"), "computer": ("Kompyuter", "Computers", "Компьютеры"),
    "hardware": ("Kurulush", "Hardware", "Стройматериалы"), "doityourself": ("Kurulush", "Building Supplies", "Стройматериалы"),
    "furniture": ("Mebel", "Furniture", "Мебель"), "florist": ("Gülder", "Flowers", "Цветы"), "books": ("Kitepkana", "Books", "Книги"),
    "stationery": ("Kantstovarlar", "Stationery", "Канцтовары"), "cosmetics": ("Kosmetika", "Cosmetics", "Косметика"),
    "jewelry": ("Zerger", "Jewellery", "Ювелирный"), "gift": ("Sovgat", "Gifts", "Подарки"), "toys": ("Oyunchuktar", "Toys", "Игрушки"),
    "sports": ("Sport", "Sports", "Спорттовары"), "fabric": ("Kezdeme", "Fabrics", "Ткани"), "carpet": ("Kilem", "Carpets", "Ковры"),
    "car_parts": ("Avtobölüktör", "Auto Parts", "Автозапчасти"), "tyres": ("Shina", "Tyres", "Шины"), "optician": ("Optika", "Optician", "Оптика"),
    "chemist": ("Üy-turmush", "Household", "Бытовая химия"), "houseware": ("Idish-ayak", "Housewares", "Посуда"),
    "hairdresser": ("Chach tarach", "Hair Salon", "Парикмахерская"), "beauty": ("Suluuluk salonu", "Beauty Salon", "Салон красоты"),
    "car_repair": ("Avtoservis", "Car Service", "Автосервис"), "variety_store": ("Bardık nerse", "Variety Store", "Всё для дома"),
    "bag": ("Sumkalar", "Bags", "Сумки"), "boutique": ("Butik", "Boutique", "Бутик"), "baby_goods": ("Balalar", "Baby Goods", "Детские товары"),
    "pet": ("Zoo", "Pet Shop", "Зоомагазин"), "hifi": ("Audio", "Audio", "Аудио"), "appliance": ("Tehnika", "Appliances", "Бытовая техника"),
    "paint": ("Bodo", "Paints", "Краски"), "religious": ("Shamdal jana ikona", "Icons & Candles", "Иконы и свечи"),
    "felt": ("Shyrdak", "Shyrdak Felt", "Шырдаки"), "saddlery": ("Eerchi", "Saddlery", "Сёдла"), "leather": ("Teri buyumdar", "Leather Goods", "Изделия из кожи"),
    "souvenir": ("Estelikter", "Souvenirs", "Сувениры"), "radio": ("Radio-tehnika", "Radio & Parts", "Радиотовары"), "kitchen": ("Ashkana", "Kitchens", "Кухни"), "watches": ("Saattar", "Watches", "Часы"),
}
GROC_SUB = {"greengrocer": ("Jemish-jashılcha", "Fruit & Veg", "Овощи-фрукты"), "butcher": ("Et dükönü", "Butcher", "Мясо"),
            "dairy": ("Süt azıktarı", "Dairy", "Молочные продукты"), "spices": ("Kanttuu jana jıttuu", "Spices", "Специи"),
            "tea": ("Chay", "Tea", "Чай"), "alcohol": ("Ichimdikter", "Drinks", "Напитки"), "beverages": ("Ichimdikter", "Drinks", "Напитки"),
            "seafood": ("Balık", "Fish", "Рыба"), "deli": ("Delikates", "Delicatessen", "Деликатесы")}

def name_shop(b, area):
    k, sub = b["kind"], b.get("sub")
    s_ir, s_en, s_ru = stem(b, "n")
    if k == "supermarket":
        r = h01(b["id"], "chain")
        c1, c2 = fl("chains", (0.38, 0.24))
        if r < c1: return set_names(b, "Bereke", "Bereke Supermarket", "Береке")
        if r < c1 + c2: return set_names(b, "Jıldız Market", "Jıldız Market", "Жылдыз Маркет")
        return set_names(b, f"Supermarket {s_ir}", f"{s_en} Supermarket", f"Супермаркет «{s_ru}»")
    if k == "grocery":
        if area == "semiz" and h01(b["id"], "abar") < 0.6:
            n = pick(MEX, b["id"], "abn"); return set_names(b, f"Abarrotes {n}", f"Abarrotes {n}", f"Продукты «{cyr_name(n)}»")
        if sub in GROC_SUB:
            w = GROC_SUB[sub]; return set_names(b, f"{w[0]} · {s_ir}", f"{s_en} {w[1]}", f"{w[2]} «{s_ru}»")
        f_ = h01(b["id"], "gf")
        if f_ < 0.45: return set_names(b, f"{fl('shop_word', 'Dükön')} {s_ir}", f"{s_en} Store", f"Магазин «{s_ru}»")
        if f_ < 0.8: return set_names(b, f"Azık-tülük {s_ir}", f"{s_en} Groceries", f"Продукты «{s_ru}»")
        return set_names(b, f"Mini-market {s_ir}", f"{s_en} Mini-Market", f"Минимаркет «{s_ru}»")
    if k == "pharmacy":
        r = h01(b["id"], "ph")
        if r < 0.2: return set_names(b, "Shıpa Dariykana", "Shıpa Pharmacy", "Аптека «Шыпа»")
        if r < 0.4:
            n = 1 + int(h01(b["id"], "phn") * 60); return set_names(b, f"{n}-Dariykana", f"Pharmacy No. {n}", f"Аптека № {n}")
        return set_names(b, f"Dariykana {s_ir}", f"{s_en} Pharmacy", f"Аптека «{s_ru}»")
    if k == "mall":
        return set_names(b, f"{s_ir} Sooda borboru", f"{s_en} Plaza", f"ТЦ «{s_ru}»")
    if k == "market":
        return set_names(b, f"{s_ir} bazarı", f"{s_en} Market", f"Рынок «{s_ru}»")
    if k == "shop" and area == "semiz" and sub == "car_repair":
        n = pick(MEX, b["id"], "tal"); return set_names(b, f"Taller {n}", f"Taller {n} (car repair)", f"Автосервис «{cyr_name(n)}»")
    if k == "shop":
        w = SHOP_SUB.get(sub, ("Düköön", "Shop", "Магазин"))
        return set_names(b, f"{w[0]} · {s_ir}", f"{s_en} {w[1]}", f"{w[2]} «{s_ru}»")


def name_stay(b, area):
    s_ir, s_en, s_ru = stem(b, "n")
    if b["kind"] == "hotel":
        return set_names(b, f"Meymankana {s_ir}", f"Hotel {s_en}", f"Гостиница «{s_ru}»")
    if b["kind"] == "hostel":
        return set_names(b, f"{s_en} Hostel", f"{s_en} Hostel", f"Хостел «{s_ru}»")
    return set_names(b, f"Konok üy {s_ir}", f"{s_en} Guest House", f"Гостевой дом «{s_ru}»")


PRICE = {  # kind -> (level, som per person) choices
    "chaikhana": [(1, "40–90 som")], "cafe": [(1, "60–150 som"), (2, "120–250 som")], "fast-food": [(1, "40–120 som")],
    "restaurant": [(2, "150–350 som"), (2, "200–400 som"), (3, "350–700 som"), (4, "700–1,500 som")], "bar": [(2, "150–400 som")],
    "bakery": [(1, None)], "hotel": [(3, None), (2, None), (4, None)], "hostel": [(1, None)], "guesthouse": [(1, None), (2, None)],
}


def dress(b, city, area=None):
    k = b["kind"]
    if k in ("restaurant", "cafe", "chaikhana", "fast-food", "bar", "bakery"):
        if k in ("restaurant", "cafe", "fast-food"): b["cuisine"] = cuisine_for(b, area)
        elif b.get("cuisine") != "mexican": b.pop("cuisine", None)
        name_food(b, area)
    elif k in ("hotel", "hostel", "guesthouse"):
        name_stay(b, area)
    elif k == "bank":
        if b.get("sub") == "bureau_de_change":
            s_ir, s_en, s_ru = stem(b, "n"); set_names(b, f"Valyuta almashuu {s_ir}", f"{s_en} Exchange", f"Обмен валют «{s_ru}»")
        else:
            set_names(b, "Talasbank", "Talasbank", "Таласбанк")      # re-branded in make_businesses: only 28 branches are Talasbank
    elif k == "fuel":
        if h01(b["id"], "ng") < 0.6: set_names(b, "NurGaz", "NurGaz", "НурГаз")
        else:
            s_ir, s_en, s_ru = stem(b, "n"); set_names(b, f"AZS {s_ir}", f"{s_en} Filling Station", f"АЗС «{s_ru}»")
    else:
        name_shop(b, area)
    pr = PRICE.get(k)
    if pr:
        lvl, txt = pick(pr, b["id"], "pr")
        if k == "hotel" and b.get("stars"):
            try: lvl = max(1, min(4, int(float(b["stars"])) - 1))
            except ValueError: pass
        b["price_level"] = lvl
        if txt: b["price"] = txt
    sub = b.get("sub")
    if b["kind"] == "shop" and sub in SHOP_SUB: w = SHOP_SUB[sub]; b["sub_label"] = (w[1], w[0], w[2])
    elif b["kind"] == "grocery" and sub in GROC_SUB: w = GROC_SUB[sub]; b["sub_label"] = (w[1], w[0], w[2])
    elif b["kind"] == "bank" and sub == "bureau_de_change": b["sub_label"] = ("Currency exchange", "Valyuta almashuu", "Обмен валют")
    if b.get("cuisine"):
        b["cuisine_label"] = CUISINE_LABEL.get(b["cuisine"], (b["cuisine"].title(),) * 2 + (b["cuisine"],))
