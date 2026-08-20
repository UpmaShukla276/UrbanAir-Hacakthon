

import osmium
import json
from shapely import wkb as shapely_wkb
from shapely.geometry import mapping, box

PBF_PATH = "/mnt/user-data/uploads/northern-zone-260709_osm.pbf"

BBOX = (76.69815895812475, 28.099302087258632, 77.70427207633861, 28.907785842966202)
CLIP_BOX = box(*BBOX)

wkbfab = osmium.geom.WKBFactory()


class RoadHandler(osmium.SimpleHandler):
    """First object: roads only (simple ways, not areas)."""
    def __init__(self):
        super().__init__()
        self.roads = []

    def way(self, w):
        tags = dict(w.tags)
        if "highway" not in tags:
            return
        try:
            for n in w.nodes:
                if n.location.valid():
                    lon, lat = n.location.lon, n.location.lat
                    if BBOX[0] <= lon <= BBOX[2] and BBOX[1] <= lat <= BBOX[3]:
                        break
            else:
                return
            wkb = wkbfab.create_linestring(w)
            geom = shapely_wkb.loads(wkb, hex=True)
            if geom.intersects(CLIP_BOX):
                self.roads.append({
                    "geometry": mapping(geom.intersection(CLIP_BOX)),
                    "properties": {"highway": tags.get("highway"), "name": tags.get("name")}
                })
        except Exception:
            pass


class AreaHandler(osmium.SimpleHandler):
   
    def __init__(self):
        super().__init__()
        self.parks = []
        self.residential = []
        self.industrial = []

    def area(self, a):
        tags = dict(a.tags)
        if not tags:
            return
        try:
            wkb = wkbfab.create_multipolygon(a)
            geom = shapely_wkb.loads(wkb, hex=True)
            if not geom.intersects(CLIP_BOX):
                return
            clipped = geom.intersection(CLIP_BOX)
            if clipped.is_empty:
                return

            if tags.get("leisure") == "park":
                self.parks.append({
                    "geometry": mapping(clipped),
                    "properties": {"name": tags.get("name"), "leisure": "park"}
                })
            elif tags.get("landuse") == "residential":
                self.residential.append({
                    "geometry": mapping(clipped),
                    "properties": {"landuse": "residential"}
                })
            elif tags.get("landuse") == "industrial":
                self.industrial.append({
                    "geometry": mapping(clipped),
                    "properties": {"landuse": "industrial"}
                })
        except Exception:
            pass


def to_featurecollection(features):
    return {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "geometry": f["geometry"], "properties": f["properties"]}
            for f in features
        ],
    }


if __name__ == "__main__":
    print("Pass 1/2: extracting roads (simple ways)...")
    road_handler = RoadHandler()
    idx1 = osmium.index.create_map("sparse_mem_array")
    lh1 = osmium.NodeLocationsForWays(idx1)
    lh1.ignore_errors()
    osmium.apply(PBF_PATH, lh1, road_handler)
    print(f"Roads: {len(road_handler.roads)}")

    print("Pass 2/2: extracting areas (parks/residential/industrial, incl. multipolygon relations)...")
    am = osmium.area.AreaManager()
    osmium.apply(PBF_PATH, am.first_pass_handler())

    area_handler = AreaHandler()
    idx2 = osmium.index.create_map("sparse_mem_array")
    lh2 = osmium.NodeLocationsForWays(idx2)
    lh2.ignore_errors()
    osmium.apply(PBF_PATH, lh2, am.second_pass_handler(area_handler))

    print(f"Parks: {len(area_handler.parks)}")
    print(f"Residential: {len(area_handler.residential)}")
    print(f"Industrial: {len(area_handler.industrial)}")

    with open("delhi_ncr_roads.geojson", "w") as f:
        json.dump(to_featurecollection(road_handler.roads), f)
    with open("delhi_ncr_parks.geojson", "w") as f:
        json.dump(to_featurecollection(area_handler.parks), f)
    with open("delhi_ncr_residential.geojson", "w") as f:
        json.dump(to_featurecollection(area_handler.residential), f)
    with open("delhi_ncr_industrial.geojson", "w") as f:
        json.dump(to_featurecollection(area_handler.industrial), f)

    print("Saved 4 corrected GeoJSON files.")
