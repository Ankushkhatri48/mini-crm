import streamlit as st
from database.db import get_session
from database.models import Campaign, Segment
from ai.gemini import generate_campaign_message
from auth.validators import validate_message, validate_ai_prompt, MAX_CAMPAIGN_NAME_LEN
from auth.audit import log_action
from auth.rate_limit import check_ai_rate_limit
from auth.auth import require_admin, is_admin
from services.simulator import simulate_campaign, get_segment_customers

CHANNELS = ["WhatsApp", "SMS", "Email", "RCS"]


def show():
    st.title("📣 Campaigns")

    db = get_session()
    segments = db.query(Segment).all()
    db.close()

    if not segments:
        st.warning("Create at least one segment before launching a campaign.")
        return

    # --- AI Message Generator ---
    with st.expander("🤖 AI Message Generator", expanded=False):
        ai_channel = st.selectbox("Channel for message", CHANNELS, key="ai_msg_channel")
        ai_prompt = st.text_area(
            "Describe the message you want",
            placeholder="e.g. Create a Diwali offer message for premium customers",
            max_chars=500,
        )
        if st.button("Generate Message", type="primary"):
            ok, msg = validate_ai_prompt(ai_prompt)
            if not ok:
                st.warning(msg)
            else:
                allowed, rate_msg = check_ai_rate_limit()
                if not allowed:
                    st.error(rate_msg)
                else:
                    with st.spinner("Generating with Gemini..."):
                        generated = generate_campaign_message(ai_prompt, ai_channel)
                    # Enforce message length limit on AI output too
                    if len(generated) > 2000:
                        generated = generated[:2000]
                    st.session_state["ai_message"] = generated

        if "ai_message" in st.session_state:
            st.text_area("Generated Message (editable)", value=st.session_state["ai_message"],
                         key="edited_ai_msg", height=120, max_chars=2000)
            if st.button("Use This Message"):
                st.session_state["prefill_message"] = st.session_state.get("edited_ai_msg", "")
                st.success("Message copied to campaign form below.")

    st.divider()

    # --- Create Campaign (admin only) ---
    with st.expander("➕ Create Campaign", expanded=True):
        if not is_admin():
            st.info("ℹ️ Only admins can launch campaigns.")
        else:
            with st.form("create_campaign_form"):
                name = st.text_input("Campaign Name*", max_chars=MAX_CAMPAIGN_NAME_LEN)
                channel = st.selectbox("Channel", CHANNELS)
                seg_map = {s.name: s for s in segments}
                seg_name = st.selectbox("Audience Segment", list(seg_map.keys()))
                prefill = st.session_state.get("prefill_message", "")
                message = st.text_area("Message*", value=prefill, height=120, max_chars=2000)

                submitted = st.form_submit_button("Launch Campaign 🚀", type="primary")
                if submitted:
                    errors = []
                    if not name.strip():
                        errors.append("Campaign name is required.")
                    ok, msg = validate_message(message)
                    if not ok:
                        errors.append(msg)

                    if errors:
                        for e in errors: st.error(e)
                    else:
                        seg = seg_map[seg_name]
                        audience = get_segment_customers(seg)
                        if not audience:
                            st.error("No customers match the selected segment.")
                        else:
                            db2 = get_session()
                            campaign = Campaign(
                                name=name.strip(), message=message.strip(),
                                channel=channel, segment_id=seg.id
                            )
                            db2.add(campaign)
                            db2.commit()
                            campaign_id = campaign.id
                            db2.close()

                            with st.spinner(f"Sending to {len(audience)} customers..."):
                                result = simulate_campaign(campaign_id)

                            if "error" in result:
                                st.error(result["error"])
                            else:
                                c = result["counts"]
                                log_action("LAUNCH_CAMPAIGN", f"Campaign '{name.strip()}' sent to {result['total']} customers via {channel}")
                                st.success(f"Campaign sent to {result['total']} customers!")
                                col1, col2, col3, col4 = st.columns(4)
                                col1.metric("✅ Delivered", c["Delivered"])
                                col2.metric("👁️ Opened", c["Opened"])
                                col3.metric("🖱️ Clicked", c["Clicked"])
                                col4.metric("❌ Failed", c["Failed"])

                            st.session_state.pop("prefill_message", None)
                            st.rerun()

    st.divider()

    # --- Campaign List ---
    st.subheader("📋 All Campaigns")
    db3 = get_session()
    campaigns = db3.query(Campaign).order_by(Campaign.created_at.desc()).all()
    db3.close()

    if not campaigns:
        st.info("No campaigns launched yet.")
        return

    from services.simulator import get_campaign_stats
    for camp in campaigns:
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{camp.name}**")
                st.caption(f"Segment: {camp.segment.name} · Channel: {camp.channel}")
                st.write(camp.message[:120] + ("..." if len(camp.message) > 120 else ""))
            with col2:
                st.caption(camp.created_at.strftime("%d %b %Y, %H:%M"))
            with col3:
                stats = get_campaign_stats(camp.id)
                st.metric("Total Sent", stats.get("Total", 0))
