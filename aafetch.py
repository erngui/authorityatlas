"""Wikidata seeder for Authority Atlas.

Developer tool (not part of site generation). Run manually to seed or refresh
an authority YAML from Wikidata. Network calls never happen during aagenerate.py.

Usage:
    python aafetch.py --qid Q8475
    python aafetch.py --qid Q170918 --output data/articles/icao.yaml
    python aafetch.py --qid Q225070 --dry-run
    python aafetch.py --qid Q170918 --output data/articles/icao.yaml --force-wikidata
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import yaml

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIDATA_ENTITY_BASE = "https://www.wikidata.org/entity/"
NOMINATIM_ENDPOINT = "https://nominatim.openstreetmap.org/search"
_USER_AGENT = "AuthorityAtlas/1.0 (https://github.com/erngui/authorityatlas)"

_CURATED_FIELDS = frozenset(
    {
        "remit",
        "factoid",
        "shortname",
        "legal_basis_name",
        "legal_basis_link",
        "regional_remit",
        "tags",
        "additional_resources",
        "head_title",
        "predecessor_organizations",
        "acronym",
        "headquarters_city",
        "headquarters_country",
        "headquarters_address",
    }
)

_WIKI_LANGS = ("en", "de", "fr", "it", "es", "nl", "pt", "zh", "ja", "ar", "ru")

# ---------------------------------------------------------------------------
# Wikidata properties used in the SPARQL query below.
# Each property has a canonical page at https://www.wikidata.org/wiki/Property:PXXX
#
# Property  Human name                  SPARQL variable(s)
# --------  --------------------------  ----------------------------------
# P1448     official name               ?officialName
# P571      inception (founding date)   ?inception
# P856      official website URL        ?website
# P625      coordinate location         ?lat / ?lon  (and ?coords as backup)
#
#             Wikidata stores P625 as a WKT (Well-Known Text) geometry
#             string, e.g. "Point(-0.076 51.509)".  WKT is an OGC/ISO
#             standard text format for geometric shapes — here just a
#             single longitude-latitude point (note: WKT order is lon,lat,
#             opposite from the conventional lat,lon).
#
#             The SPARQL GeoSPARQL extension provides geof:latitude() /
#             geof:longitude() to unpack that string into plain numbers,
#             which is what ?lat/?lon capture.  ?coords selects the raw
#             WKT string as a fallback in case the endpoint does not
#             support GeoSPARQL (rare but possible on mirrors/forks).
#             _parse_coordinates() tries ?lat/?lon first, then ?coords.
#
# P276      location (linked item)      — (intermediate join variable)
#   ↳ P625  coordinates of that item    ?locLat / ?locLon
#
#             Many authorities lack P625 on the entity itself; instead a
#             linked building or campus item (P276) carries the coordinates.
#             Real example: Rijnland (Q2619632) has P276 → office building
#             Q125679468, which has P625 → lat 52.164647, lon 4.4655.
#             aafetch calls this the "P276→P625" fallback and warns when it
#             is used, because the coordinates belong to the building, not
#             the authority — a human should verify them.
#
# P17       country (item)              → P297 → ?countryCode
# P297      ISO 3166-1 alpha-2 code     ?countryCode
# P131      located in admin. territory ?adminTerritory (English label)
# P31       instance of (entity type)   ?instanceOf (English label)
# P1448     official name               ?officialName  (preferred)
#   fallback: rdfs:label                ?entityLabel   (always present; used when
#             P1448 is absent — aafetch warns when this fallback fires because it
#             may indicate a Wikidata entry that hasn't been fully maintained)
# P1813     short name / acronym        ?shortName
#             Language-filtered to English. Maps to the `acronym` field.
#             Example: "ICAO" for the International Civil Aviation Organization.
# P18       image (Commons file URL)    ?image
# P101      field of work               ?fieldOfWork     (tag hint)
# P452      industry                    ?industry        (tag hint)
#             Both are multi-valued; LIMIT 1 returns only the first value
#             Wikidata returns for each. Treated as hints only — printed as
#             "Suggested sector tags" and never written to the YAML.
#             Coverage is patchy: present on prominent UN agencies (WHO,
#             ILO, FAO) but absent on more specialised bodies (ICAO, ISA).
#
# P457      foundational text           ?legalBasisName / ?legalBasisLink
#             Links to the official document that established the authority
#             (a treaty, charter, or statute).  The linked item's rdfs:label
#             gives the document name (?legalBasisName); its P953 ("full work
#             available at URL") gives a direct link (?legalBasisLink).
#             Coverage is patchy — present for ICAO (Chicago Convention) and
#             ISA (UNCLOS), absent for Trinity House and Rijnland.
#             Both fields are in _CURATED_FIELDS: written only for new files
#             (scaffold mode) and when --force-wikidata is passed.
#
# Wikipedia sitelinks are fetched via schema:isPartOf per language (see
# _build_sparql_query).  They are not Wikidata properties but graph links.
# ---------------------------------------------------------------------------

_SPARQL_TEMPLATE = """\
SELECT ?officialName ?entityLabel ?shortName ?inception ?website ?coords ?lat ?lon ?locLat ?locLon
       ?countryCode ?adminTerritory ?instanceOf ?image ?legalBasisName ?legalBasisLink
       ?fieldOfWork ?industry
       {wiki_selects}
