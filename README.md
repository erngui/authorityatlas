# authorityatlas
Authority Atlas is an open-source project that aims to create a comprehensive and accessible global database of authorities and similar organizations working for the common good.

## 🌐 Visit Authority Atlas

You can explore the live site at: [authorityatlas.org](https://authorityatlas.org)

## 🤝 Contributing

We welcome contributions from the community! If you'd like to contribute, here's how you can get involved:

### Submitting a New Authority

To add a new authority to the Atlas:

1. Create a YAML file in the data/articles directory for the new authority. Use the following template:

   authorities:
  - name: "Best Safety Authority"
    acronym: "BSA"
    remit: "Brief description of the authority's remit."
    type: "Type of organization (e.g., government department, NGO, etc.)"
    legal_basis:
      name: "Name of the legal basis"
      link: "URL to the legal basis"
    establishment_country: "Country of establishment"
    regional_remit: "Geographical scope of the authority"
    website: "https://www.newauthority.org"
    wikipedia: "https://en.wikipedia.org/wiki/New_Authority"
    year_established: 2000
    legal_representative: "Title of the main representative"
    date: "2024-08-07"
    factoid: "An interesting or fun fact about the authority."
    tags: ["tag1", "tag2", "tag3"]

2. Submit a Pull Request:

Commit your changes and submit a pull request. Be sure to include a meaningful commit message that describes the addition.

## 🚀 Getting Started with Development

To get started developing for Authority Atlas, you can clone this repository and set up your development environment using GitHub Codespaces or locally on your machine.

### Prerequisites

- Python 3.x
- Git

### Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/your-username/authorityatlas.git
   cd authorityatlas

2. **Set Up a Virtual Environment (Optional but Recommended):**

   python3 -m venv venv
   source venv/bin/activate

3. **Install Dependencies:**

   pip install -r requirements.txt

4. **Run the Local Server:**

   python3 -m http.server 8000

   Open http://localhost:8000 in your web browser to view the site locally.


### Reporting Issues
If you encounter any issues with the site or have suggestions for improvements, please open an issue.

## 📄 License
The code in this repository is licensed under the MIT License. See the LICENSE file for details.

The YAML files and other content within the data directory are licensed under the Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0) license. See the LICENSE-CC-BY-SA file for details.

## 🙌 Acknowledgments
* Wikimedia Commons for providing freely usable media files.
* The open-source community for their contributions and support.

## 📫 Contact

For more information or to get in touch:

Email: public@erngui.com
Twitter: @erngui
Website: https://erngui.com
