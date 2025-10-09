from machine import Pin, PWM
import time

class RGBLed:
    def __init__(self, pin_r, pin_g, pin_b, freq=1000):
        self.MAX = 65535  # Duty máximo
        # Configurar pines PWM
        self.r = PWM(Pin(pin_r), freq=freq)
        self.g = PWM(Pin(pin_g), freq=freq)
        self.b = PWM(Pin(pin_b), freq=freq)
        # Apagar al inicio
        self.off()
    
    def set_color(self, r, g, b):
        """
        Configura un color directo.
        Valores r,g,b en rango 0-65535.
        """
        self.r.duty_u16(r)
        self.g.duty_u16(g)
        self.b.duty_u16(b)
        
    def off(self):
        """Apagar LEDs"""
        self.set_color(0, 0, 0)
    
    # -------- Colores constantes -------- #
    def red(self):
        self.set_color(self.MAX, 0, 0)

    def yellow(self):
        self.set_color(self.MAX, self.MAX, 0)

    def white(self):
        self.set_color(self.MAX, self.MAX, self.MAX)

    def blue(self):
        self.set_color(0, 0, self.MAX)

    def green(self):
        self.set_color(0, self.MAX, 0)
    
    def purple(self):
        self.set_color(self.MAX, 0, self.MAX)
    
    # -------- Intermitentes -------- #
    def red_blink(self, delay=1, cycles=5):
        for _ in range(cycles):
            self.red()
            time.sleep(delay)
            self.off()
            time.sleep(delay)

    def blue_blink(self, delay=1, cycles=5):
        for _ in range(cycles):
            self.blue()
            time.sleep(delay)
            self.off()
            time.sleep(delay)
    
     # -------- Fade morado -------- #
    def purple_fade(self, mode="on", duration=4, steps=100):
        """
        Fade morado (Rojo+Azul).
        - modo="on": fade apagado -> encendido
        - modo="off": fade encendido -> apagado
        - duracion: tiempo total en segundos
        """
        delay = duration / steps
        if mode == "on":
            for i in range(steps+1):
                value = int(self.MAX * i / steps)
                self.set_color(value, 0, value)
                time.sleep(delay)
        elif mode == "off":
            for i in range(steps, -1, -1):
                value = int(self.MAX * i / steps)
                self.set_color(value, 0, value)
                time.sleep(delay)