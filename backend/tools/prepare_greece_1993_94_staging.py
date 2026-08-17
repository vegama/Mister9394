from __future__ import annotations
from pathlib import Path
import json
from datetime import date, datetime

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'data/football9394/greece_1993_94_roster_staging.json'
SOURCE = 'https://www.rsssf.org/tablesg/grk94.html'

# Compact factual transcription from the RSSSF 1993/94 roster section.
# Format: name|section|appearances|goals|dd/mm/yy|country_id
# country_id omitted/47 = Greece; foreign country ids follow the MDB country catalog.
RAW = {
'AEK Athinon': '''
Ilias Atmatzidis|GK|33|0|20/04/69|47
Vassilis Karajiannis|GK|1|0|27/09/69|47
Jiorgos Agorojiannis|DEF|24|0|03/05/66|47
Vaios Karajiannis|DEF|25|0|25/06/68|47
Jiorgos Koutoulas|DEF|12|0|09/02/67|47
Stelios Manolas|DEF|24|2|13/07/61|47
Manolis Papadopoulos|DEF|10|0|22/04/68|47
Michalis Vlachos|DEF|26|1|20/09/67|47
Michalis Kasapis|MID|29|3|06/06/71|47
Charis Kopitsis|MID|11|1|05/03/69|47
Tasos Mitropoulos|MID|30|0|23/08/57|47
Refik Sabanasovic|MID|24|0|02/08/65|20
Tony Savefsky|MID|32|3|14/06/63|54
Vassilis Tsartas|MID|22|3|12/12/72|47
Alekos Alexandris|FWD|32|24|21/10/68|47
Vassilis Dimitriadis|FWD|33|11|01/02/66|47
Vassilis Mborbokis|FWD|24|1|10/02/69|47
Zoran Zliskovic|FWD|26|7|01/03/66|31
''',
'Panathinaikos': '''
Antonis Nikopolidis|GK|0|0|04/01/71|47
Jiosef Wandzcyk|GK|34|0|13/08/63|70
Stratos Apostolakis|DEF|26|2|11/05/64|47
Jiorgos Georgiadis Savvas|DEF|5|0|30/01/71|47
Jiannis Kalitzakis|DEF|28|1|10/12/66|47
Thanasis Kolitsidakis|DEF|10|0|21/11/66|47
Kostas Mavridis|DEF|20|2|07/07/62|47
Marinos Ouzounidis|DEF|20|2|10/10/68|47
Kostas Antoniou|MID|24|1|19/04/62|47
Juan Jose Borrelli|MID|16|2|11/08/70|63
Kostas Frantzeskos|MID|17|4|04/01/69|47
Jiorgos Georgiadis Charal.|MID|31|6|14/01/70|47
Spyros Maragkos|MID|28|1|03/07/67|47
Mikos Niomblias|MID|29|3|17/01/65|47
Jiorgos Donis|FWD|24|8|20/10/69|47
Dimitris Saravakos|FWD|25|12|27/06/61|47
Krystof Warzycha|FWD|31|24|17/11/64|70
Dimitris Markou|MID|13|4|31/01/71|47
''',
'Olympiakos Pireas': '''
Alekos Rantos|GK|24|0|29/10/66|47
Foti Strakosha|GK|8|0|29/03/65|8
Jiorgos Amanatidis|DEF|30|3|04/04/70|47
Vassilis Ioannidis|DEF|23|2|24/06/67|47
Chris Kalatzis|DEF|15|2|27/07/67|47
Koulis Karantaidis|DEF|31|1|04/07/65|47
Jiorgos Mitsimbonas|DEF|21|3|01/11/62|47
Theodoros Pachatouridis|DEF|28|2|04/09/67|47
Minas Chatzidis|MID|31|5|04/07/66|47
Vassilis Karapialis|MID|21|1|13/06/65|47
Daniel Lima-Batista|MID|24|5|09/09/64|62
Gennadi Litovcenko|MID|27|2||85
Jiotis Tsalouchidis|MID|29|11|30/03/63|47
Nikos Tsiantakis|MID|30|3|20/10/63|47
Bent Christiansen|FWD|26|9|04/01/67|33
Vassilis Mouratidis|FWD|11|3|04/01/67|47
Oleg Protasov|FWD|9|8|14/02/64|85
Jiorgos Vaitsis|FWD|17|0|30/07/67|47
''',
'Aris Thessalonikis': '''
Christos Karkamanis|GK|33|0|02/09/69|47
Vaggelis Koentas|GK|0|0|30/06/72|47
Jiorgos Chrisostomidis|DEF|18|2|05/10/68|47
Trainos Dellas|DEF|1|0|31/01/76|47
Jiorgos Iosifidis|DEF|14|0|23/01/67|47
Kostas Konstantinidis|DEF|22|1|07/04/62|47
Jiorgos Koltsidas|DEF|22|1|22/09/70|47
Jiorgos Stratilatis|DEF|29|0|13/03/65|47
Theodoros Dalkidis|MID|22|4|01/12/69|47
Ivan Silva Santos|MID|28|8|17/04/67|62
Savvas Kofidis|MID|33|0|12/02/61|47
Arthur Lekbelo|MID|7|0|23/02/66|8
M. Mitsopoulos|MID|26|2|02/04/69|47
Antonis Sapountzis|MID|29|5|19/01/71|47
Stavros Imbriakos|FWD|19|1|30/11/75|47
Zoran Loncar|FWD|25|13|08/05/66|75
Lubisa Milojevic|FWD|31|12|01/04/67|75
Thanasis Jiannakidis|FWD|1|0|29/05/75|47
''',
'PAOK Thessalonikis': '''
Nikos Michopoulos|GK|21|0|20/02/70|47
Vaggelis Pourliotopoulos|GK|13|0|13/04/69|47
Alexis Alexiou|DEF|33|4|08/09/63|47
Pavlos Dermitzakis|DEF|17|5|29/06/69|47
Dimitris Kapetanopoulos|DEF|29|0|12/04/69|47
Kostas Malioufas|DEF|18|0|01/09/63|47
Nikos Panagiotidis|DEF|28|0|02/12/70|47
Theodoros Zagorakis|DEF|30|1|17/10/71|47
Jiannis Antonas|MID|7|0|24/07/73|47
Kostas Ikonomidis|MID|32|2|17/07/66|47
Kostas Lagonidis|MID|24|13|01/07/65|47
V. Kalfadopoulos|MID|0|0|21/01/72|47
Jiannis Voltezos|MID|10|0|15/08/71|47
Stefanos Bormbokis|FWD|18|3|01/09/66|47
Ioakim Makis Chavos|FWD|30|4|05/09/69|47
Antonis Jioungoudis|FWD|30|2|13/05/69|47
Aris Karasavvidis|FWD|17|1|13/03/65|47
Milan Luchovi|FWD|28|16|01/11/63|61
''',
'Iraklis Thessalonikis': '''
Polychronis Kalligas|GK|11|0|26/10/70|47
Apostolos Lekidis|GK|14|0|01/03/68|47
Jiorgos Anatolakis|DEF|31|0|16/03/74|47
Athanasios Chtzoglou|DEF|11|0|03/06/72|47
Predrag Erak|DEF|27|0|01/07/70|75
Nikos Nentidis|DEF|21|0|07/06/66|47
Daniil Papadopoulos|DEF|23|0|15/06/63|47
A. Xenitopoulos|DEF|19|0|28/07/71|47
Ivan Jiovanovic|MID|27|4|08/07/62|75
Stergios Noulis|MID|0|0|19/07/75|47
Jiorgos Papadopoulos|MID|17|3|13/11/67|47
Jiorgos Peglis|MID|12|0|25/12/73|47
Milan Petsanovic|MID|30|7|18/07/73|75
Jiorgos Skartados|MID|29|5|07/04/60|47
Christos Kostis|FWD|30|10|15/01/72|47
Jiorgos Kostis|FWD|28|2|07/10/72|47
Nikos Sakellaridis|FWD|19|1|30/09/70|47
Theofanis Tountziaris|FWD|33|20|08/01/65|47
''',
'OFI Irakliou': '''
Kostas Chaniotakis|GK|26|0|19/07/68|47
Vaggelis Chosadas|GK|7|0|17/02/61|47
Lyssandros Georgamlis|DEF|23|8|25/02/62|47
Mbambis Mystakidis|DEF|31|1|01/03/64|47
Nikos Papadopoulos|DEF|30|1|05/10/71|47
Manolis Patmetzis|DEF|22|0|22/04/64|47
Ilias Poursanidis|DEF|25|0|13/05/71|47
Stefanos Vavoulas|DEF|21|2|04/01/65|47
Dragan Djuganovic|MID|20|8|29/10/69|75
Kostas Kiassos|MID|2|0|13/12/75|47
Danut Lupu|MID|9|1|27/02/67|72
Petros Marinakis|MID|23|6|16/12/68|47
Jiannis Samaras|MID|23|1|03/05/61|47
Giorgos Tsifoutis|MID|33|3|14/10/68|47
Alexis Alexoudis|FWD|26|9|20/06/72|47
Jiorgos Athanasiadis|FWD|31|4|16/12/63|47
Nikos Machlas|FWD|31|9|16/06/73|47
Jiasmigo Velic|FWD|22|2|01/09/65|20
''',
'Skoda Xanthi': '''
Jiorgos Jiourgousis|GK|15|0|16/04/64|47
Jiorgos Mirtsos|GK|16|0|11/12/64|47
Jiorgos Chalkidis|DEF|20|1|03/08/64|47
Nikos Karageorgiou|DEF|22|7|08/12/62|47
Nikos Kechajias|DEF|26|1|22/10/69|47
Nikos Kostenoglou|DEF|26|2|03/10/70|47
Ivan Mitev|DEF|28|2|27/07/66|21
Christos Samaras|DEF|26|1|26/09/73|47
Macheridis|MID|9|1||47
Anastasios Malousis|MID|14|1|22/02/67|47
Makis Tzantzos|MID|30|5|06/11/67|47
Alexandros Vasi|MID|21|3|13/04/68|8
Juri Zaleski|MID|15|0|20/10/65|61
Chondrokoukis|MID|1|0|05/05/75|47
Christos Maladenis|FWD|31|2|23/05/74|47
Veridiano Marcelo|FWD|33|10|30/06/66|62
Lenzo Panou|FWD|16|10|23/05/68|8
Zisis Vryzas|FWD|30|6|09/11/73|47
''',
'Panionios': '''
Jiorgos Ambadiotakis|GK|27|0|21/03/67|47
Dimitris Barbalias|GK|6|0|06/03/61|47
Takis Fyssas|DEF|18|0|18/01/73|47
Jiannis Grigoriou|DEF|25|0|14/01/66|47
Nikos Kourbanas|DEF|26|1|22/03/62|47
Dimitris Kouzinos|DEF|14|0|31/08/67|47
Dimitris Nalitzis|DEF|11|2|10/07/76|47
Jiorgos Togias|DEF|28|1|21/01/60|47
Jiorgos Famelis|MID|18|4|19/08/67|47
Neboisa Krupnikovic|MID|30|9||75
Apostolos Mantzios|MID|27|0|21/10/69|47
Miliko Pantic|MID|26|8|05/06/66|75
Stavros Refenes|MID|24|0|19/02/70|47
Themistoklis Tzanetis|MID|27|0|10/01/69|47
Nikos Katsiaros|FWD|8|0|30/11/74|47
Andreas Lagonikakis|FWD|30|7|03/04/72|47
Nikos Mirtsekis|FWD|30|8|04/04/68|47
Kostas Tsavalias|FWD|17|1|10/01/64|47
''',
'AE Larisa': '''
Aggelos Georgiou|GK|8|0|13/08/74|47
Christos Michail|GK|26|0|28/02/62|47
Jiannis Alexoudis|DEF|21|1|22/04/64|47
Kostas Kolomitrousis|DEF|19|0|30/03/64|47
Lazaros Kyrillidis|DEF|1|0|09/04/63|47
Kostas Mouratidis|DEF|18|5|01/03/64|47
Thanasis Ntelopoulos|DEF|17|1|20/02/69|47
Dimitris Tzotzios|DEF|30|0|28/12/69|47
Paolo Da Silva|MID|28|8|17/07/67|62
Kostas Nembegleras|MID|14|0||47
Jiannis Providas|MID|29|8|20/11/75|47
Stephan Stoika|MID|26|4|23/06/67|72
Jiannis Tsakmakidis|MID|15|1|02/02/74|47
Vaggelis Tsoukalis|MID|27|6|16/09/63|47
Marceu Iza|FWD|28|5|28/06/66|62
Lefteris Milos|FWD|28|3|02/04/66|8
Dimitris Nikolakoulis|FWD|6|0|18/03/70|47
Alexandros Tzanis|FWD|3|0||47
''',
'Levadiakos': '''
Mirsa Jionus|GK|33|0||54
Kostas Katsimitros|GK|3|0|01/05/66|47
Nikos Gkoulis|DEF|29|1|18/02/59|47
Spyros Gkoulis|DEF|25|0|17/05/64|47
Fotis Lagos|DEF|30|0|17/01/71|47
Andreas Loukas|DEF|25|2|15/05/67|47
Jiannis Martinaios|DEF|30|0|03/10/59|47
Nikos Markou|DEF|27|3|11/08/70|47
Kostas Galamelos|MID|2|0|03/01/74|47
Thanasis Kalogrias|MID|3|0|30/03/74|47
Vladimir Koic|MID|32|8|12/07/65|75
Vaggelis Kryos|MID|20|0|23/09/73|47
Dimitris Lazarou|MID|25|1|06/08/70|47
Michalis Mbletsas|MID|26|2|24/11/65|47
Davor Jiakovlevic|FWD|27|4|07/09/67|75
Vaggelis Kalogeropoulos|FWD|2|0|13/02/65|47
Thanasis Mbasbanas|FWD|5|0|16/04/65|47
Kostas Tsanas|FWD|28|9|22/08/67|47
''',
'Athinaikos': '''
Jiorgos Dafkos|GK|31|0|08/01/59|47
Nikos Kefalas|GK|3|0|28/08/68|47
Tasos Chatziaggelis|DEF|34|0|03/03/59|47
Theodoros Mboutsoukas|DEF|19|0|20/01/66|47
Zannis Monnos|DEF|11|0|09/02/67|47
Panagiotis Papadopoulos|DEF|17|0|25/04/73|47
Dimitris Thanopoulos|DEF|26|1|01/01/64|47
Kostas Theodorakos|DEF|29|0|29/06/69|47
Michalis Alvertis|MID|31|6|05/04/72|47
Jiorgos Anastasiou|MID|31|3|14/10/63|47
Nikos Kardianos|MID|7|0|08/05/72|47
Salvatore Katsaj|MID|28|2|23/10/67|8
Nikos Mavrommatis|MID|22|2|18/07/69|47
Danir Spica|MID|19|3|11/11/62|75
Miroslav Bong|FWD|27|6|23/11/61|70
Tzimis Patikas|FWD|29|1|18/10/63|47
Antonis Spinoulas|FWD|17|4|23/10/69|47
Vassilis Tzalakostas|FWD|15|5|20/07/59|47
''',
'Apollon Athinas': '''
Jiorgos Kavaratzis|GK|4|0|10/07/72|47
Antonis Minou|GK|32|0|04/05/58|47
Dimitrios Ioannou|DEF|15|0||47
Takis Karagiozopoulos|DEF|18|0|04/02/61|47
Vaggelis Kefalas|DEF|24|0|31/07/73|47
Lachanas|DEF|9|0||47
Alvertos Papadakis|DEF|12|0|22/08/68|47
Kostas Pozapalidis|DEF|31|0|24/08/66|47
Jiannis Apostolou|MID|22|0|19/01/69|47
Boskovic|MID|10|0||75
Imre Katsenbach|MID|12|0|05/04/64|93
Milenko Kosavevic|MID|29|4|06/11/63|75
Antonis Platinakis|MID|24|2|23/04/71|47
Lefteris Velentzas|MID|33|6|11/10/69|47
Theodoros Alexis|FWD|31|3|06/05/75|47
Sakis Moustakidis|FWD|5|0|24/08/68|47
Ntemis Nikolaidis|FWD|18|5|19/04/73|47
Ily Seou|FWD|15|2|08/11/68|8
''',
'Edessaikos': '''
Dimitris Neofotistos|GK|4|0|08/08/71|47
Radek Ranbusic|GK|30|0|21/11/63|61
Nikos Charalambous|DEF|25|0|28/10/61|47
Thomas Delijiannis|DEF|21|2|20/03/62|47
Vassilis Kotsifas|DEF|27|0|23/10/69|47
M. Kouroukerezis|DEF|23|0|26/01/65|47
Jiorgos Ladias|DEF|24|1|12/02/63|47
Petros Pasalis|DEF|18|0|10/04/74|47
Christo Kolev|MID|27|7|21/09/64|21
Vaggelis Koutsoures|MID|12|0|16/02/75|47
Dimitris Stafylidis|MID|24|0|01/01/65|47
Thanasis Tentzos|MID|2|0|18/03/70|47
Theodoros Tsoleridis|MID|27|2|01/12/60|47
Jiorgos Tsoptsis|MID|27|0|09/03/75|47
Jiorgos Mbetas|FWD|23|3|10/06/68|47
Iakovos Papadopoulos|FWD|10|0|07/09/61|47
Jiorgos Papadopoulos|FWD|33|6||47
Sasha Skara|FWD|32|12|18/10/67|75
''',
'Doxa Dramas': '''
Panagiotis Logaras|GK|5|0|29/03/70|47
Kyriakos Tochouroglou|GK|29|0|13/08/72|47
Dimitris Aivazidis|DEF|17|0|07/10/72|47
Jiorgos Drogalas|DEF|28|0|23/09/63|47
Jiannis Jiaslanis|DEF|12|0|25/10/71|47
Jiorgos Kalpakis|DEF|23|0|20/03/70|47
Apostolos Terzis|DEF|21|1|13/03/71|47
Kostas Vasilakakis|DEF|19|0|27/03/57|47
Branislav Koitcic|MID|0|0|12/01/65|75
Thanasis Kosmidis|MID|21|0|06/05/73|47
Spyros Mposkopsiou|MID|0|0|16/11/69|47
Alekos Panagiotidis|MID|9|0|16/01/68|47
Aggelos Pimenidis|MID|0|0|07/08/69|47
Avraam Xanthopoulos|MID|24|1|08/08/72|47
Kyriakos Alexandridis|FWD|31|6|08/05/61|47
Miroslav Alexic|FWD|28|5|21/07/60|75
Michalis Iordanidis|FWD|26|10|01/01/62|47
Zeliko Lekovic|FWD|30|2|07/12/70|75
''',
'Panachaiki': '''
Alekos Katsiaounis|GK|8|0|22/06/62|47
Panagiotis Masouras|GK|22|0|22/10/65|47
Theodoros Andriopoulos|DEF|24|2|16/01/65|47
Dimitris Argyropoulos|DEF|19|0|15/07/74|47
Dimitris Gkenas|DEF|32|5|21/07/64|47
Mathaios Gontzias|DEF|28|1|14/06/70|47
Milan Marisic|DEF|29|0|12/10/64|75
Christos Mikes|DEF|27|0|23/09/71|47
Alfredos Fergos|MID|26|1|15/10/64|8
Grigoris Georgatos|MID|28|5|31/10/72|47
Sinisa Gonzalovic|MID|11|1|24/10/66|75
Spilios Jiovas|MID|3|0|10/10/70|47
Christos Karapitsos|MID|20|0|27/04/70|47
Jiorgos Kyriakopoulos|MID|29|4|27/07/65|47
Iraklis Anastasakis|FWD|15|5|22/12/71|47
Apostolis Drakopoulos|FWD|32|3|11/12/66|47
Amaeki Otitzi|FWD|17|8|28/12/66|59
Periklis Stathopoulos|FWD|6|0|30/08/73|47
''',
'Apollon Kalamarias': '''
Evgenios Piniotis|GK|25|0|16/11/67|47
Panagiotis Tsiapos|GK|4|0|30/08/63|47
Jiannis Dimitriadis|DEF|27|1|05/01/70|47
Christos Kalimanis|DEF|27|1|05/06/64|47
Spyros Mbaxevanos|DEF|17|1|17/01/71|47
Vaggelis Spyliotis|DEF|5|0|08/06/65|47
Dimitris Tomboulidis|DEF|31|0|10/01/60|47
Kostas Tsouloukidis|DEF|27|0|30/03/69|47
Nikos Patinios|MID|13|0|23/03/68|47
Nikos Samoladas|MID|27|1|24/01/70|47
Sergian Savisevic|MID|24|4|14/06/71|75
Jiorgos Semertzidis|MID|19|0|14/07/57|47
Zisis Tsekos|MID|29|3|29/08/64|47
Gkekas|MID|16|1||47
Sokol Koushta|FWD|24|10|17/08/64|8
Dimitris Nolis|FWD|25|7|21/09/67|47
Michalis Samaras|FWD|30|4|09/09/65|47
Jiorgos Vlachoulis|FWD|29|4|03/01/69|47
''',
'Naousa': '''
Nikos Sfyntilas|GK|6|0|27/02/62|47
Vaggelis Vourdojiannis|GK|23|0|03/08/70|47
Christos Chatzidakis|DEF|25|1|18/12/70|47
Jiannis Fassidis|DEF|24|1|11/10/71|47
Savvas Iakovidis|DEF|27|0|12/08/66|47
Spyros Nousias|DEF|24|3|11/01/73|47
Iliev Penev|DEF|28|2|14/10/66|21
Grigoris Troupkos|DEF|27|1|11/12/71|47
Vassilis Argyriou|MID|30|3|12/01/66|47
Jionovic|MID|16|0||75
Panagiotis Katsouris|MID|13|1|10/05/76|47
Vassilis Kourogeorgakis|MID|25|1|17/01/68|47
Vassilis Lakis|MID|17|2|10/07/76|47
Miroslav Zifkovic|MID|23|4|12/07/70|75
Michalis Alexiadis|FWD|24|8|04/06/66|47
Dimitriadis|FWD|13|4||47
Nikos Kyzeridis|FWD|24|2|20/04/71|47
Ilias Sambanis|FWD|25|5|15/08/73|47
''',
}

