from __future__ import annotations

from pathlib import Path
import json
import sys
from collections import Counter
from typing import Any
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from tools.deepen_historical_profiles_and_metadata_v031 import ROLE_TO_BROAD, ROLE_TO_LABEL, comparable, profile_gap_stats, role_ratings  # noqa: E402
from tools.review_created_player_profiles import materialise_attributes  # noqa: E402

DATA = ROOT / 'data' / 'football9394'
SNAP = DATA / 'historical_snapshot.json'
REG = DATA / 'created_players_registry.json'
QUEUE = DATA / 'bdfutbol_photo_queue.json'
STAGE = DATA / 'turkey_1993_94_roster_staging.json'
PHOTO_DIR = ROOT / 'frontend' / 'public' / 'historical9394' / 'players'
RAW_PHOTO_DIR = ROOT / '.tmp_photos_v034'

BDF_ALTAY = 'https://www.bdfutbol.com/en/t/t1993-9411414.html'
BDF_ANK = 'https://www.bdfutbol.com/en/t/t1993-9410353.html'
BDF_KAY = 'https://www.bdfutbol.com/en/t/t1993-9410432.html'
TM_ALTAY = 'https://www.transfermarkt.com/altay-sk/startseite/verein/2375/saison_id/1993'
TM_ANK = 'https://www.transfermarkt.com/mke-ankaragucu/startseite/verein/868/saison_id/1993'
TFF_TANRIBILIR = 'https://www.tff.org/Default.aspx?kisiId=21674&pageId=30'
TFF_CAFER = 'https://www.tff.org/Default.aspx?kisiId=22532&pageId=526'

COUNTRY_NAME = {
    4:'Alemania',8:'Albania',15:'Australia',20:'Bosnia-Herzegovina',21:'Bulgaria',40:'Rusia',43:'Escocia',
    54:'Macedonia',75:'República Federal de Yugoslavia',84:'Turquía',85:'Ucrania',202:'Tayikistán',206:'Turkmenistán',
}

