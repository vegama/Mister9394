from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from tools.deepen_historical_profiles_and_metadata_v031 import (  # noqa: E402
    ROLE_TO_BROAD, ROLE_TO_LABEL, comparable, profile_gap_stats, role_ratings,
)
from tools.review_created_player_profiles import materialise_attributes  # noqa: E402

DATA = ROOT / 'data' / 'football9394'
SNAP = DATA / 'historical_snapshot.json'
REG = DATA / 'created_players_registry.json'
QUEUE = DATA / 'bdfutbol_photo_queue.json'
STAGE = DATA / 'belgium_1993_94_roster_staging.json'

BDF_SERAING = 'https://www.bdfutbol.com/en/t/t1993-9412101.html'
BDF_CHARLEROI = 'https://www.bdfutbol.com/en/t/t1993-9410718.html'
BDF_STANDARD = 'https://www.bdfutbol.com/en/t/t1993-9410012.html'
BDF_RFC_LIEGE = 'https://www.bdfutbol.com/en/t/t1993-9410266.html'
TM_SERAING = 'https://www.transfermarkt.com/rfc-seraing-1996-/kader/verein/54426/saison_id/1993'
TM_CHARLEROI = 'https://www.transfermarkt.com/rsc-charleroi/startseite/verein/172/saison_id/1993'
TM_STANDARD = 'https://www.transfermarkt.com/standard-luttich/kader/verein/3057/saison_id/1993'
TM_DONATIEN = 'https://www.transfermarkt.co.uk/donatien-kimoni/profil/spieler/939131'
PHOTO_URLS = {
    9498005:'https://www.bdfutbol.com/i/j/68668.jpg',
    9498006:'https://www.bdfutbol.com/i/j/68635.jpg',
    9498007:'https://www.bdfutbol.com/i/j/701428.jpg?v=1698862581',
    9498008:'https://www.bdfutbol.com/i/j/6844.jpg?v=1230397300',
}
PHOTO_DIR = ROOT / 'frontend' / 'public' / 'historical9394' / 'players'

TEAM = {'FC Seraing': 9352001, 'Charleroi': 454, 'Standard Liège': 409, 'RFC Liège': 9352005}
COUNTRY_NAME = {
    3:'Países Bajos',4:'Alemania',17:'Bélgica',33:'Dinamarca',40:'Rusia',42:'Ghana',47:'Grecia',
    53:'Luxemburgo',54:'Macedonia',62:'Brasil',63:'Italia',66:'Camerún',72:'Rumanía',75:'República Federal de Yugoslavia',
    81:'Togo',88:'Zaire',93:'Hungría'
}
ROLE_ES={0:'Portero',1:'Lateral derecho',2:'Lateral izquierdo',3:'Defensa central',4:'Defensa central',5:'Líbero',6:'Mediocentro defensivo',7:'Centrocampista',8:'Mediapunta',9:'Interior derecho',10:'Interior derecho',11:'Extremo derecho',12:'Extremo derecho',13:'Interior izquierdo',14:'Interior izquierdo',15:'Extremo izquierdo',16:'Extremo izquierdo',17:'Delantero centro'}

# Curated profile data. BDF supplies identity/biographical data; Transfermarkt season pages supply
# exact specialist roles when BDF is only broad. Former Yugoslavia/USSR birth states are not
# retrofitted to modern successor birth_country_id values.
def p(club:str,name:str,dob:str,nat:list[int],birth_country:int|None,place:str|None,role:int,pos:str,bdf:str|None,
      height:int|None=None,weight:int|None=None,precision:str='exact',note:str|None=None,position_url:str|None=None,
      profile_url:str|None=None) -> dict[str,Any]:
    return dict(club=club,name=name,dob=dob,nat=nat,birth_country=birth_country,place=place,role=role,pos=pos,bdf=bdf,
                height=height,weight=weight,precision=precision,note=note,position_url=position_url,profile_url=profile_url)

