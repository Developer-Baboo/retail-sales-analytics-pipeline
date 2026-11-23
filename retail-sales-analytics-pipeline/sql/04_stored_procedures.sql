USE RetailDW;
GO
/* ============================================================
   etl.usp_load_star_schema
   Upserts dimensions from staging (MERGE) and appends new facts.
   Idempotent: re-running does not duplicate rows.
   ============================================================ */
CREATE OR ALTER PROCEDURE etl.usp_load_star_schema
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;
    DECLARE @rows_in INT = (SELECT COUNT(*) FROM etl.stg_sales), @rows_out INT;

    BEGIN TRY
        BEGIN TRAN;

        MERGE dw.dim_product AS t
        USING (SELECT product_id, MAX(product_name) product_name, MAX(category) category, MAX(unit_cost) unit_cost
               FROM etl.stg_sales GROUP BY product_id) AS s
          ON t.product_id = s.product_id
        WHEN MATCHED AND (ISNULL(t.product_name,'') <> ISNULL(s.product_name,'')
                       OR ISNULL(t.category,'')     <> ISNULL(s.category,'')
                       OR t.unit_cost <> s.unit_cost)
            THEN UPDATE SET t.product_name = s.product_name, t.category = s.category, t.unit_cost = s.unit_cost
        WHEN NOT MATCHED THEN INSERT (product_id, product_name, category, unit_cost)
            VALUES (s.product_id, s.product_name, s.category, s.unit_cost);

        MERGE dw.dim_customer AS t
        USING (SELECT customer_id, MAX(customer_name) customer_name, MAX(city) city, MAX(segment) segment
               FROM etl.stg_sales GROUP BY customer_id) AS s
          ON t.customer_id = s.customer_id
        WHEN MATCHED AND (ISNULL(t.customer_name,'') <> ISNULL(s.customer_name,'')
                       OR ISNULL(t.city,'')    <> ISNULL(s.city,'')
                       OR ISNULL(t.segment,'') <> ISNULL(s.segment,''))
            THEN UPDATE SET t.customer_name = s.customer_name, t.city = s.city, t.segment = s.segment
        WHEN NOT MATCHED THEN INSERT (customer_id, customer_name, city, segment)
            VALUES (s.customer_id, s.customer_name, s.city, s.segment);

        MERGE dw.dim_store AS t
        USING (SELECT store_id, MAX(store_name) store_name, MAX(region) region
               FROM etl.stg_sales GROUP BY store_id) AS s
          ON t.store_id = s.store_id
        WHEN MATCHED AND (ISNULL(t.store_name,'') <> ISNULL(s.store_name,'')
                       OR ISNULL(t.region,'')     <> ISNULL(s.region,''))
            THEN UPDATE SET t.store_name = s.store_name, t.region = s.region
        WHEN NOT MATCHED THEN INSERT (store_id, store_name, region)
            VALUES (s.store_id, s.store_name, s.region);

        INSERT INTO dw.dim_date (date_key, full_date, [year], [quarter], [month], month_name, [day], day_of_week)
        SELECT DISTINCT
               YEAR(d.order_date)*10000 + MONTH(d.order_date)*100 + DAY(d.order_date),
               d.order_date, YEAR(d.order_date), DATEPART(QUARTER, d.order_date), MONTH(d.order_date),
               DATENAME(MONTH, d.order_date), DAY(d.order_date), DATENAME(WEEKDAY, d.order_date)
        FROM etl.stg_sales d
        WHERE NOT EXISTS (SELECT 1 FROM dw.dim_date x WHERE x.full_date = d.order_date);

        INSERT INTO dw.fact_sales (order_id, date_key, product_key, customer_key, store_key,
                                   quantity, unit_price, discount, revenue, cost, profit)
        SELECT s.order_id, dd.date_key, p.product_key, c.customer_key, st.store_key,
               s.quantity, s.unit_price, s.discount,
               CAST(s.quantity * s.unit_price * (1 - s.discount) AS DECIMAL(14,2)),
               CAST(s.quantity * s.unit_cost AS DECIMAL(14,2)),
               CAST(s.quantity * s.unit_price * (1 - s.discount) - s.quantity * s.unit_cost AS DECIMAL(14,2))
        FROM etl.stg_sales s
        JOIN dw.dim_date     dd ON dd.full_date  = s.order_date
        JOIN dw.dim_product  p  ON p.product_id  = s.product_id
        JOIN dw.dim_customer c  ON c.customer_id = s.customer_id
        JOIN dw.dim_store    st ON st.store_id   = s.store_id
        WHERE NOT EXISTS (SELECT 1 FROM dw.fact_sales f WHERE f.order_id = s.order_id);
        SET @rows_out = @@ROWCOUNT;

        COMMIT;
        INSERT etl.run_log(step, status, rows_in, rows_out, message)
        VALUES ('usp_load_star_schema', 'SUCCESS', @rows_in, @rows_out, 'Star schema loaded');
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK;
        INSERT etl.run_log(step, status, rows_in, message)
        VALUES ('usp_load_star_schema', 'FAILED', @rows_in, LEFT(ERROR_MESSAGE(), 400));
        THROW;
    END CATCH
END;
GO

/* dw.usp_sales_summary - parameterised monthly KPI report */
CREATE OR ALTER PROCEDURE dw.usp_sales_summary
    @from_date DATE = NULL,
    @to_date   DATE = NULL
AS
BEGIN
    SET NOCOUNT ON;
    SELECT d.[year], d.[month], d.month_name,
           SUM(f.revenue) AS revenue, SUM(f.profit) AS profit,
           CAST(100.0 * SUM(f.profit) / NULLIF(SUM(f.revenue),0) AS DECIMAL(6,2)) AS margin_pct,
           COUNT(*) AS order_lines
    FROM dw.fact_sales f
    JOIN dw.dim_date d ON d.date_key = f.date_key
    WHERE (@from_date IS NULL OR d.full_date >= @from_date)
      AND (@to_date   IS NULL OR d.full_date <= @to_date)
    GROUP BY d.[year], d.[month], d.month_name
    ORDER BY d.[year], d.[month];
END;
GO
