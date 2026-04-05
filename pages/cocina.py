import streamlit as st
from utils.session import init_session, agregar_notificacion


def render():
    init_session()
    queue = st.session_state.cocina_queue

    if st.button("🔄 Actualizar", key="cocina_refresh"):
        st.rerun()

    if not queue:
        st.markdown("""
        <div style='text-align:center;padding:3rem;color:#7a6a5a;'>
            <div style='font-size:48px;'>👨‍🍳</div>
            <p style='margin-top:1rem;font-size:16px;'>Sin órdenes pendientes</p>
        </div>
        """, unsafe_allow_html=True)
        return

    pendientes = [o for o in queue if o["estado"] == "pendiente"]
    listos    = [o for o in queue if o["estado"] == "listo"]

    if pendientes:
        st.markdown(f"#### En cocina ({len(pendientes)})")
        cols = st.columns(min(len(pendientes), 3))
        for i, orden in enumerate(pendientes):
            with cols[i % 3]:
                def item_line(it):
                    nota = f" <em style='color:#E85D04;font-size:11px;'>→ {it['nota']}</em>" if it.get("nota") else ""
                    return (f"<div style='padding:3px 0;border-bottom:1px solid #f0e8df;'>"
                            f"<div style='display:flex;justify-content:space-between;font-size:13px;'>"
                            f"<span>{it['cantidad']}x {it['nombre']}</span>"
                            f"<span>${it['precio']*it['cantidad']:,}</span></div>"
                            f"{nota}</div>")
                items_html = "".join(item_line(it) for it in orden["items"])
                st.markdown(f"""
                <div style='border:1.5px solid #E85D04;border-radius:10px;padding:1rem;
                    margin-bottom:8px;background:#fffaf7;'>
                    <div style='display:flex;justify-content:space-between;margin-bottom:8px;'>
                        <span style='font-weight:600;font-size:16px;'>{orden['etiqueta']}</span>
                        <span style='background:#FAEEDA;color:#7C2D12;border-radius:6px;
                            padding:2px 8px;font-size:12px;'>En cocina</span>
                    </div>
                    <div style='font-size:12px;color:#7a6a5a;margin-bottom:8px;'>
                        {orden['mesero']} · {orden['hora']}
                    </div>
                    {items_html}
                </div>
                """, unsafe_allow_html=True)

                if st.button("✅ Marcar listo", key=f"listo_{i}", use_container_width=True):
                    idx = queue.index(orden)
                    st.session_state.cocina_queue[idx]["estado"] = "listo"
                    # Notificar al mesero
                    mesero = orden["mesero"]
                    etiqueta = orden["etiqueta"]
                    agregar_notificacion(
                        mesero,
                        f"¡{etiqueta} lista para entregar! 🍖",
                        tipo="success"
                    )
                    st.success(f"Marcado listo. Se notificó a {mesero}.")
                    st.rerun()

    if listos:
        st.markdown(f"#### Listos para entregar ({len(listos)})")
        cols = st.columns(min(len(listos), 3))
        for i, orden in enumerate(listos):
            with cols[i % 3]:
                st.markdown(f"""
                <div style='border:1px solid #22c55e;border-radius:10px;padding:1rem;background:#f0fdf4;'>
                    <div style='display:flex;justify-content:space-between;'>
                        <span style='font-weight:600;'>{orden['etiqueta']}</span>
                        <span style='background:#dcfce7;color:#166534;border-radius:6px;
                            padding:2px 8px;font-size:12px;'>Listo ✓</span>
                    </div>
                    <div style='font-size:12px;color:#7a6a5a;margin-top:4px;'>
                        {orden['mesero']} · {orden['hora']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🗑 Quitar", key=f"quitar_listo_{i}", use_container_width=True):
                    st.session_state.cocina_queue.remove(orden)
                    st.rerun()

