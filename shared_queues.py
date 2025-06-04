# shared_queues.py
"""
Módulo centralizado para definir filas de comunicação thread-safe
usadas entre o jarvis_core (backend) e a jarvis_ui (frontend).
"""
import queue

# Fila para enviar comandos da UI para o Core do Jarvis
# A UI colocará strings de comando aqui.
command_queue = queue.Queue()

# Fila para enviar atualizações do Core do Jarvis para a UI
# O Core colocará dicionários aqui, ex: {"type": "log", "sender": "Jarvis", "message": "Olá!"}
# ou {"type": "status", "text": "Processando...", "icon": "some_icon_name"}
ui_update_queue = queue.Queue()

# Mensagem especial para sinalizar o encerramento da thread do core
EXIT_SIGNAL = "JARVIS_EXIT_NOW"

if __name__ == '__main__':
    # Exemplo simples de uso (não será executado normalmente)
    print("shared_queues.py - Definindo command_queue e ui_update_queue.")

    # Simular UI enviando um comando
    command_queue.put("Olá Jarvis, como você está?")
    print(f"Comando colocado na command_queue: '{command_queue.get_nowait()}'")

    # Simular Core enviando uma atualização de status
    ui_update_queue.put({"type": "status", "text": "Ouvindo..."})
    print(f"Atualização colocada na ui_update_queue: {ui_update_queue.get_nowait()}")

    # Simular Core enviando uma mensagem de log
    ui_update_queue.put({"type": "log", "sender": "Jarvis", "message": "Estou bem, obrigado!"})
    print(f"Atualização colocada na ui_update_queue: {ui_update_queue.get_nowait()}")

    print(f"Sinal de saída definido como: {EXIT_SIGNAL}")
```
