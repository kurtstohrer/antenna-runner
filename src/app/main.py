from fastapi import FastAPI, WebSocket
import os
import websockets
import json
import asyncio

import socket
import hashlib
import subprocess
import re

from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

import antenna_runner 
import httpx
import base64
import utils 
import store

import time
from datetime import datetime

import pika
import threading
import os
from jinja2 import Environment, FileSystemLoader

from yorm import yormtools

from models.Runtime import Runtime
from models.Function import Function

from routers import data
app.include_router(data.router)


# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Receive a message
            data = await websocket.receive_text()
            # Process the message (you can modify this part based on your logic)
            print(f"Message received: {data}")
            # Send a response back
            await websocket.send_text(f"Message processed: {data}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()




# HTTP GET endpoint for health checks
@app.get("/health")
def read_health():
    
    return {
        "name": antenna_runner.get_name(),
        "status": "healthy"
    }

# HTTP GET endpoint for health checks
@app.get("/info")
def info():
    return antenna_runner.get_info()

# HTTP GET endpoint for health checks
@app.get("/available-runtimes")
def info():
    return antenna_runner.available_runtimes()


async def register_runner():
    # send antenna_runner.get_info() to RUNNER_REGISTRATION_QUEUE_NAME
    utils.rabbitmq.client.send(os.getenv("RABBITMQ_REGISTRATION_QUEUE_NAME"),antenna_runner.get_info())
    


async def ping_antenna(websocket_uri: str):
    try:
        async with websockets.connect(websocket_uri) as websocket:
            data = {
                "event":"runner-ping",
                "data":{
                    "name":antenna_runner.get_name() 
                }
            }
            base64data = utils.base64_encode_dict(data)
            await websocket.send(base64data) 
            response = await websocket.recv()
            print(f"Ping Antenna Successful")
            return response
    except Exception as e:
        print(f"Ping Antenna failed. {e}")
        return False

async def test_connection(websocket_uri: str):
    try:
        async with websockets.connect(websocket_uri) as websocket:
            await websocket.send("Test Connection")
            response = await websocket.recv()
            print(f"Connection Test Successful: {response}")
            return True
    except Exception as e:
        print(f"Connection Test Failed: {e}")
        return False




@app.on_event("startup")
async def startup_event():
    websocket_uri = f"ws://{os.getenv('ANTENNA_ADDR')}/ws"  # Replace with your 
    #ws_connected = await test_connection(websocket_uri)
    print("Starting antenna runner...")
    if  os.path.exists("storage"):
        utils.files.rmdir("storage", True)
    print("Cloning storage repo...")
    utils.github.clone_repo(os.getenv("GITHUB_ANTENNA_STORAGE_REPO_NAME"), "storage")
   
    print("Running runner scan...")
    antenna_runner.scan()

    print("Attempting to register runner...")
    register = await register_runner()
    store.scheduler.add_job(ping_antenna, 'interval', seconds=60, args=[websocket_uri])
    store.scheduler.start()
    
    #asyncio.create_task(start_sync())
    

   
    print("Starting event consumer...")
    utils.rabbitmq.client.consume(os.getenv("RABBITMQ_EVENT_QUEUE_NAME"),rabbitmq_callback)

@app.on_event("shutdown")
def shutdown():
    print("Shutting Down antenna")
    utils.files.rmdir("storage", True)

def rabbitmq_callback(ch, method, properties, body):
    # Process the message here
    # ...
        
    data = body.decode()
    data = json.loads(data)

    headers = properties.headers if properties.headers else {}
    retry_count = headers.get('x-retry-count', 0)
    max_retries = 10

    supported_events = os.getenv("ANTENNA_RUNNER_SUPPORTED_EVENTS").split(",")
    result = False

    print(f"Event: {data['event_id']} recived.")
    # verify runtime can be run 

    # check if the command or function is supported by the runner if not nack the   message
    if data["event"] not in supported_events:
        print(f"Event {data['event']} not supported by runner. Nacking message.")
        
        
    else:
        if data["event"] == "exec-explore-function":
            print(f"Checking if explore-function is supported by runner...")
            runtime = Runtime.objects.get(name=data["data"]["runtime"])
            if runtime and runtime.is_supported() and antenna_runner.supports_requirements(data["data"]["requirements"]):
                print("Function supported by runner. Running function.")
                result = antenna_runner.run_explore_function(data["data"],data["event_id"])
            else:
                print("Function not supported by runner. Nacking message.")

        if data["event"] == "exec-function":
            print(f"Checking if function {data['function']['name']} is supported by runner...")
            runtime = Runtime.objects.get(name=data["function"]["runtime"])
            function = Function.objects.get(name=data["function"]["name"])
            if runtime and runtime.is_supported() and antenna_runner.supports_requirements(function.get_requirements(data["function"]["requirements"])):
                print("Function supported by runner. Running function.")
                result = function.run(data["data"],data["event_id"])
            else:
                print("Function not supported by runner. Nacking message.")

        if data["event"] == "exec-command" or data["event"] == "exec-explore-command":
            print(f"Checking if command is supported by runner...")
            # check to see if the command is supported by the runner
        
            clis = antenna_runner.get_clis_from_command(data["data"]["command"])
            requirements = {}
            
            if "requirements" in data["data"]:
                requirements = data["data"]["requirements"]
            #runtime = Runtime.objects.get(name=cli)
            #print(runtime)
            # check if all clis are supported
            if antenna_runner.supports_clis(clis) and antenna_runner.supports_requirements(requirements):
                print("Command supported by runner. Running command.")
                result = antenna_runner.run_command(data["data"]["command"])
        
                
            else:
                print("Command not supported by runner. Nacking message.")

    if result:
        result["event_id"] = data["event_id"]
        result["runner"] = os.getenv("ANTENNA_RUNNER_NAME")
        if data["event"] == "exec-command":
            result["clis"] = clis
        utils.rabbitmq.client.send(os.getenv("RABBITMQ_RESPONSE_QUEUE_NAME"), result)
        # Acknowledge the message
        ch.basic_ack(delivery_tag=method.delivery_tag)
    else:
        retry_count += 1
        if retry_count >= max_retries:
            print('Max retries exceeded, dropping message!')
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            
            message = antenna_runner.get_error_message(data)

            timestamp  = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            result = {
                "status": "error",
                "result": message,
                "execution_time": 0,
                "timestamp": timestamp
            }
            result["event_id"] = data["event_id"]
            result["runner"] = os.getenv("ANTENNA_RUNNER_NAME")
            print(result)
            utils.rabbitmq.client.send(os.getenv("RABBITMQ_RESPONSE_QUEUE_NAME"), result)
            # Exceeded max retries, drop or dead-letter the message
            
        else:

            # Update the retry count in headers and send a new message
            headers['x-retry-count'] = retry_count
            properties.headers = headers
            # Publish a new message with the updated headers
            ch.basic_publish(
                exchange='',
                routing_key=method.routing_key,
                body=body,
                properties=properties
            )
            # Acknowledge the original message
            ch.basic_ack(delivery_tag=method.delivery_tag)

# HTTP GET endpoint for health checks
@app.get("/test")
def info():
    requirements = {
        "name": None,
        "tags": [],
        "clis": {
            "python3": ">3.10.0"
        }
    }
    return antenna_runner.supports_requirements(requirements)



    

