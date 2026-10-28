# Seoul Bike Time-Series Pipeline

A team project using the Seoul Bike Sharing Demand dataset to explore time-series data, store it in SQL and NoSQL databases, expose API endpoints, and support time-series prediction.

## Technologies

- Python
- FastAPI
- MySQL
- MongoDB
- Pandas
- SQLAlchemy
- PyMongo

## Prerequisites

Install Python, MySQL Server, and MongoDB. Make sure both database services are running before starting the application.

## Installation and Configuration

1. Clone the repository and enter the project directory.
2. Install the Python dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and configure the database connection settings.
4. Create the SQL database and tables using `database/sql/schema.sql`.

## Database Setup — Task 2

Load the dataset into MySQL:

```bash
python database/loaders/load_sql.py
```

Load the dataset into MongoDB using the safe loader:

```bash
python database/loaders/load_mongo_safe.py
```

**Note:** The original `database/loaders/load_mongo.py` may drop the existing MongoDB collection. Use the safe loader when you want to avoid that behavior.

## Running the API — Task 3

Start the FastAPI development server from the project root:

```bash
uvicorn app.main:app --reload
```

The API should be available at:

- API base URL: `http://127.0.0.1:8000`
- Interactive API documentation: `http://127.0.0.1:8000/docs`

## API Endpoints

### SQL API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/bikes` | List bike records |
| GET | `/api/bikes/latest` | Retrieve the latest record |
| GET | `/api/bikes/range` | Retrieve records within a timestamp range |
| GET | `/api/bikes/{record_id}` | Retrieve a record by ID |
| POST | `/api/bikes` | Create a record |
| PUT | `/api/bikes/{record_id}` | Update a record |
| DELETE | `/api/bikes/{record_id}` | Delete a record |

### MongoDB API

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/mongo/bikes` | List bike records |
| GET | `/api/mongo/bikes/latest` | Retrieve the latest record |
| GET | `/api/mongo/bikes/range` | Retrieve records within a timestamp range |
| GET | `/api/mongo/bikes/{record_id}` | Retrieve a record by ID |
| POST | `/api/mongo/bikes` | Create a record |
| PUT | `/api/mongo/bikes/{record_id}` | Update a record |
| DELETE | `/api/mongo/bikes/{record_id}` | Delete a record |

## Forecasting Script — Task 4

`forecasting/predict.py` runs the whole pipeline in one command:

1. **Fetch.** It calls `GET /latest`, then `GET /range` on the API to pull the last 168 hourly records (one week, the longest lag the model uses). Pass `--source sql` for MySQL or `--source mongo` for MongoDB.
2. **Preprocess.** It applies the Task 1 cleaning checks (required fields, timestamp parsing, non-negative target, duplicate removal, a continuous hourly grid) and then builds features with the same `make_forecasting_features` function used in training: calendar and cyclical hour features, 1h/24h/168h lags, 24h/168h past-only moving averages, and the previous hour's weather.
3. **Load the model.** It loads `models/seoul_bike_rf_one_hour.joblib` and checks that the feature columns match.
4. **Predict.** It forecasts `rented_bike_count` for the next hour, prints the result and saves a JSON report to `outputs/predictions/`.

With the API running:

```bash
python -m forecasting.predict                            # next hour after the latest record (MySQL)
python -m forecasting.predict --source mongo             # same, through MongoDB
python -m forecasting.predict --at "2018-11-30 18:00"    # backtest: forecast a known hour and show the error
```

Example output:

```text
[1/4] Fetching history from the MONGO API: 2018-11-23 18:00:00 -> 2018-11-30 17:00:00
      received 168 records
[2/4] Preprocessing (Task 1 cleaning + lag / rolling-mean features)
[3/4] Loading model: seoul_bike_rf_one_hour.joblib
[4/4] Forecast for 2018-11-30 18:00: 1387 bikes rented
      actual: 1384  |  absolute error: 3
```

**Missing data.** The original dataset has no missing hours, but CRUD deletes can leave gaps. Up to 3 missing hours (change with `--max-gap-fill`) are filled by time interpolation, and the filled hours are listed in the JSON report. With more gaps than that, the script stops instead of feeding invented history to the lag features.

**Model file.** If `models/seoul_bike_rf_one_hour.joblib` is missing, copy in the one saved by the Task 1 notebook or rebuild it from the CSV with the same experiments (RF_1–RF_3, TimeSeriesSplit, selected by CV MAE):

```bash
python -m forecasting.train_model
```

### Tests

The tests run the real FastAPI routes against in-memory SQLite and mongomock, so neither database needs to be running:

```bash
pip install -r requirements-dev.txt
python -m pytest tests
```

They check that prediction-time features match the training features exactly, that the pipeline runs end to end through both the SQL and MongoDB APIs, that the two APIs give the same forecast, and that records deleted through the API are handled.

## Testing the API

1. Start the API server.
2. Open `http://127.0.0.1:8000/docs` in your browser.
3. Expand an endpoint and select **Try it out**.
4. Enter the required parameters or request body, then select **Execute**.
5. Verify the HTTP response and returned data.

## Project Structure

```text
app/
  main.py
  models.py
  schemas.py
  database/
  routes/
database/
  loaders/
  mongo/
  sql/
forecasting/          # Task 4
  api_client.py       # calls the SQL / MongoDB API endpoints
  preprocessing.py    # Task 1 cleaning + feature engineering (shared by train & predict)
  train_model.py      # rebuilds the model bundle from the CSV
  predict.py          # end-to-end forecast script
models/               # trained model (joblib)
outputs/predictions/  # JSON forecast reports
tests/                # end-to-end tests for Task 4
data/
requirements.txt
requirements-dev.txt
.env.example
README.md
```

## Team Contributions

This project is developed collaboratively. Refer to the Git commit history and assignment documentation for individual contributions and task allocation.
