from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
import os
from langchain_core.messages import (HumanMessage,SystemMessage,)
#os.environ["HUGGINGFACEHUB_API_TOKEN"] = input("Enter your Hugging Face API key: ")


print("After the token")
llm = HuggingFaceEndpoint(
    model="Qwen/Qwen3-4B",
    task="text-generation",
    max_new_tokens=512,
    do_sample=False,
    repetition_penalty=1.03
)

chat_model = ChatHuggingFace(llm=llm)

messages = [
    SystemMessage(content="You're a helpful assistant"),
    HumanMessage(
        content="What happens when an unstoppable force meets an immovable object?"
    ),
]

ai_msg = chat_model.invoke(messages)

print(ai_msg.content)