import asyncio
from playwright.async_api import async_playwright

async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--window-size=1280,900",
            ],
        )
        page = await browser.new_page()
        try:
            url = "https://www.google.com/maps/search/home+decor+in+bhopal/@23.1986292,77.4587233,15z?entry=ttu&g_ep=EgoyMDI2MDMxNS4wIKXMDSoASAFQAw%3D%3D"
            print(f"Navigating to {url}...")
            # Use same wait_until as scraper
            await page.goto(url, wait_until="networkidle", timeout=30000)
            print("Successfully navigated!")
        except Exception as e:
            print(f"Failed with error: {e}")
        await browser.close()

asyncio.run(test())
