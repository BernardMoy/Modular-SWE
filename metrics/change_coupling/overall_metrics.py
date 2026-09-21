"""
Metrics related to change coupling: 
Whether there are certain files that always changes together. 
Frequently changing together might indicate tight coupling. 
"""

import os
from pathlib import Path
from collections import defaultdict
import subprocess 

# Files not considered in the module count and the add / change / deleted modules count.
EXCLUDED = {".venv", "__pycache__", ".git", "node_modules", ".pytest_cache"}


# Return a list of files that are added.
def get_added_files(implementation_path_old, implementation_path_new):
    s = set()  # Set of file names
    added_file_names = []

    # Add all the old files to the dictionary
    for root, dirs, files in os.walk(implementation_path_old):
        for f in files:
            if f.endswith(".py"):
                py_file_path = Path(root) / f
                rel_path = py_file_path.relative_to(implementation_path_old)
                s.add(rel_path)

    # For the new files, track which ones does not exist in the previous set
    for root, dirs, files in os.walk(implementation_path_new):
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
    for root, dirs, files in os.walk(implementation_path_old):
        for f in files:
            if f.endswith(".py"):
                py_file_path = Path(root) / f

                # open the file
                try:
                    code = open(py_file_path, "r").read()
                    rel_path = py_file_path.relative_to(implementation_path_old)
                    d[rel_path] = code

                except Exception as e:
                    print(e)

    # For the new files, track which ones have same name but different content
    for root, dirs, files in os.walk(implementation_path_new):
        for f in files:
            if f.endswith(".py"):
                py_file_path = Path(root) / f

                # open the file
                try:
                    code = open(py_file_path, "r").read()
                    rel_path = py_file_path.relative_to(implementation_path_new)

                    if rel_path in d and d[rel_path] != code:
                        changed_file_names.append(f)

                except Exception as e:
                    print(e)

    return changed_file_names


# Return a list of files that are deleted
def get_deleted_files(implementation_path_old, implementation_path_new):
    s = set()  # Set of file names

    # Add all the old files to the dictionary
    for root, dirs, files in os.walk(implementation_path_old):
        for f in files:
            if f.endswith(".py"):
                py_file_path = Path(root) / f
                rel_path = py_file_path.relative_to(implementation_path_old)
                s.add(rel_path)

    # For the new files, remove from the set. Return the remaining set content
    for root, dirs, files in os.walk(implementation_path_new):
        for f in files:
            if f.endswith(".py"):
                py_file_path = Path(root) / f
                rel_path = py_file_path.relative_to(implementation_path_new)

                if rel_path in s:
                    s.remove(rel_path)

    return list(s)

# Given two implementations, get the number of deleted and added lines (git diff) 
def get_added_deleted_lines(old_dir: str, new_dir: str) -> tuple[int, int]:
    # no index: The impl does not have to be git directories 
    result = subprocess.run(
        [
            "git",
            "diff",
            "--no-index",
            "--numstat",
            old_dir,
            new_dir,
        ],
        capture_output=True,
        text=True,
    )

    added = 0
    deleted = 0

    for line in result.stdout.splitlines():
        parts = line.split("\t")

        if len(parts) < 3:
            continue

        added_str, deleted_str = parts[:2]

        if added_str.isdigit():
            added += int(added_str)

        if deleted_str.isdigit():
            deleted += int(deleted_str)

    # Also return the old LOC for proportion
    old_loc = 0

    for path in Path(old_dir).rglob("*.py"):
        if path.is_file():
            with path.open("r", encoding="utf-8", errors="ignore") as f:
                old_loc += sum(1 for _ in f)

    return {
        "added": added, 
        "deleted": deleted, 
        "old_loc": old_loc
    }

# Return the total number of files.
# Used for getting the change proportion
def get_all_modules(implementation_path):
    s = set()
    for root, dirs, files in os.walk(implementation_path):
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
    for root, dirs, files in os.walk(implementation_path_old):
        for f in files:
            if f.endswith(".py"):
                py_file_path = Path(root) / f

                # open the file
                try:
                    code = open(py_file_path, "r").read()
                    rel_path = py_file_path.relative_to(implementation_path_old)
                    d[rel_path] = code
                    original_count += 1

                except Exception as e:
                    print(e)

    # For the new files, track which ones have same name but different content
    for root, dirs, files in os.walk(implementation_path_new):
        for f in files:
            if f.endswith(".py"):
                py_file_path = Path(root) / f

                # open the file
                try:
                    code = open(py_file_path, "r").read()
                    rel_path = py_file_path.relative_to(implementation_path_new)

                    if rel_path in d and d[rel_path] != code:
                        changed_count += 1

                except Exception as e:
                    print(e)

    return changed_count / original_count if original_count > 0 else 0


# When given a history list of implementation paths,
def get_change_coupling(implementation_path_history):
    if len(implementation_path_history) == 0:
        return {}

    d_pair = defaultdict(int)  # (a,b): how many times a and b changed together
    d_versions = defaultdict(
        list
    )  # a: {1,2,3} indicate that these 3 modules has a changed

    # for each consecutive snapshots of the history, get its changed modules
    for i in range(1, len(implementation_path_history)):
        first = implementation_path_history[i - 1]
        second = implementation_path_history[i]

        changed_modules = list(get_changed_files(first, second))

        # iterate each pair of changed modules
        for j in range(len(changed_modules)):
            for k in range(j + 1, len(changed_modules)):
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
        number_either_changed = len(set(d_versions[a] + d_versions[b]))

        if number_either_changed > 0:
            prop = d_pair[key] / number_either_changed
            result[key] = prop
            score += prop * d_pair[key]
            total_pairs += d_pair[key]

    # Return pairs sorted by change coupling
    return {
        "score": score / total_pairs if total_pairs > 0 else 1,
        "pairs": sorted(result.items(), key=lambda item: item[1], reverse=True),
    }
