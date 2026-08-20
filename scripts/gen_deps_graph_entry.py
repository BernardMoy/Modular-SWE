"""
Given a directory, write an entrypoint file directly inside it
that imports all python files inside that directory. 
"""
import argparse 
from pathlib import Path 
import os 
from constants import IGNORED_DIRS, INVALID_CHARS

def write_entrypoint(directory, entryfile_name): 
    target_dir = Path(directory)

    with open(target_dir / f"{entryfile_name}.py", 'w') as f: 
        # walk through the target directory
        for root, dirs, files in os.walk(target_dir):
            # skip the venv directory 
            # node_modules contain modules with invalid names (@..). This will cause the graph to break and return an empty graph. 
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

            for pyfile in files: 
                if not pyfile.endswith(".py"): 
                    continue 
                
                # skip the entrypoint name file 
                if pyfile == f"{entryfile_name}.py": 
                    continue 
                
                pyfile_path = Path(root) / pyfile
                rel_path = pyfile_path.relative_to(target_dir)
                module = ".".join(rel_path.with_suffix("").parts)

                if module in {"__init__", "__main__"}: 
                    continue 

                # Convert package.__init__ to "import package"
                if module.endswith(".__init__"):
                    module = module.removesuffix(".__init__")

                # if the module starts with ".agents" (start with .) 
                # ignore it because it would cause an import error 
                if module.startswith("."): 
                    continue 

                # if the module name contains invalid characters such as '-',  ignore this as it will crash on import 
                if any(chars in module for chars in INVALID_CHARS): 
                    continue 

                f.write(f"import {module}\n")
                                    

def main(): 
    parser = argparse.ArgumentParser() 
    parser.add_argument("directory", help="directory to the implementation")
    parser.add_argument("entryfile_name", help="name of the entrypoint file to be created, no .py needed")
    args = parser.parse_args()

    write_entrypoint(args.directory, args.entryfile_name)

if __name__ == "__main__":
    main()