# Authority Atlas

**Authority Atlas** is an open-source project that creates a comprehensive and accessible global database of regulatory authorities and similar organizations working for the common good.

## 🗺️ Philosophy: An Atlas, Not an Encyclopedia

Authority Atlas serves as a **navigation tool** for discovering authorities - not a comprehensive knowledge repository. Like a geographical atlas shows you where places are and how to get there, Authority Atlas helps you:
- **Discover** authorities by geography, subject, or type
- **Navigate** to authoritative sources (official websites, Wikipedia, legal documents)

We index authorities with clean, structured metadata while driving traffic to official sources rather than competing with them.

## 🌐 Visit Authority Atlas

Explore the live site at: https://authorityatlas.org

## 🤝 Contributing

We welcome contributions from the community!

### 🏛️ Submitting a New Authority

To add a new authority to the Atlas:

1. **Check if a Wikipedia page exists** - If not, please create one first (with proper sources). This ensures the authority is notable and well-documented.

2. **Seed from Wikidata (recommended)** - If the authority has a [Wikidata](https://www.wikidata.org) entry, use `aafetch.py` to pre-populate most fields automatically:

   ```bash
   # Preview what would be written (no files changed):
   python aafetch.py --qid Q170918 --dry-run

   # Write the seeded YAML:
   python aafetch.py --qid Q170918 --output data/articles/icao.yaml
   ```

   `aafetch.py` fetches name, year, website, Wikipedia links, coordinates, and more from Wikidata and writes a ready-to-edit YAML. Human-curated fields (`factoid`, `remit`, `legal_basis_*`, `tags`, etc.) are never overwritten — you fill those in manually.

   **Pay attention to the coordinate diagnostics printed during the run:**
   - `Coordinates [P625]` — coordinates come directly from the authority's Wikidata entry. Good.
   - `Coordinates [P276→P625]` + **WARNING** — coordinates come from a linked building/location item, not the authority itself. Verify they match the actual headquarters before committing.
   - `Nominatim (name+country)` + **WARNING** — no Wikidata coordinates found; Nominatim was given only the authority name and country, which may return a city centroid rather than the real address. Replace with precise coordinates if possible.

   If the authority is not in Wikidata, skip to step 3 and create the YAML by hand using Trinity House as your blueprint.

3. **Review and complete the YAML** under `data/articles/`. Use **Trinity House** (`data/articles/trinity_house.yaml`) as your reference template — it documents every field. Fill in at minimum:
   - `factoid` — 1-3 sentences on origin story or sense of wonder
   - `remit` — what the authority actually does
   - `legal_basis_name` / `legal_basis_link` — founding legislation
   - `tags` — for search and filtering
   - `headquarters_address` — full address, needed for accurate map placement

4. **Commit your changes** and submit a **Pull Request** with a clear, descriptive message.

## 🚀 Getting Started with Development

You can develop locally or use GitHub Codespaces.

### Prerequisites

- Python 3.x
- Git

### Local Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/erngui/authorityatlas.git
   cd authorityatlas
   ```

2. **(Optional) Create a virtual environment:**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Generate the site:**

   ```bash
   python aagenerate.py
   ```

5. **Preview locally:**

   ```bash
   cd docs
   python3 -m http.server 8000
   ```

   Visit http://localhost:8000 in your browser.

### Using GitHub Codespaces

1. Click the green "Code" button and select "Open with Codespaces"
2. Once the Codespace loads, run:
   ```bash
   python aagenerate.py
   cd docs
   python -m http.server 8000
   ```
3. Click "Open in Browser" when prompted, or use the PORTS tab

## 🐞 Reporting Issues

Please open an issue if you encounter bugs or have ideas for improvements.

## 📄 License

- **Code**: Licensed under the MIT License
- **Content** (`data/` directory): Licensed under the CC BY-SA 4.0

### ✍️ Summary of CC BY-SA 4.0

You are free to:

- **Share** — copy and redistribute the material in any medium or format  
- **Adapt** — remix, transform, and build upon the material for any purpose, even commercially  

Under these terms:

- **Attribution** — You must give appropriate credit.  
- **ShareAlike** — You must license your contributions under the same terms.

## 🙌 Acknowledgments

- [Wikidata](https://www.wikidata.org) for structured authority data (coordinates, founding dates, official names, multilingual Wikipedia links) used to seed YAML entries via `aafetch.py`
- [Wikipedia](https://www.wikipedia.org) for the comprehensive knowledge base we link to
- [OpenStreetMap](https://www.openstreetmap.org) / [Nominatim](https://nominatim.org) for geocoding fallback when Wikidata has no coordinates
- Grace's Guide and other specialized resources for domain-specific insights
- The open-source community

## 🔗 Official Sites

- 🌐 https://authorityatlas.org
- 🛠️ Developed by https://ernestoexplains.com
- 💻 GitHub: https://github.com/erngui/authorityatlas
