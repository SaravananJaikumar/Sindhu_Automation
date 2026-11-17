import os
import sys
import re
from datetime import date, timedelta

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
sys.path.insert(0, PROJECT_ROOT)

import pytest
from playwright.sync_api import expect, Page
from Utils.email_sender import send_email_report

OUTPUT_FILE = os.path.join(PROJECT_ROOT, "SavingForCollege_daily_revenue.txt")


def test_daily_revenue(page: Page):
    # ---------- Login ----------
    page.goto("https://publishers.savingforcollege.com/login")
    page.locator("//input[@type='text']").fill("forbes")
    page.locator("input[type='password']").fill("hello&Play1066")
    page.locator(".sfc-button.sfc-button-success").click()
    expect(page.locator("//span[normalize-space()='Forbes']")).to_be_visible()

    # ---------- Select "Yesterday" ----------
    dropdown = page.get_by_role("combobox")
    option_text = dropdown.locator("option").filter(
        has_text=re.compile(r"^Yesterday")
    ).first.inner_text()          # e.g. "Yesterday (Nov 16)"
    dropdown.select_option(label=option_text)

    page.get_by_text("Submit").click()
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    # ---------- Capture revenue ----------
    revenue_locator = page.locator(
        "div[class='total-numbers first'] div:nth-child(1) div:nth-child(2)"
    )
    expect(revenue_locator).to_be_visible()
    revenue = revenue_locator.inner_text().strip()

    # ---------- Date for the record ----------
    yesterday = date.today() - timedelta(days=1)
    date_str = yesterday.strftime("%Y-%m-%d")      # e.g. 2026-11-16

    print(f"{date_str}: {revenue}")

    # ---------- Append to file (write header only if file is new) ----------
    write_header = not os.path.exists(OUTPUT_FILE) or os.path.getsize(OUTPUT_FILE) == 0
    with open(OUTPUT_FILE, "a") as f:
        if write_header:
            f.write("Date, Revenue\n")
        f.write(f"{date_str}, {revenue}\n")

    # Share updated output file over email
    send_email_report(
        file_path=OUTPUT_FILE,
        subject=f"SavingForCollege Daily Revenue Report - {date_str}",
        custom_message=f"Daily revenue for {date_str}: {revenue}",
    )


if __name__ == "__main__":
    pytest.main(["-v", "-s", "--headed", __file__])
