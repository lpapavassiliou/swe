from typing import Annotated, Dict, List, TypedDict, Union
from langgraph.graph import Graph, StateGraph
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from .context import SweContext
from .ask import SweAsk
from .plan_editor import PlanEditor

# Define the Pydantic model for structured output
class ImplementResponse(BaseModel):
    file: str
    content: str
    next_file_to_implement: str

class GraphState(TypedDict):
    """State for the implementation graph."""
    question: str
    plan: str
    context: str
    chat_history: List[Dict[str, str]]
    current_file: str
    next_file: str
    implementation: Union[ImplementResponse, str] # Can be Pydantic model or raw string
    verbose: bool

class PlanNode:
    """Node for generating and processing the implementation plan."""
    def __init__(self, swe_context: SweContext):
        self.swe_context = swe_context
        self.swe_ask = SweAsk(swe_context)
        self.plan_editor = PlanEditor()

    def __call__(self, state: GraphState) -> GraphState:
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
        # Configure LLM for structured output with the ImplementResponse model
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0).with_structured_output(ImplementResponse)

    def __call__(self, state: GraphState) -> GraphState:
        from langchain.prompts import ChatPromptTemplate
        
        # Simplified prompt, as structured output handles JSON format
        prompt_template = ChatPromptTemplate.from_template(
            "You are an expert software engineer with the following task to implement: {goal}\n"
            "Here is the plan to implement the goal:\n"
            "{plan}\n"
            "You are implementing code changes ONE FILE AT A TIME. Review the project files and conversation history:\n\n"
            "CONTEXT:\n"
            "{context}\n\n"
            "CONVERSATION:\n"
            "{history}\n\n"
            "Provide the full path to the file to modify, the complete content for that file, "
            "and the path to the next file to implement (or 'None' if you don't "
            "need to edit any more files)."
        )

        chain = prompt_template | self.llm
        
        formatted_history = "\n".join([f'{msg["role"].capitalize()}: {msg["content"]}' for msg in state['chat_history']])
        
        try:
            # Invoke the chain. The result should be an ImplementResponse object.
            response_obj = chain.invoke({
                "goal": state['question'],
                "plan": state['plan'],
                "context": state['context'],
                "history": formatted_history if formatted_history else "<no messages>"
            })

            # Update chat history with the raw content (or a representation)
            # For simplicity, we'll serialize the Pydantic model to JSON string for history
            import json
            response_content_for_history = response_obj.model_dump_json()

            self.swe_context._update_chat_history(
                state['chat_history'],
                state['question'],
                response_content_for_history 
            )

            return {
                **state,
                "implementation": response_obj # Store the Pydantic object directly
            }
        except Exception as e:
            print(f"Error in ImplementationNode: {e}")
            # Fallback or error handling: store the error or an empty response
            error_response = ImplementResponse(file="ERROR", content=f"Error: {e}", next_file_to_implement="None")
            self.swe_context._update_chat_history(
                 state['chat_history'],
                 state['question'],
                 error_response.model_dump_json()
            )
            return {
                **state,
                "implementation": error_response 
            }


