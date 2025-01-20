import json
import os
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from typing import List, Dict
from pydantic import BaseModel
from swe.context import SweContext
import shutil

class ImplementResponse(BaseModel):
    file: str
    content: str
    next_file_to_implement: str

class SweImplement:

    def __init__(self, swe_context: SweContext):
        self.swe_context = swe_context
        self.llm = ChatOpenAI(model="gpt-4", temperature=0)

    def implement(self, question: str, verbose: bool = False) -> None:
        context_content = self.swe_context._get_context_content(verbose)
        chat_history = self.swe_context._load_chat_history()

        formatted_history = "\n".join([f'{msg["role"].capitalize()}: {msg["content"]}' for msg in chat_history])

        prompt_template = ChatPromptTemplate.from_template(
            "You are implementing code changes one file at a time. Review the project files and conversation history:\n\n"
            "{context}\n\n"
            "{history}\n\n"
            "Respond ONLY with a JSON object containing:\n"
            "{{\n"
            '    "file": "path/to/file",           // The file to modify\n'
            '    "content": "full file content",   // Complete file implementation\n'
            '    "next_file_to_implement": "path"  // Next file or "None" if complete\n'
            "}}\n\n"
            "GOAL: {question}\n"
        )

        chain = prompt_template | self.llm

        if verbose:
            print("\n" + "=" * 80)
            print(" " * 30 + "PROMPT TO LLM")
            print("=" * 80 + "\n")
            formatted_prompt = prompt_template.format(
                context=context_content, history=formatted_history, question=question
            )
            print(formatted_prompt)
            print("\n" + "=" * 80 + "\n")

        try:
            response = chain.invoke({
                "context": context_content,
                "history": formatted_history,
                "question": question
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
                # Create a backup of the file before writing
                backup_dir = os.path.join(os.path.expanduser("~"), ".swe", "backup")
                os.makedirs(backup_dir, exist_ok=True)
                shutil.copy(file_path, backup_dir)
                # Create the file if it doesn't exist
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                # Write the content to the file
                with open(file_path, 'w') as f:
                    f.write(content)
                print(f"Implemented changes in {file_path}")
                if implement_response.next_file_to_implement and implement_response.next_file_to_implement != "None":
                    print(f"Next file to implement: {implement_response.next_file_to_implement}")
                    self.implement(question, verbose=verbose)   
                else:
                    print("Implementation complete.")
            else:
                print("Response does not contain 'file' and 'content' fields.")
        except json.JSONDecodeError:
            print("Response is not a valid JSON.")
        
        self.swe_context._save_chat_history(chat_history)