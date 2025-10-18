import os
import yaml
import json
from jinja2 import Template

# Configuration
INPUT_DIR = "data/articles"
OUTPUT_DIR = "docs"
TEMPLATES_DIR = "templates"

# Templates
INDEX_TEMPLATE_FILE = os.path.join(TEMPLATES_DIR, "index_template.html")
ARTICLE_TEMPLATE_FILE = os.path.join(TEMPLATES_DIR, "article_template.html")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load templates
with open(INDEX_TEMPLATE_FILE, "r", encoding="utf-8") as f:
    index_template = Template(f.read())

with open(ARTICLE_TEMPLATE_FILE, "r", encoding="utf-8") as f:
    article_template = Template(f.read())

def validate_authority(authority, filename):
    required_fields = [
        'name', 'acronym', 'remit', 'type',
        'legal_basis_name', 'legal_basis_link',
        'establishment_country', 'regional_remit',
        'year_established', 'legal_representative',
        'tags', 'factoid', 'description', 'fact_checking_websites'
    ]
    for field in required_fields:
        if field not in authority:
            raise ValueError(f"❌ Missing field '{field}' in file: {filename}")
        if authority[field] in [None, '']:
            raise ValueError(f"⚠️ Empty field '{field}' in file: {filename}")

    if not isinstance(authority['tags'], list):
        raise TypeError(f"❌ 'tags' should be a list in file: {filename}")
    if not isinstance(authority['fact_checking_websites'], list):
        raise TypeError(f"❌ 'fact_checking_websites' should be a list in file: {filename}")

# Collect data
articles = []
metadata_list = []

for filename in os.listdir(INPUT_DIR):
    if filename.endswith(".yaml") or filename.endswith(".yml"):
        with open(os.path.join(INPUT_DIR, filename), "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        # Expect the file to have an 'authorities' list
        if not isinstance(data.get('authorities'), list):
            raise ValueError(f"❌ Expected 'authorities' to be a list in {filename}, but got {type(data.get('authorities')).__name__}")

        for authority in data['authorities']:
            validate_authority(authority, filename)

            # Safe file name
            safe_name = authority['name'].replace(" ", "_").lower()
            article_filename = f"{safe_name}.html"

            # Render article page
            article_output = article_template.render(authority=authority)
            with open(os.path.join(OUTPUT_DIR, article_filename), "w", encoding="utf-8") as outf:
                outf.write(article_output)

            # Add entry to index
            articles.append({
                'name': authority['name'],
                'description': authority.get('description', ''),
                'filename': article_filename
            })

            # Metadata blob for client-side search
            metadata_list.append({
                'search_blob': json.dumps(authority, ensure_ascii=False),
                'filename': article_filename
            })

# Render index page
index_output = index_template.render(
    articles=articles,
    metadata=json.dumps(metadata_list, ensure_ascii=False)
)

with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
    f.write(index_output)

print("✅ Site generation complete.")
