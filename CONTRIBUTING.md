# Contributing to Authority Atlas

## Non-negotiable coding constraints

- **Treat documentation and tests as code.** If documentation or tests and code do not
  agree, developers will not trust them. Always ensure they stay up-to-date.
  After completing a work item, check whether `README.md` needs changes before
  committing.

- **Minimise runtime dependencies.** Runtime dependencies increase maintenance,
  deployment, and security burden. Authority Atlas intentionally keeps a tiny
  footprint (`pyyaml`, `pycountry`, `jinja2`). Adding a runtime dependency requires
  explicit maintainer approval.

- **No broken windows.** Do not leave failing tests, type errors, or lint violations
  in the codebase. Fix them immediately or revert the change that introduced them.

> **Planned:** `ARCHITECTURE.md` documenting design decisions and `BACKLOG.md` for
> tracking work items. Until they exist, use GitHub Issues and PR descriptions.

## Code style

- **Prefer maps and data-driven dispatch** over chains of `if`/`elif`.
- **Loops must be uniform**: no special-casing individual elements inside a loop body.
  Set up any per-element variation in a data structure before the loop so the loop
  itself stays clean.
- **Eliminate duplication by restructuring**, not by extracting one-off helpers.
  Three similar lines of code is better than a premature abstraction.
- **Refactor aggressively for simplicity and clarity.** Do not stop when it just
  works. Aim for code that is idiomatic, succinct, and easy to understand.
- This is a balance: brevity and idiom are valued, but not at the cost of legibility.
  Code may assume a competent Python reader; it need not explain the language, but
  the intent should remain obvious at a glance.

## Code quality and security

Security is a non-functional requirement. We use static analysis tools to catch
issues early.

- **Ruff** — linting and formatting:
  ```bash
  ruff check .
  ruff format --check .
  ```
- **Mypy** — strict static type checking:
  ```bash
  mypy aafetch.py aagenerate.py
  ```
- **Pytest + coverage** — branch coverage enforced at 90%:
  ```bash
  python -m pytest --cov=. --cov-fail-under=90
  ```
- **Bandit** — static security analysis for Python:
  ```bash
  bandit -r aafetch.py aagenerate.py
  ```
  > **Planned:** Bandit is not yet in `requirements.txt` or pre-commit. Add it.
- **Pip-Audit** — checks dependencies for known CVEs:
  ```bash
  pip-audit
  ```
  > **Planned:** Pip-Audit is not yet in the workflow. Add it alongside Bandit.
- **Pre-commit hooks** — run all of the above automatically on every commit:
  ```bash
  pre-commit install   # once, after cloning
  ```
  > **Planned:** `.pre-commit-config.yaml` does not exist yet. It should run
  > Ruff, Mypy, Bandit, and `python -m pytest` (fast subset) on every commit.

All of the above must pass before opening a pull request. Do not use `--no-verify`
to bypass hooks.

## Tests

- Run the full suite before opening a PR: `python -m pytest --cov=. --cov-fail-under=90`
- All tests must pass. New features need at least one new test.
- The test suite enforces 90% branch coverage.

### How to think about test coverage

Write tests from the contract, not from the coverage report. For each function:

1. **Every `return` and `raise` is a distinct observable outcome** — ensure at least
   one test exercises each one.
2. **`if`/`else` branches that reach the same exit** are secondary: cover them only
   when the two paths produce observably different output or side effects.
3. **Do not chase the coverage number.** If the metric falls short, ask "which
   outcome is untested?" — not "which line is red?"

### Mypy approach

Strict mode is enabled. Fix source; suppress as a last resort. A `# type: ignore`
hides the symptom without fixing the cause. When suppression is truly warranted,
add a comment explaining *why*.

## Contributing data (YAML authoring)

Authority Atlas content lives in `data/articles/`. Each file represents one
authority and follows the schema validated by `aagenerate.py`.

### Before you start

The authority must have an **English Wikipedia page** — this is the notability bar.
If one does not exist, create it with proper sources before opening a PR.

### Seeding from Wikidata (recommended)

If the authority has a Wikidata entry, use `aafetch.py` to pre-populate most fields:

