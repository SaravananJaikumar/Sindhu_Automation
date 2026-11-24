import os
import sys
import re
import calendar
from datetime import datetime, date, timedelta

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROOT)

import pytest
from playwright.sync_api import Page, expect
from Utils.email_sender import send_email_report

YEAR, MONTH = 2026, 11
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "Leverage_monthly_revenue.txt")


def dates_from_month_start_to_today():
    today = date.today()
    d = today.replace(day=1)
    while d <= today:
        yield d
        d += timedelta(days=1)


def test_login(page: Page):
    page.goto("https://leveragerx.hasoffers.com/")
    page.locator("#privacyCheckbox").check()
    page.locator("#cookieCheckbox").check()
    page.locator("//*[@id='cookieComplianceContinueButton']").click()
    page.locator("//input[@id='UserEmail']").fill("mledbetter@forbesadvisor.com")
    page.locator("//input[@id='UserPassword']").fill("aEUusxxm8Qam")
    page.locator("//input[@id='loginButton']").click()
    expect(page.locator("//h1[normalize-space()='Dashboard']")).to_be_visible()

    page.locator("//span[normalize-space()='Reports']").click()
    page.locator("//a[normalize-space()='Performance Report']").click()
    date_display = page.locator("//span[@id='date-range-3-display']")
    # expect(date_display).to_be_visible()

    # payout
    payout_cell = page.locator(r"#Stat\.offer_id--46").locator("td").nth(4)

    results = []

    # Start a fresh file with header
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("Date\tPayout\n")

    try:
        for d in dates_from_month_start_to_today():
            day_str = d.strftime("%Y-%m-%d")      # 2026-11-18 (input format)
            label = d.strftime("%b %d, %Y")       # Nov 18, 2026 (display format)

            # open the date picker
            date_display.click()

            # fill start and end date (same day)
            start_input = page.locator("input.datepicker-input-start:visible")
            end_input = page.locator("input.datepicker-input-end:visible")
            # expect(start_input).to_be_visible()

            start_input.fill(day_str)
            start_input.press("Tab")
            end_input.fill(day_str)
            end_input.press("Tab")

            # click Apply
            page.locator("a.apply.btn.ng-binding:visible").click()  # TODO verify

            # wait for the report to refresh for this date
            # expect(date_display).to_contain_text(label)
            page.wait_for_load_state("networkidle")
            expect(payout_cell).to_be_visible()

            payout = payout_cell.inner_text().strip()
            print(f"{day_str} -> {payout}")
            results.append((day_str, payout))

            # Append each record immediately to the output file
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(f"{day_str}\t{payout}\n")
    finally:
        # Guarantee email is sent with the updated output file
        if os.path.exists(OUTPUT_FILE) and os.path.getsize(OUTPUT_FILE) > 0:
            send_email_report(
                file_path=OUTPUT_FILE,
                subject=f"Leverage Monthly Revenue Report - {YEAR}-{MONTH:02d}",
                custom_message=f"Monthly revenue collection for Leverage ({calendar.month_name[MONTH]} {YEAR}) is complete.",
            )

    assert results, "No payout data collected"


if __name__ == "__main__":
    pytest.main(["-v", "-s", "--headed", __file__])
