from __future__ import annotations

from pathlib import Path
from typing import Any
from collections import Counter
import json
import hashlib
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from tools.deepen_historical_profiles_and_metadata_v031 import ROLE_TO_BROAD, ROLE_TO_LABEL, comparable, profile_gap_stats, role_ratings  # noqa:E402
from tools.review_created_player_profiles import materialise_attributes  # noqa:E402

DATA = ROOT/'data'/'football9394'
SNAP = DATA/'historical_snapshot.json'
REG = DATA/'created_players_registry.json'
QUEUE = DATA/'bdfutbol_photo_queue.json'
STAGE = DATA/'belgium_1993_94_roster_staging.json'
CATALOG = DATA/'historical_source_catalog.json'

CHECKPOINT='0.43.0-belgium-final-six-deep'
VERSION='0.43'
CLUBS={
    'RFC Liège': {'team_id':9352005,'bdf_team':'https://www.bdfutbol.com/en/t/t1993-9410266.html','tm_team':'','expected_rows':24,'expected_dob_closed':23,'expected_nat_closed':23},
    'Cercle Brugge': {'team_id':455,'bdf_team':'https://www.bdfutbol.com/en/t/t1993-9410785.html','tm_team':'','expected_rows':24,'expected_dob_closed':24,'expected_nat_closed':24},
    'Oostende': {'team_id':908,'bdf_team':'https://www.bdfutbol.com/en/t/t1993-9410949.html','tm_team':'','expected_rows':19,'expected_dob_closed':19,'expected_nat_closed':19},
    'KV Mechelen': {'team_id':459,'bdf_team':'https://www.bdfutbol.com/en/t/t1993-9411101.html','tm_team':'','expected_rows':24,'expected_dob_closed':24,'expected_nat_closed':24},
    'Gent': {'team_id':456,'bdf_team':'https://www.bdfutbol.com/en/t/t1993-9410090.html','tm_team':'','expected_rows':25,'expected_dob_closed':25,'expected_nat_closed':25},
    'Lierse': {'team_id':851,'bdf_team':'https://www.bdfutbol.com/en/t/t1993-9410070.html','tm_team':'','expected_rows':20,'expected_dob_closed':20,'expected_nat_closed':20},
}

ROLE_ES={0:'Portero',1:'Lateral derecho',2:'Lateral izquierdo',3:'Defensa central',4:'Defensa central',5:'Líbero',6:'Mediocentro defensivo',7:'Centrocampista',8:'Mediapunta',9:'Interior derecho',10:'Interior derecho',11:'Extremo derecho',12:'Extremo derecho',13:'Interior izquierdo',14:'Interior izquierdo',15:'Extremo izquierdo',16:'Extremo izquierdo',17:'Delantero centro'}

def p(club:str,name:str,dob:str,nat:list[int],birth:int|None,place:str|None,role:int,pos:str,bdf:str,
      height:int|None=None,weight:int|None=None,precision:str='exact',position_source:str='bdf',
      note:str|None=None) -> dict[str,Any]:
    return dict(club=club,name=name,dob=dob,nat=nat,birth_country=birth,place=place,role=role,pos=pos,bdf=bdf,
                height=height,weight=weight,precision=precision,position_source=position_source,note=note)

