-- Local-demo equivalent of etl.usp_load_star_schema (SQLite dialect)
INSERT OR IGNORE INTO dim_product (product_id, product_name, category, unit_cost)
  SELECT product_id, MAX(product_name), MAX(category), MAX(unit_cost) FROM stg_sales GROUP BY product_id;
INSERT OR IGNORE INTO dim_customer (customer_id, customer_name, city, segment)
  SELECT customer_id, MAX(customer_name), MAX(city), MAX(segment) FROM stg_sales GROUP BY customer_id;
INSERT OR IGNORE INTO dim_store (store_id, store_name, region)
  SELECT store_id, MAX(store_name), MAX(region) FROM stg_sales GROUP BY store_id;
INSERT OR IGNORE INTO dim_date (date_key, full_date, year, quarter, month, month_name, day, day_of_week)
  SELECT DISTINCT CAST(strftime('%Y%m%d', order_date) AS INTEGER), order_date,
         CAST(strftime('%Y', order_date) AS INTEGER),
         (CAST(strftime('%m', order_date) AS INTEGER) + 2) / 3,
         CAST(strftime('%m', order_date) AS INTEGER),
         CASE strftime('%m', order_date) WHEN '01' THEN 'January' WHEN '02' THEN 'February' WHEN '03' THEN 'March'
           WHEN '04' THEN 'April' WHEN '05' THEN 'May' WHEN '06' THEN 'June' WHEN '07' THEN 'July'
           WHEN '08' THEN 'August' WHEN '09' THEN 'September' WHEN '10' THEN 'October'
           WHEN '11' THEN 'November' ELSE 'December' END,
         CAST(strftime('%d', order_date) AS INTEGER),
         CASE strftime('%w', order_date) WHEN '0' THEN 'Sunday' WHEN '1' THEN 'Monday' WHEN '2' THEN 'Tuesday'
           WHEN '3' THEN 'Wednesday' WHEN '4' THEN 'Thursday' WHEN '5' THEN 'Friday' ELSE 'Saturday' END
  FROM stg_sales;
INSERT OR IGNORE INTO fact_sales (order_id, date_key, product_key, customer_key, store_key,
                                  quantity, unit_price, discount, revenue, cost, profit)
  SELECT s.order_id, dd.date_key, p.product_key, c.customer_key, st.store_key,
         s.quantity, s.unit_price, s.discount,
         ROUND(s.quantity*s.unit_price*(1-s.discount), 2),
         ROUND(s.quantity*s.unit_cost, 2),
         ROUND(s.quantity*s.unit_price*(1-s.discount) - s.quantity*s.unit_cost, 2)
  FROM stg_sales s
  JOIN dim_date dd ON dd.full_date = s.order_date
  JOIN dim_product p ON p.product_id = s.product_id
  JOIN dim_customer c ON c.customer_id = s.customer_id
  JOIN dim_store st ON st.store_id = s.store_id;
