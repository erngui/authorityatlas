# Authority Atlas — Backlog

This is the living backlog for Authority Atlas development. Items within each section
are ordered by implementation sequence — earlier items unblock later ones.

The guiding question for every item: *does this keep the data open, the site lightweight,
and the contribution workflow simple?*

---

## Foundation (complete)

- [x] Project scaffold: `pyproject.toml`, runtime deps (`jinja2`, `pyyaml`, `pycountry`), MIT + CC BY-SA dual licence
- [x] Quality gate: `ruff` (lint + format), `mypy` (strict), `bandit` (security), `pytest-cov` (90% branch threshold), `pip-audit` (dependency CVEs), `pre-commit` hooks wiring all of the above
- [x] Authority YAML schema: 15 required fields, 9 optional fields, type validation, tag vocabulary enforcement
- [x] `aagenerate.py`: schema validation, ISO country code normalisation via `pycountry`, markdown-link rendering in `remit` and `factoid`, Jinja2 site generation
- [x] `aafetch.py`: Wikidata SPARQL seeder with P625 direct coordinates, P276→P625 linked-location fallback, WKT parsing, OSM Nominatim geocoding fallback; curated-field protection; diagnostic coordinate warnings
- [x] Wikidata properties seeded: P1448 (official name), P1813 (acronym), P571 (inception), P856 (website), P625 (coordinates), P276 (location link), P17/P297 (country), P457/P953 (legal basis), P101/P452 (tag hints — advisory only)
- [x] `rdfs:label` name fallback with warning when P1448 is absent
- [x] Controlled tag vocabulary: 25 domain tags, 11 function tags; `aagenerate.py` warns on any tag outside the lists
- [x] `shortname` field and `display_name` strategy (`shortname` → `acronym` → `name`)
- [x] URL slug derived from YAML filename; full legal name demoted to subtitle when `shortname` is present
- [x] Markdown link support (`[text](url)`) in `remit` and `factoid`; character-count warnings for card readability
- [x] Jinja2 templates: index with client-side search (embedded JSON), tag-dropdown filter, global Leaflet map, card grid; per-authority pages with single-marker map, info grid, factoid, remit, and multilingual Wikipedia links
- [x] 5 seed authorities: Trinity House, ICAO, Rijnland, ISA, WHO
- [x] GitHub Issue template for authority proposals (`.github/ISSUE_TEMPLATE/propose_authority.yml`)
- [x] `ARCHITECTURE.md` documenting design decisions, data flow, schema, and tag vocabulary
- [x] `BACKLOG.md` (this file)

---

## Milestone 1 — CI pipeline

Automate the quality gate so every push to `main` and every pull request is verified
without relying on contributors to run checks locally.

- [ ] GitHub Actions workflow (`.github/workflows/ci.yml`): triggered on push and pull_request to `main`
  - `ruff check .` and `ruff format --check .`
  - `mypy aafetch.py aagenerate.py`
  - `bandit -r aafetch.py aagenerate.py`
  - `pip-audit`
  - `python -m pytest --cov=. --cov-fail-under=90`
  - `python aagenerate.py` — validates all data files pass without errors or tag warnings
- [ ] Pin Python version in the workflow to match `pyproject.toml` (`>=3.10`); test on 3.10 and 3.12
- [ ] Add a CI status badge to `README.md`

**Exit criterion:** A push with a YAML file containing an invalid tag or a missing required field fails CI with a clear error message before it can reach `main`.

---

## Milestone 2 — Dataset expansion

Grow the dataset to make the map and tag filter genuinely useful.

- [ ] Reach 20 authorities, with at least one authority carrying each of the most common domain tags (marine, health, transport, finance, environment)
- [ ] Ensure every authority in `data/articles/` has coordinates (so all appear on the map)
- [ ] Identify and add at least one authority with `other` as its domain tag, to validate the fallback works in the UI

**Suggested additions (not exhaustive):**

| Authority | Domain | Function | Wikidata |
|---|---|---|---|
| IMO (International Maritime Organization) | marine | regulation, safety | Q182633 |
| WMO (World Meteorological Organization) | atmospheric | coordination, monitoring | Q170918 |
| IAEA (International Atomic Energy Agency) | nuclear | monitoring, safety | Q170918 |
| ILO (International Labour Organization) | labour | regulation, rights-protection | Q7814 |
| IMF (International Monetary Fund) | finance | coordination | Q3783 |
| WTO (World Trade Organization) | trade | regulation, arbitration-judicial | Q7825 |
| WIPO (World Intellectual Property Organization) | intellectual-property | regulation, standard-setting | Q170918 |
| UNESCO | cultural-heritage, education | coordination | Q7296 |
| FAO (Food and Agriculture Organization) | food-agriculture | coordination, development-aid | Q82322 |
| ITU (International Telecommunication Union) | telecommunications | regulation, standard-setting | Q170918 |

*(QIDs above are illustrative; verify before running `aafetch.py`.)*

**Exit criterion:** The index map shows markers spread across at least three continents. The tag filter dropdown produces non-empty results for at least 10 distinct tags.

---

## Later / Unscheduled

These are captured so they are not lost, but have no target milestone yet.

**Data enrichment**
- Additional Wikidata properties in `aafetch.py`: P155/P156 (predecessor/successor organisations), P749 (parent organisation), P18 (logo/image)
- Bulk-fetch mode: accept a file of QIDs and seed each in one run
- `aagenerate --check` flag: validate all YAML files and report errors without writing output (useful in CI without generating the full site)

**Site features**
- Full-text search across `remit` and `factoid` (beyond the current tag-dropdown filter)
- Authority relationship visualisation: `predecessor_organizations` rendered as a graph or linked list
- Per-type filtered views (e.g. `/by-tag/marine.html` listing all marine authorities)
- Print-friendly stylesheet for individual authority pages

**Infrastructure**
- GitHub Pages deployment workflow: push to `main` triggers `aagenerate.py` and publishes `docs/` automatically
- Dependabot or Renovate for dev dependency updates (ruff, mypy, bandit, pip-audit, pre-commit hook revs)

**Contribution workflow**
- `aafetch.py --list-missing` mode: scan `data/articles/` and report any required field that is empty or absent across all files
- Contributor-facing validator script that runs `aagenerate.py` in check mode before a PR is opened, so contributors see errors locally without needing the full dev toolchain
