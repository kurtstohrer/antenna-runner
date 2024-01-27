import kubernetes
from kubernetes import client, config, stream
from jinja2 import Template
import os
import yaml
import json
import re
import ast
from kubernetes.stream import stream
if os.getenv('K8S_ENVIRONMENT') == 'local':
    kubernetes.config.load_kube_config()
else:
    kubernetes.config.load_incluster_config()
import time
import subprocess

async def run_job(job_name, template, namespace='antenna'):
    print("- Running K8s job")

    # Depending on where you're running this (inside or outside a k8s cluster),
    # you'll want one of these:
    # config.load_kube_config()      # If outside cluster
    # config.load_incluster_config() # If inside cluster

    # Create a Kubernetes API client
    api_client = client.BatchV1Api()
    core_api = client.CoreV1Api() 

    # Create the job
    api_client.create_namespaced_job(namespace, template)
    
    # Wait for the job to complete, with a timeout of, say, 10 minutes (600 seconds)
    timeout = time.time() + 600

    while True:
        job_status = api_client.read_namespaced_job_status(job_name, namespace)
        conditions = job_status.status.conditions
        if conditions:
            last_condition = conditions[-1]
            if last_condition.status == 'True':
                break
            elif last_condition.status == 'False':
                raise Exception(f"Job {job_name} failed: {last_condition.message}")

        if time.time() > timeout:
            raise Exception(f"Job {job_name} timed out.")
        
        time.sleep(1)
    
    
    pod_name = find_job_pod_name(job_name)
    
    logs = core_api.read_namespaced_pod_log(pod_name, namespace)
 
    api_client.delete_namespaced_job(job_name, namespace)

    # If logs are usually in JSON format:

    logs = logs.replace("'", '"')

    result = logs


    # Return the logs as a dictionary
    return result


def find_job_pod_name(job_name, namespace='antenna'):
    # Create a Kubernetes API client
    api_client = client.CoreV1Api()
    
    # Get a list of pods in the namespace
    pods = api_client.list_namespaced_pod(namespace)
    
    # Iterate through the pods and find the one that has the job name as a prefix
    for pod in pods.items:
        if re.match(f"^{job_name}-", pod.metadata.name):
            return pod.metadata.name
    raise Exception(f"No pod found for job {job_name} in namespace {namespace}")



async def exec_command_on_pod(pod_name, command, directorys=[], namespace='antenna'):
    for directory in directorys:
        if "local_path" in directory and directory["local_path"] and directory["pod_path"]:
            copy_to_pod(pod_name,directory["local_path"], directory["pod_path"], namespace)
        elif "value" in directory and directory["value"] and directory["pod_path"]:
            write_to_pod(pod_name,json.dumps(directory["value"]), directory["pod_path"] , namespace)

    # Create a Kubernetes API client
    api_client = client.CoreV1Api()
   
    # Execute the command on the pod
    exec_command = ['/bin/sh', '-c', command]

     # Initialize an output buffer
    output_buffer = ""

    exec_response = stream(api_client.connect_get_namespaced_pod_exec,
                           pod_name,
                           namespace,
                           command=exec_command,
                           stderr=True, stdin=False,
                           stdout=True, tty=False,
                           _preload_content=False)

    # Read the streaming output
    while exec_response.is_open():
        exec_response.update(timeout=1)
        if exec_response.peek_stdout():
            # Append each line of stdout to the buffer
            output_buffer += exec_response.read_stdout()
        if exec_response.peek_stderr():
            print("STDERR: %s" % exec_response.read_stderr())
    exec_response.close()
    
    result= output_buffer
    # delete all temp files
    for directory in directorys:
        if "local_path" in directory and directory["local_path"] and directory["pod_path"]:
            pod_path = directory["pod_path"]
            local_path = directory["local_path"]
            delete_command = ['/bin/sh', '-c', f'rm -rf {pod_path}']
            stream(api_client.connect_get_namespaced_pod_exec, pod_name, namespace,command=delete_command, stderr=True, stdin=False, stdout=True, tty=False,  _preload_content=False)
        elif "value" in directory and directory["value"] and directory["pod_path"]:
            pod_path = directory["pod_path"]
            delete_command = ['/bin/sh', '-c', f'rm -rf {pod_path}']
            stream(api_client.connect_get_namespaced_pod_exec, pod_name, namespace,command=delete_command, stderr=True, stdin=False, stdout=True, tty=False,  _preload_content=False)

    
 
    
    
    # Return the logs as a dictionary
    return result
    




