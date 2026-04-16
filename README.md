# Unit Economics & Investment Analysis

**Capital Allocation Case Study**
**Author:** Wesley Haruo Kurosawa
**Stack:** Python (pandas, matplotlib), SQL (PostgreSQL syntax)

---
<img width="1306" height="949" alt="chart_04_ebike_by_ward" src="https://github.com/user-attachments/assets/94bd764a-69b2-4850-9666-3ba00f5a222f" />
<img width="1549" height="587" alt="chart_03_scenarios" src="https://github.com/user-attachments/assets/76a15577-a669-4d22-b7e0-be8c42936f84" />
<img width="1189" height="588" alt="chart_02_unit_economics" src="https://github.com/user-attachments/assets/4d7cec77-9be6-4763-ad82-9843997230a8" />
<img width="949" height="588" alt="chart_01_utilization" src="https://github.com/user-attachments/assets/f777bf80-c0b6-48b2-b99c-525eaedf2377" />

## Executive Summary

... is preparing its 2026 expansion with a $10M+ budget. E-bikes deliver roughly **2x the trips-per-bike-per-day** of classic bikes and generate nearly **3x the revenue per bike**, but they cost 3x to acquire, 2.3x more to maintain, and require charging infrastructure. Deciding how to allocate the next $5M of capital is therefore not obvious — it depends on the ratio of revenue potential to infrastructure constraints.

This project builds a unit-economics model for both bike types, then simulates three capital-allocation scenarios to identify the option that maximises year-1 profit while managing downside risk.

**Key findings:**

| Metric | Classic | E-bike | Ratio |
|---|---|---|---|
| Trips per bike per day | 2.00 | 3.68 | 1.84× |
| Annual trips per bike | 738 | 1,345 | 1.82× |
| Annual revenue per bike | $1,105 | $3,955 | 3.58× |
| Annual total cost per bike | $520 | $1,693 | 3.26× |
| Annual profit per bike | $585 | $2,262 | 3.87× |
| Year-1 ROI | 112% | 134% | — |

**Recommendation:** The 60/40 hybrid (Scenario C) is the right call for this budget cycle. It captures 80% of the e-bike scenario's ROI while adding 4× more fleet units — improving geographic coverage and not betting everything on charging-infrastructure rollout timelines. Pure e-bike allocation (Scenario B) has the highest ROI per dollar, but at the cost of fewer total fleet units and higher dependency on charging rollout completing on schedule.

---

## Business Context

Bike Share Toronto grew to 7.8 million trips in 2025, a 10% increase over 2024, with e-bikes delivering double the trips-per-day of classic bikes. The 2030 target is 12–16 million rides per year. Reaching that target requires continued fleet expansion, but electrification comes with infrastructure dependencies: each e-bike needs access to a charging dock, and building charging stations is capital-intensive.

The question a Data Analyst on the .... Urban Solutions team would face: *"We have $5M for the next tranche. Where does it go?"* The answer requires combining utilization data, revenue modelling, and infrastructure constraints into a unified scenario analysis.

---

## Approach

The analysis is structured as a four-part unit economics build-up:

1. **Utilization** — how intensively is each bike type used?
2. **Unit revenue** — how much revenue does each bike generate per year?
3. **Unit cost** — acquisition (amortised), maintenance, and shared infrastructure
4. **Scenario simulation** — three capital-allocation options, ranked by year-1 profit

---

## Data

Six months of synthetic trip data (June–November 2025):

- **`trips.csv`** — 435,132 trips
- **`stations.csv`** — 118 stations, of which ~55% of urban stations have charging capability
- **`weather.csv`** — Daily weather for seasonality adjustments

Fleet composition is modelled at 1,200 bikes total: 936 classic (78%) and 264 e-bikes (22%), matching real Bike Share Toronto proportions (2,319 e-bikes of 10,251 total).

---

## Unit Economics Assumptions

All figures in CAD. Assumptions benchmarked against publicly available industry data on bike-sharing operations.

| Parameter | Classic | E-bike |
|---|---|---|
| Revenue per trip | $1.80 | $3.50 |
| Acquisition cost | $1,200 | $3,800 |
| Annual maintenance | $280 | $650 |
| Bike lifespan | 5 years | 5 years |
| Charging dock cost | — | $8,500 |
| Charging dock lifespan | — | 10 years |
| E-bikes per charging dock | — | 3 |

Amortised costs use straight-line depreciation over the asset lifespan. Revenue figures are blended member/casual averages; a production model would segment further.

---

## Key Results

### 1. Utilization

| Bike Type | Fleet Size | Total Trips (6 mo) | Trips/Bike/Day |
|---|---|---|---|
| Classic | 936 | 344,413 | **2.00** |
| Electric | 264 | 90,719 | **3.68** |

E-bikes deliver 1.84× the utilization of classic bikes. Every e-bike added to the system generates 1.8× as many trip-hours of productive use as a classic bike.

### 2. Unit Revenue & Profit per Bike

