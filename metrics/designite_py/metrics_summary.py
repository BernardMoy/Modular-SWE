import os 
import json 
import argparse 

def get_metrics_summary_from_dpy(dpy_folder_path_old, dpy_folder_path_new = None):
    """
    Provide certain metrics that arent necessarily code smells
    so that the code quality can be analyzed more thoroughly. 
    For example: LOC. 

    Given an old and new dpy folder path, generate metric summary showing the differences before and after impl
    so the agent can more easily see where can have room for improvement. 
    
    Average class LOC: before, after 
    Average class NOM: before, after  - NOPM is already available before impl 

    Top increased LOC class: (x2) 
    Top increased NOM class: (x2) 

    Average function LOC: before, after 
    Average CC: before, after 
    Max CC: before, after 
    Max PC: before, after 
    Function count: before, after 

    Top increased LOC function: (x3) 
    Top increased CC functions: (x3) 
    """ 
    
    # Read the dpy files 
    for json_file in os.listdir(dpy_folder_path_old): 
        # class metrics 
        if (json_file.endswith("class_module_metrics.json")): 
            with open(os.path.join(dpy_folder_path_old, json_file), 'r') as f:
                class_json_old = json.loads(f.read())

        # function metrics 
        if (json_file.endswith("function_metrics.json")): 
            with open(os.path.join(dpy_folder_path_old, json_file), 'r') as f: 
                function_json_old = json.loads(f.read()) 

    for json_file in os.listdir(dpy_folder_path_new): 
        # class metrics 
        if (json_file.endswith("class_module_metrics.json")): 
            with open(os.path.join(dpy_folder_path_new, json_file), 'r') as f:
                class_json_new = json.loads(f.read())  

        # function metrics 
        if (json_file.endswith("function_metrics.json")): 
            with open(os.path.join(dpy_folder_path_new, json_file), 'r') as f: 
                function_json_new = json.loads(f.read()) 

    result = {
        "average_class_lines_of_code": {
            "before": 0,
            "after": 0,
        },
        "average_class_number_of_methods": {
            "before": 0,
            "after": 0,
        },
        "top_increased_lines_of_code_classes": [
            # {"class": "", "before": 0, "after": 0, "percentage_change": 0}
        ],
        "top_increased_number_of_methods_classes": [
            # {"class": "", "before": 0, "after": 0, "percentage_change": 0}
        ],

        "average_function_lines_of_code": {
            "before": 0,
            "after": 0,
        },
        "average_function_cyclomatic_complexity": {
            "before": 0,
            "after": 0,
        },
        "maximum_function_cyclomatic_complexity": {
            "before": 0,
            "after": 0,
        },
        "maximum_function_parameter_count": {
            "before": 0,
            "after": 0,
        },
        "function_count": {
            "before": 0,
            "after": 0,
        },

        "top_increased_lines_of_code_functions": [
            # {"function": "", "before": 0, "after": 0, "percentage_change": 0}
        ],
        "top_increased_cyclomatic_complexity_functions": [
            # {"function": "", "before": 0, "after": 0, "percentage_change": 0}
        ],
    }

    TOP_CLASS_THRESHOLD = 2 
    TOP_FUNCTION_THRESHOLD = 3 

    # Fill in the class level metrics summary 
    loc = [entry["LOC"] for entry in class_json_old]
    result["average_class_lines_of_code"]["before"] = sum(loc) / len(loc) 
    loc = [entry["LOC"] for entry in class_json_new]
    result["average_class_lines_of_code"]["after"] = sum(loc)/len(loc) 

    nom = [entry["NOM"] for entry in class_json_old]
    result["average_class_number_of_methods"]["before"] = sum(nom)/len(nom) 
    nom = [entry["NOM"] for entry in class_json_new]
    result["average_class_number_of_methods"]["after"] = sum(nom)/len(nom) 

    d = {} 
    for entry in class_json_old: 
        key = f"{entry["Module"]}{'.'+entry["Class"] if entry["Class"] else ""}"
        d[key] = {
            "class": key,
            "before": entry["LOC"]
        }

    for entry in class_json_new: 
        key = f"{entry["Module"]}.{entry["Class"]}"
        if key in d: 
            d[key]["function"] = f"{entry["Module"]}.{entry["Module"]}{'.'+entry["Class"] if entry["Class"] else ""}"
            d[key]["after"] = entry["LOC"]
            d[key]["percentage_change"] = 100*(d[key]["after"] - d[key]["before"]) / d[key]["before"] if d[key]["before"] > 0 else 0

    result["top_increased_lines_of_code_classes"] = sorted([x for x in d.values() if "percentage_change" in x], key=lambda x: x["percentage_change"], reverse=True)[:TOP_CLASS_THRESHOLD]

    d = {} 
    for entry in class_json_old: 
        key = f"{entry["Module"]}{'.'+entry["Class"] if entry["Class"] else ""}"
        d[key] = {
            "class": key,
            "before": entry["NOM"]
        }

    for entry in class_json_new: 
        key = f"{entry["Module"]}.{entry["Class"]}"
        if key in d: 
            d[key]["function"] = f"{entry["Module"]}.{entry["Module"]}{'.'+entry["Class"] if entry["Class"] else ""}"
            d[key]["after"] = entry["NOM"]
            d[key]["percentage_change"] = 100*(d[key]["after"] - d[key]["before"]) / d[key]["before"] if d[key]["before"] > 0 else 0

    result["top_increased_number_of_methods_classes"] = sorted([x for x in d.values() if "percentage_change" in x], key=lambda x: x["percentage_change"], reverse=True)[:TOP_CLASS_THRESHOLD]


    # Fill in the function level metrics summary 
    loc = [entry["LOC"] for entry in function_json_old]
    result["average_function_lines_of_code"]["before"] = sum(loc) / len(loc) 
    loc = [entry["LOC"] for entry in function_json_new]
    result["average_function_lines_of_code"]["after"] = sum(loc)/len(loc) 

    cc = [entry["CC"] for entry in function_json_old]
    result["average_function_cyclomatic_complexity"]["before"] = sum(cc)/len(cc) 
    result["maximum_function_cyclomatic_complexity"]["before"] = max(cc)
    cc = [entry["CC"] for entry in function_json_new]
    result["average_function_cyclomatic_complexity"]["after"] = sum(cc)/len(cc) 
    result["maximum_function_cyclomatic_complexity"]["after"] = max(cc)
    pc = [entry["PC"] for entry in function_json_old] 
    result["maximum_function_parameter_count"]["before"] = max(pc)
    pc = [entry["PC"] for entry in function_json_new] 
    result["maximum_function_parameter_count"]["after"] = max(pc)

    result["function_count"]["before"] = len(function_json_old)
    result["function_count"]["after"] = len(function_json_new)

    d = {} 
    for entry in function_json_old: 
        key = f"{entry["Module"]}.{entry["Class"] + '.' if entry["Class"] else ""}{entry["Method"]}"
        d[key] = {
            "function": key,
            "before": entry["LOC"]
        }

    for entry in function_json_new: 
        key = f"{entry["Module"]}.{entry["Class"] + '.' if entry["Class"] else ""}{entry["Method"]}"
        if key in d: 
            d[key]["after"] = entry["LOC"]
            d[key]["percentage_change"] = 100*(d[key]["after"] - d[key]["before"]) / d[key]["before"] if d[key]["before"] > 0 else 0
    result["top_increased_lines_of_code_functions"] = sorted([x for x in d.values() if "percentage_change" in x], key=lambda x: x["percentage_change"], reverse=True)[:TOP_FUNCTION_THRESHOLD]

    d = {} 
    for entry in function_json_old: 
        key = f"{entry["Module"]}.{entry["Class"] + '.' if entry["Class"] else ""}{entry["Method"]}"
        d[key] = {
            "function": key,
            "before": entry["CC"]
        }

    for entry in function_json_new: 
        key = f"{entry["Module"]}.{entry["Class"] + '.' if entry["Class"] else ""}{entry["Method"]}"
        if key in d: 
            d[key]["after"] = entry["CC"]
            d[key]["percentage_change"] = 100*(d[key]["after"] - d[key]["before"]) / d[key]["before"] if d[key]["before"] > 0 else 0

    result["top_increased_cyclomatic_complexity_functions"] = sorted([x for x in d.values() if "percentage_change" in x], key=lambda x: x["percentage_change"], reverse=True)[:TOP_FUNCTION_THRESHOLD]

    return result 



# usage: metrics-summary [old_dpy_path] [new_dpy_path]
# results are printed 
def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("old_dpy_path", help="Dpy folder path to the prev impl")
    parser.add_argument("new_dpy_path", help="Dpy folder path to the current impl")
    args = parser.parse_args()

    summary = get_metrics_summary_from_dpy(
        args.old_dpy_path, 
        args.new_dpy_path
    )

    print(json.dumps(summary, indent=2))
   

if __name__ == "__main__": 
    main() 

