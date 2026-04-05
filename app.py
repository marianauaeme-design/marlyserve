import streamlit as st
from utils.db import init_db
from utils.auth import render_login

st.set_page_config(
    page_title="MarlyServe",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS global
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 1rem; padding-bottom: 1rem;}
div[data-testid="stSidebarNav"] {display: none;}
.stButton > button {
    border-radius: 8px;
    font-weight: 500;
    transition: all 0.15s;
}
.stButton > button:hover {opacity: 0.88;}
.metric-card {
    background: #f9f6f2;
    border: 1px solid #e8ddd0;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    text-align: center;
}
.metric-label {font-size: 13px; color: #7a6a5a; margin-bottom: 4px;}
.metric-value {font-size: 26px; font-weight: 600; color: #1a1a1a;}
.naranja {color: #E85D04;}
.tag-mesero {
    display: inline-block;
    background: #FAEEDA;
    color: #7C2D12;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 12px;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

init_db()

if "usuario" not in st.session_state:
    st.session_state.usuario = None
if "es_admin" not in st.session_state:
    st.session_state.es_admin = False

if st.session_state.usuario is None:
    render_login()
else:
    from utils.nav import render_nav
    render_nav()
