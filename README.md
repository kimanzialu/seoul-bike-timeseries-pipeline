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

## Testing

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
data/
requirements.txt
.env.example
README.md
```

## Team Contributions

This project is developed collaboratively. Refer to the Git commit history and assignment documentation for individual contributions and task allocation.
