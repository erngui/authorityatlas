from __future__ import annotations

import json
import os
import tempfile
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import yaml

import aafetch

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

_FULL_BINDINGS: list[dict[str, Any]] = [
    {
        "officialName": {"value": "Test Authority"},
        "shortName": {"value": "TA"},
        "inception": {"value": "1944-04-04T00:00:00Z"},
        "website": {"value": "https://example.org"},
        "lat": {"value": "45.4215"},
        "lon": {"value": "-75.6972"},
        "countryCode": {"value": "CA"},
        "adminTerritory": {"value": "Ontario"},
        "instanceOf": {"value": "intergovernmental organization"},
        "image": {"value": "https://commons.wikimedia.org/wiki/File:Logo.png"},
        "enwiki": {"value": "https://en.wikipedia.org/wiki/Test_Authority"},
        "frwiki": {"value": "https://fr.wikipedia.org/wiki/Test_Autorite"},
        "legalBasisName": {"value": "Convention on Test Authority"},
        "legalBasisLink": {"value": "https://example.org/treaty"},
        "fieldOfWork": {"value": "air transport"},
        "industry": {"value": "transport"},
    }
]


def _mock_response(bindings: list[dict[str, Any]]) -> dict[str, Any]:
    return {"results": {"bindings": bindings}}


# ---------------------------------------------------------------------------
# sparql_query (unit: mocked at urllib level, tested via fetch_entity)
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_sparql() -> Any:
    with patch("aafetch.sparql_query") as mock:
        mock.return_value = _mock_response(_FULL_BINDINGS)
        yield mock


# ---------------------------------------------------------------------------
# fetch_entity
# ---------------------------------------------------------------------------


def test_fetch_entity_parses_full_response(mock_sparql: MagicMock) -> None:
    result = aafetch.fetch_entity("170918")
    assert result["wikidata_id"] == "Q170918"
    assert result["name"] == "Test Authority"
    assert result["year_established"] == 1944
    assert result["website"] == "https://example.org"
    assert result["establishment_country"] == "CA"
    assert result["type"] == "intergovernmental organization"
    assert result["image"] == "https://commons.wikimedia.org/wiki/File:Logo.png"


def test_fetch_entity_parses_acronym_from_p1813(mock_sparql: MagicMock) -> None:
    result = aafetch.fetch_entity("170918")
    assert result["acronym"] == "TA"