POSITIONS = {
    'GK': [0, 0],
    'DEF': [3, 4, 1, 2, 3, 4],
    'MID': [6, 7, 8, 9, 13, 7],
    'FWD': [17, 17, 12, 16, 17, 17],
}
ORDER = [
    ('AEK Athinon', 1), ('Panathinaikos', 2), ('Olympiakos Pireas', 3), ('Aris Thessalonikis', 4),
    ('PAOK Thessalonikis', 5), ('Iraklis Thessalonikis', 6), ('OFI Irakliou', 7), ('Skoda Xanthi', 8),
    ('Panionios', 9), ('AE Larisa', 10), ('Levadiakos', 11), ('Athinaikos', 12),
    ('Apollon Athinas', 13), ('Edessaikos', 14), ('Doxa Dramas', 15), ('Panachaiki', 16),
    ('Apollon Kalamarias', 17), ('Naousa', 18),
]

def parse_dob(raw: str):
    raw = raw.strip()
    if not raw:
        return None, None
    try:
        d = datetime.strptime(raw, '%d/%m/%y').date()
        # strptime maps 00-68 to 2000-2068; all these players are pre-1980.
        if d.year >= 2000:
            d = d.replace(year=d.year - 100)
        age = 1993 - d.year - ((8, 22) < (d.month, d.day))
        return d.isoformat() + 'T00:00:00', age
    except ValueError:
        return None, None

