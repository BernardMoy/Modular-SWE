import os 
from pathlib import Path 
from collections import defaultdict 

# Return a list of files that are added. 
def get_added_files(implementation_path_old, implementation_path_new): 
    s = set() # Set of file names 
    added_file_names = [] 

    # Add all the old files to the dictionary
    for (root, dirs, files) in os.walk(implementation_path_old): 
        for f in files: 
            if f.endswith(".py"): 
                py_file_path = Path(root) / f
                rel_path = py_file_path.relative_to(implementation_path_old)
                s.add(rel_path)

    
    # For the new files, track which ones does not exist in the previous set 
    for (root, dirs, files) in os.walk(implementation_path_new): 
        for f in files: 
            if f.endswith(".py"): 
                py_file_path = Path(root) / f
                rel_path = py_file_path.relative_to(implementation_path_new)

                if rel_path not in s: 
                    added_file_names.append(f) 

    return added_file_names

# Return a list of files that are changed
# This does not count files that are added, just existing files that changed 
# This assumes that names are not changed while implementing a feature
def get_changed_files(implementation_path_old, implementation_path_new): 
    d = {}  # file names: file content 
    changed_file_names = [] 

    # Add all the old files to the dictionary
    for (root, dirs, files) in os.walk(implementation_path_old): 
        for f in files: 
            if f.endswith(".py"): 
                py_file_path = Path(root) / f

                # open the file 
                try: 
                    code = open(py_file_path, 'r').read() 
                    rel_path = py_file_path.relative_to(implementation_path_old)
                    d[rel_path] = code 

                except Exception as e: 
                    print(e)
    
    # For the new files, track which ones have same name but different content 
    for (root, dirs, files) in os.walk(implementation_path_new): 
        for f in files: 
            if f.endswith(".py"): 
                py_file_path = Path(root) / f

                # open the file 
                try: 
                    code = open(py_file_path, 'r').read() 
                    rel_path = py_file_path.relative_to(implementation_path_new)

                    if rel_path in d and d[rel_path] != code: 
                        changed_file_names.append(f) 

                except Exception as e: 
                    print(e)
    
    return changed_file_names

# Return a list of files that are deleted 
def get_deleted_files(implementation_path_old, implementation_path_new): 
    s = set() # Set of file names 

    # Add all the old files to the dictionary
    for (root, dirs, files) in os.walk(implementation_path_old): 
        for f in files: 
            if f.endswith(".py"): 
                py_file_path = Path(root) / f
                rel_path = py_file_path.relative_to(implementation_path_old)
                s.add(rel_path)

    
    # For the new files, remove from the set. Return the remaining set content 
    for (root, dirs, files) in os.walk(implementation_path_new): 
        for f in files: 
            if f.endswith(".py"): 
                py_file_path = Path(root) / f
                rel_path = py_file_path.relative_to(implementation_path_new)

                if rel_path in s: 
                    s.remove(rel_path)

    return list(s) 


# Return the proportion of original files that were changed. 
def get_changed_proportion(implementation_path_old, implementation_path_new): 
    d = {}  # file names: file content 
    original_count = 0 
    changed_count = 0 

    # Add all the old files to the dictionary
    for (root, dirs, files) in os.walk(implementation_path_old): 
        for f in files: 
            if f.endswith(".py"): 
                py_file_path = Path(root) / f

                # open the file 
                try: 
                    code = open(py_file_path, 'r').read() 
                    rel_path = py_file_path.relative_to(implementation_path_old)
                    d[rel_path] = code 
                    original_count += 1 

                except Exception as e: 
                    print(e)
    
    # For the new files, track which ones have same name but different content 
    for (root, dirs, files) in os.walk(implementation_path_new): 
        for f in files: 
            if f.endswith(".py"): 
                py_file_path = Path(root) / f

                # open the file 
                try: 
                    code = open(py_file_path, 'r').read() 
                    rel_path = py_file_path.relative_to(implementation_path_new)

                    if rel_path in d and d[rel_path] != code: 
                        changed_count += 1 

                except Exception as e: 
                    print(e)
    
    return changed_count / original_count if original_count > 0 else 0 

# UNUSED - handled in evaluation.ipynb
# def get_changed_files_from_history(implementation_history): 
#     d = defaultdict(int) 
#     for i in range(1, len(implementation_history)): 
#         prev = implementation_history[i-1]
#         cur = implementation_history[i] 
#         changed_files = get_changed_files(prev, cur) 
#         for f in changed_files: 
#             d[f] += 1 
    
#     return d 
