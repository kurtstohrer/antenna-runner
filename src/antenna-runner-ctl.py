#!/usr/bin/env python3

import subprocess
import sys
import json
import time

def run_command(command):
    start_time = time.time()

    try:
        result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT).decode('utf-8')
        execution_time = round(time.time() - start_time, 2)
        return {
            "result": result.strip(),
            "execution_time": execution_time
        }
    except subprocess.CalledProcessError as e:
        execution_time = round(time.time() - start_time, 2)
        return {
            "result": e.output.decode('utf-8').strip(),
            "execution_time": execution_time
        }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./antenna-runner <command>")
        sys.exit(1)

    command = " ".join(sys.argv[1:])
    output = run_command(command)
    print(json.dumps(output, indent=4))

