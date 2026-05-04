# 📊 Sistema de Facturación Automatizado

Aplicación web que automatiza la **extracción, procesamiento y visualización de facturas electrónicas** a partir de correos electrónicos, permitiendo generar reportes en Excel de forma rápida y eficiente.

---

## 🚀 Descripción General

Este sistema se conecta a una cuenta de correo electrónico, identifica archivos relacionados con facturación (XML, ZIP o contenido embebido en correos `.eml`), procesa la información relevante y la presenta en un dashboard interactivo.

Además, permite filtrar la información por rango de fechas y exportar los resultados en formato Excel.

---

## ⚙️ Tecnologías Utilizadas

### Backend

* Python
* Flask
* Pandas
* IMAP (lectura de correos)
* XML (ElementTree)

### Frontend

* HTML5
* CSS3
* JavaScript 

### Infraestructura

* Render (Deploy Backend)
* GitHub (Control de versiones)

---

## 🧠 Funcionamiento del Sistema

El sistema sigue el siguiente flujo:

1. 📩 Conexión al correo mediante IMAP
2. 🔍 Filtrado de correos por rango de fechas
3. 📧 Procesamiento del contenido del correo (.eml)
4. 📄 Detección de archivos XML:

   * XML adjunto
   * XML embebido (CDATA)
5. 📦 En caso de no encontrar XML → extracción desde ZIP
6. 🧾 Lectura y parsing del XML
7. 📊 Extracción de datos relevantes:

   * Empresa
   * NIT
   * Cliente
   * Fecha
   * Total
8. 🧠 Eliminación de duplicados
9. 📁 Generación de archivo Excel
10. 🌐 Visualización en el dashboard

---

## 📅 Filtro por Fechas

El sistema permite consultar facturas dentro de un rango específico:

```
/procesar?inicio=YYYY-MM-DD&fin=YYYY-MM-DD
```

Ejemplo:

```
/procesar?inicio=2026-05-01&fin=2026-05-05
```

> ⚠️ Nota: El parámetro `fin` es exclusivo, por lo que internamente se ajusta automáticamente.

---

## 📊 Funcionalidades Principales

* ✔️ Lectura automática de correos electrónicos
* ✔️ Procesamiento de XML (incluyendo CDATA)
* ✔️ Soporte para archivos ZIP
* ✔️ Eliminación de facturas duplicadas
* ✔️ Filtro por rango de fechas
* ✔️ Dashboard interactivo
* ✔️ Exportación a Excel

---

## 📁 Estructura del Proyecto

```
project/
│
├── project.py              # Backend (Flask)
├── script.js              # Lógica frontend
├── index.html             # Interfaz principal
├── styles.css             # Estilos
├── requirements.txt       # Dependencias
├── .gitignore
└── README.md
```

---

## 🔐 Variables de Entorno

Para el correcto funcionamiento, se deben configurar:

```env
EMAIL=tu_correo@gmail.com
PASSWORD=tu_contraseña_o_app_password
```

> ⚠️ Se recomienda usar contraseñas de aplicación (App Passwords).

---

## 📦 Instalación Local

```bash
git clone <repo-url>
cd project

pip install -r requirements.txt
python project.py
```

---

## 🌐 Despliegue

El backend se encuentra desplegado en Render.

Para desplegar:

1. Conectar repositorio en GitHub
2. Configurar variables de entorno
3. Definir:

   * Build Command: `pip install -r requirements.txt`
   * Start Command: `python project.py`

---

## 📈 Posibles Mejoras

* 🔄 Procesamiento en segundo plano (background jobs)
* 🗄️ Integración con base de datos (MongoDB / PostgreSQL)
* 📊 Dashboard con gráficas (Chart.js o similar)
* 🔐 Autenticación de usuarios
* ⚡ Optimización de rendimiento (caching)

---

## 👨‍💻 Autor

Desarrollado por Juan José Abril
Proyecto enfocado en automatización de procesos contables y manejo de datos.

---
