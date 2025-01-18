from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import json
import os

class SweAsk:
    def __init__(self, swe_context):
        self.swe_context = swe_context
        self.llm = ChatOpenAI(model="gpt-4", temperature=0)
        self.chat_file = os.path.join(os.path.expanduser("~"), ".swe", "chat.json")
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.chat_file), exist_ok=True)

    def _load_chat_history(self):
        """Load existing chat history from the chat.json file."""
        if os.path.exists(self.chat_file):
            try:
                with open(self.chat_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                print("Warning: Could not read or parse chat history. Starting fresh.")
        return []

    def _save_chat_history(self, chat_history):
        """Save chat history to the chat.json file."""
        try:
            with open(self.chat_file, 'w') as f:
                json.dump(chat_history, f, indent=4)
        except IOError as e:
            print(f"Error saving chat history: {e}")

    def ask(self, question: str, verbose: bool = False):
        user_message = {"role": "user", "content": question}

        # Load the context
        data = self.swe_context._load_context()
        if data is None or not data.get("context"):
            print("No context files available. Use 'swe add <file>' to add files.")

        # Read content from all context files
        context_content = ""
        for file in data["context"]:
            try:
                if verbose:
                    print(f"Reading file: {file}")
                with open(file, "r") as f:
                    file_content = f.read()
                    context_content += f"\n\n### File: {file}\n\n{file_content}\n"
            except Exception as e:
                print(f"Warning: Could not read {file}, removed from context.")
                self.swe_context.remove(file)

        # Load existing chat history
        chat_history = self._load_chat_history()

        # Format chat history as part of the prompt
        formatted_history = ""
        for msg in chat_history:
            role = msg["role"].capitalize()
            content = msg["content"]
            formatted_history += f"{role}: {content}\n"

        # Define a prettier prompt template with chat history included
        prompt_template = ChatPromptTemplate.from_template(
            "You are a helpful coding assistant. The following are the contents of files in the current context:\n\n"
            "{context}\n\n"
            "The following is the conversation so far:\n\n"
            "{history}\n\n"
            "Using this information, address the following request as concisely as possible:\n\nREQUEST: {question}"
        )

        # Create the chain using the prompt and the LLM
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

        # Run the chain
        try:
            response = chain.invoke({
                "context": context_content,
                "history": formatted_history,
                "question": question
            })
            print(f"\n\n{response.content}")
            chat_history.append({'role': 'assistant', 'content': response.content})
        except Exception as e:
            print(f"Error generating response: {e}")

        # Save updated chat history
        self._save_chat_history(chat_history)

    def clear_conversation(self):
        """Clear the conversation history and remove the saved chat file."""
        try:
            if os.path.exists(self.chat_file):
                os.remove(self.chat_file)
            print("Conversation history cleared.")
        except IOError as e:
            print(f"Error clearing conversation history: {e}")