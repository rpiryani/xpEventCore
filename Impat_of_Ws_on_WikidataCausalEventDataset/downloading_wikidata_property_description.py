import requests
import pandas as pd

# Define the SPARQL query to retrieve property descriptions
sparql_query = """
SELECT ?property ?propertyLabel ?propertyDescription
WHERE {
  ?property a wikibase:Property .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
}
"""

# Define the WikiData Query Service endpoint
wdqs_endpoint = "https://query.wikidata.org/sparql"

# Define HTTP headers
headers = {
    "User-Agent": "Your_User_Agent",
    "Accept": "application/sparql-results+json"
}

# Execute the SPARQL query
response = requests.get(wdqs_endpoint, params={"query": sparql_query}, headers=headers)
properties_list = []
# Check if the request was successful
if response.status_code == 200:
    data = response.json()
    # Process the results
    for item in data['results']['bindings']: 
        property_id = item['property']['value']
        property_label = item['propertyLabel']['value']
        property_description = item.get('propertyDescription', {'value': 'No description available'})['value']
        #print(f"Property ID: {property_id}, Label: {property_label}, Description: {property_description}")
        properties_list.append({"id":property_id,"label":property_label,"description":property_description})
    print("Data collected")
else:
    print("Failed to retrieve data from WikiData.")

property_df = pd.DataFrame(properties_list)
property_df.to_csv("Wikidata_properties_description.csv")