"""
Given a deps graph json in the design level, 
write its svg 
"""
import graphviz
import argparse 
import json 

def json_to_svg(graph_dict, output_path):
    dot = graphviz.Digraph(format="svg")
    dot.attr(rankdir="BT")
    dot.attr("node", shape="box", style="rounded", fontname="Helvetica", fontsize="18", margin="0.2,0.15")
    dot.attr("edge", penwidth="1.2")
    dot.attr(nodesep="0.4", ranksep="0.6")
 
    for node, deps in graph_dict.items(): 
        dot.node(node)
        for dep in deps:
            dot.edge(node, dep)
 
    return dot.render(filename=output_path, cleanup=True)

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("path")
    parser.add_argument("-o")

    args = parser.parse_args()

    with open(args.path, 'r') as f: 
        json_to_svg(json.load(f), args.o)

if __name__ == "__main__":
    main()
