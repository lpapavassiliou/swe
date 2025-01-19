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
        chat_history.append({"role": "user", "content": question})

        formatted_history = "\n".join([f'{msg["role"].capitalize()}: {msg["content"]}' for msg in chat_history])

        prompt_template = ChatPromptTemplate.from_template(
            "You are a highly skilled coding assistant. Below are the contents of the files in the current project:\n\n"
            "{context}\n\n"
            "Here is the conversation history so far:\n\n"
            "{history}\n\n"
            "Your task is to achieve the following goal:\n\nGoal: {question}\n\n"
            "Please follow these rules when providing your response:\n"
            "1. You can only implement one file at a time.\n"
            "2. Your response must be a single valid JSON object with the following fields:\n"
            "   - 'file': The path to the file being implemented.\n"
            "   - 'content': The complete content of the file being implemented (no partial content or shortcuts).\n"
            "   - 'next_file_to_implement': The path to the next file to be implemented, or 'None' if no further files are needed.\n\n"
            "Here is an example of a valid response:\n"
            "{{\n"
            "    'file': 'path/to/file.py',\n"
            "    'content': 'print(\"Hello, world!\")',\n"
            "    'next_file_to_implement': 'path/to/next_file.py'\n"
            "}}\n\n"
            "Additional instructions:\n"
            "- Avoid using Markdown or any additional formatting.\n"
            "- Do not include comments or explanations in your response.\n"
            "- Your output should strictly adhere to the JSON format provided above.\n"
            "- Ensure the 'content' field contains the full implementation of the file.\n"
            "- If you already edited all the necessary files, set 'next_file_to_implement' to None."
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
            chat_history.append({'role': 'assistant', 'content': response.content})
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
                with open(file_path, 'w') as f:
                    f.write(content)
                print(f"Implemented changes in {file_path}")
                if implement_response.next_file_to_implement and implement_response.next_file_to_implement != "None":
                    print(f"Next file to implement: {implement_response.next_file_to_implement}")
                    self.implement(question)   
                else:
                    print("Implementation complete.")
            else:
                print("Response does not contain 'file' and 'content' fields.")
        except json.JSONDecodeError:
            print("Response is not a valid JSON.")
        
        self.swe_context._save_chat_history(chat_history)