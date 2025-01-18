from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from swe.context import SweContext

class SweAsk:
    def __init__(self, swe_context: SweContext):
        self.swe_context = swe_context
        self.llm = ChatOpenAI(model="gpt-4", temperature=0)

from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

class SweAsk:
    def __init__(self, swe_context):
        self.swe_context = swe_context
        self.llm = ChatOpenAI(model="gpt-4", temperature=0)

    def ask(self, question: str, verbose: bool = False):
        # Load the context
        data = self.swe_context._load_context()
        if data is None or not data.get("context"):
            print("No context files available. Use 'swe add <file>' to add files.")

        # Read content from all context files
        context_content = ""
        for file in data["context"]:
            try:
                # Print the file being read
                print(f"Reading file: {file}")
                with open(file, "r") as f:
                    file_content = f.read()
                    context_content += f"\n\n### File: {file}\n\n{file_content}\n"
            except Exception as e:
                print(f"Warning: Could not read {file}, removed from context")
                self.swe_context.remove(file)

        # Define a prettier prompt template
        prompt_template = ChatPromptTemplate.from_template(
            "You are a helpful coding assistant. The following are the contents of files in the current context:\n\n"
            "{context}\n\n"
            "Using this information, answer the following question as concisely as possible:\n\nQUESTION: {question}"
        )

        # Create the chain using the prompt and the LLM
        chain = prompt_template | self.llm
        
        if verbose:
            print("\n" + "="*80)
            print(" "*30 + "PROMPT TO LLM")
            print("="*80 + "\n")
            formatted_prompt = prompt_template.format(context=context_content, question=question)
            print(formatted_prompt)
            print("\n" + "="*80 + "\n")

        # Run the chain
        try:
            response = chain.invoke({"context": context_content, "question": question})
            print(f"Answer:\n\n{response.content}")
        except Exception as e:
            print(f"Error generating response: {e}")