# Identity, DOB, birthplace, position and measurements: BDFutbol individual profiles.
# Broad BDF labels remain broad; no squad-balance specialization is invented.
# Shared identities already deepened in earlier Belgian passes keep stronger source-backed exact roles when compatible.
P:dict[int,dict[str,Any]]={
    9496278:p('RFC Liège','Jean-François Lecomte','1968-11-17',[17],17,'Huy',0,'Goalkeeper','66374',183,81),
    9496285:p('RFC Liège','Bernard Wégria','1963-03-07',[17],17,'Liège',1,'Right back','69113'),
    9496280:p('RFC Liège','Vincent Machiels','1965-09-16',[17],17,None,3,'Defender','69542',None,None,precision='broad_only'),
    9496269:p('RFC Liège','Jean-François de Sart','1961-12-18',[17],17,'Waremme',3,'Central','98432'),
    9496270:p('RFC Liège','Eric Deflandre','1973-08-02',[17],17,'Liège',1,'Right back','84799',181,80,precision='exact',note='BDFutbol identifies Deflandre as right back; the prior central/other inference is removed.'),
    9496283:p('RFC Liège','Kelvin Sebwe','1972-04-04',[169],169,'Monrovia',7,'Midfielder','48434',187,None,precision='broad_only'),
    9496281:p('RFC Liège','Didier Quain','1960-12-15',[17],17,'Tournai',7,'Midfielder','69341',None,None,precision='broad_only'),
    9496273:p('RFC Liège','Emmanuel Godfroid','1972-08-16',[17],17,'Huy',7,'Midfielder','68596',180,71,precision='broad_only'),
    9494187:p('RFC Liège','Sunday Ogorchukwu Oliseh','1974-09-14',[59],59,'Delta',7,'Midfielder','90009',183,78,precision='broad_only'),
    9495163:p('RFC Liège','Graham Arnold','1963-08-03',[15],15,'Sydney',17,'Forward','62912',179,None,precision='broad_only'),
    9495160:p('RFC Liège','Cvijan Milošević','1963-10-27',[20],20,'Tuzla',17,'Forward','66364',None,None,precision='broad_only',note='BDFutbol records Tuzla/Bosnia-Herzegovina; Bosnia-Herzegovina is a valid independent state in the project 1993 catalog.'),
    9496266:p('RFC Liège','Pascal Beeken','1973-08-12',[17],17,'Liège',0,'Goalkeeper','62916'),
    9496279:p('RFC Liège','Philippe Lenglois','1972-08-16',[17],17,'Huy',2,'Left back','66273',186,65,precision='exact',note='BDFutbol identifies Lenglois as left back; prior attacking inference removed.'),
    9496274:p('RFC Liège','Thierry Habets','1971-07-30',[17],17,None,7,'Midfielder','69541',188,None,precision='broad_only'),
    9496277:p('RFC Liège','Jacques Kinkomba Kingambo','1962-01-04',[88],88,'Mabulu (Zaire / modern DR Congo)',7,'Midfielder','69537',None,None,precision='broad_only',note='Modern source geography is DR Congo; the 1993 state/football identity is frozen to Zaire through country id 88.'),
    9496282:p('RFC Liège','Raphaël Quaranta','1957-12-29',[17],17,'Ternaaien',7,'Midfielder','69539',183,None,precision='broad_only'),
    9496272:p('RFC Liège','Moreno Giusto','1961-11-03',[17],17,None,3,'Defender','69538',None,None,precision='broad_only'),
    9496326:p('RFC Liège','Luc Ernès','1965-02-24',[17],17,"Villers-l'Évêque",17,'Forward','68883',None,None,precision='broad_only'),
    9496276:p('RFC Liège','Donatien Kimoni','1973-10-07',[17],17,None,7,'Midfielder','69534',None,None,precision='broad_only'),
    9496268:p('RFC Liège','Luciano Crapa','1974-01-10',[17],17,None,7,'Midfielder','69346',183,79,precision='broad_only'),
    9496275:p('RFC Liège','Boris Henry','1970-09-18',[17],17,None,7,'Midfielder','69532',None,None,precision='broad_only',note='BDFutbol gives Midfielder; unsupported specialist inference removed.'),
    9496267:p('RFC Liège','César Luís dos Santos Camargo','1969-03-21',[62, 10],62,None,17,'Forward','89313',177,68,precision='broad_only',note='BDFutbol records Brazilian and Portuguese nationality; both are retained.'),
    9496284:p('RFC Liège','Christian Theissen','1974-09-14',[17],17,None,17,'Forward','69533',None,None,precision='broad_only',note='BDFutbol gives Forward; prior defensive inference removed.'),
    9496271:p('RFC Liège','Jean-François Demonceau','1974-08-01',[17],17,None,7,'Midfielder','69677',None,None,precision='broad_only',note='BDFutbol gives Midfielder; prior defensive inference removed.'),
    9496043:p('Cercle Brugge','Yves Feys','1969-01-16',[17],17,'Torhout',0,'Goalkeeper','66135',183,79),
    9496046:p('Cercle Brugge','Bert Lamaire','1971-04-28',[17],17,'Poperinge',1,'Right back','68649',179,None),
    9494021:p('Cercle Brugge','Tibor Selymes','1970-05-14',[72],72,'Bălan',2,'Left back','99904',176,73),
    9496049:p('Cercle Brugge','Thierry Siquet','1968-10-18',[17],17,'Huy',3,'Central','65610',185,None),
    9496044:p('Cercle Brugge','Didier Frenay','1966-04-09',[17],17,'Liège',3,'Defender','87750',None,None,precision='broad_only'),
    9496035:p('Cercle Brugge','Bernard Beuken','1971-02-28',[17],17,'Liège',3,'Defender','707722',None,None,precision='broad_only'),
    9494017:p('Cercle Brugge','Dorinel Ionel Munteanu','1968-06-25',[72],72,'Grădinari',7,'Midfielder','90085',169,72,precision='broad_only'),
    9496050:p('Cercle Brugge','Kurt Soenens','1967-01-09',[17],17,'Izegem',7,'Midfielder','69156',None,None,precision='broad_only'),
    9496036:p('Cercle Brugge','Marius Cheregi','1967-10-04',[72],72,'Oradea',7,'Midfielder','69678',184,80,precision='broad_only'),
    9494220:p('Cercle Brugge','Josip Weber','1964-11-16',[17, 31],31,'Slavonski Brod',17,'Forward','99673',183,None,precision='broad_only',note='BDFutbol records Belgian and Croatian nationality; both are retained.'),
    9496047:p('Cercle Brugge','Christophe Lauwers','1972-09-17',[17],17,'Oudenburg',17,'Forward','87663',179,71,precision='broad_only'),
    9496051:p('Cercle Brugge','Nico Vaesen','1969-09-28',[17],17,'Hasselt',0,'Goalkeeper','94321',193,83),
    9496052:p('Cercle Brugge','Serge Vande Walle','1971-10-02',[17],17,None,3,'Central','66424'),
    9496040:p('Cercle Brugge','Marc De Buyser','1963-11-13',[17],17,'Willebroek',17,'Forward','69095',176,None,precision='broad_only'),
    9495153:p('Cercle Brugge','Dominic Longo','1970-08-23',[15],15,'Hobart',3,'Defender','69512',None,None,precision='broad_only'),
    9496042:p('Cercle Brugge','Stéphane Auguste Ernest Demol','1966-03-11',[17],17,'Watermael-Boitsfort',3,'Central','81729',188,78),
    9496034:p('Cercle Brugge','William Osei Berkoe','1974-12-27',[42],42,'Accra',7,'Midfielder','69303',182,80,precision='broad_only'),
    9496048:p('Cercle Brugge','Kofi Mbeah','1974-12-11',[42],42,'Sekondi-Takoradi',3,'Defender','69155',None,None,precision='broad_only'),
    9496037:p('Cercle Brugge','Geoffrey Claeys','1974-10-05',[17],17,'Brugge',3,'Central','44921',185,None),
    9496038:p('Cercle Brugge','Davy Cooreman','1971-01-27',[17],17,'Aalst',7,'Midfielder','66051',170,68,precision='broad_only'),
    9496045:p('Cercle Brugge','Ovidiu Cornel Hanganu','1970-05-12',[72],72,'Ghelar',17,'Forward','69513',None,None,precision='broad_only'),
    9496041:p('Cercle Brugge','Nico De Coninck','1973-08-26',[17],17,None,7,'Midfielder','69096',178,None,precision='broad_only'),
    9496033:p('Cercle Brugge','Anthony Annicaert','1973-10-09',[17],17,None,7,'Midfielder','69148',None,None,precision='broad_only'),
    9496039:p('Cercle Brugge',"Stefaan D'Hondt",'1975-05-15',[17],17,None,7,'Midfielder','69514',None,None,precision='broad_only'),
    9496256:p('Oostende','Christophe Lycke','1966-06-21',[17],17,None,0,'Goalkeeper','69519'),
    9496257:p('Oostende','Daniël Maes','1966-07-07',[17],17,'Sint-Niklaas',1,'Right back','66411',181,None),
    9496251:p('Oostende','Danny Devuyst','1970-04-01',[17],17,None,3,'Central','69108'),
    9496260:p('Oostende','Eric Pinson','1964-04-29',[17],17,None,7,'Midfielder','69521',None,None,precision='broad_only'),
    9496262:p('Oostende','Björn Renty','1967-07-24',[17],17,'Diksmuide',7,'Midfielder','68666',180,None,precision='broad_only'),
    9496265:p('Oostende','Patrick Van Veirdeghem','1963-01-10',[17],17,'Lokeren',7,'Midfielder','69526',171,65,precision='broad_only'),
    9496261:p('Oostende','Gerry Poppe','1970-09-19',[17],17,'Lokeren',7,'Midfielder','69522',175,72,precision='broad_only'),
    9496254:p('Oostende','Zdzisław Janik','1964-11-11',[70],70,'Kraków',7,'Midfielder','69530',179,68,precision='broad_only'),
    9496252:p('Oostende','Bart Dewaele','1961-12-25',[17],17,'Deinze',7,'Midfielder','69350',190,78,precision='broad_only'),
    9496264:p('Oostende','Zbigniew Świętek','1966-10-19',[70],70,'Zaklików',17,'Forward','69529',181,77,precision='broad_only'),
    9496255:p('Oostende','Kayode Keshinro','1972-12-25',[59],59,'Lagos',17,'Forward','69523',None,None,precision='broad_only'),
    9496263:p('Oostende','Kurt Stoops','1970-04-09',[17],17,'Brugge',0,'Goalkeeper','69524',184,None),
    9496247:p('Oostende','Didier Ndama Bapupa','1972-06-30',[88],88,'Kinshasa (Zaire / modern DR Congo)',3,'Defender','68677',181,None,precision='broad_only',note='Modern source geography is DR Congo; 1993 state/football identity is Zaire.'),
    9496249:p('Oostende','Patrick Bonomi','1965-10-15',[17],17,None,7,'Midfielder','69525',None,None,precision='broad_only'),
    9496248:p('Oostende','Xavier Bertein','1970-03-11',[17],17,None,7,'Midfielder','69527',None,None,precision='broad_only'),
    9496259:p('Oostende','Michael Okoth Origi','1967-11-16',[124],124,'Nairobi',17,'Striker','701357',186,None),
    9496258:p('Oostende','Johnny Nierynck','1973-01-07',[17],17,None,1,'Right back','68673',175,73),
    9496253:p('Oostende','David Gérard','1971-11-22',[17],17,None,3,'Defender','69520',None,None,precision='broad_only'),
    9496250:p('Oostende','Bart Deschacht','1972-06-08',[17],17,None,3,'Defender','69664',191,70,precision='broad_only'),
    2830:p('KV Mechelen',"Michel Georges Jean Ghislain Preud'homme",'1959-01-24',[17],17,'Seraing',0,'Goalkeeper','79265',183,75),
    9496172:p('KV Mechelen','Davy Gijsbrechts','1972-09-20',[17],17,'Heusden',3,'Defender','59789',185,None,precision='broad_only'),
    9496177:p('KV Mechelen','Bart Mauroo','1968-04-08',[17],17,'Waregem',3,'Defender','59793',None,None,precision='broad_only'),
    9495300:p('KV Mechelen','Glen de Boeck','1971-08-22',[17],17,'Boom',3,'Central','79211',189,None),
    9496175:p('KV Mechelen','Frank Leen','1970-10-04',[17],17,'Lommel',7,'Midfielder','57019',179,None,precision='broad_only'),
    9496167:p('KV Mechelen','Joël Bartholomeeussen','1966-03-02',[17],17,'Zoersel',7,'Midfielder','68473',None,None,precision='broad_only'),
    9496181:p('KV Mechelen','Koenraad Sanders','1962-12-17',[17],17,'Brugge',7,'Midfielder','46196',178,None,precision='broad_only'),
    9496182:p('KV Mechelen','Constant van den Buijs','1957-06-08',[17],17,'Kalmthout',7,'Midfielder','59802',185,None,precision='broad_only'),
    9494215:p('KV Mechelen','Alexandre Czerniatynski','1960-07-28',[17],17,'Charleroi',17,'Striker','41781',186,None),
    9496183:p('KV Mechelen','Kurt Vangompel','1973-09-20',[17],17,'Bree',17,'Forward','59792',None,None,precision='broad_only'),
    9496171:p('KV Mechelen','Denes Eszenyi','1968-01-09',[93],93,'Nyíregyháza',17,'Forward','59791',184,None,precision='broad_only'),
    9496169:p('KV Mechelen','Ivan De Wilde','1966-05-09',[17],17,None,0,'Goalkeeper','59796'),
    9496180:p('KV Mechelen','Marino Sabbadini','1969-12-10',[17],17,'Genk',7,'Midfielder','91177',None,None,precision='broad_only'),
    2565:p('KV Mechelen','Johnny Mølby','1969-02-04',[33],33,'Kolding',7,'Midfielder','80115',176,None,precision='broad_only'),
    9496329:p('KV Mechelen','Flórián Urbán','1968-07-29',[93],93,'Budapest',7,'Midfielder','68620',182,82,precision='broad_only',note='BDFutbol gives broad Midfielder at Mechelen; the source-backed defensive-midfield profile from the earlier Waregem pass must be preserved.'),
    9496166:p('KV Mechelen','Zlatko Arambašić','1969-09-20',[31],31,'Split',17,'Forward','1081813',190,None,precision='broad_only'),
    9496170:p('KV Mechelen','Geert Deferm','1963-05-06',[17],17,'Hasselt',2,'Left back','46195'),
    9496184:p('KV Mechelen','Stijn Vreven','1973-07-18',[17],17,'Hasselt',1,'Right back','92180',180,80),
    9496179:p('KV Mechelen','Marcos Antonio Pereira','1975-04-02',[62],62,'Sertaneja',17,'Striker','59794',175,None),
    9496173:p('KV Mechelen','Ulli Hulsmans','1973-05-28',[17],17,'Heusden',7,'Midfielder','69665',None,None,precision='broad_only'),
    9496168:p('KV Mechelen','Paul de Mesmaeker','1963-08-12',[17],17,'Oudenaarde',7,'Midfielder','46190',None,None,precision='broad_only'),
    9496174:p('KV Mechelen','Marc Janssen','1974-02-08',[17],17,None,1,'Right back','68522'),
    9496178:p('KV Mechelen','Alain Peetermans','1967-12-05',[17],17,None,3,'Defender','59800',None,None,precision='broad_only'),
    9496176:p('KV Mechelen','Jan-Pieter Martens','1974-09-23',[17],17,'Bilzen',7,'Midfielder','56877',177,70,precision='broad_only'),
    9496133:p('Gent','Zsolt János Petry','1966-09-23',[93],93,'Budapest',0,'Goalkeeper','91200',185,82),
    9496124:p('Gent','Gunter De Meyer','1968-04-14',[17],17,None,3,'Defender','66345',None,None,precision='broad_only'),
    9496129:p('Gent','Tony Herreman','1969-01-23',[17],17,'Hamme',2,'Left back','66204'),
    9496125:p('Gent','Bart de Roover','1967-08-21',[17],17,'Deurne',3,'Central','62859'),
    9496142:p('Gent','Mark Verkuyl','1963-11-19',[3],3,'Utrecht',2,'Left back','42354'),
    9495309:p('Gent','Alain De Nil','1966-08-17',[17],17,'Jette',7,'Midfielder','69293',178,None,precision='broad_only'),
    9495307:p('Gent','Frank Dauwen','1967-11-03',[17],17,'Geel',7,'Midfielder','66173',198,85,precision='broad_only'),
    9496127:p('Gent','Dirk De Vriese','1958-12-03',[17],17,'Knokke',7,'Midfielder','69682',None,None,precision='broad_only'),
    9496143:p('Gent','Eric Viscaal','1968-03-20',[3],3,'Eindhoven',17,'Forward','77579',180,None,precision='broad_only'),
    9496123:p('Gent','Foeke Booy','1962-04-25',[3],3,'Leeuwarden',17,'Forward','78402',None,None,precision='broad_only'),
    9496136:p('Gent','Erwin Vandenbergh','1959-01-26',[17],17,'Ramsel',17,'Forward','41779',184,None,precision='broad_only'),
    9496128:p('Gent','Patrick Deman','1968-07-31',[17],17,'Marke',0,'Goalkeeper','64869',184,81),
    9496137:p('Gent','Marc Angéle van der Linden','1964-02-04',[17],17,'Merksem',17,'Striker','98378',177,None),
    9496130:p('Gent','Branko Karačić','1960-09-24',[31],31,'Vinkovci',7,'Midfielder','702645',184,None,precision='broad_only'),
    9496139:p('Gent','Dirk Vangronsveld','1967-08-16',[17],17,None,3,'Defender','68913',177,70,precision='broad_only'),
    9496327:p('Gent','Thierry Pister','1965-09-02',[17],17,'Gent',7,'Midfielder','65661',None,None,precision='broad_only',note='Shared identity: retain any earlier source-backed exact role when compatible with this broad BDF label.'),
    9496141:p('Gent','Stefan Vereycken','1966-04-29',[17],17,'Schelle',7,'Midfielder','69684',None,None,precision='broad_only'),
    9496328:p('Gent','Gunther Schepens','1973-05-04',[17],17,'Gent',7,'Midfielder','98424',175,75,precision='broad_only',note='Shared identity: retain any earlier source-backed exact role when compatible with this broad BDF label.'),
    9496134:p('Gent','Edin Ramčić','1970-08-01',[20],20,None,7,'Midfielder','66265',185,78,precision='broad_only'),
    9496140:p('Gent','Tom Verdegem','1967-09-13',[17],17,None,7,'Midfielder','69685',None,None,precision='broad_only'),
    9496132:p('Gent','Davy Minnaert','1974-05-09',[17],17,None,7,'Midfielder','69508',None,None,precision='broad_only'),
    9496135:p('Gent','Stefan Van Laere','1972-09-21',[17],17,None,7,'Midfielder','69511',None,None,precision='broad_only'),
    9496138:p('Gent','Johan Vandevelde','1973-01-09',[17],17,None,7,'Midfielder','69510',None,None,precision='broad_only'),
    9496126:p('Gent','Kristoff de Roy','1973-09-20',[17],17,None,3,'Defender','69683',None,None,precision='broad_only'),
    9496131:p('Gent','Mohamed Ali Kurtuluş','1974-08-29',[17],17,'Gent',7,'Midfielder','1114319',176,None,precision='broad_only',note='BDFutbol birth-country evidence is Belgium; no unsupported Turkish nationality is inferred from the surname.'),
    9496192:p('Lierse','Kris Mampaey','1970-11-02',[17],17,'Mortsel',0,'Goalkeeper','85696',188,84),
    9496198:p('Lierse','Eduard Roza Lodewijk Snelders','1959-04-09',[17],17,'Kapellen',3,'Defender','69114',183,76,precision='broad_only'),
    9496200:p('Lierse','Nicolas Van Kerckhoven','1970-12-14',[17],17,'Lier',2,'Left back','90245',189,79),
    9496188:p('Lierse','Steve Goossen','1968-11-12',[3],3,'Goirle',3,'Central','85988'),
    9494197:p('Lierse','Kjetil André Rekdal','1968-11-06',[60],60,'Molde',3,'Defender','98250',188,81,precision='broad_only'),
    9496187:p('Lierse','Marc Fierens','1963-06-12',[17],17,None,3,'Defender','69490',187,80,precision='broad_only'),
    9496191:p('Lierse','Joop Lankhaar','1966-09-12',[3],3,'Alphen aan den Rijn',3,'Defender','63619',None,None,precision='broad_only'),
    9496186:p('Lierse','Stefan De Smet','1969-04-03',[17],17,'Lier',7,'Midfielder','69299',182,76,precision='broad_only'),
    9496196:p('Lierse','Ives Serneels','1972-10-16',[17],17,'Leuven',7,'Midfielder','66312',177,75,precision='broad_only'),
    9496193:p('Lierse','Rafaël Pauwels','1968-06-14',[17],17,'Lier',17,'Forward','69298',180,68,precision='broad_only'),
    9496190:p('Lierse','Dirk Huysmans','1973-09-03',[17],17,'Mortsel',17,'Forward','66055',178,71,precision='broad_only'),
    9496195:p('Lierse','Patrick Rondags','1964-12-12',[17],17,'Spouwen',0,'Goalkeeper','62773',186,None),
    9496202:p('Lierse','Kurt van Roosbroeck','1966-10-10',[17],17,None,3,'Defender','69680',None,None,precision='broad_only'),
    9496197:p('Lierse','Daniel Simmes','1966-08-12',[4],4,'Dortmund',17,'Forward','80404',182,79,precision='broad_only'),
    2777:p('Lierse','Jahn Ivar Jakobsen','1965-11-08',[60],60,'Gravdal',17,'Forward','80154',168,None,precision='broad_only'),
    9496194:p('Lierse','Bob Peeters','1974-01-10',[17],17,'Lier',17,'Forward','85779',196,86,precision='broad_only',note='Shared identity: retain any earlier source-backed exact role when compatible with this broad BDF label.'),
    9496185:p('Lierse','David Brocken','1971-02-18',[17],17,'Lier',1,'Right back','700139',177,None),
    9496199:p('Lierse','Karel Snoeckx','1973-10-29',[17],17,'Turnhout',7,'Midfielder','65842',181,78,precision='broad_only'),
    9496189:p('Lierse','Joris Heylen','1969-12-27',[17],17,None,7,'Midfielder','69679',None,None,precision='broad_only'),
    9496201:p('Lierse','Paul van Nuffelen','1961-06-26',[17],17,None,3,'Defender','69681',None,None,precision='broad_only'),
}

