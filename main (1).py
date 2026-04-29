from machine import Pin, ADC, PWM          # Manejo de pines, ADC y PWM del ESP32
import network                             # Manejo de conexión WiFi
import socket                              # Comunicación por sockets (UDP)
import time                                # Temporización y control de tiempo

# ---------------------------------------------------
# CONFIGURACIÓN WIFI
# ---------------------------------------------------
SSID = "CLARO-BC8E"                        # Nombre de la red WiFi
PASSWORD = "Cy4aeUDu"                      # Contraseña de la red WiFi

wifi = network.WLAN(network.STA_IF)        # Configura/Prepara el ESP32 en modo estación (cliente)

# ---------------------------------------------------
# CONFIGURACIÓN UDP
# ---------------------------------------------------
PC_IP = "192.168.40.69"                   # IP del computador que recibe los datos
UDP_PORT = 4210                           # Puerto UDP de recepción en el computador

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Socket UDP

# ---------------------------------------------------
# HARDWARE
# ---------------------------------------------------
lm35 = ADC(Pin(35))                       # Sensor LM35 conectado al pin 35
lm35.atten(ADC.ATTN_11DB)                 # Atenuación para rango completo (0–3.3 V)

pot = ADC(Pin(34))                        # Potenciómetro en el pin 34 (referencia)
pot.atten(ADC.ATTN_11DB)                  # Atenuación 11 dB

ldr = ADC(Pin(32))                        # LDR (sensor de luz) en el pin 32
ldr.atten(ADC.ATTN_11DB)                  # Atenuación para lectura completa

led_R = Pin(27, Pin.OUT)                  # LED rojo conectado al pin 27
led_A = Pin(26, Pin.OUT)                  # LED amarillo conectado al pin 26
led_V = Pin(25, Pin.OUT)                  # LED verde conectado al pin 25

servo = PWM(Pin(18), freq=50)             # Servo conectado al pin 18 (50 Hz)

boton = Pin(33, Pin.IN, Pin.PULL_UP)      # Botón en pin 33 con pull-up interno
sistema_habilitado = True                 # Estado inicial del sistema
ultimo = 0                                # Variable para antirrebote

# ---------------------------------------------------
# FUNCIONES
# ---------------------------------------------------
def apagar_leds():
    led_R.off()                           # Apaga LED rojo
    led_A.off()                           # Apaga LED amarillo
    led_V.off()                           # Apaga LED verde

def mover_servo(grados):
    grados = max(0, min(180, grados))     # Limita el ángulo entre 0° y 180°
    duty = int(40 + (115 - 40) * grados / 180)  # Conversión grados → PWM
    servo.duty(duty)                      # Envía el PWM al servo

def irq_toggle(pin):
    global sistema_habilitado, ultimo
    ahora = time.ticks_ms()               # Tiempo actual en milisegundos
    if time.ticks_diff(ahora, ultimo) > 200:  # Antirrebote de 200 ms
        sistema_habilitado = not sistema_habilitado  # Cambia estado del sistema
        print("Sistema habilitado:", sistema_habilitado)
    ultimo = ahora                        # Actualiza el tiempo del último evento

boton.irq(trigger=Pin.IRQ_FALLING, handler=irq_toggle)  # Interrupción por pulsación

def leer_temperatura():
    adc = lm35.read()                     # Lee valor ADC del LM35
    volt = adc * 3.3 / 4095               # Convierte ADC a voltaje
    return volt * 100                     # Convierte voltaje a temperatura °C

def leer_referencia():
    adc = pot.read()                      # Lee potenciómetro
    return 25 + (adc / 4095) * 20         # Escala de 25 °C a 45 °C

def leer_luz():
    return ldr.read()                     # Lee nivel de luz (0–4095)

def controlar_leds(luz):
    apagar_leds()                         # Apaga todos los LEDs
    if luz > 3000:                        # Nivel de luz alto
        led_V.on()                        # Enciende LED verde
        return "VERDE"
    elif luz > 1000:                      # Nivel de luz medio
        led_A.on()                        # Enciende LED amarillo
        return "AMARILLO"
    else:                                 # Nivel de luz bajo
        led_R.on()                        # Enciende LED rojo
        return "ROJO"

# ---------------------------------------------------
# TIEMPOS
# ---------------------------------------------------
CONTROL_MS = 300                          # Periodo de control físico (ms)
ENVIO_MS   = 1000                         # Periodo de envío UDP (ms)

t_control = time.ticks_ms()               # Marca inicial de control
t_envio   = time.ticks_ms()               # Marca inicial de envío

# ---------------------------------------------------
# MAIN
# ---------------------------------------------------
print("Conectando WiFi...")
wifi.active(True)                         # Activa la interfaz WiFi
wifi.connect(SSID, PASSWORD)              # Conecta a la red WiFi

while not wifi.isconnected():             # Espera hasta conectar
    time.sleep(0.3)

print("WiFi conectado:", wifi.ifconfig()[0])  # Muestra IP asignada

temp = ref = luz = 0                      # Inicializa variables
servo_ang = 0                             # Ángulo del servo
led_estado = "OFF"                        # Estado del LED

while True:
    ahora = time.ticks_ms()               # Tiempo actual

    # -------- CONTROL FÍSICO --------
    if time.ticks_diff(ahora, t_control) >= CONTROL_MS:
        t_control = ahora

        if sistema_habilitado:
            temp = leer_temperatura()     # Lee temperatura
            ref  = leer_referencia()      # Lee referencia
            luz  = leer_luz()             # Lee nivel de luz

            if temp < ref:                # Comparación temperatura
                mover_servo(0)            # Ventilación cerrada
                servo_ang = 0
            else:
                mover_servo(180)          # Ventilación abierta
                servo_ang = 180

            led_estado = controlar_leds(luz)  # Controla LEDs
        else:
            mover_servo(0)                # Sistema apagado: servo cerrado
            apagar_leds()                 # Apaga LEDs
            servo_ang = 0
            led_estado = "OFF"

    # -------- ENVÍO UDP --------
    if time.ticks_diff(ahora, t_envio) >= ENVIO_MS:
        t_envio = ahora

        mensaje = (
            "{"
            "\"temp_measured\":" + str(round(temp, 2)) + ","  # Temperatura medida
            "\"temp_ref\":" + str(round(ref, 2)) + ","        # Temperatura referencia
            "\"light\":" + str(luz) + ","                     # Nivel de luz
            "\"system\":" + str(int(sistema_habilitado)) + ","# Estado del sistema
            "\"servo\":" + str(servo_ang) + ","               # Ángulo del servo
            "\"led\":\"" + led_estado + "\""                  # Estado del LED
            "}"
        )

        sock.sendto(mensaje.encode(), (PC_IP, UDP_PORT))      # Envía UDP al PC

    time.sleep_ms(5)                   # Pequeña pausa para estabilidad
