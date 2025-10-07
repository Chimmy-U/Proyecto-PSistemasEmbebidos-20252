"""
Aplicación principal Raspberry Pi - Sistema de Agente IA
Maneja MQTT, consultas API, Machine Learning y toma de decisiones
"""

import json
import time
import logging
from datetime import datetime
import threading
import requests
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

# Imports locales
from mqtt.mqtt_client import MQTTManager
from api.weather_api import WeatherAPI
from ml_models.neural_network import NeuralNetworkPredictor
from utils.data_processor import DataProcessor

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_ai.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AIAgent:
    """Clase principal del Agente de IA"""
    
    def __init__(self):
        # Componentes principales
        self.mqtt_manager = MQTTManager(self.process_sensor_data)
        self.weather_api = WeatherAPI()
        self.ml_predictor = NeuralNetworkPredictor()
        self.data_processor = DataProcessor()
        
        # Estado del sistema
        self.sensor_data = {}
        self.api_data = {}
        self.last_decision_time = 0
        self.decision_interval = 10  # Tomar decisiones cada 10 segundos
        
        # Configuración
        self.emergency_mode = False
        self.running = False
        
        logger.info("AIAgent inicializado")
    
    def start(self):
        """Inicia el agente de IA"""
        logger.info("Iniciando Agente de IA...")
        
        try:
            # Inicializar componentes
            self.mqtt_manager.start()
            self.ml_predictor.load_model()
            
            self.running = True
            
            # Iniciar hilos de procesamiento
            decision_thread = threading.Thread(target=self._decision_loop, daemon=True)
            api_thread = threading.Thread(target=self._api_loop, daemon=True)
            
            decision_thread.start()
            api_thread.start()
            
            logger.info("Agente de IA iniciado correctamente")
            
            # Bucle principal
            self._main_loop()
            
        except Exception as e:
            logger.error(f"Error iniciando agente: {e}")
            self.stop()
    
    def stop(self):
        """Detiene el agente de IA"""
        logger.info("Deteniendo Agente de IA...")
        
        self.running = False
        self.mqtt_manager.stop()
        
        logger.info("Agente de IA detenido")
    
    def process_sensor_data(self, topic: str, data: Dict[str, Any]):
        """Procesa datos recibidos de sensores"""
        try:
            sensor_name = data.get('sensor', 'unknown')
            value = data.get('value', 0)
            timestamp = data.get('timestamp', time.time())
            
            # Actualizar datos de sensores
            self.sensor_data[sensor_name] = {
                'value': value,
                'timestamp': timestamp,
                'unit': data.get('unit', '')
            }
            
            logger.debug(f"Datos actualizados - {sensor_name}: {value}")
            
            # Verificar condiciones de emergencia
            self._check_emergency_conditions()
            
        except Exception as e:
            logger.error(f"Error procesando datos de sensor: {e}")
    
    def _check_emergency_conditions(self):
        """Verifica condiciones que requieren parada de emergencia"""
        try:
            # Condiciones de emergencia
            temp = self.sensor_data.get('temperatura', {}).get('value', 0)
            humidity = self.sensor_data.get('humedad', {}).get('value', 0)
            noise = self.sensor_data.get('ruido', {}).get('value', 0)
            
            emergency_triggered = False
            
            if temp > 45:  # Temperatura muy alta
                logger.warning(f"EMERGENCIA: Temperatura crítica {temp}°C")
                emergency_triggered = True
            
            if humidity > 95:  # Humedad muy alta
                logger.warning(f"EMERGENCIA: Humedad crítica {humidity}%")
                emergency_triggered = True
            
            if noise > 90:  # Ruido muy alto
                logger.warning(f"EMERGENCIA: Ruido crítico {noise}dB")
                emergency_triggered = True
            
            if emergency_triggered and not self.emergency_mode:
                self._trigger_emergency()
                
        except Exception as e:
            logger.error(f"Error verificando emergencia: {e}")
    
    def _trigger_emergency(self):
        """Activa modo de emergencia"""
        self.emergency_mode = True
        
        emergency_command = {
            "command": "emergency_stop",
            "timestamp": time.time(),
            "source": "AI_AGENT"
        }
        
        self.mqtt_manager.publish("proyecto/comandos/emergencia", emergency_command)
        logger.critical("MODO EMERGENCIA ACTIVADO")
    
    def _decision_loop(self):
        """Bucle de toma de decisiones con ML"""
        while self.running:
            try:
                current_time = time.time()
                
                if current_time - self.last_decision_time >= self.decision_interval:
                    if not self.emergency_mode:
                        self._make_decisions()
                    self.last_decision_time = current_time
                
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Error en bucle de decisiones: {e}")
                time.sleep(5)
    
    def _api_loop(self):
        """Bucle de consulta a API externa"""
        while self.running:
            try:
                # Consultar API cada 30 segundos
                weather_data = self.weather_api.get_current_weather()
                if weather_data:
                    self.api_data = weather_data
                    logger.debug("Datos de API actualizados")
                
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Error en bucle de API: {e}")
                time.sleep(60)
    
    def _make_decisions(self):
        """Toma decisiones basadas en ML y datos integrados"""
        try:
            # Verificar que tengamos datos suficientes
            if len(self.sensor_data) < 3:
                logger.debug("Datos insuficientes para tomar decisiones")
                return
            
            # Preparar datos para ML
            input_data = self._prepare_ml_input()
            if input_data is None:
                return
            
            # Hacer predicción
            predictions = self.ml_predictor.predict(input_data)
            if predictions is None:
                return
            
            # Convertir predicciones en comandos
            commands = self._predictions_to_commands(predictions, input_data)
            
            # Enviar comandos
            for actuator, command in commands.items():
                topic = f"proyecto/actuadores/{actuator}"
                self.mqtt_manager.publish(topic, command)
                logger.info(f"Comando enviado a {actuator}: {command}")
            
        except Exception as e:
            logger.error(f"Error en toma de decisiones: {e}")
    
    def _prepare_ml_input(self) -> Optional[np.ndarray]:
        """Prepara datos de entrada para el modelo de ML"""
        try:
            # Obtener valores de sensores
            temp = self.sensor_data.get('temperatura', {}).get('value', 0)
            humidity = self.sensor_data.get('humedad', {}).get('value', 0)
            light = self.sensor_data.get('luz', {}).get('value', 0)
            noise = self.sensor_data.get('ruido', {}).get('value', 0)
            
            # Datos de API externa
            external_temp = self.api_data.get('temperature', temp)
            external_humidity = self.api_data.get('humidity', humidity)
            wind_speed = self.api_data.get('wind_speed', 0)
            
            # Crear array de entrada normalizado
            input_array = np.array([
                temp / 50.0,           # Normalizar temperatura (0-50°C)
                humidity / 100.0,      # Normalizar humedad (0-100%)
                light / 1000.0,        # Normalizar luz (0-1000 lux)
                noise / 100.0,         # Normalizar ruido (0-100 dB)
                external_temp / 50.0,  # Temperatura externa
                external_humidity / 100.0,  # Humedad externa
                wind_speed / 50.0      # Velocidad del viento (0-50 m/s)
            ])
            
            return input_array.reshape(1, -1)
            
        except Exception as e:
            logger.error(f"Error preparando entrada ML: {e}")
            return None
    
    def _predictions_to_commands(self, predictions: np.ndarray, input_data: np.ndarray) -> Dict[str, Dict]:
        """Convierte predicciones del ML en comandos para actuadores"""
        try:
            commands = {}
            
            # Interpretar predicciones (asumiendo salidas normalizadas 0-1)
            fan_intensity = int(predictions[0] * 100)
            led_intensity = int(predictions[1] * 100) if len(predictions) > 1 else 0
            pump_intensity = int(predictions[2] * 100) if len(predictions) > 2 else 0
            
            # Generar comandos
            if fan_intensity > 10:  # Umbral mínimo para activar
                commands['ventilador'] = {
                    "action": "on",
                    "intensity": min(fan_intensity, 100),
                    "duration": 60,
                    "timestamp": time.time(),
                    "source": "ML_MODEL"
                }
            else:
                commands['ventilador'] = {
                    "action": "off",
                    "intensity": 0,
                    "timestamp": time.time(),
                    "source": "ML_MODEL"
                }
            
            if led_intensity > 5:
                commands['led'] = {
                    "action": "on",
                    "intensity": min(led_intensity, 100),
                    "timestamp": time.time(),
                    "source": "ML_MODEL"
                }
            else:
                commands['led'] = {
                    "action": "off",
                    "intensity": 0,
                    "timestamp": time.time(),
                    "source": "ML_MODEL"
                }
            
            if pump_intensity > 15:
                commands['bomba'] = {
                    "action": "on",
                    "intensity": min(pump_intensity, 100),
                    "duration": 30,
                    "timestamp": time.time(),
                    "source": "ML_MODEL"
                }
            else:
                commands['bomba'] = {
                    "action": "off",
                    "intensity": 0,
                    "timestamp": time.time(),
                    "source": "ML_MODEL"
                }
            
            return commands
            
        except Exception as e:
            logger.error(f"Error generando comandos: {e}")
            return {}
    
    def _main_loop(self):
        """Bucle principal del agente"""
        logger.info("Agente en funcionamiento. Presiona Ctrl+C para detener.")
        
        try:
            while self.running:
                # Mostrar estado cada 30 segundos
                self._print_status()
                time.sleep(30)
                
        except KeyboardInterrupt:
            logger.info("Interrupción por usuario")
        except Exception as e:
            logger.error(f"Error en bucle principal: {e}")
        finally:
            self.stop()
    
    def _print_status(self):
        """Imprime el estado actual del sistema"""
        try:
            print("\n" + "="*50)
            print(f"Estado del Sistema - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*50)
            
            if self.emergency_mode:
                print("🚨 MODO EMERGENCIA ACTIVADO 🚨")
            
            print("\n📊 Sensores:")
            for sensor, data in self.sensor_data.items():
                value = data.get('value', 'N/A')
                unit = data.get('unit', '')
                print(f"  {sensor.capitalize()}: {value} {unit}")
            
            print("\n🌤️  Datos Externos:")
            if self.api_data:
                temp = self.api_data.get('temperature', 'N/A')
                humidity = self.api_data.get('humidity', 'N/A')
                wind = self.api_data.get('wind_speed', 'N/A')
                print(f"  Temperatura: {temp}°C")
                print(f"  Humedad: {humidity}%")
                print(f"  Viento: {wind} m/s")
            else:
                print("  No disponibles")
            
            print("\n🔗 Conexión MQTT:", "✅ Conectado" if self.mqtt_manager.connected else "❌ Desconectado")
            
        except Exception as e:
            logger.error(f"Error mostrando estado: {e}")

def main():
    """Función principal"""
    print("🤖 Iniciando Sistema de Agente IA")
    print("Integración ESP32 - Raspberry Pi")
    print("-" * 40)
    
    agent = AIAgent()
    
    try:
        agent.start()
    except Exception as e:
        logger.error(f"Error crítico: {e}")
    finally:
        agent.stop()

if __name__ == "__main__":
    main()