P: dict[int, dict[str,Any]] = {
# FC Seraing — 18 existing BDF league identities + repaired Edmilson + two source-roster members.
9496095:p('FC Seraing','Ranko Stojić','1959-01-18',[75],None,'Bugojno (Yugoslavia)',0,'Goalkeeper','42794',note='Born in SFR Yugoslavia; the 1993 sporting context is retained without assigning a modern successor-state birth country.'),
9496091:p('FC Seraing',"Danny N'Gombo",'1963-10-25',[88],None,None,3,'Centre-Back','68884',precision='exact',position_url=TM_SERAING,note='1993 nationality context uses Zaire; the modern DR Congo label is not back-projected into the historical country field.'),
9496082:p('FC Seraing','Benjamin Debusschere','1968-12-07',[17],17,'Tienen',2,'Left-Back','98401',height=179,position_url=TM_SERAING),
9496093:p('FC Seraing','Lars Christian Olsen','1961-02-02',[33],33,'Glostrup',5,'Sweeper','701501',height=182,weight=78,position_url=TM_SERAING),
9496083:p('FC Seraing','Olivier Doll','1973-06-09',[17],17,'Brussels',3,'Centre-Back','99675',height=181,position_url=TM_SERAING),
9496097:p('FC Seraing','Patrick Teppers','1964-07-30',[17],17,'Bocholt',13,'Left Midfield','66389',height=178,weight=76,position_url=TM_SERAING),
9496088:p('FC Seraing','Emmanuel Karagiannis','1966-11-22',[17,47],17,'Leut',6,'Defensive Midfield','99693',height=175,position_url=TM_SERAING),
9496087:p('FC Seraing','Isaias Magalhaes da Silva','1973-11-29',[62],62,'Maranhão',8,'Attacking Midfield','87780',height=175,weight=70,position_url=TM_SERAING),
9498005:p('FC Seraing','Edmilson Paulo da Silva','1968-04-16',[62],62,'Pernambuco',16,'Left Winger','68668',height=176,weight=76,position_url=TM_SERAING,note='Separate identity from Edmilson Dias Lucena (MDB/source_id 4929), which had been incorrectly reused by surname.'),
9496090:p('FC Seraing','Roger Menama Lukaku','1967-06-06',[88],None,'Kinshasa',17,'Centre-Forward','68680',height=186,position_url=TM_SERAING,note='1993 nationality context uses Zaire; birthplace is retained textually.'),
9496099:p('FC Seraing','Wamberto de Jesus Sousa Campos','1974-12-13',[62],62,'Cururupu',12,'Right Winger','85709',height=168,weight=67,position_url=TM_SERAING),
9496094:p('FC Seraing','Serge Sironval','1971-09-03',[17],17,'Anderlecht',0,'Goalkeeper','97415'),
9496085:p('FC Seraing','Ronald Foguenne','1970-08-10',[17],17,'Verviers',13,'Left Midfield','66203',height=180,weight=74,position_url=TM_SERAING),
9496098:p('FC Seraing','Zvonko Varga','1959-11-27',[75,93],None,'Zrenjanin (Yugoslavia)',17,'Centre-Forward','42805',height=178,position_url=TM_SERAING,note='Born in SFR Yugoslavia; 1993 sporting nationality is stored as FR Yugoslavia with Hungarian secondary context.'),
9496086:p('FC Seraing','Jean-Marie Houben','1966-11-24',[17],17,'Liège',3,'Defender','98450',precision='broad_only',position_url=TM_SERAING),
9496089:p('FC Seraing','Axel Lawarée','1973-10-09',[17],17,'Huy',17,'Centre-Forward','6734',height=177,weight=73,position_url=TM_SERAING),
9496092:p('FC Seraing','Domenico Olivieri','1968-01-16',[17,63],17,'Genk',5,'Sweeper','701429',height=176,weight=75,position_url=TM_SERAING),
9496084:p('FC Seraing','Paulo Edson da Silva','1976-02-22',[62],62,None,7,'Midfielder','69342',height=168,weight=67,precision='broad_only'),
9496096:p('FC Seraing','David Swerdtfegers','1974-10-30',[17],17,None,3,'Defender','69340',height=182,weight=71,precision='broad_only',position_url=TM_SERAING),
9498009:p('FC Seraing','Harald Heinen','1966-06-07',[17,4],None,None,0,'Goalkeeper',None,position_url=TM_SERAING,profile_url=TM_SERAING,note='Transfermarkt 93/94 lists Belgian citizenship; German historical context also appears in secondary sources, so birth country is left unresolved.'),
9498010:p('FC Seraing','Johan Vanheusden','1968-04-25',[17],17,None,3,'Defender',None,precision='broad_only',position_url=TM_SERAING,profile_url=TM_SERAING),
# Charleroi — 19 existing/repaired league identities + source-roster members.
9496064:p('Charleroi','Peter Kerremans','1961-02-02',[17],17,None,0,'Goalkeeper','69663'),
9496060:p('Charleroi','Roch Gérard','1972-01-04',[17],17,None,1,'Right-Back','68513',height=179,weight=75,position_url=TM_CHARLEROI),
9496068:p('Charleroi','Rudy Moury','1966-03-01',[17],17,None,2,'Left-Back','66400',height=180,weight=78,position_url=TM_CHARLEROI),
9494222:p('Charleroi','Eric Van Meir','1968-02-28',[17],17,'Brecht',5,'Sweeper','701882',height=187,weight=85,position_url=TM_CHARLEROI),
9496069:p('Charleroi','Michel Rasquin','1964-02-20',[17],17,'Ougrée',2,'Left-Back','68917',height=178,weight=78,position_url=TM_CHARLEROI),
9496063:p('Charleroi','Cedomir Janevski','1961-07-03',[54],None,'Skopje (Yugoslavia)',5,'Sweeper','64739',position_url=TM_CHARLEROI,note='Born in SFR Yugoslavia; 1993 Macedonian sporting identity is retained without assigning a modern birth-state id.'),
9496067:p('Charleroi','Raymond Mommens','1958-12-27',[17],17,'Lebbeke',13,'Left Midfield','701518',height=178,weight=70,position_url=TM_CHARLEROI),
9496054:p('Charleroi','Tibor Balog','1966-03-01',[93],93,'Kakucs',7,'Central Midfield','65240',height=180,weight=78,position_url=TM_CHARLEROI),
9496055:p('Charleroi','Dante Brogno','1966-05-02',[17,63],17,'Charleroi',17,'Centre-Forward','66101',height=177,position_url=TM_CHARLEROI),
9496066:p('Charleroi','Jean-Jacques Missé-Missé','1968-08-07',[66],66,'Yaoundé',17,'Centre-Forward','89488',height=180,weight=77,position_url=TM_CHARLEROI),
9496065:p('Charleroi','Nebojša Malbaša','1959-06-25',[75],None,'Belgrade (Yugoslavia)',17,'Centre-Forward','69290',position_url=TM_CHARLEROI,note='Born in SFR Yugoslavia; 1993 sporting nationality is FR Yugoslavia.'),
9496061:p('Charleroi','István Gulyás','1960-05-01',[93],93,'Sajószentpéter',0,'Goalkeeper','69301',height=183,weight=80),
9496057:p('Charleroi','Marco Casto','1972-06-02',[17,63],17,'Haine-Saint-Paul',2,'Left-Back','66025',height=175,weight=75,position_url=TM_CHARLEROI),
9496070:p('Charleroi','Fabrice Silvagni','1966-08-26',[17,63],17,None,3,'Centre-Back','69164',position_url=TM_CHARLEROI),
9496062:p('Charleroi','Frédéric Jacquemart','1972-06-12',[17],17,None,17,'Centre-Forward','69662',position_url=TM_CHARLEROI),
9496053:p('Charleroi','Atty Affo','1971-08-27',[81],81,None,7,'Midfielder','69506',precision='broad_only',position_url=TM_CHARLEROI),
9498006:p('Charleroi','Samuel Remy','1973-10-23',[17],17,'Mettet',13,'Left Midfield','68635',height=178,weight=71,position_url=TM_CHARLEROI,note='Separate identity from Jacques Remy (MDB/source_id 6387), which had been incorrectly reused by surname.'),
9496056:p('Charleroi','Gábor Bukrán','1975-11-16',[93],93,'Eger',7,'Central Midfield','402227',height=183,weight=78,position_url=TM_CHARLEROI),
9496058:p('Charleroi','Eric Depireux','1972-02-18',[17],17,None,3,'Defender','69661',precision='broad_only',position_url=TM_CHARLEROI),
9496059:p('Charleroi','Mario Fasano','1973-10-08',[17,63],17,'Charleroi',2,'Left-Back','68633',height=181,weight=82,position_url=TM_CHARLEROI),
9498011:p('Charleroi','Olivier Desbruyeres','1975-02-21',[17],17,None,0,'Goalkeeper',None,position_url=TM_CHARLEROI,profile_url=TM_CHARLEROI),
9498012:p('Charleroi','Michael Paci','1973-12-13',[17],17,None,17,'Centre-Forward',None,position_url=TM_CHARLEROI,profile_url=TM_CHARLEROI),
# Standard Liège — full BDF league row (26) plus source-roster Habran.
9495311:p('Standard Liège','Gilbert Bodart','1962-09-02',[17],17,'Ougrée',0,'Goalkeeper','87772',height=181),
9496318:p('Standard Liège','Mircea Rednic','1962-04-09',[72],72,'Hunedoara',1,'Right-Back','701515',height=175,weight=71,position_url=TM_STANDARD),
9496315:p('Standard Liège','Philippe Léonard','1974-02-14',[17],17,'Liège',2,'Left-Back','84825',height=185,weight=78,position_url=TM_STANDARD),
9496308:p('Standard Liège','André Cruz','1968-09-20',[62],62,'Piracicaba',3,'Centre-Back','99410',height=183,weight=83,position_url=TM_STANDARD),
9496311:p('Standard Liège','Dinga','1972-11-11',[62],62,None,2,'Left-Back','68866',height=179,weight=83,position_url=TM_STANDARD),
9495301:p('Standard Liège','Régis Genaux','1973-08-31',[17],17,'Charleroi',1,'Right-Back','96268',height=175,weight=73,position_url=TM_STANDARD),
9494221:p('Standard Liège','Marc Wilmots','1969-02-22',[17],17,'Dongelberg',8,'Attacking Midfield','90501',height=183,weight=89,position_url=TM_STANDARD),
9496309:p('Standard Liège','Patrick Asselman','1968-10-30',[17],17,None,8,'Attacking Midfield','89141',height=181,weight=80,position_url=TM_STANDARD),
9496313:p('Standard Liège','Guy Hellers','1964-10-10',[53],53,'Luxembourg',6,'Defensive Midfield','42786',position_url=TM_STANDARD),
9496310:p('Standard Liège','Roberto Bisconti','1973-07-21',[17,63],17,'Montegnée',6,'Defensive Midfield','84591',height=180,position_url=TM_STANDARD),
9495303:p('Standard Liège','Michaël Goossens','1973-11-30',[17],17,'Ougrée',17,'Centre-Forward','98196',height=183,weight=75,position_url=TM_STANDARD),
9496316:p('Standard Liège','Jacky Munaron','1956-09-08',[17],17,'Namur',0,'Goalkeeper','41774',height=180,weight=75),
9496328:p('Standard Liège','Gunther Schepens','1973-05-04',[17],17,'Gent',8,'Attacking Midfield','98424',height=175,weight=75,position_url=TM_STANDARD),
9496319:p('Standard Liège','Aleksandr Rytchkov','1974-09-29',[40],None,'Ussolje-Sibirskoje (USSR)',8,'Attacking Midfield','98434',height=178,position_url=TM_STANDARD,note='Born in the USSR; Russian football identity is retained without retrofitting a modern birth_country_id.'),
9496322:p('Standard Liège','Frans van Rooy','1963-07-03',[3],3,'Woensel',13,'Left Midfield','41859',height=177,weight=72,position_url=TM_STANDARD,note='BDFutbol spelling Van Rooy is retained; Transfermarkt uses Frans van Rooij.'),
9496321:p('Standard Liège','Yves Soudan','1967-10-23',[17],17,'Gent',17,'Centre-Forward','69528',position_url=TM_STANDARD),
9494020:p('Standard Liège','Bogdan Stelea','1967-12-05',[72],72,'București',0,'Goalkeeper','327',height=190,weight=87),
9496323:p('Standard Liège','Patrick Vervoort','1965-01-17',[17],17,'Beerse',13,'Left Midfield','81502',height=178,weight=76,position_url=TM_STANDARD),
9496320:p('Standard Liège','Axel Smeets','1974-07-12',[17],17,'Brussels',1,'Right-Back','303',height=181,weight=76,position_url=TM_STANDARD),
9496327:p('Standard Liège','Thierry Pister','1965-09-02',[17],17,'Gent',13,'Left Midfield','65661',position_url=TM_STANDARD),
9496314:p('Standard Liège','Mohamed Lashaf','1967-10-07',[17],17,'Mons',9,'Right Midfield','89086',height=182,weight=80,position_url=TM_STANDARD,note='BDFutbol classifies him broadly as forward; the 1993-94 Transfermarkt season squad supplies Right Midfield.'),
9495314:p('Standard Liège','Alain Bettagno','1968-11-09',[17],17,'Seraing',9,'Right Midfield','42175',position_url=TM_STANDARD),
9496312:p('Standard Liège','Didier Ernst','1971-09-15',[17],17,'Dison',1,'Right-Back','66188',height=176,weight=72,position_url=TM_STANDARD),
9496317:p('Standard Liège','Tim Nuyens','1974-07-16',[17],17,None,0,'Goalkeeper','69292'),
9498007:p('Standard Liège','Daniel Marc Kimoni','1971-08-18',[17],17,'Liège',3,'Centre-Back','701428',height=178,weight=76,position_url=TM_STANDARD,note='BDFutbol individual profile date (18/08/1971) is retained; this is a separate person from RFC Liège midfielder Donatien Kimoni.'),
9498008:p('Standard Liège','Emmanuel Duah','1976-11-14',[42],42,'Kumasi',16,'Left Winger','6844',height=177,weight=74,position_url=TM_STANDARD),
9498013:p('Standard Liège','Dimitri Habran','1975-08-22',[17],17,None,0,'Goalkeeper',None,position_url=TM_STANDARD,profile_url=TM_STANDARD),
# RFC Liège disambiguation.
9496276:p('RFC Liège','Donatien Kimoni','1973-10-07',[17],17,'Verviers',7,'Midfield',None,precision='broad_only',position_url=TM_DONATIEN,profile_url=TM_DONATIEN,note='Explicitly disambiguated from Daniel Marc Kimoni of Standard Liège.'),
}

