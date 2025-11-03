import os
import yaml
import json
import re
from jinja2 import Template
import pycountry

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

def normalize_country_to_code(country_value):
    """Convert country names to ISO 3166-1 alpha-2 codes using pycountry. Pass through if already a code."""
    if not country_value:
        return country_value
    
    # If already a 2-letter code, validate and return
    if len(country_value) == 2 and country_value.isupper():
        try:
            pycountry.countries.get(alpha_2=country_value)
            return country_value
        except (KeyError, AttributeError):
            pass
    
    # Special cases not in ISO 3166-1
    special_cases = {
        'European Union': 'EU',
        'England': 'GB',
        'Scotland': 'GB',
        'Wales': 'GB',
        'Northern Ireland': 'GB'
    }
    
    if country_value in special_cases:
        return special_cases[country_value]
    
    # Try to find by name
    try:
        country = pycountry.countries.search_fuzzy(country_value)[0]
        return country.alpha_2
    except (LookupError, AttributeError, IndexError):
        # If not found, return original value
        print(f"  ⚠️ Warning: Could not find ISO code for country: {country_value}")
        return country_value

def get_country_name(country_code):
    """Get country name from ISO code using pycountry."""
    if not country_code:
        return country_code
    
    # Special cases
    special_names = {
        'EU': 'European Union'
    }
    
    if country_code in special_names:
        return special_names[country_code]
    
    try:
        country = pycountry.countries.get(alpha_2=country_code)
        return country.name
    except (KeyError, AttributeError):
        return country_code

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
            
            # Normalize country fields to ISO codes
            if 'establishment_country' in authority:
                authority['establishment_country'] = normalize_country_to_code(authority['establishment_country'])
            if 'headquarters_country' in authority:
                authority['headquarters_country'] = normalize_country_to_code(authority['headquarters_country'])
            
            # Process markdown links to HTML
            authority = process_authority_fields(authority)
            
            # Add country names for display (in addition to codes)
            authority['establishment_country_name'] = get_country_name(authority.get('establishment_country', ''))
            authority['headquarters_country_name'] = get_country_name(authority.get('headquarters_country', ''))
            
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
                'establishment_country_name': get_country_name(authority.get('establishment_country', '')),
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
