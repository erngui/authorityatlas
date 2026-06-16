# Authority Atlas — Architecture

## Guiding principles

**Data is the product.** The YAML files in `data/articles/` are the authoritative record.
Everything in `docs/` is derived output and can be regenerated at any time. If the
generated HTML and the YAML disagree, the YAML is right.

**Minimal runtime footprint.** The site generator depends on exactly three runtime
packages: `jinja2`, `pyyaml`, and `pycountry`. Adding a runtime dependency increases
maintenance, deployment, and security burden and requires explicit maintainer approval.

**Network access only at authoring time.** `aagenerate.py` never calls the network.
Only `aafetch.py` does, and only when a maintainer explicitly invokes it to seed or
refresh a YAML file. This keeps site generation fast, deterministic, and offline-capable.

**Curated over automated.** Wikidata seeds mechanical facts — name, coordinates, website,
year, Wikipedia links. Human authors supply the editorial judgment that makes the site
useful: `remit`, `factoid`, `tags`, and `legal_basis_*`. The tool enforces this split.

**Static over dynamic.** The site is pre-rendered HTML. There is no server, no database,
no request-time logic. A static site is fast to serve, easy to audit, and requires no
infrastructure beyond a file host.

**Schema enforced at generation time.** `validate_authority()` raises an error for any
YAML file with a missing or malformed required field. Bad data never ships.

---

## Non-negotiable constraints

These define the shape of the project. A change that violates them is an architecture
change, not an implementation detail.

**`aagenerate.py` must never make network calls.** It reads local files and writes local
files. If generation requires fetching remote data, that fetch belongs in `aafetch.py`.

**YAML filename = URL slug.** The file `data/articles/icao.yaml` generates `docs/icao.html`
at the public URL `/icao.html`. Renaming a YAML file breaks every external link that
cites the old URL. Never rename a YAML file without a redirect strategy.

**Curated fields are protected.** `aafetch.py` will never overwrite the fields listed in
`_CURATED_FIELDS` unless `--force-wikidata` is explicitly passed. These are the fields
that reflect human editorial judgment and must not be silently overwritten by automation.

**Tags must come from the controlled vocabulary.** `aagenerate.py` warns on any tag not
in `_DOMAIN_TAGS` or `_FUNCTION_TAGS`. Do not invent new tags in data files; request
additions via a GitHub Issue instead.

**90% branch coverage is a hard gate, not a target.** The CI check fails if coverage
falls below this threshold. Do not write code that cannot be tested.

---

## System overview

```
Wikidata SPARQL  /  OSM Nominatim
         │
         ▼  (authoring time only — never during site generation)
      aafetch.py
         │
         ▼
data/articles/*.yaml          ← source of truth; edit here
         │
         ▼
    aagenerate.py
    (validate → normalise → render)
         │
         ▼
      docs/*.html              ← generated output; never edit by hand
```

---

## Two-tool design

**`aafetch.py`** is a maintainer tool. It makes network calls, queries the Wikidata
SPARQL endpoint, falls back to OSM Nominatim for geocoding, and merges the results into
a YAML file on disk. It is never imported or called by `aagenerate.py`. Run it once to
seed a new authority or to refresh mechanical fields.

**`aagenerate.py`** is the site generator. It reads YAML files, validates them, normalises
country codes via `pycountry`, converts markdown links in `remit` and `factoid` to HTML,
renders Jinja2 templates, and writes the static site to `docs/`. It has no network
access and no side effects beyond writing to `docs/`.

The split is intentional: it keeps generation fast and hermetic, and it makes the network
dependency explicit and auditable.

---

## Authority schema

Each YAML file under `data/articles/` contains one authority. Use `trinity_house.yaml`
as the canonical template — it documents every field with inline comments.

### Required fields (15)

| Field | Type | Source |
|---|---|---|
| `name` | string | Wikidata P1448 / rdfs:label |
| `acronym` | string | Curated (aafetch seeds P1813 for new files) |
| `type` | string | Wikidata `instanceOf` label |
| `remit` | string | Curated — ≤ 400 visible chars |
| `legal_basis_name` | string | Curated (aafetch seeds P457 for new files) |
| `legal_basis_link` | string | Curated (aafetch seeds P457/P953 for new files) |
| `establishment_country` | string | Wikidata P17/P297 (ISO 3166-1 alpha-2 or full name) |
| `regional_remit` | string | Curated |
| `headquarters_city` | string | Curated |
| `headquarters_country` | string | Curated |
| `headquarters_address` | string | Curated |
| `website` | string | Wikidata P856 |
| `wikipedia` | string | Wikidata sitelink (English) |
| `year_established` | integer | Wikidata P571 |
| `tags` | list of strings | Curated — 2–5 tags from controlled vocabulary |

