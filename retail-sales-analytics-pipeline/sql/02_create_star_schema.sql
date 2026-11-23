USE RetailDW;
GO
/* ---------- Staging (cleaned landing table) ---------- */
IF OBJECT_ID('etl.stg_sales') IS NULL
CREATE TABLE etl.stg_sales (
    order_id      VARCHAR(20)   NOT NULL,
    order_date    DATE          NOT NULL,
    customer_id   VARCHAR(20)   NOT NULL,
    customer_name NVARCHAR(100) NULL,
    city          NVARCHAR(60)  NULL,
    segment       NVARCHAR(30)  NULL,
    product_id    VARCHAR(20)   NOT NULL,
    product_name  NVARCHAR(100) NULL,
    category      NVARCHAR(50)  NULL,
    unit_cost     DECIMAL(10,2) NOT NULL,
    store_id      VARCHAR(20)   NOT NULL,
    store_name    NVARCHAR(100) NULL,
    region        NVARCHAR(40)  NULL,
    quantity      INT           NOT NULL,
    unit_price    DECIMAL(10,2) NOT NULL,
    discount      DECIMAL(4,2)  NOT NULL
);

IF OBJECT_ID('etl.run_log') IS NULL
CREATE TABLE etl.run_log (
    run_id      INT IDENTITY(1,1) PRIMARY KEY,
    run_ts      DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
    step        VARCHAR(60) NOT NULL,
    status      VARCHAR(10) NOT NULL,   -- SUCCESS / FAILED / WARN
    rows_in     INT NULL,
    rows_out    INT NULL,
    message     NVARCHAR(400) NULL
);

/* ---------- Dimensions ---------- */
IF OBJECT_ID('dw.dim_date') IS NULL
CREATE TABLE dw.dim_date (
    date_key     INT PRIMARY KEY,          -- yyyymmdd
    full_date    DATE NOT NULL UNIQUE,
    [year]       SMALLINT NOT NULL,
    [quarter]    TINYINT  NOT NULL,
    [month]      TINYINT  NOT NULL,
    month_name   VARCHAR(12) NOT NULL,
    [day]        TINYINT  NOT NULL,
    day_of_week  VARCHAR(12) NOT NULL
);

IF OBJECT_ID('dw.dim_product') IS NULL
CREATE TABLE dw.dim_product (
    product_key  INT IDENTITY(1,1) PRIMARY KEY,
    product_id   VARCHAR(20) NOT NULL UNIQUE,
    product_name NVARCHAR(100) NULL,
    category     NVARCHAR(50)  NULL,
    unit_cost    DECIMAL(10,2) NOT NULL
);

IF OBJECT_ID('dw.dim_customer') IS NULL
CREATE TABLE dw.dim_customer (
    customer_key  INT IDENTITY(1,1) PRIMARY KEY,
    customer_id   VARCHAR(20) NOT NULL UNIQUE,
    customer_name NVARCHAR(100) NULL,
    city          NVARCHAR(60)  NULL,
    segment       NVARCHAR(30)  NULL
);

IF OBJECT_ID('dw.dim_store') IS NULL
CREATE TABLE dw.dim_store (
    store_key  INT IDENTITY(1,1) PRIMARY KEY,
    store_id   VARCHAR(20) NOT NULL UNIQUE,
    store_name NVARCHAR(100) NULL,
    region     NVARCHAR(40)  NULL
);

/* ---------- Fact ---------- */
IF OBJECT_ID('dw.fact_sales') IS NULL
CREATE TABLE dw.fact_sales (
    sales_key    BIGINT IDENTITY(1,1) PRIMARY KEY,
    order_id     VARCHAR(20) NOT NULL,                 -- degenerate dimension
    date_key     INT NOT NULL REFERENCES dw.dim_date(date_key),
    product_key  INT NOT NULL REFERENCES dw.dim_product(product_key),
    customer_key INT NOT NULL REFERENCES dw.dim_customer(customer_key),
    store_key    INT NOT NULL REFERENCES dw.dim_store(store_key),
    quantity     INT NOT NULL,
    unit_price   DECIMAL(10,2) NOT NULL,
    discount     DECIMAL(4,2)  NOT NULL,
    revenue      DECIMAL(14,2) NOT NULL,
    cost         DECIMAL(14,2) NOT NULL,
    profit       DECIMAL(14,2) NOT NULL,
    CONSTRAINT UQ_fact_sales_order UNIQUE (order_id)
);
GO
