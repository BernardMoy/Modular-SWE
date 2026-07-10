"""
Given a directory, write an entrypoint file directly inside it
that imports all python files inside that directory. 
"""
import argparse 
from pathlib import Path 
import os 

def write_entrypoint(directory, entryfile_name): 
    target_dir = Path(directory)

    with open(target_dir / f"{entryfile_name}.py", 'w') as f: 
        # walk through the target directory
        for root, dirs, files in os.walk(target_dir):
            # skip the venv directory 
            dirs[:] = [d for d in dirs if d not in {".venv", "__pycache__", ".git"}]

            for pyfile in files: 
                if not pyfile.endswith(".py"): 
                    continue 
                
                # skip the entrypoint name file 
                if pyfile == f"{entryfile_name}.py": 
                    continue 
                
                pyfile_path = Path(root) / pyfile
                rel_path = pyfile_path.relative_to(target_dir)
                module = ".".join(rel_path.with_suffix("").parts)

                # Convert package.__init__ to "import package"
                if module.endswith(".__init__"):
                    module = module.removesuffix(".__init__")

                f.write(f"import {module}\n")
                                    

def main(): 
    parser = argparse.ArgumentParser() 
    parser.add_argument("directory", help="directory to the implementation")
    parser.add_argument("entryfile_name", help="name of the entrypoint file to be created, no .py needed")
    args = parser.parse_args()

    write_entrypoint(args.directory, args.entryfile_name)

if __name__ == "__main__":
    main()