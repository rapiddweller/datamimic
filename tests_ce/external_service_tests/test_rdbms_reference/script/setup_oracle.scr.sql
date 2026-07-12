DECLARE
    count_ref_customers NUMBER;
    count_ref_customers_composite NUMBER;
BEGIN
    SELECT COUNT(*) INTO count_ref_customers FROM user_tables WHERE table_name = 'REF_CUSTOMERS';
    IF count_ref_customers > 0 THEN
        EXECUTE IMMEDIATE 'DROP TABLE REF_CUSTOMERS CASCADE CONSTRAINTS';
    END IF;

    SELECT COUNT(*) INTO count_ref_customers_composite FROM user_tables WHERE table_name = 'REF_CUSTOMERS_COMPOSITE';
    IF count_ref_customers_composite > 0 THEN
        EXECUTE IMMEDIATE 'DROP TABLE REF_CUSTOMERS_COMPOSITE CASCADE CONSTRAINTS';
    END IF;
END;

CREATE TABLE REF_CUSTOMERS (
    customer_id INT PRIMARY KEY,
    tier VARCHAR2(20)
);

CREATE TABLE REF_CUSTOMERS_COMPOSITE (
    cust_id INT PRIMARY KEY,
    region VARCHAR2(20)
);
