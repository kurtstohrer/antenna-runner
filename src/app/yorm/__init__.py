import os 
import yaml
import json
import re
from jinja2 import Environment, FileSystemLoader, Template
# ------------ Manager (Model objects handler) ------------ #
class BaseManager:

    def __init__(self,model_class):
        #self.directory_path = os.getcwd() + self.directory_path
        self.model_class =  model_class
        self.full_dir_path = os.getcwd() + self.model_class.directory_path
        
        pass
    
    def get(self, **query):
        #if there is a name just load that file and return other wise 
        if "name" in query:
            try: 
                data = load_yaml_file(self.full_dir_path + query["name"] +".yaml")
                return self.model_class(**data)
            except:
                return None
            
        else: # load the dir and query 
            found = list()
            data = load_yaml_dir( self.full_dir_path)
            for item in data:
                match = True
                for key, value in item.items():
                    if key in query and item[key] != query[key]:
                        match = False
                if match: 
                    found.append(self.model_class(**item))
            return found
        

    def create(self, new_data: dict):
        if "name" not in new_data:
            return {"error": "data must contain name key"}

        name = new_data["name"]
        if self.get(name=name):
           return {"error": "names must be unique"}

        write_yaml(self.full_dir_path + name +".yaml",new_data)
        return self.get(name=name)

    def bulk_insert(self, rows: list):
        pass

    def update(self, new_data: dict, **args):
        model = self.get(name=args["name"])
        data = model.dump()
        for k,v in new_data.items():
            data[k] = v
        if model.name != data["name"]:
            # name has changed  check if already exist
            if self.get(name=data["name"]):
                return {"error": "names must be unique"}
            self.delete(name=model.name)
            
        write_yaml(self.full_dir_path + data["name"] +".yaml",data)
        return self.get(name=data["name"])

    def delete(self,**args):
        try: 
            os.remove(self.full_dir_path + args["name"] +".yaml")
            return {"success":self.full_dir_path + args["name"] +".yaml" + " deleted."}
        except Exception as e:  # capture the exception instance
            return {"error": f"Error deleting file: {str(e)}"}

# ----------------------- Model ----------------------- #
class MetaModel(type):
    manager_class = BaseManager

    def _get_manager(cls):
        return cls.manager_class(model_class=cls)

    @property
    def objects(cls):
        return cls._get_manager()


class BaseModel(metaclass=MetaModel):
    directory_path = ""

    def __init__(self, **row_data):
        for field_name, value in row_data.items():
            setattr(self, field_name, value)

    def __repr__(self):
        attrs_format = ", ".join([f'{field}={value}' for field, value in self.__dict__.items()])
        return f"<{self.__class__.__name__}: ({attrs_format})>"

    def dump(self):
        ignore = ["directory_path","manager_class"]
        result = {}
        for key,value in self.__dict__.items():
            if key not in ignore:
                result[key] = value
        return result

    def get_route(self):
        return get_last_segment(self.directory_path)

    
def jinja_constructor(loader, node):
    """Return Jinja-like templates as plain strings."""
    return loader.construct_scalar(node)

yaml.SafeLoader.add_implicit_resolver("!jinja", re.compile(r"{{.*?}}"), None)
yaml.SafeLoader.add_constructor('!jinja', jinja_constructor)


def load_yaml(path):
    result = None
    if os.path.isfile(path):
        result = load_yaml_file(path)
    else:
        result = load_yaml_dir(path)
    return result

def load_yaml_dir(path):
    result = []
    for filename in os.listdir(path):
        f = os.path.join(path, filename)
        if os.path.isfile(f):
            result.append(load_yaml(f))
    return result
            
def load_yaml_file(path):
    with open(path, "r") as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            return {"error" : exc}
    return data

def write_yaml(path,data):
    try:
        open(path, "w").write("---\n" + yaml.dump(data,allow_unicode=True))
    except:
        print("Error writing files.")

def get_last_segment(url):
    m = re.search(r'\/([^\/]*)\/$', url)
    return m.group(1) if m else None