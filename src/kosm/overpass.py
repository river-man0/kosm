"""Build and execute Overpass QL queries against the Overpass API."""

from __future__ import annotations

import logging
import time
from typing import Sequence

import requests

from kosm.constants import DEFAULT_OVERPASS_ENDPOINTS, MILITARY_TAG_FILTERS

logger = logging.getLogger(__name__)

BBox = tuple[float, float, float, float]  # (south, west, north, east)


class OverpassError(RuntimeError):
    """Raised when every configured Overpass endpoint fails."""


def build_military_query(bbox: BBox, timeout: int = 180) -> str:
    """Build an Overpass QL query for military features within a bbox.

    Matches every element tagged with a `military=*` key (any value) or
    `landuse=military`, across nodes, ways and relations, and returns full
    geometry so ways/relations can be turned into LineStrings/Polygons
    without a second lookup.
    """
    south, west, north, east = bbox
    bbox_str = f"{south},{west},{north},{east}"

    clauses = []
    for elem_type in ("node", "way", "relation"):
        for tag_filter in MILITARY_TAG_FILTERS:
            if "=" in tag_filter:
                key, value = tag_filter.split("=", 1)
                clauses.append(f'  {elem_type}["{key}"="{value}"]({bbox_str});')
            else:
                clauses.append(f'  {elem_type}["{tag_filter}"]({bbox_str});')

    body = "\n".join(clauses)
    # "out body geom" embeds each way/relation's coordinates directly in the
    # response, so no follow-up recursion (">; out skel qt;") is needed to
    # resolve member node positions. Adding it back would pull in every
    # untagged member node as its own bare "feature" once run through
    # osm2geojson, flooding the output with junk points.
    return f"[out:json][timeout:{timeout}];\n(\n{body}\n);\nout body geom;\n"


def run_query(
    query: str,
    endpoints: Sequence[str] = DEFAULT_OVERPASS_ENDPOINTS,
    http_timeout: int = 240,
    max_retries_per_endpoint: int = 3,
    retry_backoff: float = 15.0,
) -> dict:
    """Execute an Overpass QL query, retrying across endpoints on failure.

    Overpass instances are free, shared, and rate-limited, so a single
    endpoint may time out or return a 429 (too many concurrent queries from
    this client) or 5xx under load. This tries each endpoint, with a few
    retries and backoff (honoring a `Retry-After` header when the server
    sends one) before moving to the next endpoint.
    """
    last_error: Exception | None = None

    for endpoint in endpoints:
        for attempt in range(1, max_retries_per_endpoint + 1):
            try:
                logger.info("Querying %s (attempt %d)", endpoint, attempt)
                response = requests.post(
                    endpoint, data={"data": query}, timeout=http_timeout
                )
                if response.status_code == 200:
                    return response.json()
                if response.status_code in (429, 502, 503, 504):
                    logger.warning(
                        "%s returned %d, will retry", endpoint, response.status_code
                    )
                    last_error = OverpassError(
                        f"{endpoint} returned HTTP {response.status_code}"
                    )
                    wait = retry_backoff * attempt
                    retry_after = response.headers.get("Retry-After")
                    if retry_after and retry_after.isdigit():
                        wait = max(wait, float(retry_after))
                    if attempt < max_retries_per_endpoint:
                        time.sleep(wait)
                    continue
                response.raise_for_status()
            except (requests.RequestException, ValueError) as exc:
                logger.warning("%s failed: %s", endpoint, exc)
                last_error = exc
                if attempt < max_retries_per_endpoint:
                    time.sleep(retry_backoff * attempt)

    raise OverpassError(
        f"All Overpass endpoints failed. Last error: {last_error}"
    ) from last_error
