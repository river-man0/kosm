# kosm — Arctic military features from OpenStreetMap

`kosm` queries [OpenStreetMap](https://www.openstreetmap.org) (via the
[Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API)) for every
feature tagged as military, keeps only the ones located inside the Arctic
Circle, and writes the result to a [GeoPackage](https://www.geopackage.org/)
(`.gpkg`) for use in GIS tools like QGIS, ArcGIS, or `geopandas`.

## What counts as a "military feature"

OSM's tagging scheme for military features is documented at
[Key:military](https://wiki.openstreetmap.org/wiki/Key:military). This tool
matches any element (node, way, or relation) tagged with:

- **`military=*`** (any value) — airfields, bases, barracks, bunkers,
  checkpoints, danger areas, naval bases, nuclear explosion sites, obstacle
  courses, offices, ranges, training areas, trenches, etc.
- **`landuse=military`** — the older/companion area tag, present on some
  features without an explicit `military=*` value.

This is intentionally broad ("any and all military features"), not limited
to installations tagged specifically as bases — a WWII trench line and a
nuclear test site are both included alongside airfields and barracks.

## What counts as "the Arctic Circle"

The Arctic Circle currently sits at approximately 66°33'N (66.56°) and
drifts slowly north as Earth's axial tilt decreases. This tool defaults to
**66.5°N** (`kosm.constants.ARCTIC_CIRCLE_LATITUDE`) as a stable, slightly
conservative boundary, and:

1. Queries Overpass with a bounding box covering the full circumpolar band
   from 66.5°N to the North Pole (all longitudes).
2. Applies a second, defensive filter after fetching results: a feature is
   kept only if its
   [representative point](https://shapely.readthedocs.io/en/stable/manual.html#object.representative_point)
   (guaranteed to fall on the geometry itself, unlike a centroid) is north
   of 66.5°N. This drops features Overpass's bbox filter includes because
   *part* of a large way/relation pokes into the box, but whose bulk lies
   south of the circle.

Both the boundary latitude and the query bbox can be overridden on the
command line.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

Requires Python 3.10+. Pulls in `geopandas`, `shapely`, `pyogrio` (for
GeoPackage I/O), `osm2geojson` (for turning Overpass's element format into
proper GeoJSON geometry, including multipolygon assembly for relations),
and `requests`.

## Usage

```bash
kosm-arctic-military --output arctic_military.gpkg
```

or, without installing the console script:

```bash
python -m kosm.cli --output arctic_military.gpkg
```

### Options

| Flag | Default | Description |
| --- | --- | --- |
| `-o, --output` | `arctic_military.gpkg` | Output GeoPackage path |
| `--layer` | `arctic_military_features` | Layer name inside the GeoPackage |
| `--min-latitude` | `66.5` | Southern latitude boundary (°N) for both the query bbox and the post-fetch filter |
| `--bbox SOUTH WEST NORTH EAST` | full circumpolar band | Override the Overpass query bounding box entirely (e.g. to restrict to one country/region) |
| `--endpoint` | built-in list of public mirrors | Overpass API endpoint; repeatable to set fallback order |
| `--query-timeout` | `180` | Overpass server-side query timeout (seconds) |
| `--http-timeout` | `240` | HTTP client timeout per request (seconds) |
| `-v, --verbose` | off | Debug logging, including the generated Overpass QL query |

Example: only Svalbard and the Barents Sea region, using a specific mirror:

```bash
kosm-arctic-military \
  --output svalbard_military.gpkg \
  --bbox 74 0 82 40 \
  --endpoint https://overpass.private.coffee/api/interpreter
```

### Reliability notes

Public Overpass instances are free, shared, and rate-limit concurrent
queries per client IP. A full circumpolar query is large (tens of thousands
of elements) and can take 1-3 minutes, and may receive a `429` if the
server is busy. `kosm` retries each configured endpoint a few times with
backoff (honoring a `Retry-After` header when present) before moving to the
next one; the default endpoint list includes multiple community mirrors.
If every endpoint fails, rerun later or point `--endpoint` at an Overpass
instance you control.

## Output schema

Each row is one OSM node/way/relation. Geometry type follows the source
element: `Point` for nodes, `LineString`/`Polygon` for ways, and
`Polygon`/`MultiPolygon` for relations (e.g. multipolygon training areas).

| Column | Description |
| --- | --- |
| `osm_type`, `osm_id` | Source element type and ID |
| `osm_url` | Link to the element on openstreetmap.org |
| `military`, `landuse`, `name`, `name:en`, `operator`, `operator:type`, `operator:wikidata`, `access`, `building`, `historic`, `description`, `start_date`, `disused`, `abandoned`, `wikidata`, `wikipedia` | Common OSM tags, flattened into their own columns for easy filtering (null if absent) |
| `tags_json` | The complete raw OSM tag set for the element, as JSON — nothing is lost even if a tag isn't one of the flattened columns above |

## Data source & license

Data comes from OpenStreetMap contributors via the Overpass API, licensed
under the [Open Database License (ODbL)](https://www.openstreetmap.org/copyright).
Any redistribution of the generated GeoPackage should carry that
attribution.

## Development

```bash
pip install -e ".[dev]"
pytest
```

Tests run entirely against fixture data (no network access) by mocking the
Overpass response, so `pytest` is fast and deterministic.