NEW: dict[int,dict[str,Any]] = {
9498005:dict(team_id=TEAM['FC Seraing'],overall=73,stats=(25,31,30,2703,15),bdf_name='Edmilson',source_roster=False),
9498006:dict(team_id=TEAM['Charleroi'],overall=70,stats=(20,8,4,382,1),bdf_name='Remy',source_roster=False),
9498007:dict(team_id=TEAM['Standard Liège'],overall=69,stats=(22,1,0,4,0),bdf_name='Kimoni',source_roster=False),
9498008:dict(team_id=TEAM['Standard Liège'],overall=68,stats=(17,1,0,20,0),bdf_name='Duah',source_roster=False),
9498009:dict(team_id=TEAM['FC Seraing'],overall=68,stats=(28,0,0,0,0),bdf_name='Heinen',source_roster=True),
9498010:dict(team_id=TEAM['FC Seraing'],overall=68,stats=(26,0,0,0,0),bdf_name='Vanheusden',source_roster=True),
9498011:dict(team_id=TEAM['Charleroi'],overall=67,stats=(19,0,0,0,0),bdf_name='Desbruyeres',source_roster=True),
9498012:dict(team_id=TEAM['Charleroi'],overall=67,stats=(20,0,0,0,0),bdf_name='Paci',source_roster=True),
9498013:dict(team_id=TEAM['Standard Liège'],overall=67,stats=(18,0,0,0,0),bdf_name='Habran',source_roster=True),
}

