from __future__ import annotations
from datetime import datetime, date
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data/football9394'

# Additional source rows omitted by the old 18-player activation gate. 18 is now only
# the minimum safety floor; every row available in the pinned season source belongs
# in the historical season roster.
TURKEY={
'Galatasaray': [('Arslan',23,8,5,454,0),('Tolungüc',29,9,3,363,1),('Altıntaş',32,9,4,422,1),('Babaoğlu',23,4,0,79,0),('Okan',20,2,0,40,0),('Hinçal',19,2,0,15,0),('Demiriz',31,0,0,0,0)],
'Fenerbahçe': [('Hotić',31,4,4,238,1),('Rıdvan',31,3,3,233,1),('Saatcioğlu',18,3,0,53,0),('Hakan',26,2,1,83,0),('Demirtaş',25,1,0,52,0),('Alpacar',20,0,0,0,0),('Şenel',19,0,0,0,0)],
'Trabzonspor': [('Shelepnytskyi',28,6,6,456,0),('Alarçin',21,5,2,207,0),('Traş',19,5,0,96,1),('Akyüz',23,2,0,29,0),('Durak',27,1,0,67,0),('Gusev',26,1,0,44,0),('Usta',20,1,0,8,0)],
'Beşiktaş': [('Gültiken',28,7,2,250,0),('Demirbay',20,7,1,225,1),('Güveneroğlu',33,4,4,337,0),('Manessero',29,2,1,134,0),('Yüksel',26,0,0,0,0)],
'Samsunspor': [('Dobre',26,9,6,663,1),('Yıldırım',19,9,6,550,0),('Tüzün',24,7,7,524,0),('Hanganu',23,8,6,421,1),('Işık',24,8,4,438,0),('Akpınar',25,2,1,64,0),('Kahraman',20,1,0,44,0),('Şahin',19,1,0,25,1),('Demirci',25,0,0,0,0)],
'Kocaelispor': [('Kula',25,9,5,455,0),('Doğansoy',26,4,1,195,0),('Oral',19,3,0,47,0),('Şişman',19,3,0,66,0),('Suna',28,1,0,25,0),('Altıntaş',36,1,0,14,0),('Danacı',27,0,0,0,0)],
'Gençlerbirliği': [('Damla',20,3,1,142,0),('Şenvardar',22,1,1,46,0),('Atik',22,2,1,71,0),('Özyılmaz',18,2,0,40,0),('Altıparmak',24,2,0,46,0),('Güler',21,0,0,0,0),('Baştürk',20,0,0,0,0)],
'Gaziantepspor': [('Gönülacar',21,11,2,391,2),('Sarı',19,6,4,376,0),('Yücedağ',27,3,1,92,0),('Yiğit',18,2,0,64,0),('Murat',16,1,0,25,0),('Oğur',18,1,0,19,0),('Turgut',23,0,0,0,0),('Şenyurt',22,0,0,0,0)],
'Bursaspor': [('Yıldırım',23,8,3,439,0),('Ünal',20,6,4,380,0),('Arslan',19,7,1,171,0),('Yılmaz',25,4,1,191,0),('Baştan',18,2,1,118,0),('Bayhan',16,2,1,134,0),('Şentürk',20,2,1,90,0),('Dilaver',28,1,0,30,0),('Bastık',19,0,0,0,0),('Özdemir',18,0,0,0,0),('Çayla',18,0,0,0,0),('Gürbüz',16,0,0,0,0)],
'Altay': [('Serkan',19,8,7,628,0),('Ješić',35,6,6,540,0),('Mitchell',31,3,3,226,0),('Duran',20,3,0,35,0),('Balcı',19,4,0,46,0),('Yurtkoru',18,2,1,100,0),('Meriç',16,1,0,14,0),('Yaytaş',18,0,0,0,0),('Gün',18,0,0,0,0)],
'Ankaragücü': [('Şevket',27,10,8,706,0),('Kutlu',21,8,7,620,1),('Büyükergün',25,9,3,412,1),('Üstüner',24,8,1,248,1),('Mukhadov',24,5,4,317,1),('Hacımustafaoğlu',20,2,1,112,0),('Beyzat',23,2,1,113,0),('Onuk',19,1,0,13,0),('Öztürk',20,0,0,0,0)],
'Kayserispor': [('Kalemci',25,7,7,574,0),('Duman',29,5,4,335,0),('Demirović',35,5,2,237,1),('Erikdemir',23,2,2,160,0),('Aydın',22,4,1,184,0),('Tanrıbilir',27,0,0,0,0),('Ünsal',18,2,0,13,0),('İlhan',26,1,0,44,0),('Bakar',19,0,0,0,0)],
'Zeytinburnuspor': [('Avcıoğlu',22,13,1,357,1),('Tokoğlu',27,7,6,457,1),('Hattat',28,8,2,212,0),('Sünnetçiler',29,4,3,278,0),('Aydemir',24,4,1,140,0),('Uğur',27,3,0,25,0),('Ünver',26,2,1,48,0),('Köseoğlu',25,0,0,0,0)],
'Karabükspor': [('Sayın',23,7,4,296,0),('Buthelezi',24,6,5,463,0),('Kalkan',27,4,4,285,0),('Mwakapuki',26,4,3,314,0),('İlarslan',29,2,1,109,0),('Baygın',26,3,0,95,1),('Tasçı',22,2,0,65,0),('Sarı',22,1,0,60,0),('Saraç',23,0,0,0,0)],
'Karşıyaka': [('Cyzio',25,9,5,420,0),('Golubica',28,7,4,336,0),('Tamsan',19,5,2,241,0),('Akçura',24,5,0,137,0),('Gürgenç',18,0,0,0,0),('Kocaman',21,0,0,0,0),('Alptekin',22,0,0,0,0)],
'Sarıyer': [('Başar',23,10,7,696,0),('Baybatmaz',24,9,2,304,0),('Heroll',29,4,4,360,0),('Aktaş',23,1,1,20,0),('Ulusavaş',31,1,0,15,0),('Ülker',32,0,0,0,0)],
}

