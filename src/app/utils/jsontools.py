import json


def load_file(filepath):
    try:
        with open(filepath, 'r') as file:
            json_data = json.load(file)
            return json_data
    except FileNotFoundError:
        print(f"File not found: {filepath}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")

        


def analyze_for_types(data):
    manifest = {}

    if isinstance(data, list):
        if len(data) > 0:
            manifest = [analyze_for_types(data[0])]  # Represent as a list containing a single object
    elif isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict) or isinstance(value, list):
                manifest[key] = analyze_for_types(value)
            else:
                manifest[key] = type(value).__name__
    
    return manifest

def try_convert_to_json(data):
    print("***** jsontools.try_convert_to_json ******")
    try:
        jsn = json.loads(data)
        print("load as json")
        return json.loads(data)  # This will convert the string to a dict if possible
    except json.JSONDecodeError:
        print("dont load as json")
        return data  # If it's not valid JSON, return the original string
        