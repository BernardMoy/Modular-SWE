import argparse 
import json
import subprocess
import shutil
from metrics.designite_py.metrics import get_metrics_from_dpy
from metrics.pylint.metrics import check_duplicated_lines_of_code
from reusables.sort_smells import sort_smells
from metrics.designite_py.summary.get_summary import get_dpy_summary
from metrics.jscpd.summary.get_summary import get_jscpd_summary
from pathlib import Path
from metrics.deps_graph.metrics import get_metrics_from_deps_graph
import time 

SCRIPT_DIR = Path(__file__).resolve().parent.parent 



def _get_smells_from_dpy_and_pylint(dpy_path, pylint_path): 
    smells = []

    # Read the pylint json path 
    with open(pylint_path, 'r') as f: 
        pylint_json = json.load(f) 

    # Add dpy smells 
    smells.extend(get_metrics_from_dpy(dpy_path))

    # Obtain the duplicated loc smell from pylint 
    smells.extend(check_duplicated_lines_of_code(pylint_json))

    # Sort smells 
    smells = sort_smells(smells) 

    # Return the smells 
    return smells 

def _get_smells_from_deps_graph(implementation_path): 
    TEMP_FILE = Path(f"temp_graph_{str(time.time()).replace(".", "_")}")
    
    subprocess.run([
        "python", 
        "scripts/deps_graph.py", 
        implementation_path,
        TEMP_FILE
    ])

    smells = [] 
    with open(TEMP_FILE / "deps_graph.json", 'r') as f: 
        graph = json.load(f) 
        smells = get_metrics_from_deps_graph(graph)

    shutil.rmtree(TEMP_FILE)

    return smells 


def write_metrics_from_implementation(implementation_path, current_metrics_path, prev_implementation_path = None): 
    TEMP_METRICS_NEW_DIR = Path(f"metrics_new_{str(time.time()).replace(".", "_")}")
    TEMP_METRICS_OLD_DIR = Path(f"metrics_old_{str(time.time()).replace(".", "_")}")
    
    # generate the metrics folder 
    subprocess.run(
        [
            SCRIPT_DIR / "scripts" / "metrics.sh", 
            implementation_path, 
            TEMP_METRICS_NEW_DIR
        ], 
        check=True
    )

    if prev_implementation_path: 
        subprocess.run(
                [
                    SCRIPT_DIR / "scripts" / "metrics.sh", 
                    prev_implementation_path, 
                    TEMP_METRICS_OLD_DIR
                ], 
                check=True
            )

    # use the dpy and pylint path inside metrics to get smells 
    smells = _get_smells_from_dpy_and_pylint(
        TEMP_METRICS_NEW_DIR / "dpy_metrics", 
        TEMP_METRICS_NEW_DIR / "pylint_metrics.json"
    ) + _get_smells_from_deps_graph(
        implementation_path
    )

    # obtain the summary from dpy and jscpd 
    dpy_summary = get_dpy_summary(dpy_folder_new=TEMP_METRICS_NEW_DIR / "dpy_metrics", dpy_folder_old=(TEMP_METRICS_OLD_DIR / "dpy_metrics" if prev_implementation_path else None)) 
    jscpd_summary = get_jscpd_summary(implementation_new=implementation_path, implementation_old=prev_implementation_path)
    summary = {**dpy_summary, **jscpd_summary}  # jscpd summary already includes the duplicates data 

    # Remove the temp metrics new and old dir 
    shutil.rmtree(TEMP_METRICS_NEW_DIR)
    if TEMP_METRICS_OLD_DIR.exists(): 
        shutil.rmtree(TEMP_METRICS_OLD_DIR)
    
    # write to current metrics.json combining summary and smells 
    result = {
        "summary": summary, 
        "smells": smells
    }

    with open(current_metrics_path, "w") as f: 
        f.write(
            json.dumps(result, indent=2)
        )


# usage: write.py [impl_path] [current_metrics_output_path] [prev_impl_path (optional)]
def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("implementation_path", help="Abs path to the implementation directory")
    parser.add_argument("current_metrics_path", help="Abs path to write the metrics to")
    parser.add_argument("prev_implementation_path", nargs="?", default=None, help="Abs path to the previous implementation for writing summary")
    args = parser.parse_args()

    write_metrics_from_implementation(
        args.implementation_path, 
        args.current_metrics_path, 
        args.prev_implementation_path
    )

if __name__ == "__main__": 
    main() 