class FileWriterNode:
    """Node for writing implementation to files."""
    def __init__(self, swe_context: SweContext):
        self.swe_context = swe_context

    def __call__(self, state: GraphState) -> GraphState:
        import os
        import shutil
        
        implement_response = state['implementation']

        # Check if implementation is the Pydantic model or needs parsing (fallback)
        if not isinstance(implement_response, ImplementResponse):
            # This is a fallback in case structured output failed and a string was returned
            # Or if an error occurred and we have the error Pydantic model
            print(f"Warning: FileWriterNode received a string, attempting to parse. Content: {implement_response}")
            try:
                # If it's an error string from a previous node that didn't produce a Pydantic object
                if isinstance(implement_response, str) and implement_response.startswith("ERROR"):
                     return {**state, "next_file": "None"} # Stop further processing

                # Attempt to parse if it's a JSON string
                implement_response_obj = ImplementResponse.model_validate_json(implement_response)
            except Exception as e:
                print(f"Error parsing implementation string in FileWriterNode: {e}")
                # Decide how to handle: maybe stop, or try to extract info if possible
                return {**state, "next_file": "None"} # Stop if parsing fails
        else:
            implement_response_obj = implement_response


        if implement_response_obj.file == "ERROR": # Check for error sentinel
            print(f"Skipping file writing due to previous error: {implement_response_obj.content}")
            return {**state, "next_file": "None"}


        file_path = implement_response_obj.file
        content = implement_response_obj.content
        next_file = implement_response_obj.next_file_to_implement

        # Clean the content: remove markdown code fences
        import re
        # Regex to find markdown code blocks (e.g., ```python ... ``` or ``` ... ```)
        # It captures the content within the fences.
        match = re.search(r"^```(?:[a-zA-Z0-9_\-]+)?\n(.*?)\n^```$", content, re.DOTALL | re.MULTILINE)
        if match:
            content = match.group(1).strip() # Get the captured group and strip whitespace
        else:
            # Fallback for cases where only fences might be present without language spec or newline structure
            content = re.sub(r"^```(?:[a-zA-Z0-9_\-]+)?\n?", "", content, flags=re.MULTILINE)
            content = re.sub(r"\n?^```$", "", content, flags=re.MULTILINE).strip()

        if file_path and content and file_path.lower() != "none":
            try:
                # Ensure directory exists
                dir_name = os.path.dirname(file_path)
                if dir_name: # Ensure dirname is not empty (for files in root)
                    os.makedirs(dir_name, exist_ok=True)
                
                # Create backup
                backup_dir = os.path.join(os.path.expanduser("~"), ".swe", "backup")
                os.makedirs(backup_dir, exist_ok=True)
                if os.path.exists(file_path):
                    shutil.copy(file_path, os.path.join(backup_dir, os.path.basename(file_path) + f".{os.times().user:.0f}.bak")) # Add timestamp to backup
                else: # If file doesn't exist, create an empty one for shutil.copy
                    open(file_path, "x").close()
                    shutil.copy(file_path, os.path.join(backup_dir, os.path.basename(file_path) + f".{os.times().user:.0f}.bak"))


                # Write file
                with open(file_path, 'w') as f:
                    f.write(content)
                print(f"Implemented changes in {file_path}")
                
                # Add implemented file to context for next iteration if needed
                self.swe_context.add_file(file_path)

                return {
                    **state,
                    "current_file": file_path,
                    "next_file": next_file
                }
            except Exception as e:
                print(f"Error writing file {file_path}: {e}")
                # If writing fails, we might want to stop or try something else
                return {**state, "next_file": "None"} # Stop on write error
        else:
            print(f"FileWriterNode: file_path or content is missing or file_path is 'none'. file_path='{file_path}'")
            # If no file_path, or content is empty, or file_path is "None" then we are done or there's an issue.
            return {**state, "next_file": "None"}

def create_implementation_graph(swe_context: SweContext) -> Graph:
    """Create the implementation graph."""
    plan_node = PlanNode(swe_context)
    context_node = ContextNode(swe_context)
    implementation_node = ImplementationNode(swe_context)
    file_writer_node = FileWriterNode(swe_context)

    workflow = StateGraph(GraphState)

    workflow.add_node("gather_context", context_node)
    workflow.add_node("generate_plan", plan_node)
    workflow.add_node("generate_implementation", implementation_node)
    workflow.add_node("write_file", file_writer_node)
    workflow.add_node("end", lambda x: x) 

    workflow.add_edge("gather_context", "generate_plan")
    workflow.add_edge("generate_plan", "generate_implementation")
    workflow.add_edge("generate_implementation", "write_file")
    
    def should_continue(state: GraphState) -> str:
        next_file_val = state.get("next_file")
        return "gather_context" if next_file_val and next_file_val.lower() != "none" else "end"
    
    workflow.add_conditional_edges(
        "write_file",
        should_continue,
        {
            "gather_context": "gather_context",
            "end": "end"
        }
    )

    workflow.set_entry_point("gather_context")
    return workflow.compile()


def plot_graph(graph: Graph, output_path: str = "implementation_graph.png") -> None:
    """Plot the graph and save it to a file."""
    try:
        pydot_graph = graph.get_graph()
        pydot_graph.draw_png(output_path)
        print(f"Graph visualization saved to {output_path}")
    except Exception as e:
        print(f"Error plotting graph: {e}")
        print("Please ensure you have graphviz and pydotplus installed: pip install graphviz pydotplus")