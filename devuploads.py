import time
import argparse
from playwright.sync_api import sync_playwright, TimeoutError

parser = argparse.ArgumentParser(description="devuploads")
parser.add_argument("-u", "--url", help="url")
parser.add_argument("-p", "--proxy", help="Proxy")
args = parser.parse_args()


def add_job(route, filename):
    print(route.request.url)
    # print(route.request.headers)
    with open(f"{filename}.crawljob", "w+") as f:
        f.write(f"text={route.request.url}\n")
        f.write(f"filename={filename}\n")
        f.write("autoConfirm=TRUE\n")
    print(f"{filename}.crawljob")
    route.abort('accessdenied')


def run(playwright, url):
    if args.proxy:
        browser = playwright.firefox.launch(headless=False, proxy={"server": args.proxy})
    else:
        browser = playwright.firefox.launch()

    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    page.goto(url, referer=url)
    try:
        page.get_by_role("button", name="Generate Free Download Link").click(timeout=5000)
    except TimeoutError:
        page.get_by_role("button", name="Consent", exact=True).click(timeout=2000)
        page.get_by_role("button", name="Generate Free Download Link").click(timeout=5000)
    page.get_by_role("button", name="Link Generated!").click(trial=True)
    time.sleep(2)
    page.get_by_role("button", name="Link Generated!").click()
    for try_again in page.get_by_text("Try Again", exact=True).all():
        if try_again.is_visible():
            print("Try Again")
            exit(1)
    page.get_by_text("Download Now").scroll_into_view_if_needed()
    filename = page.locator(".name > h4").text_content().strip()
    filesize = page.locator(".name > span").nth(1).text_content().strip()
    page.route("https://*/d/**", lambda r: add_job(r, filename))
    page.get_by_text("Download Now").click()
    print(f"'{filename}' {filesize}")
    browser.close()


if args.url:
    with sync_playwright() as playwright:
        run(playwright, args.url)
