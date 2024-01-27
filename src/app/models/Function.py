from yorm import BaseManager, BaseModel

import requests
import utils
import re
import json 
import time 
import uuid
import os
import shutil


from jinja2 import Environment, FileSystemLoader, Template

import time
from datetime import datetime

import antenna_runner


from models.Runtime import Runtime

class Function(BaseModel):
    manager_class = BaseManager
    directory_path = "/storage/data/functions/"  

    

    def get_requirements(self, overide_requirements=None):
        if not hasattr(self, "requirements"):
            self.requirements = {}
        if overide_requirements:
            for key, value in overide_requirements.items():
                self.requirements[key] = value
        return self.requirements

    def run(self,data,event_id):
        runtime = Runtime.objects.get(name=self.runtime)
        start_time = time.time()
        timestamp  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        # genenrate funciton command based on wrapper 
        # run function command

        # Copy funciton files to /storage/tmp/{event-id}/code
        if not os.path.exists(f"{os.getcwd()}/storage/tmp/"):
            os.mkdir(f"{os.getcwd()}/storage/tmp/")

        os.mkdir(f"{os.getcwd()}/storage/tmp/{event_id}")
        
        os.mkdir(f"{os.getcwd()}/storage/tmp/{event_id}/data")
       

        
        #utils.files.cp(f"{os.getcwd()}/storage/files/functions/{function['name']}", f"{os.getcwd()}/storage/tmp/{event_id}/function")
        # render function wrapper 
        try:
            shutil.copytree(f"{os.getcwd()}/storage/files/functions/{self.name}", f"{os.getcwd()}/storage/tmp/{event_id}/function")
        except Exception as e:
            print(e)
            return {
                "function": self.name,
                "status": "error",
                "result": str(e),
                "execution_time": 0,
                "timestamp": timestamp
            }

        # add a try cath to the creation of these dirs
        try:
            utils.files.write(f"{os.getcwd()}/storage/tmp/{event_id}/data/input.json", json.dumps(data))
            rendered_wrapper = self.render_wrapper()
            
            utils.files.write(f"{os.getcwd()}/storage/tmp/{event_id}/wrapper{runtime.extension}", rendered_wrapper)
        except Exception as e:
            
            return {
                "function": self.name,
                "status": "error",
                "result": str(e),
                "execution_time": 0,
                "timestamp": timestamp
            }

        try:
            # render the function command from wrapper 
            function_command = runtime.render_command(f"{os.getcwd()}/storage/tmp/{event_id}")
            # function_command = f"{runtime.command['run']} {os.getcwd()}/storage/tmp/{event_id}/wrapper{runtime.extension}"
            
            command_res = antenna_runner.run_command(function_command)
            print("COMMAND RES")            
            print(command_res)

            raw_result = utils.files.read(f"{os.getcwd()}/storage/tmp/{event_id}/data/output.json")
            


            # Try to jsonify the result

            execution_time = round(time.time() - start_time, 2)
        
            try:
                jsonified_result = json.loads(raw_result)
                result_type = 'json'
            except json.JSONDecodeError:
                jsonified_result = raw_result.strip()
                result_type = 'text'

            utils.files.rmdir(f"{os.getcwd()}/storage/tmp/{event_id}", True)

            return {
                "function": self.name,
                "result": jsonified_result,
                "status": "success",
                "result_type": result_type,
                "execution_time": execution_time,
                "timestamp": timestamp
            }

        except Exception as e:
            execution_time = round(time.time() - start_time, 2)
            print("WE HAVE AN ERROR")
            print(data)
            utils.files.rmdir(f"{os.getcwd()}/storage/tmp/{event_id}", True)
            return {
                "function":  self.name,
                "status": "error",
                "result": str(e),
                "execution_time": execution_time,
                "timestamp": timestamp
            }

    def render_wrapper(self):
        
        runtime = Runtime.objects.get(name=self.runtime)

        wrapper_template_str = runtime.wrapper_template()
        
        wrapper_template = Template(wrapper_template_str)
        rendered_wrapper = wrapper_template.render(function=self.dump())
        return rendered_wrapper


