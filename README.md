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
- **Procesamiento**: Integración de datos y generación de comandos de control

### Flujo de Información

1. **Adquisición**: Sensores → ESP32
2. **Transmisión**: ESP32 → MQTT → Raspberry Pi
3. **Integración**: RPi consulta API externa
4. **Procesamiento**: Red neuronal procesa datos combinados
5. **Decisión**: RPi genera comandos de control
6. **Ejecución**: RPi → MQTT → ESP32 → Actuadores

### Estructura del Proyecto

```
proyecto/
├── data/                          # Datos y modelos de ML
│   ├── datasets/                  # Conjuntos de datos
│   │   ├── data.csv              # Datos sin formatear
│   │   ├── dataset.csv           # Dataset
│   │   └── dataset_generator.py   # Generador de datasets
│   └── models/                    # Modelos entrenados
│       ├── model_trainer.py       # Script de entrenamiento
│       ├── sound_classifier.h5    # Modelo TensorFlow
│       ├── sound_classifier.tflite # Modelo TF Lite
│       └── test_model.py         # Script de pruebas
│
├── esp32/                         # Código del ESP32
│   └── src/                      # Código fuente
│       ├── inmp.py               # Control del sensor
│       ├── main.py               # Programa principal
│       ├── mqtt.py               # Cliente MQTT
│       ├── rgb.py                # Control de LEDs
│       └── secrets.py            # Configuraciones
│
└── raspberry_pi/                  # Código de Raspberry Pi
    └── src/                      # Código fuente
        ├── api.py                # Interfaz API
        ├── main.py               # Programa principal
        ├── ml.py                 # Procesamiento ML
        ├── mqtt_host.py          # Broker MQTT
        └── secrets.py            # Configuraciones
```


### Tecnologías Utilizadas

- **ESP32**: MicroPython, MQTT Client
- **Raspberry Pi**: Python 3, TensorFlow Lite, MQTT Broker
- **Comunicación**: MQTT Protocol
- **Machine Learning**: Neural Network (MLP)
- **APIs**: HTTP/REST
- **Control de Versiones**: Git


### Autores

- [Tu nombre y equipo]

### Licencia

Este proyecto es parte del curso de Sistemas Embebidos - Universidad [Nombre]