import socket              # Manejo de conexiones de red (UDP)
import json                # Conversión entre texto JSON y diccionarios Python
import threading           # Permite ejecutar tareas en paralelo (hilos)
import time                # Manejo de tiempo y timestamps
from flask import Flask, jsonify, render_template_string  # Framework web ligero

# =====================================================
# CONFIGURACIÓN UDP
# =====================================================
UDP_IP = "0.0.0.0"          # Escuchar UDP en todas las interfaces de red
UDP_PORT = 4210             # Puerto UDP (debe coincidir con el cliente)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Crear socket UDP (IPv4)
sock.bind((UDP_IP, UDP_PORT))                             # Asociar el socket a IP y puerto

print(f"📡 Escuchando UDP en puerto {UDP_PORT}")          # Confirmación en consola

# =====================================================
# VARIABLE COMPARTIDA
# =====================================================
ultimo_estado = {           # Diccionario que almacena el último estado recibido
    "temp_measured": 0.0,   # Temperatura medida
    "temp_ref": 0.0,        # Temperatura de referencia
    "light": 0,             # Nivel de luz
    "system": 0,            # Estado del sistema (on/off)
    "servo": 0,             # Posición del servo
    "led": "OFF",           # Estado del LED
    "ts": 0                 # Timestamp del último dato recibido
}

# =====================================================
# HILO UDP
# =====================================================
def udp_listener():
    global ultimo_estado     # Permite modificar la variable global
    while True:              # Escucha UDP de forma continua
        try:
            data, addr = sock.recvfrom(1024)  # Recibir paquete UDP (máx 1024 bytes)
            estado = json.loads(data.decode())# Decodificar JSON recibido
            estado["ts"] = time.time()         # Agregar timestamp actual
            ultimo_estado = estado              # Actualizar estado global
            print("📥 UDP recibido:", ultimo_estado)  # Log en consola
        except Exception as e:
            print("❌ Error UDP:", e)            # Manejo de errores UDP

# =====================================================
# FLASK
# =====================================================
app = Flask(__name__)        # Crear aplicación Flask

@app.get("/data")            # Endpoint HTTP GET /data
def data():
    return jsonify(ultimo_estado)  # Enviar último estado en formato JSON

HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sistema Ambiental</title>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

<style>
body {
    font-family: Arial, sans-serif;
    background: #f2f2f2;
    padding: 20px;
}
h2 { margin-bottom: 15px; }

.grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 15px;
}

.card {
    background: white;
    padding: 14px;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.12);
}

.title {
    font-weight: bold;
    font-size: 0.9em;
    margin-bottom: 6px;
}

.big { font-size: 1.6em; }

