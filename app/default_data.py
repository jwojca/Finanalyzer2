"""
Default categories and keywords for FinAnalazer2.
Called on first run when the categories table is empty.
"""
from app import database as db


def load_defaults():
    """Load default categories and keywords if the DB is empty."""
    cats = db.get_all_categories()
    if cats:
        return  # Already initialized

    # ── Top-level categories ──────────────────────────────────────────────────
    id_prevod = db.add_category("Převod", None, '#888888', is_transfer=True, is_income=False)
    id_prijem = db.add_category("Příjem", None, '#2ecc71', is_transfer=False, is_income=True)
    id_potraviny = db.add_category("Potraviny", None, '#e67e22')
    id_bydleni = db.add_category("Bydlení", None, '#3498db')
    id_doprava = db.add_category("Doprava", None, '#9b59b6')
    id_zdravi = db.add_category("Zdraví", None, '#e74c3c')
    id_zabava = db.add_category("Zábava a volný čas", None, '#f39c12')
    id_obleceni = db.add_category("Oblečení a obuv", None, '#1abc9c')
    id_elektronika = db.add_category("Elektronika a IT", None, '#34495e')
    id_deti = db.add_category("Děti", None, '#fd79a8')
    id_vzdelani = db.add_category("Vzdělání", None, '#6c5ce7')
    id_darky = db.add_category("Dárky a dary", None, '#e84393')
    id_ostatni = db.add_category("Ostatní", None, '#95a5a6')

    # ── Subcategories ─────────────────────────────────────────────────────────
    id_mzda = db.add_category("Mzda", id_prijem, '#27ae60', is_income=True)
    id_diety = db.add_category("Diety", id_prijem, '#2ecc71', is_income=True)
    id_bonus = db.add_category("Přeplatek/Bonus", id_prijem, '#55efc4', is_income=True)

    id_supermarket = db.add_category("Supermarkety", id_potraviny, '#e67e22')
    id_drogerie = db.add_category("Drogerie", id_potraviny, '#d35400')
    id_maso = db.add_category("Maso a lahůdky", id_potraviny, '#c0392b')
    id_restaurace = db.add_category("Restaurace a fast food", id_potraviny, '#e74c3c')

    id_najem = db.add_category("Nájem", id_bydleni, '#2980b9')
    id_energie = db.add_category("Energie", id_bydleni, '#3498db')
    id_internet = db.add_category("Internet a telefon", id_bydleni, '#1abc9c')
    id_pojistky = db.add_category("Pojistky", id_bydleni, '#16a085')
    id_vybaveni = db.add_category("Vybavení a opravy", id_bydleni, '#27ae60')

    id_phm = db.add_category("Pohonné hmoty", id_doprava, '#8e44ad')
    id_autoservis = db.add_category("Auto - servis a pojistky", id_doprava, '#9b59b6')
    id_hromadna = db.add_category("Hromadná doprava", id_doprava, '#a29bfe')

    id_lekarna = db.add_category("Lékárna", id_zdravi, '#e74c3c')
    id_lekar = db.add_category("Lékař", id_zdravi, '#c0392b')

    id_streaming = db.add_category("Streaming", id_zabava, '#f39c12')
    id_kino = db.add_category("Kino a kultura", id_zabava, '#e67e22')
    id_sport = db.add_category("Sport", id_zabava, '#d35400')
    id_cestovani = db.add_category("Cestování", id_zabava, '#fdcb6e')

    # ── Keywords ──────────────────────────────────────────────────────────────
    # Helper: add_keyword(keyword, category_id, field='all', priority=0)
    kw = db.add_keyword

    # Převod (transfers) – priority 10 so they dominate
    for word in [
        "PŘEVOD NA MSPOŘENÍ", "VKLAD NA CÍL", "PŘEVOD Z CÍLE",
        "ZRUŠENÍ CÍLE", "VLASTNÍ PŘEVOD", "POPLATEK ZA OKAMŽITOU",
        "PLATBA Z ÚČTU NA ÚČET", "MEZIBANKOVNÍ PŘEVOD",
    ]:
        kw(word, id_prevod, 'all', 10)

    # Splátka kreditu – also transfer
    kw("SPLÁTKA ÚVĚRU", id_prevod, 'all', 10)
    kw("SPLÁTKA KREDITU", id_prevod, 'all', 10)

    # Mzda
    kw("VÝPLATA", id_mzda, 'all', 5)
    kw("PLAT", id_mzda, 'description', 5)
    kw("MZDA", id_mzda, 'all', 5)
    kw("SALARY", id_mzda, 'all', 5)

    # Diety
    kw("DIETY", id_diety, 'message', 5)
    kw("DIETY", id_diety, 'description', 5)
    kw("CESTOVNÍ NÁHRADY", id_diety, 'all', 5)

    # Přeplatek/Bonus
    kw("PŘEPLATEK", id_bonus, 'all', 3)
    kw("VRÁCENÍ", id_bonus, 'all', 2)
    kw("REFUND", id_bonus, 'all', 2)

    # Supermarkety – priority 5
    for word in [
        "KAUFLAND", "LIDL", "TESCO", "ALBERT",
        "PENNY", "BILLA", "GLOBUS", "COOP",
        "HRUŠKA", "JMP S.A. BIEDRONKA", "FH POR-SAM BEATA",
        "BIEDRONKA", "MAKRO", "METRO", "SPAR",
    ]:
        kw(word, id_supermarket, 'all', 5)

    # Drogerie – priority 4 (PEPCO has lower, clothing has higher)
    for word in ["DM DROGERIE", "ROSSMANN", "TETA DROGERIE", "DM DROG"]:
        kw(word, id_drogerie, 'all', 5)
    kw("PEPCO", id_drogerie, 'all', 2)  # low priority – clothing wins

    # Maso a lahůdky
    for word in ["REZNIK", "ŘEZNÍK", "PRODEJNA MASA", "ŘEZNICKÁ",
                 "UZENINY", "LAHŮDKY", "LAHUDKY"]:
        kw(word, id_maso, 'all', 5)

    # Restaurace a fast food
    for word in [
        "RESTAURACE", "PIZZA", "KFC", "MCDONALD", "SUBWAY",
        "CHACHAR", "KEBAB", "BISTRO", "FAST FOOD",
        "GUTY", "QERKO", "SLIVKAFE", "BOKOFKA",
        "TANKOVNA", "SENK", "HOSPODA", "PIVNICE",
        "STEAK", "BURGER", "GRILL", "GRIL",
        "POTRAVINY EXPRES", "FRESHMARKET",
    ]:
        kw(word, id_restaurace, 'all', 5)

    # Nájem
    kw("ČAJKOVSKÉHO 2026", id_najem, 'message', 10)
    kw("NÁJEM", id_najem, 'message', 8)
    kw("NÁJEMNÉ", id_najem, 'message', 8)
    kw("NÁJEMNÉ", id_najem, 'description', 8)

    # Energie
    for word in [
        "MND ZÁLOHA ELEKTŘINA", "MND ZÁLOHA PLYN",
        "MND VYÚČTOVÁNÍ", "MND A.S.", "MND",
        "ČEZ", "EON", "E.ON", "PRE ", "INNOGY",
        "ZÁLOHA ELEKTŘINA", "ZÁLOHA PLYN", "ZÁLOHA NA ELEKTŘINU",
        "ZÁLOHA NA PLYN", "VYÚČTOVÁNÍ ENERGIÍ",
    ]:
        kw(word, id_energie, 'all', 5)

    # Internet a telefon
    for word in [
        "O2 CZECH REPUBLIC", "GOPAY * O2", "O2 INKASO",
        "O2 PRODEJNA", "O2 ", "T-MOBILE", "VODAFONE",
        "CETIN", "UPC ", "CABLE", "INTERNET",
    ]:
        kw(word, id_internet, 'all', 5)

    # Pojistky
    for word in [
        "KOOPERATIVA", "ALLIANZ", "UNIQA",
        "RBP ZDRAVOTNÍ POJIŠŤOVNA", "WWW.RBP",
        "POJIŠŤOVNA", "POJISTKA", "POJISTNÉ",
        "ČESKÁ POJIŠŤOVNA", "GENERALI",
    ]:
        kw(word, id_pojistky, 'all', 4)
    kw("RBP", id_pojistky, 'all', 4)

    # Vybavení a opravy
    for word in [
        "IKEA", "JYSK", "KIKA", "HORNBACH", "OBI",
        "BAUHAUS", "BAUMAX", "OPRAVA", "SERVIS SPOTŘEBIČŮ",
        "DOMESTOS", "ZÁCLONY",
    ]:
        kw(word, id_vybaveni, 'all', 4)

    # Pohonné hmoty
    for word in [
        "ORLEN", "CS EUROOIL", "STACJA PALIW",
        "BENZINA", "OMV", "MOL ", "ČERPACÍ STANICE",
        "CERPACI STANICE", "BENZIN", "NAFTA",
        "SHELL", "BP ", "LUKOIL",
    ]:
        kw(word, id_phm, 'all', 5)

    # Auto servis a pojistky
    for word in [
        "AUTOTECHNA", "AUTODILY", "AUTO DÍLY",
        "AUTOPOJISTENI", "STK", "PNEUSERVIS",
        "PNEU ", "AUTOSERVIS", "AUTOUMYVARNA",
        "DÁLNIČNÍ KUPÓN", "DALNICNI KUPON",
    ]:
        kw(word, id_autoservis, 'all', 5)
    kw("AUTOPOJISTENI", id_autoservis, 'message', 6)

    # Hromadná doprava
    for word in [
        "STUDENTAGENCY", "REGIOJET", "FLIXBUS", "FLIX ",
        "GOPAY *LEOEXPRESS", "LEOEXPRESS", "CD.CZ",
        "ČESKÉ DRÁHY", "CESKE DRAHY", "DPP",
        "RYANAIR", "FINNAIR", "WIZZAIR", "EASYJET",
        "WIZZ", "LOT ", "CSA ", "DPO ", "MHD ",
        "JÍZDNÉ", "JIZDNE",
    ]:
        kw(word, id_hromadna, 'all', 5)

    # Lékárna
    for word in [
        "LEKARNA", "LÉKÁRNA", "DR. MAX", "DR.MAX",
        "BENU LEKARNA", "BENU", "PHOENIX", "LLOYDS",
    ]:
        kw(word, id_lekarna, 'all', 5)

    # Lékař
    for word in [
        "MUDR", "MUDr", "VETERINARNI", "VETERINÁRNÍ",
        "OPTIVET", "HAPPYPET", "STOMATOL",
        "NEMOCNICE", "POLIKLINIKA", "AMBULANCE",
        "OPTIKA", "OČNÍ",
    ]:
        kw(word, id_lekar, 'all', 5)

    # Streaming
    for word in [
        "SPOTIFY", "NETFLIX", "TALKTV",
        "HEROHERO", "GOPAY *IPRIMA", "DISNEY+",
        "DISNEY PLUS", "HBO MAX", "HBOMAX",
        "APPLE TV", "YOUTUBE PREMIUM", "DAZN",
        "TWITCH", "PRIMEVIDEO",
    ]:
        kw(word, id_streaming, 'all', 5)
    kw("GOPAY *CINEMAWARE", id_streaming, 'all', 3)  # lower – kino wins

    # Kino a kultura
    for word in [
        "KINO ", "CINEMA", "CINEMAWARE",
        "GOOUT", "TICKETPORTAL", "ENIGOO",
        "DIVADLO", "MUZEUM", "GALERIE",
        "KONCERT", "FESTIVAL",
    ]:
        kw(word, id_kino, 'all', 5)
    kw("CINEMAWARE", id_kino, 'all', 6)  # override streaming for cinema

    # Sport
    for word in [
        "SPORTISIMO", "DECATHLON", "BOWLING",
        "MESTSKY BAZEN", "MĚSTSKÝ BAZÉN", "SKI AREAL", "SKI AREÁL",
        "STRONGGEAR", "ZOOZLIN", "GOLF",
        "FITNESS", "GYM ", "POSILOVNA",
        "SQUASH", "TENIS", "PLAVANI",
    ]:
        kw(word, id_sport, 'all', 5)

    # Cestování
    for word in [
        "AIRBNB", "HOTEL ", "BOOKING",
        "BKG*HOTEL", "APART.EU", "HOSTEL",
        "ZOO OSTRAVA", "ARCHEOPARK", "HRAD ",
        "TURISTIKA", "CAMPING",
    ]:
        kw(word, id_cestovani, 'all', 5)

    # Oblečení a obuv – higher priority PEPCO than drogerie
    for word in [
        "NEW YORKER", "CROPP", "SINSAY",
        "NKD", "LPP ", "VINTED", "BOLF",
        "ZARA", "H&M", "C&A", "RESERVED",
        "LODICKY DOKORAN", "DEICHMANN", "CCC ",
        "HUMANIC", "BAŤA", "BATA ",
        "OUTLET", "SECOND HAND",
    ]:
        kw(word, id_obleceni, 'all', 5)
    kw("PEPCO", id_obleceni, 'all', 4)  # slightly higher than drogerie

    # Elektronika a IT
    for word in [
        "ALZA", "ELECTROWORLD", "DATART",
        "PLANEO", "GM ELECTRONIC", "STEAMGAMES",
        "GOPAY *METALSHOP", "CZNIC", "CZDOM",
        "APPLE ", "MICROSOFT", "GOOGLE PLAY",
        "MALL.CZ", "CZC.CZ",
    ]:
        kw(word, id_elektronika, 'all', 5)

    # Děti
    for word in [
        "DĚTSKÉ", "DETSKE", "HRAČKY", "HRACKY",
        "BABY", "KOJENECKE", "KOJENEKÉ",
    ]:
        kw(word, id_deti, 'all', 5)
    kw("LODICKY DOKORAN", id_deti, 'all', 6)  # kids shoes store

    # Vzdělání
    for word in [
        "KNIHY DOBROVSKY", "LEVNE KNIHY", "LEVNÉ KNIHY",
        "KNIHOBOT", "GOPAY *UMIMEUSINAT", "UMIMEUSINAT",
        "KNIHKUPECTVI", "AKADEMIE", "ŠKOLNÉ",
        "KURZ ", "ŠKOLNÍ",
    ]:
        kw(word, id_vzdelani, 'all', 5)

    # Dárky (hard to auto-detect, just a few clues)
    for word in ["KYTKY", "KVĚTINY", "FLORIST", "DÁRKOVÝ POUKAZ"]:
        kw(word, id_darky, 'all', 3)

    # Ostatní – low priority catch-all
    for word in [
        "ACTION ", "TEDI ", "COOP TIP",
        "POHŘEBNÍ", "NOTÁŘ",
    ]:
        kw(word, id_ostatni, 'all', 2)