def main():
    from expand_bel_tur_rus_gre_rosters_v030 import GREECE, ROLE, dob as extra_dob
    clubs=[]
    seen=[]
    for team_name, pos in ORDER:
        rows=[]; section_idx={k:0 for k in POSITIONS}
        raw_lines=[ln.strip() for ln in RAW[team_name].strip().splitlines() if ln.strip()]
        if len(raw_lines)<18:
            raise RuntimeError(f'{team_name}: below 18-player safety floor: {len(raw_lines)}')
        for line in raw_lines:
            parts=line.split('|')
            if len(parts)!=6: raise RuntimeError((team_name,line,parts))
            name,section,apps,goals,dob_raw,cid=parts
            idx=section_idx[section]; section_idx[section]+=1
            role=POSITIONS[section][min(idx,len(POSITIONS[section])-1)]
            dob,age=parse_dob(dob_raw)
            rows.append({
                'rsssf_name':name,'section':section,'appearances':int(apps),'goals':int(goals),
                'birth_date':dob,'historical_age_1993_94':age,'country_id':int(cid or 47),
                'suggested_primary_role':role,'source_url':SOURCE,
            })
            seen.append((team_name,name,dob_raw))
        have={r['rsssf_name'] for r in rows}
        for extra in GREECE[team_name]:
            ename,section,apps,goals,dob_raw,*country=extra
            if ename in have: continue
            bd,age=extra_dob(dob_raw);cid=country[0] if country else 47
            rows.append({'rsssf_name':ename,'section':section,'appearances':apps,'goals':goals,'birth_date':bd,'historical_age_1993_94':age,'country_id':cid,'suggested_primary_role':ROLE[section],'source_url':SOURCE,'core_18_candidate':False,'source_roster_member':True})
            have.add(ename)
        clubs.append({'name':team_name,'historical_position':pos,'rsssf_roster_url':SOURCE,'players':rows})
    out={
        'schema_version':1,'season':'1993-94','country':'Grecia','country_id':47,
        'league':'Alpha Ethniki','historical_runtime_league_id':930047,
        'source':{'name':'RSSSF Greece 1993/94','url':SOURCE,'roster_section':'ROSTERS','standings_note':'3 points for a win; 18 teams; bottom three relegated'},
        'selection_policy':'Full available RSSSF 1993-94 season roster per club, including reserves/zero-appearance rows explicitly listed by the source; 18 is minimum only; no fictional filler',
        'clubs':clubs,
    }
    if min(len(c['players']) for c in clubs)<18: raise RuntimeError('Greek staging minimum-depth gate failed')
    OUT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'clubs':len(clubs),'players':sum(len(c['players']) for c in clubs),'min_per_club':min(len(c['players']) for c in clubs)},ensure_ascii=False))

if __name__=='__main__': main()
