from langchain_openai import AzureChatOpenAI
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
import os
load_dotenv(dotenv_path=".env")
load_dotenv()
api_key = os.getenv("AZURE_OPENAI_API_KEY")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT_GPT4")
llm = AzureChatOpenAI(
            azure_endpoint=endpoint,
            azure_deployment="gpt-4o",
            api_version="2025-01-01-preview",
            temperature=0,
            max_tokens=1000,
            timeout=None,
            max_retries=2,
            api_key=api_key
        )


# Define tools
def add(a: int, b: int) -> int:
    """Add two numbers together."""
    print("Inside add")
    return a + b


def multiply(a: int, b: int) -> int:
    """Multiply two numbers together."""
    print("Inside multiply")
    return a * b

tools = [add, multiply]
# Initialize the LLM
# Create the ReAct agent
graph = create_react_agent(model=llm, tools=tools)
# User input
inputs = {"messages": [("system", "Please use the available tools to resolve the problem."),
                       ("user", "Add 3 and 4. Multiply the result by 2.")]}
# Run the ReAct agent
for event in graph.stream(inputs):
    print(event)

print("-----------------------------------------------------------------------------------------------------------------")
messages = graph.invoke(inputs)
for message in messages["messages"]:
    print(message.content)

