#!/usr/bin/env python3
import asyncio
import argparse
from selenium_driverless import webdriver
from selenium_driverless.types.by import By
from selenium_driverless.types.webelement import StaleElementReferenceException
from selenium_driverless.scripts.network_interceptor import NetworkInterceptor, InterceptedRequest, RequestPattern
from urllib.parse import urlparse
from pathvalidate import sanitize_filename
import warnings

warnings.filterwarnings("ignore")

parser = argparse.ArgumentParser(description="devuploads")
parser.add_argument("-u", "--url", help="url")
parser.add_argument("-p", "--proxy", help="Proxy")
args = parser.parse_args()

ALLOW = [
    "devuploads.com",
    "du2.devuploads.com",
    "thecubexguide.com",
    "dev.miuiflash.com",
    "jytechs.in",
    "djxmaza.in",
    "devfiles.pages.dev",
    "cdnjs.cloudflare.com",
    "securepubads.g.doubleclick.net",
    "pagead2.googlesyndication.com",
    "cdn.ampproject.org",
]

downloads = asyncio.Queue()


async def on_request(data: InterceptedRequest):
    if "devuploads.com" in data.request.url:
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
    # options.add_argument("--user-data-dir=/tmp/drl")
    if args.proxy:
        options.add_argument(f"--proxy-server={args.proxy}")
    async with webdriver.Chrome(options=options) as driver:
        async with NetworkInterceptor(
            driver, on_request=on_request, patterns=[RequestPattern.AnyRequest]
        ) as interceptor:
            await driver.get(args.url, wait_load=True)
            name_h1 = await driver.find_element(By.CSS, ".name > h4")
            filename = await name_h1.text
            name_b = await driver.find_elements(By.CSS, ".name span")
            f_date = await name_b[0].text
            f_size = await name_b[1].text
            u_date = " ".join(f_date.split())
            print(f"{filename.strip()} {f_size.strip()} {u_date}")
            dl_button = await driver.find_element(By.CSS, "#downloadbtnf", timeout=10)
            while True:
                try:
                    await dl_button.scroll_to()
                    if await dl_button.is_visible():
                        await dl_button.click()
                        break
                except StaleElementReferenceException:
                    break
            dl_button2 = await driver.find_element(By.CSS, "#downloadbtn", timeout=10)
            while True:
                t = await dl_button2.text
                if "Generated" in t:
                    print(t)
                    try:
                        if await dl_button2.is_visible():
                            await dl_button2.click()
                            break
                    except StaleElementReferenceException:
                        break
            final_dl = await driver.find_element(By.CSS, "#dlbtn", timeout=10)
            await final_dl.scroll_to()
            while True:
                try:
                    if await final_dl.is_visible():
                        await final_dl.click()
                except StaleElementReferenceException:
                    break
                url = await downloads.get()
                print(f"Direct: {url}")
                if url:
                    break
    crawljob = f"{sanitize_filename(filename.strip())}.crawljob"
    print(f"JD Folder Watch: '{crawljob}'")
    with open(crawljob, "w+") as f:
        f.write(f"text={url}\n")
        f.write(f"filename={filename.strip()}\n")
        f.write(f"comment={args.url}\n")
        f.write("autoConfirm=TRUE\n")
        f.write("autoStart=TRUE\n")
        f.write("chunks=1\n")


if args.url:
    asyncio.run(main())
