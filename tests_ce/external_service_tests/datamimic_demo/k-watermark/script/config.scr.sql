DROP TABLE IF EXISTS watermark;
CREATE TABLE "watermark"(
    id SERIAL PRIMARY KEY,
    key_column VARCHAR NOT NULL,
    value_column TIMESTAMP
);
INSERT INTO watermark (key_column, value_column) VALUES ('last_processed_datetime', '2020-01-01 00:00:00');
