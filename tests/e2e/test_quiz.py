import requests
from playwright.sync_api import Page, expect


def test_submit_disabled_until_all_questions_answered(page: Page, live_server_url):
    page.goto(live_server_url)
    submit = page.locator("#submit-btn")
    expect(submit).to_be_disabled()

    fieldsets = page.locator("fieldset")
    count = fieldsets.count()
    for i in range(count):
        fieldsets.nth(i).locator("input[type=radio]").first.check()
        if i < count - 1:
            expect(submit).to_be_disabled()

    expect(submit).to_be_enabled()


def test_quiz_recommends_sensodyne_and_confirms_agreement(page: Page, live_server_url):
    page.goto(live_server_url)

    fieldsets = page.locator("fieldset")
    for i in range(fieldsets.count()):
        fieldsets.nth(i).locator("input[type=radio]").last.check()

    page.locator("#submit-btn").click()

    result = page.locator("#result")
    expect(result).to_contain_text("Sensodyne")
    expect(result).to_have_class("agree")


def test_footer_release_matches_health_endpoint(page: Page, live_server_url):
    health = requests.get(f"{live_server_url}/health", timeout=5).json()

    page.goto(live_server_url)
    footer = page.locator("#release-footer")
    expect(footer).to_contain_text(health["commit"])
    expect(footer).to_contain_text(health["built_at"])
