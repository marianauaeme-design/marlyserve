import streamlit as st
from utils.db import get_meseros, get_admin_pin


def render_login():
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
        <div style='text-align:center; padding: 2rem 0 1rem;'>
            <div style='width:64px;height:64px;background:#E85D04;border-radius:50%;
                display:inline-flex;align-items:center;justify-content:center;
                color:white;font-size:22px;font-weight:600;margin-bottom:1rem;'>MS</div>
            <h2 style='margin:0;font-size:22px;'>MarlyServe</h2>
            <p style='color:#7a6a5a;font-size:14px;margin-top:4px;'>Sistema de punto de venta</p>
        </div>
        """, unsafe_allow_html=True)

        if "pin_mode" not in st.session_state:
            st.session_state.pin_mode = False
        if "pin_seleccionado" not in st.session_state:
            st.session_state.pin_seleccionado = None
        if "pin_es_admin" not in st.session_state:
            st.session_state.pin_es_admin = False
        if "pin_ingresado" not in st.session_state:
            st.session_state.pin_ingresado = ""
        if "pin_error" not in st.session_state:
            st.session_state.pin_error = ""

        if not st.session_state.pin_mode:
            _render_selector()
        else:
            _render_pin_pad()


def _render_selector():
    meseros = [m for m in get_meseros() if m["activo"]]
    st.markdown("<p style='text-align:center;color:#7a6a5a;font-size:14px;margin-bottom:1rem;'>¿Quién eres?</p>", unsafe_allow_html=True)

    cols = st.columns(2)
    for i, m in enumerate(meseros):
        with cols[i % 2]:
            if st.button(m["nombre"], key=f"sel_{m['nombre']}", use_container_width=True):
                st.session_state.pin_seleccionado = m
                st.session_state.pin_es_admin = False
                st.session_state.pin_mode = True
                st.session_state.pin_ingresado = ""
                st.session_state.pin_error = ""
                st.rerun()

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown("<hr style='border-color:#e8ddd0;margin:0.5rem 0 1rem;'>", unsafe_allow_html=True)

    if st.button("🔐  Acceso administrador", use_container_width=True):
        st.session_state.pin_seleccionado = None
        st.session_state.pin_es_admin = True
        st.session_state.pin_mode = True
        st.session_state.pin_ingresado = ""
        st.session_state.pin_error = ""
        st.rerun()


def _render_pin_pad():
    if st.session_state.pin_es_admin:
        titulo = "PIN de administrador"
    else:
        titulo = f"PIN de {st.session_state.pin_seleccionado['nombre']}"

    st.markdown(f"<p style='text-align:center;color:#7a6a5a;font-size:14px;'>{titulo}</p>", unsafe_allow_html=True)

    # Dots indicador
    pin = st.session_state.pin_ingresado
    dots_html = "".join([
        f"<div style='width:16px;height:16px;border-radius:50%;background:{'#E85D04' if i < len(pin) else '#e8ddd0'};display:inline-block;margin:0 6px;'></div>"
        for i in range(4)
    ])
    st.markdown(f"<div style='text-align:center;margin:1rem 0;'>{dots_html}</div>", unsafe_allow_html=True)

    if st.session_state.pin_error:
        st.error(st.session_state.pin_error)

    # Teclado numérico
    keys = [["1","2","3"],["4","5","6"],["7","8","9"],["←","0","✓"]]
    for fila in keys:
        cols = st.columns(3)
        for j, k in enumerate(fila):
            with cols[j]:
                if st.button(k, key=f"key_{k}", use_container_width=True):
                    _on_key(k)
                    st.rerun()

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    if st.button("← Volver", key="volver_pin"):
        st.session_state.pin_mode = False
        st.session_state.pin_ingresado = ""
        st.session_state.pin_error = ""
        st.rerun()


def _on_key(k):
    if k == "←":
        st.session_state.pin_ingresado = st.session_state.pin_ingresado[:-1]
        st.session_state.pin_error = ""
    elif k == "✓":
        _validar()
    elif len(st.session_state.pin_ingresado) < 4:
        st.session_state.pin_ingresado += k
        if len(st.session_state.pin_ingresado) == 4:
            _validar()


def _validar():
    pin = st.session_state.pin_ingresado
    if st.session_state.pin_es_admin:
        if pin == get_admin_pin():
            st.session_state.usuario = {"nombre": "Administrador"}
            st.session_state.es_admin = True
            _reset_pin_state()
        else:
            st.session_state.pin_error = "PIN incorrecto"
            st.session_state.pin_ingresado = ""
    else:
        m = st.session_state.pin_seleccionado
        if pin == m["pin"]:
            st.session_state.usuario = m
            st.session_state.es_admin = False
            _reset_pin_state()
        else:
            st.session_state.pin_error = "PIN incorrecto"
            st.session_state.pin_ingresado = ""


def _reset_pin_state():
    st.session_state.pin_mode = False
    st.session_state.pin_seleccionado = None
    st.session_state.pin_es_admin = False
    st.session_state.pin_ingresado = ""
    st.session_state.pin_error = ""