def load(path:Path): return json.loads(path.read_text(encoding='utf-8'))
def dump(path:Path,obj:Any): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def split_name(name:str):
    parts=name.split(); return (None,name) if len(parts)==1 else (' '.join(parts[:-1]),parts[-1])
def profile_url(patch:dict[str,Any])->str: return f"https://www.bdfutbol.com/en/j/j{patch['bdf']}.html"

def russia_fingerprint(snapshot:dict[str,Any])->str:
    tids={int(t['source_id']) for t in snapshot.get('teams',[]) if t.get('league_id')==930015}
    payload={
      'teams':[t for t in snapshot.get('teams',[]) if int(t.get('source_id') or -1) in tids],
      'players':[p for p in snapshot.get('players',[]) if p.get('team_id') in tids],
    }
    raw=json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


def country_names(catalog:dict[str,Any])->dict[int,str]:
    out={}
    for c in catalog.get('countries',[]):
        sid=int(c['source_id'])
        out[sid]=str(c.get('historical_name_1993') or c.get('name') or sid)
    return out


def reattribute(player:dict[str,Any],role:int,originals:list[dict[str,Any]],sid:int)->None:
    a,b=comparable(originals,ROLE_TO_BROAD[role],int(player.get('overall') or 70),sid)
    player['attributes']=materialise_attributes(int(player.get('overall') or 70),a,b)
    player['attribute_source']='fixed_source_comparable_role_correction_0.42'
    player['attribute_comparable_source_ids']=[int(a['source_id']),int(b['source_id'])]


