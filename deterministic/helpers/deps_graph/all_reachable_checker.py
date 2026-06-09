# # Not used, as pydeps output noise 
# # Such as test.support or tkinter.Tk

# import argparse 
# import json
# from collections import deque 
# from helpers.get_all_modules import get_all_modules

# # Given a dependency graph in JSON
# # Return whether all nodes can be reached from the entry point file 
# def check_all_reachable(json_object, entrypoint): 
#     # Calculate the total number of nodes in the json object 
#     total = get_all_modules(json_object) 

#     # BFS from the entrypoint node 
#     if entrypoint not in json_object: 
#         return False 

#     q = deque([entrypoint])
#     visited = set()
#     while q:
#         cur = q.popleft()
#         # If the node is already visited, skip 
#         if cur in visited:
#             continue
#         visited.add(cur)
 
#         # If the node is not in the graph, skip 
#         if cur not in json_object:
#             continue

#         # Push the neighbours to the queue 
#         for nei in json_object[cur]:
#             if nei not in visited:
#                 q.append(nei)

#     # Check if all nodes have been visited from the entrypoint
#     print(total.difference(visited)) 
#     return len(total) == len(visited)
    


# # usage: check.py [abs-path] [entrypoint] 
# # This assumes the entrypoint file to be named exactly [entrypoint.py], e.g. "circopt.py" in the dependency graph.
# # Importable modules use "name", scripts use "name.py" in the dependency graph.  
# def main(): 
#     parser = argparse.ArgumentParser()
#     parser.add_argument("path", help="Abs path to the dependency graph JSON file")
#     parser.add_argument("entrypoint", help="Name of the entrypoint node (e.g. circopt.py)")
#     args = parser.parse_args()

#     with open(args.path, 'r') as f:
#         graph_json = json.load(f)

#     result = check_all_reachable(json_object=graph_json, entrypoint=args.entrypoint)
#     print(result) 


# if __name__ == "__main__": 
#     main() 