"""
TEST: 

python -m deterministic.write_metrics.duplicated_lines_density datasets/slopCodeBench/scb-problems/circuit_eval/implementations_noDesign/checkpoint_8
"""

import subprocess
import requests
from pathlib import Path
import os
import argparse
from dotenv import load_dotenv

load_dotenv() 

SONAR_HOST = "http://localhost:9000"
SONAR_TOKEN = os.environ.get("SONAR_TOKEN")
PROJECT_KEY = "metrics"

def sonar_analysis(implementation_path):
    abs_path = os.path.abspath(implementation_path)
    subprocess.run(
        [
            "docker", "run", "--rm",
            "--network=host",
            "-v", f"{abs_path}:/usr/src",
            "sonarsource/sonar-scanner-cli",
            f"-Dsonar.projectKey={PROJECT_KEY}",
            "-Dsonar.sources=.",
            f"-Dsonar.host.url={SONAR_HOST}",
            f"-Dsonar.token={SONAR_TOKEN}",
            "-Dsonar.python.version=3.12",
        ],
        check=True,
    )

def sonar_duplicated_density():
    response = requests.get(
        f"{SONAR_HOST}/api/measures/component",
        params={
            "component": PROJECT_KEY,
            "metricKeys": "duplicated_lines_density",
        },
        headers={
            "Authorization": f"Bearer {SONAR_TOKEN}",
        },
    )

    data = response.json()
    measures = data["component"]["measures"]

    if not measures:
        return 0.0

    return float(measures[0]["value"])

def get_duplicated_lines_density(implementation_path): 
    sonar_analysis(implementation_path) 
    density = sonar_duplicated_density() 
    return density 

# usage: duplicated_lines_density [implementation folder path]
# results are printed 
def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("implementation_path", help="Path to the impl folder")
    args = parser.parse_args()

    density = get_duplicated_lines_density(args.implementation_path) 

    # print the result 
    print(density)
   

if __name__ == "__main__": 
    main() 
