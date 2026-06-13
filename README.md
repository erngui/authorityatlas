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

### 💡 Propose a New Authority

Know of a regulatory authority or public body that belongs in the Atlas?
[Open a GitHub Issue](https://github.com/erngui/authorityatlas/issues/new/choose)
using the **Propose a New Authority** template — no coding required.
The authority must have an English Wikipedia page (please create one first if it
does not exist).

### 🛠️ Contribute Directly

Developers and data contributors who want to add or improve entries themselves:
see [CONTRIBUTING.md](CONTRIBUTING.md) for the full workflow — including seeding
from Wikidata, completing YAML fields, tagging rules, and the git process.

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
