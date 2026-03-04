# Project Context: DCA on Filling Your Motorbike

## Overview
This repository contains tools to simulate and analyze motorbike fuel costs in Vietnam. It compares different refueling strategies (standard "Full Tank" vs. an adaptive "DCA/Fixed Budget" approach) using historical petrol price data crawled from PVOIL.

## Repository Structure

### 1. Data Acquisition
*   **`00. get gas price.py`**
    *   **Purpose**: Crawls historical gas prices from the PVOIL website.
    *   **Mechanism**: Uses `playwright` (async) to navigate the site, detect the date dropdown, and scrape pricing tables.
    *   **Storage**: Updates `pvoil_prices.json`. It checks existing data to only fetch new dates.

### 2. Simulations
*   **`01. full_tank purchase_simulation.py`**
    *   **Strategy**: **Full Tank**.
    *   **Logic**: The rider refills the tank completely whenever the fuel level drops to **10%**.
    *   **Output**: `01.fuel_purchase_history.json`.

*   **`03. DCA purchase_simulation.py`**
    *   **Strategy**: **Adaptive / DCA (Dollar Cost Averaging)**.
    *   **Logic**: Attempts to simulate a real-world habit of paying a fixed round amount (budget), but adapts based on price fluctuations:
        *   **Fixed Budget**: Initially set to ~80% of a full tank cost (rounded to 10k VND).
        *   **Capped Rule**: If the fixed budget buys more fuel than the tank can hold (price dropped), the budget is reduced.
        *   **Short Gap Rule**: If the rider has to refuel too frequently (price rose), the system triggers a "Restart" (Full Tank) and recalculates a higher budget.
    *   **Output**: `03. fuel_purchase_history.json`.

### 3. Documentation
*   **`01. purchase explanation.md`**: Explains the constants (20km/day, 10% threshold) and basic consumption logic.
*   **`03. DCA purchase explanation.md`**: Details the complex adaptive logic (Rule 1: Capped, Rule 2: Short Gaps) used in script `03`.

### 4. Data Files
*   **`pvoil_prices.json`**: JSON database of historical prices keyed by date (DD-MM-YYYY).
*   **`bike_fuel_rate.csv`**: (Input) Specifications for different motorbikes (Model, Consumption L/100km, Tank Capacity, Recommended Fuel).

## How It Works

### Step 1: Data Crawling
Run `00. get gas price.py`. It launches a browser (headless or visible), iterates through date options on PVOIL, extracts prices for "RON 95-III" and "E5 RON 92", and saves them.

### Step 2: Simulation Execution
The simulation scripts (`01` and `03`) perform the following steps for each bike in the CSV:

1.  **Initialization**:
    *   Start Date: `2018-08-22`.
    *   Daily Distance: Fixed at **20 km/day**.
    *   Fuel Mapping: Selects **RON 95** if the bike spec mentions "95", otherwise **RON 92**.

2.  **Daily Loop**:
    *   Calculates daily consumption: `(20 / 100) * Consumption_Rate`.
    *   Decreases fuel level.
    *   Checks if fuel <= 10% of tank capacity.

3.  **Refueling Event**:
    *   Determines the price for the current date (looks up `pvoil_prices.json`; uses the most recent previous price if the current date is missing).
    *   Calculates volume and cost based on the specific strategy (Full Tank vs. Adaptive Budget).
    *   Logs the transaction.

## Key Logic Snippets

*   **Price Lookup**:
    ```python
    # Finds the closest date in history <= current_date
    valid_dates = [d for d in sorted_price_dates if d <= target_date]
    closest_date_str = valid_dates[-1].strftime("%d-%m-%Y")
    ```