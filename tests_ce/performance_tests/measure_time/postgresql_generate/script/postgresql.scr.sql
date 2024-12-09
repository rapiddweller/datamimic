CREATE SCHEMA IF NOT EXISTS simple;

DROP TABLE IF EXISTS simple.time_measure CASCADE;
CREATE TABLE simple.time_measure
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


