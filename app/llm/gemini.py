import os
from langchain_openai import ChatOpenAI

def get_llm():
    return ChatOpenAI(
        model="openai/gpt-4o-mini",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
        temperature=0.3,
        tags=["streamlit", "multimodal-chatbot"],
    )