WHERE {{
  BIND(wd:Q{qid} AS ?entity)
  OPTIONAL {{
    ?entity wdt:P1448 ?officialName .
    FILTER(LANG(?officialName) = "en")
  }}
  OPTIONAL {{
    ?entity rdfs:label ?entityLabel .
    FILTER(LANG(?entityLabel) = "en")
  }}
  OPTIONAL {{
    ?entity wdt:P1813 ?shortName .
    FILTER(!LANG(?shortName) || LANG(?shortName) = "en")
  }}
  OPTIONAL {{ ?entity wdt:P571 ?inception }}
  OPTIONAL {{ ?entity wdt:P856 ?website }}
  OPTIONAL {{
    ?entity wdt:P625 ?coords .
    BIND(geof:latitude(?coords) AS ?lat)
    BIND(geof:longitude(?coords) AS ?lon)
  }}
  OPTIONAL {{
    ?entity wdt:P276 ?locationItem .
    ?locationItem wdt:P625 ?locCoords .
    BIND(geof:latitude(?locCoords) AS ?locLat)
    BIND(geof:longitude(?locCoords) AS ?locLon)
  }}
  OPTIONAL {{
    ?entity wdt:P17 ?countryItem .
    ?countryItem wdt:P297 ?countryCode .
  }}
  OPTIONAL {{
    ?entity wdt:P131 ?adminItem .
    ?adminItem rdfs:label ?adminTerritory .
    FILTER(LANG(?adminTerritory) = "en")
  }}
  OPTIONAL {{
    ?entity wdt:P31 ?instanceItem .
    ?instanceItem rdfs:label ?instanceOf .
    FILTER(LANG(?instanceOf) = "en")
  }}
  OPTIONAL {{ ?entity wdt:P18 ?image }}
  OPTIONAL {{
    ?entity wdt:P457 ?foundingDoc .
    ?foundingDoc rdfs:label ?legalBasisName .
    FILTER(LANG(?legalBasisName) = "en")
    OPTIONAL {{ ?foundingDoc wdt:P953 ?legalBasisLink . }}
  }}
  OPTIONAL {{
    ?entity wdt:P101 ?fwItem .
    ?fwItem rdfs:label ?fieldOfWork .
    FILTER(LANG(?fieldOfWork) = "en")
  }}
  OPTIONAL {{
    ?entity wdt:P452 ?indItem .
    ?indItem rdfs:label ?industry .
    FILTER(LANG(?industry) = "en")
  }}
  {wiki_optionals}
}}
LIMIT 1
"""


def _normalize_qid(raw: str) -> str:
    """Strip leading Q/q and validate the remainder is all digits.

    Raises ValueError if the input is not a valid Wikidata Q-number.
    """
    digits = raw.lstrip("Qq")
    if not digits.isdigit():
        raise ValueError(
            f"Invalid Wikidata Q-ID: '{raw}'. "
            "Expected a positive integer (e.g. 170918 or Q170918)."
        )
    return digits


def _build_sparql_query(qid: str) -> str:
    selects = " ".join(f"?{lang}wiki" for lang in _WIKI_LANGS)
    optionals = "\n  ".join(
        f'OPTIONAL {{ ?{lang}wikiPage schema:about ?entity ; '
        f'schema:isPartOf <https://{lang}.wikipedia.org/> . '
        f"BIND(STR(?{lang}wikiPage) AS ?{lang}wiki) }}"
        for lang in _WIKI_LANGS
    )
    return _SPARQL_TEMPLATE.format(qid=qid, wiki_selects=selects, wiki_optionals=optionals)


def sparql_query(query: str) -> dict[str, Any]:
    params = urllib.parse.urlencode({"query": query, "format": "json"})
    url = f"{SPARQL_ENDPOINT}?{params}"
    req = urllib.request.Request(  # noqa: S310
        url,
        headers={
            "Accept": "application/sparql-results+json",
            "User-Agent": _USER_AGENT,
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310  # nosec B310
        return dict(json.loads(resp.read().decode("utf-8")))


def geocode_nominatim(query: str) -> dict[str, float] | None:
    """Geocode a free-text address query using OSM Nominatim.

    Returns {"lat": ..., "lon": ...} on success, None on failure or no results.
    Nominatim policy requires max 1 req/s; callers must respect this.
    """
    params = urllib.parse.urlencode({"q": query, "format": "json", "limit": "1"})
    url = f"{NOMINATIM_ENDPOINT}?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})  # noqa: S310
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310  # nosec B310
            results: list[dict[str, Any]] = json.loads(resp.read().decode("utf-8"))
            if results:
                return {"lat": float(results[0]["lat"]), "lon": float(results[0]["lon"])}
    except (urllib.error.URLError, ValueError, KeyError, IndexError):
        pass
    return None


def _parse_coordinates(row: dict[str, Any]) -> tuple[dict[str, float] | None, str]:
    """Extract lat/lon from a SPARQL result row.

    Returns (coords_or_None, source_label).  source_label is one of:
    "P625"      – direct coordinate location on the entity (best)
    "P276→P625" – coordinates on the P276-linked location item (see property
                  table above; warn caller to verify against headquarters)
    "WKT"       – parsed from the raw WKT Point string in ?coords (rare)
    "none"      – no coordinates found in Wikidata (caller may try Nominatim)
    """
    if "lat" in row and "lon" in row:
        try:
            return (
                {"lat": float(row["lat"]["value"]), "lon": float(row["lon"]["value"])},
                "P625",
            )
        except (KeyError, ValueError):
            pass
    if "locLat" in row and "locLon" in row:
        try:
            return (
                {"lat": float(row["locLat"]["value"]), "lon": float(row["locLon"]["value"])},
                "P276→P625",
            )
        except (KeyError, ValueError):
            pass
    if "coords" in row:
        m = re.match(r"Point\(([^ ]+) ([^ ]+)\)", row["coords"]["value"])
        if m:
            try:
                return (
                    {"lat": float(m.group(2)), "lon": float(m.group(1))},
                    "WKT",
                )
            except ValueError:
                pass
    return None, "none"


def _parse_year(row: dict[str, Any]) -> int | None:
    if "inception" not in row:
        return None
    raw = row["inception"]["value"]  # e.g. "1944-04-04T00:00:00Z"
    try:
        return int(raw[:4])
    except (ValueError, IndexError):
        return None


def fetch_entity(qid: str) -> dict[str, Any]:
    """Query Wikidata for one entity and return a normalised dict."""
    qid = _normalize_qid(qid)
    query = _build_sparql_query(qid)
    raw = sparql_query(query)
    bindings: list[dict[str, Any]] = raw.get("results", {}).get("bindings", [])
    if not bindings:
        raise ValueError(f"No Wikidata results for Q{qid}")
    row = bindings[0]

    multilang: dict[str, str] = {}
    for lang in _WIKI_LANGS:
        key = f"{lang}wiki"
        if key in row:
            multilang[lang] = row[key]["value"]

    coords, coord_source = _parse_coordinates(row)

    official_name = row.get("officialName", {}).get("value")
    if not official_name:
        print(
            f"  WARNING: Q{qid} has no P1448 (official name) — falling back to "
            "rdfs:label. The Wikidata entry may be under-maintained; consider "
            "adding P1448 at https://www.wikidata.org/wiki/Q" + qid
        )
    name = official_name or row.get("entityLabel", {}).get("value", "")

    return {
        "wikidata_id": f"Q{qid}",
        "name": name,
        "acronym": row.get("shortName", {}).get("value", ""),
        "year_established": _parse_year(row),
        "website": row.get("website", {}).get("value", ""),
        "wikipedia": multilang.get("en", ""),
        "wikipedia_multilang": multilang,
        "establishment_country": row.get("countryCode", {}).get("value", ""),
        "type": row.get("instanceOf", {}).get("value", ""),
        "image": row.get("image", {}).get("value", ""),
        "coordinates": coords,
        "legal_basis_name": row.get("legalBasisName", {}).get("value", ""),
        "legal_basis_link": row.get("legalBasisLink", {}).get("value", ""),
        "_coordinate_source": coord_source,
        "_suggested_tags": [
            v for v in (
                row.get("fieldOfWork", {}).get("value", ""),
                row.get("industry", {}).get("value", ""),
            )
            if v
        ],
    }


# Ordered template for new authority files. All fields are present so the
# contributor knows exactly what to fill in. Wikidata-fetched values are
# merged in on top; curated fields stay empty for the human to complete.
# Field order mirrors data/articles/trinity_house.yaml (the reference template).
_AUTHORITY_SCAFFOLD: dict[str, Any] = {
    "name": "",
    "shortname": "",
    "acronym": "",
    "type": "",
    "remit": "",
    "establishment_country": "",
    "regional_remit": "",
    "headquarters_address": "",
    "headquarters_city": "",
    "headquarters_country": "",
    "year_established": None,
    "predecessor_organizations": "",
    "wikidata_id": "",
    "coordinates": None,
    "website": "",
    "wikipedia": "",
    "wikipedia_multilang": {},
    "factoid": "",
    "legal_basis_name": "",
    "legal_basis_link": "",
    "head_title": "",
    "tags": [],
    "additional_resources": [],
}


def wikidata_to_authority(
    qid: str,
    wikidata_data: dict[str, Any],
    existing: dict[str, Any] | None = None,
    force_wikidata: bool = False,
) -> dict[str, Any]:
    """Merge Wikidata-sourced fields into an authority dict.

    Curated fields (_CURATED_FIELDS) are never overwritten unless
    force_wikidata is True. Empty/absent fields are always filled.
    """
    result: dict[str, Any] = dict(existing) if existing else {}

    for field, value in wikidata_data.items():
        if field in _CURATED_FIELDS and not force_wikidata:
            continue
        if value in (None, "", {}, []):
            continue
        if field not in result or result[field] in (None, "", {}, []) or force_wikidata:
            result[field] = value

    return result


def seed_yaml(
    qid: str,
    output_path: str,
    force_wikidata: bool = False,
    dry_run: bool = False,
) -> None:
    """Fetch Wikidata entity Q{qid} and write (or update) output_path YAML."""
    wikidata_data = fetch_entity(qid)
    coord_source: str = wikidata_data.pop("_coordinate_source", "none")
    suggested_tags: list[str] = wikidata_data.pop("_suggested_tags", [])

    path = Path(output_path)
    existing_authority: dict[str, Any] | None = None
    existing_doc: dict[str, Any] = {}
    is_new_file = not path.exists()

    if path.exists():
        with path.open(encoding="utf-8") as f:
            existing_doc = yaml.safe_load(f) or {}
        authorities = existing_doc.get("authorities", [])
        if isinstance(authorities, list) and authorities:
            existing_authority = authorities[0]
    else:
        # New file: start from the full scaffold so all fields are present.
        # force_wikidata=True because there is no existing curation to protect.
        existing_authority = dict(_AUTHORITY_SCAFFOLD)
        force_wikidata = True
        print("  New file — generating scaffold with all fields.")

    merged = wikidata_to_authority(qid, wikidata_data, existing_authority, force_wikidata)

    if merged.get("coordinates"):
        coords = merged["coordinates"]
        print(
            f"  Coordinates [{coord_source}]: "
            f"lat={coords['lat']}, lon={coords['lon']}"
        )
        if coord_source == "P276→P625":
            print(
                "  WARNING: coordinates are from a linked location item (P276), "
                "not the entity itself — verify they match the headquarters."
            )
        elif coord_source == "WKT":
            print(
                "  NOTE: coordinates parsed from WKT Point string "
                "— less reliable than P625 literal."
            )
    else:
        address = merged.get("headquarters_address", "")
        if address:
            nominatim_query = address
            nominatim_label = f"address: {address!r}"
        else:
            nominatim_query = (
                f"{merged.get('name', '')} {merged.get('establishment_country', '')}".strip()
            )
            nominatim_label = f"name+country: {nominatim_query!r}"
        if nominatim_query:
            print(f"  No coordinates from Wikidata — trying Nominatim ({nominatim_label})")
            if not address:
                print(
                    "  WARNING: Nominatim query is name+country only — result may be "
                    "an approximate city/country centroid, not the actual headquarters."
                )
            time.sleep(1)  # Nominatim policy: max 1 req/s
            coords = geocode_nominatim(nominatim_query)
            if coords:
                merged["coordinates"] = coords
                print(f"  Geocoded [Nominatim]: lat={coords['lat']}, lon={coords['lon']}")
            else:
                print("  Nominatim returned no results — coordinates left empty")

    if suggested_tags:
        print(f"  Suggested sector tags from Wikidata (P101/P452): {', '.join(suggested_tags)}")

    if is_new_file:
        empty = [f for f in ("remit", "factoid", "legal_basis_name", "tags") if not merged.get(f)]
        if empty:
            print(f"  TODO: fill in required fields before running aagenerate: {', '.join(empty)}")

    if dry_run:
        print(yaml.dump({"authorities": [merged]}, allow_unicode=True, sort_keys=False, indent=2))
        return

    out_doc: dict[str, Any]
    if existing_doc:
        authorities_list = existing_doc.get("authorities", [])
        if isinstance(authorities_list, list) and authorities_list:
            authorities_list[0] = merged
        else:
            authorities_list = [merged]
        out_doc = {**existing_doc, "authorities": authorities_list}
    else:
        out_doc = {"authorities": [merged]}

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.dump(out_doc, f, allow_unicode=True, sort_keys=False, indent=2)
    print(f"Written: {output_path}")


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(
        description="Seed an Authority Atlas YAML from Wikidata.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--qid",
        required=True,
        help="Wikidata Q-number (e.g. Q170918 or 170918)",
    )
    parser.add_argument(
        "--output",
        help="Output YAML file path. Defaults to data/articles/Q<qid>.yaml",
    )
    parser.add_argument(
        "--force-wikidata",
        action="store_true",
        help="Overwrite curated fields with Wikidata values.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the merged YAML to stdout without writing any file.",
    )
    args = parser.parse_args()

    qid = args.qid.lstrip("Qq")

    try:
        if args.output:
            output = args.output
        else:
            # Fetch the entity first so we can derive a human-readable filename
            # from the name or acronym rather than falling back to Q<number>.
            entity = fetch_entity(qid)
            raw = entity.get("acronym") or entity.get("name") or f"Q{qid}"
            slug = "".join(
                c for c in raw.replace(" ", "_").replace("/", "-").lower()
                if c.isalnum() or c in ("_", "-")
            )
            output = f"data/articles/{slug}.yaml"
            print(f"  Output: {output}")
        seed_yaml(qid, output, force_wikidata=args.force_wikidata, dry_run=args.dry_run)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
