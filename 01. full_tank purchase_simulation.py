import pandas as pd
import json
import os
import random
from datetime import datetime, timedelta

def simulate_fuel_purchases():
    # Đường dẫn file
    csv_path = "/Users/my/DCA-on-filling-your-motorbike/bike_fuel_rate.csv"
    json_prices_path = "pvoil_prices.json"
    output_path = "fuel_purchase_history.json"

    # 1. Đọc dữ liệu xe từ CSV
    if not os.path.exists(csv_path):
        print(f"Không tìm thấy file CSV tại: {csv_path}")
        return
    
    bikes_df = pd.read_csv(csv_path)

    # 2. Đọc dữ liệu giá từ JSON
    if not os.path.exists(json_prices_path):
        print("Không tìm thấy file pvoil_prices.json. Vui lòng chạy script crawl trước.")
        return
        
    with open(json_prices_path, 'r', encoding='utf-8') as f:
        price_data = json.load(f)

    # Chuyển đổi keys thành datetime để sắp xếp
    sorted_price_dates = sorted(
        [datetime.strptime(d, "%d-%m-%Y") for d in price_data.keys()]
    )

    def get_price_for_date(target_date, fuel_type_keyword):
        """Tìm giá xăng dựa trên schema mới: { "date": { "fuels": [...] } }"""
        valid_dates = [d for d in sorted_price_dates if d <= target_date]
        if not valid_dates:
            return None
        
        closest_date_str = valid_dates[-1].strftime("%d-%m-%Y")
        
        # Lấy danh sách fuels từ dictionary của ngày đó
        day_info = price_data.get(closest_date_str, {})
        fuels_list = day_info.get('fuels', [])
        
        for item in fuels_list:
            # So khớp keyword (ví dụ: "RON 95") với "Xăng RON 95-III"
            if fuel_type_keyword.upper() in item['fuel_type'].upper():
                return item['price_vnd']
        return None

    # 3. Simulation Logic
    start_date = datetime(2018, 8, 22, 6, 0)
    end_date = sorted_price_dates[-1] if sorted_price_dates else datetime.now()
    
    simulation_results = {}

    for _, bike in bikes_df.iterrows():
        bike_name = f"{bike['Hãng xe']} {bike['Dòng xe']}"
        print(f"Đang mô phỏng cho: {bike_name}...")
        
        consumption_per_100km = float(bike['Tiêu thụ (L/100km)'])
        tank_capacity = float(bike['Dung tích bình xăng (Lít)'])
        fuel_recommendation = str(bike['Xăng khuyến nghị (Tỷ số nén)'])
        fuel_keyword = "RON 95" if "95" in fuel_recommendation else "RON 92"
        
        daily_consumption = (20 / 100) * consumption_per_100km
        hourly_consumption = daily_consumption / 16
        
        current_fuel_level = 0 
        current_date = start_date
        purchase_history = []

        while current_date <= end_date:
            # Morning check: predict if fuel hits <= 10% today
            if current_fuel_level - daily_consumption <= (0.1 * tank_capacity):
                refuel_hour = random.randint(6, 22)
                price_per_liter = get_price_for_date(current_date, fuel_keyword)
                
                if price_per_liter:
                    hours_passed = refuel_hour - 6
                    fuel_at_refuel = max(0, current_fuel_level - (hours_passed * hourly_consumption))
                    
                    amount_to_fill = tank_capacity - fuel_at_refuel
                    total_cost = amount_to_fill * price_per_liter
                    
                    purchase_history.append({
                        "date": current_date.strftime("%d-%m-%Y"),
                        "time": f"{refuel_hour:02d}:00",
                        "fuel_type": fuel_keyword,
                        "price_per_liter": price_per_liter,
                        "volume_liters": round(amount_to_fill, 2),
                        "cost_vnd": int(total_cost)
                    })
                    
                    remaining_hours = 22 - refuel_hour
                    current_fuel_level = tank_capacity - (remaining_hours * hourly_consumption)
                else:
                    current_fuel_level = max(0, current_fuel_level - daily_consumption)
            else:
                current_fuel_level -= daily_consumption

            current_date += timedelta(days=1)

        simulation_results[bike_name] = {
            "specs": {
                "consumption_rate": consumption_per_100km,
                "tank_capacity": tank_capacity,
                "fuel_type": fuel_keyword
            },
            "total_purchases": len(purchase_history),
            "total_spent": sum(p['cost_vnd'] for p in purchase_history),
            "history": purchase_history
        }

    # 4. Lưu kết quả
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(simulation_results, f, ensure_ascii=False, indent=4)
    
    print(f"\nHoàn tất! Đã lưu vào {output_path}")

if __name__ == "__main__":
    simulate_fuel_purchases()