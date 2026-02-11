import streamlit as st
import os
import requests
import json
from tools import get_current_time

# 🔐 Use environment variable in production
OPENROUTER_API_KEY = "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"

MODEL = "openai/gpt-4o-mini"  # Make sure model exists in OpenRouter

st.set_page_config(page_title="🌍 AI World Clock Agent")
st.title("🌍 AI World Clock Agent")

if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------
# Tool Schema (VERY IMPORTANT)
# -------------------------
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current time for a given IANA timezone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "IANA timezone like Asia/Karachi, Europe/London, America/New_York"
                    }
                },
                "required": ["timezone"]
            }
        }
    }
]

# -------------------------
# Call LLM
# -------------------------
def call_llm(messages, tools=None):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.4,
    }

    if tools:
        data["tools"] = tools
        data["tool_choice"] = "auto"

    response = requests.post(url, headers=headers, json=data)

    if response.status_code != 200:
        st.error(f"API Error: {response.text}")
        return None

    return response.json()


# -------------------------
# Display Chat History
# -------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# -------------------------
# User Input
# -------------------------
user_input = st.chat_input("Ask about time anywhere in the world...")

if user_input:

    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("user"):
        st.markdown(user_input)

    system_prompt = """
You are a professional AI World Clock assistant.

Rules:
- If user asks about time, call get_current_time tool.
- If location is mentioned, extract correct IANA timezone.
- If user says only "current time", default to Asia/Karachi.
- NEVER guess time yourself.
- Use tool result to generate final answer.
- Respond beautifully with emojis.
"""

    messages = [
        {"role": "system", "content": system_prompt},
    ] + st.session_state.messages

    # -------------------------
    # STEP 1 — Let LLM decide tool call
    # -------------------------
    llm_response = call_llm(messages, tools=tools)

    if llm_response is None:
        st.stop()

    assistant_message = llm_response["choices"][0]["message"]

    # -------------------------
    # STEP 2 — If tool call requested
    # -------------------------
    if "tool_calls" in assistant_message:

        tool_call = assistant_message["tool_calls"][0]

        function_name = tool_call["function"]["name"]
        arguments = json.loads(tool_call["function"]["arguments"])

        # Default to Pakistan if no timezone provided
        timezone = arguments.get("timezone", "Asia/Karachi")

        tool_result = get_current_time(timezone)

        # Append tool call message
        messages.append(assistant_message)

        # Append tool result
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "content": json.dumps(tool_result)
        })

        # -------------------------
        # STEP 3 — Final LLM Response
        # -------------------------
        final_response = call_llm(messages)

        if final_response is None:
            st.stop()

        final_text = final_response["choices"][0]["message"]["content"]

        st.session_state.messages.append(
            {"role": "assistant", "content": final_text}
        )

        with st.chat_message("assistant"):
            st.markdown(final_text)

    else:
        # If no tool needed
        final_text = assistant_message.get("content", "")

        st.session_state.messages.append(
            {"role": "assistant", "content": final_text}
        )

        with st.chat_message("assistant"):
            st.markdown(final_text)
