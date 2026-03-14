"""
One-time script: pre-fill 'note' for well-known keywords in the DB.
Run once after adding the note column.
"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from app import database as db

NOTES = {
    # Restaurace a fast food
    "KFC": "Světový fast food řetězec Kentucky Fried Chicken",
    "MCDONALD": "Světový fast food řetězec McDonald's",
    "SUBWAY": "Fast food řetězec se sendviči",
    "BURGER": "Fast food – burgery",
    "PIZZA": "Pizzerie / rozvoz pizzy",
    "KEBAB": "Kebab restaurace",
    "BISTRO": "Bistro / rychlé občerstvení",
    "RESTAURACE": "Obecné klíčové slovo pro restaurace",
    "SLIVKAFE": "Kavárna Slivkafé",
    "CHACHAR": "Restaurace Chachar",
    "POPEYES": "Fast food řetězec Popeyes",
    "QERKO": "Platební aplikace Qerko v restauracích",
    "FRESHMARKET": "Fresh Market – bistro / kavárna",

    # Supermarkety
    "TESCO": "Britský supermarketový řetězec",
    "KAUFLAND": "Německý hypermarket Kaufland",
    "LIDL": "Německý diskontní supermarket",
    "ALBERT": "Supermarketový řetězec Albert",
    "BILLA": "Supermarketový řetězec Billa",
    "PENNY": "Diskontní supermarketový řetězec Penny",
    "GLOBUS": "Hypermarket Globus",
    "HRUŠKA": "Česká síť prodejen Hruška",
    "MAKRO": "Velkoobchodní řetězec Makro",
    "COOP": "Spotřební družstvo COOP",
    "SPAR": "Mezinárodní supermarketový řetězec Spar",
    "BIEDRONKA": "Polský diskontní supermarket Biedronka",

    # Lékárna
    "BENU": "Řetězec lékáren Benu",
    "DR. MAX": "Řetězec lékáren Dr. Max",
    "DR.MAX": "Řetězec lékáren Dr. Max",
    "LEKARNA": "Obecné klíčové slovo pro lékárny",
    "LÉKÁRNA": "Obecné klíčové slovo pro lékárny",
    "PHOENIX": "Distributor léčiv Phoenix",
    "LLOYDS": "Lékárna Lloyds",

    # Streaming
    "NETFLIX": "Streamovací platforma Netflix",
    "SPOTIFY": "Hudební streamovací platforma Spotify",
    "DISNEY PLUS": "Streamovací platforma Disney+",
    "DISNEY+": "Streamovací platforma Disney+",
    "HBO MAX": "Streamovací platforma HBO Max",
    "HBOMAX": "Streamovací platforma HBO Max",
    "APPLE TV": "Streamovací platforma Apple TV+",
    "YOUTUBE PREMIUM": "Prémiová verze YouTube bez reklam",
    "TWITCH": "Platforma pro streamování hraní her",
    "DAZN": "Sportovní streamovací platforma DAZN",
    "PRIMEVIDEO": "Streamovací platforma Amazon Prime Video",
    "TALKTV": "Česká streamovací platforma TalkTV",
    "HEROHERO": "Česká platforma pro podporu tvůrců obsahu",

    # Elektronika a IT
    "ALZA": "Největší e-shop s elektronikou v ČR",
    "DATART": "Řetězec prodejen elektroniky Datart",
    "MALL.CZ": "Český e-shop Mall.cz",
    "PLANEO": "Prodejna elektroniky Planeo",
    "ELECTROWORLD": "Prodejna elektroniky Electroworld",
    "MICROSOFT": "Americká technologická společnost Microsoft",
    "GOOGLE PLAY": "Obchod s aplikacemi Google Play",
    "APPLE ": "Americká technologická společnost Apple",
    "STEAMGAMES": "Herní platforma Steam (PC hry)",
    "CZC.CZ": "Český e-shop s elektronikou CZC.cz",
    "GM ELECTRONIC": "Součástky a elektronika GM Electronic",

    # Oblečení a obuv
    "ZARA": "Španělský módní řetězec Zara",
    "H&M": "Švédský módní řetězec H&M",
    "RESERVED": "Polský módní řetězec Reserved",
    "SINSAY": "Módní řetězec Sinsay",
    "DEICHMANN": "Řetězec prodejen obuvi Deichmann",
    "HUMANIC": "Řetězec prodejen obuvi Humanic",
    "NEW YORKER": "Módní řetězec New Yorker",
    "BATA ": "Český obuvní řetězec Baťa",
    "BAŤA": "Český obuvní řetězec Baťa",
    "VINTED": "Online second-hand platforma Vinted",
    "C&A": "Módní řetězec C&A",

    # Pohonné hmoty
    "BENZINA": "Česká síť čerpacích stanic Benzina",
    "SHELL": "Mezinárodní síť čerpacích stanic Shell",
    "OMV": "Mezinárodní síť čerpacích stanic OMV",
    "ORLEN": "Polská síť čerpacích stanic Orlen",
    "MOL ": "Maďarská síť čerpacích stanic MOL",
    "LUKOIL": "Ruská síť čerpacích stanic Lukoil",
    "CS EUROOIL": "Česká síť čerpacích stanic Eurooil",
    "NAFTA": "Pohonná hmota – nafta",
    "BENZIN": "Pohonná hmota – benzín",

    # Hromadná doprava
    "ČESKÉ DRÁHY": "Národní železniční dopravce České dráhy",
    "CESKE DRAHY": "Národní železniční dopravce České dráhy",
    "LEOEXPRESS": "Soukromý vlakový dopravce Leo Express",
    "REGIOJET": "Soukromý autobusový a vlakový dopravce RegioJet",
    "FLIXBUS": "Evropský autobusový dopravce FlixBus",
    "RYANAIR": "Irský nízkonákladový letecký dopravce Ryanair",
    "WIZZAIR": "Maďarský nízkonákladový letecký dopravce Wizz Air",
    "EASYJET": "Britský nízkonákladový letecký dopravce EasyJet",
    "FINNAIR": "Finský národní letecký dopravce Finnair",
    "STUDENTAGENCY": "Dopravce Student Agency / RegioJet",
    "AIRBNB": "Platforma pro krátkodobý pronájem ubytování Airbnb",
    "BOOKING": "Platforma pro rezervaci hotelů Booking.com",
    "HOTEL ": "Ubytování v hotelu",

    # Internet a telefon
    "O2 ": "Český telekomunikační operátor O2",
    "O2 CZECH REPUBLIC": "Český telekomunikační operátor O2",
    "T-MOBILE": "Mobilní operátor T-Mobile",
    "VODAFONE": "Mobilní operátor Vodafone",
    "CETIN": "Česká telekomunikační infrastruktura CETIN",
    "UPC ": "Kabelový operátor UPC",

    # Energie
    "ČEZ": "Největší český energetický podnik ČEZ",
    "E.ON": "Energetická společnost E.ON",
    "MND": "Energetická společnost MND",
    "INNOGY": "Energetická společnost innogy",

    # Sport
    "DECATHLON": "Mezinárodní síť prodejen sportovního zboží",
    "SPORTISIMO": "Česká prodejna sportovního zboží Sportisimo",
    "STRONGGEAR": "Fitness vybavení StrongGear",
    "FITNESS": "Fitness centrum",
    "GYM ": "Posilovna / fitness centrum",

    # Kino a kultura
    "KINO ": "Kino – vstupenky na filmy",
    "CINEMA": "Kino / kino vstupenky",
    "DIVADLO": "Divadelní představení",
    "MUZEUM": "Muzeum – vstupné",
    "TICKETPORTAL": "Prodejce vstupenek Ticketportal",
    "GOOUT": "Platforma pro prodej vstupenek GoOut",

    # Drogerie
    "ROSSMANN": "Drogistický řetězec Rossmann",
    "DM DROG": "Drogistický řetězec DM",
    "DM DROGERIE": "Drogistický řetězec DM",
    "TETA DROGERIE": "Česká drogerie Teta",

    # Pojistky
    "ALLIANZ": "Pojišťovna Allianz",
    "GENERALI": "Pojišťovna Generali",
    "KOOPERATIVA": "Pojišťovna Kooperativa",
    "UNIQA": "Pojišťovna UNIQA",
    "ČESKÁ POJIŠŤOVNA": "Největší česká pojišťovna",
    "RBP": "Revírní bratrská pokladna – zdravotní pojišťovna",
    "RBP ZDRAVOTNÍ POJIŠŤOVNA": "Revírní bratrská pokladna",
    "WWW.RBP": "Revírní bratrská pokladna – platba online",

    # Vybavení a opravy
    "IKEA": "Švédský nábytkový řetězec IKEA",
    "HORNBACH": "Německý řetězec hobby marketů Hornbach",
    "OBI": "Řetězec hobby marketů OBI",
    "BAUHAUS": "Řetězec hobby marketů Bauhaus",
    "JYSK": "Dánský nábytkový řetězec JYSK",
    "KIKA": "Nábytkový řetězec Kika",

    # Mzda
    "VÝPLATA": "Výplata mzdy / platu",
    "MZDA": "Výplata mzdy",
    "SALARY": "Salary – výplata (anglicky)",

    # Výběry
    "VÝBĚR Z BANKOMATU": "Výběr hotovosti z bankomatu",

    # Převody
    "VLASTNÍ PŘEVOD": "Interní převod mezi vlastními účty",

    # Revolut
    "REVOLUT": "Britský digitální neobank Revolut",

    # Přeplatek
    "PŘEPLATEK": "Přeplatek / vrácení peněz",
    "VRÁCENÍ": "Vrácení platby / refundace",
    "REFUND": "Refundace / vrácení platby (anglicky)",

    # Cestování
    "ARCHEOPARK": "Archeopark Chotěbuz – muzeum v přírodě",
    "ZOO OSTRAVA": "Zoologická zahrada Ostrava",

    # Vzdělání
    "UMIMEUSINAT": "Vzdělávací platforma Umíme učit se",
    "AKADEMIE": "Vzdělávací kurz / akademie",
    "ŠKOLNÉ": "Školné – poplatek za vzdělání",

    # Dárky
    "KVĚTINY": "Floristika / kytice",
    "DÁRKOVÝ POUKAZ": "Dárkový poukaz / voucher",

    # Děti
    "BABY": "Zboží pro miminka",
    "HRAČKY": "Hračky pro děti",
    "HRACKY": "Hračky pro děti",

    # Nájem
    "NÁJEM": "Platba nájemného",
    "NÁJEMNÉ": "Platba nájemného",
}


def main():
    db.init_db()
    keywords = db.get_keywords()
    updated = 0
    skipped = 0

    with db.get_conn() as conn:
        for kw in keywords:
            kw_upper = kw['keyword'].strip().upper()
            # Try exact match first, then prefix match
            note = None
            for key, val in NOTES.items():
                if kw_upper == key.upper().strip():
                    note = val
                    break
            if note is None:
                for key, val in NOTES.items():
                    if kw_upper.startswith(key.upper().strip()):
                        note = val
                        break

            if note and not kw['note']:
                conn.execute(
                    "UPDATE keywords SET note=? WHERE id=?",
                    (note, kw['id'])
                )
                updated += 1
            else:
                skipped += 1

    print(f"Hotovo: aktualizováno {updated} poznámek, přeskočeno {skipped}")


if __name__ == "__main__":
    main()
