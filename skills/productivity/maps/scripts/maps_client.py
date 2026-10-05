#!/usr/bin/env python3
"""
maps_client.py - CLI tool for maps, geocoding, routing, POI search, and more.
Uses only Python stdlib. Data from OpenStreetMap/Nominatim, Overpass API, OSRM,
and TimeAPI.io.

Commands:
  search     - Geocode a place name to coordinates
  reverse    - Reverse geocode coordinates to an address
  nearby     - Find nearby POIs by category
  distance   - Road distance and travel time between two places
  directions - Turn-by-turn directions between two places
  timezone   - Timezone info for coordinates
  bbox       - Find POIs within a bounding box
  area       - Get bounding box and area info for a named place
"""

import argparse
import json
import math
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

USER_AGENT = "HermesAgent/1.0 (contact: hermes@agent.ai)"
DATA_SOURCE = "OpenStreetMap/Nominatim"

NOMINATIM_SEARCH  = "https://nominatim.openstreetmap.org/search"
NOMINATIM_REVERSE = "https://nominatim.openstreetmap.org/reverse"
# Public Overpass endpoints. We try them in order so a single server
# outage doesn't break the skill — kumi.systems is a well-known mirror.
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
# Backward-compat alias for any caller that imports OVERPASS_API directly.
OVERPASS_API      = OVERPASS_URLS[0]
OSRM_BASE         = "https://router.project-osrm.org/route/v1"
TIMEAPI_BASE      = "https://timeapi.io/api/timezone/coordinate"

# Allowed domains for outbound requests to prevent SSRF
ALLOWED_DOMAINS = {
    "nominatim.openstreetmap.org",
    "overpass-api.de",
    "overpass.kumi.systems",
    "router.project-osrm.org",
    "timeapi.io",
}

# Seconds to sleep between Nominatim requests (ToS requirement)
NOMINATIM_RATE_LIMIT = 1.0

# Maximum retries for HTTP errors
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # seconds

# Category -> (OSM tag key, OSM tag value)
CATEGORY_TAGS = {
    # Food & Drink
    "restaurant":        ("amenity", "restaurant"),
    "cafe":              ("amenity", "cafe"),
    "bar":               ("amenity", "bar"),
    # bakery is tagged as shop=bakery in the OSM wiki, but some mappers use
    # amenity=bakery. Search both so small indie bakeries aren't missed.
    "bakery":            [("shop", "bakery"), ("amenity", "bakery")],
    "convenience_store": ("shop",    "convenience"),
    # Health
    "hospital":          ("amenity", "hospital"),
    "pharmacy":          ("amenity", "pharmacy"),
    "dentist":           ("amenity", "dentist"),
    "doctor":            ("amenity", "doctors"),
    "veterinary":        ("amenity", "veterinary"),
    # Accommodation
    "hotel":             ("tourism", "hotel"),
    "guest_house":       ("tourism", "guest_house"),
    "camp_site":         ("tourism", "camp_site"),
    # Shopping & Services
    "supermarket":       ("shop",    "supermarket"),
    "bookshop":          ("shop",    "books"),
    "laundry":           ("shop",    "laundry"),
    # Finance
    "atm":               ("amenity", "atm"),
    "bank":              ("amenity", "bank"),
    # Transport
    "gas_station":       ("amenity", "fuel"),
    "parking":           ("amenity", "parking"),
    "airport":           ("aeroway", "aerodrome"),
    "train_station":     ("railway", "station"),
    "bus_stop":          ("highway", "bus_stop"),
    "taxi":              ("amenity", "taxi"),
    "car_wash":          ("amenity", "car_wash"),
    "car_rental":        ("amenity", "car_rental"),
    "bicycle_rental":    ("amenity", "bicycle_rental"),
    # Culture & Entertainment
    "museum":            ("tourism", "museum"),
    "cinema":            ("amenity", "cinema"),
    "theatre":           ("amenity", "theatre"),
    "nightclub":         ("amenity", "nightclub"),
    "zoo":               ("tourism", "zoo"),
    # Education
    "school":            ("amenity", "school"),
    "university":        ("amenity", "university"),
    "library":           ("amenity", "library"),
    # Public Services
    "police":            ("amenity", "police"),
    "fire_station":      ("amenity", "fire_station"),
    "post_office":       ("amenity", "post_office"),
    # Religion
    "church":            ("amenity", "place_of_worship"),  # refined by religion tag
    "mosque":            ("amenity", "place_of_worship"),
    "synagogue":         ("amenity", "place_of_worship"),
    # Recreation
    "park":              ("leisure", "park"),
    "gym":               ("leisure", "fitness_centre"),
    "swimming_pool":     ("leisure", "swimming_pool"),
    "playground":        ("leisure", "playground"),
    "stadium":           ("leisure", "stadium"),
}

