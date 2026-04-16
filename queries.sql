-- =====================================================================
-- PROJECT 2: E-BIKE vs CLASSIC — UNIT ECONOMICS & INVESTMENT ANALYSIS
-- =====================================================================
-- Business Question: Should the next $5M expansion budget go to more e-bikes,
-- more classic bikes, or more charging infrastructure?
-- =====================================================================


-- ---------------------------------------------------------------------
-- QUERY 1: Fleet utilization by bike type
-- ---------------------------------------------------------------------
-- Purpose: Baseline trips-per-bike-per-day comparison.
-- Assumes a fleet reference table; in production this would pull from
-- the bike fleet master (bike_id → bike_type → active status).

WITH fleet_assumptions AS (
    SELECT 'classic' AS bike_type,  936 AS fleet_size UNION ALL
    SELECT 'electric' AS bike_type, 264 AS fleet_size
),
trip_counts AS (
    SELECT
        bike_type,
        COUNT(*) AS total_trips,
        COUNT(DISTINCT trip_start_time::date) AS active_days
    FROM trips
    GROUP BY bike_type
)
SELECT
    tc.bike_type,
    fa.fleet_size,
    tc.total_trips,
    tc.active_days,
    ROUND(tc.total_trips::numeric / fa.fleet_size / tc.active_days, 2) AS trips_per_bike_per_day
FROM trip_counts tc
JOIN fleet_assumptions fa USING (bike_type)
ORDER BY trips_per_bike_per_day DESC;


-- ---------------------------------------------------------------------
-- QUERY 2: Revenue per bike type per month
-- ---------------------------------------------------------------------
-- Purpose: Track revenue contribution trend by bike type. Revenue is
-- modelled as a fixed rate per trip; real implementation would join
-- to a trip_pricing table.

WITH pricing AS (
    SELECT 'classic' AS bike_type,  1.80 AS revenue_per_trip UNION ALL
    SELECT 'electric' AS bike_type, 3.50 AS revenue_per_trip
)
SELECT
    DATE_TRUNC('month', t.trip_start_time) AS month,
    t.bike_type,
    COUNT(*) AS trips,
    ROUND(COUNT(*) * p.revenue_per_trip, 2) AS revenue,
    ROUND(
        100.0 * COUNT(*) * p.revenue_per_trip /
        SUM(COUNT(*) * p.revenue_per_trip)
            OVER (PARTITION BY DATE_TRUNC('month', t.trip_start_time)),
        1
    ) AS revenue_share_pct
FROM trips t
JOIN pricing p USING (bike_type)
GROUP BY DATE_TRUNC('month', t.trip_start_time), t.bike_type, p.revenue_per_trip
ORDER BY month, bike_type;


-- ---------------------------------------------------------------------
-- QUERY 3: E-bike adoption by user type
-- ---------------------------------------------------------------------
-- Purpose: Do members and casual users adopt e-bikes at different rates?
-- If casual users over-index on e-bikes, per-trip pricing may need review.

SELECT
    user_type,
    bike_type,
    COUNT(*) AS trips,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (PARTITION BY user_type), 1) AS pct_of_user_type
FROM trips
GROUP BY user_type, bike_type
ORDER BY user_type, bike_type;


-- ---------------------------------------------------------------------
-- QUERY 4: E-bike adoption by ward (geographic signal)
-- ---------------------------------------------------------------------
-- Purpose: Where is e-bike demand highest? Informs where to invest
-- in additional charging infrastructure.

SELECT
    s.ward,
    s.area_type,
    SUM(CASE WHEN t.bike_type = 'electric' THEN 1 ELSE 0 END) AS ebike_trips,
    SUM(CASE WHEN t.bike_type = 'classic' THEN 1 ELSE 0 END)  AS classic_trips,
    COUNT(*) AS total_trips,
    ROUND(
        100.0 * SUM(CASE WHEN t.bike_type = 'electric' THEN 1 ELSE 0 END) / COUNT(*),
        1
    ) AS ebike_share_pct
FROM trips t
JOIN stations s ON t.start_station_id = s.station_id
GROUP BY s.ward, s.area_type
ORDER BY ebike_share_pct DESC;


-- ---------------------------------------------------------------------
-- QUERY 5: Trip duration distribution by bike type
-- ---------------------------------------------------------------------
-- Purpose: Do e-bikes enable genuinely different trips (longer, further)?
-- Percentiles give a better picture than averages for skewed distributions.

SELECT
    bike_type,
    COUNT(*) AS trips,
    ROUND(AVG(trip_duration_min)::numeric, 1) AS avg_duration_min,
    PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY trip_duration_min) AS median_duration,
    PERCENTILE_CONT(0.90) WITHIN GROUP (ORDER BY trip_duration_min) AS p90_duration,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY trip_duration_min) AS p95_duration
FROM trips
GROUP BY bike_type;


-- ---------------------------------------------------------------------
-- QUERY 6: Charging station productivity
-- ---------------------------------------------------------------------
-- Purpose: How many e-bike trips per charging station? Identifies
-- whether charging capacity is a binding constraint.

