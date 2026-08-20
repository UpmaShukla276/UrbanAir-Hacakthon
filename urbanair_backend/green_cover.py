

import math
import numpy as np
import rasterio
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

TREE_COVER_RASTER = BASE_DIR / "DelhiNCR_TreeCover_2021.tif"


GREEN_SPACE_BENCHMARK_SQM_PER_CAPITA = 9.0


AVG_MATURE_TREE_CANOPY_SQM = 20.0


ANALYSIS_RADIUS_KM = 2.0


POPULATION_DENSITY = {
    # NCR cities (own district, Census 2011)
    "Faridabad": 2442,
    "Ghaziabad": 3971,
    "Gurgaon": 1241,
    "Noida": 1286,

    # Delhi -- generic city-average fallback
    "Delhi": 11320,

    # North East Delhi district (37,346/km²) -- inner dense East Delhi
    "Anand Vihar": 37346,
    "Vivek Vihar": 37346,

    # North West Delhi district (8,254/km²) -- outer Delhi
    "Rohini": 8254,
    "Bawana": 8254,
    "Narela": 8254,
    "Jahangirpuri": 8254,
    "Mundka": 8254,

    # West Delhi district (19,563/km²)
    "Ashok Vihar": 19563,
    "Wazirpur": 19563,
    "Punjabi Bagh": 19563,
    "Dwarka": 19563,
    "R.K. Puram": 19563,
    "Okhla": 19563,

   
    "Chandni Chowk": 4057,
    "Red Fort": 4057,
    "Connaught Place": 4057,
}


def tree_cover_fraction(lat, lon, radius_km=ANALYSIS_RADIUS_KM):
    """Reads the tree-cover raster in a window around (lat, lon) and
    computes the fraction of pixels classified as tree cover within a
    circular buffer of the given radius."""
    with rasterio.open(TREE_COVER_RASTER) as src:
        # Convert radius to degrees (approximate, fine at this scale)
        deg_buffer = radius_km / 111.0
        window = rasterio.windows.from_bounds(
            lon - deg_buffer, lat - deg_buffer, lon + deg_buffer, lat + deg_buffer,
            transform=src.transform
        )
        window = window.round_lengths().round_offsets()
        arr = src.read(1, window=window)
        win_transform = src.window_transform(window)

        if arr.size == 0:
            return 0.0, 0.0

        rows, cols = arr.shape
        # Build lat/lon grid for this window to apply circular mask
        xs = win_transform.c + (np.arange(cols) + 0.5) * win_transform.a
        ys = win_transform.f + (np.arange(rows) + 0.5) * win_transform.e

        lon_grid, lat_grid = np.meshgrid(xs, ys)
        # Approximate distance in km (equirectangular, fine at NCR scale)
        dlat_km = (lat_grid - lat) * 111.0
        dlon_km = (lon_grid - lon) * 111.0 * math.cos(math.radians(lat))
        dist_km = np.sqrt(dlat_km ** 2 + dlon_km ** 2)

        circle_mask = dist_km <= radius_km
        total_pixels = np.sum(circle_mask)
        if total_pixels == 0:
            return 0.0, 0.0

        tree_pixels = np.sum((arr == 1) & circle_mask)
        fraction = tree_pixels / total_pixels

        pixel_area_m2 = 10 * 10  # WorldCover native ~10m resolution
        tree_area_m2 = tree_pixels * pixel_area_m2

        return float(fraction), float(tree_area_m2)


def compute_green_cover_index(point_name, lat, lon):
    density = POPULATION_DENSITY.get(point_name, 11320)  # fallback: Delhi city average

    fraction, tree_area_m2 = tree_cover_fraction(lat, lon)

    analysis_area_km2 = math.pi * (ANALYSIS_RADIUS_KM ** 2)
    estimated_population = density * analysis_area_km2

    green_sqm_per_capita = tree_area_m2 / estimated_population if estimated_population > 0 else 0
    gap_sqm_per_capita = max(0.0, GREEN_SPACE_BENCHMARK_SQM_PER_CAPITA - green_sqm_per_capita)
    meets_benchmark = green_sqm_per_capita >= GREEN_SPACE_BENCHMARK_SQM_PER_CAPITA

    total_area_deficit_sqm = gap_sqm_per_capita * estimated_population
    illustrative_trees_needed = int(total_area_deficit_sqm / AVG_MATURE_TREE_CANOPY_SQM)

    return {
        "point": point_name,
        "analysis_radius_km": ANALYSIS_RADIUS_KM,
        "tree_cover_fraction_pct": round(fraction * 100, 2),
        "tree_area_sqm": round(tree_area_m2, 0),
        "population_density_per_km2": density,
        "estimated_population_in_radius": round(estimated_population, 0),
        "green_sqm_per_capita": round(green_sqm_per_capita, 2),
        "benchmark_sqm_per_capita": GREEN_SPACE_BENCHMARK_SQM_PER_CAPITA,
        "meets_benchmark": meets_benchmark,
        "gap_sqm_per_capita": round(gap_sqm_per_capita, 2),
        "illustrative_trees_needed": illustrative_trees_needed,
        "caveats": [
            "Population is a district-density estimate, not exact ward census count.",
            "Tree count is illustrative (area deficit / avg canopy size), not a literal planting target.",
            "9 sq.m/person benchmark is a widely-cited planning reference, not a binding regulatory standard.",
        ],
    }


def compute_for_all_points(city_coords_dict):
    """city_coords_dict: {name: (lat, lon)} -- pass sa.CITY_COORDS from the caller."""
    return [
        compute_green_cover_index(name, lat, lon)
        for name, (lat, lon) in city_coords_dict.items()
    ]
