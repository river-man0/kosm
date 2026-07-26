import geopandas as gpd

from kosm import cli
from tests.test_convert import SAMPLE_OVERPASS_JSON


def test_main_writes_geopackage(tmp_path, monkeypatch):
    output = tmp_path / "out.gpkg"

    monkeypatch.setattr(
        cli, "run_query", lambda *args, **kwargs: SAMPLE_OVERPASS_JSON
    )

    exit_code = cli.main(["--output", str(output), "--layer", "features"])

    assert exit_code == 0
    assert output.exists()

    gdf = gpd.read_file(output, layer="features")
    # The southern (59.9N) sample feature must be filtered out.
    assert len(gdf) == 2
    assert set(gdf["osm_id"]) == {1001, 2002}


def test_main_also_writes_geojson_when_requested(tmp_path, monkeypatch):
    output = tmp_path / "out.gpkg"
    geojson_output = tmp_path / "out.geojson"

    monkeypatch.setattr(
        cli, "run_query", lambda *args, **kwargs: SAMPLE_OVERPASS_JSON
    )

    exit_code = cli.main(
        ["--output", str(output), "--geojson-output", str(geojson_output)]
    )

    assert exit_code == 0
    assert geojson_output.exists()

    gdf = gpd.read_file(geojson_output)
    assert set(gdf["osm_id"]) == {1001, 2002}
