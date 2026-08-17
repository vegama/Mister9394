from __future__ import annotations
import json, sys
from pathlib import Path
from datetime import datetime
from typing import Any

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'backend'))
from app.football9394.identity_reconciliation import clean_text
from app.football9394.mdb_jet4 import Jet4MDB

DATA=ROOT/'data'/'football9394'
SNAP=DATA/'historical_snapshot.json'
STAGE=DATA/'belgium_1993_94_roster_staging.json'
MDB=Path('/mnt/data/m9394_source/basedatos(1).mdb')
REPORT=DATA/'belgium_1993_94_identity_reconciliation.json'

def norm_variants_snapshot(p:dict[str,Any])->set[str]:
    vals=[]
    for k in ('display_name','first_name','surname1','surname2'):
        if p.get(k): vals.append(str(p[k]))
    combos=[p.get('display_name'),p.get('surname1'),p.get('surname2'),f"{p.get('first_name') or ''} {p.get('surname1') or ''}",f"{p.get('surname1') or ''} {p.get('surname2') or ''}"]
    return {clean_text(x) for x in combos if clean_text(x)}

def norm_variants_mdb(p:dict[str,Any])->set[str]:
    combos=[p.get('Apodo'),p.get('NombreFamiliar'),p.get('Mote'),p.get('Apellido1'),p.get('Apellido2'),
            f"{p.get('Nombre') or ''} {p.get('Apellido1') or ''}",f"{p.get('Nombre') or ''} {p.get('Apellido1') or ''} {p.get('Apellido2') or ''}"]
    return {clean_text(x) for x in combos if clean_text(x)}

def birth_year(v:Any)->int|None:
    if isinstance(v,datetime): return v.year
    s=str(v or '')[:4]
    try:return int(s)
    except:return None

def age_compatible(age:int|None, y:int|None)->bool:
    if age is None or y is None:return False
    # BDF's displayed age may be measured on a date inside the season.
    return y in {1993-age,1994-age,1992-age}

def hist_club_match(p:dict[str,Any], club:str)->bool:
    a=clean_text(p.get('historical_club_1994'))
    b=clean_text(club)
    if not a:return False
    return b in a or a in b or any(tok in a for tok in b.split() if len(tok)>4)

