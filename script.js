let datosGlobal = [];

const BASE_URL = "https://project-cajasan.onrender.com";

// 🔥 Ejecutar consulta por fechas
async function ejecutarPython() {
    try {
        const inicio = document.getElementById("fechaInicio").value;
        const fin = document.getElementById("fechaFin").value;

        if (!inicio || !fin) {
            alert("Selecciona ambas fechas");
            return;
        }

        const res = await fetch(`${BASE_URL}/procesar?inicio=${inicio}&fin=${fin}`);

        if (!res.ok) {
            throw new Error("Error en la API");
        }

        const data = await res.json();

        datosGlobal = data;

        renderTabla(data);
        calcularTotal(data);

    } catch (error) {
        console.error("Error:", error);
        alert("Error cargando los datos");
    }
}

// 🔥 Renderizar tabla
function renderTabla(data) {
    const tbody = document.getElementById("tabla");
    tbody.innerHTML = "";

    if (data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7">No hay datos</td></tr>`;
        return;
    }

    data.forEach(f => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${f.ID_Factura || "-"}</td>
            <td>${f.Empresa || "-"}</td>
            <td>${f.NIT || "-"}</td>
            <td>${f.Cliente || "-"}</td>
            <td>${f.Fecha || "-"}</td>
            <td>${f.Ciudad || "-"}</td>
            <td>$${formatearNumero(f.Total)}</td>
        `;

        tbody.appendChild(row);
    });
}

// 🔥 Calcular total
function calcularTotal(data) {
    let total = 0;

    data.forEach(f => {
        total += Number(f.Total) || 0;
    });

    document.getElementById("totalGeneral").textContent = formatearNumero(total);
}

// 🔥 Normalizar texto (para tildes)
function normalizar(texto) {
    return texto
        ? texto.toLowerCase()
              .normalize("NFD")
              .replace(/[\u0300-\u036f]/g, "")
        : "";
}

// 🔥 Buscador
function filtrar() {
    const texto = normalizar(document.getElementById("buscador").value);

    // si está vacío → mostrar todo
    if (!texto) {
        renderTabla(datosGlobal);
        calcularTotal(datosGlobal);
        return;
    }

    const filtrados = datosGlobal.filter(f =>
        normalizar(f.Empresa).includes(texto) ||
        normalizar(f.NIT).includes(texto) ||
        normalizar(f.Cliente).includes(texto)
    );

    renderTabla(filtrados);
    calcularTotal(filtrados);
}

// 🔥 Descargar Excel
function descargarExcel() {
    window.location.href = `${BASE_URL}/descargar`;
}

// 🔥 Formatear números
function formatearNumero(num) {
    return new Intl.NumberFormat('es-CO').format(num || 0);
}