# Broad-only records deliberately do not claim a specialist role. Their internal role is a neutral carrier for the
# sourced line of play (3 defender, 7 midfielder, 17 forward). Exact roles are used only where corroborated.
P: dict[int, dict[str, Any]] = {
# ALTAY
9495318: dict(club='Altay',name='Şanver Göymen',dob='1967-01-22',nat=[84],birth_country=84,place='Samsun',role=0,pos='Goalkeeper',bdf='700587'),
9496489: dict(club='Altay',name='Orhan Üstündağ',dob='1967-02-01',nat=[84],birth_country=84,place='Kastamonu',role=3,pos='Centre-Back',bdf='700588',position_url=TM_ALTAY,note='Transfermarkt season squad specifies Centre-Back; BDFutbol gives broad Defender.'),
9496490: dict(club='Altay',name='Müfit İkizoğlu',dob='1964-01-05',nat=[84],birth_country=84,place='Bolu',role=3,pos='Defender',precision='broad_only',bdf='1176188'),
9496491: dict(club='Altay',name='Ahmet Akuygur',dob='1967-05-29',nat=[84],birth_country=84,place='Konya',role=1,pos='Right-Back',height=176,bdf='1176189',position_url=TM_ALTAY),
9496492: dict(club='Altay',name='Toprak Kırtoğlu',dob='1971-06-10',nat=[84,4],birth_country=4,place='Germany',role=1,pos='Right-Back',bdf='55599',position_url=TM_ALTAY,note='Transfermarkt season squad specifies Right-Back; BDFutbol broad profile labels Midfielder.'),
9496493: dict(club='Altay',name='Tahir Karapınar',dob='1967-04-20',nat=[84],birth_country=84,place='Izmir',role=13,pos='Left Midfield',height=180,bdf='1100568',position_url='https://www.transfermarkt.co.uk/tahir-karapinar/profil/spieler/324025'),
9496494: dict(club='Altay',name='Şeyhmus Suna',dob='1965-04-05',nat=[84],birth_country=84,place='Diyarbakır',role=1,pos='Right-Back',bdf='702772',position_url=TM_ALTAY,note='Transfermarkt season squad specifies Right-Back; BDFutbol broad profile labels Midfielder.'),
9496495: dict(club='Altay',name='Hakan Kayalar',dob='1970-04-13',nat=[84],birth_country=84,place='Izmir',role=17,pos='Forward',precision='broad_only',bdf='1174837'),
9496496: dict(club='Altay',name='Atakan Sancarbarlaz',dob='1973-07-05',nat=[84],birth_country=84,place='Kars',role=17,pos='Forward',precision='broad_only',bdf='702409'),
9496497: dict(club='Altay',name='Ramazan Mahmut Torunoğlu',dob='1967-12-27',nat=[84],birth_country=84,place='Istanbul',role=17,pos='Centre-Forward',bdf='1175048',position_url=TM_ALTAY),
9496498: dict(club='Altay',name='Sergei Yevgenovich Gusev',dob='1967-07-01',nat=[85],birth_country=None,place='Odesa (USSR)',role=17,pos='Centre-Forward',height=180,bdf='702760',position_url='https://www.transfermarkt.com/sergiy-gusev/alletore/spieler/185481/wettbewerb/TR1/saison/1993/stand/gamewinning',note='BDFutbol records 07/07/1967; Transfermarkt and independent career profiles agree on 01/07/1967. Former-USSR birthplace is retained without a modern birth_country_id.'),
9496499: dict(club='Altay',name='Aydın Ethem Dağdelen',dob='1971-04-15',nat=[84],birth_country=84,place='Izmir',role=0,pos='Goalkeeper',bdf='700597'),
9496500: dict(club='Altay',name='Ali Mehmedi',dob='1966-01-15',nat=[8],birth_country=8,place='Tirana',role=3,pos='Defender',precision='broad_only',bdf='1178389'),
9496501: dict(club='Altay',name='Özgür Kaymaz',dob='1972-06-10',nat=[84],birth_country=84,place='Ordu',role=7,pos='Midfielder',precision='broad_only',bdf='1170014'),
9496502: dict(club='Altay',name='Yuriy Hryhorovych Shelepnytskyi',dob='1965-01-18',nat=[85],birth_country=None,place='Luzhany, Chernivtsi Oblast (USSR)',role=6,pos='Defensive Midfield',height=184,bdf='702758',position_url=TM_ALTAY,note='Former-USSR birthplace is retained without a modern birth_country_id.'),
9496503: dict(club='Altay',name='Ilian Dimov Iliev',dob='1968-07-02',nat=[21],birth_country=21,place='Varna',role=8,pos='Attacking Midfield',height=175,weight=68,bdf='71783',position_url='https://www.transfermarkt.co.uk/ilian-iliev/leistungsdaten/spieler/17467/saison/1993/wettbewerb/TRP'),
9496504: dict(club='Altay',name='Varol Özhan',dob='1968-01-20',nat=[84],birth_country=84,place='Izmir',role=0,pos='Goalkeeper',bdf='1174840'),
9496505: dict(club='Altay',name='Ahmet Acar',dob='1975-01-01',nat=[84],birth_country=84,place='Afyonkarahisar',role=3,pos='Defender',precision='broad_only',bdf='1173566'),
9497292: dict(club='Altay',name='Serkan Demir',dob='1974-05-02',nat=[84],birth_country=84,place='Izmir',role=7,pos='Midfielder',precision='broad_only',bdf='1136865'),
9497293: dict(club='Altay',name='Miodrag Ješić',dob='1958-11-30',nat=[75],birth_country=None,place='Osečenica (Yugoslavia)',role=3,pos='Defender',precision='broad_only',bdf='42795',note='Birthplace predates the 1993 FR Yugoslavia state; no successor-state birth_country_id is fabricated.'),
9497294: dict(club='Altay',name='David Stuart Mitchell',dob='1962-06-13',nat=[15,43],birth_country=43,place='Glasgow',role=17,pos='Centre-Forward',height=184,weight=74,bdf='91791',position_url='https://www.transfermarkt.com/altay-sk/startseite/verein/2375/saison_id/1993'),
9497295: dict(club='Altay',name='Murat Duran',dob='1973-08-25',nat=[84],birth_country=84,place='Izmir',role=3,pos='Defender',precision='broad_only',bdf='1179551'),
9497296: dict(club='Altay',name='Yasin Balcı',dob='1974-12-01',nat=[84],birth_country=84,place='Izmir',role=7,pos='Midfielder',precision='broad_only',bdf='1179548'),
9497297: dict(club='Altay',name='Orkan Şevket Yurtkoru',dob='1975-03-15',nat=[84],birth_country=84,place='Izmir',role=3,pos='Defender',precision='broad_only',bdf='1179550'),
9497298: dict(club='Altay',name='Serdar Meriç',dob='1977-10-10',nat=[84],birth_country=84,place='Izmir',role=17,pos='Forward',precision='broad_only',bdf='700601'),
9497299: dict(club='Altay',name='Birand Yaytaş',dob='1975-07-11',nat=[84],birth_country=84,place='Bornova (Izmir)',role=3,pos='Defender',precision='broad_only',bdf='1173565'),
9497300: dict(club='Altay',name='Hüseyin Gün',dob=None,birth_year=1975,nat=[84],birth_country=84,place='Izmir',role=7,pos='Midfielder',precision='broad_only',bdf='1179553',note='BDFutbol supplies only birth year 1975; month/day are deliberately not invented.'),
# ANKARAGÜCÜ
9496506: dict(club='Ankaragücü',name='Adnan Erkan',dob='1968-01-15',nat=[84],birth_country=84,place='Denizli',role=0,pos='Goalkeeper',bdf='59641'),
9495324: dict(club='Ankaragücü',name='Serhat Güller',dob='1968-12-18',nat=[84],birth_country=84,place='Eskişehir',role=3,pos='Defender',precision='broad_only',bdf='702878'),
9496507: dict(club='Ankaragücü',name='Taner Ertaş',dob='1967-08-11',nat=[84],birth_country=84,place='Bursa',role=3,pos='Defender',precision='broad_only',bdf='1179565'),
9496508: dict(club='Ankaragücü',name='Bahaddin Günes',dob='1960-03-10',nat=[84],birth_country=84,place='Trabzon',role=3,pos='Defender',precision='broad_only',bdf='703103'),
9496509: dict(club='Ankaragücü',name='Ergün Yücel',dob='1966-03-10',nat=[84],birth_country=84,place='Kayseri',role=7,pos='Midfielder',precision='broad_only',bdf='1173610'),
9496510: dict(club='Ankaragücü',name='Hayati Soydaş',dob='1966-05-01',nat=[84],birth_country=84,place='Gümüşhane',role=1,pos='Right-Back',bdf='1171772',position_url=TM_ANK,note='Transfermarkt 1993-94 squad identifies Right-Back; BDFutbol labels broad Midfielder.'),
9496511: dict(club='Ankaragücü',name='Sergey Nikolaevich Agashkov',dob='1962-11-06',nat=[40],birth_country=None,place='Ashgabat (USSR)',role=7,pos='Central Midfield',height=176,bdf='1177909',position_url='https://www.besoccer.com/player/sergey-agashkov-512178',note='Russian football identity; birthplace was Ashgabat in the USSR, so no modern Turkmen birth_country_id is assigned.'),
9496512: dict(club='Ankaragücü',name='Mukhsin Muslimovich Mukhamadiev',dob='1966-10-21',nat=[202,40],birth_country=None,place='Dushanbe (USSR)',role=17,pos='Centre-Forward',height=172,weight=65,bdf='1159085',position_url='https://en.wikipedia.org/wiki/Mukhsin_Mukhamadiev',note='Represented Tajikistan in 1992 and Russia in 1995; both historical football nationalities are retained. Birthplace is former USSR.'),
9496513: dict(club='Ankaragücü',name='Hakan Çobanoğlu',dob='1969-11-05',nat=[84],birth_country=84,place='Istanbul',role=17,pos='Forward',height=190,bdf='1173611',precision='broad_only'),
9496514: dict(club='Ankaragücü',name='Ramazan Konya',dob='1968-12-05',nat=[84],birth_country=84,place='Istanbul',role=17,pos='Forward',bdf='1178734',precision='broad_only'),
9496515: dict(club='Ankaragücü',name='Cafer Aydın',dob='1971-11-17',nat=[84],birth_country=84,place='Çorum',role=17,pos='Centre-Forward',height=181,bdf='702562',position_url=TFF_CAFER),
9496516: dict(club='Ankaragücü',name='Muharrem Kayan',dob='1969-11-22',nat=[84],birth_country=84,place='Istanbul',role=0,pos='Goalkeeper',bdf='1179555'),
9496517: dict(club='Ankaragücü',name='Mehmet Yıldırım',dob='1972-09-15',nat=[84],birth_country=84,place='Erzurum',role=17,pos='Centre-Forward',bdf='702407',position_url=TM_ANK),
9496518: dict(club='Ankaragücü',name='Tarık Üstün',dob='1968-05-23',nat=[84],birth_country=84,place='Ankara',role=3,pos='Defender',precision='broad_only',bdf='1176194'),
9496519: dict(club='Ankaragücü',name='Yuriy Aleksandrovich Matveev',dob='1967-06-08',nat=[40],birth_country=None,place='Nizhniy Tagil, Sverdlovsk Oblast (USSR)',role=17,pos='Centre-Forward',height=183,weight=83,bdf='591077',position_url=TM_ANK,note='Former-USSR birthplace is retained without a modern birth_country_id.'),
9496520: dict(club='Ankaragücü',name='Tayfun Hut',dob='1967-07-19',nat=[84],birth_country=84,place='Istanbul',role=7,pos='Midfielder',precision='broad_only',bdf='702778'),
9496521: dict(club='Ankaragücü',name='Murat Türksoy',dob='1974-12-01',nat=[84],birth_country=84,place='Elazığ',role=0,pos='Goalkeeper',bdf='707164'),
9496522: dict(club='Ankaragücü',name='Gökhan Gedikali',dob='1966-01-08',nat=[84],birth_country=84,place='Ankara',role=3,pos='Defender',precision='broad_only',bdf='55604'),
9497301: dict(club='Ankaragücü',name='Şevket Candar',dob='1966-01-06',nat=[84],birth_country=84,place='Hakkari',role=17,pos='Forward',precision='broad_only',bdf='702779'),
9497302: dict(club='Ankaragücü',name='Hakan Kutlu',dob='1972-01-14',nat=[84],birth_country=84,place='Amasya',role=5,pos='Sweeper',height=182,bdf='52611',position_url='https://www.transfermarkt.us/hakan-kutlu/profil/spieler/6996',note='Transfermarkt gives Sweeper; other profiles describe central defender. Exact source role is retained with the conflict documented.'),
9497303: dict(club='Ankaragücü',name='Soner Büyükergün',dob='1968-08-29',nat=[84],birth_country=84,place='Sakarya',role=17,pos='Forward',precision='broad_only',bdf='1179561'),
9497304: dict(club='Ankaragücü',name='Bülent Üstüner',dob='1969-07-30',nat=[84],birth_country=84,place=None,role=3,pos='Defender',precision='broad_only',bdf='1176196'),
9497305: dict(club='Ankaragücü',name='Charyar Abdurakhmanovich Mukhadov',dob='1969-11-12',nat=[206],birth_country=None,place='Ashgabat (USSR)',role=17,pos='Centre-Forward',height=179,bdf='1178793',note='Born in the Turkmen SSR before independence; nationality is Turkmenistan, but modern birth_country_id is not retrofitted.'),
9497306: dict(club='Ankaragücü',name='Ensar Hacımustafaoğlu',dob=None,birth_year=1973,nat=[84],birth_country=84,place='Trabzon',role=3,pos='Defender',precision='broad_only',bdf='1179566',note='BDFutbol supplies only birth year 1973; month/day are deliberately not invented.'),
9497307: dict(club='Ankaragücü',name='Beyzat Kaya',dob='1970-06-07',nat=[84],birth_country=84,place='Istanbul',role=7,pos='Midfielder',precision='broad_only',bdf='1178735'),
9497308: dict(club='Ankaragücü',name='Ekrem Onuk',dob='1974-04-20',nat=[84],birth_country=4,place='Philippsburg',role=8,pos='Attacking Midfield',height=173,bdf='1150050',position_url='https://www.transfermarkt.com/ekrem-onuk/profil/spieler/91016'),
9497309: dict(club='Ankaragücü',name='Ahmet Öztürk',dob='1973-08-20',nat=[84],birth_country=84,place='Tokat',role=7,pos='Midfielder',precision='broad_only',bdf='1179562'),
# KAYSERİSPOR
9496523: dict(club='Kayserispor',name='Ferhat Turunç',dob='1961-02-02',nat=[84],birth_country=84,place='Antakya (Hatay)',role=0,pos='Goalkeeper',bdf='1179908'),
9496524: dict(club='Kayserispor',name='Mustafa Uğur',dob='1963-01-19',nat=[84],birth_country=84,place='Kayseri',role=3,pos='Defender',precision='broad_only',bdf='1120089'),
9496525: dict(club='Kayserispor',name='Mehmet Soykök',dob='1964-09-27',nat=[84],birth_country=84,place='Ankara',role=3,pos='Defender',precision='broad_only',bdf='702820'),
9496526: dict(club='Kayserispor',name='Mehmet Şen',dob='1965-01-14',nat=[84],birth_country=84,place='Ankara',role=3,pos='Defender',precision='broad_only',bdf='702890'),
9496527: dict(club='Kayserispor',name='İlhan Sancaktar',dob='1969-09-16',nat=[84],birth_country=84,place='Istanbul',role=3,pos='Defender',precision='broad_only',bdf='1173833'),
9496528: dict(club='Kayserispor',name='Hayrettin Kılıç',dob='1963-11-17',nat=[84],birth_country=84,place='Bursa',role=7,pos='Midfielder',precision='broad_only',bdf='1176296'),
9496529: dict(club='Kayserispor',name='Abdullah Duran',dob='1968-07-30',nat=[84],birth_country=84,place='Ankara',role=7,pos='Midfielder',precision='broad_only',bdf='1176293'),
9496530: dict(club='Kayserispor',name='Levent Devrim',dob='1969-08-26',nat=[84],birth_country=84,place='Hatay',role=7,pos='Midfielder',precision='broad_only',bdf='702737'),
9496531: dict(club='Kayserispor',name='Salih Eken',dob='1965-02-26',nat=[84],birth_country=84,place='Ankara',role=7,pos='Midfielder',precision='broad_only',bdf='1176291'),
9496532: dict(club='Kayserispor',name='Zafer Tüzün',dob='1962-08-30',nat=[84],birth_country=84,place='Eskişehir',role=17,pos='Forward',precision='broad_only',bdf='57065'),
9496533: dict(club='Kayserispor',name='Levent Kurt',dob='1967-03-15',nat=[84],birth_country=84,place='Mersin',role=17,pos='Forward',precision='broad_only',bdf='1176274'),
9496534: dict(club='Kayserispor',name='Hakan Polat',dob='1969-05-22',nat=[84],birth_country=84,place='Kayseri',role=0,pos='Goalkeeper',bdf='1178568'),
9496535: dict(club='Kayserispor',name='Hakan Azman',dob='1964-03-19',nat=[84],birth_country=84,place='Karabük',role=3,pos='Defender',precision='broad_only',bdf='1174844'),
9496536: dict(club='Kayserispor',name='Tahir Ağdere',dob='1972-05-08',nat=[84],birth_country=84,place='Giresun',role=7,pos='Midfielder',precision='broad_only',bdf='1178569'),
9496537: dict(club='Kayserispor',name='Ferhat Özdemir',dob='1968-07-02',nat=[84],birth_country=84,place='Kahramanmaraş',role=17,pos='Forward',precision='broad_only',height=178,bdf='1179907'),
9496538: dict(club='Kayserispor',name='Nexhat Shabani',dob='1963-11-11',nat=[54],birth_country=None,place='Gjilan (Yugoslavia)',role=17,pos='Centre-Forward',bdf='1179910',position_url='https://en.wikipedia.org/wiki/Nexhat_Shabani',note='BDFutbol assigns a modern North Macedonia birth-country label to Gjilan. Historical birthplace was SFR Yugoslavia; nationality is Macedonian and no successor-state birth_country_id is fabricated.'),
9496539: dict(club='Kayserispor',name='Enver Lugušić',dob='1961-05-01',nat=[20],birth_country=None,place='Foča (Yugoslavia)',role=0,pos='Goalkeeper',height=188,bdf='1178565',note='Birthplace was Yugoslavia; Bosnia-Herzegovina nationality is retained without retrofitting the birth state.'),
9496540: dict(club='Kayserispor',name='Atabey Aktepe',dob='1970-12-10',nat=[84],birth_country=84,place='Ardahan',role=7,pos='Midfielder',precision='broad_only',bdf='41280'),
9497310: dict(club='Kayserispor',name='Mehmet Kalemci',dob='1968-08-18',nat=[84],birth_country=84,place='Istanbul',role=3,pos='Defender',precision='broad_only',bdf='1178570'),
9497311: dict(club='Kayserispor',name='Özcan Duman',dob='1964-03-10',nat=[84],birth_country=84,place='Çorum',role=3,pos='Defender',precision='broad_only',height=170,bdf='1179844'),
9497312: dict(club='Kayserispor',name='Mersud Demirović',dob='1958-09-17',nat=[20],birth_country=None,place='Bihać (Yugoslavia)',role=3,pos='Defender',precision='broad_only',height=185,bdf='1179909',note='Bosnia-Herzegovina football identity; birthplace predates independence and is stored textually as Yugoslavia.'),
9497313: dict(club='Kayserispor',name='Ergun Erikdemir',dob='1970-11-25',nat=[84],birth_country=84,place='Istanbul',role=7,pos='Midfielder',precision='broad_only',bdf='1179911'),
9497314: dict(club='Kayserispor',name='Cafer Aydın',dob='1971-11-17',nat=[84],birth_country=84,place='Çorum',role=17,pos='Centre-Forward',height=181,bdf='702562',position_url=TFF_CAFER),
9497315: dict(club='Kayserispor',name='Öztürk Tanrıbilir',dob='1966-05-03',nat=[84],birth_country=84,place='Kayseri',role=0,pos='Goalkeeper',height=180,bdf='1179912',position_url=TFF_TANRIBILIR,note='TFF official player record gives 03/05/1966; BDFutbol/Kayserispor archive gives 19/05/1966. Official federation date is retained.'),
9497316: dict(club='Kayserispor',name='Seyit Cem Ünsal',dob='1975-10-09',nat=[84],birth_country=84,place='Sarıoğlan',role=17,pos='Forward',precision='broad_only',height=182,weight=73,bdf='702726'),
9497317: dict(club='Kayserispor',name='Metin İlhan',dob='1967-05-23',nat=[84],birth_country=84,place='Kayseri',role=3,pos='Defender',precision='broad_only',bdf='1179906'),
9497318: dict(club='Kayserispor',name='Ferhat Bakar',dob='1974-10-13',nat=[84],birth_country=84,place='Kayseri',role=3,pos='Defender',precision='broad_only',bdf='1173830'),
}

