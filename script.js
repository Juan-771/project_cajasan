let datosGlobal = [];
let ultimoHash = "";

const BASE_URL = "https://tu-app.onrender.com";
await fetch(`${BASE_URL}/procesar`);
window.open(`${BASE_URL}/descargar`);

async function ejecutarPython() {
    try {
        const res = await fetch("http://127.0.0.1:5000/procesar");
        const data = await res.json();

        // 🔥 Detectar cambios reales
        const nuevoHash = JSON.stringify(data);

        if (nuevoHash === ultimoHash) {
            console.log("Sin cambios...");
            return;
        }

        console.log("Actualizando datos...");

        ultimoHash = nuevoHash;
        datosGlobal = data;

        renderTabla(data);
        calcularTotal(data);

    } catch (error) {
        console.error("Error:", error);
    }
}

function renderTabla(data) {
    const tbody = document.getElementById("tabla");
    tbody.innerHTML = ""; // limpiar sin recargar página

    data.forEach(f => {
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${f.ID_Factura}</td>
            <td>${f.Empresa}</td>
            <td>${f.NIT}</td>
            <td>${f.Cliente}</td>
            <td>${f.Fecha}</td>
            <td>${f.Ciudad}</td>
            <td>$${formatearNumero(f.Total)}</td>
        `;

        tbody.appendChild(row);
    });
}

function calcularTotal(data) {
    let total = 0;

    data.forEach(f => {
        total += parseFloat(f.Total || 0);
    });

    document.getElementById("totalGeneral").textContent = formatearNumero(total);
}

function filtrar() {
    const texto = document.getElementById("buscador").value.toLowerCase();

    const filtrados = datosGlobal.filter(f =>
        f.Empresa && f.Empresa.toLowerCase().includes(texto)
    );

    renderTabla(filtrados);
    calcularTotal(filtrados);
}

function descargarExcel() {
    window.open("http://127.0.0.1:5000/descargar");
}

function formatearNumero(num) {
    return new Intl.NumberFormat('es-CO').format(num);
}

// 🚀 Cargar una vez al inicio
ejecutarPython();