import streamlit as st
from utils.session import (init_session, agregar_item, quitar_item, get_total,
                            enviar_cocina, get_orden, mis_mesas, mesa_bloqueada,
                            actualizar_nota, eliminar_item_enviado, LLEVAR_KEY)
from utils.db import get_menu, get_num_mesas


def render():
    init_session()
    n = get_num_mesas()
    menu = get_menu()
    usuario = st.session_state.usuario["nombre"]
    es_admin = st.session_state.get("es_admin", False)

    # ── Selector de mesa ──────────────────────────────────────────────────────
    opciones_num = list(range(1, n + 1))
    if not es_admin:
        opciones_num = [
            i for i in opciones_num
            if not mesa_bloqueada(i) or mesa_bloqueada(i) == usuario
        ]

    opciones = opciones_num + [LLEVAR_KEY]
    label_map = {i: f"Mesa {i}" for i in opciones_num}
    label_map[LLEVAR_KEY] = "🥡 Para llevar"

    mesa_actual = st.session_state.mesa_actual
    if mesa_actual not in opciones:
        mesa_actual = opciones[0] if opciones else LLEVAR_KEY

    col_sel, _ = st.columns([1.4, 2.6])
    with col_sel:
        mesa = st.selectbox(
            "Mesa / Pedido",
            options=opciones,
            format_func=lambda x: label_map.get(x, str(x)),
            index=opciones.index(mesa_actual) if mesa_actual in opciones else 0,
            key="orden_mesa_sel"
        )
        st.session_state.mesa_actual = mesa

    orden = get_orden(mesa)
    mesero_orden = orden["mesero"] or usuario
    etiqueta = "Para llevar" if mesa == LLEVAR_KEY else f"Mesa {mesa}"

    st.markdown(f"<span class='tag-mesero'>Mesero: {mesero_orden} · {etiqueta}</span>",
                unsafe_allow_html=True)
    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    col_menu, col_orden = st.columns([1.6, 1])

    # ── Menú ──────────────────────────────────────────────────────────────────
    with col_menu:
        st.markdown("**Menú — toca para agregar**")
        for cat, items in menu.items():
            with st.expander(cat, expanded=True):
                cols = st.columns(2)
                for i, item in enumerate(items):
                    with cols[i % 2]:
                        if st.button(
                            f"{item['nombre']}\n**${item['precio']}**",
                            key=f"menu_{cat}_{item['nombre']}_{mesa}",
                            use_container_width=True
                        ):
                            agregar_item(mesa, item["nombre"], item["precio"])
                            st.rerun()

    # ── Orden activa ──────────────────────────────────────────────────────────
    with col_orden:
        items = orden["items"]
        enviados   = [it for it in items if it["enviado"]]
        pendientes = [it for it in items if not it["enviado"]]

        # ── Items ya enviados a cocina ────────────────────────────────────────
        if enviados:
            st.markdown("**✅ Ya en cocina**")
            for idx, item in enumerate(items):
                if not item["enviado"]:
                    continue
                real_idx = items.index(item)
                c1, c2, c3 = st.columns([3, 1, 0.7])
                with c1:
                    nota_txt = f" · *{item['nota']}*" if item.get("nota") else ""
                    st.markdown(
                        f"<span style='font-size:13px;color:#7a6a5a;'>"
                        f"{item['cantidad']}x {item['nombre']}{nota_txt}</span>",
                        unsafe_allow_html=True
                    )
                with c2:
                    st.markdown(
                        f"<span style='font-size:12px;color:#7a6a5a;'>${item['precio']*item['cantidad']:,}</span>",
                        unsafe_allow_html=True
                    )
                with c3:
                    # Botón para eliminar con confirmación
                    if st.button("🗑", key=f"del_env_{mesa}_{real_idx}",
                                 help="Eliminar este item (ya enviado a cocina)"):
                        st.session_state[f"confirm_del_{mesa}_{real_idx}"] = True
                        st.rerun()

                if st.session_state.get(f"confirm_del_{mesa}_{real_idx}"):
                    st.warning(f"¿Eliminar '{item['nombre']}' de la orden? Ya fue enviado a cocina.")
                    ca, cb = st.columns(2)
                    with ca:
                        if st.button("Sí, eliminar", key=f"yes_del_{mesa}_{real_idx}", type="primary"):
                            eliminar_item_enviado(mesa, real_idx)
                            del st.session_state[f"confirm_del_{mesa}_{real_idx}"]
                            st.rerun()
                    with cb:
                        if st.button("Cancelar", key=f"no_del_{mesa}_{real_idx}"):
                            del st.session_state[f"confirm_del_{mesa}_{real_idx}"]
                            st.rerun()

        # ── Items pendientes (aún no enviados) ───────────────────────────────
        if pendientes:
            st.markdown("**🕐 Pendientes de enviar**")
            for item in pendientes:
                real_idx = items.index(item)
                c1, c2, c3, c4 = st.columns([2.2, .5, .5, 1])
                with c1:
                    st.markdown(
                        f"<span style='font-size:13px;font-weight:500;'>{item['nombre']}</span>",
                        unsafe_allow_html=True
                    )
                with c2:
                    if st.button("−", key=f"menos_{mesa}_{real_idx}"):
                        quitar_item(mesa, real_idx, -1)
                        st.rerun()
                with c3:
                    st.markdown(
                        f"<span style='font-weight:600;font-size:14px;'>{item['cantidad']}</span>",
                        unsafe_allow_html=True
                    )
                with c4:
                    if st.button("+", key=f"mas_{mesa}_{real_idx}"):
                        agregar_item(mesa, item["nombre"], item["precio"])
                        st.rerun()

                # Nota / observación por item
                nota_key = f"nota_{mesa}_{real_idx}"
                nota_val = st.text_input(
                    "Observación",
                    value=item.get("nota", ""),
                    placeholder="Ej: sin chile, con tortilla...",
                    key=nota_key,
                    label_visibility="collapsed"
                )
                if nota_val != item.get("nota", ""):
                    actualizar_nota(mesa, real_idx, nota_val)

                st.markdown(
                    f"<div style='text-align:right;font-size:13px;font-weight:500;"
                    f"margin-bottom:8px;'>${item['precio']*item['cantidad']:,}</div>",
                    unsafe_allow_html=True
                )

        if not items:
            st.caption("Sin artículos. Toca el menú para agregar.")

        # ── Total y acciones ─────────────────────────────────────────────────
        if items:
            st.markdown("---")
            total = get_total(mesa)
            total_enviado = sum(i["precio"]*i["cantidad"] for i in enviados)
            total_nuevo   = sum(i["precio"]*i["cantidad"] for i in pendientes)

            if enviados and pendientes:
                st.markdown(
                    f"<div style='font-size:13px;color:#7a6a5a;'>Ya enviado: ${total_enviado:,}"
                    f"  +  Nuevo: ${total_nuevo:,}</div>",
                    unsafe_allow_html=True
                )
            st.markdown(f"### Total: ${total:,.0f}")

        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

        # Botón enviar — solo activo si hay pendientes
        hay_pendientes = bool(pendientes)
        if st.button(
            "👨‍🍳 Enviar a cocina" + (" (nuevo)" if enviados and hay_pendientes else ""),
            use_container_width=True,
            type="primary",
            disabled=not hay_pendientes
        ):
            resultado = enviar_cocina(mesa)
            if resultado == "nada_nuevo":
                st.info("Todo ya fue enviado a cocina. Agrega nuevos platillos para enviar más.")
            elif resultado:
                n_items = len(pendientes)
                st.success(f"✅ {n_items} platillo(s) de {etiqueta} enviados a cocina.")
                st.rerun()

        if not hay_pendientes and items:
            st.caption("Todo enviado. Agrega más platillos para enviar de nuevo.")

        if st.button("💳 Cobrar", use_container_width=True):
            st.session_state.pagina = "cobrar"
            st.rerun()
