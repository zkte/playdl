import re
import time
import argparse
from playwright.sync_api import sync_playwright, TimeoutError
from contextlib import suppress

parser = argparse.ArgumentParser(description="dropgalaxy")
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

    context = browser.new_context()
    page = context.new_page()
    page.goto(url, referer=url)
    page.get_by_role("button", name="Free Download").is_enabled()
    print("Free Download > enabled" + " " * 20, end="\r")
    try:
        page.get_by_role("button", name="Free Download").click(timeout=1000)
    except TimeoutError:
        page.get_by_role("button", name="SKIP").click(timeout=2000)
        page.get_by_role("button", name="Free Download").click(timeout=5000)
    print("Free Download > click" + " " * 20, end="\r")
    page.get_by_role("button", name="Free Download ready!").is_enabled()
    print("Free Download ready > enabled" + " " * 20, end="\r")
    try:
        page.get_by_role("button", name="Free Download ready!").click(timeout=3000)
    except TimeoutError:
        page.get_by_role("button", name="SKIP").click(timeout=2000)
        page.get_by_role("button", name="Free Download ready!").click(timeout=5000)
    print("Free Download ready > click" + " " * 20, end="\r")
    page.get_by_text(re.compile("Wait")).is_enabled(timeout=5000)
    with suppress(TimeoutError):
        while page.get_by_text(re.compile("Wait")).is_visible():
            print(page.get_by_text(re.compile("Wait")).text_content() + " " * 20, end="\r")
            time.sleep(1)
    print("Create download link > enabled" + " " * 20, end="\r")
    try:
        page.get_by_role("button", name="Create download link").click(timeout=3000)
    except TimeoutError:
        with suppress(TimeoutError):
            page.get_by_role("button", name="AGREE").click(timeout=1000)
        with suppress(TimeoutError):
            page.get_by_role("button", name="SKIP").click(timeout=1000)
        page.get_by_role("button", name="Create download link").click(timeout=5000)
    print("Create download link > click" + " " * 20, end="\r")
    page.get_by_role("button", name="Click here to download").is_enabled()
    filename = page.locator(".name > h1").text_content().strip()
    filesize = page.locator(".name > span").nth(0).text_content().strip()
    context.route("https://*/d/**", lambda r: add_job(r, filename))
    try:
        page.get_by_role("button", name="Click here to download").click(timeout=3000)
    except TimeoutError:
        page.get_by_role("button", name="SKIP").click(timeout=2000)
        page.get_by_role("button", name="Click here to download").click(timeout=5000)
    print("Click here to download > click" + " " * 20, end="\r")
    print(f"'{filename}' {filesize}")
    time.sleep(5)
    browser.close()


if args.url:
    with sync_playwright() as playwright:
        run(playwright, args.url)
