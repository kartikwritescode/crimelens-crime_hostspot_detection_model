import logging

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors

import config
from geocode import enforce_coverage_gate, geocode_crimes, load_india_city_lookup
from jitter import jitter_points

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("vigilgrid.data_prep")


df = pd.read_csv(config.RAW_CRIME_CSV)
original_row_count = len(df)
logger.info("Loaded %d raw crime records", original_row_count)


df["Date of Occurrence"] = pd.to_datetime(df["Date of Occurrence"], format="%m-%d-%Y %H:%M")
df["Date Reported"] = pd.to_datetime(df["Date Reported"], format="%d-%m-%Y %H:%M")
df["Time of Occurrence"] = pd.to_datetime(df["Time of Occurrence"], format="%d-%m-%Y %H:%M")

bad_order = df[df["Date of Occurrence"] > df["Date Reported"]]
if len(bad_order) > 0:
    logger.warning("%d rows have occurrence AFTER report date — investigate before trusting dates", len(bad_order))

# NaN in Date Case Closed means "case still open" — a real value, not
# missing data. Make that explicit instead of leaving an ambiguous null.


df["is_case_closed"] = df["Case Closed"] == "Yes"




city_lookup = load_india_city_lookup(config.WORLD_CITIES_CSV)
df = geocode_crimes(df, city_lookup, config.CITY_ALIASES)
enforce_coverage_gate(df, config.COVERAGE_THRESHOLD)


unresolved = df[df["lat"].isna()]
if len(unresolved) > 0:
    config.QUARANTINE_CSV.parent.mkdir(parents=True, exist_ok=True)
    unresolved.to_csv(config.QUARANTINE_CSV, index=False)
    logger.info(
        "Quarantined %d unresolved rows (%.2f%%) -> %s",
        len(unresolved), len(unresolved) / original_row_count * 100, config.QUARANTINE_CSV,
    )

df = df.dropna(subset=["lat", "lng"]).copy()



df = jitter_points(df, config.CITY_TIER_SPREAD_KM, config.DEFAULT_SPREAD_KM, seed=config.JITTER_RANDOM_SEED)



coords = np.radians(df[["lat_j", "lon_j"]].values)
neighbors = NearestNeighbors(n_neighbors=config.DBSCAN_MIN_PTS, metric="haversine", algorithm="ball_tree").fit(coords)
distances, _ = neighbors.kneighbors(coords)
k_dist = np.sort(distances[:, -1]) * 6371  # radians -> km

plt.plot(k_dist)
plt.ylabel(f"distance to {config.DBSCAN_MIN_PTS}th nearest neighbor (km)")
plt.xlabel("points sorted by distance")
plt.title("Read the elbow, set DBSCAN_EPS_KM in config.py")
plt.show()


# %%
processed = df[
    [
        "Report Number", "Date of Occurrence", "Date Reported", "City",
        "Crime Description", "Crime Domain", "Victim Age", "Victim Gender",
        "Weapon Used", "Police Deployed", "is_case_closed",
        "lat_j", "lon_j",
    ]
].rename(columns={"lat_j": "lat", "lon_j": "lon"})

config.PROCESSED_POINTS.parent.mkdir(parents=True, exist_ok=True)
processed.to_parquet(config.PROCESSED_POINTS, index=False)
logger.info("Saved %d processed points -> %s", len(processed), config.PROCESSED_POINTS)
