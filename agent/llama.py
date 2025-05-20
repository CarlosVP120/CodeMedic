from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
from langchain_core.messages import SystemMessage, HumanMessage
#model_id="TheCasvi/Qwen3-1.7B-35KD-adapter"
model_id="meta-llama/Llama-3.2-1B-Instruct"
llm = HuggingFacePipeline.from_model_id(
    model_id=model_id,
    task="text-generation",
    pipeline_kwargs={
        "max_new_tokens": 512,
        "do_sample": True,
        "repetition_penalty": 1.03,
    }
)
chat_model = ChatHuggingFace(llm=llm, model_id=model_id)
messages = [
    SystemMessage(content="Please use the available tools to resolve the problem."),
    HumanMessage(content="Add 3 and 4. Multiply the result by 2.")
]

response = chat_model.invoke(messages)
print(response.content)
