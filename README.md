# Authority Atlas

**Authority Atlas** is an open-source project that aims to create a comprehensive and accessible global database of authorities and similar organizations working for the common good.

## 🌐 Visit Authority Atlas

Explore the live site at: https://authorityatlas.org

## 🤝 Contributing

We welcome contributions from the community!

### 🏛️ Submitting a New Authority

To add a new authority to the Atlas:

1. Create a YAML file under the `data/articles/` directory, following this format:

```
authorities:
  - name: "Best Safety Authority"
    acronym: "BSA"
    remit: "Brief description of the authority's remit."
    type: "Type of organization (e.g., government department, NGO, etc.)"
    legal_basis_name: "Name of the legal basis"
    legal_basis_link: "https://example.org/legal-basis"
    establishment_country: "Country of establishment"
    regional_remit: "Geographical scope of the authority"
    website: "https://www.newauthority.org"
    wikipedia: "https://en.wikipedia.org/wiki/New_Authority"
    year_established: 2000
    legal_representative: "Title of the main representative"
    factoid: "An interesting or fun fact about the authority."
    description: "A slightly longer summary that can appear in search results."
    tags: ["tag1", "tag2", "tag3"]
    fact_checking_websites: ["https://example.org/factcheck"]

```

2. Commit your changes and submit a **Pull Request** with a clear, descriptive message.

## 🚀 Getting Started with Development

You can develop locally or use GitHub Codespaces.

### Prerequisites

- Python 3.x
- Git

### Local Setup

1. **Clone the repository:**

    git clone https://github.com/erngui/authorityatlas.git
    cd authorityatlas

2. **(Optional) Create a virtual environment:**

    python3 -m venv venv
    source venv/bin/activate

3. **Install dependencies:**

    pip install -r requirements.txt

4. **Generate the site:**

    python aagenerate.py

5. **Preview locally (optional):**

    cd output
    python3 -m http.server 8000

    Visit http://localhost:8000 in your browser.

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

- Wikimedia Commons for freely usable media
- The open-source community

## 🔗 Official Sites

- 🌐 https://authorityatlas.org
- 🛠️ Developed by https://ernestoexplains.com
