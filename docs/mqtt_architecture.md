# Arquitectura MQTT y Comunicación

## Tópicos MQTT

### Estructura de Tópicos

```
proyecto/
├── sensores/
│   ├── temperatura
│   ├── humedad
│   ├── luz
│   └── ruido
├── actuadores/
│   ├── ventilador
│   ├── led
│   └── bomba
├── estado/
│   ├── esp32/conectado
│   └── rpi/conectado
└── comandos/
    ├── emergencia
    └── configuracion
```

### Flujo de Mensajes

#### ESP32 → Raspberry Pi (Publicación)
- **Sensores**: `proyecto/sensores/{sensor_name}`
- **Estado**: `proyecto/estado/esp32/conectado`
- **Formato**: JSON con timestamp

```json
{
  "sensor": "temperatura",
  "value": 25.6,
  "unit": "°C",
  "timestamp": "2025-01-07T19:00:00Z",
  "device_id": "ESP32_001"
}
```

#### Raspberry Pi → ESP32 (Publicación)
- **Comandos**: `proyecto/actuadores/{actuator_name}`
- **Estado**: `proyecto/estado/rpi/conectado`
- **Emergencia**: `proyecto/comandos/emergencia`

```json
{
  "actuator": "ventilador",
  "action": "on",
  "intensity": 75,
  "duration": 300,
  "timestamp": "2025-01-07T19:00:05Z",
  "source": "ML_MODEL"
}
```

## Configuración del Broker

### Mosquitto en Raspberry Pi
```bash
# Instalación
sudo apt update
sudo apt install mosquitto mosquitto-clients

# Configuración básica (/etc/mosquitto/mosquitto.conf)
listener 1883
allow_anonymous true
persistence true
persistence_location /var/lib/mosquitto/

# Iniciar servicio
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

### Cliente MQTT en ESP32
```python
# Configuración de conexión
MQTT_BROKER = "192.168.1.100"  # IP de la Raspberry Pi
MQTT_PORT = 1883
CLIENT_ID = "ESP32_001"
```

### Cliente MQTT en Raspberry Pi
```python
# Configuración de cliente
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
CLIENT_ID = "RPI_MAIN"
```

## Calidad de Servicio (QoS)

- **QoS 0**: Datos de sensores (frecuentes, pérdida tolerable)
- **QoS 1**: Comandos a actuadores (importante entrega)
- **QoS 2**: Comandos de emergencia (entrega garantizada)

## Manejo de Reconexión

### ESP32
- Reintentos automáticos cada 30 segundos
- LED indicador de estado de conexión
- Buffer local para datos críticos

### Raspberry Pi
- Mantenimiento de sesión persistente
- Log de eventos de conexión/desconexión
- Recuperación automática del broker