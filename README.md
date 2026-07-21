# VigilGrid Backend

Hotspot detection and patrol allocation for RakshaGrid.

## Overview

VigilGrid processes raw crime data, geocodes city names, generates jittered
points for mapping, clusters hotspots with DBSCAN, and serves results through
a FastAPI application.

## Repository Layout

```text
vigilgrid/
  config.py        # tunable values: paths, aliases, DBSCAN params, thresholds
  geocode.py       # city-to-lat/lon lookup and coverage gate
  jitter.py        # synthetic point scatter around city centroids
  data_prep.py     # offline pipeline: raw CSV -> data/processed/points.parquet
  model.py         # online model: loads parquet, runs DBSCAN, ranks hotspots
  app.py           # FastAPI serving layer
  requirements.txt
  data/
    raw/           # place crime_dataset_india.csv and worldcities.csv here
    processed/     # written by data_prep.py; should remain git-ignored
```

## Requirements

- Python 3.10+
- `crime_dataset_india.csv`
- `worldcities.csv`

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### 1. Prepare the data

Run the offline preprocessing step whenever the raw data or city aliases
change:

```bash
python data_prep.py
```

This step generates the k-distance elbow plot used to set
`DBSCAN_EPS_KM` in `config.py`.

### 2. Optionally check the model

```bash
python model.py
```

### 3. Start the API

```bash
uvicorn app:app --reload
```

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check with point and hotspot counts |
| `GET` | `/vigilgrid/hotspots` | Ranked hotspot clusters |
| `GET` | `/vigilgrid/points?limit=5000` | Jittered points for map rendering |
| `GET` | `/vigilgrid/patrol-allocation?n_units=5` | Greedy allocation across top hotspots |

## Configuration

Key settings live in `config.py`:

- `CITY_ALIASES`
- `COVERAGE_THRESHOLD`
- `DBSCAN_EPS_KM`
- path and clustering parameters

## Notes

- `COVERAGE_THRESHOLD` raises a `ValueError` in `data_prep.py` if geocoding
  coverage drops below 98%. If this happens, review the unmatched cities and
  add them to `CITY_ALIASES`.
- The FastAPI app does not rerun geocoding or DBSCAN per request. It loads
  the processed parquet file at startup. Re-run `data_prep.py` and restart
  the API after data changes.

## License

No license has been specified.
