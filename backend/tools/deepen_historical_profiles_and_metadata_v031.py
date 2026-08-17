from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from tools.review_created_player_profiles import materialise_attributes

DATA = ROOT / 'data' / 'football9394'
SNAP = DATA / 'historical_snapshot.json'
CATALOG = DATA / 'historical_source_catalog.json'
REGISTRY = DATA / 'created_players_registry.json'
QUEUE = DATA / 'bdfutbol_photo_queue.json'
PHOTO_DIR = ROOT / 'frontend' / 'public' / 'historical9394' / 'players'
STAGES = {
    'Belgium': DATA / 'belgium_1993_94_roster_staging.json',
    'Turkey': DATA / 'turkey_1993_94_roster_staging.json',
    'Russia': DATA / 'russia_1993_roster_staging.json',
    'Greece': DATA / 'greece_1993_94_roster_staging.json',
}
LEAGUES = {'Russia': 930015, 'Greece': 930047, 'Belgium': 930052, 'Turkey': 930057}

ROLE_TO_BROAD = {
    0:'POR',1:'DEF',2:'DEF',3:'DEF',4:'DEF',5:'DEF',6:'MED',7:'MED',8:'MED',9:'MED',10:'MED',11:'DEL',12:'DEL',13:'MED',14:'MED',15:'DEL',16:'DEL',17:'DEL'
}
ROLE_TO_LABEL = {
    0:'Goalkeeper',1:'Right Back',2:'Left Back',3:'Centre Back',4:'Centre Back',5:'Libero',6:'Defensive Midfielder',7:'Centre Midfielder',8:'Attacking Midfielder',9:'Right Midfielder',10:'Right Inside',11:'Right Attacking Midfielder',12:'Right Winger',13:'Left Midfielder',14:'Left Inside',15:'Left Attacking Midfielder',16:'Left Winger',17:'Centre Forward'
}
COUNTRY_NAME = {
    3:'Países Bajos',15:'Australia',17:'Bélgica',20:'Bosnia-Herzegovina',31:'Croacia',39:'Estonia',40:'Rusia',42:'Ghana',47:'Grecia',52:'Lituania',54:'Macedonia',59:'Nigeria',70:'Polonia',76:'Montenegro',79:'Suecia',84:'Turquía',85:'Ucrania',93:'Hungría',112:'Zambia',209:'Uzbekistán'
}

TM_ANDERLECHT = 'https://www.transfermarkt.com/rsc-anderlecht/kader/verein/58/saison_id/1993/plus/1'
TM_BRUGGE = 'https://www.transfermarkt.com/club-brugge-kv/kader/verein/2282/saison_id/1993/plus/1'
TM_SPARTAK = 'https://www.transfermarkt.com/spartak-moskau/kader/verein/232/saison_id/1993'
TM_AEK = 'https://www.transfermarkt.com/aek-athens/kader/verein/2441/saison_id/1993'
BDF = 'https://www.bdfutbol.com/en/j/j{id}.html'

