from backend.app.football9394.career_international import build_national_sheet, generated_international_windows_9394, simulate_generated_friendlies
from backend.app.football9394.snapshot_runtime import default_runtime_snapshot


def test_national_friendlies_use_real_eligible_players_and_are_explicitly_generated():
    u=default_runtime_snapshot()
    sheet=build_national_sheet(u,11,development=None)
    assert len(sheet.starters)==11
    assert sheet.team_name=='España'
    out=simulate_generated_friendlies(u,development=None,window_index=0,seed=9394)
    assert out
    assert all(row['generated_fixture'] is True and row['historical_result'] is False for row in out)
    assert all(len(row['home_sheet'].starters)==11 for row in out)


def test_international_windows_span_the_playable_9394_season():
    dates=generated_international_windows_9394()
    assert dates[0].year==1993 and dates[-1].year==1994
    assert all(a<b for a,b in zip(dates,dates[1:]))
