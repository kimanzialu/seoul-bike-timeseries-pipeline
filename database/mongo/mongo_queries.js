//1. Latest record
// Filter: { }    Sort: { "timestamp": -1 }    Limit: 1
{ }

// 2. Record of one day range: 1 June 2018
// Filter:
{ "timestamp": { "$gte": ISODate("2018-06-01"), "$lt": ISODate("2018-06-02") } }

// 3. Hot hours
// Filter:
{ "weather.temperature_c": { "$gt": 30 } }

// 4. Average rentals per season
// Aggregations tab, $group stage:
{ "_id": "$season", "avg_rentals": { "$avg": "$rented_bike_count" } }