# Filled after downloading verified BDF portraits. Key -> original portrait URL.
PHOTO_URLS: dict[int,str] = {
9495318:'https://www.bdfutbol.com/i/j/700587.jpg?v=1696866637',
9496489:'https://www.bdfutbol.com/i/j/700588.jpg?v=1696866691',
9496493:'https://www.bdfutbol.com/i/j/1100568.jpg?v=1696866983',
9496494:'https://www.bdfutbol.com/i/j/702772.jpg?v=1706693945',
9496497:'https://www.bdfutbol.com/i/j/1175048.jpg?v=1780345596',
9496498:'https://www.bdfutbol.com/i/j/702760.jpg?v=1706619692',
9495324:'https://www.bdfutbol.com/i/j/702878b.jpg?v=1708077430',
9496512:'https://www.bdfutbol.com/i/j/1159085.jpg?v=1761839587',
9497302:'https://www.bdfutbol.com/i/j/52611.jpg?v=1675337236',
9496538:'https://www.bdfutbol.com/i/j/1179910.jpg?v=1782592765',
9496539:'https://www.bdfutbol.com/i/j/1178565.jpg?v=1782161330',
9497314:'https://www.bdfutbol.com/i/j/702562.jpg?v=1705343441',
9497315:'https://www.bdfutbol.com/i/j/1179912.jpg?v=1782593200',
9497317:'https://www.bdfutbol.com/i/j/1179906.jpg?v=1782591829',
9497318:'https://www.bdfutbol.com/i/j/1173830.jpg?v=1777923037',
}

