USE seoul_bike;
SELECT COUNT(*) AS total_rows FROM bike_rentals;

SELECT * FROM bike_rentals ORDER BY timestamp DESC LIMIT 1;

SELECT s.season_name, ROUND(AVG(b.rented_bike_count),1) AS avg_rentals
FROM bike_rentals b
JOIN seasons s ON b.season_id = s.season_id
GROUP BY s.season_name
ORDER BY avg_rentals DESC;

SELECT (w.rainfall_mm > 0) AS is_raining, ROUND(AVG(b.rented_bike_count),1) AS avg_rentals
FROM bike_rentals b
JOIN weather_readings w ON b.rental_id = w.rental_id
GROUP BY is_raining;

SELECT b.timestamp, b.rented_bike_count, w.temperature_c
FROM bike_rentals b
JOIN weather_readings w ON b.rental_id = w.rental_id
WHERE b.timestamp BETWEEN '2018-06-01 00:00:00' AND '2018-06-01 23:00:00';
