#!/usr/bin/env python3
import re
import asyncio
import argparse
from selenium_driverless import webdriver
from selenium_driverless.types.by import By
from selenium_driverless.types.webelement import StaleElementReferenceException
from selenium_driverless.scripts.network_interceptor import NetworkInterceptor, InterceptedRequest, RequestPattern
from pathvalidate import sanitize_filename
import warnings

warnings.filterwarnings("ignore")
parser = argparse.ArgumentParser(description="10drives")
parser.add_argument("-u", "--url", help="url")
parser.add_argument("-p", "--proxy", help="Proxy")
args = parser.parse_args()

downloads = asyncio.Queue()


async def on_request(data: InterceptedRequest):
    if re.search("cloud\\.10drives\\.com/download", data.request.url):
        downloads.put_nowait(data.request.url)
        await data.fail_request("TimedOut")
    else:
        await data.continue_request(intercept_response=False)


async def main():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-notifications")
    options.add_argument("--headless=new")
    options.user_data_dir = "driverless-ublock"
    options.auto_clean_dirs = False
    if args.proxy:
        options.add_argument(f"--proxy-server={args.proxy}")
    async with webdriver.Chrome(options=options) as driver:
        async with NetworkInterceptor(
            driver, on_request=on_request, patterns=[RequestPattern.AnyRequest]
        ) as interceptor:
            await driver.get(args.url, wait_load=True)
            table_td = await driver.find_elements(By.CSS, "table td")
            filename = await table_td[0].text
            f_size = await table_td[1].text
            print(f"{filename} {f_size}")
            dl_button = await driver.find_element(By.CSS, ".btn-primary", timeout=20)
            await dl_button.click()
            dl_button2 = await driver.find_element(By.CSS, ".create-link", timeout=10)
            await dl_button2.click()
            get_now = await driver.find_element(By.CSS, "#get-now-button", timeout=10)
            await get_now.click()
            countdown = await driver.find_element(By.CSS, "#countdown-display", timeout=10)
            while True:
                t = await countdown.text
                if len(t):
                    break
                else:
                    driver.sleep(1)
            while True:
                t = await countdown.text
                if len(t):
                    print(t + 10 * " ", end="\r")
                    await driver.sleep(1)
                else:
                    break
            final_dl = await driver.find_element(By.CSS, "#lsdwnbtn", timeout=10)
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
        f.write(f"text=directhttp://{url}\n")
        f.write(f"filename={filename}\n")
        f.write(f"comment={args.url}\n")
        f.write("autoConfirm=TRUE\n")
        f.write("autoStart=TRUE\n")
        f.write("chunks=1\n")


if args.url:
    asyncio.run(main())
