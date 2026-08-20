from fastapi.testclient import TestClient
from backend.app.football9394.webapp import app

client = TestClient(app)


def teardown_module():
    """Close the shared TestClient so the RC pytest process exits cleanly."""
    client.close()


def test_football_api_is_separate_and_exposes_1993_94_laws():
    response=client.get('/api/football9394/health')
    assert response.status_code == 200
    data=response.json()
    assert data['season']=='1993-94'
    assert data['max_used_substitutes']==2
    assert data['domain']=='football-native'


def test_unknown_competition_never_receives_generic_rules():
    response=client.get('/api/football9394/rules/Recopa')
    assert response.status_code == 409
    assert 'fallback genérico' in response.json()['detail']


def test_match_endpoint_returns_football_stats_and_respects_substitution_cap():
    response=client.post('/api/football9394/matches/simulate',json={'seed':42})
    assert response.status_code == 200
    data=response.json()
    assert data['home']['substitutions'] <= 2
    assert data['away']['substitutions'] <= 2
    assert data['home']['possession'] + data['away']['possession'] == 100
    assert data['played_minutes'] >= 91


def test_competition_audit_has_no_career_limbo_rows():
    response=client.get('/api/football9394/rule-audit')
    assert response.status_code == 200
    data=response.json()
    # Sube al incorporar las seis ligas del 93-94 -Divizia A, Ekstraklasa,
    # A Grupa, Allsvenskan, Tippeligaen y Superligaen- con sus clubes reales.
    # Solo se activan los que pueden alinear once y tienen estadio en la
    # fuente; el resto queda apuntado en pending_activation.
    assert data['total'] == 38
    # Sube con las seis ligas del 93-94 incorporadas.
    assert data['active'] == 36
    assert data['excluded'] == 2
    assert data['non_admitted'] == 2
    assert data['unresolved'] == 0
    assert data['all_source_rows_closed'] is True
    # Default endpoint follows the original MDB's admitted selector.
    active=client.get('/api/football9394/competitions').json()
    # Seis competiciones mas: las ligas del 93-94 incorporadas.
    assert len(active) == 36
    assert all(row['active'] for row in active)


def test_world_season_endpoint_uses_persistent_world_payload_contract(monkeypatch):
    import backend.app.football9394.webapp as webapp
    monkeypatch.setattr(webapp, 'simulate_world_season_1993_94', lambda seed: {
        'schema': 1, 'career_id': 'test-career', 'season': '1993-94', 'seed': seed,
        'status': 'complete', 'competition_count': 26, 'all_competitions_complete': True,
    })
    response=client.post('/api/football9394/world/seasons/simulate',json={'seed':77})
    assert response.status_code == 200
    data=response.json()
    assert data['career_id']=='test-career'
    assert data['seed']==77
    assert data['competition_count']==26


def test_manager_career_api_persists_day_and_matchday(monkeypatch, tmp_path):
    import backend.app.football9394.webapp as webapp
    monkeypatch.setattr(webapp, 'CAREER_SAVE_ROOT', tmp_path)
    created = client.post('/api/football9394/careers', json={'team_id':16,'seed':202,'through_matchday':7})
    assert created.status_code == 200
    state = created.json()
    career_id = state['career_id']
    assert state['game_date'] == '1993-10-23'
    assert state['completed_matchday'] == 7
    assert state['result_count'] == 70

    advanced = client.post(f'/api/football9394/careers/{career_id}/advance')
    assert advanced.status_code == 200
    assert advanced.json()['date'] == '1993-10-24'
    assert advanced.json()['requires_match'] is True

    played = client.post(f'/api/football9394/careers/{career_id}/play-next')
    assert played.status_code == 200
    assert played.json()['completed_matchday'] == 8
    assert played.json()['result_count'] == 80

    restored = client.get(f'/api/football9394/careers/{career_id}')
    assert restored.status_code == 200
    assert restored.json()['completed_matchday'] == 8


def test_manager_career_api_persists_tactical_choices(monkeypatch, tmp_path):
    import backend.app.football9394.webapp as webapp
    monkeypatch.setattr(webapp, 'CAREER_SAVE_ROOT', tmp_path)
    career_id = client.post('/api/football9394/careers', json={'team_id':16}).json()['career_id']
    updated = client.put(f'/api/football9394/careers/{career_id}/tactics', json={
        'formation':'4-3-3','mentality':'attacking','tempo':'high','pressing':'high',
        'directness':'mixed','defensive_line':'medium','width':'normal','offside_trap':False,'marking':'zonal'
    })
    assert updated.status_code == 200
    assert updated.json()['career']['tactics']['formation'] == '4-3-3'
    assert client.get(f'/api/football9394/careers/{career_id}').json()['tactics']['pressing'] == 'high'


