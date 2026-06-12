import streamlit as st
import pandas as pd
from database.db import get_session
from database.models import Customer
from auth.validators import validate_name, validate_email, validate_phone, validate_city
from auth.audit import log_action
from auth.auth import require_admin, is_admin


def show():
    st.title("👥 Customers")

    db = get_session()

    # --- Add Customer ---
    with st.expander("➕ Add New Customer", expanded=False):
        with st.form("add_customer_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Name*", max_chars=100)
                email = st.text_input("Email*", max_chars=150)
                phone = st.text_input("Phone", max_chars=20)
            with col2:
                city = st.text_input("City", max_chars=100)
                total_orders = st.number_input("Total Orders", min_value=0, max_value=100000, step=1)
                total_spend = st.number_input("Total Spend (₹)", min_value=0.0, max_value=10_000_000.0, step=100.0)

            submitted = st.form_submit_button("Add Customer", type="primary")
            if submitted:
                errors = []
                ok, msg = validate_name(name)
                if not ok: errors.append(msg)
                ok, msg = validate_email(email)
                if not ok: errors.append(msg)
                ok, msg = validate_phone(phone)
                if not ok: errors.append(msg)
                ok, msg = validate_city(city)
                if not ok: errors.append(msg)

                if errors:
                    for e in errors:
                        st.error(e)
                else:
                    existing = db.query(Customer).filter(Customer.email == email.strip().lower()).first()
                    if existing:
                        st.error("A customer with this email already exists.")
                    else:
                        customer = Customer(
                            name=name.strip(), email=email.strip().lower(),
                            phone=phone.strip(), city=city.strip(),
                            total_orders=int(total_orders), total_spend=float(total_spend)
                        )
                        db.add(customer)
                        db.commit()
                        log_action("ADD_CUSTOMER", f"Added customer: {name.strip()} ({email.strip()})")
                        st.success(f"Customer '{name.strip()}' added.")
                        st.rerun()

    st.divider()

    # --- Customer List ---
    customers = db.query(Customer).all()
    db.close()

    if not customers:
        st.info("No customers yet. Add one above.")
        return

    search = st.text_input("🔍 Search by name, email or city", placeholder="Type to filter...", max_chars=100)
    data = [
        {
            "ID": c.id, "Name": c.name, "Email": c.email, "Phone": c.phone or "—",
            "City": c.city or "—", "Orders": c.total_orders, "Spend (₹)": c.total_spend
        }
        for c in customers
    ]
    df = pd.DataFrame(data)

    if search:
        mask = (
            df["Name"].str.contains(search, case=False, na=False) |
            df["Email"].str.contains(search, case=False, na=False) |
            df["City"].str.contains(search, case=False, na=False)
        )
        df = df[mask]

    st.dataframe(df, use_container_width=True, hide_index=True)
    st.caption(f"{len(df)} customer(s) shown")

    st.divider()

    # --- Edit / Delete (Admin only) ---
    if not is_admin():
        st.info("ℹ️ Contact an admin to edit or delete customers.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("✏️ Edit Customer")
        db2 = get_session()
        customers2 = db2.query(Customer).all()
        customer_map = {f"{c.id} — {c.name}": c for c in customers2}
        selected = st.selectbox("Select customer to edit", list(customer_map.keys()), key="edit_select")

        if selected:
            c = customer_map[selected]
            with st.form("edit_form"):
                new_name = st.text_input("Name", value=c.name, max_chars=100)
                new_email = st.text_input("Email", value=c.email, max_chars=150)
                new_phone = st.text_input("Phone", value=c.phone or "", max_chars=20)
                new_city = st.text_input("City", value=c.city or "", max_chars=100)
                new_orders = st.number_input("Orders", value=c.total_orders, min_value=0, max_value=100000)
                new_spend = st.number_input("Spend (₹)", value=float(c.total_spend), min_value=0.0, max_value=10_000_000.0)

                if st.form_submit_button("Save Changes", type="primary"):
                    errors = []
                    ok, msg = validate_name(new_name)
                    if not ok: errors.append(msg)
                    ok, msg = validate_email(new_email)
                    if not ok: errors.append(msg)
                    ok, msg = validate_phone(new_phone)
                    if not ok: errors.append(msg)

                    if errors:
                        for e in errors: st.error(e)
                    else:
                        c.name = new_name.strip()
                        c.email = new_email.strip().lower()
                        c.phone = new_phone.strip()
                        c.city = new_city.strip()
                        c.total_orders = int(new_orders)
                        c.total_spend = float(new_spend)
                        db2.commit()
                        log_action("EDIT_CUSTOMER", f"Edited customer ID {c.id}: {new_name.strip()}")
                        st.success("Customer updated.")
                        st.rerun()
        db2.close()

    with col2:
        st.subheader("🗑️ Delete Customer")
        db3 = get_session()
        customers3 = db3.query(Customer).all()
        del_map = {f"{c.id} — {c.name}": c for c in customers3}
        del_selected = st.selectbox("Select customer to delete", list(del_map.keys()), key="del_select")

        if del_selected:
            c_del = del_map[del_selected]
            st.warning(f"This will permanently delete **{c_del.name}** and all their communication logs.")
            confirm = st.checkbox("I understand this action is irreversible")
            if confirm and st.button("Delete Customer", type="secondary"):
                name_del = c_del.name
                db3.query(Customer).filter(Customer.id == c_del.id).delete()
                db3.commit()
                log_action("DELETE_CUSTOMER", f"Deleted customer ID {c_del.id}: {name_del}")
                st.success("Customer deleted.")
                st.rerun()
        db3.close()
