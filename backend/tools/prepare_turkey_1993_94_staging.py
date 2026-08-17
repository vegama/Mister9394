from __future__ import annotations

"""Materialise the verified 1993-94 Turkish top-flight roster staging.

Rows are transcribed from the BDFutbol 1993-94 squad pages already pinned in
``bel_tur_rus_1993_94_league_foundations.json``.  We intentionally stage the
full available season roster per club. Eighteen is only the minimum playability
floor and must never be used as a truncation target. No filler players are invented.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data" / "football9394"
FOUNDATION = DATA / "bel_tur_rus_1993_94_league_foundations.json"
OUT = DATA / "turkey_1993_94_roster_staging.json"


def r(name: str, age: int, apps: int, starts: int, minutes: int, goals: int, *, hint: str | None = None):
    row = {
        "bdfutbol_name": name,
        "age_1993_94": age,
        "appearances": apps,
        "starts": starts,
        "minutes": minutes,
        "goals": goals,
        "core_18_candidate": True,
    }
    if hint:
        row["identity_hint"] = hint
    return row


ROSTERS = {
    "Galatasaray": [
        r("Hayrettin",30,30,30,2700,-28), r("Stumpf",32,18,18,1551,0), r("Korkmaz",22,20,16,1390,1),
        r("Bülent",25,30,30,2700,1), r("Hamzaoğlu",23,27,27,2412,4), r("Suat",26,27,27,2309,8),
        r("Tugay",23,26,26,2257,10), r("Tepekule",25,26,22,2061,0), r("Götz",31,23,22,2005,5),
        r("Şükür",22,27,27,2428,16), r("Erdem",21,26,24,2040,9), r("Boloğlu",29,0,0,0,0),
        r("Tütüneker",30,18,15,1278,2), r("Ljung",27,15,14,1188,2), r("Keser",32,16,7,632,2),
        r("Türkyılmaz",26,12,9,783,4), r("Bulut",24,0,0,0,0), r("Kocabey",19,13,4,525,0),
    ],
    "Fenerbahçe": [
        r("İpekoğlu",32,30,30,2700,-26), r("Yağcıoğlu",27,27,27,2329,2), r("Wagenhaus",29,18,18,1613,1),
        r("Aşık",18,22,22,1838,0), r("Uche",26,14,14,1260,2), r("Oğuz",30,30,30,2685,5),
        r("Tayfur",23,29,29,2600,1), r("Müjdat",32,27,24,2165,0), r("Nielsen",25,19,19,1665,1),
        r("Uygun",22,30,30,2631,22), r("Çolak",26,29,29,2545,14), r("Dağdelen",23,0,0,0,0),
        r("Kocaman",28,17,14,1307,14), r("Sentürk",23,20,8,945,4), r("Kanburoğlu",26,14,11,967,0),
        r("Alp",24,15,10,922,1), r("Taşkıran",19,12,1,305,0), r("Yuvakuran",30,6,6,540,0),
    ],
    "Trabzonspor": [
        r("Silin",28,15,15,1344,-9), r("Ercan",22,29,29,2502,1), r("Aslan",26,30,28,2583,1),
        r("Serdar",31,27,27,2406,1), r("Ogün",24,25,25,2115,0), r("Çıkırıkçı",26,29,29,2508,9),
        r("Karaman",27,22,22,1871,5), r("Kafkas",25,26,21,1913,0), r("Mandıralı",25,27,27,2176,15),
        r("Arveladze",20,18,18,1592,15,hint="Shota Arveladze"), r("Atila",27,21,17,1492,4),
        r("Grischko",32,13,13,1170,-16), r("Soner",25,23,13,1326,0), r("Çelik",27,20,12,1166,1),
        r("Kaynak",23,18,9,845,2), r("Arveladze",20,15,11,1099,8,hint="Archil Arveladze"),
        r("Tümkaya",22,2,2,180,-3), r("Özköylü",22,7,4,366,0),
    ],
    "Beşiktaş": [
        r("Öğer",33,22,22,1980,-23), r("Çetin",28,18,17,1486,0), r("Topçu",23,28,28,2421,0),
        r("Günçar",23,29,29,2610,0), r("Keskin",27,25,25,2223,0), r("Çalımbay",30,29,29,2610,1),
        r("Özdilek",27,25,24,2151,9), r("Madida",27,23,23,2046,4), r("Uçar",30,26,22,1900,15),
        r("Oktay",18,27,20,1841,10), r("Nartallo",21,20,18,1622,10), r("Kurtulmuş",26,8,8,720,-7),
        r("Metin",29,22,17,1524,1), r("Yalçın",21,20,18,1581,6), r("Alpay",20,11,9,698,0),
        r("Uzun",20,8,7,600,1), r("Akbulut",33,7,5,423,0), r("Tokaç",20,11,1,221,0),
    ],
    "Samsunspor": [
        r("Aydın",27,19,19,1710,-21), r("Arslan",24,29,28,2454,0), r("Koloğlu",25,27,27,2408,1),
        r("Çıkla",26,27,26,2365,2), r("Korkmaz",24,21,19,1662,1,hint="Samsunspor Korkmaz A"),
        r("Timofte",26,26,26,2252,6), r("Akyol",24,22,19,1663,4), r("Gürsu",22,23,17,1447,0),
        r("Sağlam",24,29,29,2596,17), r("Kubat",24,20,15,1451,4),
        r("Korkmaz",24,21,14,1292,4,hint="Samsunspor Korkmaz B"), r("Aslan",26,11,11,984,-23),
        r("İsa",24,15,13,1139,0), r("Korkmaz",21,14,11,1049,0), r("Constantin",24,13,11,812,4),
        r("Cheregi",26,13,10,849,0), r("İlhan",25,0,0,0,0), r("Aykut",18,13,5,646,6),
    ],
    "Kocaelispor": [
        r("Omerović",32,30,30,2700,-45), r("Mirković",27,29,29,2517,3), r("Kuzmanovski",31,29,29,2610,1),
        r("Çakır",26,24,24,2037,1), r("Usta",28,12,10,816,0), r("Akgün",25,24,22,1824,2),
        r("Uzun",24,22,20,1825,1), r("Bacacı",25,24,18,1775,5), r("Birol",30,22,18,1642,3),
        r("Sancaklı",27,30,30,2700,18), r("Kara",21,28,28,2520,4), r("Boğuşlu",31,0,0,0,0),
        r("Gürbüztürk",27,20,18,1662,1), r("Yiğit",27,21,14,1292,1), r("Zeki",25,18,11,1061,0),
        r("Kıldıran",24,14,10,709,1), r("Arslan",18,10,7,687,0), r("Yılmaz",24,9,6,476,1),
    ],
    "Gençlerbirliği": [
        r("Gültang",21,24,24,2160,-40), r("Sözeri",27,29,29,2608,3), r("Penbe",21,26,25,2226,2),
        r("Zafer",22,27,27,2420,3), r("Taşkın",21,26,25,2180,0), r("Diyadin",25,28,28,2280,2),
        r("Moshoeu",28,27,27,2383,6), r("Özdemir",25,30,26,2373,4), r("Coşkun",21,28,25,2116,1),
        r("N'Gole",23,30,30,2700,19), r("Şimşek",24,26,15,1276,6), r("Šimunić",23,6,6,540,-11),
        r("Ace Khuse",30,19,17,1480,1), r("Çağdaş",26,20,14,1450,1), r("Işık",23,13,5,681,3),
        r("Daşgün",20,8,2,279,0), r("İsmailoğlu",29,0,0,0,0), r("Kara",21,2,2,145,0),
    ],
    "Gaziantepspor": [
        r("Akçevre",26,28,28,2505,-49), r("Okay",24,27,27,2387,3), r("Kumbasar",26,24,24,2092,0),
        r("Komphela",26,24,24,2160,1), r("Uçar",29,21,20,1616,2), r("Fidan",27,24,24,2013,1),
        r("Özer",24,24,20,1918,1), r("Sönmez",27,17,17,1530,0), r("Çelik",25,27,27,2423,13),
        r("Bolić",22,26,26,2280,11), r("Monteiro",27,26,26,2278,4), r("Bilir",27,3,2,171,-5),
        r("Toptaş",21,21,15,1326,2), r("Barut",28,15,13,1073,0), r("Karaçam",27,16,9,837,3),
        r("Özer",19,13,9,815,4,hint="Gaziantepspor Özer 19"), r("Moloi",25,15,6,743,1), r("Yungul",20,9,6,459,0),
    ],
    "Bursaspor": [
        r("Ganchev",28,23,23,2064,-28), r("Şen",27,28,28,2474,1), r("Okuroğlu",22,26,26,2302,1),
        r("Örnek",28,24,22,1997,0), r("Vatansever",24,24,19,1694,2), r("Şengül",25,23,19,1738,0),
        r("Tunahan",26,27,25,1990,3), r("Velioğlu",21,23,19,1804,1), r("Pingel",29,27,27,2390,12),
        r("Sørloth",31,25,20,1775,5), r("Durmuş",23,13,13,990,0), r("Nevzat",28,7,7,630,-11),
        r("Uzgur",26,21,19,1730,1), r("Balkanlı",28,18,18,1566,0), r("Gündüz",27,16,16,1440,0),
        r("Evke",28,15,13,1028,0), r("Kılıç",21,1,0,5,0), r("Sofuoğlu",28,8,4,365,0),
    ],
    "Altay": [
        r("Göymen",26,23,23,2070,-32), r("Üstündağ",26,27,26,2319,1), r("İkizoğlu",29,26,26,2294,1),
        r("Akuygur",26,22,17,1552,1), r("Kırtoğlu",22,25,25,2193,1), r("Karapınar",26,26,20,1780,3),
        r("Suna",28,20,20,1790,0), r("Kayalar",23,29,28,2439,6), r("Sancarbarlaz",20,25,23,2037,6),
        r("Torunoğlu",26,24,20,1873,2), r("Gusev",26,19,19,1560,5), r("Dağdelen",22,7,7,630,-13),
        r("Mehmedi",27,20,13,1406,1), r("Kaymaz",21,20,12,1142,0), r("Shelepnytskyi",28,16,16,1313,1),
        r("Iliev",25,12,11,990,2), r("Özhan",25,0,0,0,0), r("Acar",18,9,7,572,2),
    ],
    "Ankaragücü": [
        r("Erkan",25,23,23,2015,-35), r("Güller",25,27,27,2386,4), r("Ertaş",26,22,22,1936,0),
        r("Günes",33,17,16,1430,0), r("Yücel",27,25,22,2077,2), r("Soydaş",27,20,20,1667,3),
        r("Agashkov",31,23,17,1678,2), r("Mukhamadiev",27,29,25,2270,4), r("Çobanoğlu",24,25,24,2109,9),
        r("Konya",25,21,20,1666,0), r("Aydın",22,17,17,1396,5), r("Kayan",24,6,6,540,-13),
        r("Yıldırım",21,25,16,1442,2), r("Üstün",25,17,16,1323,0), r("Matveev",26,15,15,1239,1),
        r("Hut",26,17,11,984,0), r("Türksoy",19,2,1,145,-4), r("Gedikali",27,12,7,758,1),
    ],
    "Kayserispor": [
        r("Turunç",32,20,19,1691,-28), r("Uğur",30,27,26,2384,0), r("Soykök",29,25,25,2156,1),
        r("Şen",28,26,24,2138,0), r("Sancaktar",24,23,23,2070,0), r("Kılıç",30,30,28,2400,2),
        r("Duran",25,28,28,2515,2), r("Devrim",24,27,25,2199,2), r("Eken",28,27,25,2206,4),
        r("Tüzün",31,27,25,2219,11), r("Levent",26,10,10,748,3), r("Polat",24,7,6,584,-12),
        r("Azman",29,22,15,1413,0), r("Ağdere",21,16,10,936,1), r("Özdemir",25,18,6,689,1),
        r("Shabani",30,13,9,752,2), r("Lugušić",32,5,5,425,-9), r("Aktepe",23,12,5,566,0),
    ],
    "Zeytinburnuspor": [
        r("Ibrahimović",30,25,25,2250,-45), r("Sancak",27,27,27,2293,1), r("Uzuner",31,21,21,1858,0),
        r("Aydoğan",30,23,19,1758,0), r("Alpak",26,19,17,1510,2), r("Gündoğdu",28,27,27,2384,1),
        r("Gabriel",31,26,26,2295,1), r("Kanca",30,23,23,2012,5), r("Yıldırım",35,26,23,2138,9),
        r("Kiremitçi",27,24,22,1889,2), r("Baytar",29,22,21,1827,7), r("Kocakara",35,4,4,360,-3),
        r("Reçber",18,17,15,1261,0), r("Ayçiçek",27,16,14,1298,0), r("Kılıç",26,15,15,1307,0),
        r("Cvikl",26,19,10,947,2), r("Ece",29,1,1,90,-3), r("Durak",21,11,6,601,1),
    ],
    "Karabükspor": [
        r("Layiç",23,19,18,1650,-37), r("Özkayımoğlu",29,26,26,2280,0), r("Ünsal",20,26,26,2183,2),
        r("Açıkgöz",22,22,20,1831,2), r("Özer",27,24,19,1885,0), r("Yurttaş",26,29,27,2419,3),
        r("Kalaycı",27,26,25,2061,0), r("Çoban",27,20,18,1648,1), r("Dağdelen",20,26,26,2124,5),
        r("İnal",24,22,20,1705,9), r("Şermet",24,23,15,1355,2), r("Hasançebi",23,10,10,870,-21),
        r("Haraoui",28,19,17,1563,8), r("Nejat",24,18,13,1313,0), r("Çebi",25,16,12,1097,1),
        r("Bademci",21,17,9,862,0), r("Kıvanç",29,2,2,180,-4), r("Cankat",20,10,10,856,1),
    ],
    "Karşıyaka": [
        r("Valov",32,30,30,2700,-43), r("Yavaş",20,29,29,2610,2), r("Akbaş",25,25,25,2250,1),
        r("Mercan",29,25,24,2194,0), r("Sır",19,26,23,2117,0), r("Güneş",19,30,28,2462,2),
        r("Kepoğlu",25,27,27,2327,0), r("Çıkrıkçıoğlu",25,24,23,1900,1), r("Yıldız",33,27,25,2110,1),
        r("Umut",26,27,24,2136,6), r("Kiremitçi",30,17,13,1163,2), r("Küçüktaka",21,0,0,0,0),
        r("Taygun",26,18,17,1545,0), r("Kahraman",20,18,10,1037,3), r("Kanatlarovski",33,13,10,829,0),
        r("Bilal",25,15,5,541,1), r("Topal",33,0,0,0,0), r("Fedai",25,12,6,593,0),
    ],
    "Sarıyer": [
        r("Metin Mert",28,25,25,2250,-41), r("Alkan",29,26,25,2090,0), r("Yarovenko",31,24,24,2022,0),
        r("Ravcı",20,26,25,2248,2), r("Bayram",29,24,22,2026,0), r("Çalışkan",33,15,13,1140,1),
        r("Bıyıklı",27,28,28,2495,0), r("Kaplan",21,25,25,2250,1), r("Erdi",29,26,20,1821,10),
        r("Görgülü",33,24,20,1759,5), r("Güzeltepe",29,23,20,1795,0), r("Engin",27,5,5,450,-9,hint="Sarıyer Engin GK"),
        r("Demirhan",23,20,18,1631,0), r("Vazda",26,21,16,1549,4), r("Yıldırım",28,21,8,891,1),
        r("Engin",29,14,13,1015,0,hint="Sarıyer Engin outfield"), r("Tekelioğlu",20,0,0,0,0), r("Çimen",20,11,9,815,3),
    ],
}


def main() -> None:
    from expand_bel_tur_rus_gre_rosters_v030 import TURKEY
    foundation = json.loads(FOUNDATION.read_text(encoding="utf-8"))
    league = next(x for x in foundation["leagues"] if x["key"] == "tur_1993_94")
    clubs = []
    for club in league["clubs"]:
        name = club["name"]
        rows = [dict(r) for r in ROSTERS[name]]
        for pname,age,apps,starts,minutes,goals in TURKEY[name]:
            if any(r["bdfutbol_name"] == pname for r in rows):
                continue
            rows.append({"bdfutbol_name":pname,"age_1993_94":age,"appearances":apps,"starts":starts,"minutes":minutes,"goals":goals,"core_18_candidate":False,"source_roster_member":True})
        if len(rows) < 18:
            raise RuntimeError(f"{name}: below 18-player safety floor: {len(rows)}")
        clubs.append({
            "historical_position": int(club["historical_position"]),
            "name": name,
            "bdfutbol_squad_url": club["bdfutbol_squad_url"],
            "manager": None,
            "players": rows,
        })
    payload = {
        "schema_version": 1,
        "season": "1993-94",
        "country": "Turquía",
        "source_policy": (
            "BDFutbol 1993-94 squad pages; every available season-roster row is staged. "
            "18 is only the minimum safety floor. No filler identities are invented. Identity reconciliation and specialist role provenance are materialised by the importer."
        ),
        "clubs": clubs,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"clubs": len(clubs), "players": sum(len(c["players"]) for c in clubs), "minimum": min(len(c["players"]) for c in clubs)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
