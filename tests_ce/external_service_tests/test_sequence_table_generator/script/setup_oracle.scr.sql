-- Drop tables if they exist
DECLARE
    count_user NUMBER;
    count_customer NUMBER;
    count_simple_user NUMBER;
BEGIN
    -- Check if "user" table exists
    SELECT COUNT(*)
    INTO count_user
    FROM user_tables
    WHERE table_name = 'USER';

    -- If "user" table exists, drop it
    IF count_user > 0 THEN
        EXECUTE IMMEDIATE 'DROP TABLE "USER" CASCADE CONSTRAINTS';
    END IF;

    -- Check if "customer" table exists
    SELECT COUNT(*)
    INTO count_customer
    FROM user_tables
    WHERE table_name = 'CUSTOMER';

    -- If "customer" table exists, drop it
    IF count_customer > 0 THEN
        EXECUTE IMMEDIATE 'DROP TABLE CUSTOMER CASCADE CONSTRAINTS';
    END IF;

    -- Check if "simple_user" table exists
    SELECT COUNT(*)
    INTO count_simple_user
    FROM user_tables
    WHERE table_name = 'SIMPLE_USER';

    -- If "simple_user" table exists, drop it
    IF count_simple_user > 0 THEN
        EXECUTE IMMEDIATE 'DROP TABLE SIMPLE_USER CASCADE CONSTRAINTS';
    END IF;
END;

-- Create table "CUSTOMER"
CREATE TABLE CUSTOMER (
    id INT PRIMARY KEY,
    tc_creation_src CLOB,
    tc_creation TIMESTAMP NOT NULL,
    tc_update_src CLOB,
    tc_update TIMESTAMP,
    no VARCHAR2(255) NOT NULL,
    name VARCHAR2(255),
    active NUMBER(1,0) NOT NULL
);

-- Create table "USER"
CREATE TABLE "USER" (
    id INT PRIMARY KEY,
    tc_creation_src CLOB,
    tc_creation TIMESTAMP NOT NULL,
    tc_update_src CLOB,
    tc_update TIMESTAMP,
    full_name VARCHAR2(255),
    email VARCHAR2(255) NOT NULL,
    hashed_password VARCHAR2(255) NOT NULL,
    active NUMBER(1,0),
    superuser NUMBER(1,0),
    language VARCHAR2(255),
    customer_id INT,
    CONSTRAINT fk_customer_id FOREIGN KEY (customer_id) REFERENCES CUSTOMER(id)
);

-- Create table "SIMPLE_USER"
CREATE TABLE SIMPLE_USER (
    id INT PRIMARY KEY,
    tc_creation_src CLOB,
    tc_creation TIMESTAMP NOT NULL,
    tc_update_src CLOB,
    tc_update TIMESTAMP,
    full_name VARCHAR2(255),
    email VARCHAR2(255) NOT NULL,
    hashed_password VARCHAR2(255) NOT NULL,
    active NUMBER(1,0),
    superuser NUMBER(1,0),
    language VARCHAR2(255)
);