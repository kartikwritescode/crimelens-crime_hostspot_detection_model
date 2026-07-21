"""
VigilGrid — geocoding

Encapsulates every lesson learned the hard way while building this pipeline:
  1. Use `city_ascii`, not `city` — SimpleMaps stores South Asian city names
     with diacritics (e.g. "Hyderābād"), which silently fails to match plain
     ASCII city names and can even mismatch you onto a same-named city in a
     different country.
  2. Dedupe the lookup table BEFORE merging, or a left-merge onto a table
     with duplicate city rows silently multiplies your row count.
  3. Apply aliases BEFORE merging, not after.
  4. Gate on a coverage threshold instead of silently proceeding — a merge
     that "succeeds" with 60% coverage is a bug, not a result.
"""
import logging
import pandas as pd

logger = logging.getLogger("vigilgrid.geocode")


def load_india_city_lookup(world_cities_path) -> pd.DataFrame:
    """Load a deduplicated India city -> lat/lon lookup from a SimpleMaps-style
    worldcities.csv. Uses city_ascii (not city) to avoid diacritic mismatches."""
    world_cities = pd.read_csv(world_cities_path)[["city_ascii", "lat", "lng", "country"]]
    india = world_cities[world_cities["country"] == "India"][["city_ascii", "lat", "lng"]].copy()
    india = india.rename(columns={"city_ascii": "city"})
    india["city"] = india["city"].str.strip().str.title()

    dupes = india["city"].duplicated().sum()
    if dupes:
        logger.warning("Dropping %d duplicate city rows from lookup table", dupes)
    india = india.drop_duplicates(subset="city", keep="first")

    logger.info("Loaded %d unique India city coordinates", len(india))
    return india


def geocode_crimes(df: pd.DataFrame, city_lookup: pd.DataFrame, aliases: dict) -> pd.DataFrame:
    """Merge lat/lon onto crime rows by city name. Asserts row count is
    unchanged — a change means the lookup table still has duplicates."""
    df = df.copy()
    original_len = len(df)

    df["City"] = df["City"].str.strip().str.title()
    df["City"] = df["City"].replace(aliases)

    df = df.merge(city_lookup, left_on="City", right_on="city", how="left", suffixes=("", "_dup"))

    assert len(df) == original_len, (
        f"Merge changed row count: {original_len} -> {len(df)} "
        f"— the lookup table likely has duplicate city names"
    )
    assert "lat" in df.columns, f"Merge produced unexpected columns: {df.columns.tolist()}"

    return df


def coverage_report(df: pd.DataFrame) -> tuple[float, pd.Series]:
    total = len(df)
    missing = df["lat"].isna().sum()
    coverage = 1 - missing / total
    by_city = df.loc[df["lat"].isna(), "City"].value_counts()
    return coverage, by_city


def enforce_coverage_gate(df: pd.DataFrame, threshold: float) -> float:
    """Raises if geocode coverage falls below threshold, logging exactly
    which cities are unresolved so the fix is a quick alias-map addition,
    not another debugging session."""
    coverage, by_city = coverage_report(df)
    logger.info("Geocode coverage: %.2f%%", coverage * 100)
    if coverage < threshold:
        logger.error("Unmatched cities:\n%s", by_city)
        raise ValueError(
            f"Geocode coverage {coverage:.1%} below threshold {threshold:.0%} — "
            f"add aliases for: {by_city.index.tolist()}"
        )
    return coverage