# Religion-specific overrides for place_of_worship categories
RELIGION_FILTER = {
    "church":    "christian",
    "mosque":    "muslim",
    "synagogue": "jewish",
}

VALID_CATEGORIES = sorted(CATEGORY_TAGS.keys())


def _tags_for(category):
    """Return the CATEGORY_TAGS entry as a list of (key, value) pairs.

    Most categories map to a single (tag_key, tag_val) tuple, but some
    (e.g. ``bakery``) are tagged under more than one OSM key and are
    represented as a list of tuples. Normalise both forms to a list.
    """
    entry = CATEGORY_TAGS[category]
    if isinstance(entry, list):
        return list(entry)
    return [entry]

OSRM_PROFILES = {
    "driving": "driving",
    "walking": "foot",
    "cycling": "bike",
}

# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def print_json(data):
    """Print data as pretty-printed JSON to stdout."""
    print(json.dumps(data, indent=2, ensure_ascii=False))


def error_exit(message, code=1):
    """Print an error result as JSON and exit."""
    print_json({"error": message, "status": "error"})
    sys.exit(code)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def http_get(url, params=None, retries=MAX_RETRIES, silent=False):
    """
    Perform an HTTP GET request, returning parsed JSON.
    Adds the required User-Agent header. Retries on transient errors.
    If silent=True, raises RuntimeError instead of calling error_exit.
    """
    try:
        parsed_url = urllib.parse.urlparse(url)
        if parsed_url.scheme != "https":
            raise ValueError(f"Invalid URL scheme: '{parsed_url.scheme}'. Only 'https' is allowed.")
        if not parsed_url.hostname or parsed_url.hostname not in ALLOWED_DOMAINS:
            raise ValueError(f"Disallowed or missing hostname: '{parsed_url.hostname}'")
    except (ValueError, AttributeError) as exc:
        msg = f"URL validation failed: {exc}"
        if silent:
            raise RuntimeError(msg)
        error_exit(msg)

    if params:
        url = url + "?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            last_error = f"HTTP {exc.code}: {exc.reason} for {url}"
            if exc.code in {429, 503, 502, 504}:
                time.sleep(RETRY_DELAY * attempt)
            else:
                if silent:
                    raise RuntimeError(last_error)
                error_exit(last_error)
        except urllib.error.URLError as exc:
            last_error = f"URL error: {exc.reason}"
            time.sleep(RETRY_DELAY * attempt)
        except json.JSONDecodeError as exc:
            last_error = f"JSON parse error: {exc}"
            time.sleep(RETRY_DELAY * attempt)

    msg = f"Request failed after {retries} attempts. Last error: {last_error}"
    if silent:
        raise RuntimeError(msg)
    error_exit(msg)