### Optional fields (9)

| Field | Type | Source |
|---|---|---|
| `factoid` | string | Curated — ≤ 250 visible chars |
| `shortname` | string | Curated — used as page `<h1>` when present |
| `head_title` | string | Curated — e.g. "Secretary-General" |
| `predecessor_organizations` | string | Curated |
| `image` | string | Wikidata P18 (Wikimedia Commons URL) |
| `additional_resources` | list of `{name, description, link}` | Curated |
| `wikidata_id` | string | Wikidata (e.g. `Q170918`) |
| `coordinates` | `{lat: float, lon: float}` | Wikidata P625 / Nominatim fallback |
| `wikipedia_multilang` | `{lang: url}` | Wikidata sitelinks (11 languages) |

### Curated fields

The following fields are owned by human authors. `aafetch.py` never overwrites them
unless `--force-wikidata` is passed — it will only fill them when creating a new file
as scaffolding:

```
remit, factoid, shortname, acronym, legal_basis_name, legal_basis_link,
regional_remit, tags, additional_resources, head_title, predecessor_organizations,
headquarters_city, headquarters_country, headquarters_address
```

All other fields are Wikidata-sourced and may be refreshed by running `aafetch.py`.

---

## Tag vocabulary

Tags are the primary navigation and filtering mechanism. They must be drawn exclusively
from two disjoint lists enforced in `aagenerate.py`.

**Rules:**
- Assign 2–5 tags per authority. 2–3 is ideal; 5 is the maximum.
- Every authority must carry at least one domain tag and at least one function tag.
- Do not invent tags. If nothing fits, use `other` for domain and open a GitHub Issue.
- `aagenerate.py` warns on any tag outside these lists; warnings block CI.

### Domain tags (25) — what realm does this authority operate in?

```
marine, atmospheric, space, terrestrial, freshwater, biodiversity,
food-agriculture, health, labour, finance, trade, energy, nuclear,
transport, telecommunications, cultural-heritage, education,
intellectual-property, justice, civil-society, industrial-development,
digital, sport, media, other
```

### Function tags (11) — what does this authority do?

```
regulation, standard-setting, conservation, coordination, monitoring,
safety, development-aid, rights-protection, research, scientific-advisory,
arbitration-judicial
```

**Distinction:** `research` = produces original science.
`scientific-advisory` = synthesises existing evidence and issues expert opinions.
A body may carry both.

---

## Coordinate handling

`aafetch.py` attempts four sources in order, printing a diagnostic for each:

1. **`Coordinates [P625]`** — direct from the authority's Wikidata entry. Best.
2. **`Coordinates [P276→P625]`** + WARNING — from a linked building or location item.
   Verify they match the actual headquarters address before committing.
3. **WKT parsing** — raw coordinate text from the SPARQL result. Verify.
4. **`Nominatim (name+country)`** + WARNING — no Wikidata coordinates found; the
   result may be a city centroid rather than the real address. Replace if possible.

If none of these yield a result, `aafetch.py` omits the `coordinates` field. The
authority will not appear on the index map until coordinates are added manually.

---

## URL slug strategy

The YAML filename (without `.yaml`) becomes the HTML filename and the public URL path.

```
data/articles/trinity_house.yaml  →  docs/trinity_house.html  →  /trinity_house.html
```

`aafetch.py` derives the default output path from the authority's name or acronym using
`slugify`-style lowercasing and underscore substitution. Once a file is committed, its
name is permanent. Never rename a YAML file — doing so breaks every external link that
cites the old URL. If a rename is ever necessary, add a redirect at the hosting layer
before removing the old file.

---

## Template system

Three Jinja2 templates live in `templates/`. They are rendered at generation time by
`aagenerate.py` — there is no server-side rendering at request time.

