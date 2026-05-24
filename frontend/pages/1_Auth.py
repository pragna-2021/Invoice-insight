import streamlit as st
from frontend.api_client import client
from frontend import ui

st.set_page_config(page_title="Authentication - Invoice Insight", page_icon="🔐")
ui.load_css()

st.title("🔐 Authentication")

if "token" in st.session_state:
    st.success(f"Currently logged in as {st.session_state['email']}")
    if st.button("Logout"):
        del st.session_state["token"]
        del st.session_state["email"]
        st.rerun()
else:
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login to your account")
        with st.form("login_form"):
            l_email = st.text_input("Email", key="l_email")
            l_password = st.text_input("Password", type="password", key="l_pass")
            submit = st.form_submit_button("Login")
            if submit:
                if client.login(l_email, l_password):
                    st.success("Logged in successfully!")
                    st.rerun()
                else:
                    st.error("Invalid credentials")
                    
    with tab2:
        st.subheader("Create a new account")
        with st.form("register_form"):
            r_email = st.text_input("Email", key="r_email")
            r_password = st.text_input("Password", type="password", key="r_pass")
            submit = st.form_submit_button("Register")
            if submit:
                if client.register(r_email, r_password):
                    st.success("Account created and logged in!")
                    st.rerun()
                else:
                    st.error("Failed to register. Email might already be taken.")
