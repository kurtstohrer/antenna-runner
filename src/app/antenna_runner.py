import socket
import hashlib
import subprocess
import re
import uuid
import json
import utils
import uuid
import os
import yaml

import time
from datetime import datetime


from models.Runtime import Runtime
from models.Function import Function
def init():
    scan()

def get_name():

    return os.getenv('ANTENNA_RUNNER_NAME')

def get_mac_address():
    mac_address = uuid.getnode()
    mac_address = ':'.join(("%012X" % mac_address)[i:i+2] for i in range(0, 12, 2))
    return mac_address

def get_info():
    hostname = socket.gethostname()

    return {
        "url":"http://127.0.0.1:8001",
        "name": get_name(),
        "hostname": hostname,
        "fqdn": socket.getfqdn(),
        "tags": os.getenv("ANTENNA_RUNNER_TAGS").split(","),
        "mac_address": get_mac_address(),
        "runtimes": available_runtimes(),
        "clis":{
            "installed": installed_clis(),
            "available": available_clis(),
            "allowed": os.getenv("ANTENNA_RUNNER_ALLOWED_CLIS").split(",")
        }
    }



def available_clis():
    aclis = os.getenv("ANTENNA_RUNNER_ALLOWED_CLIS").split(",")
    result = {}
    installed = installed_clis()
    for cli in aclis:
        if cli in installed:
            result[cli] = installed[cli]
    return result

def available_runtimes():
    available_runtimes = {}
    for runtime in Runtime.objects.get():
        if runtime.is_supported():
            available_runtimes[runtime.name] = runtime.get_version()

    return available_runtimes


def installed_clis():
    return json.loads(utils.files.read("storage/info/installed_clis.json"))

def scan():
    os.mkdir("storage/info")
    utils.files.write("storage/info/installed_clis.json",json.dumps(scan_clis()))

def supports_clis(clis):
    allowed = True
    availableClis= available_clis()
    for cli in clis:
        if not cli in availableClis:
            allowed = False
    return allowed

def get_unsupported_clis_from_command(command):
    clis = get_clis_from_command(command)
   
    availableClis = available_clis()
    unsupported_clis = []
    for cli in clis:

        if not cli in availableClis:
            unsupported_clis.append(cli)
    return unsupported_clis

def get_clis_from_command(command):
    # Split the command into blocks separated by '&&', '|', and ';'
    blocks = re.split(r'&&|\||;', command)

    clis = []

    for block in blocks:
        # Remove leading and trailing spaces from the block
        block = block.strip()

        # Split each block into parts
        parts = block.split(" ")

        # Check if the first part is a CLI
        cli = parts[0]
        clis.append(cli)

    return clis


def is_command_supported(command):
    # Split the command into parts
    parts = command.split(" ")

    # Check if the first part is a runtime
    if supports_runtime(parts[0]):
        return parts[0]
    return None

import packaging.version

def supports_requirements(requirements):
    info = get_info()
    allowed = True
    # check if name is not null or "*"
    if "name" in requirements and requirements["name"] != None and requirements["name"] != "*":
        # if requirements.name is set then check it against the runner
        # check if requirements.name is a list
        if isinstance(requirements["name"], list):
            # check if runner name is in the list
            if not info["name"] in requirements["name"]:
               allowed = False

        else:
            if requirements["name"] != info["name"]:
                allowed = False

    if "tags" in requirements:
        # check if all tags are present
        for tag in requirements["tags"]:
            if not tag in info["tags"]:
                allowed = False

    if "clis" in requirements:
        # check if the cli versions are allowed
        for cli, version in requirements["clis"].items():
            if not cli in info["clis"]["available"]:
                allowed = False
            else:
                if not utils.versioning.meets_version_requirement(info["clis"]["available"][cli], version):
                    allowed = False

    if "runtimes" in requirements:
        # check if the runtime versions are allowed
        for runtime, version in requirements["runtimes"].items():
            if not runtime in info["runtimes"]:
                allowed = False
            else:
                if not utils.versioning.meets_version_requirement(info["runtimes"][runtime], version):
                    allowed = False
    return allowed

def scan_clis():
    #load yaml file
    clis = yaml.load(open(f"{os.getcwd()}/storage/config/clis.yaml"), Loader=yaml.FullLoader)


    result = {}

    for cli, val in clis.items():
        try:
            # Run the command and decode the output
            message = subprocess.check_output(val["command"]["version"], stderr=subprocess.DEVNULL, shell=True).decode().strip()
            version = determine_version(message)

            # If both the message and version are non-empty, include them in the result
            if message and version:
                result[cli] =  version
        except subprocess.CalledProcessError:
            # If command failed, continue to the next one
            continue

    return result