def position_source_text(patch:dict[str,Any])->tuple[str,str]:
    bdf=profile_url(patch); club=CLUBS[patch['club']]
    precision=patch.get('precision','exact'); src=patch.get('position_source','bdf')
    if precision=='source_conflict_review':
        return ('Season-specific/individual historical evidence with explicit source conflict v0.43', club['tm_team'] if src=='tm' else bdf)
    if precision=='broad_only':
        return ('BDFutbol broad position; exact specialist role unresolved v0.43', bdf)
    if src=='tm':
        return ('BDFutbol individual profile + Transfermarkt specialist corroboration v0.43', club['tm_team'])
    return ('BDFutbol individual profile exact position v0.43', bdf)


def apply_profile(player:dict[str,Any],patch:dict[str,Any],originals:list[dict[str,Any]])->dict[str,Any]:
    sid=int(player['source_id']); old_role=int(player.get('primary_role') or 0); old_broad=player.get('broad_position'); old_nat=player.get('international_country_id')
    prior_club=player.get('historical_club_1994')
    prior_profile_source=player.get('historical_profile_source')
    prior_precision=player.get('profile_position_precision')
    preserve_prior_deep=(
        prior_precision=='exact'
        and bool(prior_profile_source)
        and prior_club not in {None,patch['club']}
        and patch.get('precision','exact')=='broad_only'
        and old_broad==ROLE_TO_BROAD[int(patch['role'])]
    )
    prior_position={k:player.get(k) for k in ['primary_role','broad_position','role_ratings','profile_position_precision','source_profile_position','profile_review_required','historical_position_1993_94','historical_position_source','historical_position_source_url','historical_profile_source','historical_profile_source_url','historical_profile_source_note','historical_club_1994']}
    first,surname=split_name(patch['name']); player['display_name']=patch['name']; player['first_name']=first; player['surname1']=surname
    player['birth_date']=patch['dob']+'T00:00:00'
    if patch.get('birth_country') is not None: player['birth_country_id']=int(patch['birth_country'])
    else: player.pop('birth_country_id',None)
    player['international_country_id']=int(patch['nat'][0]); player['profile_nationality_country_ids']=[int(x) for x in patch['nat']]
    if len(patch['nat'])>1: player['secondary_nationality_country_id']=int(patch['nat'][1])
    else: player.pop('secondary_nationality_country_id',None)
    player['historical_birth_place_text']=patch.get('place'); player['historical_birth_place_source_url']=profile_url(patch); player['historical_birth_place_source_label']='BDFutbol individual profile / historical-state policy v0.43'
    player['bdfutbol_id']=str(patch['bdf']); player['bdfutbol_url']=profile_url(patch)
    if patch.get('height') is not None: player['height_cm']=int(patch['height'])
    if patch.get('weight') is not None: player['weight_kg']=int(patch['weight'])
    role=int(patch['role']); player['primary_role']=role; player['broad_position']=ROLE_TO_BROAD[role]; player['role_ratings']=role_ratings(role)
    precision=patch.get('precision','exact'); player['profile_position_precision']=precision; player['source_profile_position']=patch['pos']; player['profile_review_required']=precision!='exact'
    if precision=='broad_only': player['historical_position_1993_94']=patch['pos']+' (exact role unresolved)'
    elif precision=='source_conflict_review': player['historical_position_1993_94']=ROLE_TO_LABEL[role]+' (source conflict: review retained)'
    else: player['historical_position_1993_94']=ROLE_TO_LABEL[role]
    ptext,purl=position_source_text(patch); player['historical_position_source']=ptext; player['historical_position_source_url']=purl
    club=CLUBS[patch['club']]
    player['historical_profile_source']='BDFutbol individual profile + targeted specialist cross-check v0.43'
    player['historical_profile_source_url']=profile_url(patch); player['historical_club_1994']=patch['club']; player['historical_data_source']='BDFutbol 1993-94 + targeted specialist cross-check v0.43'; player['bdfutbol_squad_url']=club['bdf_team']
    if patch.get('note'): player['historical_profile_source_note']=patch['note']
    if preserve_prior_deep:
        # A player can appear for multiple Belgian clubs in 1993-94. A broad label from the
        # current-club page must not erase a specialist role already source-backed earlier.
        for key,value in prior_position.items():
            if value is None:
                player.pop(key,None)
            else:
                player[key]=value
        role=int(player['primary_role']); precision=str(player.get('profile_position_precision') or 'exact')
    elif role!=old_role or player['broad_position']!=old_broad:
        reattribute(player,role,originals,sid)
    clubs=list(player.get('historical_clubs_1993_94') or [])
    for cname in [prior_club,patch['club']]:
        if cname and cname not in clubs: clubs.append(cname)
    player['historical_clubs_1993_94']=clubs
    return {'source_id':sid,'club':patch['club'],'display_name':player['display_name'],'role_before':old_role,'role_after':role,'nat_before':old_nat,'nat_after':player.get('international_country_id'),'precision':precision,'preserved_prior_deep_profile':preserve_prior_deep}


