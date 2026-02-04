from dotenv import load_dotenv
load_dotenv()

import sys
sys.dont_write_bytecode = True

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.chains.chat_chain import get_chat_chain
from app.llm.gemini import get_llm
from app.ui.chat_ui import render_chat_ui

chat_chain = get_chat_chain()
llm = get_llm()
render_chat_ui(chat_chain, llm)

