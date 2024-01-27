from datetime import datetime
import jq
import time
import yaml
import json
import re
import shlex
import ast
import io
import sys
import base64
from store import  settings
import kubernetes
from kubernetes import client, config, stream
stream = stream.stream
from jinja2 import Template
from git import Repo
from git import Git
import os
import shutil
import random
import string
from . import github
from . import files
from . import jsontools
#from . import k8s
from . import websockets
from . import rabbitmq
from . import versioning


def copy_dir(src_dir, dst_dir):
    # Ensure destination directory exists
    os.makedirs(dst_dir, exist_ok=True)

    for item in os.listdir(src_dir):
        s = os.path.join(src_dir, item)
        d = os.path.join(dst_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

def delete_directory(folder_path):
    try:
        shutil.rmtree(folder_path)
        print(f"Folder '{folder_path}' deleted successfully.")
    except OSError as e:
        print(f"Error deleting folder: {e}")

def clear_directory(folder_path):
    for root, dirs, files in os.walk(folder_path, topdown=False):
        for file in files:
            file_path = os.path.join(root, file)
            os.remove(file_path)
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            os.rmdir(dir_path)

def remove_keys(d, keys_to_remove):
    for key in keys_to_remove:
        if key in d:
            del d[key]
    return d

def to_dict(obj):
    if hasattr(obj, 'attribute_map'):
        result = {}
        for k,v in getattr(obj, 'attribute_map').items():
            val = getattr(obj, k)
            if val is not None:
                result[v] = to_dict(val)
        return result
    elif type(obj) == list:
        return [to_dict(x) for x in obj]
    elif type(obj) == datetime:
        return str(obj)
    else:
        return obj

def truncate_list_of_dicts_by_key(list_of_dicts, key):
    result = []
    for item in list_of_dicts:
        result.append(deep_dict_value(item,key))
    return result

def deep_dict_value(data, key):
    layers = key.split('.')
    for layer in layers:
        data = data[layer]
   
    return data


def get_first_word_in_string(string):
    regex = r"^\w+"
    match = re.search(regex, string)
    if match:
        return match.group()
    return None

def find_object_by_key(obj, key, value):
    if isinstance(obj, dict):
        for obj_key, obj_value in obj.items():
            if obj_key == key and obj_value == value:
                return obj
            else:
                result = find_object_by_key(obj_value, key, value)
                if result is not None:
                    return result
    elif isinstance(obj, list):
        for item in obj:
            result = find_object_by_key(item, key, value)
            if result is not None:
                return result

def sort_and_compare_arrays(arr1, arr2):
    sorted_arr1 = sorted(arr1)
    sorted_arr2 = sorted(arr2)

    if sorted_arr1 == sorted_arr2:
        return True
    else:
        return False
        

def is_regex(string):
    try:
        re.compile(string)
        return True
    except re.error:
        return False


import urllib.parse

def clone_repo(git_url, repo_dir, username, password):
    g = Git(repo_dir)
    g.clone(git_url.replace('https://', f'https://{username}:{password}@'))


def get_repo_name_from_url(url):
    parsed_url = urllib.parse.urlparse(url)
    path_parts = parsed_url.path.split("/")
    if path_parts[-1].endswith(".git"):
        repo_name = path_parts[-1][:-4]  # Remove ".git" extension
    else:
        repo_name = path_parts[-1]
    return repo_name


def generate_timestamp(format='%Y-%m-%d %H:%M:%S'):
    return datetime.now().strftime(format)

def process_dict_for_metrics(obj):
    labels = {}
    for key, value in obj.items():
        if isinstance(value, list):
            # Check if items in the list are dictionaries
            if value and isinstance(value[0], dict):
                value = [str(item) for item in value]
            else:
                value = [str(item) for item in value]
            labels[key] = ",".join(value)
        else:
            labels[key] = str(value)
    return labels

def random_string(x, lowercase_only=False):
    """Generate a random string of length x."""
    if lowercase_only:
        characters = string.ascii_lowercase  # Only lowercase ASCII letters
    else:
        characters = string.ascii_letters + string.digits  # ASCII letters (both lowercase and uppercase) and digits

    return ''.join(random.choice(characters) for _ in range(x))

def try_json_loads(value):
    """
    Try to convert a string to a Python dictionary using json.loads.
    
    Parameters:
        value (str): The string to try to convert.
        
    Returns:
        dict or str: The converted dictionary if conversion is successful, 
                     otherwise the original string.
    """
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return value

def base64_encode_dict(data):
    json_string = json.dumps(data)
    json_bytes = json_string.encode('utf-8')
    base64_encoded = base64.b64encode(json_bytes)
    base64_string = base64_encoded.decode('utf-8')
    return base64_string
    
def base64_decode_to_dict(base64_string):
    # Decode the base64 string to bytes
    decoded_bytes = base64.b64decode(base64_string)

    # Convert the bytes to a JSON string
    json_string = decoded_bytes.decode('utf-8')

    # Convert the JSON string back to a dictionary
    data = json.loads(json_string)

    return data