def ensure_stage(stage:dict[str,Any],player:dict[str,Any],patch:dict[str,Any])->None:
    club=next(c for c in stage['clubs'] if c['name']==patch['club'])
    sid=int(player['source_id']); row=next((r for r in club['players'] if int(r.get('resolved_source_id') or -1)==sid),None)
    if row is None: raise RuntimeError(f"missing {patch['club']} staging row {sid}")
    row.update({'resolved_display_name':player['display_name'],'resolved_primary_role':player['primary_role'],'resolved_exact_position':player['historical_position_1993_94'],
      'resolved_birth_date':player['birth_date'],'resolved_country_id':player.get('international_country_id'),'source_profile_position':patch['pos'],
      'profile_source':player['historical_profile_source'],'profile_source_url':player['historical_profile_source_url'],'position_source':player['historical_position_source'],
      'position_source_url':player['historical_position_source_url'],'resolved_birth_place_text':patch.get('place'),'individual_profile_source_url':player['historical_profile_source_url'],
      'bdfutbol_id':str(patch['bdf'])})
    if patch.get('note'): row['profile_source_note']=patch['note']


def sync_registry_queue(reg:dict[str,Any],queue:dict[str,Any],player:dict[str,Any],patch:dict[str,Any],cnames:dict[int,str],preserve_gate:bool=False)->None:
    sid=int(player['source_id']); rb={int(x['source_id']):x for x in reg['players']}; qb={int(x['source_id']):x for x in queue['players']}; club=CLUBS[patch['club']]
    base={'source_id':sid,'display_name':player['display_name'],'first_name':player.get('first_name'),'surname1':player.get('surname1'),'surname2':player.get('surname2'),
      'birth_date':str(player.get('birth_date') or '')[:10] or None,'country_id':player.get('international_country_id'),'country_name':cnames.get(int(player.get('international_country_id') or 0)),
      'broad_position':player.get('broad_position'),'team_id':club['team_id'],'team_name':patch['club'],'origin':'historical_belgium_1993_94','source':f"BDFutbol/Transfermarkt {patch['club']} deep v0.43",
      'overall':player.get('overall'),'attribute_source':player.get('attribute_source'),'profile_review_required':bool(player.get('profile_review_required')),
      'historical_position_1993_94':player.get('historical_position_1993_94'),'historical_club_1994':patch['club'],'historical_birth_place_text':patch.get('place'),
      'individual_profile_source':player.get('historical_profile_source'),'individual_profile_source_url':player.get('historical_profile_source_url'),
      'duplicate_check':'exact_name_birthdate_source_profile_gate_v043','matched_existing_id':None,'asset_filename':f'{sid}.jpg',
      'bdfutbol_id':str(patch['bdf']),'bdfutbol_url':profile_url(patch),'bdfutbol_search_name':player['display_name']}
    if sid not in rb: reg['players'].append(dict(base,photo_status='ready_for_download'))
    else:
        old_photo=rb[sid].get('photo_status'); old_gate=rb[sid].get('duplicate_check'); rb[sid].update(base); rb[sid]['photo_status']=old_photo if str(old_photo).startswith('bundled') else 'ready_for_download'
        if old_gate: rb[sid]['duplicate_check']=old_gate
    if sid not in qb: queue['players'].append(dict(base,photo_status='ready_for_download'))
    else:
        old_photo=qb[sid].get('photo_status'); old_gate=qb[sid].get('duplicate_check'); qb[sid].update(base); qb[sid]['photo_status']=old_photo if str(old_photo).startswith('bundled') else 'ready_for_download'
        if old_gate: qb[sid]['duplicate_check']=old_gate


