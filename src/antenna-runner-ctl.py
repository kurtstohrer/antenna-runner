#!/usr/bin/env python3

import subprocess
import sys
import json
import time
import argparse

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

def scan():
     # Call the external script and return its response
    script_path = "scripts/get_available_clis.sh"
    return run_command(script_path)

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

if __name__ == "__main__":
    main()
