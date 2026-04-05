import streamlit as st
from utils.db import (
    get_menu, update_menu, add_menu_item, delete_menu_item,
    get_meseros, add_mesero, update_pin, toggle_mesero, delete_mesero,
    get_admin_pin, update_config, get_num_mesas
)


def render():
    st.markdown("### ⚙️ Panel de administración")

    tab1, tab2, tab3 = st.tabs(["Equipo", "Menú completo", "Configuración"])

    # ── TAB 1: Meseros ───────────────────────────────────────────────────────
    with tab1:
        st.markdown("#### Meseros registrados")
        meseros = get_meseros()
        for m in meseros:
            c1, c2, c3, c4, c5 = st.columns([2, 1.4, 1, 1.8, 0.7])
            with c1:
                st.markdown(f"**{m['nombre']}**")
            with c2:
                st.markdown(f"`PIN: {m['pin']}`")
            with c3:
                activo = m.get("activo", True)
                label = "✅ Activo" if activo else "❌ Inactivo"
                if st.button(label, key=f"toggle_{m['nombre']}"):
                    toggle_mesero(m["nombre"], not activo)
                    st.rerun()
            with c4:
                nuevo_pin = st.text_input(
                    "Nuevo PIN", max_chars=4, key=f"pin_input_{m['nombre']}",
                    placeholder="4 dígitos"
                )
                if st.button("Cambiar PIN", key=f"pin_btn_{m['nombre']}"):
                    if nuevo_pin.isdigit() and len(nuevo_pin) == 4:
                        update_pin(m["nombre"], nuevo_pin)
                        st.success(f"PIN de {m['nombre']} actualizado.")
                        st.rerun()
                    else:
                        st.error("El PIN debe ser 4 dígitos numéricos.")
            with c5:
                if st.button("🗑", key=f"del_mesero_{m['nombre']}", help=f"Eliminar a {m['nombre']}"):
                    st.session_state[f"confirmar_del_{m['nombre']}"] = True
                    st.rerun()

            if st.session_state.get(f"confirmar_del_{m['nombre']}"):
                st.warning(f"¿Eliminar a **{m['nombre']}** permanentemente?")
                ca, cb, _ = st.columns([1, 1, 3])
                with ca:
                    if st.button("Sí, eliminar", key=f"confirm_yes_{m['nombre']}", type="primary"):
                        delete_mesero(m["nombre"])
                        del st.session_state[f"confirmar_del_{m['nombre']}"]
                        st.success(f"{m['nombre']} eliminado.")
                        st.rerun()
                with cb:
                    if st.button("Cancelar", key=f"confirm_no_{m['nombre']}"):
                        del st.session_state[f"confirmar_del_{m['nombre']}"]
                        st.rerun()
            st.markdown("<hr style='margin:6px 0;border-color:#f0e8df;'>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Agregar mesero")
        with st.form("form_agregar_mesero"):
            c1, c2 = st.columns(2)
            with c1:
                nuevo_nombre = st.text_input("Nombre")
            with c2:
                nuevo_pin_m = st.text_input("PIN (4 dígitos)", max_chars=4)
            if st.form_submit_button("➕ Agregar mesero"):
                if nuevo_nombre and nuevo_pin_m.isdigit() and len(nuevo_pin_m) == 4:
                    add_mesero(nuevo_nombre.strip(), nuevo_pin_m)
                    st.success(f"{nuevo_nombre} agregado al equipo.")
                    st.rerun()
                else:
                    st.error("Nombre requerido y PIN de 4 dígitos numéricos.")

    # ── TAB 2: Menú completo ─────────────────────────────────────────────────
    with tab2:
        menu = get_menu()
        cats = list(menu.keys())

        sub1, sub2 = st.tabs(["✏️ Editar productos", "➕ Agregar / eliminar"])

        # -- Subtab: Editar precios y nombres --
        with sub1:
            st.markdown("#### Editar productos existentes")
            st.caption("Cambia nombre, precio o elimina cada producto.")

            for cat in cats:
                st.markdown(f"""
                <div style='background:#FAEEDA;border-left:4px solid #E85D04;
                    padding:6px 12px;border-radius:4px;margin:1rem 0 6px;
                    font-weight:600;color:#7C2D12;'>{cat}</div>
                """, unsafe_allow_html=True)

                for item in menu[cat]:
                    with st.container():
                        c1, c2, c3, c4 = st.columns([2.5, 1.2, 0.8, 0.8])
                        with c1:
                            nombre_nuevo = st.text_input(
                                "Nombre", value=item["nombre"],
                                key=f"edit_nombre_{cat}_{item['nombre']}",
                                label_visibility="collapsed"
                            )
                        with c2:
                            precio_nuevo = st.number_input(
                                "Precio", value=item["precio"], min_value=1, step=5,
                                key=f"edit_precio_{cat}_{item['nombre']}",
                                label_visibility="collapsed"
                            )
                        with c3:
                            if st.button("💾", key=f"save_{cat}_{item['nombre']}",
                                        help="Guardar cambios"):
                                # Si cambió el nombre, eliminar el viejo y agregar nuevo
                                if nombre_nuevo != item["nombre"]:
                                    delete_menu_item(cat, item["nombre"])
                                    add_menu_item(cat, nombre_nuevo, precio_nuevo)
                                else:
                                    update_menu(cat, item["nombre"], precio_nuevo)
                                st.success(f"'{nombre_nuevo}' actualizado.")
                                st.rerun()
                        with c4:
                            if st.button("🗑", key=f"del_{cat}_{item['nombre']}",
                                        help="Eliminar producto"):
                                delete_menu_item(cat, item["nombre"])
                                st.success(f"'{item['nombre']}' eliminado.")
                                st.rerun()

        # -- Subtab: Agregar productos y categorías --
        with sub2:
            # Agregar producto a categoría existente
            st.markdown("#### Agregar producto")
            with st.form("form_nuevo_producto"):
                c1, c2, c3 = st.columns([2, 2, 1])
                with c1:
                    cat_opts = cats + ["🆕 Nueva categoría"]
                    cat_sel = st.selectbox("Categoría", cat_opts, key="cat_sel_form")
                with c2:
                    prod_nombre = st.text_input("Nombre del producto")
                with c3:
                    prod_precio = st.number_input("Precio ($)", min_value=1, step=5, value=50)

                cat_nueva_input = ""
                if cat_sel == "🆕 Nueva categoría":
                    cat_nueva_input = st.text_input("Nombre de la nueva categoría")

                if st.form_submit_button("➕ Agregar producto"):
                    cat_final = cat_nueva_input.strip() if cat_sel == "🆕 Nueva categoría" else cat_sel
                    if cat_final and prod_nombre.strip():
                        add_menu_item(cat_final, prod_nombre.strip(), prod_precio)
                        st.success(f"'{prod_nombre}' agregado a {cat_final}.")
                        st.rerun()
                    else:
                        st.error("Completa el nombre de categoría y producto.")

            st.markdown("---")

            # Renombrar categoría completa
            st.markdown("#### Renombrar categoría")
            with st.form("form_renombrar_cat"):
                c1, c2 = st.columns(2)
                with c1:
                    cat_vieja = st.selectbox("Categoría actual", cats, key="cat_vieja")
                with c2:
                    cat_nueva_nombre = st.text_input("Nuevo nombre")
                if st.form_submit_button("✏️ Renombrar"):
                    if cat_nueva_nombre.strip() and cat_nueva_nombre != cat_vieja:
                        # Mueve todos los items a la nueva categoría
                        for it in menu[cat_vieja]:
                            add_menu_item(cat_nueva_nombre.strip(), it["nombre"], it["precio"])
                            delete_menu_item(cat_vieja, it["nombre"])
                        st.success(f"'{cat_vieja}' renombrada a '{cat_nueva_nombre}'.")
                        st.rerun()
                    else:
                        st.error("Escribe un nombre diferente.")

            st.markdown("---")

            # Eliminar categoría completa
            st.markdown("#### Eliminar categoría completa")
            st.warning("⚠️ Esto elimina todos los productos de la categoría.")
            with st.form("form_eliminar_cat"):
                cat_eliminar = st.selectbox("Categoría a eliminar", cats, key="cat_del")
                confirmacion = st.text_input("Escribe ELIMINAR para confirmar")
                if st.form_submit_button("🗑 Eliminar categoría"):
                    if confirmacion == "ELIMINAR":
                        for it in menu[cat_eliminar]:
                            delete_menu_item(cat_eliminar, it["nombre"])
                        st.success(f"Categoría '{cat_eliminar}' eliminada.")
                        st.rerun()
                    else:
                        st.error("Escribe ELIMINAR en mayúsculas para confirmar.")

    # ── TAB 3: Configuración ─────────────────────────────────────────────────
    with tab3:
        st.markdown("#### Configuración general")

        with st.form("form_config"):
            c1, c2 = st.columns(2)
            with c1:
                admin_pin_actual = get_admin_pin()
                nuevo_admin_pin = st.text_input(
                    "PIN de administrador", value=admin_pin_actual,
                    max_chars=4, help="4 dígitos numéricos"
                )
            with c2:
                num_mesas_actual = get_num_mesas()
                nuevo_num_mesas = st.number_input(
                    "Número de mesas", value=num_mesas_actual,
                    min_value=1, max_value=50, step=1
                )

            nombre_negocio = st.text_input("Nombre del negocio", value="Barbacoa Tío R")

            if st.form_submit_button("💾 Guardar configuración"):
                if nuevo_admin_pin.isdigit() and len(nuevo_admin_pin) == 4:
                    update_config("admin_pin", nuevo_admin_pin)
                    update_config("num_mesas", nuevo_num_mesas)
                    update_config("negocio", nombre_negocio)
                    st.success("Configuración guardada. Reinicia la app para aplicar cambios de mesas.")
                else:
                    st.error("El PIN de admin debe ser 4 dígitos numéricos.")

        st.markdown("---")
        st.markdown("#### Información de impresora Bluetooth")
        st.markdown("""
        Para conectar la impresora mini Bluetooth:
        1. Instala la dependencia: `pip install python-escpos[bt]`
        2. En el menú **Cobrar**, elige *Bluetooth* e ingresa la MAC de tu impresora
        3. La MAC la encuentras en la app de tu teléfono o en la etiqueta de la impresora

        Para impresión USB:
        1. Instala: `pip install python-escpos[usb]`
        2. En **Cobrar**, elige *USB* — detecta automáticamente la impresora
        """)
