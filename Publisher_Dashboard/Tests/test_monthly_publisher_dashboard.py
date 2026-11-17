import os
import sys
import re
import calendar
from datetime import datetime, date

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROOT)

import pytest
from playwright.sync_api import Page, expect
from Utils.email_sender import send_email_report

YEAR, MONTH = 2026, 11
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "SavingForCollege_monthly_revenue.txt")


def pick_date(page: Page, date_input, year: int, month: int, day: int):
    """Open the vdp-datepicker attached to `date_input` and click the given day."""
    date_input.click()

    cal = page.locator(".vdp-datepicker__calendar:visible")
    expect(cal).to_be_visible()

    # Navigate to the target month/year (header text looks like "Nov 2026")
    header = cal.locator("header .day__month_btn")
    target = datetime(year, month, 1)
    for _ in range(60):  # safety limit
        current = datetime.strptime(header.inner_text().strip(), "%b %Y")
        if current == target:
            break
        cal.locator("header .prev" if current > target else "header .next").click()

    # Exact-match regex so "1" doesn't match "11", "21", etc.
    cal.locator("span.cell.day:not(.disabled)").filter(
        has_text=re.compile(rf"^{day}$")
    ).click()


def test_monthly_revenue(page: Page):
    # ---------- Login ----------
    page.goto("https://publishers.savingforcollege.com/login")
    page.locator("//input[@type='text']").fill("forbes")
    page.locator("input[type='password']").fill("hello&Play1066")
    page.locator(".sfc-button.sfc-button-success").click()
    expect(page.locator("//span[normalize-space()='Forbes']")).to_be_visible()

    # ---------- Choose "Custom" in Filter by ----------
    page.get_by_role("combobox").select_option(label="Custom")

    from_input = page.get_by_text("From", exact=True).locator("xpath=following::input[1]")
    to_input = page.get_by_text("To", exact=True).locator("xpath=following::input[1]")

    # ---------- Work out which days to loop over ----------
    last_day = calendar.monthrange(YEAR, MONTH)[1]
    today = date.today()
    if (today.year, today.month) == (YEAR, MONTH):
        last_day = min(last_day, today.day)  # future dates are not selectable

    revenue_locator = page.locator(
        "div[class='total-numbers first'] div:nth-child(1) div:nth-child(2)"
    )

    # Start a fresh file with a header
    with open(OUTPUT_FILE, "w") as f:
        f.write("Date, Revenue\n")

    try:
        # ---------- Loop through every day ----------
        for day in range(1, last_day + 1):
            # The picker may block a From date later than the current To date (and vice versa),
            # so set them in the order that keeps From <= To.
            if day == 1:
                pick_date(page, from_input, YEAR, MONTH, day)
                pick_date(page, to_input, YEAR, MONTH, day)
            else:
                pick_date(page, to_input, YEAR, MONTH, day)
                pick_date(page, from_input, YEAR, MONTH, day)

            page.get_by_text("Submit").click()
            page.wait_for_load_state("networkidle")
            page.wait_for_timeout(1000)

            expect(revenue_locator).to_be_visible()
            revenue = revenue_locator.inner_text().strip()

            date_str = f"{YEAR}-{MONTH:02d}-{day:02d}"
            print(f"{date_str}: {revenue}")

            with open(OUTPUT_FILE, "a") as f:
                f.write(f"{date_str}, {revenue}\n")
    finally:
        # Guarantee email is sent with the updated output file
        if os.path.exists(OUTPUT_FILE) and os.path.getsize(OUTPUT_FILE) > 0:
            send_email_report(
                file_path=OUTPUT_FILE,
                subject=f"SavingForCollege Monthly Revenue Report - {YEAR}-{MONTH:02d}",
                custom_message=f"Monthly revenue collection for {calendar.month_name[MONTH]} {YEAR}.",
            )


if __name__ == "__main__":
    pytest.main(["-v", "-s", "--headed", __file__])