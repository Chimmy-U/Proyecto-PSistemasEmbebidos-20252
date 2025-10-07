"""
Red Neuronal para el Agente de IA
Implementa MLP para toma de decisiones basada en sensores y datos externos
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import pickle
import logging
from typing import Optional, Tuple
import os

logger = logging.getLogger(__name__)

class NeuralNetworkPredictor:
    """Predictor basado en red neuronal MLP"""
    
    def __init__(self, model_path: str = "data/models/agent_model.h5"):
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.input_size = 7  # 4 sensores + 3 datos externos
        self.output_size = 3  # 3 actuadores
        
        # Configuración del modelo
        self.hidden_layers = [16, 8]
        self.learning_rate = 0.001
        self.epochs = 200
    
    def create_model(self) -> keras.Model:
        """Crea la arquitectura de la red neuronal"""
        model = keras.Sequential([
            # Capa de entrada
            layers.Input(shape=(self.input_size,)),
            
            # Capas ocultas
            layers.Dense(self.hidden_layers[0], activation='relu', 
                        kernel_initializer='he_uniform'),
            layers.Dropout(0.2),
            
            layers.Dense(self.hidden_layers[1], activation='relu',
                        kernel_initializer='he_uniform'),
            layers.Dropout(0.1),
            
            # Capa de salida
            layers.Dense(self.output_size, activation='sigmoid')
        ])
        
        # Compilar modelo
        model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss='mse',
            metrics=['mae']
        )
        
        return model
    
    def train_model(self, X_train: np.ndarray, y_train: np.ndarray, 
                   X_val: Optional[np.ndarray] = None, 
                   y_val: Optional[np.ndarray] = None) -> dict:
        """Entrena el modelo con los datos proporcionados"""
        try:
            logger.info("Iniciando entrenamiento del modelo...")
            
            # Crear modelo
            self.model = self.create_model()
            
            # Normalizar datos
            self.scaler = self._create_scaler(X_train)
            X_train_scaled = self.scaler.transform(X_train)
            
            if X_val is not None:
                X_val_scaled = self.scaler.transform(X_val)
                validation_data = (X_val_scaled, y_val)
            else:
                validation_data = None
            
            # Callbacks
            callbacks = [
                keras.callbacks.EarlyStopping(
                    monitor='val_loss' if validation_data else 'loss',
                    patience=20,
                    restore_best_weights=True
                ),
                keras.callbacks.ReduceLROnPlateau(
                    monitor='val_loss' if validation_data else 'loss',
                    factor=0.5,
                    patience=10,
                    min_lr=1e-6
                )
            ]
            
            # Entrenar
            history = self.model.fit(
                X_train_scaled, y_train,
                validation_data=validation_data,
                epochs=self.epochs,
                batch_size=32,
                callbacks=callbacks,
                verbose=1
            )
            
            # Guardar modelo y scaler
            self.save_model()
            
            logger.info("Entrenamiento completado exitosamente")
            return history.history
            
        except Exception as e:
            logger.error(f"Error durante el entrenamiento: {e}")
            return {}
    
    def load_model(self) -> bool:
        """Carga un modelo previamente entrenado"""
        try:
            if os.path.exists(self.model_path):
                self.model = keras.models.load_model(self.model_path)
                
                # Cargar scaler si existe
                scaler_path = self.model_path.replace('.h5', '_scaler.pkl')
                if os.path.exists(scaler_path):
                    with open(scaler_path, 'rb') as f:
                        self.scaler = pickle.load(f)
                
                logger.info("Modelo cargado exitosamente")
                return True
            else:
                logger.warning(f"No se encontró modelo en {self.model_path}")
                # Crear modelo básico como fallback
                self.model = self.create_model()
                self._create_dummy_scaler()
                return False
                
        except Exception as e:
            logger.error(f"Error cargando modelo: {e}")
            # Fallback a modelo básico
            self.model = self.create_model()
            self._create_dummy_scaler()
            return False
    
    def save_model(self):
        """Guarda el modelo y el scaler"""
        try:
            # Crear directorio si no existe
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            
            # Guardar modelo
            self.model.save(self.model_path)
            
            # Guardar scaler
            if self.scaler:
                scaler_path = self.model_path.replace('.h5', '_scaler.pkl')
                with open(scaler_path, 'wb') as f:
                    pickle.dump(self.scaler, f)
            
            logger.info(f"Modelo guardado en {self.model_path}")
            
        except Exception as e:
            logger.error(f"Error guardando modelo: {e}")
    
    def predict(self, input_data: np.ndarray) -> Optional[np.ndarray]:
        """Realiza predicción con el modelo"""
        try:
            if self.model is None:
                logger.warning("Modelo no cargado")
                return None
            
            # Normalizar entrada si hay scaler
            if self.scaler:
                input_scaled = self.scaler.transform(input_data.reshape(1, -1))
            else:
                input_scaled = input_data.reshape(1, -1)
            
            # Predecir
            predictions = self.model.predict(input_scaled, verbose=0)
            
            return predictions[0]  # Retornar solo la primera predicción
            
        except Exception as e:
            logger.error(f"Error en predicción: {e}")
            return None
    
    def _create_scaler(self, X: np.ndarray):
        """Crea y ajusta un scaler para normalización"""
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        scaler.fit(X)
        return scaler
    
    def _create_dummy_scaler(self):
        """Crea un scaler dummy para casos donde no hay datos de entrenamiento"""
        from sklearn.preprocessing import StandardScaler
        self.scaler = StandardScaler()
        # Ajustar con datos dummy normalizados
        dummy_data = np.random.rand(100, self.input_size)
        self.scaler.fit(dummy_data)
    
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> dict:
        """Evalúa el modelo con datos de prueba"""
        try:
            if self.model is None or self.scaler is None:
                logger.error("Modelo o scaler no disponibles")
                return {}
            
            X_test_scaled = self.scaler.transform(X_test)
            results = self.model.evaluate(X_test_scaled, y_test, verbose=0)
            
            metrics = {
                'loss': results[0],
                'mae': results[1]
            }
            
            logger.info(f"Evaluación del modelo: {metrics}")
            return metrics
            
        except Exception as e:
            logger.error(f"Error en evaluación: {e}")
            return {}
    
    def get_model_info(self) -> dict:
        """Retorna información del modelo"""
        if self.model is None:
            return {}
        
        return {
            'input_shape': self.model.input_shape,
            'output_shape': self.model.output_shape,
            'total_params': self.model.count_params(),
            'layers': len(self.model.layers),
            'optimizer': self.model.optimizer.__class__.__name__,
            'loss': self.model.loss
        }