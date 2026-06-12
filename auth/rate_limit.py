import time
import streamlit as st

# Max AI calls per user per session window
AI_CALL_LIMIT = 20
AI_WINDOW_SECONDS = 3600  # 1 hour


def check_ai_rate_limit() -> tuple[bool, str]:
    """
    Returns (allowed: bool, message: str).
    Tracks calls in session state — resets after the window expires.
    """
    now = time.time()
    window_start = st.session_state.get("ai_window_start", now)
    call_count = st.session_state.get("ai_call_count", 0)

    # Reset window if expired
    if now - window_start > AI_WINDOW_SECONDS:
        st.session_state["ai_window_start"] = now
        st.session_state["ai_call_count"] = 0
        call_count = 0

    if call_count >= AI_CALL_LIMIT:
        remaining = int(AI_WINDOW_SECONDS - (now - window_start))
        minutes = remaining // 60
        return False, f"AI call limit reached ({AI_CALL_LIMIT}/hour). Resets in {minutes} minute(s)."

    st.session_state["ai_call_count"] = call_count + 1
    return True, ""
