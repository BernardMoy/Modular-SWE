import os 
from pathlib import Path 
from collections import defaultdict 

# Files not considered in the module count and the add / change / deleted modules count. 
EXCLUDED = {".venv", "__pycache__", ".git", "node_modules", ".pytest_cache"}

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

# Return the total number of files. 
# Used for getting the change proportion
def get_all_modules(implementation_path): 
    s = set() 
    for (root, dirs, files) in os.walk(implementation_path): 
            for f in files: 
                if f.endswith(".py"): 
                    py_file_path = Path(root) / f
                    rel_path = py_file_path.relative_to(implementation_path)
                    s.add(rel_path)

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


# When given a history list of implementation paths, 
def get_change_coupling(implementation_path_history): 
    if len(implementation_path_history) == 0: return {} 

    d_pair = defaultdict(int)  # (a,b): how many times a and b changed together 
    d_versions = defaultdict(list)   # a: {1,2,3} indicate that these 3 modules has a changed 

    # for each consecutive snapshots of the history, get its changed modules 
    for i in range(1, len(implementation_path_history)): 
        first = implementation_path_history[i-1]
        second = implementation_path_history[i] 

        changed_modules = list(get_changed_files(first, second))

        # iterate each pair of changed modules 
        for j in range(len(changed_modules)): 
            for k in range(j+1, len(changed_modules)): 
                key = (changed_modules[j], changed_modules[k])
                d_pair[key] += 1 

        # for each changed modules, increment its count by appending to the list using the version change's key (i) 
        for module in changed_modules: 
            d_versions[module].append(i) 

    result = {} 

    # score = the pair change proportion * how many times the pair is actually changed 
    # FREQUENT coupled change is the problem 
    score = 0 
    total_pairs = 0 

    # for all pairs inside d_pair, calculate change coupling = Count that (A,B) changed together / Count that either A or B changed 
    for key, value in d_pair.items(): 
        a, b = key  
        number_either_changed = len(
            set(
                d_versions[a] + d_versions[b]
                )
            )

        if number_either_changed > 0: 
            prop = d_pair[key] / number_either_changed
            result[key] = prop 
            score += prop*d_pair[key]
            total_pairs += d_pair[key]

    # Return pairs sorted by change coupling
    return {
        "score": score / total_pairs if total_pairs > 0 else 1, 
        "pairs": sorted(result.items(), key=lambda item: item[1], reverse=True)
    }


