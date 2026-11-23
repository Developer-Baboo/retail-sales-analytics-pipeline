/* Retail Sales Analytics - SQL Server (T-SQL) setup. Run in SSMS. */
IF DB_ID('RetailDW') IS NULL CREATE DATABASE RetailDW;
GO
USE RetailDW;
GO
IF SCHEMA_ID('etl') IS NULL EXEC('CREATE SCHEMA etl');  -- staging + logging
IF SCHEMA_ID('dw')  IS NULL EXEC('CREATE SCHEMA dw');   -- star schema (OLAP model)
GO
