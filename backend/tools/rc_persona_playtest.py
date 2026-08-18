from __future__ import annotations

import json, mimetypes, os, tempfile, time
from pathlib import Path
from urllib.parse import urlparse
from collections import Counter

from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright

from backend.tools.rc_production_browser_gate import ROOT, PUBLIC, resolve_dist, inline_bundle, select_spain_barcelona


def is_dark_surface(page, selector: str) -> bool:
    value = page.locator(selector).first.evaluate("el => getComputedStyle(el).backgroundColor")
    import re
    nums = [float(x) for x in re.findall(r"[0-9.]+", value)[:3]]
    return len(nums) == 3 and max(nums) < 90

REPORT = ROOT / 'docs' / 'qa' / 'rc-persona-playtest.json'
VISUAL = ROOT / 'docs' / 'visual-qa' / 'rc-persona-playtest'


def main() -> int:
    dist = resolve_dist()
    if not dist:
        print('BLOCKED: bundle missing')
        return 2
    VISUAL.mkdir(parents=True, exist_ok=True)
    checks: dict[str,bool] = {}
    obs: dict[str,object] = {'dist': str(dist.relative_to(ROOT)), 'mode':'policy-safe-compiled-bundle-proxy'}
    counts=Counter()
    with tempfile.TemporaryDirectory(prefix='m9394-persona-') as tmp:
        tmp=Path(tmp)
        os.environ['MISTER9394_SAVE_DIR']=str(tmp/'saves')
        os.environ['MISTER9394_BACKUP_DIR']=str(tmp/'backups')
        os.environ['MISTER9394_LOG_DIR']=str(tmp/'logs')
        from backend.app.football9394.webapp import app
        client=TestClient(app)
        html=inline_bundle(dist)
        bootstrap="if(location.href.startsWith('about:blank')){document.open();document.write("+json.dumps(html)+");document.close();}"
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True, executable_path='/usr/bin/chromium', args=['--no-sandbox'])
            context=browser.new_context(locale='es-ES', reduced_motion='reduce', viewport={'width':1920,'height':1080})
            page=context.new_page()
            errors=[]
            page.on('pageerror',lambda e: errors.append(str(e)))

            def proxy(route):
                req=route.request; parsed=urlparse(req.url); counts[(req.method.upper(),parsed.path)]+=1
                if parsed.netloc=='mister.local' and parsed.path.startswith('/api/'):
                    q=parsed.path+(('?'+parsed.query) if parsed.query else '')
                    headers={}
                    if req.headers.get('content-type'): headers['content-type']=req.headers['content-type']
                    r=client.request(req.method,q,content=req.post_data or None,headers=headers)
                    route.fulfill(status=r.status_code,body=r.content,headers={'content-type':r.headers.get('content-type','application/json')}); return
                if parsed.netloc=='mister.local':
                    fp=(PUBLIC/parsed.path.lstrip('/')).resolve()
                    try: fp.relative_to(PUBLIC.resolve())
                    except ValueError: route.fulfill(status=403,body='forbidden'); return
                    if fp.is_file(): route.fulfill(status=200,body=fp.read_bytes(),headers={'content-type':mimetypes.guess_type(str(fp))[0] or 'application/octet-stream'})
                    else: route.fulfill(status=204,body=b'')
                    return
                route.continue_()

            page.route('https://mister.local/**',proxy)
            page.set_content(html,wait_until='load',timeout=60000)
            context.add_init_script(script=bootstrap)
            page.locator('.career-setup').wait_for(state='visible',timeout=30000)
            select_spain_barcelona(page)
            page.locator('button.start-career').click()
            page.locator('.manager-topbar').wait_for(state='visible',timeout=30000)
            page.wait_for_timeout(250)
            career_id=page.evaluate("localStorage.getItem('mister9394-career-id')")
            obs['career_id_created']=bool(career_id)

            # Persona A — newcomer: contextual first action and easy return.
            guide=page.locator('.first-run-guide')
            checks['novice_understands_first_action']=guide.is_visible() and 'No necesitas revisar todos los menús' in guide.inner_text()
            guide.locator('.football-button.primary').click()
            page.locator('.redesigned-tactics').wait_for(state='visible',timeout=15000)
            checks['novice_reaches_meaningful_decision']=page.locator('.tactics-process-trail').is_visible() and page.locator('.tactics-footer').is_visible()
            page.screenshot(path=str(VISUAL/'01-novice-tactics.png'),full_page=False)
            back=page.locator('.topbar-back').first
            checks['novice_has_visible_back']=back.count()>0 and back.is_visible()
            if back.count(): back.click(); page.wait_for_timeout(180)
            checks['novice_back_returns_home']=page.locator('.home-command-center').count()>0

            # Persona B — expert: keyboard to market, one search, one inquiry, visible process.
            page.keyboard.press('Control+K'); page.locator('.command-search input').fill('Mercado'); page.keyboard.press('Enter'); page.wait_for_timeout(180)
            search=page.locator('.market-search-main input'); search.fill('Ronaldo'); search.press('Enter'); page.wait_for_timeout(500)
            checks['expert_market_in_two_actions']=page.locator('.market-results .market-player-row').count()>0
            if page.locator('.market-results .market-player-row').count():
                row=page.locator('.market-results .market-player-row').first
                obs['market_candidate']=row.inner_text().split('\n')[0:4]
                consult=row.get_by_role('button',name='Consultar')
                if consult.count() and consult.is_enabled(): consult.click(); page.wait_for_timeout(500)
            checks['market_inquiry_becomes_visible_process']=page.locator('.inquiry-stack .negotiation-card').count()>0
            checks['market_keeps_dark_visual_grammar']=page.locator('.market-player-row').count()>0 and is_dark_surface(page,'.market-player-row')
            page.screenshot(path=str(VISUAL/'02-expert-market-inquiry.png'),full_page=False)

            print('PERSONA: novice/market complete', flush=True)
            # Persona C — complete match experience. We already test Continue in the production gate;
            # direct career advancement here avoids re-running a long asynchronous browser job and
            # isolates the match UX itself.
            reached=False; advances=[]
            for step in range(8):
                print(f'PERSONA: advance {step+1}', flush=True)
                t=time.monotonic(); r=client.post(f'/api/football9394/careers/{career_id}/advance-until-event?max_days=14'); elapsed=round(time.monotonic()-t,2)
                data=r.json(); advances.append({'seconds':elapsed,'date':data.get('date'),'requires_match':data.get('requires_match'),'advanced_days':data.get('advanced_days'),'reason':data.get('reason'),'requires_decision':data.get('requires_decision')})
                print('PERSONA: advance result', data.get('date'), data.get('advanced_days'), data.get('requires_match'), data.get('reason'), flush=True)
                if data.get('requires_match'): reached=True; break
            obs['direct_advances_to_matchday']=advances
            checks['career_progresses_to_matchday']=reached
            if reached:
                print('PERSONA: remounting matchday state', flush=True)
                page.evaluate("history.replaceState(null,'','#home')")
                page.set_content(html,wait_until='load',timeout=60000)
                page.locator('.manager-topbar').wait_for(state='visible',timeout=30000); page.wait_for_timeout(300)
                primary=page.locator('.home-matchday-actions .football-button.primary')
                checks['matchday_home_exposes_preview']=primary.count()>0 and 'Ir a la previa' in primary.inner_text()
                pre_next=page.locator('.home-matchup-v2').inner_text() if page.locator('.home-matchup-v2').count() else ''
                primary.click(); page.locator('.redesigned-live').wait_for(state='visible',timeout=30000); page.wait_for_timeout(300)
                checks['match_topbar_keeps_orientation']=page.locator('.topbar-heading h1').inner_text() == 'Partido' and 'DÍA DE PARTIDO' in page.locator('.topbar-heading small').inner_text()
                checks['preview_has_context_and_control']=page.locator('.match-preview-v2').is_visible() and page.get_by_role('button',name='Revisar XI').is_visible() and page.get_by_role('button',name='Táctica', exact=True).is_visible()
                checks['preview_does_not_start_clock']= "El reloj no corre" in page.locator('body').inner_text()
                checks['matchday_keeps_dark_visual_grammar']=is_dark_surface(page,'.prematch-xi') and is_dark_surface(page,'.match-world-context>span')
                page.screenshot(path=str(VISUAL/'03-match-preview.png'),full_page=False)
                print('PERSONA: simulate result', flush=True)
                page.locator('button.result-button').click()
                page.get_by_role('button',name='Cerrar partido').wait_for(state='visible',timeout=60000); page.wait_for_timeout(300)
                print('PERSONA: result finished', flush=True)
                checks['postmatch_is_explained']=page.locator('.modern-commentary.finished').count()>0 and page.locator('.post-causes').count()>0
                checks['postmatch_grid_has_no_orphan_half_row']=page.locator('.match-post-v2>div').count()==0 or page.locator('.match-post-v2>div').last.evaluate("el => { const s=getComputedStyle(el); const n=el.parentElement.children.length; return n%2===0 || (s.gridColumnStart==='1' && (s.gridColumnEnd==='-1' || s.gridColumnEnd==='-1')) }")
                page.screenshot(path=str(VISUAL/'04-postmatch.png'),full_page=False)
                page.get_by_role('button',name='Cerrar partido').click()
                page.locator('.home-command-center').wait_for(state='visible',timeout=30000); page.wait_for_timeout(400)
                post_next=page.locator('.home-matchup-v2').inner_text() if page.locator('.home-matchup-v2').count() else ''
                checks['postmatch_returns_to_career']=page.url.endswith('#home')
                checks['postmatch_changes_next_event']=bool(post_next and post_next != pre_next)
                page.screenshot(path=str(VISUAL/'05-home-after-match.png'),full_page=False)
            else:
                for k in ['match_topbar_keeps_orientation','matchday_home_exposes_preview','preview_has_context_and_control','preview_does_not_start_clock','matchday_keeps_dark_visual_grammar','postmatch_is_explained','postmatch_grid_has_no_orphan_half_row','postmatch_returns_to_career','postmatch_changes_next_event']: checks[k]=False
            checks['no_browser_page_errors']=not errors
            obs['page_errors']=errors
            obs['requests']=sum(counts.values())
            browser.close()

    passed=all(checks.values())
    report={'kind':'rc-persona-playtest','status':'passed' if passed else 'failed','passed':passed,'checks':checks,'observations':obs}
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for k,v in checks.items(): print(('PASS' if v else 'FAIL'),k)
    print('Report:',REPORT)
    return 0 if passed else 1

if __name__=='__main__': raise SystemExit(main())
