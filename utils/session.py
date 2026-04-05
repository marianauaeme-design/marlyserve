import streamlit as st
from datetime import datetime
from utils.db import get_num_mesas

LLEVAR_KEY = "llevar"


def init_session():
    if "ordenes_mesas" not in st.session_state:
        n = get_num_mesas()
        st.session_state.ordenes_mesas = {
            i: _orden_vacia() for i in range(1, n + 1)
        }
        st.session_state.ordenes_mesas[LLEVAR_KEY] = _orden_vacia()
    if "mesa_actual" not in st.session_state:
        st.session_state.mesa_actual = 1
    if "cocina_queue" not in st.session_state:
        st.session_state.cocina_queue = []
    if "ventas_sesion" not in st.session_state:
        st.session_state.ventas_sesion = 0
    if "ordenes_sesion" not in st.session_state:
        st.session_state.ordenes_sesion = 0
    if "notificaciones" not in st.session_state:
        st.session_state.notificaciones = []


def _orden_vacia():
    return {
        "items": [],           # [{nombre, precio, cantidad, nota, enviado}]
        "mesero": None,
        "hora_apertura": None,
        "forma_pago": "Efectivo",
    }


def _item_vacio(nombre, precio):
    return {"nombre": nombre, "precio": precio, "cantidad": 1,
            "nota": "", "enviado": False}


def get_orden(mesa):
    init_session()
    return st.session_state.ordenes_mesas[mesa]


def agregar_item(mesa, nombre, precio):
    init_session()
    orden = st.session_state.ordenes_mesas[mesa]
    usuario = st.session_state.usuario
    if not orden["mesero"] and usuario:
        orden["mesero"] = usuario["nombre"]
    if not orden["hora_apertura"]:
        orden["hora_apertura"] = datetime.now().strftime("%H:%M")
    # Si ya existe y aún no se envió, solo sube cantidad
    for item in orden["items"]:
        if item["nombre"] == nombre and not item["enviado"]:
            item["cantidad"] += 1
            return
    # Si existe pero ya se envió, agrega nueva línea sin enviar
    for item in orden["items"]:
        if item["nombre"] == nombre and item["enviado"]:
            orden["items"].append(_item_vacio(nombre, precio))
            return
    orden["items"].append(_item_vacio(nombre, precio))


def quitar_item(mesa, idx, delta=-1):
    init_session()
    items = st.session_state.ordenes_mesas[mesa]["items"]
    if 0 <= idx < len(items):
        if items[idx]["enviado"]:
            return  # no se pueden quitar items ya enviados a cocina
        items[idx]["cantidad"] += delta
        if items[idx]["cantidad"] <= 0:
            items.pop(idx)


def eliminar_item_enviado(mesa, idx):
    """Elimina un item aunque ya esté enviado (requiere confirmación en UI)."""
    init_session()
    items = st.session_state.ordenes_mesas[mesa]["items"]
    if 0 <= idx < len(items):
        items.pop(idx)


def actualizar_nota(mesa, idx, nota):
    init_session()
    items = st.session_state.ordenes_mesas[mesa]["items"]
    if 0 <= idx < len(items):
        items[idx]["nota"] = nota


def get_total(mesa):
    init_session()
    return sum(i["precio"] * i["cantidad"] for i in st.session_state.ordenes_mesas[mesa]["items"])


def enviar_cocina(mesa):
    """Solo envía los items que NO han sido enviados antes (incremental)."""
    init_session()
    orden = st.session_state.ordenes_mesas[mesa]
    pendientes = [i for i in orden["items"] if not i["enviado"]]
    if not pendientes:
        return "nada_nuevo"
    mesero = orden["mesero"] or "Sin asignar"
    etiqueta = "Para llevar" if mesa == LLEVAR_KEY else f"Mesa {mesa}"
    snapshot = {
        "mesa": mesa,
        "etiqueta": etiqueta,
        "mesero": mesero,
        "hora": datetime.now().strftime("%H:%M"),
        "items": [dict(i) for i in pendientes],
        "estado": "pendiente",
    }
    st.session_state.cocina_queue.append(snapshot)
    # Marcar como enviados
    for item in orden["items"]:
        if not item["enviado"]:
            item["enviado"] = True
    return True


def cerrar_mesa(mesa, pago, forma_pago="Efectivo"):
    init_session()
    from utils.db import guardar_orden, cerrar_orden_db
    orden = st.session_state.ordenes_mesas[mesa]
    total = get_total(mesa)
    cambio = pago - total if forma_pago == "Efectivo" else 0
    if forma_pago == "Efectivo" and cambio < 0:
        return False, 0
    mesero = orden["mesero"] or "Sin asignar"
    etiqueta = "Para llevar" if mesa == LLEVAR_KEY else str(mesa)
    guardar_orden(etiqueta, mesero, orden["items"], orden["hora_apertura"] or "", forma_pago)
    if mesa != LLEVAR_KEY:
        cerrar_orden_db(mesa)
    st.session_state.ventas_sesion += total
    st.session_state.ordenes_sesion += 1
    st.session_state.ordenes_mesas[mesa] = _orden_vacia()
    st.session_state.cocina_queue = [
        q for q in st.session_state.cocina_queue if q["mesa"] != mesa
    ]
    return True, cambio


def get_mesas_ocupadas():
    init_session()
    return [m for m, o in st.session_state.ordenes_mesas.items()
            if o["items"] and m != LLEVAR_KEY]


def mesa_bloqueada(mesa):
    init_session()
    orden = st.session_state.ordenes_mesas.get(mesa)
    if orden and orden["items"] and orden["mesero"]:
        return orden["mesero"]
    return None


def mis_mesas(nombre_mesero):
    init_session()
    return [m for m, o in st.session_state.ordenes_mesas.items()
            if o["mesero"] == nombre_mesero and o["items"] and m != LLEVAR_KEY]


def agregar_notificacion(para_mesero, mensaje, tipo="info"):
    init_session()
    st.session_state.notificaciones.append({
        "para": para_mesero,
        "mensaje": mensaje,
        "tipo": tipo,
        "hora": datetime.now().strftime("%H:%M"),
    })


def mis_notificaciones(nombre_mesero):
    init_session()
    return [n for n in st.session_state.notificaciones if n["para"] == nombre_mesero]


def limpiar_notificaciones(nombre_mesero):
    init_session()
    st.session_state.notificaciones = [
        n for n in st.session_state.notificaciones if n["para"] != nombre_mesero
    ]
