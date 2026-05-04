import imaplib
import email
import zipfile
import os
import shutil
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime, timedelta
from flask import Flask, jsonify, send_file, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

EMAIL = os.environ.get("EMAIL")
PASSWORD = os.environ.get("PASSWORD")
IMAP_SERVER = "imap.gmail.com"

CARPETA = "facturas"
ARCHIVO_EXCEL = "reporte_facturas.xlsx"


# ----------------------------
# 🔧 FUNCIONES
# ----------------------------

def limpiar_tag(tag):
    return tag.split("}")[-1].lower()


def buscar(root, tag):
    for elem in root.iter():
        if limpiar_tag(elem.tag) == tag.lower():
            return elem.text
    return None


def limpiar_numero(valor):
    try:
        return float(valor)
    except:
        return 0


def formatear_fecha(fecha_str):
    fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
    return fecha.strftime("%d-%b-%Y")


def obtener_root_real(root):
    for elem in root.iter():
        if limpiar_tag(elem.tag) == "description":
            if elem.text and "<Invoice" in elem.text:
                try:
                    return ET.fromstring(elem.text.strip())
                except:
                    pass
    return root


def buscar_total(root):
    for elem in root.iter():
        tag = limpiar_tag(elem.tag)

        if tag in ["vlrpagarcop", "totalnetofacturacop"]:
            if elem.text and elem.text.strip():
                return limpiar_numero(elem.text)

    for elem in root.iter():
        if limpiar_tag(elem.tag) == "payableamount":
            if elem.text and elem.text.strip():
                return limpiar_numero(elem.text)

    for elem in root.iter():
        if limpiar_tag(elem.tag) == "taxinclusiveamount":
            if elem.text and elem.text.strip():
                return limpiar_numero(elem.text)

    return 0


# ----------------------------
# 📩 PROCESAR CORREOS
# ----------------------------

def procesar_correos(fecha_inicio=None, fecha_fin=None):
    datos = []

    if os.path.exists(CARPETA):
        shutil.rmtree(CARPETA)
    os.makedirs(CARPETA, exist_ok=True)

    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")

    if fecha_inicio and fecha_fin:
        since = formatear_fecha(fecha_inicio)

        fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d") + timedelta(days=1)
        before = fecha_fin_dt.strftime("%d-%b-%Y")

        criterio = f'(SINCE {since} BEFORE {before})'
        status, mensajes = mail.search(None, criterio)
    else:
        status, mensajes = mail.search(None, 'ALL')

    ids = mensajes[0].split()

    for num in ids:
        status, data = mail.fetch(num, "(RFC822)")

        for response in data:
            if isinstance(response, tuple):
                msg = email.message_from_bytes(response[1])

                xml_encontrado = False

                # 🔥 1. PROCESAR .EML
                for part in msg.walk():
                    content_type = part.get_content_type()
                    filename = part.get_filename()

                    # XML adjunto
                    if filename and filename.lower().endswith(".xml"):
                        ruta_xml = os.path.join(CARPETA, filename)

                        with open(ruta_xml, "wb") as f:
                            f.write(part.get_payload(decode=True))

                        xml_encontrado = True

                    # XML dentro del texto
                    if content_type == "text/plain":
                        try:
                            texto = part.get_payload(decode=True).decode(errors="ignore")

                            if "<Invoice" in texto:
                                ruta_xml = os.path.join(CARPETA, f"correo_{num.decode()}.xml")

                                with open(ruta_xml, "w", encoding="utf-8") as f:
                                    f.write(texto)

                                xml_encontrado = True

                        except:
                            pass

                # 📦 2. SI NO HAY XML → ZIP
                if not xml_encontrado:
                    for part in msg.walk():
                        filename = part.get_filename()

                        if filename and filename.lower().endswith(".zip"):
                            ruta_zip = os.path.join(CARPETA, filename)

                            with open(ruta_zip, "wb") as f:
                                f.write(part.get_payload(decode=True))

                            with zipfile.ZipFile(ruta_zip, 'r') as zip_ref:
                                zip_ref.extractall(CARPETA)

    # 🔍 LEER XML
    for root_dir, dirs, files in os.walk(CARPETA):
        for file in files:
            if file.endswith(".xml"):
                ruta_xml = os.path.join(root_dir, file)

                try:
                    tree = ET.parse(ruta_xml)
                    root = tree.getroot()

                    root = obtener_root_real(root)

                    datos.append({
                        "ID_Factura": buscar(root, "ID"),
                        "Empresa": buscar(root, "RegistrationName"),
                        "NIT": buscar(root, "CompanyID"),
                        "Cliente": buscar(root, "Name"),
                        "Fecha": buscar(root, "IssueDate"),
                        "Ciudad": buscar(root, "CityName"),
                        "Total": buscar_total(root),
                        "Subtotal": limpiar_numero(buscar(root, "TaxExclusiveAmount")),
                        "Total_Impuestos": limpiar_numero(buscar(root, "TaxAmount")),
                        "Moneda": buscar(root, "DocumentCurrencyCode")
                    })

                except Exception as e:
                    print("Error XML:", e)

    # 📊 GUARDAR SIN DUPLICADOS
    if datos:
        df_nuevo = pd.DataFrame(datos)

        if os.path.exists(ARCHIVO_EXCEL):
            df_existente = pd.read_excel(ARCHIVO_EXCEL)
            df_total = pd.concat([df_existente, df_nuevo], ignore_index=True)

            df_total.drop_duplicates(
                subset=["ID_Factura", "Empresa", "Total"],
                inplace=True
            )
        else:
            df_total = df_nuevo

        df_total.to_excel(ARCHIVO_EXCEL, index=False)

    return datos


# ----------------------------
# 🌐 API
# ----------------------------

@app.route("/procesar")
def procesar():
    inicio = request.args.get("inicio")
    fin = request.args.get("fin")

    if not inicio or not fin:
        datos = procesar_correos()
    else:
        datos = procesar_correos(inicio, fin)

    return jsonify(datos)


@app.route("/descargar")
def descargar():
    return send_file(ARCHIVO_EXCEL, as_attachment=True)


# ----------------------------
# 🚀 RUN
# ----------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)