.badge {
    display: inline-block;
    padding: 6px 18px;
    border-radius: 20px;
    font-weight: bold;
    color: white;
}
.green { background: #2ECC71; }
.red { background: #CC2E2E; }

/* BARRAS */
.progress {
    width: 100%;
    height: 14px;
    background: #ddd;
    border-radius: 8px;
    position: relative;
    margin-top: 8px;
}

/* Barra Temperatura Medida */
.fill {
    height: 100%;
    background: #00D4FF;
    border-radius: 8px;
}

/* Barra Nivel de luz */
.fill-light {
    height: 100%;
    background: #000000;
    border-radius: 8px;
}

/* Marcadores */
.marker {
    position: absolute;
    top: -4px;
    width: 3px;
    height: 22px;
}
.marker-blue   { background: #0023F5; }
.marker-yellow { background: #FFE300; }
.marker-green  { background: #00FF2E; }

/* Tarjeta LED Activo */
.led-oval {
    display: inline-block;
    padding: 8px 30px;
    border-radius: 30px;
    font-weight: bold;
    color: white;
}
.rojo { background: #F2001B; }
.amarillo { background: #FFE300; }
.verde { background: #00FF2E; }
.off { background: #000000; 
}

canvas {
    width: 100% !important;
    height: 100% !important;
}

.footer {
    margin-top: 18px;
    font-size: 0.85em;
    color: #555;
}
</style>
</head>

<body>

<h2>Sistema de Monitoreo Ambiental</h2>

<div class="grid">

<!-- FILA 1 -->
<div class="card" style="grid-column: 1 / 2;">
    <div class="title">Estado del sistema</div><br>
    <div id="systemBadge" class="badge">--</div>
</div>

<!-- FILA 2 -->
<div class="card" style="grid-column: 1 / 2;">
    <div class="title">Temperatura referencia</div>
    <div class="big"><span id="tr">--</span> °C</div>
</div>

<div class="card" style="grid-column: 2 / 5;">
    <div class="title">Temperatura medida</div>
    <div class="big"><span id="tm">--</span> °C</div>
    <div class="progress">
        <div id="tempBar" class="fill"></div>
        <div id="tempRef" class="marker marker-blue"></div>
    </div>
</div>

<div class="card" style="grid-column: 5 / 6;">
    <div class="title">Servo</div>
    <div class="big"><span id="servo">--</span> °</div>
    <div id="servoText">--</div>
</div>

<!-- FILA 3 -->
<div class="card" style="grid-column: 1 / 2;">
    <div class="title">LED activo</div><br>
    <div id="led" class="led-oval">--</div>
</div>

<div class="card" style="grid-column: 2 / 5;">
    <div class="title">Nivel de luz</div>
    <div class="big"><span id="light">--</span></div>
    <div class="progress">
        <div id="lightBar" class="fill-light"></div>
        <div id="lightYellow" class="marker marker-yellow"></div>
        <div id="lightGreen" class="marker marker-green"></div>
    </div>
</div>

<!-- FILAS 4–6 -->
<div class="card" style="grid-column: 1 / 3; grid-row: 4 / 7;">
    <div class="title">Temperatura vs Tiempo</div>
    <canvas id="tempChart"></canvas>
</div>

<div class="card" style="grid-column: 4 / 6; grid-row: 4 / 7;">
    <div class="title">Nivel de Luz vs Tiempo</div>
    <canvas id="lightChart"></canvas>
</div>

</div>

<div class="footer">
Última actualización: <span id="ts">--</span>
</div>

<script>
const labels = [];
const tempData = [];
const refData = [];
const lightData = [];

/* ---- Gráfica Temperatura ---- */
const tempChart = new Chart(document.getElementById("tempChart"), {
    type: "line",
    data: {
        labels,
        datasets: [
            {
                label: "Temperatura medida",
                data: tempData,
                borderColor: "#00D4FF",
                pointBackgroundColor: "#00D4FF",
                borderWidth: 2,
                tension: 0.3
            },
            {
                label: "Temperatura referencia",
                data: refData,
                borderColor: "#0023F5",
                borderDash: [6,6],
                pointRadius: 0
            }
        ]
    },
    options: {
        animation: false,
        scales: { y: { min: 0, max: 100, ticks: { stepSize: 10 } } }
    }
});

/* ---- Gráfica Luz ---- */
const lightChart = new Chart(document.getElementById("lightChart"), {
    type: "line",
    data: {
        labels,
        datasets: [
            { label: "Nivel de Luz", data: lightData, borderColor: "#000000", pointBackgroundColor: "#000000", borderWidth: 2, tension: 0.3 },
            { label: "Luz Media", data: Array(30).fill(1000), borderColor: "#FFE300", borderDash: [6,6], pointRadius: 0 },
            { label: "Luz Alta", data: Array(30).fill(3000), borderColor: "#00FF2E", borderDash: [6,6], pointRadius: 0 }
        ]
    },
    options: {
        animation: false,
        scales: { y: { min: 0, max: 4095, ticks: { stepSize: 500 } } }
    }
});

async function actualizar() {
    const r = await fetch("/data");
    const d = await r.json();

    const sistemaHabilitado = Number(d.system) === 1;

    /* ========= ESTADO DEL SISTEMA ========= */
    const sys = document.getElementById("systemBadge");
    if (sistemaHabilitado) {
        sys.textContent = "HABILITADO";
        sys.classList.remove("red");
        sys.classList.add("badge", "green");
    } else {
        sys.textContent = "DESHABILITADO";
        sys.classList.remove("green");
        sys.classList.add("badge", "red");
    }

    /* ========= VALORES (0 si está deshabilitado) ========= */
    const tempMedida = sistemaHabilitado ? d.temp_measured : 0;
    const tempRef    = sistemaHabilitado ? d.temp_ref      : 0;
    const luz        = sistemaHabilitado ? d.light         : 0;
    const servo      = sistemaHabilitado ? d.servo         : 0;

    /* ========= TEXTOS ========= */
    document.getElementById("tm").textContent = tempMedida.toFixed(1);
    document.getElementById("tr").textContent = tempRef.toFixed(1);
    document.getElementById("light").textContent = luz;
    document.getElementById("servo").textContent = servo;

    document.getElementById("servoText").textContent =
        servo === 0 ? "Ventilación Cerrada" : "Ventilación Abierta";

    /* ========= BARRA TEMPERATURA ========= */
    document.getElementById("tempBar").style.width =
        Math.min(tempMedida, 100) + "%";
    document.getElementById("tempRef").style.left =
        Math.min(tempRef, 100) + "%";

    /* ========= BARRA LUZ ========= */
    document.getElementById("lightBar").style.width =
        Math.min(luz, 4095) / 4095 * 100 + "%";
    document.getElementById("lightYellow").style.left = (1000 / 4095 * 100) + "%";
    document.getElementById("lightGreen").style.left = (3000 / 4095 * 100) + "%";

    /* ========= LED ========= */
    const led = document.getElementById("led");
    
    if (!sistemaHabilitado || d.led === "OFF") {
        led.textContent = "OFF";
        led.className = "led-oval off";
    } else {
        led.textContent = d.led;
        led.className = "led-oval " + d.led.toLowerCase();
    }

    /* ========= GRÁFICAS ========= */
    const now = new Date().toLocaleTimeString();
    labels.push(now);
    tempData.push(tempMedida);
    refData.push(tempRef);
    lightData.push(luz);

    if (labels.length > 30) {
        labels.shift();
        tempData.shift();
        refData.shift();
        lightData.shift();
    }

    tempChart.update();
    lightChart.update();

    document.getElementById("ts").textContent =
        new Date(d.ts * 1000).toLocaleTimeString();
}

setInterval(actualizar, 1000);
actualizar();
</script>

</body>
</html>
"""

@app.get("/")
def home():
    return render_template_string(HTML)

if __name__ == "__main__":
    threading.Thread(target=udp_listener, daemon=True).start()
    print("🌐 Servidor web activo en http://0.0.0.0:8000")
    app.run(host="0.0.0.0", port=8000, debug=False)