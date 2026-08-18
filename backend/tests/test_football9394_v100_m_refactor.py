from __future__ import annotations

import inspect
import json
from pathlib import Path

from fastapi.routing import APIRoute

from backend.app.football9394.manager_career import ManagerCareerRuntime9394
from backend.app.football9394.webapp import app

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = Path(__file__).resolve().parent / 'fixtures'


def _signature_shape(callable_obj) -> str:
    sig = inspect.signature(callable_obj)
    parts = []
    for p in sig.parameters.values():
        if p.kind == inspect.Parameter.VAR_POSITIONAL:
            parts.append('*' + p.name)
        elif p.kind == inspect.Parameter.VAR_KEYWORD:
            parts.append('**' + p.name)
        elif p.kind == inspect.Parameter.KEYWORD_ONLY:
            if not any(x == '*' for x in parts) and not any(x.startswith('*') and not x.startswith('**') for x in parts):
                parts.append('*')
            parts.append(p.name if p.default is inspect._empty else f'{p.name}=...')
        else:
            parts.append(p.name if p.default is inspect._empty else f'{p.name}=...')
    return '(' + ', '.join(parts) + ')'


def test_m_api_route_contract_matches_pre_refactor_snapshot():
    expected = json.loads((FIXTURES / 'v100_m_api_route_contract.json').read_text())
    actual = []
    for route in app.routes:
        if not isinstance(route, APIRoute) or not route.path.startswith('/api/football9394'):
            continue
        methods = sorted((route.methods or set()) & {'GET', 'POST', 'PUT', 'DELETE', 'PATCH'})
        for method in methods:
            actual.append({'method': method, 'path': route.path, 'handler': route.endpoint.__name__})
    assert sorted(actual, key=lambda x: (x['path'], x['method'], x['handler'])) == expected


def test_m_extracted_runtime_methods_keep_pre_refactor_signatures():
    expected = json.loads((FIXTURES / 'v100_m_runtime_signature_contract.json').read_text())
    for name, signature in expected.items():
        assert hasattr(ManagerCareerRuntime9394, name), name
        assert _signature_shape(getattr(ManagerCareerRuntime9394, name)) == signature


def test_m_runtime_behavior_survives_history_and_market_extraction():
    career = ManagerCareerRuntime9394.create(team_id=16, league_id=1, seed=9394, through_matchday=0)
    table = career.league_standings(1)
    market = career.market_snapshot()
    economy = career.economy_snapshot()
    assert len(table) == 20
    assert table[0]['position'] == 1
    assert market['period']['label']
    assert 'workflow' in market and 'processes' in market
    assert economy['currency']['label'] == 'ptas.'
    assert career.snapshot()['team']['source_id'] == 16


def test_m_source_roots_are_materially_smaller_and_have_real_seams():
    manager = ROOT / 'backend/app/football9394/manager_career.py'
    webapp = ROOT / 'backend/app/football9394/webapp.py'
    root_app = ROOT / 'frontend/src/football9394/Football9394App.vue'
    css_entry = ROOT / 'frontend/src/styles/football9394-manager.css'
    assert manager.stat().st_size < 300_000
    assert webapp.stat().st_size < 20_000
    assert root_app.stat().st_size < 70_000
    assert css_entry.stat().st_size < 2_000
    for rel in [
        'backend/app/football9394/career_history_runtime.py',
        'backend/app/football9394/career_market_runtime.py',
        'backend/app/football9394/career_routes.py',
        'backend/app/football9394/management_routes.py',
        'backend/app/football9394/match_market_routes.py',
        'backend/app/football9394/world_routes.py',
        'frontend/src/football9394/composables/useNavigationContext.js',
        'frontend/src/football9394/composables/useCareerState.js',
        'frontend/src/football9394/composables/useAsyncActionLock.js',
    ]:
        assert (ROOT / rel).is_file(), rel


def test_m_css_layers_preserve_compatibility_entrypoint():
    entry = (ROOT / 'frontend/src/styles/football9394-manager.css').read_text()
    expected = [
        'football9394-tokens.css', 'football9394-shell.css', 'football9394-workspaces.css',
        'football9394-depth.css', 'football9394-product.css', 'football9394-dark.css',
    ]
    for name in expected:
        assert name in entry
        assert (ROOT / 'frontend/src/styles' / name).stat().st_size > 100
