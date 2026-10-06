import requests
from playwright.sync_api import Page, expect


def _calculate(page: Page, live_server_url, a, operation, b):
    page.goto(f"{live_server_url}/calc")
    page.locator("#a").fill(str(a))
    page.locator("#operation").select_option(operation)
    page.locator("#b").fill(str(b))
    page.locator("#calculate-btn").click()


def test_browser_and_server_agree_on_six_times_seven(page: Page, live_server_url):
    errors = []
    page.on("console", lambda message: message.type == "error" and errors.append(message.text))
    _calculate(page, live_server_url, 6, "multiply", 7)

    expect(page.locator("#browser-result")).to_have_text("42")
    expect(page.locator("#api-result")).to_have_text("42")
    expect(page.locator("#status")).to_have_text("Results match")
    expect(page.locator("#result")).to_have_class("agree")
    assert errors == []  # the page runs under its CSP (CALC-30)


def test_division_by_zero_is_refused_by_both(page: Page, live_server_url):
    _calculate(page, live_server_url, 1, "divide", 0)

    expect(page.locator("#browser-result")).to_have_text("Cannot divide by zero.")
    expect(page.locator("#api-result")).to_have_text("Cannot divide by zero.")
    expect(page.locator("#status")).to_have_text("Both refused it")


def test_calculator_footer_shows_the_running_release(page: Page, live_server_url):
    health = requests.get(f"{live_server_url}/health", timeout=5).json()
    page.goto(f"{live_server_url}/calc")
    expect(page.locator("#release-footer")).to_contain_text(health["commit"])
