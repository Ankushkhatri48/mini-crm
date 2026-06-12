# Mini CRM — AI-Native Marketing CRM (Secured)

Production-ready CRM for marketing teams. Built with Python, Streamlit, MySQL, SQLAlchemy, and Gemini AI.

---

## Security Features

| Layer | What's implemented |
|---|---|
| Authentication | Username/password login with PBKDF2 password hashing |
| Rate limiting | 5 failed login attempts → 5-minute lockout |
| Session timeout | Auto-logout after 60 minutes of inactivity |
| Role-based access | `admin` can edit/delete/launch; `viewer` is read-only |
| Input validation | Email regex, field length limits, numeric range checks |
| AI filter sanitization | Gemini output validated against allowlist before DB use |
| AI rate limiting | 20 AI calls per user per hour |
| Audit log | Every action recorded with user + timestamp |
| Secret management | Credentials via env vars only, never hardcoded |
| `.gitignore` | `.env` and `secrets.toml` excluded from version control |

---

## Local Setup

### 1. Prerequisites
- Python 3.10+
- MySQL running locally
- Gemini API key from [Google AI Studio](https://aistudio.google.com/)

### 2. Create MySQL database
```sql
CREATE DATABASE mini_crm;
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
cp .env.example .env
# Edit .env — set DATABASE_URL, GEMINI_API_KEY, and AUTH_PLAIN_USERS
```

### 5. Run the app
```bash
streamlit run app.py
```

All database tables (including audit_logs) are created automatically on first run.

---

## User Roles

| Role | Can do |
|---|---|
| `admin` | Everything: add/edit/delete customers, create segments, launch campaigns, view audit log |
| `viewer` | View customers, segments, campaigns, analytics. Can use AI tools but cannot modify data |

Configure users in `.env`:
```
AUTH_PLAIN_USERS=admin:yourpassword:admin,analyst:theirpassword:viewer
```

---

## Streamlit Cloud Deployment

1. Push to GitHub (`.env` and `secrets.toml` are gitignored)
2. Connect repo on [Streamlit Cloud](https://streamlit.io/cloud)
3. Add secrets in the Streamlit Cloud dashboard:
```
DATABASE_URL = "mysql+pymysql://user:pass@host:3306/mini_crm"
GEMINI_API_KEY = "your_key"
AUTH_PLAIN_USERS = "admin:securepassword:admin,viewer:viewerpass:viewer"
```
Use a cloud MySQL provider: PlanetScale, Railway, or Aiven.

---

## Project Structure

```
mini_crm/
├── app.py                      # Entry point, dashboard, routing, auth gate
├── auth/
│   ├── auth.py                 # Login, session management, roles, rate limiting
│   ├── validators.py           # Input validation + AI filter sanitization
│   ├── audit.py                # Audit log writer/reader
│   └── rate_limit.py           # AI API call rate limiter
├── pages/
│   ├── customers.py            # Customer CRUD (edit/delete: admin only)
│   ├── segments.py             # Segment builder + AI generator
│   ├── campaigns.py            # Campaign launcher (admin only) + AI messages
│   └── analytics.py            # Plotly analytics
├── database/
│   ├── db.py                   # SQLAlchemy engine + session
│   └── models.py               # ORM models incl. AuditLog
├── ai/
│   └── gemini.py               # Gemini API calls
├── services/
│   └── simulator.py            # Fake messaging engine
├── .gitignore                  # Excludes .env, secrets.toml
├── .env.example                # Template — copy to .env
├── .streamlit/secrets.toml.example
├── requirements.txt
└── README.md
```

---

## Simulated Message Statuses

| Status | Probability |
|---|---|
| Opened | 35% |
| Delivered | 30% |
| Clicked | 25% |
| Failed | 10% |
