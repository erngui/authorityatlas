from __future__ import annotations

import json
import os
import re
from typing import Any

import pycountry
import yaml
from jinja2 import Template

INPUT_DIR = "data/articles"
OUTPUT_DIR = "docs"
TEMPLATES_DIR = "templates"
INDEX_TEMPLATE_FILE = os.path.join(TEMPLATES_DIR, "index_template.html")
ARTICLE_TEMPLATE_FILE = os.path.join(TEMPLATES_DIR, "article_template.html")

_SPECIAL_COUNTRY_CODES: dict[str, str] = {
    "European Union": "EU",
    "England": "GB",
    "Scotland": "GB",
    "Wales": "GB",
    "Northern Ireland": "GB",
}

_SPECIAL_COUNTRY_NAMES: dict[str, str] = {
    "EU": "European Union",
}


def markdown_links_to_html(text: str) -> str:
    """Convert markdown links [text](url) to HTML <a> tags."""
    pattern = r"\[([^\]]+)\]\(([^\)]+)\)"
    return re.sub(pattern, r'<a href="\2" target="_blank">\1</a>', text)


def normalize_country_to_code(country_value: str) -> str:
    """Convert country names to ISO 3166-1 alpha-2 codes. Pass through if already a valid code."""
    if not country_value:
        return country_value
    if len(country_value) == 2 and country_value.isupper():
        if pycountry.countries.get(alpha_2=country_value):
            return country_value
    if country_value in _SPECIAL_COUNTRY_CODES:
        return _SPECIAL_COUNTRY_CODES[country_value]
    try:
        return str(pycountry.countries.search_fuzzy(country_value)[0].alpha_2)
    except (LookupError, AttributeError, IndexError):
        print(f"  Warning: Could not find ISO code for country: {country_value}")
        return country_value


def get_country_name(country_code: str) -> str:
    """Get country display name from an ISO 3166-1 alpha-2 code."""
    if not country_code:
        return country_code
    if country_code in _SPECIAL_COUNTRY_NAMES:
        return _SPECIAL_COUNTRY_NAMES[country_code]
    country = pycountry.countries.get(alpha_2=country_code)
    return str(country.name) if country else country_code


def process_authority_fields(authority: dict[str, Any]) -> dict[str, Any]:
    """Convert markdown links to HTML in fields that allow rich text."""
    for field in ("factoid", "remit"):
        if authority.get(field):
            authority[field] = markdown_links_to_html(authority[field])
    return authority


def validate_authority(authority: dict[str, Any], filename: str) -> None:
    """Raise ValueError/TypeError if any required field is missing, empty, or wrong type."""
    required_fields = [
        "name",
        "acronym",
        "remit",
        "type",
        "legal_basis_name",
        "legal_basis_link",
        "establishment_country",
        "regional_remit",
        "headquarters_city",
        "headquarters_country",
        "headquarters_address",
        "website",
        "wikipedia",
        "year_established",
        "tags",
    ]
    for field in required_fields:
        if field not in authority:
            raise ValueError(f"Missing required field '{field}' in file: {filename}")
        if authority[field] in (None, ""):
            raise ValueError(f"Empty required field '{field}' in file: {filename}")
    if not isinstance(authority["tags"], list):
        raise TypeError(f"'tags' should be a list in file: {filename}")
    if not authority["tags"]:
        raise ValueError(f"'tags' list is empty in file: {filename}")
    if authority.get("additional_resources") is not None:
        if not isinstance(authority["additional_resources"], list):
            raise TypeError(f"'additional_resources' should be a list in file: {filename}")
    if not isinstance(authority["year_established"], int):
        raise TypeError(f"'year_established' should be an integer in file: {filename}")
    if authority.get("wikidata_id") is not None:
        if not isinstance(authority["wikidata_id"], str):
            raise TypeError(f"'wikidata_id' should be a string in file: {filename}")
    if authority.get("coordinates") is not None:
        coords = authority["coordinates"]
        if not isinstance(coords, dict):
            raise TypeError(f"'coordinates' should be a dict in file: {filename}")
        for key in ("lat", "lon"):
            if key not in coords:
                raise ValueError(f"'coordinates' missing '{key}' in file: {filename}")
            if not isinstance(coords[key], (int, float)):
                raise TypeError(f"'coordinates.{key}' should be a number in file: {filename}")
    if authority.get("wikipedia_multilang") is not None:
        if not isinstance(authority["wikipedia_multilang"], dict):
            raise TypeError(f"'wikipedia_multilang' should be a dict in file: {filename}")
    if authority.get("shortname") is not None:
        if not isinstance(authority["shortname"], str):
            raise TypeError(f"'shortname' should be a string in file: {filename}")
    optional_fields = [
        "factoid",
        "head_title",
        "predecessor_organizations",
        "image",
        "additional_resources",
        "wikidata_id",
        "coordinates",
        "wikipedia_multilang",
        "shortname",
    ]
    missing_optional = [f for f in optional_fields if not authority.get(f)]
    if missing_optional:
        print(f"  Optional fields not provided: {', '.join(missing_optional)}")
    print(f"Validated: {authority['name']}")


