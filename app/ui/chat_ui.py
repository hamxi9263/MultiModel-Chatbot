import streamlit as st
import uuid
import base64
import json
from langchain_core.messages import HumanMessage, AIMessage
from app.tools.time_tool import get_current_time


def image_to_base64(image_bytes: bytes) -> str:
    """Convert raw image bytes to base64 string."""
    return base64.b64encode(image_bytes).decode("utf-8")


def _build_history_from_session(last_n_turns: int = 5):
    """
    Convert the last N (user, assistant) turns from Streamlit session state
    into LangChain chat messages, to be passed as `history` to the chain.
    """
    if "messages" not in st.session_state:
        return []

    # Each "turn" is typically (user, assistant), so we take 2 * N messages.
    raw_history = st.session_state.messages[-2 * last_n_turns :]

    history = []
    for msg in raw_history:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "user":
            # If this user message included an image, keep it as multimodal
            image_bytes = msg.get("image")
            if image_bytes is not None:
                image_b64 = image_to_base64(image_bytes)
                text_part = str(content) if content else "Uploaded an image."
                history.append(
                    HumanMessage(
                        content=[
                            {"type": "text", "text": text_part},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}"
                                },
                            },
                        ]
                    )
                )
            else:
                # Pure text user message
                history.append(HumanMessage(content=str(content)))
        elif role == "assistant":
            # Tool responses may be dicts; convert them to a readable string
            if isinstance(content, dict):
                try:
                    content_str = json.dumps(content)
                except Exception:
                    content_str = str(content)
                history.append(AIMessage(content=content_str))
            else:
                history.append(AIMessage(content=str(content)))

    return history


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

    # UI state for image upload "plus" behavior
    if "show_image_uploader" not in st.session_state:
        st.session_state.show_image_uploader = False

    # Container for chat history (will be rendered after handling input)
    history_container = st.container()

    # ---------------------------
    # Inputs (GPT-like row: large [+] button + chat input)
    # ---------------------------
    input_cols = st.columns([0.08, 0.95])

    with input_cols[0]:
        if st.button("➕", help="Add an image", key="plus_button", use_container_width=True):
            st.session_state.show_image_uploader = not st.session_state.show_image_uploader

    with input_cols[1]:
        user_input = st.chat_input("Ask your question")

    uploaded_image = None
    if st.session_state.show_image_uploader:
        with st.expander("Add an image", expanded=True):
            uploaded_image = st.file_uploader(
                "Upload an image", type=["png", "jpg", "jpeg"], key="image_uploader"
            )

    # ---------------------------
    # Handle interaction: update session_state (history rendered afterwards)
    # ---------------------------
    if user_input or uploaded_image:

        # ---- User message (text + optional image, recorded once)
        user_message: dict = {"role": "user"}
        image_bytes = None

        if uploaded_image is not None:
            image_bytes = uploaded_image.getvalue()
            user_message["image"] = image_bytes

        if user_input:
            user_message["content"] = user_input
        else:
            user_message["content"] = "Uploaded an image."

        st.session_state.messages.append(user_message)

        # ---------------------------
        # 🔹 IMAGE FLOW (with session history)
        # ---------------------------
        if uploaded_image:
            # Close uploader after using the image
            st.session_state.show_image_uploader = False

            image_bytes = image_bytes or uploaded_image.getvalue()
            image_base64 = image_to_base64(image_bytes)

            multimodal_message = HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": user_input or "Please analyze this image.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        },
                    },
                ]
            )

            # Include the last N turns of history so image questions
            # also benefit from prior context in this session.
            history = _build_history_from_session(last_n_turns=5)
            messages = history + [multimodal_message]

            with st.spinner("Analyzing image..."):
                response = llm.invoke(messages)

            st.session_state.messages.append(
                {"role": "assistant", "content": response.content}
            )

        else:
            # ---------------------------
            # 🔹 TEXT FLOW (WITH TOOLS + SESSION MEMORY)
            # ---------------------------
            history = _build_history_from_session(last_n_turns=5)

            with st.spinner("Thinking..."):
                response = chat_chain.invoke(
                    {
                        "input": user_input,
                        "history": history,
                    }
                )

            # ---------------------------
            # 🔹 TOOL CALL HANDLING (LLM-driven + fallback)
            # ---------------------------
            handled_tool = False

            # Primary: let the LLM decide via tool calling
            if getattr(response, "tool_calls", None):
                tool_call = response.tool_calls[0]

                if tool_call["name"] == "get_current_time":
                    tool_result = get_current_time.invoke(tool_call.get("args", {}))

                    # Format as a natural chat sentence
                    timezone = tool_result.get("timezone", "the specified timezone")
                    time_str = tool_result.get("time", "")
                    time_text = f"The current time in {timezone} is {time_str}."

                    st.session_state.messages.append(
                        {"role": "assistant", "content": time_text}
                    )
                    handled_tool = True

            # Fallback: if the user clearly asked for current time but
            # the model didn't trigger the tool, call it directly.
            if (
                not handled_tool
                and isinstance(user_input, str)
                and "time" in user_input.lower()
                and "current" in user_input.lower()
            ):
                tool_result = get_current_time.invoke({})

                timezone = tool_result.get("timezone", "the specified timezone")
                time_str = tool_result.get("time", "")
                time_text = f"The current time in {timezone} is {time_str}."

                st.session_state.messages.append(
                    {"role": "assistant", "content": time_text}
                )

                return

            if not handled_tool:
                # ---------------------------
                # 🔹 Normal text response
                # ---------------------------
                st.session_state.messages.append(
                    {"role": "assistant", "content": response.content}
                )

    # ---------------------------
    # Render full chat history above the input (chronological)
    # ---------------------------
    with history_container:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                if isinstance(msg.get("content"), dict):
                    st.json(msg["content"])
                elif "content" in msg:
                    st.markdown(msg["content"])
                if "image" in msg:
                    st.image(msg["image"], caption="Uploaded Image")

    # (No additional rendering here; history will be shown on next rerun
    # with the updated `st.session_state.messages`.)