FALSE_ALIAS = {
    4929: {'original_team_id':301,'wrong_club':'FC Seraing','wrong_name':'Edmilson','replacement':9498005,'identity':'Edmilson Dias Lucena'},
    6387: {'original_team_id':244,'wrong_club':'Charleroi','wrong_name':'Remy','replacement':9498006,'identity':'Jacques Remy'},
}

BELGIUM_FIELDS_TO_STRIP = {
 'historical_club_1994','historical_position_1993_94','historical_position_source','historical_position_source_url',
 'bdfutbol_name_1993_94','historical_age_1993_94','historical_club_spells_1993_94','historical_data_source',
 'bdfutbol_squad_url','historical_biography_1993_94','historical_biography_source_url','historical_biography_source_label',
 'historical_biography_evidence','historical_biography_status','historical_biography_staged_clubs','source_profile_position',
 'profile_position_precision','historical_profile_source','historical_profile_source_url','historical_profile_source_note',
 'historical_birth_place_text','historical_birth_place_source_url','historical_birth_place_source_label','profile_nationality_country_ids',
 'secondary_nationality_country_id','bdfutbol_id','bdfutbol_url','profile_review_required'
}


def load(path:Path): return json.loads(path.read_text(encoding='utf-8'))
def dump(path:Path,obj:Any): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def split_name(name:str):
    parts=name.split(); return (None,name) if len(parts)==1 else (' '.join(parts[:-1]),parts[-1])

def profile_url(patch:dict[str,Any]) -> str:
    if patch.get('profile_url'): return str(patch['profile_url'])
    return f"https://www.bdfutbol.com/en/j/j{patch['bdf']}.html"

def reattribute(player:dict[str,Any],role:int,originals:list[dict[str,Any]],sid:int,tag:str='0.36') -> None:
    a,b=comparable(originals,ROLE_TO_BROAD[role],int(player.get('overall') or 70),sid)
    player['attributes']=materialise_attributes(int(player.get('overall') or 70),a,b)
    player['attribute_source']=f'fixed_source_comparable_role_correction_{tag}'
    player['attribute_comparable_source_ids']=[int(a['source_id']),int(b['source_id'])]

