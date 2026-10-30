# Seoul Bike Sharing Demand — Time-Series Analysis and Forecasting

## ** Task 1: Preprocessing, Exploratory Analysis and Machine Learning**

## 1. Project overview

This project analyzes hourly bicycle-rental demand in Seoul, South Korea, and trains a **one-hour-ahead Random Forest forecasting model**. It covers Task 1: A (data understanding and preprocessing), B (five analytical questions), and C (model training and evaluation).


## 2. Dataset

- **Name:** Seoul Bike Sharing Demand
- **Source:** [Kaggle dataset](https://www.kaggle.com/datasets/waleedejaz/seoul-bike-sharing-demand)
- **Input file:** `SeoulBikeData.csv` 
- **Granularity:** Hourly
- **Size:** 8,760 observations and 14 original columns
- **Target:** `rented_bike_count` — hourly number of bicycles rented

**Data quality:** No missing cells, duplicate rows, duplicate timestamps, or missing hourly timestamps were detected. The 295 zero-rental observations during non-functioning periods were retained because they are valid records, not missing data.

The notebook converts the separate date and hour columns into a timestamp, standardizes column names, and saves a cleaned CSV suitable for subsequent database work.

## 3. Tools and dependencies

Python, Pandas, NumPy, Matplotlib, Seaborn, Scikit-learn, Joblib, and Jupyter Notebook / Google Colab.

For local execution, use Python 3.10+ and install the dependencies:

```bash
python -m pip install -r requirements.txt
```

Google Colab provides its own `google.colab` tools for Drive mounting and manual uploads. These are **not** required for local execution.

## 4. How to run

### Google Colab (recommended)

1. Open [Google Colab](https://colab.research.google.com/) and select **File → Upload notebook**.
2. Upload `notebooks/Seoul_Bike_Hourly_Demand.ipynb` 
3. Select **Runtime → Run all**.
4. Authorize the Google Drive mount when prompted.
5. **Manually select `SeoulBikeData.csv`** when the notebook displays the file-upload prompt.
6. All input and output files are saved automatically to **My Drive → Seoul_Bike_Task1**.


### Local Jupyter / VS Code

Place the CSV in `data/raw/SeoulBikeData.csv`, install `requirements.txt`, and run all notebook cells. The notebook accepts execution from the project root or its `notebooks/` folder; outputs are saved locally rather than to Google Drive.

## 5. Project structure

```text
Seoul_Bike_Task1/
├── README.md
├── requirements.txt
├── notebooks/
│   └── Seoul_Bike_Hourly_Demand.ipynb
├── data/
│   ├── raw/SeoulBikeData.csv
│   └── processed/cleaned_seoul_bike.csv
├── outputs/
│   ├── figures/        # 10 generated PNG charts
│   └── tables/         # Statistics, findings, experiments and predictions
├── models/
│   └── seoul_bike_rf_one_hour.joblib
└── report/
    └── Task1_Auto_Charts_and_Findings.pdf
```

The output folders and their generated files are created automatically when the notebook runs.

## 6. Methodology

**A — Data preprocessing and exploration:** Load the manually uploaded CSV, parse timestamps, check missing/duplicate data and hourly continuity, calculate descriptive statistics, and explore rental distributions, seasons, operating status and variable correlations.

**B — Five analytical questions:**

1. How does rental demand change over the year? (daily totals and monthly patterns)
2. At what times of day is demand highest? (hourly averages)
3. How is temperature associated with demand? (scatter plots, bins and Pearson correlation)
4. Do historical rental counts relate to current demand? (1h, 24h and 168h lags)
5. Do past-only moving averages reveal demand patterns? (24h and 168h rolling averages)

Each analytical question has a visualization and an interpretation in the notebook.

**C — Machine learning:** Generate 15 time/calendar, historical-demand, rolling and lagged-weather features. Use 85% of model-ready observations for development and the last 15% for chronological holdout testing. Compare three Random Forest configurations using **three-fold forward-time cross-validation** and select the one with the lowest mean validation MAE. Evaluate against a naive previous-hour baseline and save the trained model using Joblib.

All predictive lag and moving-average features use **past observations only** to reduce data leakage.

## 7. Results from the completed Google Colab run

| Metric | Result |
|---|---:|
| Model-ready rows | 8,592 |
| Development / holdout test rows | 7,303 / 1,289 |
| Best model | Random Forest `RF_2` |
| Hyperparameters | 140 trees; max depth 14; min leaf 2 |
| Cross-validation MAE | 185.52 bicycles/hour |
| Test MAE | **69.63 bicycles/hour** |
| Test RMSE | **108.06 bicycles/hour** |
| Test R² | **0.963** |
| Naive previous-hour baseline MAE | 206.06 bicycles/hour |
| Illustrative next-hour forecast | 430.4 bicycles for 01 Dec 2018 00:00 |

The model evaluation is based on the **historical 2018 holdout period**. The next-hour example is an illustrative forecast without an observed value for verification, not a present-day forecast. Future accuracy is not guaranteed.

## 8. Key output files

- `data/processed/cleaned_seoul_bike.csv` — cleaned dataset to share with database teammates.
- `outputs/figures/` — ten figures, including Q1–Q5 visualizations, predicted vs. observed rentals, and feature importance.
- `outputs/tables/data_quality_checks.csv` and `descriptive_statistics.csv` — preprocessing and summary statistics.
- `outputs/tables/analytical_findings.json` — the five questions, methods and interpretations.
- `outputs/tables/experiment_results.csv` — the three hyperparameter experiments.
- `outputs/tables/model_metrics.json` and `test_predictions.csv` — held-out evaluation.
- `outputs/tables/next_hour_forecast.json` — example forecast.
- `models/seoul_bike_rf_one_hour.joblib` — saved model and feature-order metadata.
- `report/Task1_Auto_Charts_and_Findings.pdf` — automatically generated **supporting** findings pack (not the complete group report).
