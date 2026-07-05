import json
import subprocess
from pathlib import Path
import argparse 
import shutil 

def get_duplicates(implementation_path):
    """
    Return duplicated lines and tokens percentage 
    {
        "lines": 0-1, 
        "tokens": 0-1
    }
    """

    duplicates = {
        "lines": 0,
        "tokens": 0
    }

    result = subprocess.run(
        # Run jscpd with the default min tokens 50 and min lines 5 
        # https://www.npmjs.com/package/jscpd
        [
            "jscpd", 
            implementation_path,
            "--reporters", "json",
            "--output", 
            "temp_duplicates",  # Output is in temp_duplicates / jscpd-report.json
            "--ignore", "**/__pycache__/**,**/.venv/**",
            "--silent",
        ],
        capture_output=True,
        text=True,
        shell=False,
    )

    # Read the temp duplicates folder 
    REPORT_PATH = Path("temp_duplicates") / "jscpd-report.json"
    with open(REPORT_PATH, 'r') as f: 
        report_json = json.load(f)
        
        # Only return the percentage duplicated for lines and tokens 
        duplicates["lines"] = report_json["statistics"]["total"]["percentage"]
        duplicates["tokens"] = report_json["statistics"]["total"]["percentageTokens"]
    
    # Now remove the temp duplicates folder 
    shutil.rmtree(Path("temp_duplicates"))
    
    return duplicates


# usage: duplicated_lines_density [implementation folder path]
# results are printed 
def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("implementation_path", help="Path to the impl folder")
    args = parser.parse_args()

    density = get_duplicated_lines(args.implementation_path) 

    # print the result 
    print(density)
   

if __name__ == "__main__": 
    main() 
