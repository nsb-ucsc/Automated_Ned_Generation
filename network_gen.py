#!/usr/bin/env python3

import argparse
import os
import sys
import subprocess

# Define the paths to your generator scripts
SCRIPT_PATHS = {
    "omnet": "omnet/omnet_ned_gen.py",
    "inet": "inet/inet_omnet_gen.py",
    "ns3": "ns3/ns3_gen.py",
}

# Define a constant for the output directory.
DEFAULT_OUTPUT_DIR = "output"

def run_generator(target, config_file, output_dir):
    """
    Executes a specific generator script as a separate process inside the output directory.
    """
    print(f"\n{'='*15} Running {target.upper()} Generator {'='*15}")

    # Use absolute paths to prevent issues when changing directories
    abs_script_path = os.path.abspath(SCRIPT_PATHS.get(target))
    abs_config_path = os.path.abspath(config_file)

    if not os.path.exists(abs_script_path):
        print(f"Error: Generator script for target '{target}' not found at '{abs_script_path}'")
        return
    if not os.path.exists(abs_config_path):
        print(f"Error: Config file not found at '{abs_config_path}'")
        return

    command = ["python3", abs_script_path, abs_config_path]
    working_dir = output_dir

    try:
        print(f"Executing command inside '{working_dir}' directory...")
        print(f"  > {' '.join(command)}")
        # `cwd=working_dir` tells the subprocess to run in the 'output' folder.
        subprocess.run(command, check=True, cwd=working_dir)
        print(f"Successfully generated files for '{target}' in '{working_dir}/'")

    except FileNotFoundError:
        print(f"Error: Could not find the Python interpreter 'python3'. Make sure it's in your PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Error: The '{target}' generator script failed with exit code {e.returncode}.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def main():
    """
    Main function to parse arguments and orchestrate the generation process.
    """
    parser = argparse.ArgumentParser(
        description="Master network generator script. Generates simulation files from a unified YAML config.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # UPDATED: Changed the config file from a positional argument to a required, flagged argument.
    parser.add_argument(
        "-c", "--config",
        required=True,
        metavar="<path>",
        help="Path to the unified YAML configuration file."
    )

    parser.add_argument(
        "-t", "--target",
        required=True,
        nargs='+',
        choices=['omnet', 'inet', 'ns3', 'all'],
        help="The target generator(s) to run. Can be one or more.\n"
             "  omnet - Basic OMNeT++ NED file\n"
             "  inet  - INET NED and INI files\n"
             "  ns3   - NS-3 C++ simulation file\n"
             "  all   - Run all available generators"
    )
    
    args = parser.parse_args()

    output_dir = DEFAULT_OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    # If 'all' is present anywhere in the list, run all generators.
    if 'all' in args.target:
        targets_to_run = SCRIPT_PATHS.keys()
    else:
        # Use a set to handle potential duplicate inputs gracefully (e.g., -t ns3 ns3)
        targets_to_run = sorted(list(set(args.target)))

    for target in targets_to_run:
        # UPDATED: Use args.config instead of args.config_file
        run_generator(target, args.config, output_dir)

if __name__ == "__main__":
    main()