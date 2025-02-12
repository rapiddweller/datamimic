CREATE DATABASE IF NOT EXISTS simple;

DROP TABLE IF EXISTS simple.user;
DROP TABLE IF EXISTS simple.customer;
DROP TABLE IF EXISTS simple.product;

-- Create the "simple.customer" table
CREATE TABLE simple.customer (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tc_creation_src TEXT,
    tc_creation DATETIME NOT NULL,
    tc_update_src TEXT,
    tc_update DATETIME,
    no TEXT NOT NULL,
    name TEXT,
    active BOOLEAN NOT NULL,
    UNIQUE (id)
);

-- Create the "simple.product" table
CREATE TABLE simple.product (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tc_creation_src TEXT,
    tc_creation DATETIME NOT NULL,
    tc_update_src TEXT,
    tc_update DATETIME,
    active BOOLEAN NOT NULL,
    name TEXT,
    description TEXT,
    img_links TEXT,
    shop_link TEXT,
    no TEXT NOT NULL,
    UNIQUE (id)
);

-- Create the "simple.user" table
CREATE TABLE simple.user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    tc_creation_src TEXT,
    tc_creation DATETIME NOT NULL,
    tc_update_src TEXT,
    tc_update DATETIME,
    full_name TEXT,
    email TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    active BOOLEAN,
    superuser BOOLEAN,
    language TEXT,
    customer_id INT,
    FOREIGN KEY (customer_id) REFERENCES simple.customer (id)
);
