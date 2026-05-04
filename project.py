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
from PyPDF2 import PdfReader
from docx import Document
import re

app = Flask(__name__)
CORS(app)

EMAIL = os.environ.get("EMAIL")
PASSWORD = os.environ.get("PASSWORD")
IMAP_SERVER = "imap.gmail.com"

CARPETA = "facturas"
ARCHIVO_EXCEL = "reporte_facturas.xlsx"


# ----------------------------
# 🔧 UTILIDADES
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
        if not valor:
            return 0

        valor = valor.strip()

        if "," in valor and "." in valor:
            valor = valor.replace(",", "")
        elif "," in valor:
            valor = valor.replace(".", "").replace(",", ".")

        return float(valor)

    except:
        return 0


def clasificar_texto(texto):
    texto = texto.lower()

    if "cuenta de cobro" in texto:
        return "Cuenta de Cobro"

    if "factura" in texto:
        return "Factura"

    return "Desconocido"


# ----------------------------
# XML
# ----------------------------

def obtener_root_real(root):
    for elem in root.iter():
        if limpiar_tag(elem.tag) == "description":
            if elem.text and ("<Invoice" in elem.text or "<CreditNote" in elem.text):
                try:
                    return ET.fromstring(elem.text.strip())
                except:
                    pass
    return root


def buscar_total(root):
    for elem in root.iter():
        if limpiar_tag(elem.tag) == "payableamount":
            return limpiar_numero(elem.text)

    for elem in root.iter():
        if limpiar_tag(elem.tag) == "taxinclusiveamount":
            return limpiar_numero(elem.text)

    return 0


# ----------------------------
# PDF
# ----------------------------

def procesar_pdf(ruta_pdf):
    datos = []

    try:
        reader = PdfReader(ruta_pdf)
        texto = ""

        for page in reader.pages:
            texto += (page.extract_text() or "") + "\n"

        tipo = clasificar_texto(texto)

        matches = re.findall(r'\$?\s*([\d.,]+)', texto)

        if matches:
            total = limpiar_numero(matches[-1])

            datos.append({
                "Tipo": tipo,
                "ID_Factura": f"PDF_{os.path.basename(ruta_pdf)}",
                "Empresa": "PDF",
                "NIT": "",
                "Cliente": "",
                "Fecha": "",
                "Ciudad": "",
                "Total": total,
                "Subtotal": 0,
                "Total_Impuestos": 0,
                "Moneda": "COP"
            })

    except Exception as e:
        print("Error PDF:", e)

    return datos


# ----------------------------
# DOCX
# ----------------------------

def procesar_docx(ruta_docx):
    datos = []

    try:
        doc = Document(ruta_docx)

        texto = "\n".join([p.text for p in doc.paragraphs])

        tipo = clasificar_texto(texto)

        matches = re.findall(r'Total a Pagar.*?\$([\d.,]+)', texto)

        for i, m in enumerate(matches):
            datos.append({
                "Tipo": tipo,
                "ID_Factura": f"DOCX_{i}",
                "Empresa": "CAJASAN",
                "NIT": "",
                "Cliente": "",
                "Fecha": "",
                "Ciudad": "",
                "Total": limpiar_numero(m),
                "Subtotal": 0,
                "Total_Impuestos": 0,
                "Moneda": "COP"
            })

    except Exception as e:
        print("Error DOCX:", e)

    return datos


# ----------------------------
# PROCESAR CORREOS
# ----------------------------

def procesar_correos():
    datos = []

    if os.path.exists(CARPETA):
        shutil.rmtree(CARPETA)
    os.makedirs(CARPETA, exist_ok=True)

    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL, PASSWORD)
    mail.select("inbox")

    status, mensajes = mail.search(None, 'ALL')
    ids = mensajes[0].split()

    for num in ids:
        status, data = mail.fetch(num, "(RFC822)")

        for response in data:
            if isinstance(response, tuple):
                msg = email.message_from_bytes(response[1])

                xml_encontrado = False

                for part in msg.walk():
                    filename = part.get_filename()

                    if filename:

                        # XML
                        if filename.lower().endswith(".xml"):
                            ruta = os.path.join(CARPETA, filename)

                            with open(ruta, "wb") as f:
                                f.write(part.get_payload(decode=True))

                            xml_encontrado = True

                        # ZIP
                        elif filename.lower().endswith(".zip"):
                            ruta_zip = os.path.join(CARPETA, filename)

                            with open(ruta_zip, "wb") as f:
                                f.write(part.get_payload(decode=True))

                            with zipfile.ZipFile(ruta_zip, 'r') as zip_ref:
                                zip_ref.extractall(CARPETA)

                        # PDF
                        elif filename.lower().endswith(".pdf"):
                            ruta_pdf = os.path.join(CARPETA, filename)

                            with open(ruta_pdf, "wb") as f:
                                f.write(part.get_payload(decode=True))

                            datos.extend(procesar_pdf(ruta_pdf))

                        # DOCX
                        elif filename.lower().endswith(".docx"):
                            ruta_docx = os.path.join(CARPETA, filename)

                            with open(ruta_docx, "wb") as f:
                                f.write(part.get_payload(decode=True))

                            datos.extend(procesar_docx(ruta_docx))

    # XML
    for root_dir, dirs, files in os.walk(CARPETA):
        for file in files:
            if file.endswith(".xml"):
                ruta_xml = os.path.join(root_dir, file)

                try:
                    tree = ET.parse(ruta_xml)
                    root = tree.getroot()

                    root = obtener_root_real(root)

                    datos.append({
                        "Tipo": "Factura",
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

    # Excel
    if datos:
        df = pd.DataFrame(datos)
        df.drop_duplicates(subset=["ID_Factura", "Total"], inplace=True)
        df.to_excel(ARCHIVO_EXCEL, index=False)

    return datos


# ----------------------------
# API
# ----------------------------

@app.route("/procesar")
def procesar():
    return jsonify(procesar_correos())


@app.route("/descargar")
def descargar():
    return send_file(ARCHIVO_EXCEL, as_attachment=True)


# ----------------------------
# RUN
# ----------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)