RUSSIA={
'Spartak Moskva':[('Gashkin',23,11,3,382,0),('Tikhonov',23,7,5,390,2),('Rodionov',31,8,2,342,0),('Chernyshov',25,4,3,285,0),('Bondar',26,2,2,180,0),('Pogodin',25,2,1,83,0),('Chudin',20,2,0,65,0),('Chizhov',18,0,0,0,0),('Kechinov',19,1,0,26,0),('Konovalov',19,1,0,7,0),('Gradilenko',24,1,0,26,0),('Baksheev',23,0,0,0,0),('Alexey Sergeev',27,0,0,0,0),('Krestov',21,0,0,0,0),('Beschastnykh',19,0,0,0,0),('Rekuts',18,0,0,0,0)],
'Rotor Volgograd':[('Kuznetsov',27,4,3,277,0),('Shkilov',28,8,2,204,0),('Konovalov',23,3,1,81,0),('Miroshnichenko',25,2,1,54,0),('Perminov',25,0,0,0,0)],
'Dynamo Moskva':[('Derkach',27,12,10,802,1),('Hovhannisyan',25,8,7,607,0),('Gudymenko',27,9,4,414,1),('Nekrasov',20,10,1,236,0),('Varlamov',22,8,5,522,0),('Sklyarov',27,7,5,428,1),('Savchenko',18,11,0,215,0),('Filippov',20,6,0,115,0),('Gavrilin',21,2,0,12,1),('Kostyuk',21,2,0,41,0),('Layushkin',21,1,0,25,0)],
'Tekstilshchik Kamyshin':[('Demin',25,7,0,65,0),('Kleymenov',18,7,0,98,0),('Polstyanov',26,4,2,169,2),('Nedorostkov',26,1,0,44,0),('Zazdravnykh',30,2,0,88,0),('Evseev',31,1,1,90,0),('Tereshchenko',21,1,1,90,0),('Soshenko',35,0,0,0,0),('Bukin',26,0,0,0,0)],
'Lokomotiv Moskva':[('Petrov',19,11,3,421,1),('Maryushkin',25,8,0,115,0),('But',21,4,1,153,0),('Rachimov',28,3,3,270,0),('Maminov',19,2,0,25,0),('Fedin',23,2,1,80,0),('Kiselev',23,1,0,6,0),('Veselov',20,1,0,35,1),('Ashurmamadov',25,1,0,25,0),('Chekmarev',21,0,0,0,0),('Evseev',20,0,0,0,0)],
'Spartak Vladikavkaz':[('Konovalov',20,7,0,242,1),('Sosnitsky',31,5,2,218,0),('Mozgovoy',27,4,0,79,0),('Ostaev',20,2,0,22,0)],
'Torpedo Moskva':[('Grishin',29,11,11,942,2),('Arefjev',22,11,7,613,0),('Kalaychev',30,9,8,715,0),('Khachatryan',25,8,5,477,0),('Aslanyan',26,6,3,276,0),('Skachenko',21,5,3,310,0),('Sevidov',24,3,1,81,0),('Kuzmichev',22,4,0,83,0),('Sudarikov',24,2,1,67,0),('Smirnov',16,2,1,65,0),('Kuznetsov',21,2,0,2,0)],
'Uralmash':[('Tkachenko',29,10,5,448,0),('Safin',21,12,1,309,0),('Bakharev',20,9,6,462,0),('Shushlyakov',27,11,2,358,0),('Titov',24,4,1,104,0),('Ignatov',23,3,1,92,0),('Arnautov',20,0,0,0,0)],
'CSKA Moskva':[('Masalitin',27,13,3,391,1),('Kupriyanov',20,9,5,529,0),('Broshin',31,6,5,477,2),('Shoukov',18,8,0,141,1),('Krutov',24,4,4,331,2),('Bystrov',26,3,3,270,0),('Oreshchuk',18,4,0,40,1),('Markevich',20,3,0,102,0),('Radimov',18,3,0,53,1),('Semyonov',21,2,0,42,0),('Khokhlov',18,1,0,28,0)],
'KAMAZ':[('Tsveiba',27,11,11,990,0),('Sakhno',32,11,8,656,2),('Babenko',21,10,8,658,2),('Fakhrutdinov',30,15,1,541,4),('Kuznetsov',35,8,6,437,3),('Kurakin',27,8,3,295,0),('Varlamov',18,7,5,445,0),('Tukhvatullin',19,7,0,143,0),('Snigirev',25,3,3,270,0),('Pivtsov',33,2,2,136,0),('Tsaplyuk',23,3,1,172,0)],
'Zhemchuzhina Sochi':[('Ignatyev',22,14,4,556,0),('Kuznetsov',21,18,1,538,0),('Titov',29,13,5,696,4),('Fedorov',28,9,6,561,0),('Protsenko',19,11,0,422,2),('Shinkarev',28,4,3,300,0),('Medvedev',22,3,1,86,0),('Yakovenko',18,1,0,37,0),('Kazentsov',22,0,0,0,0)],
'Dynamo Stavropol':[('Pobedennyi',27,4,4,360,-8),('Maslov',24,12,10,942,0),('Bogachev',26,10,10,900,0),('Osipyan',28,8,8,572,0),('Minibaev',27,7,7,630,0),('Yarygin',18,9,2,215,0),('Kaloev',20,6,0,111,0),('Sushiy',33,6,0,145,0),('Spanderashvili',24,3,3,243,0),('Volobuev',21,3,0,23,0),('Ivanov',21,2,0,24,0),('Kontsevenko',31,0,0,0,0)],
'Lokomotiv Nizhny Novgorod':[('Gadalov',20,4,3,273,0),('Gulyaev',30,2,0,24,0),('Abdulov',20,1,0,1,0),('Lysov',18,0,0,0,0),('Zaranko',16,0,0,0,0)],
'Krylia Sovetov':[('Gapotiy',23,12,3,394,0),('Fakhrutdinov',30,8,2,261,3),('Semin',25,4,1,146,0),('Zhupikov',39,3,1,123,0),('Fomin',24,3,1,98,0),('Dzneladze',25,2,2,180,0),('Tsiklauri',19,1,0,34,0),('Yumatov',19,1,0,57,0)],
'Luch Vladivostok':[('Khodoronok',28,9,2,274,0),('Koberskiy',19,12,0,205,0),('Bogdanov',27,9,3,381,0),('Kasyanenko',28,2,2,180,0),('Perminov',18,1,0,44,1),('Melnik',16,1,0,22,0)],
'Okean Nakhodka':[('Netunaev',33,9,7,552,0),('Ryabov',24,7,1,282,0),('Gatikoev',23,3,0,22,0),('Markin',27,2,1,150,0),('Tikhonovetskiy',20,1,0,4,0),('Kienko',19,1,0,1,0),('Kislyi',19,1,0,7,0),('Golovchenko',20,0,0,0,0),('Epurash',18,0,0,0,0)],
'Rostselmash':[('Andreyev',37,15,12,1039,7),('Loskov',19,18,6,759,1),('Parovin',28,10,9,769,0),('Golubkin',19,10,7,533,0),('Maslov',24,9,4,408,1),('Balakhnin',34,7,6,545,2),('Sereda',27,7,4,323,0),('Kovtun',23,3,3,270,0),('Yuri Klyuchnikov',30,2,2,180,0),('Vernigorov',21,2,0,49,0),('Skokov',21,1,1,59,0)],
'Asmaral Moskva':[('Shikunov',25,8,3,323,0),('Nikulin',23,9,4,430,2),('Medvedev',20,7,5,475,0),('Demin',19,5,5,450,0),('Semak',17,8,1,198,1),('Bekoev',24,7,1,237,0),('Khakhalev',27,6,2,278,1),('Grishin',20,2,1,54,0),('Kyrylov',18,1,0,10,0),('Zudenkov',23,2,0,48,0),('Gubernskiy',23,1,0,31,0),('Lushnikov',18,1,0,14,0),('Zhilkin',18,0,0,0,0),('Strikalov',24,0,0,0,0),('Zhdanov',20,0,0,0,0)],
}

