-- SQLite does not support schemas, so we remove "simple." prefix
-- Also, CASCADE in DROP TABLE is not supported in SQLite

DROP TABLE IF EXISTS customer;
CREATE TABLE customer
(
    id              INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    tc_creation_src VARCHAR,
    tc_creation     TIMESTAMP NOT NULL,
    tc_update_src   VARCHAR,
    tc_update       TIMESTAMP,
    no              VARCHAR NOT NULL,
    name            VARCHAR,
    active          INTEGER NOT NULL,  -- BOOLEAN as INTEGER
    UNIQUE (id)
);

DROP TABLE IF EXISTS product;
CREATE TABLE product
(
    id              INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    tc_creation_src VARCHAR,
    tc_creation     TIMESTAMP NOT NULL,
    tc_update_src   VARCHAR,
    tc_update       TIMESTAMP,
    active          INTEGER NOT NULL,  -- BOOLEAN as INTEGER
    name            VARCHAR,
    description     VARCHAR,
    img_links       TEXT,  -- Using TEXT to store JSON
    shop_link       VARCHAR,
    no              VARCHAR,
    UNIQUE (id)
);

DROP TABLE IF EXISTS user;
CREATE TABLE user
(
    id              INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    tc_creation_src VARCHAR,
    tc_creation     TIMESTAMP NOT NULL,
    tc_update_src   VARCHAR,
    tc_update       TIMESTAMP,
    full_name       VARCHAR,
    email           VARCHAR NOT NULL,
    hashed_password VARCHAR NOT NULL,
    active          INTEGER,  -- BOOLEAN as INTEGER
    superuser       INTEGER,  -- BOOLEAN as INTEGER
    language        VARCHAR,
    customer_id     INTEGER,
    FOREIGN KEY (customer_id) REFERENCES customer (id) ON DELETE CASCADE,
    UNIQUE (email),
    UNIQUE (id)
);
