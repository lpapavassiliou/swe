from swe.graph import create_implementation_graph, plot_graph
from swe.context import SweContext

def main():
    # Create context
    context = SweContext()
    
    # Create graph
    graph = create_implementation_graph(context)
    
    # Plot graph
    plot_graph(graph)

if __name__ == "__main__":
    main() 