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

2. **Create a YAML file** under the `data/articles/` directory, using **Trinity House as your blueprint**. The Trinity House YAML (`data/articles/trinity_house.yaml`) serves as the reference template for all authorities and includes comprehensive documentation of all fields.

3. **Some guidelines:**
   - Keep `factoid` to 1-3 sentences focused on sense of wonder or origin story.
   - Include full official address for mapping functionality
   - Only add `additional_resources` if they provide unique perspectives beyond the official website and Wikipedia
   
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

- Wikipedia for providing the comprehensive knowledge base we link to
- Grace's Guide and other specialized resources for domain-specific insights
- The open-source community

## 🔗 Official Sites

- 🌐 https://authorityatlas.org
- 🛠️ Developed by https://ernestoexplains.com
- 💻 GitHub: https://github.com/erngui/authorityatlas
