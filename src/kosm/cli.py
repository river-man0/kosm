"""CLI: query OSM for Arctic military features and write them to a GeoPackage."""

from __future__ import annotations

import argparse
import logging
import sys

from kosm.constants import ARCTIC_BBOX, ARCTIC_CIRCLE_LATITUDE, DEFAULT_OVERPASS_ENDPOINTS
from kosm.convert import filter_to_arctic_circle, overpass_json_to_geodataframe
from kosm.overpass import OverpassError, build_military_query, run_query

logger = logging.getLogger("kosm")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="kosm-arctic-military",
        description=(
            "Query OpenStreetMap (via Overpass API) for all military features "
            "(military=* and landuse=military) located within the Arctic "
            "Circle, and write the results to a GeoPackage."
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        default="arctic_military.gpkg",
        help="Path to the output GeoPackage (default: %(default)s)",
    )
    parser.add_argument(
        "--layer",
        default="arctic_military_features",
        help="Layer name inside the GeoPackage (default: %(default)s)",
    )
    parser.add_argument(
        "--min-latitude",
        type=float,
        default=ARCTIC_CIRCLE_LATITUDE,
        help=(
            "Southern latitude boundary in degrees N (default: %(default)s, "
            "the current approximate latitude of the Arctic Circle)"
        ),
    )
    parser.add_argument(
        "--bbox",
        type=float,
        nargs=4,
        metavar=("SOUTH", "WEST", "NORTH", "EAST"),
        default=None,
        help=(
            "Override the query bounding box (default: the full circumpolar "
            "band from --min-latitude to the North Pole)"
        ),
    )
    parser.add_argument(
        "--endpoint",
        action="append",
        dest="endpoints",
        default=None,
        help=(
            "Overpass API endpoint to query; may be repeated to provide "
            "fallbacks in order (default: a built-in list of public mirrors)"
        ),
    )
    parser.add_argument(
        "--query-timeout",
        type=int,
        default=180,
        help="Overpass server-side query timeout in seconds (default: %(default)s)",
    )
    parser.add_argument(
        "--http-timeout",
        type=int,
        default=240,
        help="HTTP client timeout in seconds per request (default: %(default)s)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable debug logging"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if args.bbox is not None:
        bbox = tuple(args.bbox)
    else:
        south, west, north, east = ARCTIC_BBOX
        bbox = (args.min_latitude, west, north, east)

    endpoints = args.endpoints or DEFAULT_OVERPASS_ENDPOINTS

    query = build_military_query(bbox, timeout=args.query_timeout)
    logger.debug("Overpass query:\n%s", query)

    logger.info("Querying Overpass for military features in bbox %s", bbox)
    try:
        overpass_json = run_query(
            query, endpoints=endpoints, http_timeout=args.http_timeout
        )
    except OverpassError as exc:
        logger.error("Failed to fetch data from Overpass: %s", exc)
        return 1

    element_count = len(overpass_json.get("elements", []))
    logger.info("Overpass returned %d raw elements", element_count)

    gdf = overpass_json_to_geodataframe(overpass_json)
    gdf = filter_to_arctic_circle(gdf, min_latitude=args.min_latitude)
    logger.info("%d military features after Arctic Circle filtering", len(gdf))

    if gdf.empty:
        logger.warning(
            "No military features found; writing an empty layer to %s", args.output
        )

    gdf.to_file(args.output, layer=args.layer, driver="GPKG")
    logger.info("Wrote %d features to %s (layer %r)", len(gdf), args.output, args.layer)
    return 0


if __name__ == "__main__":
    sys.exit(main())