def test_fetch_entity_falls_back_to_rdfs_label_and_warns(
    mock_sparql: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    bindings = [{k: v for k, v in _FULL_BINDINGS[0].items() if k != "officialName"}]
    bindings[0]["entityLabel"] = {"value": "Fallback Label"}
    mock_sparql.return_value = _mock_response(bindings)
    result = aafetch.fetch_entity("170918")
    assert result["name"] == "Fallback Label"
    captured = capsys.readouterr()
    assert "WARNING" in captured.out
    assert "P1448" in captured.out


def test_fetch_entity_parses_coordinates(mock_sparql: MagicMock) -> None:
    result = aafetch.fetch_entity("170918")
    assert result["coordinates"] == {"lat": 45.4215, "lon": -75.6972}


def test_fetch_entity_handles_missing_coordinates(mock_sparql: MagicMock) -> None:
    bindings = [{k: v for k, v in _FULL_BINDINGS[0].items() if k not in ("lat", "lon")}]
    mock_sparql.return_value = _mock_response(bindings)
    result = aafetch.fetch_entity("170918")
    assert result["coordinates"] is None


def test_fetch_entity_handles_missing_inception(mock_sparql: MagicMock) -> None:
    bindings = [{k: v for k, v in _FULL_BINDINGS[0].items() if k != "inception"}]
    mock_sparql.return_value = _mock_response(bindings)
    result = aafetch.fetch_entity("170918")
    assert result["year_established"] is None


def test_fetch_entity_parses_multilang_wikipedia(mock_sparql: MagicMock) -> None:
    result = aafetch.fetch_entity("170918")
    assert result["wikipedia"] == "https://en.wikipedia.org/wiki/Test_Authority"
    assert result["wikipedia_multilang"]["fr"] == "https://fr.wikipedia.org/wiki/Test_Autorite"
    assert "de" not in result["wikipedia_multilang"]


def test_fetch_entity_raises_for_empty_results(mock_sparql: MagicMock) -> None:
    mock_sparql.return_value = _mock_response([])
    with pytest.raises(ValueError, match="No Wikidata results"):
        aafetch.fetch_entity("99999999")


def test_fetch_entity_raises_for_invalid_qid(mock_sparql: MagicMock) -> None:
    with pytest.raises(ValueError, match="Invalid Wikidata Q-ID"):
        aafetch.fetch_entity("not-a-number")


def test_fetch_entity_raises_for_injected_qid(mock_sparql: MagicMock) -> None:
    with pytest.raises(ValueError, match="Invalid Wikidata Q-ID"):
        aafetch.fetch_entity("12345} UNION { ?x ?y ?z")


def test_fetch_entity_uses_p276_location_coordinates(mock_sparql: MagicMock) -> None:
    bindings = [{k: v for k, v in _FULL_BINDINGS[0].items() if k not in ("lat", "lon")}]
    bindings[0]["locLat"] = {"value": "52.164647"}
    bindings[0]["locLon"] = {"value": "4.4655"}
    mock_sparql.return_value = _mock_response(bindings)
    result = aafetch.fetch_entity("2619632")
    assert result["coordinates"] == {"lat": 52.164647, "lon": 4.4655}


def test_fetch_entity_uses_wkt_coordinate_fallback(mock_sparql: MagicMock) -> None:
    bindings = [
        {k: v for k, v in _FULL_BINDINGS[0].items() if k not in ("lat", "lon")}
    ]
    bindings[0]["coords"] = {"value": "Point(-75.6972 45.4215)"}
    mock_sparql.return_value = _mock_response(bindings)
    result = aafetch.fetch_entity("170918")
    assert result["coordinates"] == {"lat": 45.4215, "lon": -75.6972}


def test_fetch_entity_handles_malformed_inception_date(mock_sparql: MagicMock) -> None:
    bindings = [{**_FULL_BINDINGS[0], "inception": {"value": "not-a-date"}}]
    mock_sparql.return_value = _mock_response(bindings)
    result = aafetch.fetch_entity("170918")
    assert result["year_established"] is None


def test_fetch_entity_parses_legal_basis_from_p457(mock_sparql: MagicMock) -> None:
    result = aafetch.fetch_entity("170918")
    assert result["legal_basis_name"] == "Convention on Test Authority"
    assert result["legal_basis_link"] == "https://example.org/treaty"


def test_fetch_entity_parses_suggested_tags_from_p101_p452(mock_sparql: MagicMock) -> None:
    result = aafetch.fetch_entity("170918")
    assert result["_suggested_tags"] == ["air transport", "transport"]


def test_fetch_entity_suggested_tags_empty_when_absent(mock_sparql: MagicMock) -> None:
    bindings = [
        {k: v for k, v in _FULL_BINDINGS[0].items()
         if k not in ("fieldOfWork", "industry")}
    ]
    mock_sparql.return_value = _mock_response(bindings)
    result = aafetch.fetch_entity("170918")
    assert result["_suggested_tags"] == []


def test_fetch_entity_handles_missing_p457(mock_sparql: MagicMock) -> None:
    bindings = [
        {k: v for k, v in _FULL_BINDINGS[0].items()
         if k not in ("legalBasisName", "legalBasisLink")}
    ]
    mock_sparql.return_value = _mock_response(bindings)
    result = aafetch.fetch_entity("170918")
    assert result["legal_basis_name"] == ""
    assert result["legal_basis_link"] == ""


# ---------------------------------------------------------------------------
# wikidata_to_authority (merge logic)
# ---------------------------------------------------------------------------


def _wikidata_data() -> dict[str, Any]:
    return {
        "wikidata_id": "Q170918",
        "name": "ICAO",
        "year_established": 1944,
        "website": "https://icao.int",
        "wikipedia": "https://en.wikipedia.org/wiki/ICAO",
        "wikipedia_multilang": {"en": "https://en.wikipedia.org/wiki/ICAO"},
        "establishment_country": "CA",
        "type": "intergovernmental organization",
        "image": "",
        "coordinates": {"lat": 45.4215, "lon": -75.6972},
    }


def test_wikidata_to_authority_merge_preserves_curated() -> None:
    existing = {"remit": "Manages global aviation standards.", "website": ""}
    result = aafetch.wikidata_to_authority("170918", _wikidata_data(), existing)
    assert result["remit"] == "Manages global aviation standards."
    assert result["website"] == "https://icao.int"


def test_wikidata_to_authority_merge_fills_empty_fields() -> None:
    existing: dict[str, Any] = {"website": ""}
    result = aafetch.wikidata_to_authority("170918", _wikidata_data(), existing)
    assert result["website"] == "https://icao.int"
    assert result["wikidata_id"] == "Q170918"


def test_wikidata_to_authority_force_wikidata_overwrites_curated() -> None:
    existing = {"remit": "Old remit."}
    data = {**_wikidata_data(), "remit": "New remit from Wikidata."}
    result = aafetch.wikidata_to_authority("170918", data, existing, force_wikidata=True)
    assert result["remit"] == "New remit from Wikidata."


def test_wikidata_to_authority_no_existing_creates_from_scratch() -> None:
    result = aafetch.wikidata_to_authority("170918", _wikidata_data())
    assert result["name"] == "ICAO"
    assert result["coordinates"] == {"lat": 45.4215, "lon": -75.6972}


def test_wikidata_to_authority_skips_empty_wikidata_values() -> None:
    data = {**_wikidata_data(), "image": "", "type": None}
    result = aafetch.wikidata_to_authority("170918", data)
    assert "image" not in result or result.get("image") == ""
    assert result.get("type") != "should not be set"


# ---------------------------------------------------------------------------
# seed_yaml
# ---------------------------------------------------------------------------


def test_seed_yaml_writes_file(mock_sparql: MagicMock) -> None:
    mock_sparql.return_value = _mock_response(_FULL_BINDINGS)
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "test_authority.yaml")
        aafetch.seed_yaml("170918", out)
        assert os.path.isfile(out)
        with open(out, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
        assert doc["authorities"][0]["wikidata_id"] == "Q170918"
        assert doc["authorities"][0]["name"] == "Test Authority"


def test_seed_yaml_new_file_uses_scaffold(mock_sparql: MagicMock) -> None:
    mock_sparql.return_value = _mock_response(_FULL_BINDINGS)
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "new_authority.yaml")
        aafetch.seed_yaml("170918", out)
        with open(out, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
    authority = doc["authorities"][0]
    # Wikidata fields seeded
    assert authority["name"] == "Test Authority"
    assert authority["acronym"] == "TA"
    assert authority["wikidata_id"] == "Q170918"
    # All scaffold fields present (even empty ones)
    for field in aafetch._AUTHORITY_SCAFFOLD:
        assert field in authority, f"scaffold field '{field}' missing from new file"


def test_seed_yaml_dry_run_does_not_write(
    mock_sparql: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    mock_sparql.return_value = _mock_response(_FULL_BINDINGS)
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "should_not_exist.yaml")
        aafetch.seed_yaml("170918", out, dry_run=True)
        assert not os.path.isfile(out)
    captured = capsys.readouterr()
    assert "Q170918" in captured.out


def test_geocode_nominatim_returns_coordinates() -> None:
    mock_resp = [{"lat": "52.164647", "lon": "4.4655"}]
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_cm)
        mock_cm.__exit__ = MagicMock(return_value=False)
        mock_cm.read.return_value = json.dumps(mock_resp).encode()
        mock_urlopen.return_value = mock_cm
        result = aafetch.geocode_nominatim("Archimedesweg 1, 2333 CM Leiden")
    assert result == {"lat": 52.164647, "lon": 4.4655}