def restore_false_aliases(snapshot:dict[str,Any],stage:dict[str,Any]) -> list[dict[str,Any]]:
    by={int(x['source_id']):x for x in snapshot['players']}; repairs=[]
    for sid,meta in FALSE_ALIAS.items():
        player=by[sid]
        before_team=player.get('team_id'); before_hist=player.get('historical_club_1994')
        player['team_id']=meta['original_team_id']
        for key in BELGIUM_FIELDS_TO_STRIP: player.pop(key,None)
        # The original raw identities did not have Belgium nationality assigned. Preserve their pre-import biography/core fields.
        player['historical_identity_repair_v036']={
            'reason':'false_surname_alias_reuse_in_belgium_v025',
            'restored_team_id':meta['original_team_id'],
            'replaced_belgium_identity_with_source_id':meta['replacement'],
        }
        club=next(c for c in stage['clubs'] if c['name']==meta['wrong_club'])
        row=next(r for r in club['players'] if r.get('bdfutbol_name')==meta['wrong_name'])
        row['resolved_source_id']=meta['replacement']
        row['identity_resolution']='created_historical_identity_after_false_alias_repair'
        row['identity_repair_note']=f"source_id {sid} ({meta['identity']}) restored to original team {meta['original_team_id']}; Belgian row gets separate historical identity {meta['replacement']}."
        repairs.append({'source_id':sid,'identity':meta['identity'],'before_team_id':before_team,'before_historical_club_1994':before_hist,'restored_team_id':meta['original_team_id'],'replacement_source_id':meta['replacement']})
    return repairs

def make_player(sid:int,patch:dict[str,Any],meta:dict[str,Any],originals:list[dict[str,Any]]) -> dict[str,Any]:
    first,surname=split_name(patch['name']); role=int(patch['role']); overall=int(meta['overall'])
    a,b=comparable(originals,ROLE_TO_BROAD[role],overall,sid); attrs=materialise_attributes(overall,a,b)
    return {
      'source_id':sid,'team_id':meta['team_id'],'display_name':patch['name'],'first_name':first,'surname1':surname,'surname2':None,
      'birth_date':patch['dob']+'T00:00:00','birth_country_id':patch['birth_country'],'international_country_id':patch['nat'][0],
      'preferred_foot':None,'shirt_number':None,'primary_role':role,'broad_position':ROLE_TO_BROAD[role],'overall':overall,'category':overall,
      'height_cm':patch.get('height'),'weight_kg':patch.get('weight'),'salary':0,'release_clause':0,'contract_start_year':1993,'contract_end_year':None,
      'loan':False,'initially_reserve':True,'retired':False,'attributes':attrs,'birth_city_id':None,'naturalized_country_id':None,'basque_origin':False,
      'favorite_shirt_number':None,'injury_proneness':0,'progression_mean':0,'fan_affection':0,'academy_team_id':None,'previous_team_id':None,
      'previous_team_years':None,'buyback_option':False,'role_ratings':role_ratings(role),
      'hidden_traits':{'individualist':False,'killer_pass':False,'holds_ball':False,'long_shots':False,'cuts_inside':False,'first_time_play':False,'dives':False},
      'historical_squad_1994':True,'external_origin':'historical_belgium_1993_94','creation_batch':'belgium_profiles_deep_0.36',
      'attribute_source':'fixed_source_comparable_role_profile_0.36','attribute_comparable_source_ids':[int(a['source_id']),int(b['source_id'])],
    }

def append_new_stage_rows(stage:dict[str,Any]) -> None:
    # Replacement rows already exist: Edmilson/Remy. Add BDF league rows absent from old staging + source-visible season-squad members.
    for sid in [9498007,9498008,9498009,9498010,9498011,9498012,9498013]:
        meta=NEW[sid]; patch=P[sid]; club=next(c for c in stage['clubs'] if c['name']==patch['club'])
        if any(int(r.get('resolved_source_id') or -1)==sid for r in club['players']): continue
        age,apps,starts,minutes,goals=meta['stats']
        club['players'].append({
          'bdfutbol_name':meta['bdf_name'],'age_1993_94':age,'appearances':apps,'starts':starts,'minutes':minutes,'goals':goals,
          'core_18_candidate':False,'source_roster_member':True,'league_row_absent':bool(meta['source_roster']),
          'identity_resolution':'created_historical_identity','resolved_source_id':sid,'resolved_display_name':patch['name'],
          'opening_club_1993_94':patch['club'],
        })

