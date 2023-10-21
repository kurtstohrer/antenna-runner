#!/usr/bin/env python3

import subprocess
import sys
import json
import time
from datetime import datetime
import argparse
import re

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

def version():
    # Replace with your version checking command or operations
    return run_command("echo 'Version 0.0.0'")

def main():
    parser = argparse.ArgumentParser(description="Antenna runner tool")
    subparsers = parser.add_subparsers(dest="subparser_name")

    run_parser = subparsers.add_parser('run', help="Run the specified command")
    run_parser.add_argument('command', help="Command to run", nargs=argparse.REMAINDER)

    scan_parser = subparsers.add_parser('scan', help="Perform a scan")

    parser.add_argument('--version', '-v', help="Show version", required=False, action='store_true')

    args = parser.parse_args()

    if args.subparser_name == "run":
        output = run_command(" ".join(args.command))
    elif args.subparser_name == "scan":
        output = scan()
    elif args.version:
        output = version()
    else:
        parser.print_help()
        sys.exit(1)

    print(json.dumps(output, indent=4))




def determine_version(message):
    # Use regex to capture a version number pattern
    # The pattern captures versions like: x.y.z, x.y, x.y.z.a, etc.
    match = re.search(r'[0-9]+(\.[0-9]+)+', message)
    if match:
        return match.group(0)
    return None

def scan():
    languages = {
        "node": "node -v",
        "npm": "npm -v",
        "go": "go version",
        "php": "php -v",
        "python": "python --version",
        "java": "java -version",
        "rust": "rustc --version",
        "bash": "bash --version",
        "sqlite3": "sqlite3 --version",
        "ruby": "ruby -v",
        "perl": "perl -v",
        "docker": "docker --version",
        "docker-compose": "docker-compose --version",
        "terraform": "terraform version",
        "typescript": "tsc --version",
        "awscli": "aws --version",
        "jq": "jq --version",
        "git": "git --version",
        "kubectl": "kubectl version --client",
        "ansible": "ansible --version",
        "vagrant": "vagrant --version",
        "mysql": "mysql --version",
        "psql": "psql --version",
        "mongo": "mongo --version",
        "dotnet": "dotnet --version",
        "helm": "helm version --client",
        "az": "az --version",
        "gcloud": "gcloud --version",
        "vault": "vault version",
    }

    result = {}

    for lang, cmd in languages.items():
        try:
            # Run the command and decode the output
            message = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, shell=True).decode().strip()
            version = determine_version(message)
            
            # If both the message and version are non-empty, include them in the result
            if message and version:
                result[lang] = {
                    "message": message,
                    "version": version
                }
        except subprocess.CalledProcessError:
            # If command failed, continue to the next one
            continue
    
    return result

if __name__ == "__main__":
    main()




