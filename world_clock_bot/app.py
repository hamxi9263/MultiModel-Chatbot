import streamlit as st
import os
import requests
import json
from tools import get_current_time

OPENROUTER_API_KEY = "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"
MODEL = "openai/gpt-4o-mini"

st.set_page_config(page_title="🌍 AI World Clock Agent")
st.title("🌍 AI World Clock Agent")

if "messages" not in st.session_state:
    st.session_state.messages = []

# -------------------------
# Tool Schema
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
                        "description": "IANA timezone like Asia/Karachi, Europe/London"
                    }
                },
                "required": ["timezone"]
            }
        }
    }
]

# -------------------------
# Streaming LLM Call
# -------------------------
def stream_llm(messages, tools=None):

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.4,
        "stream": True
    }

    if tools:
        data["tools"] = tools
        data["tool_choice"] = "auto"

    response = requests.post(url, headers=headers, json=data, stream=True)

    for line in response.iter_lines():
        if line:
            line = line.decode("utf-8")
            if line.startswith("data: "):
                line = line.replace("data: ", "")
                if line == "[DONE]":
                    break
                yield json.loads(line)


# -------------------------
# Show chat history
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
- NEVER guess time.
- Use tool result to generate final answer.
- Respond beautifully with emojis.
"""

    messages = [
        {"role": "system", "content": system_prompt},
    ] + st.session_state.messages

    # -------------------------
    # STEP 1 — Tool decision (non-stream, quick)
    # -------------------------
    decision_response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL,
            "messages": messages,
            "tools": tools,
            "tool_choice": "auto",
            "temperature": 0.2
        }
    ).json()

    assistant_message = decision_response["choices"][0]["message"]

    # -------------------------
    # If Tool Called
    # -------------------------
    if "tool_calls" in assistant_message:

        tool_call = assistant_message["tool_calls"][0]
        arguments = json.loads(tool_call["function"]["arguments"])
        timezone = arguments.get("timezone", "Asia/Karachi")

        tool_result = get_current_time(timezone)

        messages.append(assistant_message)

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "content": json.dumps(tool_result)
        })

        # -------------------------
        # STEP 2 — Stream final response
        # -------------------------
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""

            for chunk in stream_llm(messages):
                delta = chunk["choices"][0]["delta"]

                if "content" in delta:
                    full_response += delta["content"]
                    placeholder.markdown(full_response + "▌")

            placeholder.markdown(full_response)

        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )

    else:
        # If no tool used → stream directly
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_response = ""

            for chunk in stream_llm(messages):
                delta = chunk["choices"][0]["delta"]

                if "content" in delta:
                    full_response += delta["content"]
                    placeholder.markdown(full_response + "▌")

            placeholder.markdown(full_response)

        st.session_state.messages.append(
            {"role": "assistant", "content": full_response}
        )
