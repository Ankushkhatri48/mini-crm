import streamlit as st

st.set_page_config(
    page_title="Mini CRM",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

from database.db import init_db, get_session
from database.models import Customer, Campaign, CommunicationLog
from auth.auth import require_auth, logout, get_current_user, is_admin
from auth.audit import get_recent_logs
import pandas as pd

# Initialize DB tables (including audit_logs)
init_db()

# --- Auth gate: stop here if not logged in ---
if not require_auth():
    st.stop()

# Import pages only after auth passes
from pages import customers, segments, campaigns, analytics


def get_dashboard_stats():
    db = get_session()
    try:
        total_customers = db.query(Customer).count()
        total_campaigns = db.query(Campaign).count()
        all_logs = db.query(CommunicationLog).all()
        total_sent = len(all_logs)
        delivered = sum(1 for l in all_logs if l.status in ("Delivered", "Opened", "Clicked"))
        opened = sum(1 for l in all_logs if l.status in ("Opened", "Clicked"))
        clicked = sum(1 for l in all_logs if l.status == "Clicked")
        return {
            "customers": total_customers,
            "campaigns": total_campaigns,
            "sent": total_sent,
            "delivery_rate": round((delivered / total_sent) * 100, 1) if total_sent else 0,
            "open_rate": round((opened / total_sent) * 100, 1) if total_sent else 0,
            "click_rate": round((clicked / total_sent) * 100, 1) if total_sent else 0,
        }
    finally:
        db.close()


def show_dashboard():
    st.title("📊 Dashboard")
    st.caption("Overview of your CRM activity")

    stats = get_dashboard_stats()

    col1, col2, col3 = st.columns(3)
    col1.metric("👥 Total Customers", stats["customers"])
    col2.metric("📣 Total Campaigns", stats["campaigns"])
    col3.metric("📨 Total Messages Sent", stats["sent"])

    col4, col5, col6 = st.columns(3)
    col4.metric("✅ Delivery Rate", f"{stats['delivery_rate']}%")
    col5.metric("👁️ Open Rate", f"{stats['open_rate']}%")
    col6.metric("🖱️ Click Rate", f"{stats['click_rate']}%")

    st.divider()

    db = get_session()
    recent = db.query(Campaign).order_by(Campaign.created_at.desc()).limit(5).all()
    db.close()

    if recent:
        st.subheader("Recent Campaigns")
        for camp in recent:
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"**{camp.name}** · {camp.channel} · Segment: *{camp.segment.name}*")
                with col2:
                    st.caption(camp.created_at.strftime("%d %b %Y"))
    else:
        st.info("No campaigns yet. Go to Campaigns to launch your first one.")


def show_audit_log():
    st.title("🔒 Audit Log")
    st.caption("All user actions are recorded here. Visible to admins only.")

    logs = get_recent_logs(limit=100)
    if not logs:
        st.info("No audit logs yet.")
        return

    data = [
        {
            "Time": l.timestamp.strftime("%d %b %Y, %H:%M:%S"),
            "User": l.username,
            "Action": l.action,
            "Detail": l.detail,
        }
        for l in logs
    ]
    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)


# --- Sidebar ---
with st.sidebar:
    st.markdown("## 📊 Mini CRM")
    st.divider()

    user = get_current_user()
    st.caption(f"👤 {user['username']} · {user['role'].title()}")
    st.divider()

    nav_options = ["Dashboard", "Customers", "Segments", "Campaigns", "Analytics"]
    if is_admin():
        nav_options.append("Audit Log")

    page = st.radio("Navigate", nav_options, label_visibility="collapsed")

    st.divider()
    if st.button("🚪 Logout", use_container_width=True):
        logout()
        st.rerun()

    st.caption("Powered by Gemini AI")

# --- Route ---
if page == "Dashboard":
    show_dashboard()
elif page == "Customers":
    customers.show()
elif page == "Segments":
    segments.show()
elif page == "Campaigns":
    campaigns.show()
elif page == "Analytics":
    analytics.show()
elif page == "Audit Log":
    if is_admin():
        show_audit_log()
    else:
        st.error("Access denied.")
