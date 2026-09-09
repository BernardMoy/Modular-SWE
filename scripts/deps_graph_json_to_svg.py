"""
Given a deps graph json in the design level, 
write its svg 
"""
import graphviz
import argparse 
import json 

def json_to_svg(graph_dict, design_dict, output_path):
    dot = graphviz.Digraph(format="svg")
    dot.attr(rankdir="BT")
    dot.attr("node", shape="box", style="rounded", fontname="Helvetica", fontsize="18", margin="0.2,0.15")
    dot.attr("edge", penwidth="1.2")
    dot.attr(nodesep="0.4", ranksep="0.6")

    # new nodes are highlighted in green 
    new_nodes = [x["module_name"] for x in design_dict if "module_name" in x and x.get("type", "keep") == "new"]

    # changed nodes are highlighted in yellow 
    changed_nodes = [x["module_name"] for x in design_dict if "module_name" in x and x.get("type", "keep") == "changed"]
 
    for node, deps in graph_dict.items(): 
        # render nodes 
        if node in new_nodes: 
            dot.node(node, style="rounded,filled", fillcolor="lightgreen")
        elif node in changed_nodes:
            dot.node(node, style="rounded,filled", fillcolor="yellow")
        else: 
            dot.node(node)

        # render edges 
        for dep in deps:
            dot.edge(node, dep)
 
    return dot.render(filename=output_path, cleanup=True)

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("deps_graph_json_path")
    parser.add_argument("design_json_path")
    parser.add_argument("-o")

    args = parser.parse_args()

    # load the deps graph and design 
    with open(args.deps_graph_json_path, 'r') as f: 
        deps_graph_json = json.load(f) 

    with open(args.design_json_path, 'r') as f: 
        design_json = json.load(f) 

    # gen json 
    json_to_svg(deps_graph_json, design_json, args.o)

if __name__ == "__main__":
    main()