def apply_profile(player:dict[str,Any],patch:dict[str,Any],originals:list[dict[str,Any]],sid:int) -> dict[str,Any]:
    before={'display_name':player.get('display_name'),'role':int(player.get('primary_role') or 0),'broad':player.get('broad_position'),'position':player.get('historical_position_1993_94'),'birth_date':player.get('birth_date'),'country':player.get('international_country_id')}
    first,surname=split_name(patch['name']); player['display_name']=patch['name']; player['first_name']=first; player['surname1']=surname
    player['birth_date']=patch['dob']+'T00:00:00'
    if patch.get('birth_country') is None: player.pop('birth_country_id',None)
    else: player['birth_country_id']=int(patch['birth_country'])
    player['international_country_id']=int(patch['nat'][0]); player['profile_nationality_country_ids']=[int(x) for x in patch['nat']]
    if len(patch['nat'])>1: player['secondary_nationality_country_id']=int(patch['nat'][1])
    else: player.pop('secondary_nationality_country_id',None)
    player['historical_birth_place_text']=patch.get('place')
    url=profile_url(patch); player['historical_birth_place_source_url']=url; player['historical_birth_place_source_label']='BDFutbol/Transfermarkt profile cross-check v0.36'
    if patch.get('bdf'):
        player['bdfutbol_id']=str(patch['bdf']); player['bdfutbol_url']=url
    if patch.get('height') is not None: player['height_cm']=int(patch['height'])
    if patch.get('weight') is not None: player['weight_kg']=int(patch['weight'])
    role=int(patch['role']); old_role=int(player.get('primary_role') or 0); old_broad=player.get('broad_position')
    player['primary_role']=role; player['broad_position']=ROLE_TO_BROAD[role]; player['role_ratings']=role_ratings(role)
    precision=patch.get('precision','exact'); player['profile_position_precision']=precision; player['source_profile_position']=patch['pos']; player['profile_review_required']=precision=='broad_only'
    if precision=='broad_only':
        player['historical_position_1993_94']=patch['pos']+' (exact role unresolved)'; player['historical_position_source']='BDFutbol/Transfermarkt broad position only v0.36'
    else:
        player['historical_position_1993_94']=ROLE_TO_LABEL[role]; player['historical_position_source']='BDFutbol identity + Transfermarkt 1993-94 specialist role v0.36'
    player['historical_position_source_url']=patch.get('position_url') or url
    player['historical_profile_source']='BDFutbol individual profile + Transfermarkt 1993-94 season cross-check v0.36'
    player['historical_profile_source_url']=url
    if patch.get('note'): player['historical_profile_source_note']=patch['note']
    player['historical_club_1994']=patch['club']; player['historical_data_source']='BDFutbol 1993-94 + Transfermarkt season/profile cross-check v0.36'
    player['bdfutbol_squad_url']={'FC Seraing':BDF_SERAING,'Charleroi':BDF_CHARLEROI,'Standard Liège':BDF_STANDARD,'RFC Liège':BDF_RFC_LIEGE}[patch['club']]
    if role!=old_role or player['broad_position']!=old_broad: reattribute(player,role,originals,sid)
    return {'source_id':sid,'club':patch['club'],'before':before,'after':{'display_name':player['display_name'],'role':role,'broad':player['broad_position'],'position':player['historical_position_1993_94'],'birth_date':player['birth_date'],'country':player['international_country_id']},'role_changed':role!=old_role,'precision':precision}

def sync_entry(target:dict[str,Any],player:dict[str,Any],patch:dict[str,Any]) -> None:
    target.update({'display_name':player['display_name'],'first_name':player.get('first_name'),'surname1':player.get('surname1'),'birth_date':str(player['birth_date'])[:10],
      'country_id':player.get('international_country_id'),'country_name':COUNTRY_NAME.get(player.get('international_country_id')),'broad_position':player.get('broad_position'),
      'team_id':player.get('team_id'),'team_name':patch['club'],'historical_position_1993_94':player.get('historical_position_1993_94'),'historical_club_1994':patch['club'],
      'profile_review_required':bool(player.get('profile_review_required')),'individual_profile_source':'BDFutbol/Transfermarkt profile cross-check v0.36',
      'individual_profile_source_url':profile_url(patch),'historical_birth_place_text':patch.get('place')})
    if patch.get('bdf'):
        target.update({'bdfutbol_id':str(patch['bdf']),'bdfutbol_url':profile_url(patch),'photo_status':target.get('photo_status') if target.get('photo_status','').startswith('bundled') else 'ready_for_download'})

def ensure_registry_queue(reg:dict[str,Any],queue:dict[str,Any],player:dict[str,Any],patch:dict[str,Any]) -> None:
    sid=int(player['source_id']); reg_by={int(x['source_id']):x for x in reg['players']}; q_by={int(x['source_id']):x for x in queue['players']}
    if sid not in reg_by:
        reg_by[sid]={'source_id':sid,'display_name':player['display_name'],'first_name':player.get('first_name'),'surname1':player.get('surname1'),'surname2':None,
          'birth_date':str(player['birth_date'])[:10],'country_id':player.get('international_country_id'),'country_name':COUNTRY_NAME.get(player.get('international_country_id')),
          'broad_position':player['broad_position'],'team_id':player['team_id'],'team_name':patch['club'],'creation_batch':player.get('creation_batch'),
          'identity_source':'BDFutbol/Transfermarkt Belgium 1993-94 identity gate v0.36','identity_source_url':profile_url(patch),'verified_national_pool_year':1994,
          'historical_position_1993_94':player['historical_position_1993_94'],'historical_club_1994':patch['club'],'overall':player['overall'],'attribute_source':player.get('attribute_source'),
          'profile_review_required':bool(player.get('profile_review_required')),'duplicate_check':'exact_name_birthdate_source_profile_gate_v036','matched_existing_id':None,
          'bdfutbol_search_name':player['display_name'],'bdfutbol_id':str(patch.get('bdf') or ''),'bdfutbol_url':profile_url(patch) if patch.get('bdf') else '',
          'photo_filename':f'{sid}.jpg','photo_status':'ready_for_download' if patch.get('bdf') else 'pending_identity_profile'}
        reg['players'].append(reg_by[sid])
    if sid not in q_by:
        base=dict(reg_by[sid]); base.pop('overall',None); base.pop('attribute_source',None); base.update({'photo_width':40,'photo_height':55,'photo_format':'JPEG','photo_mode':'RGB'})
        queue['players'].append(base); q_by[sid]=base
    sync_entry(reg_by[sid],player,patch); sync_entry(q_by[sid],player,patch)

