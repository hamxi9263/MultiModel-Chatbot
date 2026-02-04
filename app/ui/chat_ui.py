import streamlit as st
import uuid
import base64
from langchain_core.messages import HumanMessage
from app.tools.time_tool import get_current_time


def image_to_base64(image_file):
    return base64.b64encode(image_file.read()).decode("utf-8")


def render_chat_ui(chat_chain, llm):
    st.set_page_config(page_title="🤰 Pregnancy Support Chatbot")

    st.title("🤰 Pregnancy Support Chatbot")
    st.write("Safe, calm pregnancy guidance")

    # ---------------------------
    # Session setup
    # ---------------------------
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # ---------------------------
    # Display chat history
    # ---------------------------
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            if isinstance(msg.get("content"), dict):
                st.json(msg["content"])
            elif "content" in msg:
                st.markdown(msg["content"])
            if "image" in msg:
                st.image(msg["image"], caption="Uploaded Image")

    # ---------------------------
    # Inputs
    # ---------------------------
    uploaded_image = st.file_uploader(
        "Upload an image (optional)",
        type=["png", "jpg", "jpeg"]
    )

    user_input = st.chat_input("Ask your question")

    # ---------------------------
    # Handle interaction
    # ---------------------------
    if user_input or uploaded_image:

        # ---- User message
        if user_input:
            st.session_state.messages.append(
                {"role": "user", "content": user_input}
            )
            with st.chat_message("user"):
                st.markdown(user_input)

        # ---------------------------
        # 🔹 IMAGE FLOW (no tools, no memory)
        # ---------------------------
        if uploaded_image:
            image_base64 = image_to_base64(uploaded_image)

            multimodal_message = HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": user_input or "Please analyze this image."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            )

            response = llm.invoke([multimodal_message])

            with st.chat_message("assistant"):
                st.markdown(response.content)

            st.session_state.messages.append(
                {"role": "assistant", "content": response.content}
            )

            return

        # ---------------------------
        # 🔹 TEXT FLOW (WITH TOOLS)
        # ---------------------------
        response = chat_chain.invoke(
            {"input": user_input},
            config={"configurable": {"session_id": st.session_state.session_id}}
        )

        # ---------------------------
        # 🔹 TOOL CALL HANDLING
        # ---------------------------
        if response.tool_calls:
            tool_call = response.tool_calls[0]

            if tool_call["name"] == "get_current_time":
                tool_result = get_current_time.invoke(
                    tool_call.get("args", {})
                )

                with st.chat_message("assistant"):
                    st.json(tool_result)

                st.session_state.messages.append(
                    {"role": "assistant", "content": tool_result}
                )
                return

        # ---------------------------
        # 🔹 Normal text response
        # ---------------------------
        with st.chat_message("assistant"):
            st.markdown(response.content)

        st.session_state.messages.append(
            {"role": "assistant", "content": response.content}
        )