def test_national_teams_api_is_source_backed():
    rows = client.get('/api/football9394/national-teams')
    assert rows.status_code == 200
    assert any(row['name'] == 'España' for row in rows.json())
    spain = client.get('/api/football9394/national-teams/11')
    assert spain.status_code == 200
    data = spain.json()
    assert data['source_backed'] is True
    assert len(data['squad']) == 22


def test_career_transfer_changes_squad_and_cash(monkeypatch, tmp_path):
    import backend.app.football9394.webapp as webapp
    monkeypatch.setattr(webapp, 'CAREER_SAVE_ROOT', tmp_path)
    created = client.post('/api/football9394/careers', json={'team_id':16,'seed':303,'through_matchday':0}).json()
    cid = created['career_id']
    market = client.get(f'/api/football9394/careers/{cid}/market?limit=60').json()
    assert market
    # El club es español y el cupo de extranjeros de Primera 1993-94 es de
    # cuatro: hay que elegir a alguien inscribible o el traspaso se rechaza por
    # regla y este test dejaría de medir el traspaso en sí.
    target = next(row for row in market if (row.get('market') or {}).get('foreign_quota_allowed'))
    cash = created['finances']['cash']
    fee = min(cash, int(target['estimated_transfer_value']))
    result = client.post(f"/api/football9394/careers/{cid}/transfers/{target['id']}", json={
        'fee_offer': fee, 'salary_offer': 0, 'contract_years': 3,
    })
    assert result.status_code == 200
    payload = result.json()
    # If the target is too expensive for this club, the API must return a real
    # counter/rejection rather than fake a signing.
    if payload['decision']['accepted']:
        assert any(p['id'] == target['id'] for p in payload['career']['squad'])
        assert payload['career']['finances']['cash'] < cash
    else:
        assert payload['decision']['reason'] in {'presupuesto_insuficiente','oferta_insuficiente','contrato_invalido','salario_insuficiente'}


def test_background_league_standings_are_persistent_in_career(monkeypatch, tmp_path):
    import backend.app.football9394.webapp as webapp
    monkeypatch.setattr(webapp, 'CAREER_SAVE_ROOT', tmp_path)
    state = client.post('/api/football9394/careers', json={'team_id':16,'seed':404,'through_matchday':7}).json()
    cid = state['career_id']
    france = client.get(f'/api/football9394/careers/{cid}/leagues/14/standings')
    assert france.status_code == 200
    data = france.json()
    assert data['completed_round'] == 7
    assert len(data['rows']) == 20
    assert all(row['played'] == 7 for row in data['rows'])


def test_career_exposes_world_economy_and_real_contract_renewal_decision(monkeypatch, tmp_path):
    import backend.app.football9394.webapp as webapp
    monkeypatch.setattr(webapp, 'CAREER_SAVE_ROOT', tmp_path)
    state=client.post('/api/football9394/careers',json={'team_id':16,'seed':505,'through_matchday':0}).json()
    cid=state['career_id']; player=state['squad'][0]
    contract=player['contract']
    assert contract['career_inferred'] is True
    renewal=client.post(f"/api/football9394/careers/{cid}/contracts/{player['id']}/renew",json={'years':3,'salary_offer':contract['salary']})
    assert renewal.status_code==200
    assert renewal.json()['decision']['accepted'] is True
    economy=client.get(f'/api/football9394/careers/{cid}/economy')
    assert economy.status_code==200 and 'finances' in economy.json()
    world=client.get(f'/api/football9394/careers/{cid}/world')
    assert world.status_code==200
    assert set(world.json()['special_progress'])=={'47','111','120'}
    # Las competiciones europeas históricas deben seguir ahí; el conjunto ya no
    # se fija de forma exacta porque el mundo incorpora además las copas
    # nacionales de los demás países, y un igual estricto convertía cada
    # competición nueva en un fallo.
    progress=world.json()['tournament_progress']
    assert {'1','2','3','90'} <= set(progress)
    assert all({'source_id','name','stage','completed'} <= set(row) for row in progress.values())


def test_new_career_options_expose_real_league_and_team_selection(monkeypatch, tmp_path):
    import backend.app.football9394.webapp as webapp
    monkeypatch.setattr(webapp, 'CAREER_SAVE_ROOT', tmp_path)
    options=client.get('/api/football9394/career-options')
    assert options.status_code==200
    leagues=options.json()['leagues']
    france=next(row for row in leagues if row['source_id']==14)
    team_id=france['teams'][0]['source_id']
    created=client.post('/api/football9394/careers',json={'league_id':14,'team_id':team_id,'through_matchday':0})
    assert created.status_code==200
    state=created.json()
    assert state['league_id']==14 and state['team']['source_id']==team_id
    calendar=client.get(f"/api/football9394/careers/{state['career_id']}/calendar")
    assert calendar.status_code==200
    assert len(calendar.json())==42
    assert sum(1 for row in calendar.json() if row.get('fixture_type')=='friendly')==4


