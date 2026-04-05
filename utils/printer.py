"""
Impresión de tickets para impresora térmica Bluetooth (58mm / 80mm)
Compatible con impresoras ESC/POS como la mostrada (Bluetooth + USB)

Instalación requerida:
    pip install python-escpos

Para Bluetooth en Linux/Mac:
    pip install python-escpos[bt]
    
Para USB:
    pip install python-escpos[usb]
"""

from datetime import datetime

NEGOCIO = "BARBACOA TÍO Gor"
DIRECCION = "Tu dirección aquí"
TEL = "Tel: 000-000-0000"
TICKET_WIDTH = 32  # caracteres para 58mm


def _linea(char="-", n=TICKET_WIDTH):
    return char * n


def _centrar(texto, n=TICKET_WIDTH):
    return texto.center(n)


def _izq_der(izq, der, n=TICKET_WIDTH):
    espacio = n - len(izq) - len(der)
    if espacio < 1:
        espacio = 1
    return izq + " " * espacio + der


def generar_texto_ticket(mesa, mesero, items, total, pago, cambio, folio=None, forma_pago="Efectivo"):
    """Genera el texto plano del ticket para previsualización o impresión."""
    ahora = datetime.now()
    fecha = ahora.strftime("%d/%m/%Y %H:%M")
    folio_str = f"#{folio}" if folio else ""
    etiqueta = str(mesa)

    lineas = [
        _centrar(NEGOCIO),
        _centrar(DIRECCION),
        _centrar(TEL),
        _linea(),
        _centrar(f"{etiqueta}  {folio_str}"),
        f"Fecha: {fecha}",
        f"Mesero: {mesero}",
        f"Pago: {forma_pago}",
        _linea(),
        _izq_der("PRODUCTO", "TOTAL"),
        _linea("-"),
    ]

    for item in items:
        nombre = item["nombre"][:20]
        cant = item["cantidad"]
        precio = item["precio"]
        sub = cant * precio
        nota = item.get("nota", "") or ""
        lineas.append(f"{cant}x {nombre}")
        if nota:
            lineas.append(f"  * {nota[:28]}")
        lineas.append(_izq_der(f"  ${precio} c/u", f"${sub:,.0f}"))

    lineas += [
        _linea(),
        _izq_der("TOTAL:", f"${total:,.0f}"),
    ]

    if forma_pago == "Efectivo":
        lineas += [
            _izq_der("Pago:", f"${pago:,.0f}"),
            _izq_der("Cambio:", f"${cambio:,.0f}"),
        ]

    lineas += [
        _linea(),
        _centrar("¡Gracias por su preferencia!"),
        _centrar("Vuelva pronto"),
        "",
        "",
    ]

    return "\n".join(lineas)


def imprimir_ticket_bluetooth(texto_ticket, mac_address=None):
    """
    Imprime por Bluetooth. Requiere python-escpos instalado.
    mac_address: dirección MAC de la impresora, ej: "AA:BB:CC:DD:EE:FF"
    """
    try:
        from escpos.printer import Bluetooth
        if not mac_address:
            return False, "No se configuró la dirección MAC de la impresora."
        p = Bluetooth(mac_address)
        p.set(align="center", bold=True, height=2, width=2)
        p.text(NEGOCIO + "\n")
        p.set(align="left", bold=False, height=1, width=1)
        p.text(texto_ticket)
        p.cut()
        return True, "Ticket impreso correctamente."
    except ImportError:
        return False, "python-escpos no está instalado. Ejecuta: pip install python-escpos[bt]"
    except Exception as e:
        return False, f"Error al imprimir: {e}"


def imprimir_ticket_usb(texto_ticket, vendor_id=None, product_id=None):
    """
    Imprime por USB. Requiere python-escpos instalado.
    vendor_id / product_id se encuentran con: lsusb (Linux) o gestor de dispositivos (Windows)
    """
    try:
        from escpos.printer import Usb
        vid = vendor_id or 0x0416
        pid = product_id or 0x5011
        p = Usb(vid, pid)
        p.set(align="center", bold=True, height=2, width=2)
        p.text(NEGOCIO + "\n")
        p.set(align="left", bold=False, height=1, width=1)
        p.text(texto_ticket)
        p.cut()
        return True, "Ticket impreso por USB."
    except ImportError:
        return False, "python-escpos no está instalado. Ejecuta: pip install python-escpos[usb]"
    except Exception as e:
        return False, f"Error al imprimir: {e}"
