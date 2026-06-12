import streamlit as st
import json
from database.db import get_session
from database.models import Segment, Customer
from ai.gemini import generate_segment_filters
from auth.validators import validate_ai_prompt, sanitize_ai_filters, MAX_SEGMENT_NAME_LEN
from auth.audit import log_action
from auth.rate_limit import check_ai_rate_limit
from auth.auth import is_admin


def count_matching_customers(rules: dict) -> int:
    db = get_session()
    try:
        query = db.query(Customer)
        if "min_spend" in rules:
            query = query.filter(Customer.total_spend >= rules["min_spend"])
        if "max_spend" in rules:
            query = query.filter(Customer.total_spend <= rules["max_spend"])
        if "min_orders" in rules:
            query = query.filter(Customer.total_orders >= rules["min_orders"])
        if "max_orders" in rules:
            query = query.filter(Customer.total_orders <= rules["max_orders"])
        if "city" in rules:
            query = query.filter(Customer.city.ilike(rules["city"]))
        return query.count()
    finally:
        db.close()


def show():
    st.title("🎯 Audience Segments")

    db = get_session()

    # --- AI Segment Generator ---
    with st.expander("🤖 AI Segment Generator", expanded=False):
        ai_input = st.text_area(
            "Describe your audience in plain English",
            placeholder="e.g. Customers who spent more than 5000 and placed at least 3 orders",
            max_chars=500,
        )
        if st.button("Generate Filters with AI", type="primary"):
            ok, msg = validate_ai_prompt(ai_input)
            if not ok:
                st.warning(msg)
            else:
                allowed, rate_msg = check_ai_rate_limit()
                if not allowed:
                    st.error(rate_msg)
                else:
                    with st.spinner("Asking Gemini..."):
                        raw_filters = generate_segment_filters(ai_input)

                    if "error" in raw_filters:
                        st.error(f"AI error: {raw_filters['error']}")
                    else:
                        valid, err, clean_filters = sanitize_ai_filters(raw_filters)
                        if not valid:
                            st.error(f"Filter validation failed: {err}")
                        else:
                            st.session_state["ai_filters"] = clean_filters
                            st.success("Filters generated and validated. Review below.")

        if "ai_filters" in st.session_state:
            filters = st.session_state["ai_filters"]
            st.json(filters)
            match_count = count_matching_customers(filters)
            st.metric("Matching Customers", match_count)

            seg_name = st.text_input("Segment Name", key="ai_seg_name", max_chars=MAX_SEGMENT_NAME_LEN)
            if st.button("Save as Segment"):
                if not seg_name.strip():
                    st.warning("Enter a segment name.")
                else:
                    seg = Segment(name=seg_name.strip(), rules=json.dumps(filters))
                    db.add(seg)
                    db.commit()
                    log_action("CREATE_SEGMENT", f"AI-generated segment: {seg_name.strip()}")
                    st.success(f"Segment '{seg_name.strip()}' saved.")
                    del st.session_state["ai_filters"]
                    st.rerun()

    st.divider()

    # --- Manual Segment Builder ---
    with st.expander("➕ Create Segment Manually", expanded=False):
        with st.form("manual_segment_form"):
            seg_name = st.text_input("Segment Name*", max_chars=MAX_SEGMENT_NAME_LEN)
            col1, col2 = st.columns(2)
            with col1:
                min_spend = st.number_input("Min Spend (₹)", value=0.0, min_value=0.0, max_value=10_000_000.0, step=100.0)
                max_spend = st.number_input("Max Spend (₹)", value=0.0, min_value=0.0, max_value=10_000_000.0, step=100.0, help="Leave 0 to skip")
                min_orders = st.number_input("Min Orders", value=0, min_value=0, max_value=100000, step=1)
            with col2:
                max_orders = st.number_input("Max Orders", value=0, min_value=0, max_value=100000, step=1, help="Leave 0 to skip")
                city = st.text_input("City (exact match)", placeholder="Leave blank to skip", max_chars=100)

            submitted = st.form_submit_button("Create Segment", type="primary")
            if submitted:
                if not seg_name.strip():
                    st.error("Segment name is required.")
                else:
                    rules = {}
                    if min_spend > 0: rules["min_spend"] = float(min_spend)
                    if max_spend > 0: rules["max_spend"] = float(max_spend)
                    if min_orders > 0: rules["min_orders"] = int(min_orders)
                    if max_orders > 0: rules["max_orders"] = int(max_orders)
                    if city.strip(): rules["city"] = city.strip()

                    seg = Segment(name=seg_name.strip(), rules=json.dumps(rules))
                    db.add(seg)
                    db.commit()
                    log_action("CREATE_SEGMENT", f"Manual segment: {seg_name.strip()}")
                    st.success(f"Segment '{seg_name.strip()}' created.")
                    st.rerun()

    db.close()
    st.divider()

    # --- Existing Segments ---
    st.subheader("📋 Saved Segments")
    db2 = get_session()
    segments = db2.query(Segment).all()
    db2.close()

    if not segments:
        st.info("No segments yet.")
        return

    for seg in segments:
        rules = json.loads(seg.rules)
        match_count = count_matching_customers(rules)
        with st.container(border=True):
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{seg.name}**")
                st.caption(f"Rules: {rules}")
            with col2:
                st.metric("Matching", match_count)
            with col3:
                if is_admin():
                    if st.button("🗑️", key=f"del_seg_{seg.id}", help="Delete segment"):
                        db3 = get_session()
                        db3.query(Segment).filter(Segment.id == seg.id).delete()
                        db3.commit()
                        db3.close()
                        log_action("DELETE_SEGMENT", f"Deleted segment ID {seg.id}: {seg.name}")
                        st.rerun()
