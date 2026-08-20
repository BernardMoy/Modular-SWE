import argparse 
import os 
from constants import IMPL_DIR_DICT, BASE_REFERENCE_DIR, ENTRYFILE_NAME
import subprocess 
import shutil 
from pathlib import Path 

def main(): 
    parser = argparse.ArgumentParser() 
    parser.add_argument("implementation_path", help="Impl folder path")
    parser.add_argument("output", help="Output directory")
    args = parser.parse_args()

    # if the impl path start with the base reference dir (so we know we are doing graph on a reference problem) 
    # and it matches the implementation directory dict, then change the directory 
    implementation_path = Path(args.implementation_path)
    deps_graph_path = args.implementation_path
    if deps_graph_path.startswith(BASE_REFERENCE_DIR): 
        # Remove the base dir, process through the dict, then join back 
        deps_graph_path = deps_graph_path.removeprefix(BASE_REFERENCE_DIR).removesuffix("/")
        if deps_graph_path in IMPL_DIR_DICT: 
            deps_graph_path = IMPL_DIR_DICT[deps_graph_path]["path"]

        deps_graph_path = os.path.join(BASE_REFERENCE_DIR, deps_graph_path)
    deps_graph_path = Path(deps_graph_path)

    # entry file path must have deps graph path (the path that calls pydeps) as the root
    # to prevent import errors 
    entryfile_path = deps_graph_path / ENTRYFILE_NAME

    # Create the output directory 
    output_path = Path(args.output) 
    if output_path.exists(): 
        shutil.rmtree(output_path) 
    output_path.mkdir(parents=True) 

    # 1. Generate missing __init__.py files so that pydeps can recognise them 
    print("[GRAPH 1/6] Generating missing init.py") 
    subprocess.run([
        "python", 
        "scripts/gen_missing_init_files.py", 
        deps_graph_path
    ])

    # 2. Generate a temporary entrypoint file that imports all python modules
    print("[GRAPH 2/6] Generating temp entrypoint file") 
    subprocess.run([
        "python", 
        "scripts/gen_deps_graph_entry.py", 
        implementation_path, 
        deps_graph_path
    ])

    # Obtain REAL_MODULES from the entry file (import A; import B) --> REAL_MODULES = (A,B)...
    with entryfile_path.open() as f: 
        REAL_MODULES = [
            line.removeprefix("import ").strip()
            for line in f
            if line.startswith("import ")
        ]

    common_args = [
        "pydeps",
        entryfile_path,
        "--noshow",
        "--max-bacon=0",
        "--reverse",
        "--only",
        *REAL_MODULES,
    ]

    # 3. Generate the dependency graph (dot, svg) using pydeps
    # Reversed, meaning A -> B indicates A import B
    # include missing, meaning module imports are still visualised in the graph even when they cannot be resolved
    print("[GRAPH 3/6] Generating dependency graph") 

    # Generate SVG
    subprocess.run(
        [
            *common_args,
            "-o",
            str(output_path / "deps_graph.svg"),
        ],
        check=True,
    )

    # Generate DOT
    subprocess.run(
        [
            *common_args,
            "-T",
            "dot",
            "-o",
            str(output_path / "deps_graph.dot"),
        ],
        check=True,
    )

    # 4. Process the graph to generate the json format for the agent to read
    print("[GRAPH 4/6] Converting the dependency graphs to JSON")
    subprocess.run(
        [
            "python", 
            "scripts/process_deps_graph.py",
            str(output_path / "deps_graph.dot"),
            "-o",
            str(output_path / "deps_graph.json"),
        ],
        check=True,
    )

    # 5. Generate visibility matrix
    print("[GRAPH 5/6] Generating visibility matrix")

    subprocess.run(
        [
            "python", 
            "scripts/gen_visibility_matrix.py",
            str(output_path / "deps_graph.json"),
            "-o",
            str(output_path),
        ],
        check=True,
    )

    # 6. Remove temporary entry file
    # print("[GRAPH 6/6] Removing temp file")
    # entryfile_path.unlink()

    
# usage: python scripts/references_deps_graph.py <problem> <output> 
# the problem is the PROBLEM NAME not the entrypoint directory (src) 
if __name__ == "__main__":
    main()