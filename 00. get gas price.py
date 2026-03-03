import asyncio
import csv
from playwright.async_api import async_playwright

async def crawl_pvoil_prices():
    async with async_playwright() as p:
        # Launch browser (set headless=True to run in background)
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        url = "https://www.pvoil.com.vn/tin-gia-xang-dau"
        print(f"Navigating to {url}...")
        await page.goto(url, wait_until="networkidle")

        # 1. Locate the date dropdown trigger
        # Based on the site structure, this is typically a custom select box
        dropdown_trigger = page.locator(".select-selected")
        
        # Open dropdown to load all available dates
        await dropdown_trigger.click()
        await page.wait_for_selector(".select-items")
        
        # Get all date options from the list
        date_elements = await page.locator(".select-items div").all()
        dates = [await el.inner_text() for el in date_elements]
        print(f"Found {len(dates)} dates to crawl.")

        all_results = []

        # 2. Iterate through each date
        for date_text in dates:
            print(f"Fetching data for: {date_text}")
            
            # Ensure dropdown is open
            if not await page.locator(".select-items").is_visible():
                await dropdown_trigger.click()
            
            # Click the specific date
            await page.get_by_text(date_text, exact=True).click()
            
            # Wait for the table to refresh (usually indicated by a short delay or state change)
            # We wait for the table header to reflect the selected date
            await page.wait_for_function(
                f"document.querySelector('table').innerText.includes('{date_text}')"
            )
            
            # 3. Extract table data
            # Target the table rows (skipping the header)
            rows = await page.locator("table tbody tr").all()
            if not rows: # Fallback for different table structures
                rows = await page.locator("table tr").all()[1:]

            for row in rows:
                cols = await row.locator("td").all_inner_texts()
                if len(cols) >= 4:
                    all_results.append({
                        "Date": date_text,
                        "No": cols[0].strip(),
                        "Product": cols[1].strip(),
                        "Price_VND": cols[2].strip().replace(" đ", "").replace(".", ""),
                        "Change": cols[3].strip()
                    })

        # 4. Save results to CSV
        keys = all_results[0].keys() if all_results else []
        with open('pvoil_fuel_prices.csv', 'w', newline='', encoding='utf-8-sig') as f:
            dict_writer = csv.DictWriter(f, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(all_results)

        print(f"Successfully saved {len(all_results)} records to pvoil_fuel_prices.csv")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(crawl_pvoil_prices())