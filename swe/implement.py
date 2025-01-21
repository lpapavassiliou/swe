import json
import os
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from typing import List, Dict
from pydantic import BaseModel
from swe.context import SweContext
import shutil
from swe.ask import SweAsk
from swe.plan_editor import PlanEditor

class ImplementResponse(BaseModel):
    file: str
    content: str
    next_file_to_implement: str

class SweImplement:

    def __init__(self, swe_context: SweContext):
        self.swe_context = swe_context
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.plan_editor = PlanEditor()

    def implement(self, question: str, verbose: bool = False) -> None:
        # Ask to explain in a few sentences what files are going to be edited to implement the goal.
        # The answer will be part of the chat history.
        swe_ask = SweAsk(self.swe_context)
        preliminary_prompt = (
            f"You are an expert software engineer. You are going to implement a goal: {question}. "
            "List the steps to implement the goal: which files are going to be edited or created?"
        )
        plan = swe_ask.ask(preliminary_prompt)
        self.plan_editor.set_content(plan)
        self.swe_context.clear_conversation()

        context_content = self.swe_context._get_context_content(verbose)
        chat_history = self.swe_context._load_chat_history()

        formatted_history = "\n".join([f'{msg["role"].capitalize()}: {msg["content"]}' for msg in chat_history])

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

        if verbose:
            print("\n" + "=" * 80)
            print(" " * 30 + "PROMPT TO LLM")
            print("=" * 80 + "\n")
            formatted_prompt = prompt_template.format_prompt(
                goal=question,
                plan=plan,
                context=context_content,
                history=formatted_history if formatted_history != '' else '<no messages>'
            ).to_string()
            print(formatted_prompt)
            print("\n" + "=" * 80 + "\n")

        try:
            response = chain.invoke({
                "goal": question,
                "plan": plan,
                "context": context_content,
                "history": formatted_history if formatted_history != '' else '<no messages>'
            })
            chat_history.append({"role": "user", "content": question})
            chat_history.append({'role': 'assistant', 'content': response.content})
            if verbose:
                print(f"🤖 Assistant: {response.content}")
        except Exception as e:
            print(f"Error generating response: {e}")

        try:
            implement_response = ImplementResponse.model_validate_json(response.content)
            file_path = implement_response.file
            content = implement_response.content
            if file_path and content:
                # Create subdirectories and file if they don't exist
                if file_path != "None":
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    if not os.path.exists(file_path):
                        open(file_path, "x").close()
                # Create a backup of the file before writing
                backup_dir = os.path.join(os.path.expanduser("~"), ".swe", "backup")
                os.makedirs(backup_dir, exist_ok=True)
                shutil.copy(file_path, backup_dir)
                # Write the content to the file
                with open(file_path, 'w') as f:
                    f.write(content)
                print(f"Implemented changes in {file_path}")
                if implement_response.next_file_to_implement and implement_response.next_file_to_implement != "None":
                    self.swe_context.add_file(implement_response.file)
                    print(f"Next file to implement: {implement_response.next_file_to_implement}")
                    self.implement(question, verbose=verbose)   
                else:
                    print("Implementation complete.")
            else:
                print("Response does not contain 'file' and 'content' fields.")
        except json.JSONDecodeError:
            print("Response is not a valid JSON.")
        
        self.swe_context._save_chat_history(chat_history)