def biography(player:dict[str,Any],row:dict[str,Any],club:str)->str:
    role='Futbolista' if player.get('profile_position_precision')=='broad_only' else ROLE_ES.get(int(player.get('primary_role') or 0),'Futbolista')
    parts=[f'{role} de {club} en la temporada 1993-94.']; stats=[]
    for k,label in [('appearances','partidos'),('starts','como titular')]:
        if isinstance(row.get(k),int): stats.append(f"{row[k]} {label}")
    if isinstance(row.get('minutes'),int): stats.append(f"{row['minutes']:,}".replace(',','.')+' minutos')
    if stats: parts.append('En el registro liguero figura con '+', '.join(stats)+'.')
    if int(player.get('primary_role') or 0)!=0 and isinstance(row.get('goals'),int): parts.append(f"Marcó {row['goals']} gol"+('' if row['goals']==1 else 'es')+'.')
    d=str(player['birth_date'])[:10]; y,m,day=d.split('-'); parts.append(f'Fecha de nacimiento registrada: {day}/{m}/{y}.')
    if player.get('historical_birth_place_text'): parts.append('Lugar de nacimiento documentado: '+str(player['historical_birth_place_text'])+'.')
    return ' '.join(parts)


def main()->None:
    snap=load(SNAP); reg=load(REG); queue=load(QUEUE); stage=load(STAGE); catalog=load(CATALOG); cnames=country_names(catalog); before=profile_gap_stats(snap); russia_fp_before=russia_fingerprint(snap)
    originals=[x for x in snap['players'] if x.get('attributes') and not x.get('external_origin') and not x.get('creation_batch')]
    by={int(x['source_id']):x for x in snap['players']}; changes=[]; missing=[sid for sid in P if sid not in by]
    if missing: raise RuntimeError(f'missing Belgium snapshot ids: {missing}')
    for sid,patch in P.items():
        change=apply_profile(by[sid],patch,originals); changes.append(change); ensure_stage(stage,by[sid],patch); sync_registry_queue(reg,queue,by[sid],patch,cnames,bool(change.get('preserved_prior_deep_profile')))
    # Build source-backed season summaries from the canonical BDF staging rows.
    for clubname,meta in CLUBS.items():
        club=next(c for c in stage['clubs'] if c['name']==clubname)
        rows={int(r['resolved_source_id']):r for r in club['players'] if r.get('resolved_source_id') is not None}
        for sid,patch in P.items():
            if patch['club']!=clubname: continue
            player=by[sid]; row=rows[sid]
            spell={'club':clubname,'team_id':meta['team_id'],'appearances':row.get('appearances'),'starts':row.get('starts'),'minutes':row.get('minutes'),'goals':row.get('goals')}
            spells=[x for x in list(player.get('historical_club_spells_1993_94') or []) if x.get('club')!=clubname]
            spells.append(spell); player['historical_club_spells_1993_94']=spells
            current_text=biography(player,row,clubname)
            bios=list(player.get('historical_biographies_1993_94') or [])
            if not bios and player.get('historical_biography_1993_94') and player.get('historical_biography_evidence'):
                ev=player.get('historical_biography_evidence') or {}; prior_club=ev.get('club')
                if prior_club and prior_club!=clubname:
                    bios.append({'club':prior_club,'text':player['historical_biography_1993_94'],'source_url':player.get('historical_biography_source_url'),'evidence':ev})
            bios=[x for x in bios if x.get('club')!=clubname]
            current_ev={'season':'1993-94','club':clubname,'appearances':row.get('appearances'),'starts':row.get('starts'),'minutes':row.get('minutes'),'goals':row.get('goals')}
            bios.append({'club':clubname,'text':current_text,'source_url':row.get('profile_source_url'),'evidence':current_ev})
            player['historical_biographies_1993_94']=bios
            player['historical_biography_1993_94']=' '.join(x['text'] for x in bios)
            player['historical_biography_source_url']=row.get('profile_source_url'); player['historical_biography_source_label']=('Multiple source-backed club spells 1993-94' if len(bios)>1 else f'BDFutbol/Transfermarkt {clubname} deep v0.43'); player['historical_biography_status']='source_backed_season_summary'
            player['historical_biography_evidence']=({'season':'1993-94','clubs':[x['evidence'] for x in bios]} if len(bios)>1 else current_ev)
    after=profile_gap_stats(snap); russia_fp_after=russia_fingerprint(snap)
    reg_ids=[int(x['source_id']) for x in reg['players']]; q_ids=[int(x['source_id']) for x in queue['players']]
    if len(reg_ids)!=len(set(reg_ids)) or len(q_ids)!=len(set(q_ids)) or set(reg_ids)!=set(q_ids): raise RuntimeError('registry/queue identity integrity failure')
    for clubname,meta in CLUBS.items():
        club=next(c for c in stage['clubs'] if c['name']==clubname)
        if len(club['players'])!=meta['expected_rows']: raise RuntimeError(f'{clubname} stage expected {meta["expected_rows"]}, got {len(club["players"])}')
        if not all(r.get('resolved_birth_date') for r in club['players']): raise RuntimeError(f'{clubname} still has staging DOB gaps')
        if not all(r.get('resolved_country_id') is not None for r in club['players']): raise RuntimeError(f'{clubname} still has staging nationality gaps')
        if not all(r.get('bdfutbol_id') for r in club['players']): raise RuntimeError(f'{clubname} still has unlinked BDF identities')
    # The v0.42 queue markers describe unresolved staging fields, not disjoint snapshot gaps.
    # Several identities were already partially deepened or shared across clubs, so the regression
    # gate must count the actual unique missing fields in the incoming canonical snapshot.
    incoming_by_sid={int(x['source_id']):x for x in load(SNAP)['players']}
    # SNAP on disk is still the incoming version here because writes happen after all gates.
    dob_expected=sum(not bool(incoming_by_sid[sid].get('birth_date')) for sid in P)
    nat_expected=sum(incoming_by_sid[sid].get('international_country_id') is None for sid in P)
    if after['Belgium']['missing_birth_date'] != before['Belgium']['missing_birth_date']-dob_expected: raise RuntimeError('Final-six Belgium DOB reduction gate not met')
    if after['Belgium']['missing_international_country_id'] != before['Belgium']['missing_international_country_id']-nat_expected: raise RuntimeError('Final-six Belgium nationality reduction gate not met')
    conflicts=[{'source_id':c['source_id'],'display_name':c['display_name'],'club':c['club']} for c in changes if c['precision']=='source_conflict_review']
    gap_closure={}
    incoming_stage_queue={x['club']:x for x in load(DATA/'belgium_deepening_queue_v042.json')['queue']}
    for clubname,meta in CLUBS.items():
        ids=[sid for sid,x in P.items() if x['club']==clubname]
        gap_closure[clubname]={
          'incoming_queue_marker_missing_birth_date':incoming_stage_queue[clubname]['missing_birth_date'],
          'incoming_queue_marker_missing_nationality':incoming_stage_queue[clubname]['missing_nationality'],
          'actual_snapshot_birth_dates_filled':sum(not bool(incoming_by_sid[sid].get('birth_date')) for sid in ids),
          'actual_snapshot_nationalities_filled':sum(incoming_by_sid[sid].get('international_country_id') is None for sid in ids),
          'remaining_staging_missing_birth_date':0,'remaining_staging_missing_nationality':0,'season_rows':meta['expected_rows']}
    audit={'schema_version':1,'checkpoint':CHECKPOINT,'status':'pass','profile_gaps_before':before,'profile_gaps_after':after,
      'profiles':{'curated_existing':len(P),'by_club':dict(Counter(x['club'] for x in P.values())),'role_corrections':sum(c['role_before']!=c['role_after'] for c in changes),'review_required':sum(bool(by[s].get('profile_review_required')) for s in P),'preserved_prior_deep_profiles':[c['source_id'] for c in changes if c.get('preserved_prior_deep_profile')],'changes':changes},
      'gap_closure':gap_closure,
      'source_conflicts':conflicts,
      'historical_country_policy':{
        'Zaire_1993':'Country source id 88 is rendered as Zaire for the 1993 context. Modern DR Congo source text is retained only as geography/source wording.',
        'post_Yugoslavia_1993':'Bosnia-Herzegovina and Croatia are stored as their independent 1993 state identities where the source supports them; no later state is back-projected.',
        'future_Russia':'Russia league remains untouched in v0.43. The next pass must separate historical birthplace state, 1993 citizenship/nationality, represented selection and transliterations; USSR must never be auto-mapped to Russia.'},
      'photo_queue':{'bdf_individual_profiles_linked':len(P),'policy':'Every target season identity is linked to its BDF individual profile and marked ready_for_download unless an already bundled normalized portrait exists; no portrait URL is fabricated.'},
      'identity_integrity':{'registry_rows':len(reg_ids),'queue_rows':len(q_ids),'registry_queue_match':set(reg_ids)==set(q_ids),'unique_registry_ids':len(reg_ids)==len(set(reg_ids))},
      'source_policy':['Finish the remaining Belgian club queue before Russia.','BDFutbol individual profiles anchor identity, DOB, birthplace, position and measurements.','Broad BDF positions are never silently converted into unsupported specialist roles.','Shared earlier deep profiles are preserved when a new club page only supplies a compatible broad label.','Historical country naming is separated from modern source labels.','No basketball 75/25 rule is used.'],
      'belgium_queue_complete':True,
      'russia_touched':russia_fp_before!=russia_fp_after,
      'russia_integrity':{'before_sha256':russia_fp_before,'after_sha256':russia_fp_after,'unchanged':russia_fp_before==russia_fp_after},
      'next_front':['Russia']
    }
    dump(SNAP,snap); dump(REG,reg); dump(QUEUE,queue); dump(STAGE,stage)
    dump(DATA/'historical_profiles_metadata_audit_v043.json',audit)
    dump(DATA/'historical_metadata_gaps_v043.json',{'checkpoint':CHECKPOINT,'gaps':after})
    dump(DATA/'historical_biographies_audit_v043.json',{'checkpoint':CHECKPOINT,'profiles_considered':len(P),'by_club':audit['profiles']['by_club'],'status':'pass'})
    dump(DATA/'belgium_source_conflicts_v043.json',{'checkpoint':CHECKPOINT,'status':'pass','conflicts':conflicts,'historical_country_policy':audit['historical_country_policy']})
    dump(DATA/'belgium_deepening_queue_v043.json',{'schema_version':1,'checkpoint':CHECKPOINT,'queue':[],'completed_clubs':list(CLUBS),'belgium_queue_complete':True,'russia_status':'unlocked_next_but_untouched_in_v043'})
    print(json.dumps({'checkpoint':CHECKPOINT,'curated_existing':len(P),'by_club':audit['profiles']['by_club'],'belgium_gaps_before':before['Belgium'],'belgium_gaps_after':after['Belgium'],'role_corrections':audit['profiles']['role_corrections'],'review_required':audit['profiles']['review_required'],'next_front':audit['next_front']},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
