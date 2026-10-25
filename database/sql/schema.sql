DROP DATABASE IF EXISTS seoul_bike;
CREATE DATABASE seoul_bike;
USE seoul_bike;

CREATE TABLE seasons (
  season_id   INT AUTO_INCREMENT PRIMARY KEY,
  season_name VARCHAR(20) NOT NULL UNIQUE
);

CREATE TABLE bike_rentals (
  rental_id         INT AUTO_INCREMENT PRIMARY KEY,
  timestamp         DATETIME NOT NULL UNIQUE,
  rented_bike_count INT NOT NULL,
  season_id         INT NOT NULL,
  holiday           ENUM('Holiday','No Holiday') NOT NULL,
  functioning_day   ENUM('Yes','No') NOT NULL,
  FOREIGN KEY (season_id) REFERENCES seasons(season_id),
  INDEX idx_timestamp (timestamp)
);

CREATE TABLE weather_readings (
  weather_id        INT AUTO_INCREMENT PRIMARY KEY,
  rental_id         INT NOT NULL UNIQUE,
  temperature_c     FLOAT,
  humidity_pct      INT,
  wind_speed_ms     FLOAT,
  visibility_10m    INT,
  dew_point_c       FLOAT,
  solar_radiation   FLOAT,
  rainfall_mm       FLOAT,
  snowfall_cm       FLOAT,
  FOREIGN KEY (rental_id) REFERENCES bike_rentals(rental_id) ON DELETE CASCADE
);