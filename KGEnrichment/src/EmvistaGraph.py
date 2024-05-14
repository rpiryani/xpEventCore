import requests
import json
import argparse
import os
from tqdm import tqdm  # Import the tqdm module

token = ""
#pss_url = "https://pss-api.prevyo.com/pss/api/v2/rdf"  # Use this for RDF
pss_url = "https://pss-api.prevyo.com/pss/api/v2/meaningrepresentation"  # Use this to get JSONs just like the ones you've been working with so far

def post(text):
    headers = {
        "Content-Type": "application/json",
        "Poa-Token": token
    }
    payload = {"text": text}
    response = requests.post(pss_url, headers=headers, json=payload)

    return response

def get_emvista_graph(input_file_name, output_file_name):
    with open(input_file_name, "r", encoding="utf-8") as in_file:
        text = in_file.read()
    
    response = post(text)

    if response.status_code == 200:
        result_json = response.json()
        with open(output_file_name, "w") as json_file:
            json.dump(result_json, json_file)
    else:
        print("ERROR!")
        print(response)

def main(args):
    data_dir = args.data_dir
    input_dir = os.path.join(data_dir, args.input_dir)
    save_dir = os.path.join(data_dir, args.save_dir)

    if not os.path.isdir(save_dir):
        os.mkdir(save_dir)
    
    input_dir_files = os.listdir(input_dir)
    save_dir_files = os.listdir(save_dir)
    
    for index, in_file in enumerate(tqdm(input_dir_files, desc="Processing Files")):
        out_file = in_file.split(".txt")[0] + ".json"
        output_fileName = os.path.join(save_dir, out_file)
        input_fileName = os.path.join(input_dir, in_file)

        if output_fileName not in save_dir_files:
            get_emvista_graph(input_fileName, output_fileName)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default="Emvista_Wikipedia_dataset")
    parser.add_argument("--input_dir", type=str, default="combined_text")
    parser.add_argument("--save_dir", type=str, default="combined_json")
    args = parser.parse_args()
    main(args)
