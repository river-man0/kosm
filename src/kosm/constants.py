"""Shared constants for the kosm Arctic military feature extractor."""

# The Arctic Circle drifts slowly (~15 m/year) with Earth's axial tilt.
# 66.5622 deg N is its current (2020s) approximate latitude; we round down
# slightly to 66.5 deg N so the query stays correct for years without
# re-tuning and never excludes a feature that is genuinely inside the circle.
ARCTIC_CIRCLE_LATITUDE = 66.5

# A bounding box spanning the full range of longitudes north of the Arctic
# Circle: (south, west, north, east) as used by Overpass QL.
ARCTIC_BBOX = (ARCTIC_CIRCLE_LATITUDE, -180.0, 90.0, 180.0)

# Public Overpass API endpoints, tried in order. overpass-api.de (the
# "main" instance) is listed first since it is the canonical instance, with
# community mirrors as fallbacks for resilience against rate limiting or
# downtime.
DEFAULT_OVERPASS_ENDPOINTS = (
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass-api.de/api/interpreter",
)

# OSM tagging scheme for military features:
# https://wiki.openstreetmap.org/wiki/Key:military
# `military=*` is the primary key describing military feature type
# (airfield, base, barracks, bunker, checkpoint, danger_area, naval_base,
# nuclear_explosion_site, obstacle_course, office, range, training_area,
# trench, ...). `landuse=military` is the long-standing companion area tag,
# and is sometimes present without an explicit `military=*` value.
MILITARY_TAG_FILTERS = (
    'military',
    'landuse=military',
)

# Well-known tag keys worth surfacing as their own GeoPackage columns for
# easy filtering/inspection; every raw tag is also preserved as JSON in the
# `tags_json` column so nothing is lost.
FLATTENED_TAG_KEYS = (
    "military",
    "landuse",
    "name",
    "name:en",
    "operator",
    "operator:type",
    "operator:wikidata",
    "access",
    "building",
    "historic",
    "description",
    "start_date",
    "disused",
    "abandoned",
    "wikidata",
    "wikipedia",
)
