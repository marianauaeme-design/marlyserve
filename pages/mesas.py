import streamlit as st
from utils.session import (init_session, get_mesas_ocupadas, get_total,
                            mis_notificaciones, limpiar_notificaciones,
                            mesa_bloqueada, mis_mesas, LLEVAR_KEY)
from utils.db import get_num_mesas, get_ventas_hoy


def render():
    init_session()
    n = get_num_mesas()
    usuario = st.session_state.usuario["nombre"]
    es_admin = st.session_state.get("es_admin", False)

    # ── Notificaciones ────────────────────────────────────────────────────────
    notifs = mis_notificaciones(usuario)
    if notifs:
        for notif in notifs:
            st.success(f"🔔 {notif['hora']} — {notif['mensaje']}")
        if st.button("✓ Marcar como leídas", key="limpiar_notifs"):
            limpiar_notificaciones(usuario)
            st.rerun()
        st.markdown("---")

    # ── Métricas — admin ve todo, mesero solo sus propios números ─────────────
    if es_admin:
        total_dia, ordenes_dia, _ = get_ventas_hoy()
        venta_total   = total_dia + st.session_state.get("ventas_sesion", 0)
        ordenes_total = ordenes_dia + st.session_state.get("ordenes_sesion", 0)
        ocupadas = get_mesas_ocupadas()

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""<div class='metric-card'>
                <div class='metric-label'>Mesas ocupadas</div>
                <div class='metric-value'>{len(ocupadas)} / {n}</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class='metric-card'>
                <div class='metric-label'>Órdenes cerradas hoy</div>
                <div class='metric-value'>{ordenes_total}</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class='metric-card'>
                <div class='metric-label'>Venta del día</div>
                <div class='metric-value naranja'>${venta_total:,.0f}</div>
            </div>""", unsafe_allow_html=True)
    else:
        # Mesero solo ve sus propias métricas
        mis = mis_mesas(usuario)
        mi_venta = sum(get_total(m) for m in mis)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""<div class='metric-card'>
                <div class='metric-label'>Mis mesas activas</div>
                <div class='metric-value'>{len(mis)}</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class='metric-card'>
                <div class='metric-label'>Acumulado en mis mesas</div>
                <div class='metric-value naranja'>${mi_venta:,.0f}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── Mis mesas (badges rápidos) ────────────────────────────────────────────
    if not es_admin:
        mis = mis_mesas(usuario)
        if mis:
            badges = "  ".join(
                [f"<span style='background:#FAEEDA;color:#7C2D12;border-radius:6px;"
                 f"padding:3px 10px;font-size:13px;font-weight:500;'>Mesa {m}</span>"
                 for m in sorted(mis)]
            )
            st.markdown(f"**Tus mesas:** {badges}", unsafe_allow_html=True)
            st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    # ── Pedido para llevar ────────────────────────────────────────────────────
    orden_llevar  = st.session_state.ordenes_mesas.get(LLEVAR_KEY, {})
    tiene_llevar  = bool(orden_llevar.get("items"))
    mesero_llevar = orden_llevar.get("mesero", "")
    puede_llevar  = es_admin or not mesero_llevar or mesero_llevar == usuario
    total_llevar  = get_total(LLEVAR_KEY) if tiene_llevar and puede_llevar else 0

    if tiene_llevar and puede_llevar:
        llevar_label = f"🥡 Para llevar — {mesero_llevar} · ${total_llevar:,.0f}"
    elif tiene_llevar and not puede_llevar:
        llevar_label = f"🥡 Para llevar — ocupado por {mesero_llevar}"
    else:
        llevar_label = "🥡 Nuevo pedido para llevar"

    if st.button(llevar_label, key="btn_llevar"):
        if tiene_llevar and not puede_llevar:
            st.warning(f"Este pedido lo está atendiendo **{mesero_llevar}**.")
        else:
            st.session_state.mesa_actual = LLEVAR_KEY
            st.session_state.pagina = "orden"
            st.rerun()

    # ── Mapa de mesas ─────────────────────────────────────────────────────────
    col_tit, col_ref = st.columns([4, 1])
    with col_tit:
        st.markdown("#### Mapa de mesas")
    with col_ref:
        if st.button("🔄", key="refresh_mesas", help="Actualizar"):
            st.rerun()

    if es_admin:
        st.markdown(
            "<div style='font-size:12px;color:#7a6a5a;margin-bottom:10px;'>"
            "🟠 Ocupada · ⬜ Libre</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            "<div style='font-size:12px;color:#7a6a5a;margin-bottom:10px;'>"
            "🟠 Tu mesa · 🔒 Otro mesero · ⬜ Libre</div>", unsafe_allow_html=True)

    cols = st.columns(5)
    for i in range(1, n + 1):
        orden   = st.session_state.ordenes_mesas[i]
        tiene   = bool(orden["items"])
        atiende = orden.get("mesero", "")
        es_mia  = atiende == usuario

        with cols[(i - 1) % 5]:
            if not tiene:
                # ── Libre ──────────────────────────────────────────────────
                label = f"⬜ Mesa {i}\nLibre"
                if st.button(label, key=f"mesa_btn_{i}", use_container_width=True):
                    st.session_state.mesa_actual = i
                    st.session_state.pagina = "orden"
                    st.rerun()

            elif es_mia or es_admin:
                # ── Mi mesa (o admin) — muestra detalles ───────────────────
                total = get_total(i)
                pendientes = sum(1 for it in orden["items"] if not it.get("enviado", False))
                alerta = f"\n⚠ {pendientes} sin enviar" if pendientes else ""
                label = f"🟠 Mesa {i}\n{atiende}\n${total:,.0f}{alerta}"
                if st.button(label, key=f"mesa_btn_{i}", use_container_width=True):
                    st.session_state.mesa_actual = i
                    st.session_state.pagina = "orden"
                    st.rerun()

            else:
                # ── Mesa de otro mesero — sin detalles ─────────────────────
                label = f"🔒 Mesa {i}\n{atiende}"
                if st.button(label, key=f"mesa_btn_{i}", use_container_width=True):
                    st.warning(
                        f"🔒 La Mesa {i} la está atendiendo **{atiende}**. "
                        f"Se libera al cobrar."
                    )
