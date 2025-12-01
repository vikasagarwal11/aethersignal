import streamlit as st

def render_dsur_pbrer_panel(state):
    rep = state.get("dsur_pbrer_report")

    if not rep:
        st.info("Generate DSUR/PBRER from chat or using the quick-action button.")
        return

    st.markdown(rep["content"])
