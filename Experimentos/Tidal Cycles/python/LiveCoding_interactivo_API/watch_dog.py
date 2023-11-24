import subprocess
import time
from openai import OpenAI
import json
import datetime
from apikey import API_KEY  # Importa la clave desde apikey.py
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

nombre_archivo_tidal = 'dummy.tidal'

# Crear el cliente de OpenAI
client = OpenAI(api_key=API_KEY)

# Iniciar GHCi con el proceso de TidalCycles
try:
    process = subprocess.Popen(["ghci"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, bufsize=1, universal_newlines=True)
except Exception as e:
    print(f"Error al iniciar GHCi: {e}")
    exit(1)

# Función para enviar un comando a TidalCycles a través de GHCi


def run_tidal_command(command):
    try:
        print("Enviando comando a TidalCycles:", command)
        process.stdin.write(command + "\n")
        process.stdin.flush()
    except Exception as e:
        print(f"Error al enviar comando a TidalCycles: {e}")


# Inicializar TidalCycles
run_tidal_command(":script /usr/share/haskell-tidal/BootTidal.hs")
time.sleep(5)  # Esperar a que TidalCycles se inicialice

# Leer y almacenar la versión inicial del archivo de Tidal
with open(nombre_archivo_tidal, 'r') as file:
    original_content = file.read()

# Función para dividir el contenido en patrones


def segment_into_patterns(content):
    patterns = {}
    current_pattern = None
    for line in content.split('\n'):
        # Separar comentarios del código del patrón
        pattern_part, _, comment_part = line.partition('--')
        clean_line = pattern_part.strip()

        # Ignorar líneas completamente vacías y finalizar el patrón actual
        if not clean_line:
            current_pattern = None
            continue

        if clean_line.startswith('d') and clean_line[1].isdigit() and ' $' in clean_line:
            current_pattern = clean_line.split(' $')[0]
            patterns[current_pattern] = clean_line
        elif current_pattern:
            patterns[current_pattern] += '\n' + clean_line

    return patterns


original_patterns = segment_into_patterns(original_content)

# Handler para evento de modificación de archivos


class MyHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_modified = time.time()

    def on_modified(self, event):
        global original_patterns
        # Debounce para evitar múltiples disparos por guardar rápidamente
        if time.time() - self.last_modified < 1:
            return

        if event.src_path.endswith(".tidal"):
            with open(event.src_path, 'r') as file:
                new_content = file.read()
            new_patterns = segment_into_patterns(new_content)

            # Comparar y mostrar diferencias
            for pattern in new_patterns:
                if pattern not in original_patterns or new_patterns[pattern] != original_patterns[pattern]:
                    run_tidal_command(new_patterns[pattern])
                    print(
                        f"Tidal: {pattern}\n{new_patterns[pattern]}")

            # Actualizar contenido original
            original_patterns = new_patterns

        self.last_modified = time.time()


# Configurar el observador
event_handler = MyHandler()
observer = Observer()
observer.schedule(event_handler, path='./', recursive=False)
observer.start()

# Resto del script para interactuar con GHCi y la API de OpenAI

# Detener el observador al terminar
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    observer.stop()
observer.join()
