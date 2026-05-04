let datosGlobal = [];

const BASE_URL = "https://project-cajasan.onrender.com";

async function ejecutarPython() {
    try {
        const inicio = document.getElementById("fechaInicio").value;
        const fin = document.getElementById("fechaFin").value;

        if (!inicio || !fin) {
            alert("Selecciona ambas fechas");
            return;
        }

        const res = await fetch(`${BASE_URL}/procesar?inicio=${inicio}&fin=${fin}`);
        const data = await res.json();

        datosGlobal = data;

        renderTabla(data);
        calcularTotal(data);

    } catch (error) {
        console.error(error);
        alert("Error cargando datos");
    }
}

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

function calcularTotal(data) {
    let total = 0;

    data.forEach(f => {
        total += Number(f.Total) || 0;
    });

    document.getElementById("totalGeneral").textContent = formatearNumero(total);
}

function descargarExcel() {
    window.location.href = `${BASE_URL}/descargar`;
}

function formatearNumero(num) {
    return new Intl.NumberFormat('es-CO').format(num || 0);
}