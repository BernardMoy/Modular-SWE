import argparse 
import os 
import subprocess 
import shutil
import json 
from pathlib import Path

def get_dpy_metrics(implementation_path): 
    """
    {
        "function_cyclomatic_complexity_count": 0, 
        "high_fan_out_classes_count": 0, 
    }
    """

    TEMP_DIR = Path("temp_metrics")

    CC_THRESHOLD = 5 
    FAN_OUT_THRESHOLD = 3 

    counts = {
        "function_cyclomatic_complexity_count": 0, 
        "high_fan_out_classes_count": 0, 
    }

    # Run the metrics script against the implementation path 
    subprocess.run([
        "scripts/metrics.sh", 
        implementation_path, 
        TEMP_DIR 
    ])

    # Read the number of complex functions 
    for json_file in os.listdir(TEMP_DIR / "dpy_metrics"): 

        if (json_file.endswith("class_module_metrics.json")): 
            with open(TEMP_DIR / "dpy_metrics" / json_file, 'r') as f: 
                data = json.load(f) 
                counts["high_fan_out_classes_count"] = len([x for x in data if x["Fan-Out"] >= FAN_OUT_THRESHOLD])
        
        if (json_file.endswith("function_metrics.json")): 
            with open(TEMP_DIR / "dpy_metrics" / json_file, 'r') as f: 
                data = json.load(f) 
                counts["function_cyclomatic_complexity_count"] = len([x for x in data if x["CC"] >= CC_THRESHOLD])

    # Remove the temp dir 
    shutil.rmtree(TEMP_DIR) 

    return counts 



# usage: write.py [implementation folder path]
# results are printed 
def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("implementation_path", help="Path to the impl folder")
    args = parser.parse_args()

    metrics = get_dpy_metrics(args.implementation_path)
    print(metrics) 
   

if __name__ == "__main__": 
    main() 

