# Power BI Dashboard Guide

Build the dashboard yourself in Power BI Desktop (about 30-45 minutes), save the `.pbix` into this folder,
and add screenshots to `powerbi/screenshots/` for your README.

## 1. Connect
Get Data > SQL Server > server `localhost`, database `RetailDW`, Import mode.
Load: `dw.fact_sales`, `dw.dim_date`, `dw.dim_product`, `dw.dim_customer`, `dw.dim_store`
(or just the single view `dw.vw_sales_flat` for a quick start).

## 2. Model (star schema)
Create one-to-many relationships (dimension -> fact, single direction) on `date_key`, `product_key`,
`customer_key`, `store_key`. Mark `dim_date` as the Date table (`full_date`).

## 3. DAX measures
```DAX
Total Revenue = SUM(fact_sales[revenue])
Total Profit  = SUM(fact_sales[profit])
Margin % = DIVIDE([Total Profit], [Total Revenue])
Orders = DISTINCTCOUNT(fact_sales[order_id])
Avg Order Value = DIVIDE([Total Revenue], [Orders])
Revenue LY = CALCULATE([Total Revenue], SAMEPERIODLASTYEAR(dim_date[full_date]))
Revenue YoY % = DIVIDE([Total Revenue] - [Revenue LY], [Revenue LY])
Revenue YTD = TOTALYTD([Total Revenue], dim_date[full_date])
```

## 4. Suggested report page
- KPI cards: Revenue, Profit, Margin %, Orders, YoY %
- Line chart: Revenue and Profit by month
- Clustered bar: Revenue by category; map or bar: revenue by region
- Table / matrix: Top 10 products
- Slicers: Year, Region, Category, Segment
- Optional: drill-through page per customer segment

## 5. Publish evidence
Export a PDF and 2-3 screenshots of the report into `powerbi/screenshots/`.
