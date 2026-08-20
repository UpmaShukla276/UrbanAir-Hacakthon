

import csv
import numpy as np

# Same bbox as DelhiNCR_*.tif files
LEFT, BOTTOM, RIGHT, TOP = 76.69815895812475, 28.099302087258632, 77.70427207633861, 28.907785842966202

# 6x6 spatial grid (36 points) -- good coverage, stays within free-tier rate limits
N = 6
lons = np.linspace(LEFT, RIGHT, N)
lats = np.linspace(BOTTOM, TOP, N)

CITY_CENTERS = {
    "Delhi": (28.7041, 77.1025),
    "Faridabad": (28.4089, 77.3178),
    "Ghaziabad": (28.6692, 77.4538),
    "Gurgaon": (28.4595, 77.0266),
    "Noida": (28.5355, 77.3910),
}


KNOWN_HOTSPOTS = {
    "Anand Vihar": (28.6469, 77.3152),
    "Rohini": (28.7495, 77.0565),
}

rows = []
grid_id = 0
for lat in lats:
    for lon in lons:
        if BOTTOM <= lat <= TOP and LEFT <= lon <= RIGHT:
            rows.append({"point_id": f"grid_{grid_id}", "type": "grid", "name": "", "lat": round(lat, 6), "lon": round(lon, 6)})
            grid_id += 1

for name, (lat, lon) in CITY_CENTERS.items():
    rows.append({"point_id": f"city_{name}", "type": "city_center", "name": name, "lat": lat, "lon": lon})

for name, (lat, lon) in KNOWN_HOTSPOTS.items():
    rows.append({"point_id": f"hotspot_{name.replace(' ', '_')}", "type": "hotspot", "name": name, "lat": lat, "lon": lon})

with open("ncr_grid_points.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["point_id", "type", "name", "lat", "lon"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Generated {len(rows)} points -> ncr_grid_points.csv")
print(f"  Grid points: {grid_id}")
print(f"  City centers: {len(CITY_CENTERS)}")
print(f"  Known hotspots: {len(KNOWN_HOTSPOTS)}")
