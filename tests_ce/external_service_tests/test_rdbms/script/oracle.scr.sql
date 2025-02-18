-- Check for existing database is not directly possible in Oracle during script execution; typically handled at the DBA level

-- Drop tables if they exist (handled differently in Oracle as it does not have IF EXISTS clause)
BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE ORACLE_USER PURGE';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN
         RAISE;
      END IF;
END;
BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE ORACLE_CUSTOMER PURGE';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN
         RAISE;
      END IF;
END;
BEGIN
   EXECUTE IMMEDIATE 'DROP TABLE ORACLE_PRODUCT PURGE';
EXCEPTION
   WHEN OTHERS THEN
      IF SQLCODE != -942 THEN
         RAISE;
      END IF;
END;

-- Sequence and Trigger creation for auto-increment behavior
DECLARE
    v_seq_count_customer NUMBER;
BEGIN
    -- Check and handle oracle_customer_seq
    SELECT COUNT(*)
    INTO v_seq_count_customer
    FROM user_objects
    WHERE object_type = 'SEQUENCE'
    AND object_name = 'ORACLE_CUSTOMER_SEQ';

    IF v_seq_count_customer = 0 THEN
        EXECUTE IMMEDIATE 'CREATE SEQUENCE ORACLE_CUSTOMER_SEQ';
    ELSE
        EXECUTE IMMEDIATE 'ALTER SEQUENCE ORACLE_CUSTOMER_SEQ RESTART';
    END IF;
END;

DECLARE
    v_seq_count_product NUMBER;
BEGIN
    -- Check and handle oracle_product_seq
    SELECT COUNT(*)
    INTO v_seq_count_product
    FROM user_objects
    WHERE object_type = 'SEQUENCE'
    AND object_name = 'ORACLE_PRODUCT_SEQ';

    IF v_seq_count_product = 0 THEN
        EXECUTE IMMEDIATE 'CREATE SEQUENCE ORACLE_PRODUCT_SEQ';
    ELSE
        EXECUTE IMMEDIATE 'ALTER SEQUENCE ORACLE_PRODUCT_SEQ RESTART';
    END IF;
END;

DECLARE
    v_seq_count_user NUMBER;
BEGIN
    -- Check and handle oracle_user_seq
    SELECT COUNT(*)
    INTO v_seq_count_user
    FROM user_objects
    WHERE object_type = 'SEQUENCE'
    AND object_name = 'ORACLE_USER_SEQ';

    IF v_seq_count_user = 0 THEN
        EXECUTE IMMEDIATE 'CREATE SEQUENCE ORACLE_USER_SEQ';
    ELSE
        EXECUTE IMMEDIATE 'ALTER SEQUENCE ORACLE_USER_SEQ RESTART';
    END IF;
END;

-- Create the "oracle_customer" table
CREATE TABLE oracle_customer (
    id INT DEFAULT oracle_customer_seq.NEXTVAL PRIMARY KEY,
    tc_creation_src VARCHAR2(4000),
    tc_creation TIMESTAMP NOT NULL,
    tc_update_src VARCHAR2(4000),
    tc_update TIMESTAMP,
    no VARCHAR2(255) NOT NULL,
    name VARCHAR2(255),
    active NUMBER(1) NOT NULL CHECK (active IN (0, 1)) -- assuming BOOLEAN maps to NUMBER
);

-- Create the "oracle_product" table
CREATE TABLE oracle_product (
    id INT DEFAULT oracle_product_seq.NEXTVAL PRIMARY KEY,
    tc_creation_src VARCHAR2(4000),
    tc_creation TIMESTAMP NOT NULL,
    tc_update_src VARCHAR2(4000),
    tc_update TIMESTAMP,
    active NUMBER(1) NOT NULL CHECK (active IN (0, 1)), -- assuming BOOLEAN maps to NUMBER
    name VARCHAR2(4000),
    description VARCHAR2(4000),
    img_links VARCHAR2(4000),
    shop_link VARCHAR2(4000),
    no VARCHAR2(255) NOT NULL
);

-- Create the "oracle_user" table
CREATE TABLE oracle_user (
    id INT DEFAULT oracle_user_seq.NEXTVAL PRIMARY KEY,
    tc_creation_src VARCHAR2(4000),
    tc_creation TIMESTAMP NOT NULL,
    tc_update_src VARCHAR2(4000),
    tc_update TIMESTAMP,
    full_name VARCHAR2(255),
    email VARCHAR2(255) NOT NULL,
    hashed_password VARCHAR2(4000) NOT NULL,
    active NUMBER(1) CHECK (active IN (0, 1)), -- assuming BOOLEAN maps to NUMBER
    superuser NUMBER(1) CHECK (superuser IN (0, 1)), -- assuming BOOLEAN maps to NUMBER
    language VARCHAR2(255),
    customer_id INT,
    FOREIGN KEY (customer_id) REFERENCES oracle_customer (id)
);
