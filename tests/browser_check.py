"""Exercise real static datasets, payment period semantics, exports, and navigation."""

import csv
import json
import os
from decimal import Decimal
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
URL = os.environ.get("DASHBOARD_URL", "http://127.0.0.1:8765")
outlays = json.loads((ROOT / "dist/data/outlays.json").read_text())
assert outlays["metadata"]["annual_exports_available"], (
    "Annual financial reports must be assembled before handoff."
)
with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True, executable_path="/usr/bin/chromium", args=["--no-sandbox"]
    )
    page = browser.new_page(
        viewport={"width": 1440, "height": 1100}, device_scale_factor=1
    )
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto(URL)
    page.wait_for_load_state("networkidle")
    page.locator("#app").wait_for(state="visible")
    assert page.locator("#measure").input_value() == "outlays"
    assert page.locator("#year").input_value() == "2025"
    assert page.locator("path.district[d]").count() == 441
    assert page.locator(".data-note").count() == 0
    assert page.locator("#amount-heading").inner_text() == "Payments"
    page.screenshot(path=str(ROOT / "research/desktop.png"), full_page=False)
    page.locator("#state").select_option("AL")
    assert page.locator("#district-count").inner_text() == "7 / 7"
    page.locator("#search").fill("AL-05")
    page.locator('[data-select="0105"]').click()
    page.locator("#kind").select_option("contracts")
    expected = next(
        r["contracts"]
        for r in outlays["years"]["2025"]["districts"]
        if r["id"] == "0105"
    )
    title = page.locator(".big-amount").get_attribute("title")
    assert abs(
        Decimal(title.replace("$", "").replace(",", "")) - Decimal(str(expected))
    ) < Decimal(".02")
    with page.expect_download() as pending:
        page.locator("#download").click()
    pending.value.save_as(str(ROOT / "research/test-export.csv"))
    exported = list(csv.DictReader((ROOT / "research/test-export.csv").open()))
    al05 = next(r for r in exported if r["district_id"] == "0105")
    assert al05["measure"] == "outlays" and al05["period_start"] == "2024-10-01"
    assert abs(Decimal(al05["amount_usd"]) - Decimal(str(expected))) < Decimal(".02")
    page.locator("#load-live").click()
    page.wait_for_function("!document.getElementById('load-live').disabled")
    assert "Top awarding agencies" in page.locator("#live-detail").inner_text()
    page.locator('[data-view="cycles"]').click()
    assert page.locator("#measure").input_value() == "outlays"
    assert page.locator("#year").input_value() == "cycles-available"
    assert page.locator("#cycle-comparison tr").count() == 5
    assert "Opening-quarter" in page.locator("#cycle-comparison tr").first.inner_text()
    page.locator("#year").select_option("cycle115")
    assert page.locator("#total").inner_text() == "Unavailable"
    assert page.locator("#district-count").inner_text() == "0 / 7"
    assert "Opening-quarter" in page.locator("#coverage").inner_text()
    assert "Payment data are unavailable" in page.locator("#rankings").inner_text()
    with page.expect_download() as pending:
        page.locator("#download").click()
    pending.value.save_as(str(ROOT / "research/test-export.csv"))
    missing = list(csv.DictReader((ROOT / "research/test-export.csv").open()))
    assert len(missing) == 7 and all(
        r["amount_usd"] == "" and r["reporting_coverage"] == "unavailable"
        for r in missing
    )
    page.locator("#year").select_option("cycle118")
    assert "2023–2024" in page.locator("#map-subtitle").inner_text()
    page.locator("#metric").select_option("capita")
    assert "per resident" in page.locator("#map-title").inner_text()
    page.locator("#year").select_option("cycle119")
    assert "2026-09-30" in page.locator("#map-subtitle").inner_text()
    page.locator("#measure").select_option("obligations")
    page.locator("#year").select_option("cycles-all")
    assert page.locator("#amount-heading").inner_text() == "Obligations"
    assert "Five cycles" in page.locator("#map-subtitle").inner_text()
    # Verify that the live obligation detail carries the selected cycle's dates.
    posted = []

    def category_response(route):
        posted.append(route.request.post_data_json)
        route.fulfill(
            json={
                "results": [{"name": "Test agency", "amount": 100, "code": None}],
                "spending_level": "transactions",
            }
        )

    page.route(
        "https://api.usaspending.gov/api/v2/search/spending_by_category/**",
        category_response,
    )
    page.locator("#load-live").click()
    page.wait_for_function("!document.getElementById('load-live').disabled")
    assert posted and all(
        body["filters"]["time_period"]
        == [{"start_date": "2017-01-01", "end_date": "2026-09-30"}]
        for body in posted
    )
    page.unroute(
        "https://api.usaspending.gov/api/v2/search/spending_by_category/**",
        category_response,
    )
    page.locator("#state").select_option("")
    page.locator("#search").fill("")
    page.locator("#metric").select_option("total")
    page.locator("#cycle-comparison").scroll_into_view_if_needed()
    page.screenshot(path=str(ROOT / "research/cycles.png"), full_page=False)
    page.locator("#measure").select_option("outlays")
    assert page.locator("#year").input_value() == "cycles-available"
    page.locator("#year").select_option("all-reported")
    assert "as of" in page.locator("#map-subtitle").inner_text()
    page.locator("#state-earmarks").click()
    assert page.locator("#earmark-view").is_visible()
    page.locator("#ear-state").select_option("")
    page.locator("#ear-year").select_option("2024")
    assert page.locator("#ear-count").inner_text() == "8,098 unique projects"
    page.locator("#ear-search").fill("zzzzzzzzzzzz")
    assert "No projects match" in page.locator("#ear-projects").inner_text()
    page.locator("#ear-search").fill("")
    page.locator("#method-open").click()
    assert page.locator("#method").is_visible()
    page.keyboard.press("Escape")
    page.locator('[data-view="districts"]').click()
    page.locator("#year").select_option("2025")
    page.locator('path.district[data-id="3001"]').dispatch_event("click")
    assert page.locator(".district-title h2").inner_text() == "MT-01"
    page.locator("#zoom-in").click()
    page.locator("#reset-map").click()
    page.set_viewport_size({"width": 390, "height": 844})
    page.evaluate("scrollTo(0,0)")
    page.screenshot(path=str(ROOT / "research/mobile.png"), full_page=False)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    page.locator('[data-view="cycles"]').click()
    assert page.locator("#year").input_value() == "cycles-available"
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    assert not errors, errors
    print(
        "PASS: annual and cumulative payments; five calendar cycles and combined views; unavailable first cycle stays null in CSV; payment detail; obligation API dates; search, filters, exports, earmarks, dialog, map controls; mobile no overflow; no JavaScript errors."
    )
    browser.close()