def generate_site(
    input_dir: str,
    output_dir: str,
    index_template: Template,
    article_template: Template,
) -> int:
    """Process all YAML authority files, write HTML pages, and return the count generated."""
    os.makedirs(output_dir, exist_ok=True)
    articles: list[dict[str, Any]] = []
    metadata_list: list[dict[str, Any]] = []

    for filename in os.listdir(input_dir):
        if not (filename.endswith(".yaml") or filename.endswith(".yml")):
            continue
        filepath = os.path.join(input_dir, filename)
        print(f"\nProcessing: {filename}")
        with open(filepath, encoding="utf-8") as f:
            data: Any = yaml.safe_load(f)
        if not isinstance(data.get("authorities"), list):
            raise ValueError(
                f"Expected 'authorities' to be a list in {filename}, "
                f"but got {type(data.get('authorities')).__name__}"
            )
        for authority in data["authorities"]:
            validate_authority(authority, filename)
            authority["establishment_country"] = normalize_country_to_code(
                authority["establishment_country"]
            )
            authority["headquarters_country"] = normalize_country_to_code(
                authority["headquarters_country"]
            )
            authority = process_authority_fields(authority)
            authority["establishment_country_name"] = get_country_name(
                authority["establishment_country"]
            )
            authority["headquarters_country_name"] = get_country_name(
                authority["headquarters_country"]
            )

            article_filename = f"{os.path.splitext(filename)[0]}.html"
            authority["display_name"] = (
                authority.get("shortname")
                or authority.get("acronym")
                or authority["name"]
            )

            article_output = article_template.render(authority=authority)
            with open(os.path.join(output_dir, article_filename), "w", encoding="utf-8") as outf:
                outf.write(article_output)
            print(f"  -> Generated: {article_filename}")

            articles.append(
                {
                    "name": authority["name"],
                    "display_name": authority["display_name"],
                    "acronym": authority.get("acronym", ""),
                    "remit": authority.get("remit", ""),
                    "factoid": authority.get("factoid", ""),
                    "type": authority.get("type", ""),
                    "establishment_country": authority["establishment_country"],
                    "establishment_country_name": get_country_name(
                        authority["establishment_country"]
                    ),
                    "year_established": authority.get("year_established", ""),
                    "website": authority.get("website", ""),
                    "wikipedia": authority.get("wikipedia", ""),
                    "filename": article_filename,
                    "coordinates": authority.get("coordinates"),
                    "wikidata_id": authority.get("wikidata_id", ""),
                    "headquarters_city": authority.get("headquarters_city", ""),
                    "headquarters_country_name": authority.get(
                        "headquarters_country_name", ""
                    ),
                    "headquarters_address": authority.get("headquarters_address", ""),
                }
            )
            metadata_list.append(
                {
                    "search_blob": json.dumps(
                        {
                            "name": authority["name"],
                            "acronym": authority.get("acronym", ""),
                            "remit": authority.get("remit", ""),
                            "factoid": authority.get("factoid", ""),
                            "type": authority.get("type", ""),
                            "tags": authority.get("tags", []),
                            "establishment_country": authority["establishment_country"],
                            "regional_remit": authority.get("regional_remit", ""),
                            "headquarters_city": authority.get("headquarters_city", ""),
                            "headquarters_country": authority["headquarters_country"],
                            "headquarters_address": authority.get("headquarters_address", ""),
                            "year_established": authority.get("year_established", ""),
                            "predecessor_organizations": authority.get(
                                "predecessor_organizations", ""
                            ),
                        },
                        ensure_ascii=False,
                    ),
                    "filename": article_filename,
                    "name": authority["name"],
                    "year_established": authority.get("year_established", 0),
                }
            )

    articles.sort(key=lambda x: str(x["name"]))
    index_output = index_template.render(
        articles=articles,
        metadata=json.dumps(metadata_list, ensure_ascii=False),
    )
    with open(os.path.join(output_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_output)

    return len(articles)


def main() -> None:  # pragma: no cover
    with open(INDEX_TEMPLATE_FILE, encoding="utf-8") as f:
        index_template = Template(f.read())
    with open(ARTICLE_TEMPLATE_FILE, encoding="utf-8") as f:
        article_template = Template(f.read())

    count = generate_site(INPUT_DIR, OUTPUT_DIR, index_template, article_template)
    print("\nSite generation complete!")
    print(f"   Generated {count} authority page(s)")
    print(f"   Output directory: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
