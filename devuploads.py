import time
import argparse
from playwright.sync_api import sync_playwright

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
        browser = playwright.firefox.launch(proxy={"server": args.proxy})
    else:
        browser = playwright.firefox.launch()

    page = browser.new_page()
    page.goto(url, referer=url)
    page.get_by_role("button", name="Generate Download Link").click()
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


if args.url:
    with sync_playwright() as playwright:
        run(playwright, args.url)
