CREATE SCHEMA IF NOT EXISTS dm_s53_sales;
CREATE SCHEMA IF NOT EXISTS dm_s53_billing;
DROP TABLE IF EXISTS dm_s53_sales.dm_s53_lines;
DROP TABLE IF EXISTS dm_s53_billing.dm_s53_lines;
DROP TABLE IF EXISTS public.dm_s53_lines;
CREATE TABLE public.dm_s53_lines (decoy INTEGER PRIMARY KEY)
