import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, date

# ─── CONEXIÓN A GOOGLE SHEETS ────────────────────────────────────────────────
# Esta línea usa los "Secrets" que pegaste en Streamlit Cloud
conn = st.connection("gsheets", type=GSheetsConnection)

# ─── CONFIGURACIÓN INICIAL ──────────────────────────────────────────────────
ADMIN_PIN = "0000"

def init_db():
    """Verifica si las hojas existen, si no, podrías crearlas manualmente en Drive"""
    # En Google Sheets, es mejor crear las pestañas (Menu, Ordenes, etc.) 
    # directamente en el navegador para asegurar el formato.
    pass

# ─── MENÚ ────────────────────────────────────────────────────────────────────

def get_menu():
    # Lee la pestaña 'Menu' de tu Google Sheet
    df = conn.read(worksheet="Menu")
    menu = {}
    for _, row in df.iterrows():
        cat, prod, precio = row['Categoria'], row['Producto'], row['Precio']
        if cat not in menu:
            menu[cat] = []
        menu[cat].append({"nombre": prod, "precio": int(precio or 0)})
    return menu

def add_menu_item(cat, nombre, precio):
    df = conn.read(worksheet="Menu")
    nuevo_item = pd.DataFrame([{"Categoria": cat, "Producto": nombre, "Precio": precio}])
    df = pd.concat([df, nuevo_item], ignore_index=True)
    conn.update(worksheet="Menu", data=df)

# ─── MESEROS ─────────────────────────────────────────────────────────────────

def get_meseros():
    df = conn.read(worksheet="Meseros")
    meseros = []
    for _, row in df.iterrows():
        meseros.append({"nombre": row['Nombre'], "pin": str(row['PIN']), "activo": row['Activo']})
    return meseros

def get_admin_pin():
    df = conn.read(worksheet="Config")
    # Busca el valor donde la clave sea admin_pin
    pin = df[df['Clave'] == 'admin_pin']['Valor'].values
    return str(pin[0]) if len(pin) > 0 else ADMIN_PIN

# ─── ÓRDENES (EL CORAZÓN DEL NEGOCIO) ────────────────────────────────────────

def get_next_id():
    df = conn.read(worksheet="Ordenes")
    if df.empty or 'ID' not in df.columns:
        return 1
    return int(df['ID'].max()) + 1

def guardar_orden(mesa, mesero, items, hora_apertura, forma_pago="Efectivo"):
    df_actual = conn.read(worksheet="Ordenes")
    oid = get_next_id()
    hoy = date.today().isoformat()
    
    nuevas_filas = []
    for item in items:
        subtotal = item["precio"] * item["cantidad"]
        nuevas_filas.append({
            "ID": oid, "Fecha": hoy, "Mesa": mesa, "Mesero": mesero,
            "Producto": item["nombre"], "Precio_unit": item["precio"], 
            "Cantidad": item["cantidad"], "Subtotal": subtotal,
            "Estado": "abierta", "Hora_apertura": hora_apertura, 
            "Hora_cierre": None, "Forma_pago": forma_pago, "Nota": item.get("nota", "")
        })
    
    df_nuevo = pd.concat([df_actual, pd.DataFrame(nuevas_filas)], ignore_index=True)
    conn.update(worksheet="Ordenes", data=df_nuevo)
    return oid

def cerrar_orden_db(mesa):
    df = conn.read(worksheet="Ordenes")
    ahora = datetime.now().strftime("%H:%M")
    hoy = date.today().isoformat()
    
    # Cambia el estado a cerrada para la mesa activa de hoy
    mask = (df['Mesa'].astype(str) == str(mesa)) & (df['Estado'] == 'abierta') & (df['Fecha'] == hoy)
    df.loc[mask, 'Estado'] = 'cerrada'
    df.loc[mask, 'Hora_cierre'] = ahora
    
    conn.update(worksheet="Ordenes", data=df)

# ─── REPORTES ────────────────────────────────────────────────────────────────

def get_ventas_hoy():
    df = conn.read(worksheet="Ordenes")
    hoy = date.today().isoformat()
    
    df_hoy = df[(df['Fecha'] == hoy) & (df['Estado'] == 'cerrada')]
    total = df_hoy['Subtotal'].sum()
    num_ordenes = df_hoy['ID'].nunique()
    
    ventas_mesero = df_hoy.groupby('Mesero')['Subtotal'].sum().to_dict()
    return total, num_ordenes, ventas_mesero
