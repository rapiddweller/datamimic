-- Create table business_mapping if it does not exist
CREATE TABLE IF NOT EXISTS business_mapping (
    idTop INTEGER PRIMARY KEY,
    idSub INTEGER,
    countryCode TEXT,
    city TEXT,
    postCode TEXT,
    description TEXT,
    title TEXT,
    title_description TEXT
);

-- Ensure table is empty before inserting data
DELETE FROM business_mapping;