# from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
# from langchain_core.messages import (HumanMessage,SystemMessage,)
#
# llm = HuggingFaceEndpoint(
#     model="Qwen/Qwen3-4B",
#     task="text-generation",
#     max_new_tokens=512,
#     do_sample=False,
#     repetition_penalty=1.03
# )
#
# chat_model = ChatHuggingFace(llm=llm)
# print(chat_model)
# messages = [
#     SystemMessage(content="You're a helpful assistant"),
#     HumanMessage(
#         content="What happens when an unstoppable force meets an immovable object?"
#     ),
# ]
#
# ai_msg = chat_model.invoke(messages)
#
# print(ai_msg.content)


from langchain_core.messages import SystemMessage, HumanMessage
from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
model_id="TheCasvi/Qwen3-1.7B-35KD"
llm = HuggingFacePipeline.from_model_id(
    model_id=model_id,
    task="text-generation",
    pipeline_kwargs={
        "max_new_tokens": 512,
        "do_sample": False,
        "repetition_penalty": 1.03,
    }
)
chat_model = ChatHuggingFace(llm=llm, model_id=model_id)
messages = [
    SystemMessage(content="You're a helpful assistant"),
    HumanMessage(
        content="What happens when an unstoppable force meets an immovable object?"
    ),
]

ai_msg = chat_model.invoke(messages)

print(ai_msg.content)