# 🌮 Barbacoa Tío R — Sistema POS

App de punto de venta para negocio de barbacoa.
Construida con Streamlit. Base de datos en Excel (`.xlsx`).

---

## Instalación

### 1. Requisitos previos
- Python 3.10 o superior
- pip

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Para impresión Bluetooth (impresora mini)
```bash
pip install "python-escpos[bt]"
```

### 4. Para impresión USB
```bash
pip install "python-escpos[usb]"
```

---

## Iniciar la app

```bash
cd barbacoa_app
streamlit run app.py
```

La app abre en tu navegador en `http://localhost:8501`

---

## Acceso

| Rol | Cómo entrar |
|-----|-------------|
| Mesero | Selecciona tu nombre → ingresa tu PIN |
| Admin | "Acceso administrador" → PIN: **0000** |

> Los PINs iniciales de meseros son: Ana=1111, Carlos=2222, Lupita=3333, Miguel=4444  
> Cámbialos desde el panel Admin antes de usar en producción.

---

## Estructura del proyecto

```
barbacoa_app/
├── app.py              ← Punto de entrada
├── requirements.txt
├── barbacoa_db.xlsx    ← Se crea automáticamente al primer arranque
├── utils/
│   ├── db.py           ← Lectura/escritura en Excel
│   ├── auth.py         ← Login con PIN
│   ├── nav.py          ← Navegación
│   ├── session.py      ← Estado de mesas en memoria
│   └── printer.py      ← Generación e impresión de tickets
└── pages/
    ├── mesas.py        ← Vista de mesas
    ├── orden.py        ← Tomar órdenes
    ├── cocina.py       ← Display de cocina
    ├── cobrar.py       ← Cobro y ticket
    ├── corte.py        ← Corte de caja y reportes
    └── admin.py        ← Panel administrador
```

---

## Hoja de datos (Excel)

El archivo `barbacoa_db.xlsx` se crea automáticamente con estas hojas:

| Hoja | Contenido |
|------|-----------|
| `Menu` | Categorías, productos y precios |
| `Meseros` | Nombres, PINs y estado activo/inactivo |
| `Ordenes` | Historial completo de todas las órdenes |
| `Cortes` | Registro de cada corte de caja |
| `Config` | PIN admin, número de mesas, nombre del negocio |

Puedes abrir este archivo en Excel en cualquier momento para ver el historial.

---

## Impresora Bluetooth

1. Enciende la impresora y emparéjala con la computadora o tablet
2. Busca su dirección MAC (formato: `AA:BB:CC:DD:EE:FF`)
3. En la app, ve a **Cobrar** → ingresa la MAC → imprime

---

## Cambiar precios

Admin → pestaña **Precios del menú** → modifica el precio → presiona 💾

Los cambios se aplican inmediatamente para todas las órdenes nuevas.
