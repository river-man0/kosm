import json

from kosm.convert import filter_to_arctic_circle, overpass_json_to_geodataframe

SAMPLE_OVERPASS_JSON = {
    "version": 0.6,
    "elements": [
        {
            "type": "node",
            "id": 1001,
            "lat": 78.2232,
            "lon": 15.6267,
            "tags": {"military": "base", "name": "Test Arctic Base"},
        },
        {
            "type": "way",
            "id": 2002,
            "tags": {
                "military": "barracks",
                "landuse": "military",
                "name": "Test Barracks",
            },
            "geometry": [
                {"lat": 70.0, "lon": 10.0},
                {"lat": 70.0, "lon": 10.01},
                {"lat": 70.01, "lon": 10.01},
                {"lat": 70.01, "lon": 10.0},
                {"lat": 70.0, "lon": 10.0},
            ],
        },
        {
            # South of the Arctic Circle: should be dropped by the
            # representative-point filter even though the raw Overpass
            # response (e.g. from a manually widened bbox) contains it.
            "type": "node",
            "id": 3003,
            "lat": 59.9,
            "lon": 10.7,
            "tags": {"military": "office", "name": "Southern HQ"},
        },
    ],
}


def test_overpass_json_to_geodataframe_flattens_tags_and_geometry():
    gdf = overpass_json_to_geodataframe(SAMPLE_OVERPASS_JSON)

    assert len(gdf) == 3
    assert set(gdf["osm_type"]) == {"node", "way"}
    assert set(gdf["military"]) == {"base", "barracks", "office"}

    base_row = gdf[gdf["osm_id"] == 1001].iloc[0]
    assert base_row.geometry.geom_type == "Point"
    assert base_row["name"] == "Test Arctic Base"
    assert base_row["osm_url"] == "https://www.openstreetmap.org/node/1001"
    assert json.loads(base_row["tags_json"]) == {
        "military": "base",
        "name": "Test Arctic Base",
    }

    barracks_row = gdf[gdf["osm_id"] == 2002].iloc[0]
    assert barracks_row.geometry.geom_type == "Polygon"
    assert barracks_row["landuse"] == "military"


def test_overpass_json_to_geodataframe_handles_no_elements():
    gdf = overpass_json_to_geodataframe({"version": 0.6, "elements": []})
    assert gdf.empty
    assert "military" in gdf.columns


def test_filter_to_arctic_circle_drops_features_south_of_boundary():
    gdf = overpass_json_to_geodataframe(SAMPLE_OVERPASS_JSON)
    filtered = filter_to_arctic_circle(gdf, min_latitude=66.5)

    assert len(filtered) == 2
    assert 3003 not in set(filtered["osm_id"])
    assert set(filtered["osm_id"]) == {1001, 2002}


def test_filter_to_arctic_circle_handles_empty_geodataframe():
    gdf = overpass_json_to_geodataframe({"version": 0.6, "elements": []})
    filtered = filter_to_arctic_circle(gdf)
    assert filtered.empty
