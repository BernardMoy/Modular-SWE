import os 
import json
from metrics.designite_py.smells.dpy_class import get_metrics_from_dpy_class
from metrics.designite_py.smells.dpy_design import get_metrics_from_dpy_design
from metrics.designite_py.smells.dpy_function import get_metrics_from_dpy_function
from metrics.designite_py.smells.dpy_implementation import get_metrics_from_dpy_implementation

def get_metrics_from_dpy(dpy_folder_path): 
    smells = []
    # Try to read each of the JSON file of the designite python metrics 
    # Identify which dpy metric file using the end string 
    # Skip if they do not exist 
    for json_file in os.listdir(dpy_folder_path): 
        # arch smells (skipped) 
        # class module metrics 
        if (json_file.endswith("class_module_metrics.json")): 
            with open(os.path.join(dpy_folder_path, json_file), 'r') as f: 
                smells.extend(get_metrics_from_dpy_class(json.load(f)))

        # design smells 
        if (json_file.endswith("design_smells.json")): 
            with open(os.path.join(dpy_folder_path, json_file), 'r') as f: 
                smells.extend(get_metrics_from_dpy_design(json.load(f)))

        # function metrics 
        if (json_file.endswith("function_metrics.json")): 
            with open(os.path.join(dpy_folder_path, json_file), 'r') as f: 
                smells.extend(get_metrics_from_dpy_function(json.load(f)))

        # implementation smells 
        if (json_file.endswith("implementation_smells.json")): 
            with open(os.path.join(dpy_folder_path, json_file), 'r') as f:
                smells.extend(get_metrics_from_dpy_implementation(json.load(f)))

    return smells