def determine_version(message):
    # Use regex to capture a version number pattern
    # The pattern captures versions like: x.y.z, x.y, x.y.z.a, etc.
    match = re.search(r'[0-9]+(\.[0-9]+)+', message)
    if match:
        return match.group(0)
    return None


def run_command(command):
    start_time = time.time()
    timestamp  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        raw_result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT).decode('utf-8')
        execution_time = round(time.time() - start_time, 2)

        # Try to jsonify the result
        try:
            jsonified_result = json.loads(raw_result)
            result_type = 'json'
        except json.JSONDecodeError:
            jsonified_result = raw_result.strip()
            result_type = 'text'

        return {
            "command": command,
            "result": jsonified_result,
            "status": "success",
            "result_type": result_type,
            "execution_time": execution_time,
            "timestamp": timestamp
        }
    except subprocess.CalledProcessError as e:
        execution_time = round(time.time() - start_time, 2)
        return {
            "command": command,
            "status": "error",
            "result": e.output.decode('utf-8').strip(),
            "execution_time": execution_time,
            "timestamp": timestamp
        }



def get_error_message(data):
    supported_events = os.getenv("ANTENNA_RUNNER_SUPPORTED_EVENTS").split(",")
    message = ""
    if data["event"] in supported_events:
        if data["event"] == "exec-function":
            function = Function.objects.get(name=data["function"]["name"])
            requirements = function.get_requirements(data["function"]["requirements"])
            if requirements and not supports_requirements(requirements):
                message = f"Could not execute function {function.name}, no runner matches the functions requirements"
            else:
                message = f"Could not execute function {function.name}, no Runners support the {funciton.runtime} runtime"

        if data["event"] == "exec-command":
            unsupported_clis = get_unsupported_clis_from_command(data["data"]["command"])
            requirements = data["data"]["requirements"]
            if requirements and not supports_requirements(requirements):
                message = f"Could not execute '{data['data']['command']}', no runner matches the provided requirements"
            else:
                message = f"Could not execute '{data['data']['command']}', no Runners support the the requirments: { ''.join(unsupported_clis) }"

    else:

        message = f"Event {data['event']} is not supported"


    return message


def run_explore_function(data,event_id):

    start_time = time.time()
    timestamp  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


    # Copy funciton files to /storage/tmp/{event-id}/code
    if not os.path.exists(f"{os.getcwd()}/storage/tmp/"):
        os.mkdir(f"{os.getcwd()}/storage/tmp/")

    os.mkdir(f"{os.getcwd()}/storage/tmp/{event_id}")
    os.mkdir(f"{os.getcwd()}/storage/tmp/{event_id}/data")

    try:
        runtime = Runtime.objects.get(name=data["runtime"])

        # write data to data/input.json

        utils.files.write(f"{os.getcwd()}/storage/tmp/{event_id}/data/input.json", json.dumps(data["data"]))
        # write wrapper file

        wrapper = runtime.render_wrapper(f"main{runtime.extension}",data["handler"])
        utils.files.write(f"{os.getcwd()}/storage/tmp/{event_id}/wrapper{runtime.extension}", wrapper)


        # write data["code"] to tmp/{event_id}/code\
        os.mkdir(f"{os.getcwd()}/storage/tmp/{event_id}/function")
        utils.files.write(f"{os.getcwd()}/storage/tmp/{event_id}/function/main{runtime.extension}", data["code"])

    except Exception as e:
        return {
            "explore-function":event_id,
            "status": "error",
            "result": str(e),
            "execution_time": 0,
            "timestamp": timestamp
        }
        # write data["code"] to tmp/{event_id}/code

    try:
        function_command = runtime.render_command(f"{os.getcwd()}/storage/tmp/{event_id}")

        command_res = run_command(function_command)
        raw_result = utils.files.read(f"{os.getcwd()}/storage/tmp/{event_id}/data/output.json")
        execution_time = round(time.time() - start_time, 2)
        try:
            jsonified_result = json.loads(raw_result)
            result_type = 'json'
        except json.JSONDecodeError:
            jsonified_result = raw_result.strip()
            result_type = 'text'

        #utils.files.rmdir(f"{os.getcwd()}/storage/tmp/{event_id}")

        return {
            "explore-function":event_id,
            "status": "success",
            "result": jsonified_result,
            "result_type": result_type,
            "execution_time": execution_time,
            "timestamp": timestamp
        }
    except Exception as e:
        execution_time = round(time.time() - start_time, 2)
        #utils.files.rmdir(f"{os.getcwd()}/storage/tmp/{event_id}")
        return {
            "explore-function":event_id,
            "status": "error",
            "result": str(e),
            "execution_time": execution_time,
            "timestamp": timestamp
        }
