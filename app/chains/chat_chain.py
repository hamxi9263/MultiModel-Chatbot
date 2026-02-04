from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from app.prompts.system_prompt import SYSTEM_PROMPT
from app.llm.gemini import get_llm
from app.tools.time_tool import get_current_time

store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


def get_chat_chain():
    llm = get_llm()

    # 🔹 Register tools (OpenAI-style function calling)
    tools = [get_current_time]
    llm_with_tools = llm.bind_tools(tools)

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        ("human", "{input}")
    ])

    chain = prompt | llm_with_tools

    return RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history"
    )