def is_deployment_running(deployment_name, namespace = "antenna"):

    # Create a Kubernetes API client
    api_client = client.AppsV1Api()

    # Retrieve the deployment object
    deployment = api_client.read_namespaced_deployment(deployment_name, namespace)

    # Check if the deployment is available and has at least one available replica
    if deployment.status.available_replicas is not None and deployment.status.available_replicas > 0:
        return True
    else:
        return False



def find_deployment_pod_name(deployment_name, namespace='antenna'):
    # Create a Kubernetes API client
    api_client = client.CoreV1Api()
    
    # Get a list of pods in the namespace
    pods = api_client.list_namespaced_pod(namespace)
    
    # Iterate through the pods and find the one that has the deployment name as a prefix
    for pod in pods.items:
        if re.match(f"^{deployment_name}-", pod.metadata.name):
            return pod.metadata.name
    raise Exception(f"No pod found for deployment {deployment_name} in namespace {namespace}")


# copy a directory to a pod
def copy_to_pod(pod_name,local_path, pod_path, namespace='antenna'):
    try:
        directory_path = "/".join(pod_path.split("/")[:-1])

        # Command to create the directory if it does not exist
        create_dir_cmd = ["kubectl", "exec", "-n", namespace, pod_name, "--", "mkdir", "-p", directory_path]
        subprocess.run(create_dir_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        cmd = ["kubectl", "cp", local_path, f"{namespace}/{pod_name}:{pod_path}"]
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError as e:
        print(f"Error copying {local_path} to {pod_name}:{pod_path}. Error: {str(e)}")
        raise

def write_to_pod(pod_name, file_content, pod_path, namespace='antenna'):
    print("WRTIE TO POD")
    print(pod_path)
    """
    Writes content to a file on a pod.

    :param pod_name: Name of the pod.
    :param file_content: Content to be written to the file.
    :param pod_path: Path of the file on the pod.
    :param namespace: Namespace of the pod.
    """
    try:
        # Splitting the path to get the directory
        directory_path = "/".join(pod_path.split("/")[:-1])

        # Command to create the directory if it does not exist
        create_dir_cmd = ["kubectl", "exec", "-n", namespace, pod_name, "--", "mkdir", "-p", directory_path]
        subprocess.run(create_dir_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Command to write the file
        write_cmd = ["kubectl", "exec", "-n", namespace, pod_name, "--", "sh", "-c", f"echo '{file_content}' > {pod_path}"]
        subprocess.run(write_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except subprocess.CalledProcessError as e:
        error_message = (
            f"Error writing to {pod_name}:{pod_path}. \n"
            f"Command: {' '.join(e.cmd)}\n"
            f"Return Code: {e.returncode}\n"
            f"Standard Output: {e.stdout}\n"
            f"Standard Error: {e.stderr}"
        )
        print(error_message)
        raise Exception(error_message) from e

def wait_for_pod_ready(pod_name, timeout=600, sleeptime=5, namespace='antenna',):
    print("--- wait_for_pod_ready ---")
    # Create a Kubernetes API client
    api_client = client.CoreV1Api()

    start_time = time.time()

    while True:
        print("wait for pod ready")
        pod = api_client.read_namespaced_pod(pod_name, namespace)
        if pod.status.phase == 'Running':
            all_containers_ready = all([container.ready for container in pod.status.container_statuses])
            if all_containers_ready:
                print("pids")
                return True

        if time.time() - start_time > timeout:
            raise Exception(f"Pod {pod_name} not ready after {timeout} seconds.")

        time.sleep(sleeptime)  # Wait for 5 seconds before checking again

    return False


def wait_for_deployment_ready(deployment_name, timeout=600, sleeptime=5, namespace='antenna'):
    print("--- wait_for_deployment_ready ---")
    
    # Load kube-config file; include path if it's not in default location
    config.load_kube_config()
    
    # Create a Kubernetes API client
    api_client = client.AppsV1Api()
    
    start_time = time.time()
    
    while True:
        print(f"Waiting for deployment {deployment_name} to be ready...")
        
        # Get the deployment object
        deployment = api_client.read_namespaced_deployment(deployment_name, namespace)
        
        # Check if the deployment is ready
        if (deployment.status.replicas == deployment.status.ready_replicas) and (deployment.status.available_replicas == deployment.status.replicas):
            print(f"Deployment {deployment_name} is ready!")
            return True
        
        # Check for timeout
        if time.time() - start_time > timeout:
            raise Exception(f"Deployment {deployment_name} not ready after {timeout} seconds.")
        
        # Sleep for the specified interval before checking again
        time.sleep(sleeptime)

    return False
