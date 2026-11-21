from playwright.sync_api import sync_playwright
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    page=browser.new_page(viewport={'width':1440,'height':1100},device_scale_factor=1)
    errors=[];page.on('pageerror',lambda error: errors.append(str(error)))
    page.goto(os.environ.get('DASHBOARD_URL','http://localhost:8765'));page.wait_for_load_state('networkidle');page.locator('#app').wait_for(state='visible')
    page.screenshot(path=str(ROOT/'research/desktop.png'),full_page=True)
    print('paths:',page.locator('path.district').count(),'map bbox',page.locator('#map').bounding_box())
    print('map rendered paths',page.locator('path.district[d]').count(),'total:',page.locator('#total').inner_text())
    print('initial district:',page.locator('.district-title h2').inner_text())
    page.locator('#state').select_option('AL');assert page.locator('#district-count').inner_text()=='7 / 7'
    page.locator('#search').fill('AL-05');assert page.locator('#rankings tr').count()==1
    page.locator('[data-select="0105"]').click();assert page.locator('.district-title h2').inner_text()=='AL-05'
    page.locator('#kind').select_option('contracts');page.locator('#metric').select_option('capita');page.locator('#year').select_option('2024')
    assert 'per resident' in page.locator('#map-title').inner_text().lower()
    with page.expect_download() as dl:page.locator('#download').click()
    downloaded=dl.value;downloaded.save_as(str(ROOT/'research/test-export.csv'))
    page.locator('#load-live').click();page.wait_for_function("!document.getElementById('load-live').disabled",timeout=120000)
    print('live detail',page.locator('#live-detail').inner_text()[:180])
    assert 'Top awarding agencies' in page.locator('#live-detail').inner_text()
    page.locator('#state-earmarks').click();assert page.locator('#ear-state').input_value()=='AL'
    page.locator('#ear-search').fill('water');print('earmark filtered',page.locator('#ear-count').inner_text())
    assert page.locator('.project').count()>0
    page.locator('#ear-search').fill('zzzzzzzzzzzz');assert 'No projects match' in page.locator('#ear-projects').inner_text()
    page.locator('#ear-search').fill('');page.locator('#ear-state').select_option('');page.locator('#ear-year').select_option('2024')
    assert page.locator('#ear-count').inner_text()=='8,098 unique projects'
    page.screenshot(path=str(ROOT/'research/earmarks.png'),full_page=False)
    page.locator('#method-open').click();assert page.locator('#method').is_visible();page.keyboard.press('Escape');assert not page.locator('#method').is_visible()
    page.locator('[data-view="districts"]').click();page.locator('#state').select_option('');page.locator('#search').fill('');page.locator('#year').select_option('2025');page.locator('#kind').select_option('all');page.locator('#metric').select_option('total')
    # Map clicking, selection, zoom, and reset.
    target=page.locator('path.district[data-id="3001"]');target.dispatch_event('click');assert page.locator('.district-title h2').inner_text()=='MT-01'
    page.locator('#zoom-in').click();page.locator('#reset-map').click()
    page.set_viewport_size({'width':390,'height':844});page.screenshot(path=str(ROOT/'research/mobile.png'),full_page=True)
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Mobile page overflows horizontally'
    assert not errors,errors
    print('Desktop/mobile interactions and export passed; no JavaScript errors.')
    browser.close()
