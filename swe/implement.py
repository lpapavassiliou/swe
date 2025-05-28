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
        swe_ask = SweAsk(self.swe_context)
        plan = self._generate_plan(question, swe_ask)
        self.plan_editor.set_content(plan)
        self.swe_context.clear_conversation()

        context_content = self.swe_context._get_context_content(verbose)
        chat_history = self.swe_context._load_chat_history()

        formatted_history = self._format_chat_history(chat_history)

        prompt_template = self._create_prompt_template()

        if verbose:
            self._print_verbose_info(prompt_template, question, plan, context_content, formatted_history)

        try:
            response = self._invoke_chain(prompt_template, question, plan, context_content, formatted_history)
            self._update_chat_history(chat_history, question, response.content)
            if verbose:
                print(f"🤖 Assistant: {response.content}")
        except Exception as e:
            print(f"Error generating response: {e}")

        self._process_response(response.content, question, verbose)

    def _generate_plan(self, question: str, swe_ask: SweAsk) -> str:
        preliminary_prompt = (
            f"You are an expert software engineer. You are going to implement a goal: {question}. "
            "List the steps to implement the goal: which files are going to be edited or created?"
        )
        return swe_ask.ask(preliminary_prompt)

    def _format_chat_history(self, chat_history: List[Dict[str, str]]) -> str:
        return "\n".join([f'{msg["role"].capitalize()}: {msg["content"]}' for msg in chat_history])

    def _create_prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate.from_template(
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

    def _print_verbose_info(self, prompt_template: ChatPromptTemplate, goal: str, plan: str, context: str, history: str) -> None:
        print("\n" + "=" * 80)
        print(" " * 30 + "PROMPT TO LLM")
        print("=" * 80 + "\n")
        formatted_prompt = prompt_template.format_prompt(
            goal=goal,
            plan=plan,
            context=context,
            history=history if history != '' else '<no messages>'
        ).to_string()
        print(formatted_prompt)
        print("\n" + "=" * 80 + "\n")

    def _invoke_chain(self, prompt_template: ChatPromptTemplate, goal: str, plan: str, context: str, history: str):
        chain = prompt_template | self.llm
        return chain.invoke({
            "goal": goal,
            "plan": plan,
            "context": context,
            "history": history if history != '' else '<no messages>'
        })

    def _update_chat_history(self, chat_history: List[Dict[str, str]], question: str, response_content: str) -> None:
        chat_history.append({"role": "user", "content": question})
        chat_history.append({'role': 'assistant', 'content': response_content})

    def _process_response(self, response_content: str, question: str, verbose: bool) -> None:
        try:
            implement_response = ImplementResponse.model_validate_json(response_content)
            file_path = implement_response.file
            content = implement_response.content
            if file_path and content:
                self._write_to_file(file_path, content)
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

    def _write_to_file(self, file_path: str, content: str) -> None:
        if file_path != "None":
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            if not os.path.exists(file_path):
                open(file_path, "x").close()
        backup_dir = os.path.join(os.path.expanduser("~"), ".swe", "backup")
        os.makedirs(backup_dir, exist_ok=True)
        shutil.copy(file_path, backup_dir)
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"Implemented changes in {file_path}")
