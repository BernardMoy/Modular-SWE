# Given a dependency graph in JSON
# Output a set of unique nodes (modules)
def get_all_modules(json_object):
    all_modules = set()
    for key, value in json_object.items():
        all_modules.add(key)

        for v in value:
            all_modules.add(v)

    return all_modules
