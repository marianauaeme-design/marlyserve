import streamlit as st
from utils.db import get_ventas_hoy, get_cortes, registrar_corte, get_ventas_rango
from utils.session import init_session
from datetime import date, timedelta
import pandas as pd


def render():
    init_session()
    total_db, ordenes_db, ventas_mesero_db = get_ventas_hoy()

    total_sesion = st.session_state.get("ventas_sesion", 0)
    ordenes_sesion = st.session_state.get("ordenes_sesion", 0)
    total_dia = total_db + total_sesion
    ordenes_dia = ordenes_db + ordenes_sesion

    # ── Resumen del día ──────────────────────────────────────────────────────
    st.markdown("#### Resumen del día")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-label'>Órdenes cerradas</div>
            <div class='metric-value'>{ordenes_dia}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        ticket_prom = int(total_dia / ordenes_dia) if ordenes_dia else 0
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-label'>Ticket promedio</div>
            <div class='metric-value'>${ticket_prom:,}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class='metric-card'>
            <div class='metric-label'>Venta total</div>
            <div class='metric-value naranja'>${total_dia:,.0f}</div>
        </div>""", unsafe_allow_html=True)

    # ── Ventas por mesero ────────────────────────────────────────────────────
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown("#### Ventas por mesero — hoy")
    if ventas_mesero_db:
        df_mes = pd.DataFrame(
            [(k, v) for k, v in ventas_mesero_db.items()],
            columns=["Mesero", "Venta ($)"]
        ).sort_values("Venta ($)", ascending=False)
        st.dataframe(df_mes, use_container_width=True, hide_index=True)
    else:
        st.caption("Sin ventas registradas aún.")

    # ── Registrar corte ──────────────────────────────────────────────────────
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown("#### Registrar corte de caja")
    with st.form("form_corte"):
        notas = st.text_input("Notas (opcional)", placeholder="Ej: turno mañana, evento especial...")
        submitted = st.form_submit_button("💾 Registrar corte ahora", use_container_width=True)
        if submitted:
            nombre = st.session_state.usuario["nombre"]
            registrar_corte(nombre, ordenes_dia, total_dia, notas)
            st.success(f"Corte registrado: {ordenes_dia} órdenes · ${total_dia:,.0f}")

    # ── Historial de cortes ──────────────────────────────────────────────────
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    st.markdown("#### Historial de cortes")
    cortes = get_cortes()
    if cortes:
        df_c = pd.DataFrame(cortes)
        df_c.columns = ["Fecha", "Hora", "Quién cortó", "Órdenes", "Total ($)", "Notas"]
        st.dataframe(df_c, use_container_width=True, hide_index=True)
    else:
        st.caption("Sin cortes registrados.")

    # ── Reporte por fechas (solo admin) ─────────────────────────────────────
    if st.session_state.get("es_admin"):
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        st.markdown("#### Reporte por rango de fechas")
        c1, c2 = st.columns(2)
        with c1:
            fi = st.date_input("Desde", value=date.today() - timedelta(days=7), key="fi")
        with c2:
            ff = st.date_input("Hasta", value=date.today(), key="ff")
        if st.button("Generar reporte", key="gen_reporte"):
            rows = get_ventas_rango(fi, ff)
            if rows:
                df_r = pd.DataFrame(rows)
                total_r = df_r["subtotal"].sum()
                st.markdown(f"**Total del período: ${total_r:,.0f}**")
                st.dataframe(df_r, use_container_width=True, hide_index=True)
                csv = df_r.to_csv(index=False).encode("utf-8")
                st.download_button("⬇ Descargar CSV", csv, "reporte_ventas.csv", "text/csv")
            else:
                st.info("Sin ventas en ese rango.")
