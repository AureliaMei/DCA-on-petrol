import pandas as pd
import json
import os
import random
from datetime import datetime, timedelta

def simulate_fuel_purchases_v5():
    # --- CẤU HÌNH ĐƯỜNG DẪN ---
    csv_path = "bike_fuel_rate.csv"
    json_prices_path = "pvoil_prices.json"
    output_path = "03. fuel_purchase_history.json"

    # 1. Đọc dữ liệu
    if not os.path.exists(csv_path) or not os.path.exists(json_prices_path):
        print("❌ Thiếu file đầu vào (bike_fuel_rate.csv hoặc pvoil_prices.json).")
        return
    
    bikes_df = pd.read_csv(csv_path)
    with open(json_prices_path, 'r', encoding='utf-8') as f:
        price_data = json.load(f)

    # Chuyển đổi key ngày tháng để sắp xếp
    sorted_price_dates = sorted([datetime.strptime(d, "%d-%m-%Y") for d in price_data.keys()])

    def get_price_for_date(target_date, fuel_type_keyword):
        valid_dates = [d for d in sorted_price_dates if d <= target_date]
        if not valid_dates: return None
        closest_date_str = valid_dates[-1].strftime("%d-%m-%Y")
        fuels_list = price_data.get(closest_date_str, {}).get('fuels', [])
        for item in fuels_list:
            if fuel_type_keyword.upper() in item['fuel_type'].upper():
                return item['price_vnd']
        return None

    # 2. Simulation Logic
    start_date = datetime(2018, 8, 22)
    # Kết thúc tại ngày hiện tại hoặc ngày cuối cùng có dữ liệu giá
    end_date = sorted_price_dates[-1] if sorted_price_dates else datetime.now()
    simulation_results = {}

    for _, bike in bikes_df.iterrows():
        bike_name = f"{bike['Hãng xe']} {bike['Dòng xe']}"
        consumption_rate = float(bike['Tiêu thụ (L/100km)'])
        tank_capacity = float(bike['Dung tích bình xăng (Lít)'])
        fuel_recommendation = str(bike['Xăng khuyến nghị (Tỷ số nén)'])
        fuel_keyword = "RON 95" if "95" in fuel_recommendation else "RON 92"
        
        daily_consumption = (20 / 100) * consumption_rate
        hourly_consumption = daily_consumption / 16
        
        current_fuel_level = 0 
        current_date = start_date
        purchase_history = []
        
        # Biến trạng thái cho các quy tắc mới
        fixed_budget = None
        consecutive_capped_count = 0
        consecutive_short_gap_count = 0
        last_gaps = [] # Lưu 5 khoảng cách ngày gần nhất

        while current_date <= end_date:
            # Ngưỡng đổ xăng 10%
            if current_fuel_level <= (0.1 * tank_capacity):
                refuel_hour = random.randint(6, 22)
                price_per_liter = get_price_for_date(current_date, fuel_keyword)
                
                if price_per_liter:
                    # Lượng xăng thực tế tại trạm
                    fuel_at_station = max(0, current_fuel_level - ((refuel_hour - 6) * hourly_consumption))
                    is_capped = False
                    is_restart_trigger = False
                    
                    # --- RULE 2: KIỂM TRA TẦN SUẤT (SHORT GAPS) ---
                    if len(purchase_history) >= 1:
                        last_refuel_date = datetime.strptime(purchase_history[-1]['date'], "%d-%m-%Y")
                        current_gap = (current_date - last_refuel_date).days
                        
                        if len(last_gaps) >= 1:
                            avg_gap = sum(last_gaps) / len(last_gaps)
                            # Nếu gap hiện tại < 80% trung bình
                            if current_gap < (0.8 * avg_gap):
                                consecutive_short_gap_count += 1
                            else:
                                consecutive_short_gap_count = 0
                        
                        last_gaps.append(current_gap)
                        if len(last_gaps) > 5: last_gaps.pop(0)

                    if consecutive_short_gap_count >= 2:
                        is_restart_trigger = True
                        consecutive_short_gap_count = 0 # Reset sau khi trigger

                    # --- THỰC HIỆN GIAO DỊCH ---
                    if fixed_budget is None or is_restart_trigger:
                        # Đổ đầy bình (Restart hoặc lần đầu)
                        volume_to_fill = tank_capacity - fuel_at_station
                        bill_sum = volume_to_fill * price_per_liter
                        
                        # Thiết lập ngân sách 80% (làm tròn hàng chục nghìn)
                        rounded_base = (int(bill_sum) // 10000) * 10000
                        fixed_budget = int(0.8 * rounded_base)
                        
                        actual_cost = int(bill_sum)
                        volume_filled = volume_to_fill
                        p_type = "Full-tank (Restart)" if is_restart_trigger else "Full-tank (Initial)"
                        consecutive_capped_count = 0
                    else:
                        # Đổ theo ngân sách cố định
                        actual_cost = fixed_budget
                        volume_filled = actual_cost / price_per_liter
                        
                        # Kiểm tra tràn bình
                        max_possible = tank_capacity - fuel_at_station
                        if volume_filled > max_possible:
                            volume_filled = max_possible
                            actual_cost = int(volume_filled * price_per_liter)
                            is_capped = True
                        
                        p_type = "Fixed-budget"

                    # --- RULE 1: KIỂM TRA TRÀN BÌNH LIÊN TỤC (CAPPED) ---
                    if is_capped:
                        consecutive_capped_count += 1
                    else:
                        consecutive_capped_count = 0

                    if consecutive_capped_count >= 2:
                        # Lấy bill lớn hơn trong 2 lần gần nhất (lần hiện tại và lần vừa xong)
                        # Ở đây lần hiện tại là actual_cost, lần trước là purchase_history[-1]['cost_vnd']
                        prev_cost = purchase_history[-1]['cost_vnd']
                        higher_bill = max(actual_cost, prev_cost)
                        # Update budget mới = làm tròn chục của bill lớn hơn
                        fixed_budget = (higher_bill // 10000) * 10000
                        consecutive_capped_count = 0 # Reset sau khi đổi budget

                    # Lưu lịch sử (Đảm bảo đúng tên Key để không lỗi nữa)
                    purchase_history.append({
                        "date": current_date.strftime("%d-%m-%Y"),
                        "time": f"{refuel_hour:02d}:00",
                        "fuel_type": fuel_keyword,
                        "price_per_liter": price_per_liter,
                        "volume_liters": round(volume_filled, 3),
                        "cost_vnd": actual_cost,
                        "type": p_type
                    })
                    
                    # Cập nhật mức xăng cuối ngày
                    current_fuel_level = (fuel_at_station + volume_filled) - ((22 - refuel_hour) * hourly_consumption)
                else:
                    # Không có giá xăng
                    current_fuel_level = max(0, current_fuel_level - daily_consumption)
            else:
                current_fuel_level -= daily_consumption

            current_date += timedelta(days=1)

        simulation_results[bike_name] = {
            "specs": {
                "tank_capacity": tank_capacity,
                "fuel_type": fuel_keyword
            },
            "summary": {
                "total_purchases": len(purchase_history),
                "total_spent_vnd": sum(p['cost_vnd'] for p in purchase_history),
                "total_liters": round(sum(p['volume_liters'] for p in purchase_history), 2)
            },
            "history": purchase_history
        }

    # Xuất file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(simulation_results, f, ensure_ascii=False, indent=4)
    
    print(f"✅ Xong! Đã lưu {len(simulation_results)} xe vào {output_path}")

if __name__ == "__main__":
    simulate_fuel_purchases_v5()