def sync_bundled_photos(reg:dict[str,Any], queue:dict[str,Any]) -> list[dict[str,Any]]:
    reg_by={int(x['source_id']):x for x in reg['players']}; q_by={int(x['source_id']):x for x in queue['players']}; rows=[]
    for sid,url in PHOTO_URLS.items():
        out=PHOTO_DIR/f'{sid}.jpg'
        if not out.exists(): continue
        for target in (reg_by[sid],q_by[sid]):
            target.update({'photo_filename':f'{sid}.jpg','photo_status':'bundled_normalized_bdfutbol','photo_width':40,'photo_height':55,'photo_format':'JPEG','photo_mode':'RGB','photo_source':'BDFutbol individual profile v0.36','photo_source_url':url})
        rows.append({'source_id':sid,'display_name':reg_by[sid]['display_name'],'photo_url':url,'asset':str(out.relative_to(ROOT))})
    return rows

def update_stage(stage:dict[str,Any],sid:int,player:dict[str,Any],patch:dict[str,Any]) -> None:
    club=next(c for c in stage['clubs'] if c['name']==patch['club']); row=next(r for r in club['players'] if int(r.get('resolved_source_id') or -1)==sid)
    row.update({'resolved_display_name':player['display_name'],'resolved_primary_role':player['primary_role'],'resolved_exact_position':player['historical_position_1993_94'],
      'resolved_birth_date':player['birth_date'],'resolved_country_id':player['international_country_id'],'source_profile_position':patch['pos'],
      'profile_source':'BDFutbol/Transfermarkt 1993-94 profile cross-check v0.36','profile_source_url':profile_url(patch),
      'position_source':player['historical_position_source'],'position_source_url':player['historical_position_source_url'],'resolved_birth_place_text':patch.get('place'),
      'individual_profile_source_url':profile_url(patch)})
    if patch.get('bdf'): row['bdfutbol_id']=str(patch['bdf'])
    if patch.get('note'): row['profile_source_note']=patch['note']

def write_spells(snapshot:dict[str,Any],stage:dict[str,Any]) -> None:
    by={int(x['source_id']):x for x in snapshot['players']}; rows:dict[int,list[tuple[str,dict[str,Any]]]]={}
    for c in stage['clubs']:
        for r in c['players']:
            if r.get('resolved_source_id') is not None: rows.setdefault(int(r['resolved_source_id']),[]).append((c['name'],r))
    for sid in P:
        p=by[sid]; allrows=rows.get(sid,[])
        spells=[]
        for team,row in allrows:
            spells.append({'club':team,'team_id':TEAM.get(team,p.get('team_id')),'appearances':row.get('appearances'),'starts':row.get('starts'),'minutes':row.get('minutes'),'goals':row.get('goals'),'source_roster_member':bool(row.get('source_roster_member')),'league_row_absent':bool(row.get('league_row_absent'))})
        if spells: p['historical_club_spells_1993_94']=spells

def biography(player:dict[str,Any],team:str,row:dict[str,Any]) -> str:
    if player.get('profile_position_precision')=='broad_only': role={'POR':'Portero','DEF':'Defensa','MED':'Centrocampista','DEL':'Delantero'}.get(player.get('broad_position'),'Futbolista')
    else: role=ROLE_ES.get(int(player.get('primary_role') or 0),'Futbolista')
    parts=[f'{role} de {team} en la temporada 1993-94.']
    if row.get('league_row_absent'):
        parts.append('Consta como miembro de la plantilla de temporada en la fuente especializada; no se inventan minutos ni apariciones de liga ausentes de la tabla BDFutbol utilizada.')
    else:
        stats=[]
        for key,label in [('appearances','partidos'),('starts','como titular')]:
            v=row.get(key)
            if isinstance(v,int) and v>=0: stats.append(f'{v} {label}')
        if isinstance(row.get('minutes'),int) and row['minutes']>=0: stats.append(f"{row['minutes']:,}".replace(',','.')+' minutos')
        if stats: parts.append('En el registro histórico figura con '+', '.join(stats)+'.')
        if int(player.get('primary_role') or 0)!=0 and isinstance(row.get('goals'),int) and row['goals']>=0: parts.append(f"Marcó {row['goals']} gol"+('' if row['goals']==1 else 'es')+'.')
    y,m,d=str(player['birth_date'])[:10].split('-'); parts.append(f'Fecha de nacimiento registrada: {d}/{m}/{y}.')
    if player.get('historical_birth_place_text'): parts.append('Lugar de nacimiento documentado: '+str(player['historical_birth_place_text'])+'.')
    return ' '.join(parts)

def regenerate_bios(snapshot:dict[str,Any],stage:dict[str,Any]) -> dict[str,Any]:
    by={int(p['source_id']):p for p in snapshot['players']}; lookup={}
    for c in stage['clubs']:
        for r in c['players']:
            sid=r.get('resolved_source_id')
            if sid is not None: lookup.setdefault(int(sid),[]).append((c['name'],r))
    changed=0
    for sid,patch in P.items():
        candidates=lookup.get(sid)
        if not candidates: raise RuntimeError(f'missing staging row for curated Belgium id {sid}')
        team,row=next((x for x in candidates if x[0]==patch['club']),candidates[0]); p=by[sid]
        old=p.get('historical_biography_1993_94'); new=biography(p,team,row); p['historical_biography_1993_94']=new
        p['historical_biography_source_url']=row.get('profile_source_url') or profile_url(patch); p['historical_biography_source_label']=row.get('profile_source') or 'BDFutbol/Transfermarkt v0.36'
        p['historical_biography_evidence']={'season':'1993-94','club':team,'appearances':row.get('appearances'),'starts':row.get('starts'),'minutes':row.get('minutes'),'goals':row.get('goals'),'staging_name':row.get('bdfutbol_name'),'source_roster_member':bool(row.get('source_roster_member')),'league_row_absent':bool(row.get('league_row_absent'))}
        p['historical_biography_status']='source_backed_season_summary'; p['historical_biography_staged_clubs']=[x[0] for x in candidates]
        changed+=old!=new
    return {'profiles_considered':len(P),'biographies_changed':changed,'missing_stage_rows':0}