WITH charging_stations AS (
    SELECT station_id, station_name, ward
    FROM stations
    WHERE has_charging = true
)
SELECT
    cs.ward,
    COUNT(DISTINCT cs.station_id) AS charging_stations,
    COUNT(CASE WHEN t.bike_type = 'electric' THEN 1 END) AS ebike_trips,
    ROUND(
        COUNT(CASE WHEN t.bike_type = 'electric' THEN 1 END)::numeric
            / COUNT(DISTINCT cs.station_id),
        0
    ) AS ebike_trips_per_station
FROM charging_stations cs
LEFT JOIN trips t ON t.start_station_id = cs.station_id
GROUP BY cs.ward
ORDER BY ebike_trips_per_station DESC;


-- ---------------------------------------------------------------------
-- QUERY 7: Investment scenario simulation
-- ---------------------------------------------------------------------
-- Purpose: Model three $5M investment scenarios and rank by year-1 profit.
-- This is a parameterized simulation, not an aggregation — in production
-- it would run inside a reporting layer or Python model.

WITH utilization AS (
    SELECT
        bike_type,
        COUNT(*)::numeric
            / (SELECT SUM(fleet_size) FROM (
                VALUES ('classic', 936), ('electric', 264)
              ) AS f(bike_type, fleet_size) WHERE f.bike_type = t.bike_type)
            / (SELECT COUNT(DISTINCT trip_start_time::date) FROM trips)
            AS trips_per_bike_per_day
    FROM trips t
    GROUP BY bike_type
),
parameters AS (
    SELECT
        5000000.0    AS budget,
        1200.0       AS classic_cost,  3800.0 AS ebike_cost, 8500.0 AS charging_cost,
        280.0        AS classic_maint, 650.0  AS ebike_maint,
        5.0          AS bike_lifespan, 10.0   AS charging_lifespan,
        1.80         AS classic_revenue, 3.50 AS ebike_revenue
),
scenarios AS (
    -- Scenario A: all classic
    SELECT
        'A: 100% Classic'         AS scenario,
        (p.budget / p.classic_cost)::int AS n_classic,
        0                         AS n_ebikes,
        0                         AS n_charging,
        (p.budget / p.classic_cost) * (SELECT trips_per_bike_per_day FROM utilization WHERE bike_type='classic') * 365 * p.classic_revenue AS year1_revenue,
        (p.budget / p.classic_cost) * (p.classic_maint + p.classic_cost / p.bike_lifespan) AS year1_cost
    FROM parameters p

    UNION ALL

    -- Scenario B: all e-bike + matched charging (3 e-bikes per charging dock)
    SELECT
        'B: 100% E-bike + charging',
        0, (p.budget / (3 * p.ebike_cost + p.charging_cost))::int * 3,
        (p.budget / (3 * p.ebike_cost + p.charging_cost))::int,
        (p.budget / (3 * p.ebike_cost + p.charging_cost)) * 3 * (SELECT trips_per_bike_per_day FROM utilization WHERE bike_type='electric') * 365 * p.ebike_revenue,
        (p.budget / (3 * p.ebike_cost + p.charging_cost)) * 3 * (p.ebike_maint + p.ebike_cost / p.bike_lifespan)
            + (p.budget / (3 * p.ebike_cost + p.charging_cost)) * (p.charging_cost / p.charging_lifespan)
    FROM parameters p

    UNION ALL

    -- Scenario C: 60/40 hybrid
    SELECT
        'C: 60/40 Hybrid',
        ((p.budget * 0.4) / p.classic_cost)::int,
        ((p.budget * 0.6) / (3 * p.ebike_cost + p.charging_cost))::int * 3,
        ((p.budget * 0.6) / (3 * p.ebike_cost + p.charging_cost))::int,
        ((p.budget * 0.4) / p.classic_cost) * (SELECT trips_per_bike_per_day FROM utilization WHERE bike_type='classic') * 365 * p.classic_revenue
          + ((p.budget * 0.6) / (3 * p.ebike_cost + p.charging_cost)) * 3 * (SELECT trips_per_bike_per_day FROM utilization WHERE bike_type='electric') * 365 * p.ebike_revenue,
        ((p.budget * 0.4) / p.classic_cost) * (p.classic_maint + p.classic_cost / p.bike_lifespan)
          + ((p.budget * 0.6) / (3 * p.ebike_cost + p.charging_cost)) * 3 * (p.ebike_maint + p.ebike_cost / p.bike_lifespan)
          + ((p.budget * 0.6) / (3 * p.ebike_cost + p.charging_cost)) * (p.charging_cost / p.charging_lifespan)
    FROM parameters p
)
SELECT
    scenario,
    n_classic, n_ebikes, n_charging,
    ROUND(year1_revenue)            AS year1_revenue,
    ROUND(year1_cost)               AS year1_cost,
    ROUND(year1_revenue - year1_cost) AS year1_profit,
    ROUND(100.0 * (year1_revenue - year1_cost) / year1_cost, 1) AS roi_pct
FROM scenarios
ORDER BY year1_profit DESC;