| Line | Classic | E-bike |
|---|---|---|
| Annual trips | 738 | 1,345 |
| Annual revenue | $1,105 | $3,955 |
| Amortised acquisition | $240 | $760 |
| Annual maintenance | $280 | $650 |
| Infrastructure share | $0 | $283 |
| **Total annual cost** | **$520** | **$1,693** |
| **Annual profit per bike** | **$585** | **$2,262** |

### 3. Adoption Patterns

E-bike share of trips: **34.2%** (versus 22% of fleet), confirming e-bikes are used disproportionately. Annual members and casual users adopt e-bikes at similar rates (~34%), meaning the e-bike premium is not purely a casual-tourism phenomenon — it reflects genuine preference across all user segments.

Geographic signal: urban wards with charging infrastructure show e-bike shares above 40%; suburban wards without charging show shares closer to 25–28%. Charging availability is the binding constraint.

### 4. Trip Characteristics

| Metric | Classic | E-bike |
|---|---|---|
| Median duration | 14 min | 18 min |
| 90th percentile duration | 32 min | 42 min |

E-bikes enable longer trips — a key qualitative factor. They expand the viable use cases (commuting from outer wards, longer recreational rides) beyond what classic bikes support.

---

## Scenario Analysis

### Scenario A: 100% Classic Bikes ($5M)

- 4,166 classic bikes added
- 2.56M additional trips/year
- Year-1 revenue: **$4.60M**
- Year-1 profit: **$2.44M**
- Year-1 ROI: **112.4%**
- Payback: **2.05 years**

### Scenario B: 100% E-bikes + Matched Charging Infrastructure

- 753 e-bikes + 251 charging docks
- 851K additional trips/year
- Year-1 revenue: **$2.98M**
- Year-1 profit: **$1.70M**
- Year-1 ROI: **133.5%** ← highest ROI
- Payback: **2.93 years**

### Scenario C: 60/40 Hybrid

- 1,666 classic bikes + 450 e-bikes + 150 charging docks
- 1.53M additional trips/year
- Year-1 revenue: **$3.62M**
- Year-1 profit: **$1.99M**
- Year-1 ROI: **122.3%**
- Payback: **2.50 years**

---

## Recommendation: Scenario C (60/40 Hybrid)

Scenario A has the highest absolute profit but adds zero e-bike capacity, missing the strategic direction of the system (2030 targets assume continued electrification). Scenario B has the highest ROI but adds only 753 fleet units versus 4,166 in Scenario A — 82% less capacity growth for the same budget.

Scenario C is the balanced choice for three reasons:

1. **Captures most of the e-bike economics** — 450 new e-bikes increase total e-bike fleet by ~170%
2. **Maintains fleet growth** — 2,116 new bikes total, enough to meaningfully serve new wards
3. **Reduces execution risk** — classic bikes can be deployed to any existing station immediately; e-bike deployment is gated by charging dock rollout

**Suggested implementation path:**

| Phase | Timeline | Investment |
|---|---|---|
| Phase 1: Deploy 1,666 classic bikes | Months 1–3 | $2.0M |
| Phase 2: Build 150 charging docks | Months 2–9 | $1.3M |
| Phase 3: Deploy 450 e-bikes as docks come online | Months 4–12 | $1.7M |

Staggering deployment aligns e-bike procurement with charging-infrastructure availability, preventing idle inventory.

---

## Sensitivity Analysis

A robust model should stress-test its assumptions. Three factors would change the recommendation:

| Sensitivity | Threshold | Impact |
|---|---|---|
| E-bike revenue per trip | Drops below $2.80 | Classic becomes more profitable in all scenarios |
| Charging dock cost | Rises above $14,000 | Scenario B falls behind Scenario C |
| E-bike utilization | Drops below 2.5 trips/day | Scenario A becomes dominant |

Monitoring these three metrics monthly would give early signal if the recommendation needs revisiting.

---

## Repository Structure

```
project2_ebike_vs_classic/
├── README.md
├── analysis.py                    # Python analysis pipeline
├── queries.sql                    # 7 SQL queries
└── outputs/
    ├── 01_utilization_by_bike_type.csv
    ├── 02_unit_economics.csv
    ├── 03_adoption_by_user_type.csv
    ├── 04_ebike_share_by_ward.csv
    ├── 05_scenario_comparison.csv
    ├── 06_trip_characteristics.csv
    ├── chart_01_utilization.png
    ├── chart_02_unit_economics.png
    ├── chart_03_scenarios.png
    └── chart_04_ebike_by_ward.png
```

---

## How to Run

```bash
pip install pandas numpy matplotlib
python ../_shared_data/generate_data.py
python analysis.py
```

---

## What This Project Demonstrates

- **Unit economics modelling** — breaking down revenue, cost, and profit to a per-unit level
- **Scenario analysis & capital allocation** — framing strategic trade-offs for executive decision-making
- **ROI vs absolute profit trade-offs** — the difference between "best return per dollar" and "best outcome for the business"
- **Sensitivity analysis** — identifying which assumptions most affect the recommendation
- **Business framing** — translating analytical output into phased implementation plans
- **Forecasting** — projecting annualized impact from 6 months of data with seasonality awareness
