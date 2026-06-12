import re

# --- Field length limits ---
MAX_NAME_LEN = 100
MAX_EMAIL_LEN = 150
MAX_PHONE_LEN = 20
MAX_CITY_LEN = 100
MAX_MESSAGE_LEN = 2000
MAX_SEGMENT_NAME_LEN = 100
MAX_CAMPAIGN_NAME_LEN = 150
MAX_AI_PROMPT_LEN = 500

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^[\d\s\+\-\(\)]{7,20}$")

# Allowed keys that Gemini can return as segment filters
ALLOWED_FILTER_KEYS = {"min_spend", "max_spend", "min_orders", "max_orders", "city"}
ALLOWED_FILTER_TYPES = {
    "min_spend": (int, float),
    "max_spend": (int, float),
    "min_orders": int,
    "max_orders": int,
    "city": str,
}


def validate_email(email: str) -> tuple[bool, str]:
    email = email.strip()
    if not email:
        return False, "Email is required."
    if len(email) > MAX_EMAIL_LEN:
        return False, f"Email must be under {MAX_EMAIL_LEN} characters."
    if not EMAIL_REGEX.match(email):
        return False, "Invalid email format."
    return True, ""


def validate_name(name: str, field: str = "Name") -> tuple[bool, str]:
    name = name.strip()
    if not name:
        return False, f"{field} is required."
    if len(name) > MAX_NAME_LEN:
        return False, f"{field} must be under {MAX_NAME_LEN} characters."
    return True, ""


def validate_phone(phone: str) -> tuple[bool, str]:
    if not phone:
        return True, ""  # optional field
    if len(phone) > MAX_PHONE_LEN:
        return False, f"Phone must be under {MAX_PHONE_LEN} characters."
    if not PHONE_REGEX.match(phone):
        return False, "Invalid phone format. Use digits, spaces, +, -, () only."
    return True, ""


def validate_city(city: str) -> tuple[bool, str]:
    if not city:
        return True, ""  # optional field
    if len(city) > MAX_CITY_LEN:
        return False, f"City must be under {MAX_CITY_LEN} characters."
    return True, ""


def validate_message(message: str) -> tuple[bool, str]:
    message = message.strip()
    if not message:
        return False, "Message is required."
    if len(message) > MAX_MESSAGE_LEN:
        return False, f"Message must be under {MAX_MESSAGE_LEN} characters."
    return True, ""


def validate_ai_prompt(prompt: str) -> tuple[bool, str]:
    prompt = prompt.strip()
    if not prompt:
        return False, "Prompt is required."
    if len(prompt) > MAX_AI_PROMPT_LEN:
        return False, f"Prompt must be under {MAX_AI_PROMPT_LEN} characters."
    return True, ""


def sanitize_ai_filters(raw_filters: dict) -> tuple[bool, str, dict]:
    """
    Strictly validates Gemini-returned filters.
    Only allows known keys with correct types and sane value ranges.
    Rejects anything unexpected.
    """
    if not isinstance(raw_filters, dict):
        return False, "AI returned invalid filter format.", {}

    clean = {}
    for key, value in raw_filters.items():
        if key not in ALLOWED_FILTER_KEYS:
            return False, f"AI returned an unexpected filter key: '{key}'. Rejected for safety.", {}

        expected_type = ALLOWED_FILTER_TYPES[key]
        if not isinstance(value, expected_type):
            return False, f"Filter '{key}' has wrong type. Expected {expected_type}, got {type(value).__name__}.", {}

        # Value range checks
        if key in ("min_spend", "max_spend") and (value < 0 or value > 10_000_000):
            return False, f"Filter '{key}' value {value} is out of realistic range.", {}
        if key in ("min_orders", "max_orders") and (value < 0 or value > 100_000):
            return False, f"Filter '{key}' value {value} is out of realistic range.", {}
        if key == "city" and (not value.strip() or len(value) > MAX_CITY_LEN):
            return False, "City filter value is invalid.", {}

        clean[key] = value.strip() if key == "city" else value

    if not clean:
        return False, "AI returned empty filters. Try a more specific description.", {}

    return True, "", clean
