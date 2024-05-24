#!/usr/bin/env python3
import asyncio
import argparse
from selenium_driverless import webdriver
from selenium_driverless.types.by import By
from selenium_driverless.types.webelement import StaleElementReferenceException
from selenium_driverless.scripts.network_interceptor import NetworkInterceptor, InterceptedRequest, RequestPattern
from urllib.parse import urlparse
from pathvalidate import sanitize_filename

parser = argparse.ArgumentParser(description="dropgalaxy")
parser.add_argument("-u", "--url", help="url")
parser.add_argument("-p", "--proxy", help="Proxy")
args = parser.parse_args()

ALLOW = [
    "dropgalaxy.vip",
    "dropgalaxy.com",
    "assets-7pb.pages.dev",
    "assets.isavetube.com",
    "tmp.isavetube.com",
    "cdnjs.cloudflare.com",
    "fonts.googleapis.com",
    "static.cloudflareinsights.com",
    "challenges.cloudflare.com",
    "cdn.jsdelivr.net",
    "financemonk.net",
    "tpc.googlesyndication.com",
    "googleads.g.doubleclick.net",
    "securepubads.g.doubleclick.net",
    "dnhfi5nn2dt67.cloudfront.net",
    "ad.a-ads.com",
    "static.a-ads.com",
    "srtb.msn.com",
    "adoto.net",
    "pagead2.googlesyndication.com",
    "cdn.ampproject.org",
]

downloads = asyncio.Queue()


async def on_request(data: InterceptedRequest):
    if "a2zupload.com" in data.request.url:
        if "/d/" in data.request.url:
            downloads.put_nowait(data.request.url)
            await data.fail_request("TimedOut")
        else:
            await data.continue_request(intercept_response=False)
    elif urlparse(data.request.url).netloc in ALLOW:
        # print(f"{data.request.method} {data.request.url}")
        await data.continue_request(intercept_response=False)
    else:
        # print(data.request.url)
        await data.fail_request("TimedOut")


async def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--headless=new")
    if args.proxy:
        options.add_argument(f"--proxy-server={args.proxy}")
    async with webdriver.Chrome(options=options) as driver:
        async with NetworkInterceptor(
            driver, on_request=on_request, patterns=[RequestPattern.AnyRequest]
        ) as interceptor:
            await driver.get(args.url, wait_load=True)
            tab = driver.current_target.id
            dl_button = await driver.find_element(By.CSS, "#method_free2", timeout=10)
            await dl_button.click()
            await driver.switch_to.target(tab, activate=True)
            await driver.sleep(4)
            dl_button2 = await driver.find_element(By.CSS, "#method_free", timeout=10)
            await dl_button2.click()
            tokennstatus = await driver.find_element(By.CSS, "#tokennstatus", timeout=10)
            dlbtn = await driver.find_element(By.CSS, "#downloadBtnClick", timeout=10)
            while True:
                try:
                    if await dlbtn.is_displayed():
                        pass
                except StaleElementReferenceException:
                    break
                t = await tokennstatus.text
                print(t, end="\r")
                if "verify you are human" in t:
                    cfcaptcha = await driver.find_element(By.CSS, "#cfcaptcha > iframe", timeout=10)
                    await cfcaptcha.click(move_to=True)
                    await driver.switch_to.target(tab, activate=True)
                if "ready!" in t:
                    await dlbtn.click(move_to=True)
                await driver.sleep(1)
            h1 = await driver.find_element(By.CSS, ".name > h1", timeout=10)
            filename = await h1.text
            final_dl = await driver.find_element(By.CSS, "#dl", timeout=10)
            while True:
                try:
                    if await final_dl.is_displayed():
                        await final_dl.click()
                except StaleElementReferenceException:
                    break
            url = await downloads.get()
            print(url)
            print(filename)
    fn = sanitize_filename(filename.strip())
    with open(f"{fn}.crawljob", "w+") as f:
        f.write(f"text={url}\n")
        f.write(f"filename={filename}\n")
        f.write("autoConfirm=TRUE\n")


if args.url:
    asyncio.run(main())
