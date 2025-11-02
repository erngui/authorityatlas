import os
import yaml
import json
import re
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

def markdown_links_to_html(text):
    """Convert markdown links [text](url) to HTML <a> tags."""
    if not text:
        return text
    # Pattern: [link text](url)
    pattern = r'\[([^\]]+)\]\(([^\)]+)\)'
    replacement = r'<a href="\2" target="_blank">\1</a>'
    return re.sub(pattern, replacement, text)

def process_authority_fields(authority):
    """Process text fields that may contain markdown links."""
    # Only factoid and remit may contain markdown links now
    fields_with_markdown = ['factoid', 'remit']
    
    for field in fields_with_markdown:
        if field in authority and authority[field]:
            authority[field] = markdown_links_to_html(authority[field])
    
    return authority

def validate_authority(authority, filename):
    """Validate required fields in authority data."""
    required_fields = [
        'name', 'acronym', 'remit', 'type',
        'legal_basis_name', 'legal_basis_link',
        'establishment_country', 'regional_remit',
        'headquarters_city', 'headquarters_country', 'headquarters_address',
        'website', 'wikipedia',
        'year_established',
        'tags'
    ]
    
    # Optional but recommended fields
    optional_fields = ['factoid', 'head_title', 'predecessor_organizations', 'image', 'additional_resources']
    
    for field in required_fields:
        if field not in authority:
            raise ValueError(f"❌ Missing required field '{field}' in file: {filename}")
        if authority[field] in [None, '']:
            raise ValueError(f"⚠️ Empty required field '{field}' in file: {filename}")
    
    # Validate that tags is a list
    if not isinstance(authority['tags'], list):
        raise TypeError(f"❌ 'tags' should be a list in file: {filename}")
    
    # Validate that tags list is not empty
    if len(authority['tags']) == 0:
        raise ValueError(f"⚠️ 'tags' list is empty in file: {filename}")
    
    # Optional fields that should be lists if present
    optional_list_fields = ['additional_resources']
    for field in optional_list_fields:
        if field in authority and authority[field] is not None:
            if not isinstance(authority[field], list):
                raise TypeError(f"❌ '{field}' should be a list in file: {filename}")
    
    # Validate year_established is a number
    if not isinstance(authority['year_established'], int):
        raise TypeError(f"❌ 'year_established' should be an integer in file: {filename}")
    
    # Warn if optional recommended fields are missing
    missing_optional = [f for f in optional_fields if f not in authority or authority[f] in [None, '']]
    if missing_optional:
        print(f"  ℹ️ Optional fields not provided: {', '.join(missing_optional)}")
    
    print(f"✓ Validated: {authority['name']}")

# Collect data
articles = []
metadata_list = []

for filename in os.listdir(INPUT_DIR):
    if filename.endswith(".yaml") or filename.endswith(".yml"):
        filepath = os.path.join(INPUT_DIR, filename)
        print(f"\n📄 Processing: {filename}")
        
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        # Expect the file to have an 'authorities' list
        if not isinstance(data.get('authorities'), list):
            raise ValueError(
                f"❌ Expected 'authorities' to be a list in {filename}, "
                f"but got {type(data.get('authorities')).__name__}"
            )
        
        for authority in data['authorities']:
            validate_authority(authority, filename)
            
            # Process markdown links to HTML
            authority = process_authority_fields(authority)
            
            # Safe file name
            safe_name = authority['name'].replace(" ", "_").replace("/", "-").lower()
            # Remove any other problematic characters
            safe_name = "".join(c for c in safe_name if c.isalnum() or c in ('_', '-'))
            article_filename = f"{safe_name}.html"
            
            # Render article page
            article_output = article_template.render(authority=authority)
            output_path = os.path.join(OUTPUT_DIR, article_filename)
            
            with open(output_path, "w", encoding="utf-8") as outf:
                outf.write(article_output)
            
            print(f"  → Generated: {article_filename}")
            
            # Add entry to index - note: no description field anymore
            articles.append({
                'name': authority['name'],
                'acronym': authority.get('acronym', ''),
                'remit': authority.get('remit', ''),
                'factoid': authority.get('factoid', ''),  # Use factoid instead of description for preview
                'type': authority.get('type', ''),
                'establishment_country': authority.get('establishment_country', ''),
                'year_established': authority.get('year_established', ''),
                'website': authority.get('website', ''),
                'wikipedia': authority.get('wikipedia', ''),
                'filename': article_filename
            })
            
            # Metadata blob for client-side search
            # Create a searchable version with all text content
            search_content = {
                'name': authority['name'],
                'acronym': authority.get('acronym', ''),
                'remit': authority.get('remit', ''),
                'factoid': authority.get('factoid', ''),
                'type': authority.get('type', ''),
                'tags': authority.get('tags', []),
                'establishment_country': authority.get('establishment_country', ''),
                'regional_remit': authority.get('regional_remit', ''),
                'headquarters_city': authority.get('headquarters_city', ''),
                'headquarters_country': authority.get('headquarters_country', ''),
                'headquarters_address': authority.get('headquarters_address', ''),
                'year_established': authority.get('year_established', ''),
                'predecessor_organizations': authority.get('predecessor_organizations', ''),
            }
            
            metadata_list.append({
                'search_blob': json.dumps(search_content, ensure_ascii=False),
                'filename': article_filename,
                'name': authority['name'],
                'year_established': authority.get('year_established', 0)
            })

# Sort articles alphabetically by name for index
articles.sort(key=lambda x: x['name'])

# Render index page
index_output = index_template.render(
    articles=articles,
    metadata=json.dumps(metadata_list, ensure_ascii=False)
)

index_path = os.path.join(OUTPUT_DIR, "index.html")
with open(index_path, "w", encoding="utf-8") as f:
    f.write(index_output)

print(f"\n✅ Site generation complete!")
print(f"   Generated {len(articles)} authority page(s)")
print(f"   Output directory: {OUTPUT_DIR}")
