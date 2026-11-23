USE RetailDW;
GO
/* Foreign-key lookup indexes for join-heavy analytical queries */
CREATE NONCLUSTERED INDEX IX_fact_sales_date     ON dw.fact_sales(date_key)     INCLUDE (revenue, profit, quantity);
CREATE NONCLUSTERED INDEX IX_fact_sales_product  ON dw.fact_sales(product_key)  INCLUDE (revenue, profit, quantity);
CREATE NONCLUSTERED INDEX IX_fact_sales_customer ON dw.fact_sales(customer_key) INCLUDE (revenue, profit);
CREATE NONCLUSTERED INDEX IX_fact_sales_store    ON dw.fact_sales(store_key)    INCLUDE (revenue, profit);
GO
/* Optional for large volumes: columnstore index for fast aggregation (OLAP-style workloads)
CREATE NONCLUSTERED COLUMNSTORE INDEX NCCI_fact_sales
ON dw.fact_sales (date_key, product_key, customer_key, store_key, quantity, revenue, cost, profit);
*/