| Template | Rendered to |
|---|---|
| `index_template.html` | `docs/index.html` — landing page with search, tag filter, and global map |
| `article_template.html` | `docs/{slug}.html` — per-authority page |
| `search_template.html` | standalone search modal (included by index) |

**Technologies used in templates:**
- Leaflet 1.9.4 with `leaflet.markercluster` for interactive maps
- JSON metadata embedded in `index.html` for client-side search (no external search service)
- CSS Grid for responsive card layout
- Vanilla JavaScript only; no build step

`aagenerate.py` embeds a JSON metadata array in `index.html` at generation time. The
search and tag-filter UI reads this array at runtime — no server round-trip.

---

## Project structure

```
authorityatlas/
├── aafetch.py               # Wikidata seeder — run manually, never imported
├── aagenerate.py            # Site generator — run to rebuild docs/
├── data/
│   └── articles/            # Authority YAML files — source of truth
├── templates/               # Jinja2 templates
├── docs/                    # Generated static site — never edit by hand
├── tests/                   # Pytest suite
├── pyproject.toml           # Build config and all tool configuration
├── .pre-commit-config.yaml  # Pre-commit hooks (ruff, mypy, bandit, pip-audit)
├── README.md                # End-user documentation
└── CONTRIBUTING.md          # Developer guide
```

---

## Code map

| Path | Owns |
|---|---|
| `aafetch.py` | Wikidata seeder: SPARQL queries, P276→P625 coordinate fallback, Nominatim geocoding, YAML merge, curated-field protection |
| `aagenerate.py` | Site generator: schema validation, country code normalisation, markdown-to-HTML conversion, Jinja2 rendering, tag vocabulary enforcement |
| `data/articles/*.yaml` | Authority data — one file per authority, filename = URL slug |
| `templates/article_template.html` | Per-authority page (Leaflet map, info grid, factoid, remit, tags) |
| `templates/index_template.html` | Landing page (embedded JSON metadata, search, tag dropdown, global map, card grid) |
| `templates/search_template.html` | Standalone search modal |
| `docs/` | Generated HTML output — never edit by hand |
| `tests/test_aafetch.py` | Unit tests for `aafetch.py` (SPARQL parsing, YAML merge, Nominatim fallback) |
| `tests/test_aagenerate.py` | Unit tests for `aagenerate.py` (validation, country normalisation, tag enforcement, rendering) |
| `pyproject.toml` | Build metadata, runtime deps, dev deps, ruff/mypy/bandit/pytest/coverage config |
| `.pre-commit-config.yaml` | Pre-commit hooks: ruff (lint + format), mypy, bandit, pip-audit |

---

## Design decisions

**Why a static site?**
No server, no database, no runtime dependencies. The site can be served from GitHub
Pages, a CDN, or any file host. Maintenance burden is near zero, and there is no attack
surface beyond the hosting layer. The data is authoritative in the repository; the HTML
is a rendering artefact.

**Why YAML files, not a database?**
Each authority is a discrete, human-readable document. YAML can be reviewed in a pull
request, edited in any text editor, and diffed in git. A database would add infrastructure
for no benefit at this scale and make contributions harder.

**Why Wikidata and not a proprietary API?**
Wikidata is CC0-licensed, requires no API key, and is maintained by a global community.
Proprietary authority databases (such as GLEIF or national registers) are jurisdiction-specific,
require accounts or fees, and have inconsistent coverage. Wikidata has patchy coverage
too, but it is open and improvable.

**Why a closed tag vocabulary?**
Open-ended tags diverge quickly: "maritime" vs "marine", "aviation" vs "air transport",
"env" vs "environment". A closed list makes the filter UI predictable and forces
contributors to think about categorisation rather than inventing labels. The vocabulary
is small enough to fit in working memory and large enough to cover the domain.

**Why filename-as-slug?**
Simplicity and external link stability. The URL is derived once, at the time the YAML
file is created. There is no slug field to maintain and no routing table to update. The
cost is that filenames become load-bearing: a rename requires a redirect.

**Why protect curated fields from `aafetch.py`?**
Wikidata entries are sometimes incomplete, incorrect, or formatted differently from what
the site needs. A maintainer who has carefully written a `remit` or chosen specific
`tags` should not have their work silently overwritten by re-running `aafetch.py`. The
`--force-wikidata` flag exists for the rare case where Wikidata is demonstrably better
than the current curated value.