def main() -> None:
    snap=load(SNAP); reg=load(REG); queue=load(QUEUE); stage=load(STAGE)
    before=profile_gap_stats(snap); originals=[p for p in snap['players'] if p.get('attributes') and not p.get('external_origin') and not p.get('creation_batch')]
    repairs=restore_false_aliases(snap,stage); append_new_stage_rows(stage)
    by={int(x['source_id']):x for x in snap['players']}
    # New names must not collide with a different identity before materialisation.
    for sid in NEW:
        patch=P[sid]
        collisions=[p for p in snap['players'] if int(p['source_id'])!=sid and (p.get('display_name') or '').casefold()==patch['name'].casefold() and str(p.get('birth_date') or '')[:10]==patch['dob']]
        if collisions: raise RuntimeError(f'duplicate identity gate for {sid} {patch["name"]}: {[x["source_id"] for x in collisions]}')
        if sid not in by:
            player=make_player(sid,patch,NEW[sid],originals); snap['players'].append(player); by[sid]=player
    changes=[]
    for sid,patch in P.items():
        changes.append(apply_profile(by[sid],patch,originals,sid)); ensure_registry_queue(reg,queue,by[sid],patch); update_stage(stage,sid,by[sid],patch)
    write_spells(snap,stage); bios=regenerate_bios(snap,stage); photos=sync_bundled_photos(reg,queue)
    after=profile_gap_stats(snap)
    reg_ids=[int(x['source_id']) for x in reg['players']]; q_ids=[int(x['source_id']) for x in queue['players']]
    if len(reg_ids)!=len(set(reg_ids)) or len(q_ids)!=len(set(q_ids)) or set(reg_ids)!=set(q_ids): raise RuntimeError('registry/queue identity integrity failure')
    # Ensure repaired raw aliases are no longer attached to Belgium clubs.
    for sid,meta in FALSE_ALIAS.items():
        if by[sid].get('team_id')!=meta['original_team_id'] or by[sid].get('historical_club_1994')==meta['wrong_club']: raise RuntimeError(f'false alias repair failed {sid}')
    counts={c['name']:len(c['players']) for c in stage['clubs'] if c['name'] in {'FC Seraing','Charleroi','Standard Liège','RFC Liège'}}
    audit={'schema_version':1,'checkpoint':'0.36.0-belgium-seraing-charleroi-standard-deep','status':'pass','profile_gaps_before':before,'profile_gaps_after':after,
      'profiles':{'curated_this_batch':len(P),'new_historical_identities':len(NEW),'by_club':dict(Counter(x['club'] for x in P.values())),
        'exact_specialist_roles':sum(x.get('precision','exact')=='exact' for x in P.values()),'broad_only_exact_role_unresolved':sum(x.get('precision')=='broad_only' for x in P.values()),
        'role_corrections_this_batch':sum(bool(x['role_changed']) for x in changes),'changes':changes},
      'identity_repairs':repairs,'source_roster_union':{'club_stage_counts_after':counts,'source_visible_without_bdf_league_row':[sid for sid,m in NEW.items() if m['source_roster']],
        'standard_bdf_league_row_additions':[9498007,9498008]},'biographies':bios,
      'photos':{'new_portraits_bundled_this_batch':len(photos),'rows':photos,'bdf_individual_profiles_queued_ready_for_download':sum(bool(x.get('bdf')) for x in P.values()),'total_bundled_normalized_bdfutbol':sum(x.get('photo_status')=='bundled_normalized_bdfutbol' for x in reg['players']),'note':'Only portraits retrieved from viewed BDFutbol individual-profile assets are bundled; remaining identified BDF profiles stay queued.'},
      'identity_integrity':{'registry_rows':len(reg_ids),'unique_registry_ids':len(set(reg_ids)),'sets_match':set(reg_ids)==set(q_ids)},
      'source_policy':['Full source-visible 1993-94 squad union is preferred over an arbitrary 18-player cap.','No league minutes are invented for players visible only in the season squad source.','Surname-only identity reuse is rejected when date/profile evidence identifies a different person.','Former USSR/Yugoslavia birth states are kept textually rather than retrofitted to modern successor-state birth_country_id values.','Broad source positions remain exact-role unresolved.','No basketball 75/25 rule is used.']}
    dump(SNAP,snap); dump(REG,reg); dump(QUEUE,queue); dump(STAGE,stage)
    dump(DATA/'historical_profiles_metadata_audit_v036.json',audit); dump(DATA/'historical_metadata_gaps_v036.json',{'checkpoint':audit['checkpoint'],'gaps':after}); dump(DATA/'historical_biographies_audit_v036.json',bios); dump(DATA/'belgium_identity_repairs_v036.json',{'checkpoint':audit['checkpoint'],'status':'pass','repairs':repairs}); dump(DATA/'bdfutbol_photo_normalization_v036_belgium.json',{'checkpoint':audit['checkpoint'],'status':'pass','portraits':photos})
    print(json.dumps({'curated':len(P),'new_identities':len(NEW),'identity_repairs':len(repairs),'club_counts':counts,'belgium_gaps_before':before['Belgium'],'belgium_gaps_after':after['Belgium'],'role_corrections':audit['profiles']['role_corrections_this_batch'],'broad_only':audit['profiles']['broad_only_exact_role_unresolved']},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
