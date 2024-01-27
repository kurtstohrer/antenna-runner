import jsonschema
from jsonschema import validate
import importlib
import os
import sys
import utils 
print("---- INIT YORMTOOLS ----")
# Add the directory to sys.path
directory_name = "models"
sys.path.insert(0, directory_name)

# List all .py files in the directory
module_names = [f[:-3] for f in os.listdir(directory_name) if f.endswith(".py") and f != "__init__.py"]

# Import all the modules and create a class map
class_map = {}
model_names = []
for module_name in module_names:
    model_names.append(module_name.replace(".py",""))
    module = importlib.import_module(module_name)
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isinstance(attr, type):
            class_map[attr.__name__] = attr

print("Class map:", class_map)


def get_map():
    
    result = []
    for name in  model_names:
     
        model_class = class_map.get(name)
        items =  model_class.objects.get()
        
        if len(items) > 0:
            r= {}
            r["route"] = items[0].get_route()
            r["url"] = os.getenv('APP_HTTP_ADDR') + "data/" + r["route"]
            r["path"] =items[0].directory_path
            r["model"] = name
          
            result.append(r)
    return result

def get_route_model_class(route_name):
    map_item = utils.find_object_by_key(get_map(),"route",route_name)
    return class_map.get(map_item["model"])

def get_map_old():
    print("-------- GET AMP --------")
    result = {}
    for name in  model_names:
        print(name)
        model_class = class_map.get(name)
        items =  model_class.objects.get()
        print(len(items))
        if len(items) > 0:
            r = items[0].get_route()
            print(r)
            result[r] = name
    return result
# get model names 

def handle_websocket(data):
    valid, msg = validate_websocket_dict(data)
    if valid ==True:
        action = data["action"]
        model_name = data["model"]
        model_class = class_map.get(model_name)
       
        if action == "update":
            result =  dict(model_class.objects.update(data["data"],name=data["name"]))

        elif action == "delete":
            result = "delete item"
            result = dict(model_class.objects.delete(name=data["name"]))

        elif action == "create":
            result = "create item"
            result = model_class.objects.create(data["data"])
            

        else: 
           model_instance = model_class.objects.get(name=data["name"])
           result =  model_instance.dump()

        return result
    else:
        return "Validation Error:  " + str(msg)


def validate_websocket_dict(data):
    # Define the JSON schema for the validation
    schema = {
        "type" : "object",
        "properties" : {
            "model" : {"type" : "string"},
            "name" : {"type" : "string"},
            "action" : {"type" : "string", "enum" : ["create", "update", "read", "delete"]},
            "data" : {"type" : "object"},
        },
        "required": ["model", "name", "action", "data"],
    }

    try:
        validate(data, schema)  # validate will raise an exception if validation fails
    except jsonschema.exceptions.ValidationError as ve:
        print(f"Validation Error: {ve}")
        error = ve
        return False, error

    return True, "Data is valid"
