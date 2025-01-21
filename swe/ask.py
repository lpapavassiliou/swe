import json
import os
from typing import List, Dict

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from swe.context import SweContext

class SweAsk:

    def __init__(self, swe_context: SweContext):
        self.swe_context = swe_context
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)

    def ask(self, question: str, verbose: bool = False) -> str:
        context_content = self.swe_context._get_context_content(verbose)
        chat_history = self.swe_context._load_chat_history()

        formatted_history = "\n".join([f'{msg["role"].capitalize()}: {msg["content"]}' for msg in chat_history])

        prompt_template = ChatPromptTemplate.from_template(
            "You are a helpful coding assistant. The following are the contents of files in the current context:\n\n"
            "{context}\n\n"
            "The following is the conversation so far:\n\n"
            "{history}\n\n"
            "Using this information, address the following request as concisely as possible:\n\nREQUEST: {question}"
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
            print(f"\n\n{response.content}")
            chat_history.append({"role": "user", "content": question})
            chat_history.append({'role': 'assistant', 'content': response.content})
        except Exception as e:
            print(f"Error generating response: {e}")

        self.swe_context._save_chat_history(chat_history)

        return response.content