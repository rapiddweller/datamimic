-- Drop exists tables
DROP TABLE IF EXISTS hospital;
DROP TABLE IF EXISTS patient;
DROP TABLE IF EXISTS bill;

CREATE TABLE hospital (
    hospital_id INTEGER PRIMARY KEY,
    hospital_name TEXT NOT NULL,
    location TEXT NOT NULL,
    number_of_beds INTEGER NOT NULL
);

CREATE TABLE patient (
    patient_id INTEGER PRIMARY KEY,
    patient_name TEXT NOT NULL,
    age INTEGER NOT NULL,
    gender TEXT NOT NULL,
    hospital_id INTEGER NOT NULL,
    diagnosis TEXT NOT NULL
);

CREATE TABLE bill (
    bill_id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    date TEXT NOT NULL,
    payment_method TEXT NOT NULL
);