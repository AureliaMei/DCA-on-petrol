import pandas as pd
import json
import os
from datetime import datetime, timedelta

def simulate_fuel_purchases():
    # Đường dẫn file
    csv_path = "/Users/my/DCA-on-filling-your-motorbike/bike_fuel_rate.csv"
    json_prices_path = "pvoil_prices.json"  # Giả định file này nằm cùng thư mục chạy code
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

    # Chuyển đổi keys của price_data thành đối tượng datetime để dễ so sánh và sắp xếp
    sorted_price_dates = sorted(
        [datetime.strptime(d, "%d-%m-%Y") for d in price_data.keys()]
    )

    def get_price_for_date(target_date, fuel_type_keyword):
        """Tìm giá của loại xăng phù hợp vào ngày gần nhất tính từ target_date trở về trước"""
        # Tìm ngày điều chỉnh giá gần nhất (<= target_date)
        valid_dates = [d for d in sorted_price_dates if d <= target_date]
        if not valid_dates:
            return None
        
        closest_date_str = valid_dates[-1].strftime("%d-%m-%Y")
        daily_prices = price_data.get(closest_date_str, [])
        
        for item in daily_prices:
            # Tìm kiếm từ khóa RON 95 hoặc RON 92 trong tên sản phẩm
            if fuel_type_keyword.upper() in item['product'].upper():
                return item['price_vnd']
        return None

    # 3. Bắt đầu mô phỏng
    start_date = datetime(2018, 8, 22)
    end_date = sorted_price_dates[-1] if sorted_price_dates else datetime.now()
    
    simulation_results = {}

    for _, bike in bikes_df.iterrows():
        bike_name = f"{bike['Hãng xe']} {bike['Dòng xe']}"
        print(f"Đang mô phỏng cho: {bike_name}...")

        # Thông số xe
        consumption_per_100km = float(bike['Tiêu thụ (L/100km)'])
        tank_capacity = float(bike['Dung tích bình xăng (Lít)'])
        fuel_recommendation = bike['Xăng khuyến nghị (Tỷ số nén)']
        
        # Xác định từ khóa xăng (RON 95 hoặc RON 92)
        fuel_keyword = "RON 95" if "95" in fuel_recommendation else "RON 92"
        
        # Mức tiêu thụ mỗi ngày cho 20km
        daily_consumption = (20 / 100) * consumption_per_100km
        
        current_fuel_level = 0 # Bắt đầu với bình rỗng để đổ đầy ngay ngày đầu
        current_date = start_date
        purchase_history = []

        while current_date <= end_date:
            # Kiểm tra nếu bình xăng xuống dưới hoặc bằng 10%
            if current_fuel_level <= (0.1 * tank_capacity):
                price_per_liter = get_price_for_date(current_date, fuel_keyword)
                
                if price_per_liter:
                    amount_to_fill = tank_capacity - current_fuel_level
                    total_cost = amount_to_fill * price_per_liter
                    
                    purchase_history.append({
                        "date": current_date.strftime("%d-%m-%Y"),
                        "fuel_type": fuel_keyword,
                        "price_per_liter": price_per_liter,
                        "volume_liters": round(amount_to_fill, 2),
                        "cost_vnd": int(total_cost)
                    })
                    
                    # Đổ đầy bình
                    current_fuel_level = tank_capacity
            
            # Tiêu thụ xăng trong ngày
            current_fuel_level -= daily_consumption
            if current_fuel_level < 0: current_fuel_level = 0
            
            # Qua ngày tiếp theo
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
    
    print(f"\nHoàn tất! Kết quả mô phỏng đã được lưu vào {output_path}")

if __name__ == "__main__":
    simulate_fuel_purchases()