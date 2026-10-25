# seoul-bike-timeseries-pipeline

## Database setup (Task 2)
1. Install MySQL and MongoDB.
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your MySQL password.
4. Run `database/sql/schema.sql` in MySQL Workbench.
5. `python database/loaders/load_sql.py`
6. `python database/loaders/load_mongo.py`
