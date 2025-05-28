import json
import os
from typing import List, Dict
from swe.context import SweContext
from swe.graph import create_implementation_graph, GraphState

class SweImplement:

    def __init__(self, swe_context: SweContext):
        self.swe_context = swe_context
        self.graph = create_implementation_graph(swe_context)

    def implement(self, question: str, verbose: bool = False) -> None:
        initial_state: GraphState = {
            "question": question,
            "plan": "",
            "context": "",
            "chat_history": [],
            "current_file": "",
            "next_file": "",
            "implementation": "",
            "verbose": verbose,
        }

        if verbose:
            print("\n" + "=" * 80)
            print(" " * 30 + "STARTING GRAPH EXECUTION")
            print("=" * 80 + "\n")
            print(f"Initial State: {initial_state}")

        final_state = self.graph.invoke(initial_state)

        if verbose:
            print("\n" + "=" * 80)
            print(" " * 30 + "GRAPH EXECUTION COMPLETE")
            print("=" * 80 + "\n")
            print(f"Final State: {final_state}")
        
        print("Implementation complete.")