ROLE_ES={0:'Portero',1:'Lateral derecho',2:'Lateral izquierdo',3:'Defensa central',4:'Defensa central',5:'Líbero',6:'Mediocentro defensivo',7:'Centrocampista',8:'Mediapunta',9:'Interior derecho',10:'Interior derecho',11:'Extremo derecho',12:'Extremo derecho',13:'Interior izquierdo',14:'Interior izquierdo',15:'Extremo izquierdo',16:'Extremo izquierdo',17:'Delantero centro'}

def load(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def dump(p,o): Path(p).write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def split_name(n):
    a=n.split(); return (None,n) if len(a)==1 else (' '.join(a[:-1]),a[-1])

def reattribute(player,new_role,originals,sid):
    a,b=comparable(originals,ROLE_TO_BROAD[new_role],int(player.get('overall') or 70),sid)
    player['attributes']=materialise_attributes(int(player.get('overall') or 70),a,b)
    player['attribute_source']='fixed_source_comparable_role_correction_0.34'
    player['attribute_comparable_source_ids']=[int(a['source_id']),int(b['source_id'])]

def apply_profile(player,patch,originals,sid):
    old={'display_name':player.get('display_name'),'role':int(player.get('primary_role') or 0),'broad':player.get('broad_position'),'position':player.get('historical_position_1993_94'),'birth_date':player.get('birth_date'),'international_country_id':player.get('international_country_id')}
    first,surname=split_name(patch['name']); player['display_name']=patch['name']; player['first_name']=first; player['surname1']=surname
    if patch.get('dob'):
        player['birth_date']=patch['dob']+'T00:00:00'; player.pop('historical_birth_year_only',None)
    else:
        # keep a genuine gap rather than creating 01/01 from a year-only source
        player['birth_date']=None; player['historical_birth_year_only']=int(patch['birth_year'])
    if patch.get('birth_country') is not None: player['birth_country_id']=int(patch['birth_country'])
    else: player.pop('birth_country_id',None)
    player['international_country_id']=int(patch['nat'][0]); player['profile_nationality_country_ids']=[int(x) for x in patch['nat']]
    if len(patch['nat'])>1: player['secondary_nationality_country_id']=int(patch['nat'][1])
    else: player.pop('secondary_nationality_country_id',None)
    player['historical_birth_place_text']=patch.get('place')
    profile_url=f"https://www.bdfutbol.com/en/j/j{patch['bdf']}.html"
    player['historical_birth_place_source_url']=profile_url; player['historical_birth_place_source_label']='BDFutbol individual profile v0.34'
    player['bdfutbol_id']=str(patch['bdf']); player['bdfutbol_url']=profile_url
    if patch.get('height') is not None: player['height_cm']=int(patch['height'])
    if patch.get('weight') is not None: player['weight_kg']=int(patch['weight'])
    role=int(patch['role']); old_role=int(player.get('primary_role') or 0); old_broad=player.get('broad_position')
    player['primary_role']=role; player['broad_position']=ROLE_TO_BROAD[role]; player['role_ratings']=role_ratings(role)
    precision=patch.get('precision','exact'); player['profile_position_precision']=precision; player['source_profile_position']=patch['pos']; player['profile_review_required']=precision=='broad_only'
    if precision=='broad_only':
        player['historical_position_1993_94']=patch['pos']+' (exact role unresolved)'; player['historical_position_source']='BDFutbol individual profile — broad position only v0.34'
    else:
        player['historical_position_1993_94']=ROLE_TO_LABEL[role]; player['historical_position_source']='BDFutbol + specialist cross-check v0.34'
    player['historical_position_source_url']=patch.get('position_url') or profile_url
    player['historical_profile_source']='BDFutbol individual profile + specialist cross-check v0.34'; player['historical_profile_source_url']=profile_url
    if patch.get('note'): player['historical_profile_source_note']=patch['note']
    if role!=old_role or player['broad_position']!=old_broad: reattribute(player,role,originals,sid)
    return {'source_id':sid,'club':patch['club'],'before':old,'after':{'display_name':player['display_name'],'role':player['primary_role'],'broad':player['broad_position'],'position':player['historical_position_1993_94'],'birth_date':player.get('birth_date'),'international_country_id':player['international_country_id']},'role_changed':role!=old_role,'precision':precision}

def sync(target,player,patch):
    target.update({'display_name':player['display_name'],'first_name':player.get('first_name'),'surname1':player.get('surname1'),'birth_date':str(player['birth_date'])[:10] if player.get('birth_date') else None,'country_id':player.get('international_country_id'),'country_name':COUNTRY_NAME.get(player.get('international_country_id')),'broad_position':player.get('broad_position'),'historical_position_1993_94':player.get('historical_position_1993_94'),'profile_review_required':bool(player.get('profile_review_required')),'individual_profile_source':'BDFutbol/specialist profile cross-check v0.34','individual_profile_source_url':f"https://www.bdfutbol.com/en/j/j{patch['bdf']}.html",'historical_birth_place_text':patch.get('place'),'bdfutbol_id':str(patch['bdf']),'bdfutbol_url':f"https://www.bdfutbol.com/en/j/j{patch['bdf']}.html"})
    if patch.get('birth_year') and not patch.get('dob'): target['historical_birth_year_only']=int(patch['birth_year'])

def update_stage(stage,sid,player,patch):
    club=next(c for c in stage['clubs'] if c.get('name')==patch['club']); row=next(r for r in club['players'] if int(r.get('resolved_source_id') or -1)==sid)
    row.update({'resolved_display_name':player['display_name'],'resolved_primary_role':player['primary_role'],'resolved_exact_position':player['historical_position_1993_94'],'resolved_birth_date':player.get('birth_date'),'resolved_country_id':player['international_country_id'],'source_profile_position':patch['pos'],'profile_source':'BDFutbol/specialist profile cross-check v0.34','profile_source_url':f"https://www.bdfutbol.com/en/j/j{patch['bdf']}.html",'position_source':player['historical_position_source'],'position_source_url':player['historical_position_source_url'],'resolved_birth_place_text':patch.get('place'),'bdfutbol_id':str(patch['bdf']),'individual_profile_source_url':f"https://www.bdfutbol.com/en/j/j{patch['bdf']}.html"})
    if patch.get('birth_year') and not patch.get('dob'): row['resolved_birth_year_only']=int(patch['birth_year'])
    if patch.get('note'): row['profile_source_note']=patch['note']

def normalize_photos(by,reg_by,queue_by):
    PHOTO_DIR.mkdir(parents=True,exist_ok=True); rows=[]
    for sid,url in PHOTO_URLS.items():
        raw=RAW_PHOTO_DIR/f'{sid}.jpg'
        if not raw.exists(): continue
        try:
            with Image.open(raw) as im:
                rgb=im.convert('RGB'); fitted=ImageOps.fit(rgb,(40,55),method=Image.Resampling.LANCZOS,centering=(0.5,0.5)); out=PHOTO_DIR/f'{sid}.jpg'; fitted.save(out,'JPEG',quality=92,optimize=True)
            with Image.open(out) as ck:
                if ck.size!=(40,55) or ck.mode!='RGB' or ck.format!='JPEG': raise RuntimeError('bad normalized photo')
        except Exception:
            continue
        patch=P[sid]; profile_url=f"https://www.bdfutbol.com/en/j/j{patch['bdf']}.html"
        for target in (reg_by[sid],queue_by[sid]):
            target.update({'photo_filename':f'{sid}.jpg','photo_status':'bundled_normalized_bdfutbol','photo_width':40,'photo_height':55,'photo_format':'JPEG','photo_mode':'RGB','photo_source':'BDFutbol individual profile v0.34','photo_source_url':url,'bdfutbol_id':str(patch['bdf']),'bdfutbol_url':profile_url})
        rows.append({'source_id':sid,'display_name':by[sid]['display_name'],'photo_url':url,'asset':str((PHOTO_DIR/f'{sid}.jpg').relative_to(ROOT))})
    return rows

def fmt_num(value: int) -> str:
    return f'{value:,}'.replace(',', '.')

def biography(player,team,row):
    if player.get('profile_position_precision')=='broad_only':
        role={'POR':'Portero','DEF':'Defensa','MED':'Centrocampista','DEL':'Delantero'}.get(player.get('broad_position'),'Futbolista')
    else:
        role=ROLE_ES.get(int(player.get('primary_role') or 0),'Futbolista')
    parts=[f'{role} de {team} en la temporada 1993-94.']; stats=[]
    for key,label in [('appearances','partidos'),('starts','como titular')]:
        value=row.get(key)
        if isinstance(value,int) and value>=0: stats.append(f'{value} {label}')
    minutes=row.get('minutes')
    if isinstance(minutes,int) and minutes>=0: stats.append(f'{fmt_num(minutes)} minutos')
    if stats: parts.append('En el registro histórico figura con '+', '.join(stats)+'.')
    goals=row.get('goals')
    if int(player.get('primary_role') or 0)!=0 and isinstance(goals,int) and goals>=0:
        parts.append(f'Marcó {goals} gol'+('' if goals==1 else 'es')+'.')
    bd=player.get('birth_date')
    if bd:
        y,m,d=str(bd)[:10].split('-'); parts.append(f'Fecha de nacimiento registrada: {d}/{m}/{y}.')
    elif player.get('historical_birth_year_only'):
        parts.append(f"La fuente individual sólo documenta el año de nacimiento ({player['historical_birth_year_only']}); no se inventa día ni mes.")
    if player.get('historical_birth_place_text'):
        parts.append('Lugar de nacimiento documentado: '+str(player['historical_birth_place_text'])+'.')
    return ' '.join(parts)

def regenerate_bios(snap,stage):
    by={int(p['source_id']):p for p in snap['players']}; rows={}
    for c in stage['clubs']:
        for r in c['players']:
            sid=r.get('resolved_source_id')
            if sid is not None: rows.setdefault(int(sid),[]).append((c['name'],r))
    changed=0; missing=[]
    for sid in P:
        if sid not in rows:
            missing.append(sid); continue
        p=by[sid]; old=p.get('historical_biography_1993_94'); candidates=rows[sid]
        team_name=str(P[sid]['club']); chosen=candidates[0]
        for cand in candidates:
            if str(cand[0]).casefold()==team_name.casefold(): chosen=cand; break
        team,row=chosen; new=biography(p,team,row)
        p['historical_biography_1993_94']=new
        p.pop('historical_biography',None)
        p['historical_biography_source_url']=row.get('profile_source_url') or row.get('individual_profile_source_url') or f"https://www.bdfutbol.com/en/j/j{P[sid]['bdf']}.html"
        p['historical_biography_source_label']=row.get('profile_source') or 'BDFutbol/specialist profile cross-check v0.34'
        p['historical_biography_evidence']={'season':'1993-94','club':team,'appearances':row.get('appearances'),'starts':row.get('starts'),'minutes':row.get('minutes'),'goals':row.get('goals'),'staging_name':row.get('bdfutbol_name') or row.get('resolved_display_name')}
        p['historical_biography_status']='source_backed_season_summary'; p['historical_biography_staged_clubs']=[x[0] for x in candidates]
        changed+=old!=new
    if missing: raise RuntimeError(f'v0.34 curated players missing staging rows: {missing}')
    return {'profiles_considered':len(P),'biographies_changed':changed,'missing_stage_rows':0}

def main():
    snap=load(SNAP); reg=load(REG); queue=load(QUEUE); stage=load(STAGE)
    by={int(p['source_id']):p for p in snap['players']}; reg_by={int(p['source_id']):p for p in reg['players']}; queue_by={int(p['source_id']):p for p in queue['players']}
    originals=[p for p in snap['players'] if p.get('attributes') and not p.get('external_origin') and not p.get('creation_batch')]
    before=profile_gap_stats(snap); changes=[]
    missing=[sid for sid in P if sid not in by or sid not in reg_by or sid not in queue_by]
    if missing: raise RuntimeError(f'missing identities: {missing}')
    for sid,patch in P.items():
        p=by[sid]; changes.append(apply_profile(p,patch,originals,sid)); sync(reg_by[sid],p,patch); sync(queue_by[sid],p,patch); update_stage(stage,sid,p,patch)
    photos=normalize_photos(by,reg_by,queue_by); bios=regenerate_bios(snap,stage)
    dump(SNAP,snap); dump(REG,reg); dump(QUEUE,queue); dump(STAGE,stage)
    after=profile_gap_stats(snap)
    ids=[int(x['source_id']) for x in reg['players']]; qids=[int(x['source_id']) for x in queue['players']]
    if len(ids)!=len(set(ids)) or len(qids)!=len(set(qids)) or set(ids)!=set(qids): raise RuntimeError('identity registry integrity failure')
    audit={'schema_version':1,'checkpoint':'0.34.0-turkey-altay-ankaragucu-kayserispor-deep','status':'pass','profile_gaps_before':before,'profile_gaps_after':after,'profiles':{'curated_this_batch':len(P),'by_club':dict(Counter(x['club'] for x in P.values())),'exact_specialist_roles':sum(x.get('precision','exact')=='exact' for x in P.values()),'broad_only_exact_role_unresolved':sum(x.get('precision')=='broad_only' for x in P.values()),'year_only_birth_records':sum(not x.get('dob') for x in P.values()),'role_corrections_this_batch':sum(bool(c['role_changed']) for c in changes),'changes':changes},'photos':{'new_normalized_bdfutbol_portraits':len(photos),'rows':photos,'total_bundled_normalized_bdfutbol':sum(r.get('photo_status')=='bundled_normalized_bdfutbol' for r in reg['players'])},'biographies':bios,'identity_integrity':{'registry_rows':len(ids),'unique_registry_ids':len(set(ids)),'sets_match':set(ids)==set(qids)},'source_policy':['No day/month is invented when the historical source only gives a birth year.','Broad positions are marked exact-role unresolved unless a specialist/federation source corroborates a role.','Former-USSR and former-Yugoslavia birthplaces are stored textually instead of retrofitting a modern successor-state birth_country_id.','Official federation data wins documented date conflicts; multi-source specialist corroboration wins a known BDFutbol date conflict.','No basketball 75/25 rule is used.']}
    dump(DATA/'historical_profiles_metadata_audit_v034.json',audit); dump(DATA/'historical_metadata_gaps_v034.json',{'checkpoint':audit['checkpoint'],'gaps':after}); dump(DATA/'historical_biographies_audit_v034.json',bios); dump(DATA/'bdfutbol_photo_normalization_v034_altay_ank_kay.json',{'checkpoint':audit['checkpoint'],'status':'pass','portraits':photos})
    print(json.dumps({'curated':len(P),'exact_roles':audit['profiles']['exact_specialist_roles'],'broad_only':audit['profiles']['broad_only_exact_role_unresolved'],'year_only_births':audit['profiles']['year_only_birth_records'],'role_corrections':audit['profiles']['role_corrections_this_batch'],'photos_new':len(photos),'turkey_gaps_before':before['Turkey'],'turkey_gaps_after':after['Turkey']},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
