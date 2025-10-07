# Proyecto Sistemas Embebidos - Agente de IA
## Integración ESP32 - Raspberry Pi mediante MQTT

### Descripción General
Sistema distribuido que integra un ESP32 y una Raspberry Pi para crear un agente de IA inteligente. El sistema utiliza comunicación MQTT bidireccional, procesamiento de machine learning y consultas a APIs externas.

### Arquitectura del Sistema

```
┌─────────────┐             ┌──────────────────┐    HTTP/REST    ┌─────────────┐
│   Sensores  │             │   Raspberry Pi   │ ◄─────────────  │ API Externa │
└─────────────┘             │                  │                 └─────────────┘
      │                     │ ┌──────────────┐ │
      ▼                     │ │ MQTT Broker  │ │
┌─────────────┐    MQTT     │ └──────────────┘ │
│    ESP32    │ ──────────▶ │ ┌──────────────┐ │
└─────────────┘ ◄────────── │ │ Integración  │ │
      │                     │ │   de Datos   │ │
      ▼                     │ └──────────────┘ │
┌─────────────┐             │ ┌──────────────┐ │
│ Actuadores  │             │ │ ML (ANN-MLP) │ │
└─────────────┘             │ └──────────────┘ │
                            └──────────────────┘
```

### Componentes Principales

#### ESP32 (MicroPython)
- **Funciones**: Control directo de sensores y actuadores
- **Comunicación**: Cliente MQTT para envío/recepción de datos
- **Indicadores**: LEDs de estado de conexión y transmisión

#### Raspberry Pi (Python)
- **Broker MQTT**: Gestión de comunicación con ESP32
- **API Externa**: Consulta de información complementaria
- **Machine Learning**: Red neuronal (ANN-MLP) para toma de decisiones
- **Procesamiento**: Integración de datos y generación de comandos

### Flujo de Información

1. **Adquisición**: Sensores → ESP32
2. **Transmisión**: ESP32 → MQTT → Raspberry Pi
3. **Integración**: RPi consulta API externa
4. **Procesamiento**: Red neuronal procesa datos combinados
5. **Decisión**: RPi genera comandos de control
6. **Ejecución**: RPi → MQTT → ESP32 → Actuadores

### Estructura del Proyecto

```
├── esp32/                  # Código para ESP32 (MicroPython)
│   ├── src/               # Archivos fuente principales
│   └── lib/               # Librerías personalizadas
├── raspberry_pi/          # Código para Raspberry Pi (Python)
│   ├── src/               # Aplicación principal
│   ├── mqtt/              # Cliente/Broker MQTT
│   ├── api/               # Integración con API externa
│   └── ml_models/         # Modelos de Machine Learning
├── data/                  # Datasets y modelos entrenados
│   ├── datasets/          # Conjuntos de datos (CSV)
│   └── models/            # Modelos guardados
├── docs/                  # Documentación del proyecto
├── tests/                 # Pruebas unitarias
└── README.md              # Este archivo
```

### Tecnologías Utilizadas

- **ESP32**: MicroPython, MQTT Client
- **Raspberry Pi**: Python 3, TensorFlow Lite, MQTT Broker
- **Comunicación**: MQTT Protocol
- **Machine Learning**: Neural Network (MLP)
- **APIs**: HTTP/REST
- **Control de Versiones**: Git

### Instalación y Configuración

#### ESP32
1. Flashear MicroPython
2. Subir archivos desde `esp32/src/`
3. Configurar credenciales Wi-Fi y MQTT

#### Raspberry Pi
1. Instalar dependencias: `pip install -r requirements.txt`
2. Configurar Mosquitto MQTT Broker
3. Entrenar/cargar modelo de ML

### Uso

1. Conectar hardware (sensores/actuadores al ESP32)
2. Iniciar broker MQTT en RPi
3. Ejecutar aplicación principal en RPi
4. Reiniciar ESP32 para conectar

### Autores

- [Tu nombre y equipo]

### Licencia

Este proyecto es parte del curso de Sistemas Embebidos - Universidad [Nombre]