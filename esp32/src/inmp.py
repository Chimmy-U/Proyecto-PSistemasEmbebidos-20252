from machine import Pin, I2S
import struct, time, math

class INMP441:
    def __init__(self, pin_bck, pin_ws, pin_sd, i2s_id=0, sample_rate=16000, bits=16, format=I2S.MONO, ibuf=1024):
        # Guardar parámetros
        self.sample_rate = sample_rate
        self.bits = bits
        self.channels = 1 if format == I2S.MONO else 2

        # Pines I²S
        self.bck = Pin(pin_bck)
        self.ws  = Pin(pin_ws)
        self.sd  = Pin(pin_sd)

        # Configuración de I²S
        self.audio = I2S(
            i2s_id,
            sck=self.bck,
            ws=self.ws,
            sd=self.sd,
            mode=I2S.RX,
            bits=bits,
            format=format,
            rate=sample_rate,
            ibuf=ibuf
        )

        # El buffer debe ser múltiplo de 2 (para 16 bits mono)
        self.buf = bytearray(512)

    def read_sample(self):
        """Lee un bloque de muestras y devuelve un único valor RMS (para plotter)."""
        n = self.audio.readinto(self.buf)
        if n and n % 2 == 0:
            samples = struct.unpack("<" + "h"*(n//2), self.buf[:n])
            # Calcular RMS del bloque
            rms = math.sqrt(sum([s**2 for s in samples]) / len(samples))
            return int(rms)   # valor único para graficar
        return 0

    def dbs(self):
        """Devuelve el nivel en decibelios positivos (0 = silencio)."""
        n = self.audio.readinto(self.buf)
        if n and n % 2 == 0:
            samples = struct.unpack("<" + "h"*(n//2), self.buf[:n])
            rms = math.sqrt(sum([s**2 for s in samples]) / len(samples))
            if rms > 0:
                # Normalizar a rango positivo: 0 dB = silencio, ~90 dB = muy fuerte
                return 20 * math.log10(rms)
            else:
                return 0
        return 0

    def record_wav(self, filename, duration_sec):
        """Graba audio en formato WAV PCM16 escribiendo por bloques."""
        bytes_per_sample = self.bits // 8
        total_samples = int(self.sample_rate * duration_sec)
        num_channels = self.channels

        # Calcular tamaño de los datos
        data_bytes = total_samples * bytes_per_sample * num_channels
        file_size = 44 + data_bytes  # 44 bytes de header WAV

        # Construir header WAV
        wav_header = bytearray(44)
        wav_header[0:4] = b'RIFF'
        wav_header[4:8] = (file_size - 8).to_bytes(4, 'little')
        wav_header[8:12] = b'WAVE'
        wav_header[12:16] = b'fmt '
        wav_header[16:20] = (16).to_bytes(4, 'little')        # Subchunk1Size
        wav_header[20:22] = (1).to_bytes(2, 'little')         # AudioFormat = PCM
        wav_header[22:24] = num_channels.to_bytes(2, 'little')
        wav_header[24:28] = self.sample_rate.to_bytes(4, 'little')
        byte_rate = self.sample_rate * num_channels * bytes_per_sample
        wav_header[28:32] = byte_rate.to_bytes(4, 'little')
        block_align = num_channels * bytes_per_sample
        wav_header[32:34] = block_align.to_bytes(2, 'little')
        wav_header[34:36] = self.bits.to_bytes(2, 'little')
        wav_header[36:40] = b'data'
        wav_header[40:44] = data_bytes.to_bytes(4, 'little')

        written = 0
        start = time.ticks_ms()

        with open(filename + ".wav", "wb") as f:
            f.write(wav_header)  # Escribir header WAV

            while written < total_samples:
                n = self.audio.readinto(self.buf)
                if n and n % bytes_per_sample == 0:
                    f.write(self.buf[:n])
                    written += n // bytes_per_sample

                if time.ticks_diff(time.ticks_ms(), start) > duration_sec * 1000:
                    break

        print("Archivo WAV guardado:", filename + ".wav")


    def close(self):
        self.audio.deinit()
