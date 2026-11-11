import streamlit as st
import json
from pathlib import Path

# Import các hàm cốt lõi từ bài Lab
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from chat import run_model_tool_loop, trim_history

# Khởi tạo môi trường
ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)

# Cấu hình giao diện Streamlit
st.set_page_config(page_title="Research & Football Agent", page_icon="⚽", layout="wide")
st.title("⚽ Football & Research Agent")
st.caption("Trợ lý AI tích hợp Tool Calling (Web Search, Đọc báo, Phân tích Bóng đá, X/Twitter)")

# Load system prompt và tools (Cache lại để không phải đọc file nhiều lần)
@st.cache_data
def load_artifacts():
    system_prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
    tools_yaml = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
    openai_tools = to_openai_tools(tools_yaml)
    return system_prompt, openai_tools

system_prompt, openai_tools = load_artifacts()

# --- SIDEBAR (Cấu hình) ---
with st.sidebar:
    st.header("⚙️ Cấu hình Hệ thống")
    provider_name = st.selectbox("Provider", ["openrouter", "openai", "gemini", "anthropic", "ollama"])
    model_name = st.text_input("Model Override (Để trống dùng mặc định)", value="")
    history_window = st.number_input("Lịch sử ngữ cảnh (History window)", min_value=1, max_value=20, value=5)
    max_tool_rounds = st.number_input("Vòng lặp tool tối đa (Max tool rounds)", min_value=1, max_value=10, value=4)
    
    st.divider()
    if st.button("🗑️ Xóa lịch sử trò chuyện", use_container_width=True):
        st.session_state.history = []
        st.session_state.display = []
        st.rerun()

# --- QUẢN LÝ TRẠNG THÁI (SESSION STATE) ---
# history: Dùng để đẩy vào context cho LLM (chỉ lưu text user/assistant)
if "history" not in st.session_state:
    st.session_state.history = []  

# display: Dùng để render UI (lưu text và cả tool_events để hiển thị expander)
if "display" not in st.session_state:
    st.session_state.display = []  

# --- RENDER LỊCH SỬ TRUY CẬP (UI) ---
for msg in st.session_state.display:
    if msg["role"] == "tool":
        # Hiển thị tool call dạng Expander (có thể bấm mở ra xem JSON)
        with st.expander(msg["content"]):
            st.json(msg["details"])
    else:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# --- XỬ LÝ KHUNG CHAT (USER INPUT) ---
if user_text := st.chat_input("Nhập yêu cầu của bạn (VD: Tìm tin tức Arsenal, Tóm tắt link này...)"):
    # Hiển thị câu hỏi của User
    st.session_state.display.append({"role": "user", "content": user_text, "details": None})
    with st.chat_message("user"):
        st.markdown(user_text)

    # Chuẩn bị Context gửi cho Model
    provider = make_provider(provider_name)
    selected_model = model_name if model_name.strip() else getattr(provider, "default_model", None)
    
    # Gom messages: System Prompt + History (đã trim) + Câu hỏi hiện tại
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(trim_history(st.session_state.history, history_window))
    messages.append({"role": "user", "content": user_text})

    # Khung trả lời của Assistant
    with st.chat_message("assistant"):
        st_placeholder = st.empty()
        
        with st.spinner("Agent đang suy nghĩ và chạy công cụ (Tool calling)..."):
            try:
                # Gọi vòng lặp Agent từ file chat.py của Lab
                result = run_model_tool_loop(
                    provider=provider,
                    messages=messages,
                    tools=openai_tools,
                    model=selected_model,
                    max_tool_rounds=max_tool_rounds
                )
                
                # Render các Tool đã được Agent gọi
                if result.get("tool_events"):
                    for event in result["tool_events"]:
                        tool_name = event.get("tool", "unknown")
                        tool_title = f"🔧 Agent đã sử dụng công cụ: `{tool_name}`"
                        st.session_state.display.append({
                            "role": "tool",
                            "content": tool_title,
                            "details": event
                        })
                        with st.expander(tool_title):
                            st.json(event)

                # Render câu trả lời cuối cùng
                assistant_text = result.get("assistant_text") or ""
                st_placeholder.markdown(assistant_text)
                
                # Lưu vào State
                st.session_state.history.append({"role": "user", "content": user_text})
                st.session_state.history.append({"role": "assistant", "content": assistant_text})
                st.session_state.display.append({"role": "assistant", "content": assistant_text, "details": None})

            except Exception as exc:
                error_msg = f"**Lỗi hệ thống (Provider Error):** {type(exc).__name__}: {str(exc)}"
                st.error(error_msg)
                st.session_state.display.append({"role": "assistant", "content": error_msg, "details": None})