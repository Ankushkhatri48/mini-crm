import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from database.db import get_session
from database.models import Campaign, CommunicationLog


def show():
    st.title("📊 Analytics")

    db = get_session()
    campaigns = db.query(Campaign).all()

    if not campaigns:
        st.info("No campaign data yet. Launch a campaign first.")
        db.close()
        return

    all_logs = db.query(CommunicationLog).all()
    db.close()

    if not all_logs:
        st.info("No communication logs found.")
        return

    # --- Overall Metrics ---
    total = len(all_logs)
    status_counts = {"Delivered": 0, "Opened": 0, "Clicked": 0, "Failed": 0}
    for log in all_logs:
        status_counts[log.status] = status_counts.get(log.status, 0) + 1

    delivered = status_counts["Delivered"]
    opened = status_counts["Opened"]
    clicked = status_counts["Clicked"]
    failed = status_counts["Failed"]

    successful = total - failed

    st.subheader("Overall Performance")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Sent", total)
    c2.metric("Delivered", delivered)
    c3.metric("Opened", opened)
    c4.metric("Clicked", clicked)
    c5.metric("Failed", failed)

    delivery_rate = round((successful / total) * 100, 1) if total else 0
    open_rate = round((opened / total) * 100, 1) if total else 0
    click_rate = round((clicked / total) * 100, 1) if total else 0

    r1, r2, r3 = st.columns(3)
    r1.metric("Delivery Rate", f"{delivery_rate}%")
    r2.metric("Open Rate", f"{open_rate}%")
    r3.metric("Click Rate", f"{click_rate}%")

    st.divider()

    # --- Overall Funnel Chart ---
    col1, col2 = st.columns(2)

    with col1:
        fig_pie = px.pie(
            values=list(status_counts.values()),
            names=list(status_counts.keys()),
            title="Message Status Distribution",
            color_discrete_map={
                "Delivered": "#3B82F6",
                "Opened": "#10B981",
                "Clicked": "#F59E0B",
                "Failed": "#EF4444"
            },
            hole=0.4
        )
        fig_pie.update_layout(margin=dict(t=40, b=0, l=0, r=0))
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        funnel_fig = go.Figure(go.Funnel(
            y=["Sent", "Delivered", "Opened", "Clicked"],
            x=[total, delivered + opened + clicked, opened + clicked, clicked],
            textinfo="value+percent initial",
            marker={"color": ["#6366F1", "#3B82F6", "#10B981", "#F59E0B"]}
        ))
        funnel_fig.update_layout(title="Engagement Funnel", margin=dict(t=40, b=0, l=0, r=0))
        st.plotly_chart(funnel_fig, use_container_width=True)

    st.divider()

    # --- Per-Campaign Breakdown ---
    st.subheader("Campaign-wise Statistics")

    campaign_data = []
    for camp in campaigns:
        camp_logs = [l for l in all_logs if l.campaign_id == camp.id]
        if not camp_logs:
            continue
        c_total = len(camp_logs)
        c_delivered = sum(1 for l in camp_logs if l.status == "Delivered")
        c_opened = sum(1 for l in camp_logs if l.status == "Opened")
        c_clicked = sum(1 for l in camp_logs if l.status == "Clicked")
        c_failed = sum(1 for l in camp_logs if l.status == "Failed")
        campaign_data.append({
            "Campaign": camp.name,
            "Channel": camp.channel,
            "Total": c_total,
            "Delivered": c_delivered,
            "Opened": c_opened,
            "Clicked": c_clicked,
            "Failed": c_failed,
            "Open Rate %": round((c_opened / c_total) * 100, 1) if c_total else 0,
            "Click Rate %": round((c_clicked / c_total) * 100, 1) if c_total else 0,
        })

    if campaign_data:
        df = pd.DataFrame(campaign_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        fig_bar = px.bar(
            df, x="Campaign", y=["Delivered", "Opened", "Clicked", "Failed"],
            title="Campaign Results Breakdown",
            barmode="stack",
            color_discrete_map={
                "Delivered": "#3B82F6",
                "Opened": "#10B981",
                "Clicked": "#F59E0B",
                "Failed": "#EF4444"
            }
        )
        fig_bar.update_layout(xaxis_tickangle=-20)
        st.plotly_chart(fig_bar, use_container_width=True)

        fig_line = px.line(
            df, x="Campaign", y=["Open Rate %", "Click Rate %"],
            title="Open Rate vs Click Rate by Campaign",
            markers=True
        )
        st.plotly_chart(fig_line, use_container_width=True)
