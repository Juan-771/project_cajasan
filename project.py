import imaplib
import email
import zipfile
import os
import shutil
import xml.etree.ElementTree as ET
import pandas as pd
from flask import Flask, jsonify, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 🔐 VARIABLES DE ENTORNO (RENDER)
EMAIL = os.environ.get("EMAIL")
PASSWORD = os.environ.get("PASSWORD")
IMAP_SERVER = "imap.gmail.com"

CARPETA = "facturas"


# 🔍 FUNCIONES

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


def buscar_total(root):
    # 🔥 1. CustomTagGeneral (DIAN)
    for elem in root.iter():
        tag = limpiar_tag(elem.tag)

        if tag == "vlrpagarcop":
            return limpiar_numero(elem.text)

        if tag == "totalnetofacturacop":
            return limpiar_numero(elem.text)

    # 🔁 2. LegalMonetaryTotal
    for elem in root.iter():
        if limpiar_tag(elem.tag) == "legalmonetarytotal":

            payable = None
            tax_inclusive = None

            for child in elem:
                tag = limpiar_tag(child.tag)

                if tag == "payableamount":
                    payable = child.text

                elif tag == "taxinclusiveamount":
                    tax_inclusive = child.text

            total = payable if payable else tax_inclusive

            if total:
                return limpiar_numero(total)

    return 0


# 🔥 PROCESAR CORREOS
def procesar_correos():
    datos = []

    # 🧹 Limpiar carpeta
    if os.path.exists(CARPETA):
        shutil.rmtree(CARPETA)
    os.makedirs(CARPETA, exist_ok=True)

    # 📩 Conectar correo
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")

    # 🔥 SOLO ÚLTIMOS 10 CORREOS
    status, mensajes = mail.search(None, 'ALL')
    ids = mensajes[0].split()[-10:]

    for num in ids:
        status, data = mail.fetch(num, "(RFC822)")

        for response in data:
            if isinstance(response, tuple):
                msg = email.message_from_bytes(response[1])

                for part in msg.walk():
                    filename = part.get_filename()

                    if filename:
                        filename_lower = filename.lower()

                        # 📦 ZIP
                        if filename_lower.endswith(".zip"):
                            ruta_zip = os.path.join(CARPETA, filename)

                            with open(ruta_zip, "wb") as f:
                                f.write(part.get_payload(decode=True))

                            with zipfile.ZipFile(ruta_zip, 'r') as zip_ref:
                                zip_ref.extractall(CARPETA)

                        # 📄 XML
                        elif filename_lower.endswith(".xml"):
                            ruta_xml = os.path.join(CARPETA, filename)

                            with open(ruta_xml, "wb") as f:
                                f.write(part.get_payload(decode=True))

    # 🔍 LEER XML
    for root_dir, dirs, files in os.walk(CARPETA):
        for file in files:
            if file.endswith(".xml"):
                ruta_xml = os.path.join(root_dir, file)

                try:
                    tree = ET.parse(ruta_xml)
                    root = tree.getroot()

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
                    print("Error leyendo XML:", e)

    # 📊 EXCEL
    archivo_excel = "reporte_facturas.xlsx"

    if datos:
        df = pd.DataFrame(datos)
        df.drop_duplicates(subset=["ID_Factura"], inplace=True)
        df.to_excel(archivo_excel, index=False)

    return datos


# 🌐 API
@app.route("/procesar")
def procesar():
    datos = procesar_correos()
    return jsonify(datos)


@app.route("/descargar")
def descargar():
    return send_file("reporte_facturas.xlsx", as_attachment=True)


# 🚀 RUN (RENDER)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)