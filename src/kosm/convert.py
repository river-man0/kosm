"""Convert an Overpass JSON response into a GeoDataFrame of military features."""

from __future__ import annotations

import json

import geopandas as gpd
import osm2geojson
import pandas as pd
from shapely.geometry import shape

from kosm.constants import ARCTIC_CIRCLE_LATITUDE, FLATTENED_TAG_KEYS

# Columns always present in the output, in a stable order. Anything else
# discovered in `tags` is appended after these.
_BASE_COLUMNS = ["osm_type", "osm_id", "osm_url", *FLATTENED_TAG_KEYS, "tags_json"]


def overpass_json_to_geodataframe(overpass_json: dict) -> gpd.GeoDataFrame:
    """Convert a raw Overpass JSON response into a GeoDataFrame.

    Uses osm2geojson to assemble proper geometries (including multipolygons
    for relations) from Overpass's "out geom" element format, then flattens
    OSM tags into columns suitable for a GeoPackage attribute table.
    """
    geojson = osm2geojson.json2geojson(overpass_json)
    features = geojson.get("features", [])

    if not features:
        return _empty_geodataframe()

    rows = []
    geometries = []
    for feature in features:
        props = feature.get("properties", {})
        tags = props.get("tags", {}) or {}
        if not tags:
            # Untagged member nodes/ways that osm2geojson surfaces while
            # assembling way/relation geometry, not military features
            # matched by the query itself.
            continue
        osm_type = props.get("type")
        osm_id = props.get("id")

        row = {
            "osm_type": osm_type,
            "osm_id": osm_id,
            "osm_url": _osm_url(osm_type, osm_id),
        }
        for key in FLATTENED_TAG_KEYS:
            row[key] = tags.get(key)
        row["tags_json"] = json.dumps(tags, ensure_ascii=False, sort_keys=True)

        rows.append(row)
        geometries.append(shape(feature["geometry"]))

    df = pd.DataFrame(rows, columns=_BASE_COLUMNS)
    gdf = gpd.GeoDataFrame(df, geometry=geometries, crs="EPSG:4326")
    return gdf


def filter_to_arctic_circle(
    gdf: gpd.GeoDataFrame, min_latitude: float = ARCTIC_CIRCLE_LATITUDE
) -> gpd.GeoDataFrame:
    """Keep only features whose representative point lies north of `min_latitude`.

    This is a defensive second pass on top of the Overpass bbox filter:
    Overpass includes any way/relation with at least one member north of
    the bbox, which could include a feature whose bulk actually sits south
    of the Arctic Circle. Filtering on the representative point (guaranteed
    to lie within the geometry, unlike a centroid) keeps only features that
    are themselves substantially inside the circle.
    """
    if gdf.empty:
        return gdf
    inside = gdf.geometry.representative_point().y >= min_latitude
    return gdf[inside].reset_index(drop=True)


def _osm_url(osm_type: str | None, osm_id: int | None) -> str | None:
    if not osm_type or osm_id is None:
        return None
    return f"https://www.openstreetmap.org/{osm_type}/{osm_id}"


def _empty_geodataframe() -> gpd.GeoDataFrame:
    df = pd.DataFrame(columns=_BASE_COLUMNS)
    return gpd.GeoDataFrame(df, geometry=[], crs="EPSG:4326")
