import streamlit as st
from datetime import datetime


def render_nav():
    usuario = st.session_state.usuario
    es_admin = st.session_state.es_admin
    nombre = usuario["nombre"]
    ini = nombre[:2].upper()

    # Header
    st.markdown(f"""
    <div style='background:#E85D04;border-radius:12px;padding:.75rem 1.25rem;
        display:flex;align-items:center;gap:12px;margin-bottom:1rem;'>
        <div style='width:36px;height:36px;background:rgba(255,255,255,0.25);border-radius:50%;
            display:flex;align-items:center;justify-content:center;color:white;font-weight:600;font-size:13px;'>{ini}</div>
        <span style='color:white;font-size:17px;font-weight:600;flex:1;'>MarlyServe</span>
        <span style='color:rgba(255,255,255,0.8);font-size:13px;'>{datetime.now().strftime('%H:%M')} · {nombre}</span>
    </div>
    """, unsafe_allow_html=True)

    if "pagina" not in st.session_state:
        st.session_state.pagina = "mesas"

    # Tabs
    tabs_mesero = ["🪑 Mesas", "📋 Orden", "👨‍🍳 Cocina", "💳 Cobrar", "📊 Corte"]
    tabs_admin  = ["🪑 Mesas", "📋 Orden", "👨‍🍳 Cocina", "💳 Cobrar", "📊 Corte", "⚙️ Admin"]
    tabs = tabs_admin if es_admin else tabs_mesero
    keys_map = {
        "🪑 Mesas": "mesas", "📋 Orden": "orden", "👨‍🍳 Cocina": "cocina",
        "💳 Cobrar": "cobrar", "📊 Corte": "corte", "⚙️ Admin": "admin"
    }

    cols = st.columns(len(tabs))
    for i, tab in enumerate(tabs):
        with cols[i]:
            key = keys_map[tab]
            activo = st.session_state.pagina == key
            style = "background:#E85D04;color:white;border:none;" if activo else ""
            if st.button(tab, key=f"nav_{key}", use_container_width=True):
                st.session_state.pagina = key
                st.rerun()

    st.markdown("<hr style='border-color:#e8ddd0;margin:.5rem 0 1rem;'>", unsafe_allow_html=True)

    # Render page
    pagina = st.session_state.pagina
    if pagina == "mesas":
        from pages.mesas import render
        render()
    elif pagina == "orden":
        from pages.orden import render
        render()
    elif pagina == "cocina":
        from pages.cocina import render
        render()
    elif pagina == "cobrar":
        from pages.cobrar import render
        render()
    elif pagina == "corte":
        from pages.corte import render
        render()
    elif pagina == "admin" and es_admin:
        from pages.admin import render
        render()

    # Logout
    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
    if st.button("Cerrar sesión", key="logout"):
        for key in ["usuario", "es_admin", "pagina", "mesa_actual", "ordenes_mesas"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()
