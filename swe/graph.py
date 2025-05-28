from typing import Annotated, Dict, List, TypedDict, Union
from langgraph.graph import Graph, StateGraph
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from .context import SweContext
from .ask import SweAsk
from .plan_editor import PlanEditor

class GraphState(TypedDict):
    """State for the implementation graph."""
    question: str
    plan: str
    context: str
    chat_history: List[Dict[str, str]]
    current_file: str
    next_file: str
    implementation: str
    verbose: bool

class PlanNode:
    """Node for generating and processing the implementation plan."""
    def __init__(self, swe_context: SweContext):
        self.swe_context = swe_context
        self.swe_ask = SweAsk(swe_context)
        self.plan_editor = PlanEditor()

    def __call__(self, state: GraphState) -> GraphState:
        # Generate plan
        preliminary_prompt = (
            f"You are an expert software engineer. You are going to implement a goal: {state['question']}. "
            "List the steps to implement the goal: which files are going to be edited or created?"
        )
        plan = self.swe_ask.ask(preliminary_prompt)
        self.plan_editor.set_content(plan)
        
        return {
            **state,
            "plan": plan
        }

class ContextNode:
    """Node for gathering context and chat history."""
    def __init__(self, swe_context: SweContext):
        self.swe_context = swe_context

    def __call__(self, state: GraphState) -> GraphState:
        context_content = self.swe_context._get_context_content(state['verbose'])
        chat_history = self.swe_context._load_chat_history()
        
        return {
            **state,
            "context": context_content,
            "chat_history": chat_history
        }

class ImplementationNode:
    """Node for generating implementation."""
    def __init__(self, swe_context: SweContext):
        self.swe_context = swe_context
        self.llm = ChatOpenAI(model="gpt-4", temperature=0)

    def __call__(self, state: GraphState) -> GraphState:
        from langchain.prompts import ChatPromptTemplate
        
        prompt_template = ChatPromptTemplate.from_template(
            "You are an expert software engineer with the following task to implement: {goal}\n"
            "Here is the plan to implement the goal:\n"
            "{plan}\n"
            "You are implementing code changes one file at a time. Review the project files and conversation history:\n\n"
            "CONTEXT:\n"
            "{context}\n\n"
            "CONVERSATION:\n"
            "{history}\n\n"
            "Respond ONLY with a JSON object containing:\n"
            "{{\n"
            '    "file": "path/to/file",           // The file to modify\n'
            '    "content": "full file content",   // Complete file implementation\n'
            '    "next_file_to_implement": "path"  // Next file (or "None" if you reached the goal)\n'
            "}}\n\n"
        )

        chain = prompt_template | self.llm
        response = chain.invoke({
            "goal": state['question'],
            "plan": state['plan'],
            "context": state['context'],
            "history": "\n".join([f'{msg["role"].capitalize()}: {msg["content"]}' for msg in state['chat_history']])
        })

        # Update chat history
        self.swe_context._update_chat_history(
            state['chat_history'],
            state['question'],
            response.content
        )

        return {
            **state,
            "implementation": response.content
        }

class FileWriterNode:
    """Node for writing implementation to files."""
    def __init__(self, swe_context: SweContext):
        self.swe_context = swe_context

    def __call__(self, state: GraphState) -> GraphState:
        import json
        import os
        import shutil
        from pydantic import BaseModel

        class ImplementResponse(BaseModel):
            file: str
            content: str
            next_file_to_implement: str

        try:
            implement_response = ImplementResponse.model_validate_json(state['implementation'])
            file_path = implement_response.file
            content = implement_response.content
            
            if file_path and content:
                # Create backup
                backup_dir = os.path.join(os.path.expanduser("~"), ".swe", "backup")
                os.makedirs(backup_dir, exist_ok=True)
                if os.path.exists(file_path):
                    shutil.copy(file_path, backup_dir)
                
                # Write file
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w') as f:
                    f.write(content)
                
                return {
                    **state,
                    "current_file": file_path,
                    "next_file": implement_response.next_file_to_implement
                }
        except Exception as e:
            print(f"Error writing file: {e}")
            return state

def create_implementation_graph(swe_context: SweContext) -> Graph:
    """Create the implementation graph."""
    # Create nodes
    plan_node = PlanNode(swe_context)
    context_node = ContextNode(swe_context)
    implementation_node = ImplementationNode(swe_context)
    file_writer_node = FileWriterNode(swe_context)

    # Create graph
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("generate_plan", plan_node)
    workflow.add_node("gather_context", context_node)
    workflow.add_node("generate_implementation", implementation_node)
    workflow.add_node("write_file", file_writer_node)
    workflow.add_node("end", lambda x: x)  # End node that just returns the state

    # Define edges
    workflow.add_edge("generate_plan", "gather_context")
    workflow.add_edge("gather_context", "generate_implementation")
    workflow.add_edge("generate_implementation", "write_file")
    
    # Add conditional edge for next file
    def should_continue(state: GraphState) -> str:
        return "generate_plan" if state["next_file"] != "None" else "end"
    
    workflow.add_conditional_edges(
        "write_file",
        should_continue,
        {
            "generate_plan": "generate_plan",
            "end": "end"
        }
    )

    # Set entry point
    workflow.set_entry_point("generate_plan")

    return workflow.compile()

def plot_graph(graph: Graph, output_path: str = "implementation_graph.png") -> None:
    """Plot the graph and save it to a file."""
    try:
        # Get the Pydot graph object
        pydot_graph = graph.get_graph()
        
        # Render to PNG
        pydot_graph.draw_png(output_path)
        print(f"Graph visualization saved to {output_path}")
    except Exception as e:
        print(f"Error plotting graph: {e}")
        print("Please ensure you have graphviz and pydotplus installed: pip install graphviz pydotplus") 