def test_career_selection_and_dashboard_endpoints(monkeypatch, tmp_path):
    import backend.app.football9394.webapp as webapp
    monkeypatch.setattr(webapp, 'CAREER_SAVE_ROOT', tmp_path)
    created = client.post('/api/football9394/careers', json={'team_id':16,'league_id':1,'seed':8123,'through_matchday':0})
    assert created.status_code == 200
    state = created.json(); cid = state['career_id']
    dashboard = client.get(f'/api/football9394/careers/{cid}/dashboard')
    assert dashboard.status_code == 200
    assert dashboard.json()['board_expectation']['title']
    auto = client.put(f'/api/football9394/careers/{cid}/selection', json={'auto_select':True})
    assert auto.status_code == 200
    assert auto.json()['selection']['valid'] is True
    assert len(auto.json()['selection']['starter_ids']) == 11


def test_dismissed_manager_can_accept_same_league_job_through_api(monkeypatch, tmp_path):
    import backend.app.football9394.webapp as webapp
    monkeypatch.setattr(webapp, 'CAREER_SAVE_ROOT', tmp_path)
    created = client.post('/api/football9394/careers', json={'team_id':3,'league_id':1,'seed':9911,'through_matchday':0})
    assert created.status_code == 200
    cid = created.json()['career_id']
    career = webapp._load_manager_career(cid)
    career.state['job_status'] = 'dismissed'
    career._handle_user_dismissal()
    webapp._career_store().save(career.state)
    state = client.get(f'/api/football9394/careers/{cid}').json()
    offer = state['user_manager']['job_offers'][0]
    accepted = client.post(f"/api/football9394/careers/{cid}/jobs/{offer['id']}/accept")
    assert accepted.status_code == 200
    payload = accepted.json()
    assert payload['job_status'] == 'active'
    assert payload['team']['source_id'] == offer['team_id']
    assert payload['league_id'] == 1
    assert payload['selection']['valid'] is True


def test_role_promise_endpoint_persists_explicit_squad_commitment(monkeypatch, tmp_path):
    import backend.app.football9394.webapp as webapp
    monkeypatch.setattr(webapp, 'CAREER_SAVE_ROOT', tmp_path)
    state = client.post('/api/football9394/careers', json={'team_id':16,'league_id':1,'seed':1515,'through_matchday':0}).json()
    cid = state['career_id']
    player_id = state['squad'][0]['id']
    promised = client.post(f'/api/football9394/careers/{cid}/players/{player_id}/role-promise', json={'role':'Titular'})
    assert promised.status_code == 200
    payload = promised.json()
    assert payload['result']['role'] == 'Titular'
    assert payload['player']['role_promise']['status'] == 'active'
    detail = client.get(f'/api/football9394/careers/{cid}/players/{player_id}')
    assert detail.status_code == 200
    assert detail.json()['role_promise']['role'] == 'Titular'


def test_nf0_staff_responsibility_api_persists_and_validates(monkeypatch, tmp_path):
    import backend.app.football9394.webapp as webapp
    monkeypatch.setattr(webapp, 'CAREER_SAVE_ROOT', tmp_path)
    created = client.post('/api/football9394/careers', json={'team_id':16,'league_id':1,'seed':9394,'through_matchday':0})
    assert created.status_code == 200
    state = created.json(); cid = state['career_id']
    staff = client.get(f'/api/football9394/careers/{cid}/staff')
    assert staff.status_code == 200
    payload = staff.json()
    training = next(row for row in payload['responsibilities'] if row['key'] == 'first_team_training')
    candidate = next(row for row in training['eligible_assignees'] if row['id'] != 'manager')
    changed = client.put(
        f'/api/football9394/careers/{cid}/staff/responsibilities/first_team_training',
        json={'assignee': candidate['id']},
    )
    assert changed.status_code == 200
    updated = next(row for row in changed.json()['staff']['responsibilities'] if row['key'] == 'first_team_training')
    assert updated['assignee'] == candidate['id']
    restored = client.get(f'/api/football9394/careers/{cid}/staff').json()
    restored_training = next(row for row in restored['responsibilities'] if row['key'] == 'first_team_training')
    assert restored_training['assignee'] == candidate['id']

    physio = next(member for member in restored['members'] if member['role'] == 'physio')
    invalid = client.put(
        f'/api/football9394/careers/{cid}/staff/responsibilities/transfer_negotiation',
        json={'assignee': physio['id']},
    )
    assert invalid.status_code == 409
