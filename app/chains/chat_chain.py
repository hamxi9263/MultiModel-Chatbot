from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.prompts.system_prompt import SYSTEM_PROMPT
from app.llm.gemini import get_llm
from app.tools.time_tool import get_current_time


def get_chat_chain():
    """
    Build the core chat chain.

    Memory / history is provided explicitly from the Streamlit UI
    (we pass the last N turns in), so this chain itself is stateless.
    """
    llm = get_llm()

    # 🔹 Register tools (OpenAI-style function calling)
    tools = [get_current_time]
    llm_with_tools = llm.bind_tools(tools)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder("history"),
            ("human", "{input}"),
        ]
    )

    return prompt | llm_with_tools