```bash
# Preview without writing anything:
python aafetch.py --qid Q48835 --dry-run

# Write the seeded YAML (filename derived from name/acronym automatically):
python aafetch.py --qid Q48835
```

`aafetch.py` fetches name, acronym, year, website, Wikipedia links, coordinates,
legal basis, and more. Human-curated fields (`remit`, `factoid`, `legal_basis_*`,
`tags`, etc.) are never overwritten — those are your contribution.

**Pay attention to the coordinate diagnostics printed during the run:**
- `Coordinates [P625]` — direct from the authority's Wikidata entry. Good.
- `Coordinates [P276→P625]` + **WARNING** — from a linked building/location item;
  verify they match the actual headquarters before committing.
- `Nominatim (name+country)` + **WARNING** — no Wikidata coordinates found; result
  may be a city centroid, not the real address. Replace if possible.
- `Suggested sector tags from Wikidata (P101/P452)` — hints only; use as input
  to the tagging step below, not as final tags.

If the authority is not in Wikidata, create the YAML by hand using
`data/articles/trinity_house.yaml` as your template — it documents every field.

### Completing the YAML

At minimum, fill in these fields before opening a PR:

| Field | Guidance |
|-------|----------|
| `remit` | What the authority actually does — under ~400 visible chars |
| `factoid` | 1–3 sentences: origin story, sense of wonder — under ~250 visible chars |
| `legal_basis_name` / `legal_basis_link` | Founding treaty, statute, or charter |
| `tags` | See tagging rules below |
| `headquarters_address` | Full address for accurate map placement |

Run `python aagenerate.py` and resolve all warnings before committing.

### Tagging

Assign **2–5 tags** drawn exclusively from the two lists below.
`aagenerate.py` will warn on any tag not in the controlled vocabulary.

**Domain tags** — what realm does this authority operate in?

```
marine, atmospheric, space, terrestrial, freshwater, biodiversity,
food-agriculture, health, labour, finance, trade, energy, nuclear,
transport, telecommunications, cultural-heritage, education,
intellectual-property, justice, civil-society, industrial-development,
digital, sport, media
```

**Function tags** — what does this authority do?

```
regulation, standard-setting, conservation, coordination, monitoring,
safety, development-aid, rights-protection, research, scientific-advisory,
arbitration-judicial
```

Rules:
- Use **only** tags from the lists above. Do not invent new tags; request
  additions via a GitHub Issue if nothing fits.
- Choose the **minimum** tags needed. 2–3 is ideal; 5 is the maximum.
- If genuinely no domain tag fits, use `other`.
- Distinction: `research` = produces original science.
  `scientific-advisory` = synthesises existing evidence, issues expert
  opinions. A body may carry both.
- Every authority should have at least one domain tag and at least one
  function tag.

## Git workflow

- Work on a **feature branch**, never commit directly to `main`.
- Branch names follow the Conventional Commits prefix: `feat/`, `fix/`, `docs/`,
  `refactor/`, `chore/`, etc.
- Keep commits atomic and use [Conventional Commits](https://www.conventionalcommits.org/)
  prefixes: `fix:`, `feat:`, `test:`, `docs:`, `refactor:`, `chore:`.
- Review `git diff` before every commit.
- Small, focused commits. One logical change per commit. Commit messages in the
  imperative mood ("add tag filter to index" not "added tag filter").
- Do not mix refactoring with feature additions in the same commit.
- Ensure you have updated everything that changed: `README.md`, tests, templates,
  and regenerated `docs/` via `python aagenerate.py`.

### Merging back to main

When the feature is complete, merge into `main` and push:

```bash
git checkout main
git merge --no-ff feat/your-branch
git push origin main
```

Delete the feature branch after merging:

```bash
git branch -d feat/your-branch
git push origin --delete feat/your-branch
```

Do not leave stale feature branches on the remote.

## Changes requiring explicit maintainer approval

- Add a runtime dependency.
- Add a new required field to the authority YAML schema (breaks all existing files).
- Use crypto or other security-sensitive code.
- Rewrite large sections of code.
- Change the URL slug strategy (breaks existing external links).
