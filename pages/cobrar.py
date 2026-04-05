import streamlit as st
from utils.session import (init_session, get_orden, get_total, cerrar_mesa,
                            mis_mesas, mesa_bloqueada, LLEVAR_KEY)
from utils.db import get_num_mesas
from utils.printer import generar_texto_ticket, imprimir_ticket_bluetooth, imprimir_ticket_usb

FORMAS_PAGO = ["Efectivo", "Tarjeta", "Transferencia"]


def render():
    init_session()
    n = get_num_mesas()
    usuario = st.session_state.usuario["nombre"]
    es_admin = st.session_state.get("es_admin", False)

    # ── Solo mostrar mesas del mesero (o todas si es admin) ───────────────────
    if es_admin:
        opciones_num = list(range(1, n + 1))
    else:
        mis = mis_mesas(usuario)
        opciones_num = mis if mis else []

    opciones = opciones_num + [LLEVAR_KEY]
    label_map = {i: f"Mesa {i}" for i in opciones_num}
    label_map[LLEVAR_KEY] = "🥡 Para llevar"

    if not opciones_num:
        st.info("No tienes mesas activas para cobrar.")
        llevar_orden = get_orden(LLEVAR_KEY)
        if not llevar_orden["items"]:
            return

    mesa_actual = st.session_state.mesa_actual
    if mesa_actual not in opciones:
        mesa_actual = opciones[0] if opciones else LLEVAR_KEY

    col_sel, _ = st.columns([1.2, 2.8])
    with col_sel:
        mesa = st.selectbox(
            "Cobrar",
            options=opciones,
            format_func=lambda x: label_map.get(x, str(x)),
            index=opciones.index(mesa_actual) if mesa_actual in opciones else 0,
            key="cobro_mesa_sel"
        )
        st.session_state.mesa_actual = mesa

    orden = get_orden(mesa)
    items = orden["items"]
    total = get_total(mesa)
    mesero = orden["mesero"] or usuario
    etiqueta = "Para llevar" if mesa == LLEVAR_KEY else f"Mesa {mesa}"

    if not items:
        st.info(f"{etiqueta} — sin orden activa.")
        return

    col_res, col_pago = st.columns([1, 1])

    # ── Resumen ───────────────────────────────────────────────────────────────
    with col_res:
        st.markdown(f"**Resumen — {etiqueta}**")
        st.markdown(f"<span class='tag-mesero'>Mesero: {mesero}</span>", unsafe_allow_html=True)
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

        for item in items:
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"<span style='font-size:13px;'>{item['cantidad']}x {item['nombre']}</span>",
                            unsafe_allow_html=True)
            with c2:
                st.markdown(f"<span style='font-size:13px;font-weight:500;'>${item['precio']*item['cantidad']:,}</span>",
                            unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f"### 💰 Total: ${total:,.0f}")

    # ── Pago ──────────────────────────────────────────────────────────────────
    with col_pago:
        st.markdown("**Forma de pago**")
        forma_pago = st.radio(
            "Forma de pago",
            FORMAS_PAGO,
            horizontal=True,
            label_visibility="collapsed",
            key="forma_pago_radio"
        )

        # Íconos visuales por forma de pago
        iconos = {"Efectivo": "💵", "Tarjeta": "💳", "Transferencia": "📲"}
        st.markdown(f"<div style='font-size:28px;text-align:center;margin:8px 0;'>{iconos[forma_pago]}</div>",
                    unsafe_allow_html=True)

        cambio = 0
        if forma_pago == "Efectivo":
            pago = st.number_input("Pago del cliente ($)", min_value=0, value=0, step=10, key="input_pago")
            if pago > 0:
                cambio = pago - total
                if cambio < 0:
                    st.error(f"Falta: ${abs(cambio):,.0f}")
                elif cambio == 0:
                    st.success("Pago exacto ✓")
                else:
                    st.markdown(f"""
                    <div style='background:#f0fdf4;border:1.5px solid #22c55e;border-radius:10px;
                        padding:1rem;text-align:center;margin:8px 0;'>
                        <div style='font-size:13px;color:#166534;'>Cambio a entregar</div>
                        <div style='font-size:32px;font-weight:700;color:#15803d;'>${cambio:,.0f}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            pago = total
            st.markdown(f"""
            <div style='background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;
                padding:1rem;text-align:center;margin:8px 0;'>
                <div style='font-size:13px;color:#1e40af;'>Total a cobrar por {forma_pago}</div>
                <div style='font-size:28px;font-weight:700;color:#1d4ed8;'>${total:,.0f}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

        # Preview ticket
        with st.expander("👁 Ver ticket"):
            folio = st.session_state.get("ordenes_sesion", 0) + 1
            texto = generar_texto_ticket(etiqueta, mesero, items, total,
                                         pago or total, max(cambio, 0), folio, forma_pago)
            st.code(texto, language=None)

        # Cerrar
        if st.button("✅ Cerrar y registrar pago", use_container_width=True, type="primary"):
            if forma_pago == "Efectivo" and pago < total:
                st.error("El pago en efectivo es menor al total.")
            else:
                ok, cambio_final = cerrar_mesa(mesa, pago, forma_pago)
                if ok:
                    cambio_txt = f"  Cambio: ${cambio_final:,.0f}" if forma_pago == "Efectivo" else ""
                    st.success(f"✅ {etiqueta} cerrada · {forma_pago}{cambio_txt}")
                    folio_n = st.session_state.get("ordenes_sesion", 0)
                    st.session_state["ultimo_ticket"] = generar_texto_ticket(
                        etiqueta, mesero, items, total, pago, cambio_final, folio_n, forma_pago
                    )
                    st.rerun()

        # Imprimir
        if "ultimo_ticket" in st.session_state:
            st.markdown("---")
            st.markdown("**Imprimir ticket**")
            metodo = st.radio("Conexión impresora", ["Bluetooth", "USB"],
                              horizontal=True, key="print_metodo")
            if metodo == "Bluetooth":
                mac = st.text_input("Dirección MAC", placeholder="AA:BB:CC:DD:EE:FF", key="mac_input")
                if st.button("🖨 Imprimir por Bluetooth", use_container_width=True):
                    ok, msg = imprimir_ticket_bluetooth(st.session_state["ultimo_ticket"], mac)
                    st.success(msg) if ok else st.warning(msg)
            else:
                if st.button("🖨 Imprimir por USB", use_container_width=True):
                    ok, msg = imprimir_ticket_usb(st.session_state["ultimo_ticket"])
                    st.success(msg) if ok else st.warning(msg)

