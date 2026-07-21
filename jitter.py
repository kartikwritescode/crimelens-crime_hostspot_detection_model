"""
VigilGrid — synthetic point scattering

The source dataset only gives a city name per crime, not exact coordinates,
so each record is scattered into a believable point cloud around its city's
centroid. A fixed random seed makes this deterministic — re-running
data_prep.py twice on the same input produces identical output, which
matters for debugging and for keeping the DBSCAN results stable.
"""
import numpy as np
import pandas as pd


def jitter_points(
    df: pd.DataFrame,
    city_tier_spread: dict,
    default_spread_km: float,
    seed: int | None = 42,
) -> pd.DataFrame:
    df = df.copy()
    rng = np.random.default_rng(seed)

    def _jitter(row):
        spread_deg = city_tier_spread.get(row["City"], default_spread_km) * 0.009
        return (
            row["lat"] + rng.normal(0, spread_deg),
            row["lng"] + rng.normal(0, spread_deg),
        )

    jittered = df.apply(_jitter, axis=1, result_type="expand")
    df["lat_j"], df["lon_j"] = jittered[0], jittered[1]
    return df
