-- Création de la base de données si elle n'existe pas
CREATE DATABASE IF NOT EXISTS airport_db;

-- Utilisation de la base de données
USE airport_db;

-- Suppression de la table si elle existe (optionnel pour repartir de zéro)
DROP TABLE IF EXISTS flights;

-- Création de la table "flights"
CREATE TABLE IF NOT EXISTS flights (
    flight_number VARCHAR(10) NOT NULL PRIMARY KEY,
    origin VARCHAR(100) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    departure_time VARCHAR(5) NOT NULL,
    checkin_counter VARCHAR(5) NOT NULL,
    boarding_gate VARCHAR(5)
);

-- Insertion de 8 vols avec C01, C02 et P01, P02
INSERT INTO flights (flight_number, origin, destination, departure_time, checkin_counter, boarding_gate) 
VALUES 
    ('AF 133', 'Polytech Nantes', 'Dakar', '10:30', 'C01', 'P02'),
    ('AF 18', 'Polytech Nantes', 'Tokyo', '11:00', 'C02', 'P01'),
    ('AA 202', 'Polytech Nantes', 'New York', '14:15', 'C01', 'P01'),
    ('AF 09', 'Polytech Nantes', 'Lomé', '16:00', 'C02', 'P02'),
    ('DL 107', 'Polytech Nantes', 'Cotonou', '09:45', 'C01', 'P01'),
    ('BR 718', 'Polytech Nantes', 'Johannesburg', '12:20', 'C01', 'P02'),
    ('EK 57', 'Polytech Nantes', 'Rio de Janeiro', '18:00', 'C02', 'P01'),
    ('AF 39', 'Polytech Nantes', 'Guangzhou', '19:30', 'C02', 'P02');
