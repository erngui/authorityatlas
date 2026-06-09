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
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import yaml

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
WIKIDATA_ENTITY_BASE = "https://www.wikidata.org/entity/"

_CURATED_FIELDS = frozenset(
    {
        "remit",
        "factoid",
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

_SPARQL_TEMPLATE = """\
SELECT ?officialName ?inception ?website ?lat ?lon
       ?countryCode ?adminTerritory ?instanceOf ?image
       {wiki_selects}
WHERE {{
  BIND(wd:Q{qid} AS ?entity)
  OPTIONAL {{
    ?entity wdt:P1448 ?officialName .
    FILTER(LANG(?officialName) = "en")
  }}
  OPTIONAL {{ ?entity wdt:P571 ?inception }}
  OPTIONAL {{ ?entity wdt:P856 ?website }}
  OPTIONAL {{
    ?entity wdt:P625 ?coords .
    BIND(geof:latitude(?coords) AS ?lat)
    BIND(geof:longitude(?coords) AS ?lon)
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
  {wiki_optionals}
}}
LIMIT 1
"""


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
            "User-Agent": "AuthorityAtlas/1.0 (https://github.com/erngui/authorityatlas)",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310
        return dict(json.loads(resp.read().decode("utf-8")))


def _parse_coordinates(row: dict[str, Any]) -> dict[str, float] | None:
    """Extract lat/lon from a SPARQL result row.

    Tries geof:latitude/longitude bindings first; falls back to parsing a
    WKT Point string (e.g. 'Point(-0.1278 51.5074)') from a ?coords binding.
    """
    if "lat" in row and "lon" in row:
        try:
            return {"lat": float(row["lat"]["value"]), "lon": float(row["lon"]["value"])}
        except (KeyError, ValueError):
            pass
    if "coords" in row:
        m = re.match(r"Point\(([^ ]+) ([^ ]+)\)", row["coords"]["value"])
        if m:
            try:
                return {"lat": float(m.group(2)), "lon": float(m.group(1))}
            except ValueError:
                pass
    return None


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

    return {
        "wikidata_id": f"Q{qid}",
        "name": row.get("officialName", {}).get("value", ""),
        "year_established": _parse_year(row),
        "website": row.get("website", {}).get("value", ""),
        "wikipedia": multilang.get("en", ""),
        "wikipedia_multilang": multilang,
        "establishment_country": row.get("countryCode", {}).get("value", ""),
        "type": row.get("instanceOf", {}).get("value", ""),
        "image": row.get("image", {}).get("value", ""),
        "coordinates": _parse_coordinates(row),
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

    path = Path(output_path)
    existing_authority: dict[str, Any] | None = None
    existing_doc: dict[str, Any] = {}

    if path.exists():
        with path.open(encoding="utf-8") as f:
            existing_doc = yaml.safe_load(f) or {}
        authorities = existing_doc.get("authorities", [])
        if isinstance(authorities, list) and authorities:
            existing_authority = authorities[0]

    merged = wikidata_to_authority(qid, wikidata_data, existing_authority, force_wikidata)

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
    output = args.output or f"data/articles/Q{qid}.yaml"

    try:
        seed_yaml(qid, output, force_wikidata=args.force_wikidata, dry_run=args.dry_run)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