# Season-specific profile rows. `nationalities` are citizenship/national-team context;
# they are deliberately not copied into birth_country_id unless a BDF individual
# profile explicitly supplies a birth country.
PROFILE_PATCH: dict[int, dict[str, Any]] = {
    # Anderlecht 1993-94 detailed squad.
    9494216: dict(country='Belgium', dob='1964-07-05', nationalities=[17], height=185, role=0, pos='Goalkeeper', url=TM_ANDERLECHT, source='Transfermarkt detailed squad 1993-94'),
    9496002: dict(country='Belgium', dob='1964-06-01', nationalities=[17], height=188, role=0, pos='Goalkeeper', url=TM_ANDERLECHT, source='Transfermarkt detailed squad 1993-94'),
    9494209: dict(country='Belgium', dob='1967-08-10', nationalities=[17], height=190, role=3, pos='Centre-Back', url=TM_ANDERLECHT, source='Transfermarkt detailed squad 1993-94'),
    9496007: dict(country='Belgium', dob='1960-03-26', nationalities=[3,15], height=186, role=3, pos='Centre-Back', url=TM_ANDERLECHT, source='Transfermarkt detailed squad 1993-94'),
    9494182: dict(country='Belgium', dob='1967-01-01', nationalities=[59], height=178, role=3, pos='Centre-Back', url=TM_ANDERLECHT, source='Transfermarkt detailed squad 1993-94'),
    9496001: dict(country='Belgium', dob='1960-09-09', nationalities=[3], role=3, pos='Centre-Back', url=TM_ANDERLECHT, source='Transfermarkt detailed squad 1993-94'),
    9494217: dict(country='Belgium', dob='1958-01-19', nationalities=[17], height=171, role=2, pos='Left-Back', url=TM_ANDERLECHT, source='Transfermarkt detailed squad 1993-94'),
    9495305: dict(country='Belgium', dob='1971-10-15', nationalities=[17], height=178, role=1, pos='Right-Back', url=TM_ANDERLECHT, source='Transfermarkt detailed squad 1993-94'),
    9496008: dict(country='Belgium', dob='1971-10-16', nationalities=[17], height=185, role=1, pos='Right-Back', url=TM_ANDERLECHT, source='Transfermarkt detailed squad 1993-94'),
    9496003: dict(country='Belgium', dob='1965-11-04', nationalities=[17], role=1, pos='Right-Back', url=TM_ANDERLECHT, source='Transfermarkt detailed squad 1993-94'),
    9495172: dict(country='Belgium', dob='1974-09-01', nationalities=[42,17], height=169, role=1, pos='Right-Back', url=TM_ANDERLECHT, source='Transfermarkt detailed squad 1993-94'),
    9496005: dict(country='Belgium', dob='1973-09-03', nationalities=[17], height=180, role=6, pos='Defensive Midfield', url=TM_ANDERLECHT, source='Transfermarkt detailed squad 1993-94'),
    9495308: dict(country='Belgium', dob='1972-02-01', nationalities=[17], height=174, role=7, pos='Central Midfield', url=TM_ANDERLECHT, source='Transfermarkt detailed squad 1993-94'),
    9496004: dict(country='Belgium', dob='1969-08-22', nationalities=[112], role=7, pos='Central Midfield', url=TM_ANDERLECHT, source='Transfermarkt detailed squad 1993-94'),
    9496000: dict(country='Belgium', dob='1970-06-25', nationalities=[17], height=175, role=9, pos='Right Midfield', url=TM_ANDERLECHT, source='Transfermarkt detailed squad 1993-94'),
    9494218: dict(country='Belgium', dob='1966-02-25', nationalities=[17], height=180, role=9, pos='Right Midfield', url=TM_ANDERLECHT, source='Transfermarkt detailed squad 1993-94'),
    9494219: dict(country='Belgium', dob='1965-07-10', nationalities=[17], height=173, role=13, pos='Left Midfield', url=TM_ANDERLECHT, source='Transfermarkt detailed squad 1993-94'),
    9495302: dict(country='Belgium', dob='1967-08-27', nationalities=[17], height=185, role=13, pos='Left Midfield', url=TM_ANDERLECHT, source='Transfermarkt detailed squad 1993-94'),
    9496009: dict(country='Belgium', dob='1961-06-20', nationalities=[17], height=173, role=13, pos='Left Midfield', url=TM_ANDERLECHT, source='Transfermarkt detailed squad 1993-94'),
    9496010: dict(country='Belgium', dob='1970-10-14', nationalities=[79], height=174, role=8, pos='Attacking Midfield', url=TM_ANDERLECHT, source='Transfermarkt detailed squad 1993-94'),
    9494213: dict(country='Belgium', dob='1967-05-25', nationalities=[17], height=183, role=17, pos='Centre-Forward', url=TM_ANDERLECHT, source='Transfermarkt detailed squad 1993-94'),
    9496006: dict(country='Belgium', dob='1974-09-08', nationalities=[42], height=180, role=17, pos='Centre-Forward', url=TM_ANDERLECHT, source='Transfermarkt detailed squad 1993-94'),
    9494244: dict(country='Belgium', dob='1965-02-01', nationalities=[3], height=188, role=17, pos='Centre-Forward', url=TM_ANDERLECHT, source='Transfermarkt detailed squad 1993-94'),
    9494214: dict(country='Belgium', dob='1965-09-04', nationalities=[17], height=172, role=17, pos='Centre-Forward', url=TM_ANDERLECHT, source='Transfermarkt detailed squad 1993-94'),

    # Club Brugge 1993-94 detailed squad.
    9494223: dict(country='Belgium', dob='1963-08-15', nationalities=[17], height=175, role=0, pos='Goalkeeper', url=TM_BRUGGE, source='Transfermarkt detailed squad 1993-94'),
    9496071: dict(country='Belgium', dob='1973-01-03', nationalities=[17], role=0, pos='Goalkeeper', url=TM_BRUGGE, source='Transfermarkt detailed squad 1993-94'),
    9496074: dict(country='Belgium', dob='1962-06-04', nationalities=[93], height=180, role=3, pos='Centre-Back', url=TM_BRUGGE, source='Transfermarkt detailed squad 1993-94'),
    9496072: dict(country='Belgium', dob='1961-08-02', nationalities=[17], height=183, role=3, pos='Centre-Back', url=TM_BRUGGE, source='Transfermarkt detailed squad 1993-94'),
    9495306: dict(country='Belgium', dob='1965-05-07', nationalities=[17], height=181, role=3, pos='Centre-Back', url=TM_BRUGGE, source='Transfermarkt detailed squad 1993-94'),
    9494208: dict(country='Belgium', dob='1963-06-01', nationalities=[17], height=176, role=2, pos='Left-Back', url=TM_BRUGGE, source='Transfermarkt detailed squad 1993-94'),
    9494225: dict(country='Belgium', dob='1971-08-03', nationalities=[17], height=183, role=2, pos='Left-Back', url=TM_BRUGGE, source='Transfermarkt detailed squad 1993-94'),
    9494207: dict(country='Belgium', dob='1968-09-15', nationalities=[17], height=184, role=1, pos='Right-Back', url=TM_BRUGGE, source='Transfermarkt detailed squad 1993-94'),
    9496078: dict(country='Belgium', dob='1970-09-15', nationalities=[17], height=184, role=1, pos='Right-Back', url=TM_BRUGGE, source='Transfermarkt detailed squad 1993-94'),
    9494211: dict(country='Belgium', dob='1964-04-30', nationalities=[17], height=183, role=6, pos='Defensive Midfield', url=TM_BRUGGE, source='Transfermarkt detailed squad 1993-94'),
    9496077: dict(country='Belgium', dob='1972-04-05', nationalities=[15,17], height=181, role=6, pos='Defensive Midfield', url=TM_BRUGGE, source='Transfermarkt detailed squad 1993-94'),
    9494212: dict(country='Belgium', dob='1961-04-30', nationalities=[17], height=184, role=6, pos='Defensive Midfield', url=TM_BRUGGE, source='Transfermarkt detailed squad 1993-94'),
    9496080: dict(country='Belgium', dob='1973-04-04', nationalities=[17], height=183, role=7, pos='Central Midfield', url=TM_BRUGGE, source='Transfermarkt detailed squad 1993-94'),
    9496081: dict(country='Belgium', dob='1964-07-21', nationalities=[17], height=187, role=9, pos='Right Midfield', url=TM_BRUGGE, source='Transfermarkt detailed squad 1993-94'),
    9496073: dict(country='Belgium', dob='1961-08-17', nationalities=[17], role=9, pos='Right Midfield', url=TM_BRUGGE, source='Transfermarkt detailed squad 1993-94'),
    9494224: dict(country='Belgium', dob='1969-07-03', nationalities=[17], height=180, role=13, pos='Left Midfield', url=TM_BRUGGE, source='Transfermarkt detailed squad 1993-94'),
    9496079: dict(country='Belgium', dob='1973-12-24', nationalities=[17], role=16, pos='Left Winger', url=TM_BRUGGE, source='Transfermarkt detailed squad 1993-94'),
    9495312: dict(country='Belgium', dob='1970-09-20', nationalities=[17], height=188, role=12, pos='Right Winger', url=TM_BRUGGE, source='Transfermarkt detailed squad 1993-94'),
    9494186: dict(country='Belgium', dob='1972-12-30', nationalities=[59], height=182, role=17, pos='Centre-Forward', url=TM_BRUGGE, source='Transfermarkt detailed squad 1993-94'),
    9496076: dict(country='Belgium', dob='1964-04-06', nationalities=[3], role=17, pos='Centre-Forward', url=TM_BRUGGE, source='Transfermarkt detailed squad 1993-94'),
    9496075: dict(country='Belgium', dob='1968-08-08', nationalities=[70], height=176, role=17, pos='Centre-Forward', url=TM_BRUGGE, source='Transfermarkt detailed squad 1993-94'),

    # Spartak Moscow season squad: compact page gives role + nationality, not safe exact DOB.
    9496613: dict(country='Russia', nationalities=[52], role=0, pos='Goalkeeper', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    9497356: dict(country='Russia', nationalities=[40], role=0, pos='Goalkeeper', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    2705: dict(country='Russia', nationalities=[40], role=0, pos='Goalkeeper', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    9496617: dict(country='Russia', nationalities=[40,85], role=0, pos='Goalkeeper', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    9494088: dict(country='Russia', nationalities=[40,85], role=3, pos='Centre-Back', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    9494081: dict(country='Russia', nationalities=[40,85], role=3, pos='Centre-Back', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    9496618: dict(country='Russia', nationalities=[40], role=3, pos='Centre-Back', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    9496614: dict(country='Russia', nationalities=[40], role=3, pos='Centre-Back', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    9497352: dict(country='Russia', nationalities=[40], role=3, pos='Centre-Back', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    9497355: dict(country='Russia', nationalities=[40], role=3, pos='Centre-Back', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    9495357: dict(country='Russia', nationalities=[40], role=2, pos='Left-Back', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    9494090: dict(country='Russia', nationalities=[40], role=1, pos='Right-Back', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    9494083: dict(country='Russia', nationalities=[40], role=6, pos='Defensive Midfield', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    9494087: dict(country='Russia', nationalities=[40,85], role=7, pos='Central Midfield', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    9494089: dict(country='Russia', nationalities=[40], role=7, pos='Central Midfield', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    9497358: dict(country='Russia', nationalities=[40], role=7, pos='Central Midfield', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    9494084: dict(country='Russia', nationalities=[40,39], role=9, pos='Right Midfield', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    9497349: dict(country='Russia', nationalities=[40], role=9, pos='Right Midfield', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    9497350: dict(country='Russia', nationalities=[40], role=8, pos='Attacking Midfield', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    9496616: dict(country='Russia', nationalities=[40], role=8, pos='Attacking Midfield', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    9497354: dict(country='Russia', nationalities=[85,40], role=8, pos='Attacking Midfield', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    9497357: dict(country='Russia', nationalities=[40,209], role=17, pos='Second Striker', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    9496615: dict(country='Russia', nationalities=[40], role=17, pos='Centre-Forward', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    9494085: dict(country='Russia', nationalities=[40], role=17, pos='Centre-Forward', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    517: dict(country='Russia', nationalities=[40], role=17, pos='Centre-Forward', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),
    9497351: dict(country='Russia', nationalities=[40], role=17, pos='Centre-Forward', url=TM_SPARTAK, source='Transfermarkt squad 1993-94'),

    # AEK season squad: source gives exact specialist roles for most players.
    9494176: dict(country='Greece', nationalities=[47], role=0, pos='Goalkeeper', url=TM_AEK, source='Transfermarkt squad 1993-94'),
    9497517: dict(country='Greece', nationalities=[47], role=0, pos='Goalkeeper', url=TM_AEK, source='Transfermarkt squad 1993-94'),
    9496921: dict(country='Greece', nationalities=[47], role=0, pos='Goalkeeper', url=TM_AEK, source='Transfermarkt squad 1993-94'),
    9496924: dict(country='Greece', nationalities=[47], role=3, pos='Centre-Back', url=TM_AEK, source='Transfermarkt squad 1993-94'),
    9494160: dict(country='Greece', nationalities=[47], role=3, pos='Centre-Back', url=TM_AEK, source='Transfermarkt squad 1993-94'),
    9496925: dict(country='Greece', nationalities=[47], role=3, pos='Centre-Back', url=TM_AEK, source='Transfermarkt squad 1993-94'),
    9496923: dict(country='Greece', nationalities=[47], role=3, pos='Centre-Back', url=TM_AEK, source='Transfermarkt squad 1993-94'),
    9496926: dict(country='Greece', nationalities=[47], role=2, pos='Left-Back', url=TM_AEK, source='Transfermarkt squad 1993-94'),
    9494169: dict(country='Greece', nationalities=[47], role=2, pos='Left-Back', url=TM_AEK, source='Transfermarkt squad 1993-94'),
    9496931: dict(country='Greece', nationalities=[47], role=1, pos='Right-Back', url=TM_AEK, source='Transfermarkt squad 1993-94'),
    9496922: dict(country='Greece', nationalities=[47], role=1, pos='Right-Back', url=TM_AEK, source='Transfermarkt squad 1993-94'),
    9496928: dict(country='Greece', nationalities=[20,76], role=6, pos='Defensive Midfield', url=TM_AEK, source='Transfermarkt squad 1993-94'),
    9496927: dict(country='Greece', nationalities=[47], role=6, pos='Defensive Midfield', url=TM_AEK, source='Transfermarkt squad 1993-94'),
    9497519: dict(country='Greece', nationalities=[47], role=6, pos='Defensive Midfield', url=TM_AEK, source='Transfermarkt squad 1993-94'),
    9497521: dict(country='Greece', nationalities=[47], role=13, pos='Left Midfield', url=TM_AEK, source='Transfermarkt squad 1993-94'),
    9496929: dict(country='Greece', nationalities=[54,47], role=13, pos='Left Midfield', url=TM_AEK, source='Transfermarkt squad 1993-94'),
    9496930: dict(country='Greece', nationalities=[47], role=8, pos='Attacking Midfield', url=TM_AEK, source='Transfermarkt squad 1993-94'),
    9494166: dict(country='Greece', nationalities=[47], role=8, pos='Attacking Midfield', url=TM_AEK, source='Transfermarkt squad 1993-94'),
    9494177: dict(country='Greece', nationalities=[47], role=17, pos='Centre-Forward', url=TM_AEK, source='Transfermarkt squad 1993-94'),
    9494170: dict(country='Greece', nationalities=[47], role=17, pos='Centre-Forward', url=TM_AEK, source='Transfermarkt squad 1993-94'),
    9496932: dict(country='Greece', nationalities=[31], role=17, pos='Centre-Forward', url=TM_AEK, source='Transfermarkt squad 1993-94'),
    # Source only says Defender for these two, so do not pretend an exact specialist role.
    9497518: dict(country='Greece', nationalities=[47], pos='Defender', precision='broad_only', url=TM_AEK, source='Transfermarkt squad 1993-94'),
    9497522: dict(country='Greece', nationalities=[47], pos='Defender', precision='broad_only', url=TM_AEK, source='Transfermarkt squad 1993-94'),
}

GS_BDF = {
    9495316: dict(id='42823', dob='1963-06-26', birth_country=84, nationalities=[84], pos='Goalkeeper', role=0),
    9495319: dict(id='42821', dob='1968-11-24', birth_country=84, nationalities=[84], pos='Central', role=3, height=180),
    9495337: dict(id='45982', dob='1970-01-15', birth_country=47, nationalities=[84,47], pos='Midfielder'),
    9495336: dict(id='46412', dob='1967-08-26', birth_country=84, nationalities=[84], pos='Midfielder', height=169),
    9495331: dict(id='94203', dob='1970-08-24', birth_country=84, nationalities=[84], pos='Midfielder', height=176, weight=73),
    # BDF only says Midfielder. Map gameplay to neutral centre-midfield, not a fabricated specialist flank role.
    9495327: dict(id='702615', dob='1968-01-15', birth_country=84, nationalities=[84], pos='Midfielder', role=7),
    9495348: dict(id='94413', dob='1971-09-01', birth_country=84, nationalities=[84], pos='Striker', role=17, height=188, weight=77),
    9495354: dict(id='276', dob='1972-01-02', birth_country=84, nationalities=[84], pos='Forward', role=17, height=178, weight=72),
    9495342: dict(id='86306', dob='1963-08-02', birth_country=84, nationalities=[84], pos='Midfielder'),
}
for sid, row in GS_BDF.items():
    PROFILE_PATCH[sid] = dict(country='Turkey', dob=row['dob'], birth_country=row['birth_country'], nationalities=row['nationalities'], pos=row['pos'], role=row.get('role'), height=row.get('height'), weight=row.get('weight'), url=BDF.format(id=row['id']), source='BDFutbol individual profile', bdf_id=row['id'], precision='broad_only' if row['pos'] in {'Midfielder','Forward','Central'} and row.get('role') is None else 'exact_or_gameplay_mapped')

# 1993-94 Alpha Ethniki season table gives club -> historical ground. Physical
# parameters are intentionally null unless separately source-backed for the season.
GREEK_STADIUMS = [
    (9347001,'Nikos Goumas Stadium',432),
    (9347002,'Athens Olympic Stadium',5551),
    (9347003,'Karaiskakis Stadium',None),
    (9347004,'Kleanthis Vikelidis Stadium',1974),
    (9347005,'Toumba Stadium',1974),
    (9347006,'Kaftanzoglio Stadium',1974),
    (9347007,'Theodoros Vardinogiannis Stadium',1976),
    (9347008,'Xanthi Ground',1980),
    (9347009,'Nea Smyrni Stadium',432),
    (9347010,'Alcazar Stadium',1340),
    (9347011,'Levadia Municipal Stadium',1979),
    (9347012,'Vyronas National Stadium',432),
    (9347013,'Rizoupoli Stadium',432),
    (9347014,'Municipal Stadium of Edessa',5560),
    (9347015,'Doxa Drama Stadium',5552),
    (9347016,'Kostas Davourlis Stadium',5133),
    (9347017,'Kalamaria Stadium',4931),
    (9347018,'Municipal Stadium of Naousa',None),
]
GREEK_STADIUM_SOURCE='https://en.wikipedia.org/wiki/1993%E2%80%9394_Alpha_Ethniki'

# Russia 1993 primary home grounds. The season table is used as the club->ground
# roster and Wildstat match records override labels that are clearly modernised
# on the current linked stadium page (Uralmash, Luch and Rostselmash).
RUSSIAN_STADIUMS = [
    (9315001,'Central Profsoyuz Stadion'),
    (9315002,'Dynamo Stadium'),
    (9315003,'Tekstilshchik Stadium'),
    (9315004,'Lokomotiv Stadium'),
    (9315005,'Spartak Republican Stadium'),
    (9315006,'Central Stadium'),
    (9315007,'Grigory Fedotov Stadium'),
    (9315008,'KAMAZ Stadium'),
    (9315009,'Central Stadium'),
    (9315010,'Dynamo Stadium'),
    (9315011,'Lokomotiv Stadium'),
    (9315012,'Metallurg Stadium'),
    (9315013,'Luch Stadium'),
    (9315014,'Vodnik Stadium'),
    (9315015,'Rostselmash Stadium'),
    (9315016,'Krasnaya Presnya Stadium'),
]
RUSSIAN_STADIUM_SOURCE='https://en.wikipedia.org/wiki/1993_Russian_Top_League'
RUSSIAN_MATCH_SOURCE='https://wildstat.com/p/1/ch/RUS_1_1993'

BELGIUM_REFS = [
    ('Frans Van Den Wyngaert',19,78,3,1,6),('Michel Piraux',19,67,9,2,4),('Marnix Sandra',18,37,2,1,3),
    ('Eric Blareau',18,49,0,2,2),('Marcel Van Elshocht',18,40,5,1,1),('Léon Schelings',17,45,0,2,2),
    ('Marcel Javaux',17,44,1,0,1),('Amand Ancion',17,48,0,8,5),('Willy Van Driessche',17,41,1,2,3),
    ('Eric Romain',17,42,1,3,5),('Robert Jeurissen',16,29,0,3,3),('Luc Lippens',15,48,3,3,0),
    ('Fernand Meese',14,32,1,1,6),('Guido Adriaensen',13,55,2,3,2),('Guy Goethals',10,26,1,0,2),
    ('Pieter Vandevenne',8,21,1,2,1),('Jozef Hus',8,15,1,1,1),('Luc Huyghe',8,16,0,0,1),
    ('Johny Ver Eecke',7,18,0,1,2),('Ghislain Hayen',7,18,0,2,2),('Rudi Lepoutre',7,19,0,4,1),
    ('Erik Clerkx',7,23,0,2,1),('Jacky Quaranta',7,27,1,1,1),('Andre Collignon',1,4,0,0,0),('Geert Mortier',1,1,0,0,0),
]
BELGIUM_REF_SOURCE='https://www.transfermarkt.com/jupiler-pro-league/schiedsrichter/pokalwettbewerb/BE1/saison_id/1993/plus/0'
GREECE_REFS=[('Sotiris Mbazas',10),('Kostas Karapatas',10),('Kefalas',9),('Mbikas',9),('Charlavanis',9),('Symiakos',9),('Spathas',9),('Mazarakis',9),('Naziris',9),('Dimitris Iliadis',9),('Mborovilos',9)]
GREECE_REF_SOURCE='https://www.rsssf.org/tablesg/grk94.html'


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))

def dump(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def role_ratings(role: int) -> dict[str,int]:
    o={str(i):0 for i in range(18)};o[str(role)]=100
    adj={
      0:{},1:{3:60,9:55},2:{4:60,13:55},3:{4:75,5:60,6:45},4:{3:75,5:60,6:45},5:{3:75,4:75,6:60},
      6:{7:75,3:50,4:50},7:{6:70,8:65,9:45,13:45},8:{7:65,11:55,15:55,17:45},9:{12:75,7:55,8:50,1:45},
      10:{9:80,12:65,7:55},11:{12:80,9:65,8:65,17:50},12:{9:75,11:65,17:50},13:{16:75,7:55,8:50,2:45},
      14:{13:80,16:65,7:55},15:{16:80,13:65,8:65,17:50},16:{13:75,15:65,17:50},17:{11:45,15:45,12:35,16:35,8:30},
    }
    for k,v in adj[role].items():o[str(k)]=v
    return o

def comparable(originals:list[dict[str,Any]], broad:str, ov:int, sid:int) -> tuple[dict[str,Any],dict[str,Any]]:
    pool=[p for p in originals if p.get('broad_position')==broad and p.get('attributes')]
    pool.sort(key=lambda p:(abs(int(p.get('overall') or 0)-ov),int(p.get('source_id') or 0)));pool=pool[:48]
    if len(pool)<2: raise RuntimeError(f'not enough comparables for {broad}')
    a=pool[(sid*7)%len(pool)];b=pool[(sid*13+5)%len(pool)]
    if a['source_id']==b['source_id']:b=pool[(pool.index(a)+1)%len(pool)]
    return a,b

def stage_rows(stages:dict[str,dict[str,Any]]) -> dict[int,list[dict[str,Any]]]:
    out:dict[int,list[dict[str,Any]]]={}
    for stage in stages.values():
        for club in stage.get('clubs',[]):
            for row in club.get('players',[]):
                if row.get('resolved_source_id') is not None:
                    out.setdefault(int(row['resolved_source_id']),[]).append(row)
    return out

def apply_profiles(snapshot:dict[str,Any], stages:dict[str,dict[str,Any]], registry:dict[str,Any], queue:dict[str,Any]) -> list[dict[str,Any]]:
    players=snapshot['players'];by={int(p['source_id']):p for p in players}
    originals=[p for p in players if not p.get('external_origin') and not p.get('creation_batch')]
    srows=stage_rows(stages)
    regby={int(r['source_id']):r for r in registry.get('players',[]) if r.get('source_id') is not None}
    qby={int(r['source_id']):r for r in queue.get('players',[]) if r.get('source_id') is not None}
    changes=[]
    for sid,patch in PROFILE_PATCH.items():
        p=by.get(sid)
        if p is None:
            raise RuntimeError(f'profile target missing {sid}')
        before_role=int(p.get('primary_role') or 0);before_pos=p.get('historical_position_1993_94');before_birth=p.get('birth_date')
        if patch.get('dob'): p['birth_date']=patch['dob']+'T00:00:00'
        if patch.get('birth_country') is not None: p['birth_country_id']=int(patch['birth_country'])
        nats=[int(x) for x in patch.get('nationalities',[]) if x is not None]
        if nats:
            p['international_country_id']=nats[0]
            p['profile_nationality_country_ids']=nats
            if len(nats)>1:p['secondary_nationality_country_id']=nats[1]
        if patch.get('height') is not None:p['height_cm']=int(patch['height'])
        if patch.get('weight') is not None:p['weight_kg']=int(patch['weight'])
        p['source_profile_position']=patch['pos']
        p['profile_position_precision']=patch.get('precision','exact')
        p['historical_profile_source']=patch['source']+' v0.31'
        p['historical_profile_source_url']=patch['url']
        p['profile_review_required']=patch.get('precision')=='broad_only'
        role=patch.get('role')
        if role is not None:
            role=int(role);p['role_ratings']=role_ratings(role)
            p['primary_role']=role;p['broad_position']=ROLE_TO_BROAD[role];p['historical_position_1993_94']=ROLE_TO_LABEL[role]
            p['historical_position_source']=patch['source']+' v0.31'
            if role!=before_role:
                a,b=comparable(originals,ROLE_TO_BROAD[role],int(p.get('overall') or 70),sid)
                p['attributes']=materialise_attributes(int(p.get('overall') or 70),a,b)
                p['attribute_source']='fixed_source_comparable_role_correction_0.31'
                p['attribute_comparable_source_ids']=[int(a['source_id']),int(b['source_id'])]
        if patch.get('bdf_id'):
            p['bdfutbol_id']=str(patch['bdf_id']);p['bdfutbol_url']=patch['url']
        for row in srows.get(sid,[]):
            row['resolved_display_name']=p['display_name']
            row['resolved_primary_role']=int(p.get('primary_role') or 0)
            row['resolved_exact_position']=p.get('historical_position_1993_94')
            row['resolved_birth_date']=p.get('birth_date')
            row['resolved_country_id']=p.get('international_country_id') or p.get('birth_country_id')
            row['profile_source_url']=patch['url']
            row['profile_source']=patch['source']+' v0.31'
            row['source_profile_position']=patch['pos']
            row['position_source']='season_specific_profile_v0.31' if role is not None else row.get('position_source')
            if patch.get('bdf_id'):
                row['individual_profile_source_url']=patch['url'];row['bdfutbol_id']=str(patch['bdf_id'])
        for target in (regby.get(sid),qby.get(sid)):
            if target is None: continue
            target.update({
                'display_name':p['display_name'],'birth_date':(p.get('birth_date') or '')[:10] or None,
                'country_id':p.get('international_country_id') or p.get('birth_country_id'),
                'country_name':COUNTRY_NAME.get(int(p.get('international_country_id') or p.get('birth_country_id') or 0)),
                'broad_position':p.get('broad_position'),'historical_position_1993_94':p.get('historical_position_1993_94'),
                'profile_review_required':bool(p.get('profile_review_required')),
            })
            if patch.get('bdf_id'):
                target.update({'bdfutbol_search_name':p['display_name'],'bdfutbol_id':str(patch['bdf_id']),'bdfutbol_url':patch['url'],'photo_filename':f'{sid}.jpg','photo_status':'bundled_normalized_bdfutbol' if (PHOTO_DIR/f'{sid}.jpg').exists() else 'ready_for_download','individual_profile_source':'BDFutbol individual profile v0.31'})
        changes.append({'source_id':sid,'display_name':p['display_name'],'country':patch['country'],'role_before':before_role,'role_after':int(p.get('primary_role') or 0),'position_before':before_pos,'position_after':p.get('historical_position_1993_94'),'source_position':patch['pos'],'birth_before':before_birth,'birth_after':p.get('birth_date'),'nationalities':nats,'profile_source_url':patch['url'],'photo_source_ready':bool(patch.get('bdf_id'))})
    return changes

def sync_bundled_photo_status(registry:dict[str,Any], queue:dict[str,Any]) -> int:
    bundled=0
    for collection in (registry.get('players',[]), queue.get('players',[])):
        for row in collection:
            sid=row.get('source_id')
            if sid is None: continue
            asset=PHOTO_DIR/f'{int(sid)}.jpg'
            if asset.exists():
                row['photo_filename']=asset.name
                row['photo_status']='bundled_normalized_bdfutbol'
                row['photo_width']=40; row['photo_height']=55; row['photo_format']='JPEG'; row['photo_mode']='RGB'
                if row.get('bdfutbol_id'):
                    row['photo_source']='BDFutbol individual profile v0.31'
                if collection is registry.get('players',[]): bundled+=1
    return bundled


def clean_colliding_rosters(snapshot:dict[str,Any], stages:dict[str,dict[str,Any]], registry:dict[str,Any], queue:dict[str,Any]) -> list[dict[str,Any]]:
    team_by_league={country:{int(t['source_id']) for t in snapshot['teams'] if t.get('league_id')==lid} for country,lid in LEAGUES.items()}
    allowed={country:{int(row['resolved_source_id']) for club in stage.get('clubs',[]) for row in club.get('players',[]) if row.get('resolved_source_id') is not None} for country,stage in stages.items()}
    removed=[];remove_ids=set()
    for p in snapshot['players']:
        tid=p.get('team_id')
        for country,team_ids in team_by_league.items():
            if tid in team_ids and int(p['source_id']) not in allowed[country]:
                removed.append({'source_id':int(p['source_id']),'display_name':p.get('display_name'),'team_id':tid,'country':country,'reason':'legacy_mdb_club_id_collision_not_in_verified_1993_94_staging'})
                remove_ids.add(int(p['source_id']))
                break
    snapshot['players']=[p for p in snapshot['players'] if int(p['source_id']) not in remove_ids]
    # Should normally be base-MDB rows. Defensive cleanup prevents orphaned photo-registry entries.
    registry['players']=[r for r in registry.get('players',[]) if int(r.get('source_id') or -1) not in remove_ids]
    queue['players']=[r for r in queue.get('players',[]) if int(r.get('source_id') or -1) not in remove_ids]
    return removed

def add_greek_stadiums(snapshot:dict[str,Any], catalog:dict[str,Any]) -> list[dict[str,Any]]:
    teams={int(t['source_id']):t for t in snapshot['teams']}
    existing_ids={int(x['source_id']) for x in catalog['stadiums']}
    next_id=max(existing_ids)+1
    # Idempotence by source marker + team binding.
    prior={int(x.get('historical_team_id')):x for x in catalog['stadiums'] if x.get('source_label')=='1993-94 Alpha Ethniki — Stadiums and personnel' and x.get('historical_team_id') is not None}
    added=[]
    for team_id,name,city_id in GREEK_STADIUMS:
        row=prior.get(team_id)
        if row is None:
            row={
                'source_id':next_id,'name':name,'short_name':name,'without_article':False,
                'width_m':None,'length_m':None,'capacity':None,'city_id':city_id,'stars':None,'grass_quality':None,
                'temporal_confidence':'season_specific_historical_source','historical_season':'1993-94','historical_team_id':team_id,
                'source_url':GREEK_STADIUM_SOURCE,'source_label':'1993-94 Alpha Ethniki — Stadiums and personnel',
                'physical_parameters_status':'not_inferred_from_modern_values',
            }
            catalog['stadiums'].append(row);next_id+=1
        team=teams[team_id];team['stadium_id']=int(row['source_id']);team['venue_source_status']='historical_source_backed_1993_94';team['venue_source_url']=GREEK_STADIUM_SOURCE;team['venue_source_label']='1993-94 Alpha Ethniki — Stadiums and personnel'
        added.append({'team_id':team_id,'team_name':team['name'],'stadium_id':int(row['source_id']),'stadium_name':name,'city_id':city_id})
    catalog['counts']['stadiums']=len(catalog['stadiums'])
    return added

def add_russian_stadiums(snapshot:dict[str,Any], catalog:dict[str,Any]) -> list[dict[str,Any]]:
    teams={int(t['source_id']):t for t in snapshot['teams']}
    next_id=max(int(x['source_id']) for x in catalog['stadiums'])+1
    label='Russia 1993 Top League — season venues cross-checked against 1993 match records'
    prior={int(x.get('historical_team_id')):x for x in catalog['stadiums'] if x.get('source_label')==label and x.get('historical_team_id') is not None}
    added=[]
    for team_id,name in RUSSIAN_STADIUMS:
        row=prior.get(team_id)
        if row is None:
            row={
                'source_id':next_id,'name':name,'short_name':name,'without_article':False,
                'width_m':None,'length_m':None,'capacity':None,'city_id':None,'stars':None,'grass_quality':None,
                'temporal_confidence':'season_specific_historical_source','historical_season':'1993','historical_team_id':team_id,
                'source_url':RUSSIAN_STADIUM_SOURCE,'source_label':label,
                'crosscheck_url':RUSSIAN_MATCH_SOURCE,'physical_parameters_status':'not_inferred_from_modern_values',
            }
            catalog['stadiums'].append(row);next_id+=1
        team=teams[team_id];team['stadium_id']=int(row['source_id']);team['venue_source_status']='historical_source_backed_1993';team['venue_source_url']=RUSSIAN_STADIUM_SOURCE;team['venue_source_crosscheck_url']=RUSSIAN_MATCH_SOURCE;team['venue_source_label']=label
        added.append({'team_id':team_id,'team_name':team['name'],'stadium_id':int(row['source_id']),'stadium_name':name})
    catalog['counts']['stadiums']=len(catalog['stadiums'])
    return added


def split_name(name:str) -> tuple[str|None,str|None]:
    parts=name.split()
    if len(parts)<=1:return (None,name)
    return (' '.join(parts[:-1]),parts[-1])

def add_referees(snapshot:dict[str,Any], catalog:dict[str,Any]) -> dict[str,Any]:
    leagues={int(l['source_id']):l for l in snapshot['leagues']}
    refs=catalog['referees'];next_id=max(int(r['source_id']) for r in refs)+1
    existing={(r.get('league_id'),str(r.get('display_name') or '').casefold()) for r in refs}
    bel_added=[]
    for name,apps,y,sy,red,pens in BELGIUM_REFS:
        if (930052,name.casefold()) in existing: continue
        first,surname=split_name(name)
        refs.append({'source_id':next_id,'display_name':name,'first_name':first,'surname1':surname,'surname2':None,'birth_city_id':None,'birth_country_id':None,'nationality_country_id':17,'birth_date':None,'backup_birth_date':None,'birth_date_conflict':False,'yellow_tendency':round(y/apps,3),'red_tendency':round((sy+red)/apps,3),'quality':None,'association':'Belgium','profession':None,'league_id':930052,'historical_season':'1993-94','appearances':apps,'yellow_count':y,'second_yellow_count':sy,'red_count':red,'penalties_awarded':pens,'temporal_confidence':'season_specific_historical_source','source_url':BELGIUM_REF_SOURCE,'source_label':'Transfermarkt Jupiler Pro League 93/94 referees'});bel_added.append(next_id);existing.add((930052,name.casefold()));next_id+=1
    gre_added=[]
    for name,apps in GREECE_REFS:
        if (930047,name.casefold()) in existing: continue
        first,surname=split_name(name)
        refs.append({'source_id':next_id,'display_name':name,'first_name':first,'surname1':surname,'surname2':None,'birth_city_id':None,'birth_country_id':None,'nationality_country_id':47,'birth_date':None,'backup_birth_date':None,'birth_date_conflict':False,'yellow_tendency':None,'red_tendency':None,'quality':None,'association':'Greece','profession':None,'league_id':930047,'historical_season':'1993-94','appearances':apps,'temporal_confidence':'season_specific_historical_source_subset','source_url':GREECE_REF_SOURCE,'source_label':'RSSSF Greece 1993/94 referees — published top subset'});gre_added.append(next_id);existing.add((930047,name.casefold()));next_id+=1
    # Existing v0.31 rows from an earlier run are normalized too: association/nationality is not birthplace.
    for r in refs:
        if r.get('source_url')==BELGIUM_REF_SOURCE and r.get('league_id')==930052:
            r['birth_country_id']=None; r['nationality_country_id']=17
        elif r.get('source_url')==GREECE_REF_SOURCE and r.get('league_id')==930047:
            r['birth_country_id']=None; r['nationality_country_id']=47
    catalog['counts']['referees']=len(refs)
    leagues[930052]['source_rule_hints'].update({'referee_pool_status':'historical_source_backed_complete_1993_94','referee_pool_source':BELGIUM_REF_SOURCE,'referee_pool_size':25})
    leagues[930047]['source_rule_hints'].update({'referee_pool_status':'historical_source_backed_subset_1993_94','referee_pool_source':GREECE_REF_SOURCE,'referee_pool_reported_total':45,'referee_pool_encoded':11,'referee_pool_completeness_note':'RSSSF reports 45 referees in 304 matches but publishes the top 11 by appearances; no unlisted names are invented.'})
    return {'Belgium':{'added':len(bel_added),'pool_size':25,'source':BELGIUM_REF_SOURCE,'coverage':'complete page list'},'Greece':{'added':len(gre_added),'pool_size':11,'reported_total':45,'source':GREECE_REF_SOURCE,'coverage':'published top subset only'}}

def profile_gap_stats(snapshot:dict[str,Any]) -> dict[str,Any]:
    out={}
    for country,lid in LEAGUES.items():
        tids={int(t['source_id']) for t in snapshot['teams'] if t.get('league_id')==lid}
        ps=[p for p in snapshot['players'] if p.get('team_id') in tids]
        out[country]={
            'active_players':len(ps),
            'missing_birth_date':sum(not p.get('birth_date') for p in ps),
            'missing_international_country_id':sum(p.get('international_country_id') is None for p in ps),
            'missing_birth_country_id':sum(p.get('birth_country_id') is None for p in ps),
            'missing_height_cm':sum(p.get('height_cm') is None for p in ps),
            'missing_weight_kg':sum(p.get('weight_kg') is None for p in ps),
            'profile_review_required':sum(bool(p.get('profile_review_required')) for p in ps),
        }
    return out

def main() -> None:
    prior_audit=load(DATA/'historical_profiles_metadata_audit_v031.json') if (DATA/'historical_profiles_metadata_audit_v031.json').exists() else None
    snapshot=load(SNAP);catalog=load(CATALOG);registry=load(REGISTRY);queue=load(QUEUE);stages={k:load(v) for k,v in STAGES.items()}
    before=profile_gap_stats(snapshot)
    contamination=clean_colliding_rosters(snapshot,stages,registry,queue)
    changes=apply_profiles(snapshot,stages,registry,queue)
    bundled_photo_count=sync_bundled_photo_status(registry,queue)
    greek_stadia=add_greek_stadiums(snapshot,catalog)
    russian_stadia=add_russian_stadiums(snapshot,catalog)
    stadia=greek_stadia+russian_stadia
    refs=add_referees(snapshot,catalog)
    after=profile_gap_stats(snapshot)
    unresolved_venues=[int(t['source_id']) for t in snapshot['teams'] if isinstance(t.get('league_id'),int) and t.get('venue_source_status')=='unresolved_historical_1993_94']
    unresolved_refs=[lid for lid in LEAGUES.values() if not any(r.get('league_id')==lid for r in catalog['referees'])]
    # Keep regenerated registry/queue one-to-one and stable.
    reg_ids={int(r['source_id']) for r in registry.get('players',[])}; q_ids={int(r['source_id']) for r in queue.get('players',[])}
    if reg_ids != q_ids: raise RuntimeError(f'registry/queue mismatch: {len(reg_ids)} vs {len(q_ids)}')
    # Guard the exact contamination total discovered before mutation.
    by_country=Counter(r['country'] for r in contamination)
    expected={'Belgium':60,'Turkey':47,'Russia':35}
    if contamination and (dict(by_country)!=expected or len(contamination)!=142):
        raise RuntimeError(f'unexpected collision cleanup {dict(by_country)} total={len(contamination)}')
    hygiene=(prior_audit or {}).get('roster_hygiene') if not contamination else None
    if not hygiene:
        hygiene={'removed_assignments':len(contamination),'by_country':dict(by_country),'rows':contamination,'policy':'Only active-team identities absent from the verified 1993-94 staging union are removed; multi-club season rows sharing one verified identity remain valid.'}
    role_corrections=sum(c['role_before']!=c['role_after'] for c in changes)
    if role_corrections==0 and prior_audit:
        role_corrections=int(prior_audit.get('profiles',{}).get('role_corrections') or 0)
    initial_gaps=(prior_audit or {}).get('profile_gaps_before') or before
    audit={
        'schema_version':1,'checkpoint':'0.31.0-profiles-venues-referees-roster-hygiene','status':'pass',
        'roster_hygiene':hygiene,
        'profiles':{'curated':len(changes),'role_corrections':role_corrections,'photo_profiles_source_linked':sum(c['photo_source_ready'] for c in changes),'by_country':dict(Counter(c['country'] for c in changes)),'changes':changes},
        'profile_gaps_before':initial_gaps,'profile_gaps_after':after,
        'stadiums':{'greece_source_backed':len(greek_stadia),'russia_source_backed':len(russian_stadia),'rows':stadia,'unresolved_team_ids':unresolved_venues,'unresolved_count':len(unresolved_venues),'physical_parameters_policy':'No modern capacity/dimension is copied into a 1993-94 historical stadium row without a season-specific source.'},
        'referees':refs,'unresolved_referee_pool_league_ids':unresolved_refs,
        'photo_registry':{'registry_rows':len(registry['players']),'queue_rows':len(queue['players']),'registry_queue_match':True,'bundled_normalized_assets':bundled_photo_count},
    }
    gaps={'schema_version':1,'checkpoint':'0.31.0-profiles-venues-referees-roster-hygiene','status':'pass','profile_gaps':after,'unresolved_historical_venue_team_ids':unresolved_venues,'unresolved_historical_referee_pool_league_ids':unresolved_refs,'partially_resolved_referee_pools':{'930047':'RSSSF publishes 11 named leaders out of 45 referees; encoded as an explicit historical subset.'},'policy':'Known gaps remain explicit and source-gated; no biographical, stadium or referee fact is invented merely to satisfy coverage.'}
    dump(SNAP,snapshot);dump(CATALOG,catalog);dump(REGISTRY,registry);dump(QUEUE,queue)
    for country,path in STAGES.items():dump(path,stages[country])
    dump(DATA/'historical_profiles_metadata_audit_v031.json',audit);dump(DATA/'historical_metadata_gaps_v031.json',gaps)
    print(json.dumps({'status':'pass','contamination_removed':int(hygiene.get('removed_assignments') or 0),'profiles_curated':len(changes),'role_corrections':audit['profiles']['role_corrections'],'greek_stadiums':len(greek_stadia),'russian_stadiums':len(russian_stadia),'referee_pools':refs,'unresolved_venues':len(unresolved_venues),'unresolved_referee_leagues':unresolved_refs,'profile_gaps_after':after},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