# RSSSF rows: name, section, appearances, goals, DOB. Country defaults to Greece.
GREECE={
'AEK Athinon':[('Spyros Ikonomopoulos','GK',0,0,'26/07/59'),('Andreas Theodoropoulos','DEF',0,0,'27/06/71'),('Stavros Stamatis','MID',24,2,'13/01/66'),('Samouil Drakopoulos','FWD',0,0,'31/07/74'),('Pamtelis Konstantinidis','RES',0,0,'07/06/75'),('Christos Loukinas','RES',0,0,'05/03/73')],
'Panathinaikos':[('Asterios Jiotsas','DEF',8,0,'20/01/66'),('Jiorgos Kapouranis','DEF',21,2,'20/05/66'),('Louis Christodoulou','MID',23,4,'07/08/67'),('Paris Georgakopoulos','MID',0,0,'23/06/65'),('Jiorgos Kafes','FWD',0,0,'14/05/73'),('Periklis Papapanagis','FWD',2,0,'30/06/67')],
'Olympiakos Pireas':[('Ilias Talikriadis','GK',2,0,'10/07/65'),('Michalis Kousoulas','DEF',0,0,'11/06/69'),('Fabian Estay','MID',14,1,'05/10/68',23),('Takis Gkonias','MID',22,0,'06/10/71'),('Sotiris Mavromatis','MID',0,0,'21/02/66'),('Ilias Savvidis','MID',8,0,'03/01/67'),('Stamatis Syrigos','MID',1,0,'21/06/74'),('Nikos Anastopoulos','FWD',3,0,'22/01/58'),('Dimitris Kalykas','FWD',0,0,'17/05/74'),('Panagiotis Sofianopoulos','FWD',12,4,'07/07/68')],
'Aris Thessalonikis':[('Alekos Katsiaounis','GK',1,0,'22/06/62'),('Christos Tsaousidis','GK',0,0,'30/09/73'),('Kostas Kolomitrousis','DEF',0,0,'30/03/64'),('Kostas Mouratidis','DEF',1,0,'01/03/64'),('Th. Papadopoulos','DEF',0,0,'29/11/65'),('Thanasis Zacharopoulos','DEF',7,0,'04/02/75'),('Dimitris Mbougiouklis','MID',25,2,'12/05/64'),('Evripidis Samolis','MID',24,4,'23/01/65'),('Dimitris Grammenos','FWD',0,0,'05/10/68'),('Jiannis Petrakis','FWD',0,0,'17/02/69'),('Dimitris Polyzoidis','FWD',0,0,'06/02/71')],
'PAOK Thessalonikis':[('Apostolos Terzis','GK',0,0,'20/02/70'),('Kostas Iliadis','DEF',6,0,'21/04/62'),('Nikos Plitsis','DEF',2,0,'29/02/68'),('Vassilis Pekridis','MID',0,0,'28/11/72'),('Magdi Tolba','MID',0,0,'24/12/64',35),('Zacharias Toursounidis','MID',0,0,'24/02/74'),('Ioannis Anastasiadis','FWD',28,1,'13/08/68'),('T. Tcausila','FWD',8,1,''),('Thanasis Dimopoulos','FWD',0,0,'21/04/63'),('Jiorgos Toursounidis','FWD',12,1,'21/08/70')],
'Iraklis Thessalonikis':[('Jiorgos Plitsis','GK',9,0,'10/08/63'),('Jiannis Andreadis','DEF',1,0,'20/09/74'),('Jiorgos Dimitriadis','DEF',0,0,'16/09/72'),('Pagonis Vakalopoulos','DEF',8,0,'24/01/65'),('Valery Karimbof','MID',15,2,'01/02/71'),('Vassilis Xanthos','MID',1,0,'04/01/74'),('Vassilis Andreadis','FWD',8,0,'06/10/71'),('Kostas Giatias','FWD',0,0,'24/02/74'),('Stelios Katikaridis','FWD',4,2,''),('Ieroklis Stoltidis','FWD',6,1,'02/02/75'),('Stelios Tsamfiloglou','FWD',3,0,'11/10/72')],
'OFI Irakliou':[('Nikos Jialamas','GK',1,0,'13/05/71'),('Kostas Pavlopoulos','DEF',19,0,'26/12/71'),('Kostas Skentzos','DEF',12,0,'23/09/72'),('Andreadakis','FWD',2,0,'')],
'Skoda Xanthi':[('Stefanos Karkanis','GK',0,0,'07/12/73'),('Jiannis Tsakonakis','GK',5,0,'22/07/75'),('Dimitris Gavriil','DEF',0,0,'24/07/73'),('Konstantinidis','DEF',2,0,''),('Konstantopoulos','DEF',0,0,'07/12/69'),('F. Nalbantis','DEF',2,0,''),('Petros Teggelidis','DEF',28,8,'14/08/68'),('Zekeridis','DEF',11,0,''),('J. Papakonstantinou','MID',2,0,'22/07/67'),('Marco Perdague','MID',0,0,'14/07/71',63),('Nikos Doulis','FWD',1,0,'05/02/75'),('Andreas Zikos','FWD',10,0,'01/06/74')],
'Panionios':[('Nikos Paparounis','GK',0,0,'03/07/72'),('Stelios Roussis','GK',1,0,''),('Vlando Versemovic','DEF',6,0,'03/12/63',75),('Leonidas Vokolos','DEF',24,2,'02/06/70'),('Vitali Papadopoulos','MID',1,0,'08/08/65'),('Jiannis Vagias','MID',1,0,''),('Acimovic','FWD',7,0,'',31),('Nikos Tsakojiorgas','FWD',0,0,'14/09/71'),('Pantelis Tzoulis','FWD',10,1,'03/08/70')],
'AE Larisa':[('J. Papagiannopoulos','GK',0,0,''),('Triantafyllos Maggos','DEF',7,0,'30/07/70'),('Vaggelis Nasiakos','DEF',11,0,'07/08/67'),('Charalambos Nikolaou','DEF',15,0,''),('Jiorgos Papantoniou','DEF',16,0,'15/09/66'),('Kostas Taxiarchis','DEF',12,0,''),('Dimitris Zachos','DEF',1,0,''),('Tilemachos Ziakas','DEF',16,0,'29/08/67'),('Jiorgos Dodomtsakis','MID',3,0,'06/10/70'),('Jiannis Vasiliou','FWD',1,0,'18/05/74')],
'Levadiakos':[('Jiorgos Kontopoulos','GK',6,0,'16/11/70'),('Jiorgos Kaitazis','DEF',2,0,'22/02/65'),('Lazaros Kyrillidis','DEF',5,0,'09/04/63'),('Pantelis Megaritis','DEF',0,0,'12/03/70'),('Theodoros Pallis','DEF',0,0,'22/01/73'),('Christos Theocharis','DEF',13,0,'14/09/69'),('Jiannis Papanikoloau','MID',28,3,'31/08/69'),('Sotiris Zerkoulis','FWD',11,0,'04/10/69'),('Nikos Mbonovas','RES',0,0,'12/06/74'),('Kostas Zarkadoulas','RES',0,0,'04/09/74')],
'Athinaikos':[('Aggelos Pliotas','GK',0,0,'18/12/71'),('Tasos Kalogeropoulos','DEF',1,0,'15/07/66'),('Jiorgos Koltsos','DEF',2,0,'10/10/79'),('Kostas Tsironis','DEF',25,0,'05/07/71'),('Nikos Delezas','MID',0,0,'13/01/73'),('Kostas Poulios','MID',2,0,'15/08/73'),('Michalis Tsoumas','MID',0,0,'10/02/70'),('Jiorgos Zotalis','MID',9,1,'10/06/67'),('Miltiadis Christinakis','FWD',3,0,'10/01/70'),('Petros Jiavroutas','FWD',0,0,'08/08/69'),('Jiorgos Kaffes','FWD',3,0,'15/05/73')],
'Apollon Athinas':[('Nikos Chamouzas','GK',2,0,'03/07/68'),('Thanasis Kolitsidakis','DEF',10,0,'21/11/66'),('Takis Konstantopoulos','DEF',0,0,'01/03/74'),('Dimitris Roussos','DEF',15,0,'30/04/71'),('Theodoros Antonakos','MID',2,0,'23/07/70'),('Theofilos Karasavvidis','MID',31,3,'24/04/71'),('Christos Kondylis','MID',0,0,'31/07/72'),('Pavlos Papoutsis','MID',0,0,'02/08/72'),('Christos Petropoulos','MID',0,0,'21/11/73'),('Jiorgos Xanthopoulos','MID',5,0,'24/03/72'),('Djurdjevic','FWD',13,1,''),('Jiorgos Emmanouil','FWD',0,0,'18/03/68'),('Aris Karasavvidis','FWD',12,5,'13/03/65'),('Ilias Mboulios','FWD',0,0,'24/05/67')],
'Edessaikos':[('Naoum Takos','GK',0,0,'03/11/60'),('Jiorgos Karaisaridis','DEF',2,0,'25/07/71'),('Tasos Lefkopoulos','DEF',1,0,'20/01/65'),('Efstathios Mavridis','DEF',0,0,'13/10/75'),('Jiorgos Theodoridis','DEF',15,0,'08/07/73'),('S. Tsavalakoglou','DEF',0,0,'06/11/75'),('Apostolos Tsoptsis','MID',0,0,'21/01/72'),('Thymios Karytiadis','FWD',0,0,'21/02/70'),('Jiannis Vitevis','FWD',0,0,'23/11/74'),('Paris Zoumboulis','FWD',32,7,'30/08/70')],
'Doxa Dramas':[('Jiorgos Mberberidis','GK',0,0,'10/07/75'),('Vassilis Anastiadis','DEF',0,0,'18/03/72'),('Jiorgos Georgiadis Savvas','DEF',12,3,'08/03/72'),('St. Pachatouridis','DEF',6,0,'05/05/71'),('Thymios Rafailidis','DEF',6,0,'05/03/74'),('Miltiadis Telidis','DEF',21,0,'10/10/67'),('Christos Kiosses','FWD',24,0,'03/01/71'),('Zoumboulis Lazaridis','FWD',7,0,'27/08/73'),('Jiannis Thomaidis','FWD',27,7,'29/02/72'),('Jiannis Toubouzoglou','FWD',0,0,'07/03/69')],
'Panachaiki':[('Kostas Lagaris','GK',1,0,'01/03/64'),('Nikos Zafiropoulos','GK',4,0,''),('Jiannis Achajiotis','DEF',1,0,'04/09/71'),('Roland Iliadis','DEF',15,0,'18/08/63',8),('Vassilis Kotsaftis','DEF',0,0,'26/03/74'),('Jiannis Zerdevas','DEF',26,1,'23/08/61'),('Djurjevic','FWD',6,0,''),('Jiorgos Klaoudatos','FWD',0,0,'19/09/74')],
'Apollon Kalamarias':[('Vassilis Karyofyllidis','GK',1,0,'09/08/75'),('Karakasidis','GK',3,0,''),('Mbaltidis','GK',1,0,''),('Thanasis Dermitzoglou','DEF',7,1,'21/10/74'),('Nikos Tziolas','MID',6,0,'13/05/72'),('Theodoros Voutiritsas','MID',3,0,'27/07/62'),('Nikiforos Kakoglou','FWD',0,0,'25/04/72'),('Palatsidis','FWD',12,3,''),('Zoran Tosic','FWD',7,0,'',31)],
'Naousa':[('Christos Moschopoupos','GK',0,0,'19/12/74'),('Sgouros','GK',1,0,''),('Ilias Stojiannis','GK',1,0,'03/04/76'),('Christos Tseliopoulos','GK',3,0,'14/04/69'),('Kyriakos Intsiadis','DEF',0,0,'16/08/73'),('Damianos Theodoridis','DEF',0,0,'30/12/68'),('Leonidas Vosdou','DEF',7,0,'22/06/60'),('Jiannis Kourogeorgakis','MID',11,0,'15/05/69'),('Christos Paschalis','MID',16,0,'20/02/72'),('Michalis Rizopoulos','MID',5,0,'11/02/74'),('Thanasis Glossis','FWD',2,0,'21/09/60')],
}

