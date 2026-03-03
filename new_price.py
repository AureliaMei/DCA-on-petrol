import asyncio
import json
import os
from datetime import datetime
from playwright.async_api import async_playwright

def get_latest_date_from_json(filename):
    if not os.path.exists(filename):
        return None
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not data:
                return None
            # Chuyển đổi keys (ngày) thành đối tượng datetime để tìm ngày lớn nhất
            dates = [datetime.strptime(d, "%d-%m-%Y") for d in data.keys()]
            return max(dates)
    except Exception:
        return None

async def crawl_pvoil_prices():
    json_filename = 'pvoil_prices.json'
    latest_saved_date = get_latest_date_from_json(json_filename)
    
    if latest_saved_date:
        print(f"Ngày mới nhất hiện có trong file: {latest_saved_date.strftime('%d-%m-%Y')}")
    else:
        print("Không tìm thấy file hoặc file trống. Sẽ cào toàn bộ dữ liệu.")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        url = "https://www.pvoil.com.vn/tin-gia-xang-dau"
        print(f"Đang truy cập {url}...")
        
        try:
            await page.goto(url, wait_until="domcontentloaded")
            dropdown_selector = "select#ddlpricedate"
            await page.wait_for_selector(dropdown_selector)

            options = await page.locator(f"{dropdown_selector} option").all()
            
            dates_to_crawl = []
            for opt in options:
                val = await opt.get_attribute("value")
                text = await opt.inner_text()
                if val:
                    current_date = datetime.strptime(text.strip(), "%d-%m-%Y")
                    # Nếu chưa có file cũ, hoặc ngày trên web mới hơn ngày trong file
                    if not latest_saved_date or current_date > latest_saved_date:
                        dates_to_crawl.append((val, text.strip()))

            if not dates_to_crawl:
                print("Dữ liệu đã được cập nhật bản mới nhất. Không cần cào thêm.")
                return

            print(f"Tìm thấy {len(dates_to_crawl)} ngày mới cần cập nhật.")

            # Đọc dữ liệu cũ nếu có
            new_data = {}
            if os.path.exists(json_filename):
                with open(json_filename, 'r', encoding='utf-8') as f:
                    new_data = json.load(f)

            # Lặp qua các ngày mới
            for date_val, date_text in dates_to_crawl:
                print(f"Đang lấy dữ liệu ngày: {date_text}")
                await page.select_option(dropdown_selector, value=date_val)
                await asyncio.sleep(2) 

                day_data = []
                rows = await page.locator("table tbody tr").all()
                for row in rows:
                    cols = await row.locator("td").all_inner_texts()
                    if len(cols) >= 3:
                        product = cols[1].strip()
                        if not product or "Sản phẩm" in product:
                            continue
                        
                        price_raw = cols[2].strip().replace(" đ", "").replace(".", "").replace(",", "")
                        try:
                            price_int = int(price_raw)
                        except ValueError:
                            price_int = 0

                        day_data.append({
                            "product": product,
                            "price_vnd": price_int,
                            "change": cols[3].strip() if len(cols) > 3 else "0"
                        })
                
                new_data[date_text] = day_data

            # Lưu file (Hợp nhất cũ và mới)
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, ensure_ascii=False, indent=4)
            print(f"\nThành công! Đã cập nhật thêm {len(dates_to_crawl)} ngày vào {json_filename}")

        except Exception as e:
            print(f"Có lỗi xảy ra: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(crawl_pvoil_prices())