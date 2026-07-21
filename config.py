"""
VigilGrid — configuration
All tunables live here so nothing is hardcoded inside the pipeline logic.
Override any of these via environment variables when deploying (e.g. Docker,
a different machine, staging vs prod).
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# ---- paths ----
RAW_CRIME_CSV = Path(os.getenv("VG_RAW_CSV", BASE_DIR / "data" / "raw" / "crime_dataset_india.csv"))
WORLD_CITIES_CSV = Path(os.getenv("VG_WORLD_CITIES_CSV", BASE_DIR / "data" / "raw" / "worldcities.csv"))
PROCESSED_POINTS = Path(os.getenv("VG_PROCESSED_POINTS", BASE_DIR / "data" / "processed" / "points.parquet"))
QUARANTINE_CSV = Path(os.getenv("VG_QUARANTINE_CSV", BASE_DIR / "data" / "processed" / "quarantine_unmatched_geocodes.csv"))


COVERAGE_THRESHOLD = float(os.getenv("VG_COVERAGE_THRESHOLD", 0.98))


CITY_ALIASES = {
    "Nashik": "Nasik",
    "Vasai": "Vasai-Virar",
    "Visakhapatnam": "Vishakhapatnam",
}

#  synthetic point scatter (jitter) 
# Larger metros get a wider spread so the point cloud looks proportionate
CITY_TIER_SPREAD_KM = {
    "Mumbai": 15,
    "Delhi": 15,
    "Bangalore": 12,
    "Chennai": 12,
}
DEFAULT_SPREAD_KM = 6
JITTER_RANDOM_SEED = 42  # fixed seed = reproducible output across re-runs

DBSCAN_EPS_KM = float(os.getenv("VG_EPS_KM", 4.2))
DBSCAN_MIN_PTS = int(os.getenv("VG_MIN_PTS", 15))

# patrol allocation 
DEFAULT_PATROL_UNITS = int(os.getenv("VG_PATROL_UNITS", 5))