ROLE={'GK':0,'DEF':3,'MID':7,'FWD':17,'RES':7}

def dob(raw:str):
    if not raw:return None,None
    d=datetime.strptime(raw,'%d/%m/%y').date()
    if d.year>=2000:d=d.replace(year=d.year-100)
    at=date(1993,8,22);age=at.year-d.year-((at.month,at.day)<(d.month,d.day))
    return d.isoformat()+'T00:00:00',age

def norm(s):
    import unicodedata,re
    s=unicodedata.normalize('NFKD',str(s or ''))
    s=''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9]+',' ',s.lower()).strip()

def append_bdf(path:Path, extras:dict):
    x=json.load(open(path,encoding='utf8'));added=0
    for c in x['clubs']:
        have={norm(r['bdfutbol_name']) for r in c['players']}
        for name,age,apps,starts,mins,goals in extras[c['name']]:
            if norm(name) in have:continue
            c['players'].append({'bdfutbol_name':name,'age_1993_94':age,'appearances':apps,'starts':starts,'minutes':mins,'goals':goals,'core_18_candidate':False,'source_roster_member':True})
            have.add(norm(name));added+=1
    if 'source_policy' in x:
        x['source_policy']='All player rows listed by the pinned BDFutbol 1993-94 club squad pages are retained; 18 is a minimum safety floor, never a truncation target; no fictional filler.'
    if 'selection_policy' in x:
        x['selection_policy']='All player rows listed by the pinned BDFutbol season squad pages; 18 is minimum only; no fictional filler.'
    path.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return added,{c['name']:len(c['players']) for c in x['clubs']}

