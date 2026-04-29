DESCRIPCIÓN DEL TRABAJO:

En este proyecto se desarrolló un sistema de monitoreo y control ambiental utilizando una ESP32.
El sistema permite medir variables como la temperatura, el nivel de iluminación y una temperatura de referencia ajustada mediante un potenciómetro.

Los datos obtenidos son enviados a un servidor en Python, el cual genera una interfaz web que permite visualizar en tiempo real el estado del sistema, incluyendo:

*Temperatura medida
*Temperatura de referencia
*Nivel de luz
*Estado del sistema (habilitado/deshabilitado)
*Estado del servomotor
*Estado de los LEDs

Nota: La interfaz web se actualiza automáticamente sin necesidad de recargar la página
PINES USADOS:

*Sensor de temperatura: GPIO35
*Potenciómetro: GPIO34
*Sensor de luz: GPIO32
*Servomotor: GPIO18
*LED rojo: GPIO27
*LED amarillo: GPIO26
*LED verde: GPIO25
*Boton interrupción: GPIO33

INSTRUCCIONES DE USO:

1. Conectar la ESP32 con el circuito al pc
2. Cargar el programa en la ESP32 (main.py)
3. Conectar la ESP32 a una red WiFi
4. Ejecutar el servidor en el computador: python servidor.py
5. Abrir un navegador web desde un dispositivo conectado a la misma red
6. Ingresar la dirección IP del servidor
7. Visualizar los datos en tiempo real
8. Tocar el botón de interrupción si desea apagar el circuito
