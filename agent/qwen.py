from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint,HuggingFacePipeline
from langgraph.prebuilt import create_react_agent

# model_id="TheCasvi/Qwen3-1.7B-35KD-adapter"
# llm = HuggingFacePipeline.from_model_id(
#     model_id=model_id,
#     task="text-generation",
#     pipeline_kwargs={
#         "max_new_tokens": 512,
#         "do_sample": True,
#         "repetition_penalty": 1.03,
#     }
# )
# chat_model = ChatHuggingFace(llm=llm, model_id=model_id)



model_id = "Qwen/Qwen3-4B"
llm = HuggingFaceEndpoint(
    model=model_id,
    task="text-generation",
    max_new_tokens=512,
    do_sample=False,
    repetition_penalty=1.03
)
chat_model = ChatHuggingFace(llm=llm, model_id=model_id)




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
graph = create_react_agent(model=chat_model, tools=tools)
# User input
inputs = {"messages": [("system", "Please use the available tools to resolve the problem."),
                       ("user", "Add 3 and 4. Multiply the result by 2.")]}
# Run the ReAct agent
for event in graph.stream(inputs):
    print(event)

messages = graph.invoke(inputs)
for message in messages["messages"]:
    print(message.content)