def main():
    snap=json.load(open(SNAP,encoding='utf-8'))
    stage=json.load(open(STAGE,encoding='utf-8'))
    splayers=snap['players']
    mdb=Jet4MDB(MDB)
    mplayers=mdb.rows('Jugador')
    steams={int(t['source_id']):t for t in snap['teams']}
    mteams={int(t['Id']):t for t in mdb.rows('Equipo') if t.get('Id')}

    # Index exact normalized variants to avoid millions of comparisons.
    sidx={}
    for p in splayers:
        for v in norm_variants_snapshot(p): sidx.setdefault(v,[]).append(p)
    midx={}
    for p in mplayers:
        for v in norm_variants_mdb(p): midx.setdefault(v,[]).append(p)

    summary={'staged_players':0,'snapshot_unique':0,'snapshot_ambiguous':0,'mdb_unique':0,'mdb_ambiguous':0,'unresolved':0,'duplicate_traps':[],'clubs':{}}
    for club in stage['clubs']:
        cname=club['name']; tid=int(club['team_id'])
        cs={'players':len(club['players']),'snapshot_unique':0,'mdb_unique':0,'unresolved':0,'ambiguous':0}
        for row in club['players']:
            summary['staged_players']+=1
            key=clean_text(row['bdfutbol_name'])
            age=int(row['age_1993_94']) if row.get('age_1993_94') is not None else None
            scands=[]
            for p in sidx.get(key,[]):
                y=birth_year(p.get('birth_date'))
                same_team=int(p.get('team_id') or 0)==tid
                hist=hist_club_match(p,cname)
                ageok=age_compatible(age,y)
                score=(60 if key==clean_text(p.get('surname1')) else 0)+(50 if key==clean_text(p.get('display_name')) else 0)+(35 if ageok else 0)+(45 if same_team else 0)+(45 if hist else 0)
                # A surname-only match must have age/team/historical club support.
                if score>=80 or (same_team and score>=60) or (hist and score>=60):
                    scands.append((score,p,ageok,same_team,hist))
            scands.sort(key=lambda x:x[0],reverse=True)
            # De-duplicate same source id if index hit through multiple variants.
            uniq=[];seen=set()
            for x in scands:
                pid=int(x[1].get('source_id') or 0)
                if pid not in seen:uniq.append(x);seen.add(pid)
            scands=uniq
            row['snapshot_candidates']=[{'source_id':int(x[1]['source_id']),'display_name':x[1]['display_name'],'birth_date':x[1].get('birth_date'),'team_id':x[1].get('team_id'),'team_name':steams.get(int(x[1].get('team_id') or 0),{}).get('name'),'historical_club_1994':x[1].get('historical_club_1994'),'overall':x[1].get('overall'),'broad_position':x[1].get('broad_position'),'score':x[0]} for x in scands[:5]]
            if len(scands)==1 or (len(scands)>1 and scands[0][0]-scands[1][0]>=35):
                p=scands[0][1]
                row['identity_resolution']='reused_snapshot'
                row['resolved_source_id']=int(p['source_id'])
                row['resolved_display_name']=p['display_name']
                row['resolved_broad_position']=p.get('broad_position')
                row['resolved_overall']=p.get('overall')
                cs['snapshot_unique']+=1;summary['snapshot_unique']+=1
                continue
            if scands:
                row['identity_resolution']='ambiguous_snapshot'
                cs['ambiguous']+=1;summary['snapshot_ambiguous']+=1
                summary['duplicate_traps'].append({'club':cname,'name':row['bdfutbol_name'],'age':age,'snapshot_candidates':row['snapshot_candidates']})
                continue

            mcands=[]
            for p in midx.get(key,[]):
                y=birth_year(p.get('FechaNacimiento'))
                ageok=age_compatible(age,y)
                same_team=int(p.get('CodEquipo') or 0)==tid
                exact_apodo=key==clean_text(p.get('Apodo')) or key==clean_text(p.get('NombreFamiliar'))
                exact_surname=key==clean_text(p.get('Apellido1')) or key==clean_text(p.get('Apellido2'))
                score=(55 if exact_apodo else 0)+(45 if exact_surname else 0)+(40 if ageok else 0)+(45 if same_team else 0)
                if score>=85 or (same_team and score>=60):
                    mcands.append((score,p,ageok,same_team))
            mcands.sort(key=lambda x:x[0],reverse=True)
            uniq=[];seen=set()
            for x in mcands:
                pid=int(x[1].get('Id') or 0)
                if pid not in seen:uniq.append(x);seen.add(pid)
            mcands=uniq
            row['mdb_candidates']=[{'mdb_id':int(x[1]['Id']),'display_name':' '.join(str(x[1].get(k) or '') for k in ('Nombre','Apellido1','Apellido2')).strip(),'apodo':x[1].get('Apodo'),'birth_date':x[1].get('FechaNacimiento').isoformat() if isinstance(x[1].get('FechaNacimiento'),datetime) else str(x[1].get('FechaNacimiento') or ''),'team_id':x[1].get('CodEquipo'),'team_name':mteams.get(int(x[1].get('CodEquipo') or 0),{}).get('Nombre'),'primary_role':x[1].get('RolPrincipal'),'overall':x[1].get('Media_forzada'),'category':x[1].get('Categoria'),'score':x[0]} for x in mcands[:5]]
            if len(mcands)==1 or (len(mcands)>1 and mcands[0][0]-mcands[1][0]>=35):
                p=mcands[0][1]
                row['identity_resolution']='reused_full_mdb_identity'
                row['resolved_mdb_id']=int(p['Id'])
                row['resolved_display_name']=' '.join(str(p.get(k) or '') for k in ('Nombre','Apellido1','Apellido2')).strip()
                row['resolved_primary_role']=p.get('RolPrincipal')
                row['resolved_overall']=p.get('Media_forzada')
                cs['mdb_unique']+=1;summary['mdb_unique']+=1
            elif mcands:
                row['identity_resolution']='ambiguous_full_mdb'
                cs['ambiguous']+=1;summary['mdb_ambiguous']+=1
                summary['duplicate_traps'].append({'club':cname,'name':row['bdfutbol_name'],'age':age,'mdb_candidates':row['mdb_candidates']})
            else:
                row['identity_resolution']='unresolved_requires_bdf_profile'
                cs['unresolved']+=1;summary['unresolved']+=1
        summary['clubs'][cname]=cs
    json.dump(stage,open(STAGE,'w',encoding='utf-8'),ensure_ascii=False,indent=2,default=str)
    json.dump(summary,open(REPORT,'w',encoding='utf-8'),ensure_ascii=False,indent=2,default=str)
    print(json.dumps(summary,ensure_ascii=False,indent=2)[:12000])

if __name__=='__main__':main()
