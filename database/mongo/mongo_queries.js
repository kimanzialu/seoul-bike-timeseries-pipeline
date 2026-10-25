//Latest record
{ }

// Record of one day range: 1 June 2018
{ "timestamp": { "$gte": ISODate("2018-06-01"), "$lt": ISODate("2018-06-02") } }

// Hot hours
{ "weather.temperature_c": { "$gt": 30 } }

// Average rentals per season
{ "_id": "$season", "avg_rentals": { "$avg": "$rented_bike_count" } }