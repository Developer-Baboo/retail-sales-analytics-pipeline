USE RetailDW;
GO
/* Flattened view for Power BI / Excel */
CREATE OR ALTER VIEW dw.vw_sales_flat AS
SELECT f.order_id, d.full_date, d.[year], d.[quarter], d.[month], d.month_name,
       p.product_name, p.category, c.customer_id, c.customer_name, c.city, c.segment,
       s.store_name, s.region, f.quantity, f.unit_price, f.discount, f.revenue, f.cost, f.profit
FROM dw.fact_sales f
JOIN dw.dim_date d     ON d.date_key     = f.date_key
JOIN dw.dim_product p  ON p.product_key  = f.product_key
JOIN dw.dim_customer c ON c.customer_key = f.customer_key
JOIN dw.dim_store s    ON s.store_key    = f.store_key;
GO

/* OLAP-style: ROLLUP (year > quarter > month drill-down) */
CREATE OR ALTER VIEW dw.vw_revenue_rollup AS
SELECT d.[year], d.[quarter], d.[month],
       SUM(f.revenue) AS revenue, SUM(f.profit) AS profit,
       GROUPING_ID(d.[year], d.[quarter], d.[month]) AS grouping_level
FROM dw.fact_sales f JOIN dw.dim_date d ON d.date_key = f.date_key
GROUP BY ROLLUP (d.[year], d.[quarter], d.[month]);
GO

/* OLAP-style: CUBE (every category x region combination plus totals) */
CREATE OR ALTER VIEW dw.vw_category_region_cube AS
SELECT p.category, s.region, SUM(f.revenue) AS revenue, SUM(f.profit) AS profit,
       GROUPING(p.category) AS is_all_categories, GROUPING(s.region) AS is_all_regions
FROM dw.fact_sales f
JOIN dw.dim_product p ON p.product_key = f.product_key
JOIN dw.dim_store   s ON s.store_key   = f.store_key
GROUP BY CUBE (p.category, s.region);
GO

/* Window functions: month-over-month growth and YTD running total */
CREATE OR ALTER VIEW dw.vw_monthly_growth AS
WITH m AS (
    SELECT d.[year], d.[month], SUM(f.revenue) AS revenue
    FROM dw.fact_sales f JOIN dw.dim_date d ON d.date_key = f.date_key
    GROUP BY d.[year], d.[month]
)
SELECT [year], [month], revenue,
       LAG(revenue) OVER (ORDER BY [year], [month]) AS prev_month_revenue,
       CAST(100.0 * (revenue - LAG(revenue) OVER (ORDER BY [year], [month]))
            / NULLIF(LAG(revenue) OVER (ORDER BY [year], [month]), 0) AS DECIMAL(8,2)) AS mom_growth_pct,
       SUM(revenue) OVER (PARTITION BY [year] ORDER BY [month]
                          ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS ytd_revenue
FROM m;
GO

/* Top 5 products per category (RANK) */
CREATE OR ALTER VIEW dw.vw_top_products AS
SELECT * FROM (
    SELECT p.category, p.product_name, SUM(f.revenue) AS revenue,
           RANK() OVER (PARTITION BY p.category ORDER BY SUM(f.revenue) DESC) AS rnk
    FROM dw.fact_sales f JOIN dw.dim_product p ON p.product_key = f.product_key
    GROUP BY p.category, p.product_name
) x WHERE rnk <= 5;
GO