def http_get_text(url, params=None, retries=MAX_RETRIES, silent=False):
    """
    Like http_get but returns raw text instead of parsed JSON.
    Useful for APIs that may return non-JSON responses.
    """
    try:
        parsed_url = urllib.parse.urlparse(url)
        if parsed_url.scheme != "https":
            raise ValueError(f"Invalid URL scheme: '{parsed_url.scheme}'. Only 'https' is allowed.")
        if not parsed_url.hostname or parsed_url.hostname not in ALLOWED_DOMAINS:
            raise ValueError(f"Disallowed or missing hostname: '{parsed_url.hostname}'")
    except (ValueError, AttributeError) as exc:
        msg = f"URL validation failed: {exc}"
        if silent:
            raise RuntimeError(msg)
        error_exit(msg)

    if params:
        url = url + "?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            last_error = f"HTTP {exc.code}: {exc.reason} for {url}"
            if exc.code in {429, 503, 502, 504}:
                time.sleep(RETRY_DELAY * attempt)
            else:
                if silent:
                    raise RuntimeError(last_error)
                error_exit(last_error)
        except urllib.error.URLError as exc:
            last_error = f"URL error: {exc.reason}"
            time.sleep(RETRY_DELAY * attempt)

    msg = f"Request failed after {retries} attempts. Last error: {last_error}"
    if silent:
        raise RuntimeError(msg)
    error_exit(msg)


def http_post(url, data_str, retries=MAX_RETRIES):
    """
    Perform an HTTP POST with a plain-text body (for Overpass QL).
    Returns parsed JSON.
    """
    try:
        parsed_url = urllib.parse.urlparse(url)
        if parsed_url.scheme != "https":
            raise ValueError(f"Invalid URL scheme: '{parsed_url.scheme}'. Only 'https' is allowed.")
        if not parsed_url.hostname or parsed_url.hostname not in ALLOWED_DOMAINS:
            raise ValueError(f"Disallowed or missing hostname: '{parsed_url.hostname}'")
    except (ValueError, AttributeError) as exc:
        error_exit(f"URL validation failed: {exc}")

    encoded = data_str.encode("utf-8")
    req = urllib.request.Request(
        url,
        data=encoded,
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )

    last_error = None
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            last_error = f"HTTP {exc.code}: {exc.reason}"
            if exc.code in {429, 503, 502, 504}:
                time.sleep(RETRY_DELAY * attempt)
            else:
                error_exit(last_error)
        except urllib.error.URLError as exc:
            last_error = f"URL error: {exc.reason}"
            time.sleep(RETRY_DELAY * attempt)
        except json.JSONDecodeError as exc:
            last_error = f"JSON parse error: {exc}"
            time.sleep(RETRY_DELAY * attempt)

    error_exit(f"POST failed after {retries} attempts. Last error: {last_error}")


def overpass_query(query):
    """POST an Overpass QL query, trying each URL in OVERPASS_URLS in turn.

    A single public Overpass mirror can be rate-limited or down; trying the
    next mirror before giving up turns a flaky outage into a retry. Returns
    parsed JSON. Falls through to error_exit if every mirror fails.
    """
    post_data = "data=" + urllib.parse.quote(query)
    last_error = None
    for url in OVERPASS_URLS:
        try:
            return http_post(url, post_data, retries=1)
        except SystemExit:
            # error_exit inside http_post — keep trying the next mirror.
            last_error = f"mirror {url} exhausted retries"
            continue
        except Exception as exc:
            last_error = f"{url}: {exc}"
            continue
    error_exit(
        f"All Overpass mirrors failed. Last error: {last_error or 'unknown'}"
    )


# ---------------------------------------------------------------------------
# Geo math
# ---------------------------------------------------------------------------

def haversine_m(lat1, lon1, lat2, lon2):
    """Return distance in metres between two lat/lon points (Haversine)."""
    R = 6_371_000  # Earth mean radius in metres
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2)
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Nominatim helpers
# ---------------------------------------------------------------------------

def nominatim_search(query, limit=5):
    """Geocode a free-text query. Returns list of result dicts."""
    params = {
        "q":              query,
        "format":         "json",
        "limit":          limit,
        "addressdetails": 1,
    }
    time.sleep(NOMINATIM_RATE_LIMIT)
    return http_get(NOMINATIM_SEARCH, params=params)


def nominatim_reverse(lat, lon):
    """Reverse geo