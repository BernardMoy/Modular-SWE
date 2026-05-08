import json
from pathlib import Path

# get the base directory from this file 
BASE_DIR = Path(__file__).resolve().parent

def get_json_string(role): 
    # Read JSON and convert that to string with indent = 2 
    with open (BASE_DIR.parent / "JSON-schemas" / f"{role}.json", 'r') as f: 
        _schema = json.load(f) 
        schema_string = json.dumps(_schema, indent=2)
    
    return schema_string