from yorm import BaseManager, BaseModel

import requests
import utils
import re
import json 
import time 
import uuid
import os

from jinja2 import Environment, FileSystemLoader, Template
import antenna_runner
import subprocess

class Runtime(BaseModel):
    manager_class = BaseManager
    directory_path = "/storage/data/runtimes/"  
    version = str

    async def init(self):
        self.version = self.get_version()
    
    def determine_version(self,message):
        # Use regex to capture a version number pattern
        # The pattern captures versions like: x.y.z, x.y, x.y.z.a, etc.
        match = re.search(r'[0-9]+(\.[0-9]+)+', message)
        if match:
            return match.group(0)
        return None

    def get_version(self):
        result = False
        try:
            message = subprocess.check_output(self.command['version'], stderr=subprocess.DEVNULL, shell=True).decode().strip()
            version = self.determine_version(message)
            result =  version

        except subprocess.CalledProcessError:
            pass

        return result

    def is_supported(self):
        if self.get_version():
            return True
        return False


    def wrapper_template(self):
        return utils.files.read(f"{os.getcwd()}/storage/files/runtimes/{self.name}/wrapper/wrapper.j2")


    def render_command(self,event_path):
        template = Template(self.command['wrapper'])
        rendered = template.render(event_path=event_path)
        return rendered
    
    def render_wrapper(self,index,handler):
        wrapper_template_str = self.wrapper_template()
        wrapper_template = Template(wrapper_template_str)
        data = {
            "index":index,
            "handler":handler,
        }
        rendered_wrapper = wrapper_template.render(function=data)
        return rendered_wrapper