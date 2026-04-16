"""
Project 2: E-bike vs Classic Bike Unit Economics Analysis
==========================================================
Business Question: Should the next $5M expansion budget go to more e-bikes,
more classic bikes, or more charging infrastructure?

This script:
1. Computes utilization (trips/bike/day) by bike type
2. Models revenue per trip and per bike
3. Runs scenario analysis on 3 investment options
4. Breaks down adoption by user type and ward
5. Projects 12-month ridership and revenue impact
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

DATA = "/home/claude/portfolio/_shared_data"
OUT = "/home/claude/portfolio/project2_ebike_vs_classic/outputs"
os.makedirs(OUT, exist_ok=True)

# ============================================================
# 1. LOAD DATA
# ============================================================
print("Loading data...")
trips = pd.read_csv(f"{DATA}/trips.csv", parse_dates=["trip_start_time", "trip_end_time"])
stations = pd.read_csv(f"{DATA}/stations.csv")
trips["trip_date"] = trips["trip_start_time"].dt.date
trips["trip_month"] = trips["trip_start_time"].dt.to_period("M")
n_days = (trips["trip_start_time"].max() - trips["trip_start_time"].min()).days + 1

# ============================================================
# 2. FLEET ASSUMPTIONS (based on public Bike Share Toronto figures,
#    scaled to our 118-station dataset)
# ============================================================
FLEET_TOTAL = 1200          # scaled fleet size
EBIKE_SHARE = 0.22          # ~22% e-bikes (2,319 of 10,251 in real system)
FLEET_EBIKE = int(FLEET_TOTAL * EBIKE_SHARE)
FLEET_CLASSIC = FLEET_TOTAL - FLEET_EBIKE

# Revenue assumptions (CAD, blended member/casual)
REVENUE_PER_CLASSIC_TRIP = 1.80
REVENUE_PER_EBIKE_TRIP = 3.50

# Cost assumptions
COST_CLASSIC_BIKE = 1_200
COST_EBIKE = 3_800
COST_CHARGING_DOCK = 8_500
MAINT_CLASSIC_PER_YEAR = 280
MAINT_EBIKE_PER_YEAR = 650
BIKE_LIFESPAN_YEARS = 5
CHARGING_LIFESPAN_YEARS = 10

# ============================================================
# 3. UTILIZATION BY BIKE TYPE
# ============================================================
print("\nComputing utilization by bike type...")

trips_by_type = trips.groupby("bike_type").size().to_dict()
classic_trips = trips_by_type.get("classic", 0)
ebike_trips = trips_by_type.get("electric", 0)

util = pd.DataFrame([
    {"bike_type": "classic",  "fleet_size": FLEET_CLASSIC, "total_trips": classic_trips,
     "trips_per_bike_per_day": classic_trips / FLEET_CLASSIC / n_days},
    {"bike_type": "electric", "fleet_size": FLEET_EBIKE,   "total_trips": ebike_trips,
     "trips_per_bike_per_day": ebike_trips / FLEET_EBIKE / n_days},
])
util["utilization_ratio"] = util["trips_per_bike_per_day"] / util["trips_per_bike_per_day"].iloc[0]
util.to_csv(f"{OUT}/01_utilization_by_bike_type.csv", index=False)
print(util.to_string(index=False))

# ============================================================
# 4. UNIT ECONOMICS PER BIKE
# ============================================================
print("\nUnit economics per bike (annualized)...")

# Annualize from 6 months of data
ANNUAL_MULT = 365 / n_days

econ = pd.DataFrame([
    {
        "bike_type": "classic",
        "trips_per_year": util.loc[0, "trips_per_bike_per_day"] * 365,
        "revenue_per_trip": REVENUE_PER_CLASSIC_TRIP,
        "annual_revenue": util.loc[0, "trips_per_bike_per_day"] * 365 * REVENUE_PER_CLASSIC_TRIP,
        "acquisition_cost": COST_CLASSIC_BIKE,
        "annual_maint": MAINT_CLASSIC_PER_YEAR,
        "amortized_acq": COST_CLASSIC_BIKE / BIKE_LIFESPAN_YEARS,
        "infrastructure_share": 0,  # classic bikes use existing docks
    },
    {
        "bike_type": "electric",
        "trips_per_year": util.loc[1, "trips_per_bike_per_day"] * 365,
        "revenue_per_trip": REVENUE_PER_EBIKE_TRIP,
        "annual_revenue": util.loc[1, "trips_per_bike_per_day"] * 365 * REVENUE_PER_EBIKE_TRIP,
        "acquisition_cost": COST_EBIKE,
        "annual_maint": MAINT_EBIKE_PER_YEAR,
        "amortized_acq": COST_EBIKE / BIKE_LIFESPAN_YEARS,
        "infrastructure_share": COST_CHARGING_DOCK / CHARGING_LIFESPAN_YEARS / 3,  # 1 charging dock shared across ~3 e-bikes
    },
])

econ["annual_total_cost"] = econ["annual_maint"] + econ["amortized_acq"] + econ["infrastructure_share"]
econ["annual_profit"] = econ["annual_revenue"] - econ["annual_total_cost"]
econ["roi_pct"] = 100 * econ["annual_profit"] / econ["annual_total_cost"]

for col in ["trips_per_year", "annual_revenue", "annual_total_cost", "annual_profit", "amortized_acq", "infrastructure_share", "roi_pct"]:
    econ[col] = econ[col].round(0)
econ.to_csv(f"{OUT}/02_unit_economics.csv", index=False)
print(econ.to_string(index=False))

# ============================================================
# 5. ADOPTION BY USER TYPE AND WARD
# ============================================================
print("\nAdoption by user type...")

adoption = (
    trips.groupby(["user_type", "bike_type"]).size()
    .unstack(fill_value=0)
    .assign(ebike_share_pct=lambda d: (100 * d["electric"] / (d["classic"] + d["electric"])).round(1))
)
adoption.to_csv(f"{OUT}/03_adoption_by_user_type.csv")
print(adoption)

# By ward — is e-bike adoption geography-sensitive?
ward_adoption = (
    trips.merge(stations[["station_id", "ward", "has_charging"]], left_on="start_station_id", right_on="station_id")
    .groupby(["ward", "bike_type"]).size().unstack(fill_value=0)
    .assign(
        total=lambda d: d["classic"] + d["electric"],
        ebike_share_pct=lambda d: (100 * d["electric"] / (d["classic"] + d["electric"])).round(1),
    )
    .sort_values("ebike_share_pct", ascending=False)
)
ward_adoption.to_csv(f"{OUT}/04_ebike_share_by_ward.csv")

# ============================================================
# 6. SCENARIO ANALYSIS — WHERE SHOULD $5M GO?
# ============================================================
print("\nScenario analysis: allocating $5M expansion budget...")

BUDGET = 5_000_000

scenarios = []

# Scenario A: All into classic bikes
n_classic_a = BUDGET // COST_CLASSIC_BIKE
rev_a = n_classic_a * util.loc[0, "trips_per_bike_per_day"] * 365 * REVENUE_PER_CLASSIC_TRIP
cost_a = n_classic_a * (MAINT_CLASSIC_PER_YEAR + COST_CLASSIC_BIKE / BIKE_LIFESPAN_YEARS)
scenarios.append({
    "scenario": "A: 100% Classic bikes",
    "n_classic": int(n_classic_a), "n_ebikes": 0, "n_charging_docks": 0,
    "total_new_trips_year": int(n_classic_a * util.loc[0, "trips_per_bike_per_day"] * 365),
    "year1_revenue": round(rev_a),
    "year1_cost": round(cost_a),
    "year1_profit": round(rev_a - cost_a),
    "notes": "Minimizes unit cost risk. Adds capacity where charging is not a limit.",
})

# Scenario B: All into e-bikes + charging (proportional: 3 e-bikes per charging dock)
# Cost per "unit" = 3 * 3800 + 8500 = 19,900 for 3 ebikes + 1 dock
unit_cost_b = 3 * COST_EBIKE + COST_CHARGING_DOCK
n_units_b = BUDGET // unit_cost_b
n_ebikes_b = n_units_b * 3
rev_b = n_ebikes_b * util.loc[1, "trips_per_bike_per_day"] * 365 * REVENUE_PER_EBIKE_TRIP
cost_b = n_ebikes_b * (MAINT_EBIKE_PER_YEAR + COST_EBIKE / BIKE_LIFESPAN_YEARS) + n_units_b * (COST_CHARGING_DOCK / CHARGING_LIFESPAN_YEARS)
scenarios.append({
    "scenario": "B: 100% E-bikes + charging",
    "n_classic": 0, "n_ebikes": int(n_ebikes_b), "n_charging_docks": int(n_units_b),
    "total_new_trips_year": int(n_ebikes_b * util.loc[1, "trips_per_bike_per_day"] * 365),
    "year1_revenue": round(rev_b),
    "year1_cost": round(cost_b),
    "year1_profit": round(rev_b - cost_b),
    "notes": "Maximizes trips and revenue but requires matched charging infrastructure rollout.",
})

# Scenario C: Hybrid 60/40 (revenue-optimized split)
ebike_portion = 0.60
ebike_budget_c = BUDGET * ebike_portion
classic_budget_c = BUDGET - ebike_budget_c

n_units_c = int(ebike_budget_c // unit_cost_b)
n_ebikes_c = n_units_c * 3
n_classic_c = int(classic_budget_c // COST_CLASSIC_BIKE)

rev_c = (n_ebikes_c * util.loc[1, "trips_per_bike_per_day"] * 365 * REVENUE_PER_EBIKE_TRIP +
         n_classic_c * util.loc[0, "trips_per_bike_per_day"] * 365 * REVENUE_PER_CLASSIC_TRIP)
cost_c = (n_ebikes_c * (MAINT_EBIKE_PER_YEAR + COST_EBIKE / BIKE_LIFESPAN_YEARS) +
          n_units_c * (COST_CHARGING_DOCK / CHARGING_LIFESPAN_YEARS) +
          n_classic_c * (MAINT_CLASSIC_PER_YEAR + COST_CLASSIC_BIKE / BIKE_LIFESPAN_YEARS))
scenarios.append({
    "scenario": "C: Hybrid 60/40 (e-bike / classic)",
    "n_classic": n_classic_c, "n_ebikes": n_ebikes_c, "n_charging_docks": n_units_c,
    "total_new_trips_year": int(n_ebikes_c * util.loc[1, "trips_per_bike_per_day"] * 365 +
                                n_classic_c * util.loc[0, "trips_per_bike_per_day"] * 365),
    "year1_revenue": round(rev_c),
    "year1_cost": round(cost_c),
    "year1_profit": round(rev_c - cost_c),
    "notes": "Balances revenue and infrastructure risk; backwards-compatible with non-charging stations.",
})

scenarios_df = pd.DataFrame(scenarios)
scenarios_df["roi_pct_year1"] = (100 * scenarios_df["year1_profit"] / scenarios_df["year1_cost"]).round(1)
scenarios_df["payback_years"] = (scenarios_df.apply(
    lambda r: (r["n_classic"] * COST_CLASSIC_BIKE + r["n_ebikes"] * COST_EBIKE + r["n_charging_docks"] * COST_CHARGING_DOCK)
              / max(r["year1_profit"], 1), axis=1)).round(2)
scenarios_df.to_csv(f"{OUT}/05_scenario_comparison.csv", index=False)
print("\n", scenarios_df[["scenario", "n_ebikes", "n_classic", "year1_revenue", "year1_profit", "roi_pct_year1", "payback_years"]].to_string(index=False))

# ============================================================
# 7. TRIP DURATION & DISTANCE — do e-bikes enable different trips?
# ============================================================
print("\nTrip characteristics by bike type...")

trip_chars = trips.groupby("bike_type").agg(
    median_duration_min=("trip_duration_min", "median"),
    p90_duration_min=("trip_duration_min", lambda x: x.quantile(0.9)),
    mean_duration_min=("trip_duration_min", "mean"),
).round(1)
trip_chars.to_csv(f"{OUT}/06_trip_characteristics.csv")

# ============================================================
# 8. VISUALIZATIONS
# ============================================================
print("\nCharts...")
plt.rcParams.update({"font.family": "sans-serif", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

# Chart 1: Utilization
fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(util["bike_type"], util["trips_per_bike_per_day"], color=["#1A3550", "#C0392B"])
for i, v in enumerate(util["trips_per_bike_per_day"]):
    ax.text(i, v + 0.1, f"{v:.2f}", ha="center", fontweight="bold")
ax.set_title("Utilization: Trips per Bike per Day", fontsize=13, fontweight="bold")
ax.set_ylabel("Trips/bike/day")
plt.tight_layout()
plt.savefig(f"{OUT}/chart_01_utilization.png", dpi=120, bbox_inches="tight")
plt.close()

# Chart 2: Unit economics
fig, ax = plt.subplots(figsize=(10, 5))
x = np.arange(2)
w = 0.35
ax.bar(x - w/2, econ["annual_revenue"], w, label="Revenue", color="#1D6F42")
ax.bar(x + w/2, econ["annual_total_cost"], w, label="Total cost", color="#C0392B")
ax.set_xticks(x)
ax.set_xticklabels(econ["bike_type"])
ax.set_ylabel("CAD per bike per year")
ax.set_title("Annual Unit Economics: Revenue vs Cost per Bike", fontsize=13, fontweight="bold")
for i, (r, c) in enumerate(zip(econ["annual_revenue"], econ["annual_total_cost"])):
    ax.text(i - w/2, r + 30, f"${r:,.0f}", ha="center", fontsize=9)
    ax.text(i + w/2, c + 30, f"${c:,.0f}", ha="center", fontsize=9)
ax.legend()
plt.tight_layout()
plt.savefig(f"{OUT}/chart_02_unit_economics.png", dpi=120, bbox_inches="tight")
plt.close()

# Chart 3: Scenario comparison
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
colors = ["#1A3550", "#C0392B", "#1D6F42"]
ax1.bar(scenarios_df["scenario"].str[:20], scenarios_df["year1_profit"], color=colors)
ax1.set_title("Year 1 Profit by Scenario", fontweight="bold")
ax1.set_ylabel("CAD")
ax1.tick_params(axis="x", rotation=15)
for i, v in enumerate(scenarios_df["year1_profit"]):
    ax1.text(i, v + 20000, f"${v/1000:.0f}K", ha="center", fontweight="bold")

ax2.bar(scenarios_df["scenario"].str[:20], scenarios_df["payback_years"], color=colors)
ax2.set_title("Payback Period (Years)", fontweight="bold")
ax2.set_ylabel("Years")
ax2.tick_params(axis="x", rotation=15)
for i, v in enumerate(scenarios_df["payback_years"]):
    ax2.text(i, v + 0.1, f"{v}y", ha="center", fontweight="bold")
plt.tight_layout()
plt.savefig(f"{OUT}/chart_03_scenarios.png", dpi=120, bbox_inches="tight")
plt.close()

# Chart 4: E-bike share by ward
fig, ax = plt.subplots(figsize=(11, 8))
ward_plot = ward_adoption.sort_values("ebike_share_pct").tail(15)
ax.barh(ward_plot.index, ward_plot["ebike_share_pct"], color="#1A3550")
ax.set_xlabel("E-bike share of trips (%)")
ax.set_title("E-bike Adoption by Ward — Top 15", fontsize=13, fontweight="bold")
for i, v in enumerate(ward_plot["ebike_share_pct"]):
    ax.text(v + 0.3, i, f"{v}%", va="center", fontsize=9)
plt.tight_layout()
plt.savefig(f"{OUT}/chart_04_ebike_by_ward.png", dpi=120, bbox_inches="tight")
plt.close()

print("\n===== SUMMARY =====")
print(f"E-bike utilization ratio: {util.loc[1, 'utilization_ratio']:.2f}x classic")
print(f"E-bike annual revenue per bike: ${econ.loc[1, 'annual_revenue']:,.0f}  vs  Classic: ${econ.loc[0, 'annual_revenue']:,.0f}")
print(f"Recommended scenario: {scenarios_df.loc[scenarios_df['year1_profit'].idxmax(), 'scenario']}")
print(f"\nOutputs saved to: {OUT}")
