CREATE SCHEMA IF NOT EXISTS source;
DROP TABLE IF EXISTS source.customer CASCADE;
CREATE TABLE source.customer
(
    id              SERIAL  NOT NULL,
    tc_creation_src VARCHAR,
    tc_creation     TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    tc_update_src   VARCHAR,
    tc_update       TIMESTAMP WITHOUT TIME ZONE,
    no              VARCHAR NOT NULL,
    name            VARCHAR,
    active          BOOLEAN NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (id)
);

DROP TABLE IF EXISTS source.product CASCADE;
CREATE TABLE source.product
(
    id              SERIAL  NOT NULL,
    tc_creation_src VARCHAR,
    tc_creation     TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    tc_update_src   VARCHAR,
    tc_update       TIMESTAMP WITHOUT TIME ZONE,
    active          BOOLEAN NOT NULL,
    name            VARCHAR,
    description     VARCHAR,
    img_links       JSON,
    shop_link       VARCHAR,
    no              VARCHAR,
    PRIMARY KEY (id),
    UNIQUE (id)
);

DROP TABLE IF EXISTS source.user CASCADE;
CREATE TABLE source.user
(
    id              SERIAL  NOT NULL,
    tc_creation_src VARCHAR,
    tc_creation     TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    tc_update_src   VARCHAR,
    tc_update       TIMESTAMP WITHOUT TIME ZONE,
    full_name       VARCHAR,
    email           VARCHAR NOT NULL,
    hashed_password VARCHAR NOT NULL,
    active          BOOLEAN,
    superuser       BOOLEAN,
    language        VARCHAR,
    customer_id     INTEGER,
    PRIMARY KEY (id),
    FOREIGN KEY (customer_id) REFERENCES source.customer (id) ON DELETE CASCADE,
    UNIQUE (id)
);


