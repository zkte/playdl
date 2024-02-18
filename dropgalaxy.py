import re
import time
import argparse
from playwright.sync_api import sync_playwright, TimeoutError
from contextlib import suppress
from pathvalidate import sanitize_filename
from pathlib import Path

parser = argparse.ArgumentParser(description="dropgalaxy")
parser.add_argument("-u", "--url", help="url")
parser.add_argument("-p", "--proxy", help="Proxy")
args = parser.parse_args()


def add_job(route, filename, crawljob):
    print(route.request.url)
    # print(route.request.headers)
    with open(crawljob, "w+") as f:
        f.write(f"text={route.request.url}\n")
        f.write(f"filename={filename}\n")
        f.write("autoConfirm=TRUE\n")
    print(crawljob.absolute())
    route.abort("accessdenied")


def adkill(p):
    skip = p.get_by_role("button", name="SKIP")
    consent = p.get_by_role("button", name="Consent")
    with suppress(TimeoutError):
        if consent.is_enabled(timeout=1000):
            consent.click(force=True)
    with suppress(TimeoutError):
        if skip.is_enabled(timeout=1000):
            skip.click(force=True)


def run(playwright, url):
    prefs = {
        "dom.webnotifications.enabled": False,
        "security.OCSP.enabled": 0,
        "media.webspeech.synth.enabled": False,
        "browser.eme.ui.enabled": False,
        "browser.link.open_newwindow.restriction": 0,
        "browser.tabs.loadDivertedInBackground": True,
    }
    if args.proxy:
        browser = playwright.firefox.launch(proxy={"server": args.proxy}, firefox_user_prefs=prefs)
    else:
        browser = playwright.firefox.launch(firefox_user_prefs=prefs)

    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    page.goto(url, referer=url)
    dl = page.get_by_role("button", name="Free Download")
    ready = page.get_by_role("button", name="Free Download ready!")
    while True:
        with suppress(TimeoutError):
            dl.click(timeout=1000)
        with suppress(TimeoutError):
            if ready.is_enabled(timeout=1000):
                break
        adkill(page)
    print("Free Download > click" + " " * 20, end="\r")
    wait = page.get_by_text(re.compile("Wait"))
    while True:
        with suppress(TimeoutError):
            ready.click(timeout=1000)
        with suppress(TimeoutError):
            if wait.is_enabled(timeout=1000):
                break
        adkill(page)
    print("Free Download ready! > click" + " " * 20, end="\r")
    create = page.get_by_role("button", name="Create download link")
    while True:
        with suppress(TimeoutError):
            print(page.get_by_text(re.compile("Wait")).text_content(timeout=1000) + " " * 20, end="\r")
        with suppress(TimeoutError):
            if create.is_enabled(timeout=1000):
                break
        adkill(page)
    print("Create download link > enabled" + " " * 20, end="\r")
    dl = page.get_by_role("button", name="Click here to download")
    while True:
        with suppress(TimeoutError):
            create.click(force=True, timeout=1000)
        with suppress(TimeoutError):
            if dl.is_enabled(timeout=1000):
                break
        # adkill(page)
    print("Click here to download > enabled" + " " * 20, end="\r")
    filename = sanitize_filename(page.locator(".name > h1").text_content().strip())
    filesize = page.locator(".name > span").nth(0).text_content().strip()
    crawljob = Path(f"{filename}.crawljob")
    context.route("https://*/d/**", lambda r: add_job(r, filename, crawljob))
    while True:
        if crawljob.exists():
            break
        with suppress(TimeoutError):
            dl.click(force=True, timeout=1000)
        adkill(page)
    print(f"'{filename}' {filesize}")
    time.sleep(5)
    browser.close()


if args.url:
    with sync_playwright() as playwright:
        run(playwright, args.url)