def append_greece(path:Path):
    x=json.load(open(path,encoding='utf8'));added=0
    for c in x['clubs']:
        have={norm(r['rsssf_name']) for r in c['players']}
        for row in GREECE[c['name']]:
            name,sec,apps,goals,raw,*country=row
            if norm(name) in have:continue
            bd,age=dob(raw)
            cid=country[0] if country else 47
            c['players'].append({'rsssf_name':name,'section':sec,'appearances':apps,'goals':goals,'birth_date':bd,'historical_age_1993_94':age,'country_id':cid,'suggested_primary_role':ROLE[sec],'source_url':'https://www.rsssf.org/tablesg/grk94.html','core_18_candidate':False,'source_roster_member':True})
            have.add(norm(name));added+=1
    x['selection_policy']='Full available RSSSF 1993-94 season roster per club, including reserves/zero-appearance entries explicitly listed by the source; 18 is minimum only; no fictional filler. Midseason participants retain season-roster provenance.'
    path.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return added,{c['name']:len(c['players']) for c in x['clubs']}

def annotate_countries_1993():
    p=DATA/'historical_source_catalog.json';x=json.load(open(p,encoding='utf8'))
    by={int(c['source_id']):c for c in x['countries']}
    valid={104:('Georgia','Independent state in 1993'),132:('Kazajistán','Independent state in 1993'),202:('Tayikistán','Independent state in 1993'),78:('Sudáfrica','State valid in 1993'),31:('Croacia','Independent state in 1993'),20:('Bosnia-Herzegovina','Independent state in 1993'),37:('Eslovenia','Independent state in 1993'),54:('Macedonia','Independent state in 1993; historical short label used by game'),75:('República Federal de Yugoslavia','1993 state represented by the legacy Serbia source id for compatibility'),88:('Zaire','1993 historical name for the state now represented by D.R. Congo source id')}
    invalid={76:'Montenegro was not a separate state in 1993; use FR Yugoslavia context',129:'Kosovo was not a separate state in 1993; use FR Yugoslavia context'}
    for cid,(label,note) in valid.items():
        if cid in by:
            by[cid]['historical_name_1993']=label;by[cid]['valid_as_state_1993']=True;by[cid]['historical_state_note_1993']=note
    for cid,note in invalid.items():
        if cid in by:
            by[cid]['valid_as_state_1993']=False;by[cid]['historical_state_note_1993']=note
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    ctx={'schema_version':1,'reference_year':1993,'policy':'Nationalities and country labels used by the historical game must follow the political map of 1993. Modern source IDs may be retained internally for compatibility, but their historical label/state context controls display and eligibility.','historical_labels':{str(k):v[0] for k,v in valid.items()},'not_separate_states_1993':{str(k):v for k,v in invalid.items()}}
    (DATA/'country_context_1993.json').write_text(json.dumps(ctx,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def main():
    ta,tc=append_bdf(DATA/'turkey_1993_94_roster_staging.json',TURKEY)
    ra,rc=append_bdf(DATA/'russia_1993_roster_staging.json',RUSSIA)
    ga,gc=append_greece(DATA/'greece_1993_94_roster_staging.json')
    annotate_countries_1993()
    bel=json.load(open(DATA/'belgium_1993_94_roster_staging.json',encoding='utf8'))
    bc={c['name']:len(c['players']) for c in bel['clubs']}
    out={'status':'expanded_source_rosters','policy':'All historically documented season-roster rows are retained; 18 is a minimum safety floor, never a truncation target.','added':{'Belgium':0,'Turkey':ta,'Russia':ra,'Greece':ga},'totals':{'Belgium':sum(bc.values()),'Turkey':sum(tc.values()),'Russia':sum(rc.values()),'Greece':sum(gc.values())},'minimums':{'Belgium':min(bc.values()),'Turkey':min(tc.values()),'Russia':min(rc.values()),'Greece':min(gc.values())},'counts':{'Belgium':bc,'Turkey':tc,'Russia':rc,'Greece':gc}}
    (DATA/'bel_tur_rus_gre_full_roster_depth_audit.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps(out,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
