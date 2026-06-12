import streamlit as st
import hashlib
import hmac
import os
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# --- Load credentials from env/secrets ---
def _get_secret(key: str) -> str:
    try:
        return st.secrets.get(key, os.getenv(key, ""))
    except Exception:
        return os.getenv(key, "")


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        200_000  # iterations
    ).hex()


def _verify_password(password: str, salt: str, stored_hash: str) -> bool:
    candidate = _hash_password(password, salt)
    return hmac.compare_digest(candidate, stored_hash)


def _get_users() -> dict:
    """
    Load users from environment variables.
    Format in .env:
      AUTH_USERS=admin:hashed_pw:salt:admin,viewer:hashed_pw:salt:viewer
    For simplicity in demo, supports plaintext via AUTH_PLAIN_USERS:
      AUTH_PLAIN_USERS=admin:adminpass:admin,viewer:viewerpass:viewer
    Production should always use hashed passwords.
    """
    users = {}

    plain_users = _get_secret("AUTH_PLAIN_USERS")
    if plain_users:
        for entry in plain_users.split(","):
            parts = entry.strip().split(":")
            if len(parts) == 3:
                username, password, role = parts
                salt = username + "_salt_v1"
                users[username.strip()] = {
                    "hash": _hash_password(password.strip(), salt),
                    "salt": salt,
                    "role": role.strip(),
                }

    return users


# --- Rate limiting (in-memory, per session) ---
MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 300  # 5 minutes


def _check_rate_limit() -> tuple[bool, int]:
    """Returns (is_locked_out, seconds_remaining)."""
    attempts = st.session_state.get("login_attempts", 0)
    lockout_until = st.session_state.get("lockout_until", 0)

    if lockout_until and time.time() < lockout_until:
        remaining = int(lockout_until - time.time())
        return True, remaining

    if lockout_until and time.time() >= lockout_until:
        st.session_state["login_attempts"] = 0
        st.session_state["lockout_until"] = 0

    return False, 0


def _record_failed_attempt():
    attempts = st.session_state.get("login_attempts", 0) + 1
    st.session_state["login_attempts"] = attempts
    if attempts >= MAX_ATTEMPTS:
        st.session_state["lockout_until"] = time.time() + LOCKOUT_SECONDS


def _reset_attempts():
    st.session_state["login_attempts"] = 0
    st.session_state["lockout_until"] = 0


# --- Session timeout ---
SESSION_TIMEOUT_MINUTES = 60


def _is_session_expired() -> bool:
    last_active = st.session_state.get("last_active")
    if not last_active:
        return False
    return (datetime.utcnow() - last_active) > timedelta(minutes=SESSION_TIMEOUT_MINUTES)


def _refresh_session():
    st.session_state["last_active"] = datetime.utcnow()


# --- Public API ---

def login_page():
    """Renders the login form. Returns True if authenticated."""
    st.markdown(
        """
        <style>
        .login-box { max-width: 400px; margin: 80px auto; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🔐 Mini CRM Login")
        st.divider()

        locked_out, remaining = _check_rate_limit()
        if locked_out:
            st.error(f"Too many failed attempts. Try again in {remaining} seconds.")
            return False

        with st.form("login_form"):
            username = st.text_input("Username", max_chars=50)
            password = st.text_input("Password", type="password", max_chars=100)
            submitted = st.form_submit_button("Login", type="primary", use_container_width=True)

        if submitted:
            if not username or not password:
                st.warning("Enter both username and password.")
                return False

            users = _get_users()
            user = users.get(username.strip())

            if user and _verify_password(password, user["salt"], user["hash"]):
                _reset_attempts()
                st.session_state["authenticated"] = True
                st.session_state["username"] = username.strip()
                st.session_state["role"] = user["role"]
                st.session_state["last_active"] = datetime.utcnow()
                st.rerun()
            else:
                _record_failed_attempt()
                attempts = st.session_state.get("login_attempts", 0)
                remaining_attempts = MAX_ATTEMPTS - attempts
                if remaining_attempts > 0:
                    st.error(f"Invalid credentials. {remaining_attempts} attempt(s) remaining.")
                else:
                    st.error("Too many failed attempts. Account locked for 5 minutes.")

    return False


def require_auth() -> bool:
    """
    Call at the top of app.py.
    Returns True if user is authenticated and session is valid.
    Shows login page otherwise.
    """
    if not st.session_state.get("authenticated"):
        login_page()
        return False

    if _is_session_expired():
        logout()
        st.warning("Session expired. Please log in again.")
        login_page()
        return False

    _refresh_session()
    return True


def logout():
    for key in ["authenticated", "username", "role", "last_active",
                "login_attempts", "lockout_until"]:
        st.session_state.pop(key, None)


def get_current_user() -> dict:
    return {
        "username": st.session_state.get("username", ""),
        "role": st.session_state.get("role", "viewer"),
    }


def is_admin() -> bool:
    return st.session_state.get("role") == "admin"


def require_admin():
    """Show error and stop if user is not admin."""
    if not is_admin():
        st.error("⛔ Admin access required for this action.")
        st.stop()