def test_geocode_nominatim_returns_none_on_empty_results() -> None:
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_cm = MagicMock()
        mock_cm.__enter__ = MagicMock(return_value=mock_cm)
        mock_cm.__exit__ = MagicMock(return_value=False)
        mock_cm.read.return_value = b"[]"
        mock_urlopen.return_value = mock_cm
        result = aafetch.geocode_nominatim("Unknown place XYZ")
    assert result is None


def test_geocode_nominatim_returns_none_on_network_error() -> None:
    import urllib.error
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("timeout")):
        result = aafetch.geocode_nominatim("Somewhere")
    assert result is None


def test_seed_yaml_falls_back_to_nominatim_when_no_coordinates(
    mock_sparql: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    bindings = [{k: v for k, v in _FULL_BINDINGS[0].items() if k not in ("lat", "lon")}]
    mock_sparql.return_value = _mock_response(bindings)
    with patch("aafetch.geocode_nominatim", return_value={"lat": 51.5, "lon": -0.1}):
        with patch("aafetch.time") as mock_time:
            mock_time.sleep = MagicMock()
            with tempfile.TemporaryDirectory() as tmp:
                out = os.path.join(tmp, "authority.yaml")
                aafetch.seed_yaml("170918", out)
                with open(out, encoding="utf-8") as f:
                    doc = yaml.safe_load(f)
    assert doc["authorities"][0]["coordinates"] == {"lat": 51.5, "lon": -0.1}


def test_seed_yaml_prints_suggested_tags(
    mock_sparql: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    mock_sparql.return_value = _mock_response(_FULL_BINDINGS)
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "authority.yaml")
        aafetch.seed_yaml("170918", out)
    captured = capsys.readouterr()
    assert "Suggested sector tags" in captured.out
    assert "air transport" in captured.out
    assert "transport" in captured.out


def test_seed_yaml_warns_when_coordinates_from_p276(
    mock_sparql: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    bindings = [{k: v for k, v in _FULL_BINDINGS[0].items() if k not in ("lat", "lon")}]
    bindings[0]["locLat"] = {"value": "52.164647"}
    bindings[0]["locLon"] = {"value": "4.4655"}
    mock_sparql.return_value = _mock_response(bindings)
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "authority.yaml")
        aafetch.seed_yaml("170918", out)
    captured = capsys.readouterr()
    assert "P276" in captured.out
    assert "WARNING" in captured.out


def test_seed_yaml_notes_when_coordinates_from_wkt(
    mock_sparql: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    bindings = [{k: v for k, v in _FULL_BINDINGS[0].items() if k not in ("lat", "lon")}]
    bindings[0]["coords"] = {"value": "Point(-75.6972 45.4215)"}
    mock_sparql.return_value = _mock_response(bindings)
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "authority.yaml")
        aafetch.seed_yaml("170918", out)
    captured = capsys.readouterr()
    assert "WKT" in captured.out
    assert "NOTE" in captured.out


def test_seed_yaml_nominatim_uses_headquarters_address(
    mock_sparql: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    bindings = [{k: v for k, v in _FULL_BINDINGS[0].items() if k not in ("lat", "lon")}]
    mock_sparql.return_value = _mock_response(bindings)
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "authority.yaml")
        existing = {
            "authorities": [
                {
                    "headquarters_address": "Archimedesweg 1, 2333 CM Leiden",
                    "wikidata_id": "Q170918",
                }
            ]
        }
        with open(out, "w", encoding="utf-8") as f:
            yaml.dump(existing, f)
        with patch("aafetch.geocode_nominatim", return_value={"lat": 52.164647, "lon": 4.4655}):
            with patch("aafetch.time") as mock_time:
                mock_time.sleep = MagicMock()
                aafetch.seed_yaml("170918", out)
    captured = capsys.readouterr()
    assert "address" in captured.out
    assert "name+country" not in captured.out


def test_seed_yaml_nominatim_no_results_prints_message(
    mock_sparql: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    bindings = [{k: v for k, v in _FULL_BINDINGS[0].items() if k not in ("lat", "lon")}]
    mock_sparql.return_value = _mock_response(bindings)
    with patch("aafetch.geocode_nominatim", return_value=None):
        with patch("aafetch.time") as mock_time:
            mock_time.sleep = MagicMock()
            with tempfile.TemporaryDirectory() as tmp:
                out = os.path.join(tmp, "authority.yaml")
                aafetch.seed_yaml("170918", out)
    captured = capsys.readouterr()
    assert "no results" in captured.out


def test_wikidata_to_authority_skips_curated_field_without_force() -> None:
    data = {**_wikidata_data(), "remit": "Wikidata remit."}
    result = aafetch.wikidata_to_authority("170918", data)
    assert result.get("remit") is None


def test_seed_yaml_creates_parent_dirs(mock_sparql: MagicMock) -> None:
    mock_sparql.return_value = _mock_response(_FULL_BINDINGS)
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "subdir", "authority.yaml")
        aafetch.seed_yaml("170918", out)
        assert os.path.isfile(out)


def test_seed_yaml_existing_empty_authorities_list(mock_sparql: MagicMock) -> None:
    mock_sparql.return_value = _mock_response(_FULL_BINDINGS)
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "authority.yaml")
        existing = {"authorities": []}
        with open(out, "w", encoding="utf-8") as f:
            yaml.dump(existing, f)
        aafetch.seed_yaml("170918", out)
        with open(out, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
        assert doc["authorities"][0]["name"] == "Test Authority"


def test_seed_yaml_merges_with_existing_file(mock_sparql: MagicMock) -> None:
    mock_sparql.return_value = _mock_response(_FULL_BINDINGS)
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "authority.yaml")
        existing = {
            "authorities": [
                {
                    "remit": "Manages global aviation.",
                    "tags": ["aviation"],
                    "wikidata_id": "Q170918",
                }
            ]
        }
        with open(out, "w", encoding="utf-8") as f:
            yaml.dump(existing, f)
        aafetch.seed_yaml("170918", out)
        with open(out, encoding="utf-8") as f:
            doc = yaml.safe_load(f)
        authority = doc["authorities"][0]
        assert authority["remit"] == "Manages global aviation."
        assert authority["tags"] == ["aviation"]
        assert authority["name"] == "Test Authority"
