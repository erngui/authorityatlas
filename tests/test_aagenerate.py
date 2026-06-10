from __future__ import annotations

import os
import shutil
import tempfile
from typing import Any

import pytest
from jinja2 import Template

from aagenerate import (
    generate_site,
    get_country_name,
    markdown_links_to_html,
    normalize_country_to_code,
    process_authority_fields,
    validate_authority,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

# ---------------------------------------------------------------------------
# markdown_links_to_html
# ---------------------------------------------------------------------------


def test_markdown_links_converts_single_link() -> None:
    result = markdown_links_to_html("[text](http://example.com)")
    assert result == '<a href="http://example.com" target="_blank">text</a>'


def test_markdown_links_passes_through_plain_text() -> None:
    assert markdown_links_to_html("no links here") == "no links here"


def test_markdown_links_converts_multiple_links() -> None:
    result = markdown_links_to_html("[a](http://a.com) and [b](http://b.com)")
    assert '<a href="http://a.com" target="_blank">a</a>' in result
    assert '<a href="http://b.com" target="_blank">b</a>' in result


def test_markdown_links_empty_string() -> None:
    assert markdown_links_to_html("") == ""


# ---------------------------------------------------------------------------
# normalize_country_to_code
# ---------------------------------------------------------------------------


def test_normalize_empty_string() -> None:
    assert normalize_country_to_code("") == ""


def test_normalize_valid_alpha2_passthrough() -> None:
    assert normalize_country_to_code("GB") == "GB"
    assert normalize_country_to_code("NL") == "NL"


def test_normalize_invalid_alpha2_does_not_passthrough_blindly() -> None:
    # An unrecognised 2-letter code is NOT returned as-is; it falls through to fuzzy resolution
    result = normalize_country_to_code("XX")
    assert result != "XX"


def test_normalize_special_case_england() -> None:
    assert normalize_country_to_code("England") == "GB"


def test_normalize_special_case_eu() -> None:
    assert normalize_country_to_code("European Union") == "EU"


def test_normalize_special_case_scotland() -> None:
    assert normalize_country_to_code("Scotland") == "GB"


def test_normalize_by_full_name() -> None:
    assert normalize_country_to_code("Netherlands") == "NL"


def test_normalize_unknown_name_returns_as_is(capsys: pytest.CaptureFixture[str]) -> None:
    result = normalize_country_to_code("Neverland")
    assert result == "Neverland"
    assert "Warning" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# get_country_name
# ---------------------------------------------------------------------------


def test_get_country_name_empty() -> None:
    assert get_country_name("") == ""


def test_get_country_name_special_eu() -> None:
    assert get_country_name("EU") == "European Union"


def test_get_country_name_known_code() -> None:
    assert "Kingdom" in get_country_name("GB")


def test_get_country_name_unknown_code_returns_as_is() -> None:
    assert get_country_name("XX") == "XX"


# ---------------------------------------------------------------------------
# process_authority_fields
# ---------------------------------------------------------------------------


def test_process_fields_converts_markdown_in_factoid() -> None:
    authority: dict[str, Any] = {"factoid": "[text](http://x.com)", "remit": "plain"}
    result = process_authority_fields(authority)
    assert "<a href=" in result["factoid"]
    assert result["remit"] == "plain"


def test_process_fields_converts_markdown_in_remit() -> None:
    authority: dict[str, Any] = {"factoid": "plain", "remit": "[see here](http://x.com)"}
    result = process_authority_fields(authority)
    assert "<a href=" in result["remit"]


def test_process_fields_skips_empty_values() -> None:
    authority: dict[str, Any] = {"factoid": "", "remit": ""}
    result = process_authority_fields(authority)
    assert result["factoid"] == ""
    assert result["remit"] == ""


def test_process_fields_skips_absent_fields() -> None:
    authority: dict[str, Any] = {}
    result = process_authority_fields(authority)
    assert result == {}


# ---------------------------------------------------------------------------
# validate_authority
# ---------------------------------------------------------------------------


def _valid() -> dict[str, Any]:
    return {
        "name": "Test Authority",
        "acronym": "TA",
        "remit": "Test remit",
        "type": "regulatory",
        "legal_basis_name": "Test Act",
        "legal_basis_link": "http://example.com",
        "establishment_country": "GB",
        "regional_remit": "national",
        "headquarters_city": "London",
        "headquarters_country": "GB",
        "headquarters_address": "123 Test St",
        "website": "http://example.com",
        "wikipedia": "http://en.wikipedia.org/wiki/Test",
        "year_established": 2000,
        "tags": ["test"],
    }


def test_validate_passes_for_valid_authority() -> None:
    validate_authority(_valid(), "test.yaml")  # must not raise


def test_validate_raises_for_missing_required_field() -> None:
    authority = _valid()
    del authority["name"]
    with pytest.raises(ValueError, match="Missing required field 'name'"):
        validate_authority(authority, "test.yaml")


def test_validate_raises_for_empty_required_field() -> None:
    authority = _valid()
    authority["name"] = ""
    with pytest.raises(ValueError, match="Empty required field 'name'"):
        validate_authority(authority, "test.yaml")


def test_validate_raises_for_none_required_field() -> None:
    authority = _valid()
    authority["website"] = None
    with pytest.raises(ValueError, match="Empty required field 'website'"):
        validate_authority(authority, "test.yaml")


def test_validate_raises_when_tags_not_list() -> None:
    authority = _valid()
    authority["tags"] = "maritime"
    with pytest.raises(TypeError, match="'tags' should be a list"):
        validate_authority(authority, "test.yaml")


def test_validate_raises_when_tags_empty() -> None:
    authority = _valid()
    authority["tags"] = []
    with pytest.raises(ValueError, match="'tags' list is empty"):
        validate_authority(authority, "test.yaml")


def test_validate_raises_when_year_not_int() -> None:
    authority = _valid()
    authority["year_established"] = "2000"
    with pytest.raises(TypeError, match="'year_established' should be an integer"):
        validate_authority(authority, "test.yaml")


def test_validate_raises_when_additional_resources_not_list() -> None:
    authority = _valid()
    authority["additional_resources"] = "not-a-list"
    with pytest.raises(TypeError, match="'additional_resources' should be a list"):
        validate_authority(authority, "test.yaml")


def test_validate_accepts_additional_resources_as_list() -> None:
    authority = _valid()
    authority["additional_resources"] = [{"title": "Example", "url": "http://example.com"}]
    validate_authority(authority, "test.yaml")  # must not raise


def test_validate_accepts_wikidata_id_as_string() -> None:
    authority = _valid()
    authority["wikidata_id"] = "Q225070"
    validate_authority(authority, "test.yaml")  # must not raise


def test_validate_raises_when_wikidata_id_not_string() -> None:
    authority = _valid()
    authority["wikidata_id"] = 225070
    with pytest.raises(TypeError, match="'wikidata_id' should be a string"):
        validate_authority(authority, "test.yaml")


def test_validate_accepts_valid_coordinates() -> None:
    authority = _valid()
    authority["coordinates"] = {"lat": 51.5074, "lon": -0.1278}
    validate_authority(authority, "test.yaml")  # must not raise


def test_validate_raises_when_coordinates_not_dict() -> None:
    authority = _valid()
    authority["coordinates"] = "51.5,-0.1"
    with pytest.raises(TypeError, match="'coordinates' should be a dict"):
        validate_authority(authority, "test.yaml")


def test_validate_raises_when_coordinates_missing_lat() -> None:
    authority = _valid()
    authority["coordinates"] = {"lon": -0.1278}
    with pytest.raises(ValueError, match="'coordinates' missing 'lat'"):
        validate_authority(authority, "test.yaml")


def test_validate_raises_when_coordinates_lat_not_number() -> None:
    authority = _valid()
    authority["coordinates"] = {"lat": "north", "lon": 0.0}
    with pytest.raises(TypeError, match="'coordinates.lat' should be a number"):
        validate_authority(authority, "test.yaml")


def test_validate_accepts_wikipedia_multilang_dict() -> None:
    authority = _valid()
    authority["wikipedia_multilang"] = {"fr": "http://fr.wikipedia.org/wiki/Test"}
    validate_authority(authority, "test.yaml")  # must not raise


def test_validate_raises_when_wikipedia_multilang_not_dict() -> None:
    authority = _valid()
    authority["wikipedia_multilang"] = "http://fr.wikipedia.org/wiki/Test"
    with pytest.raises(TypeError, match="'wikipedia_multilang' should be a dict"):
        validate_authority(authority, "test.yaml")


def test_validate_prints_missing_optional_fields(capsys: pytest.CaptureFixture[str]) -> None:
    validate_authority(_valid(), "test.yaml")
    output = capsys.readouterr().out
    assert "Optional fields not provided" in output


# ---------------------------------------------------------------------------
# generate_site (integration)
# ---------------------------------------------------------------------------


def test_generate_site_produces_html_files() -> None:
    tmp = tempfile.mkdtemp()
    out = os.path.join(tmp, "out")
    try:
        article_tmpl = Template("<html>{{ authority.name }}</html>")
        index_tmpl = Template("<html>{% for a in articles %}{{ a.name }}{% endfor %}</html>")
        count = generate_site(FIXTURES_DIR, out, index_tmpl, article_tmpl)
        assert count == 1
        assert os.path.isfile(os.path.join(out, "index.html"))
        article_path = os.path.join(out, "test_maritime_authority.html")
        assert os.path.isfile(article_path)
        with open(article_path, encoding="utf-8") as f:
            assert "Test Maritime Authority" in f.read()
    finally:
        shutil.rmtree(tmp)


def test_generate_site_includes_new_fields_in_json() -> None:
    import json

    tmp = tempfile.mkdtemp()
    out = os.path.join(tmp, "out")
    try:
        article_tmpl = Template("<html>{{ authority.name }}</html>")
        index_tmpl = Template("{{ articles | tojson }}")
        generate_site(FIXTURES_DIR, out, index_tmpl, article_tmpl)
        with open(os.path.join(out, "index.html"), encoding="utf-8") as f:
            articles = json.loads(f.read())
        assert len(articles) == 1
        a = articles[0]
        assert a["wikidata_id"] == "Q12345"
        assert a["coordinates"] == {"lat": 51.5074, "lon": -0.1278}
        assert a["headquarters_city"] == "London"
        assert "headquarters_country_name" in a
        assert "headquarters_address" in a
    finally:
        shutil.rmtree(tmp)


def test_generate_site_raises_for_invalid_yaml_structure() -> None:
    tmp = tempfile.mkdtemp()
    bad_input = os.path.join(tmp, "input")
    out = os.path.join(tmp, "out")
    os.makedirs(bad_input)
    bad_yaml = os.path.join(bad_input, "bad.yaml")
    with open(bad_yaml, "w", encoding="utf-8") as f:
        f.write("authorities: not-a-list\n")
    try:
        with pytest.raises(ValueError, match="Expected 'authorities' to be a list"):
            generate_site(bad_input, out, Template(""), Template(""))
    finally:
        shutil.rmtree(tmp)
