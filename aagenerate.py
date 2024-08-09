import os
import yaml
import json
from jinja2 import Template

# Directory paths
data_dir = 'data/articles'
template_dir = 'templates'
output_dir = 'output'
metadata_file = os.path.join(output_dir, 'metadata.json')
index_file = os.path.join(output_dir, 'index.html')
search_file = os.path.join(output_dir, 'search.html')

# Load the templates
with open(os.path.join(template_dir, 'article_template.html'), 'r') as file:
    article_template = Template(file.read())

with open(os.path.join(template_dir, 'index_template.html'), 'r') as file:
    index_template = Template(file.read())

with open(os.path.join(template_dir, 'search_template.html'), 'r') as file:
    search_template = Template(file.read())

metadata_list = []

# Process each YAML file
for filename in os.listdir(data_dir):
    if filename.endswith('.yaml'):
        with open(os.path.join(data_dir, filename), 'r') as file:
            data = yaml.safe_load(file)

            # Check if the file contains a list of authorities or a single authority
            if 'authorities' in data:
                authorities = data['authorities']
            else:
                authorities = [data]

            for authority in authorities:
                output_html = article_template.render(authority)

                # Generate a unique filename based on the authority name
                safe_name = authority['name'].replace(" ", "_").lower()
                output_filename = os.path.join(output_dir, f"{safe_name}.html")
                with open(output_filename, 'w') as output_file:
                    output_file.write(output_html)

                # Collect metadata
                metadata_list.append({
                    'name': authority['name'],
                    'acronym': authority['acronym'],
                    'type': authority['type'],
                    'legal_basis': authority['legal_basis']['name'],
                    'legal_basis_link': authority['legal_basis']['link'],
                    'establishment_country': authority['establishment_country'],
                    'regional_remit': authority['regional_remit'],
                    'year_established': authority['year_established'],
                    'legal_representative': authority['legal_representative'],
                    'date': authority['date'],
                    'tags': authority['tags'],
                    'filename': f"{safe_name}.html"
                })

# Write metadata to JSON file
with open(metadata_file, 'w') as file:
    json.dump(metadata_list, file, indent=2)

# Create the index.html file
index_html = index_template.render(articles=metadata_list)
with open(index_file, 'w') as file:
    file.write(index_html)

# Create the search.html file
search_html = search_template.render()
with open(search_file, 'w') as file:
    file.write(search_html)

print("HTML files, index.html, search.html, and metadata generated successfully.")
