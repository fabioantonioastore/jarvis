# jarvis_ui.py
"""
Interface Gráfica do Usuário (GUI) para o Assistente Jarvis.
Utiliza Flet para criar a UI e se comunica com o Jarvis Core
através de filas thread-safe.
"""
import flet as ft
import time
import threading
import queue # Para queue.Empty
import logging # Adicionado para logging na UI
from typing import Optional, Dict, Any

# Configuração do logger para a UI
ui_logger = logging.getLogger("JarvisUI")
# Para ver logs da UI no console, mesmo que o logging do core seja diferente:
if not ui_logger.handlers: # Evitar adicionar handlers múltiplos se o script for recarregado
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(threadName)s - %(levelname)s - %(name)s - %(message)s', '%H:%M:%S')
    handler.setFormatter(formatter)
    ui_logger.addHandler(handler)
    ui_logger.setLevel(logging.INFO) # Ajuste o nível conforme necessário (DEBUG, INFO, etc.)


# --- Importações do Projeto ---
try:
    from shared_queues import command_queue, ui_update_queue, EXIT_SIGNAL
    from jarvis_core import start_jarvis_core_thread, stop_jarvis_core_thread, JARVIS_CORE_STOP_EVENT, ACTIVATE_VOICE_INPUT_COMMAND
except ImportError as e:
    ui_logger.warning(f"Falha ao importar módulos de shared_queues ou jarvis_core: {e}. UI com funcionalidade mockada.")
    class MockQueue: # Mock para permitir que a UI seja desenhada
        def __init__(self, name="MockQueue"): self.name = name
        def put(self, item, block=True, timeout=None): ui_logger.debug(f"{self.name}.put({item})")
        def get_nowait(self): raise queue.Empty
        def get(self, block=True, timeout=None):
            if block: time.sleep(timeout if timeout else 3600)
            raise queue.Empty
    command_queue, ui_update_queue = MockQueue("CmdQ"), MockQueue("UiQ")
    EXIT_SIGNAL, ACTIVATE_VOICE_INPUT_COMMAND = "EXIT_MOCK", "VOICE_MOCK"
    def start_jarvis_core_thread(): ui_logger.info("MOCK: start_jarvis_core_thread()")
    def stop_jarvis_core_thread(): ui_logger.info("MOCK: stop_jarvis_core_thread()")
    class MockEvent:
        def is_set(self): return False
        def set(self): ui_logger.info("MOCK: JARVIS_CORE_STOP_EVENT.set()")
    JARVIS_CORE_STOP_EVENT = MockEvent()

# --- Referências Globais e Mapas ---
status_icon_ref = ft.Ref[ft.Icon]()
status_text_ref = ft.Ref[ft.Text]()
chat_log_column_ref = ft.Ref[ft.Column]()
command_text_field_ref = ft.Ref[ft.TextField]()
mic_button_ref = ft.Ref[ft.IconButton]()
_page_instance_for_updates: Optional[ft.Page] = None
_ui_update_processor_thread_stop_event = threading.Event()
_ui_processor_thread: Optional[threading.Thread] = None # Referência para a thread de UI updates

ICON_MAP = { # Mapeia nomes de ícones string para constantes Flet
    "error_outline": ft.icons.ERROR_OUTLINE_ROUNDED, "settings_applications": ft.icons.SETTINGS_APPLICATIONS_ROUNDED,
    "mic_none": ft.icons.MIC_NONE_ROUNDED, "mic": ft.icons.MIC_ROUNDED, "mic_off": ft.icons.MIC_OFF_ROUNDED,
    "hourglass_empty": ft.icons.HOURGLASS_EMPTY_ROUNDED, "play_arrow": ft.icons.PLAY_ARROW_ROUNDED,
    "power_settings_new": ft.icons.POWER_SETTINGS_NEW_ROUNDED, "hearing": ft.icons.HEARING_ROUNDED,
    "info_outline": ft.icons.INFO_OUTLINE_ROUNDED, "settings_voice": ft.icons.SETTINGS_VOICE_ROUNDED,
    "default": ft.icons.INFO_ROUNDED # Ícone padrão se não mapeado
}
COLOR_MAP = { # Mapeia chaves de cor para cores Flet
    "user": ft.colors.LIGHT_BLUE_ACCENT_200, "jarvis_success": ft.colors.GREEN_ACCENT_400,
    "jarvis_info": ft.colors.LIGHT_BLUE_300, "jarvis_warning": ft.colors.ORANGE_ACCENT_200,
    "system_error": ft.colors.RED_ACCENT_700, "system_info": ft.colors.with_opacity(0.75, ft.colors.WHITE),
    "system_init": ft.colors.BLUE_GREY_200, "default": ft.colors.WHITE
}

def set_page_instance_for_updates(page: ft.Page):
    global _page_instance_for_updates
    _page_instance_for_updates = page

# --- Funções de Atualização da UI ---
def update_status_on_ui(icon_name_key: Optional[str], message: str):
    icon_to_display = ICON_MAP.get(icon_name_key, ICON_MAP["default"]) if icon_name_key else ICON_MAP["default"]
    if status_icon_ref.current: status_icon_ref.current.name = icon_to_display
    if status_text_ref.current: status_text_ref.current.value = message

def add_log_message_on_ui(sender: str, message: str, color_key: Optional[str] = None):
    text_color = COLOR_MAP.get(color_key, COLOR_MAP["default"]) if color_key else COLOR_MAP["default"]
    if chat_log_column_ref.current:
        timestamp = time.strftime("%H:%M:%S")
        log_entry = ft.Row(
            controls=[
                ft.Text(f"[{timestamp}]", color=COLOR_MAP["system_info"], size=10, italic=True),
                ft.Text(f"{sender}:", weight=ft.FontWeight.BOLD, color=text_color, width=70, size=12), # Aumentei a largura
                ft.SelectionArea(content=ft.Text(message, size=12, overflow=ft.TextOverflow.VISIBLE, selectable=True))
            ], wrap=True, vertical_alignment=ft.CrossAxisAlignment.START, spacing=5
        )
        chat_log_column_ref.current.controls.append(log_entry)
        # Auto-scroll para o final (se a página estiver disponível e o controle existir)
        if _page_instance_for_updates and chat_log_column_ref.current:
             _page_instance_for_updates.scroll_to(key="chat_log_scroll_end", duration=100)


# --- Processamento de Atualizações da UI ---
def handle_actual_ui_update(update_data: Dict[str, Any]):
    global _page_instance_for_updates
    if not _page_instance_for_updates: return

    update_type = update_data.get("type")
    # ui_logger.debug(f"UI recebendo atualização: {update_data}")

    if update_type == "log":
        add_log_message_on_ui(
            sender=update_data.get("sender", "Sistema"),
            message=update_data.get("message", "[mensagem vazia]"),
            color_key=update_data.get("color_key")
        )
    elif update_type == "status":
        update_status_on_ui(
            icon_name_key=update_data.get("icon"),
            message=update_data.get("text", "...")
        )
    else:
        ui_logger.warning(f"Tipo de atualização da UI desconhecido recebido: {update_type}")
        add_log_message_on_ui("Sistema", f"Alerta: atualização UI desconhecida - {update_data}", "system_error")

    if _page_instance_for_updates.client_storage: # Garante que a página ainda está conectada
        _page_instance_for_updates.update()

def process_ui_updates_loop():
    global _page_instance_for_updates # Precisa da instância da página para page.call_soon_threadsafe
    ui_logger.info("Thread de processamento de UI (process_ui_updates_loop) iniciada.")
    while not _ui_update_processor_thread_stop_event.is_set():
        try:
            update = ui_update_queue.get(block=True, timeout=0.2) # Reduzido timeout para checar stop_event mais rápido
            if update == EXIT_SIGNAL: # Processa EXIT_SIGNAL para esta thread também
                ui_logger.info("EXIT_SIGNAL recebido na ui_update_queue. Encerrando processador de UI.")
                break
            if _page_instance_for_updates: # Garante que a página existe
                _page_instance_for_updates.call_soon_threadsafe(lambda u=update: handle_actual_ui_update(u))
            else: # Se a página não estiver mais lá, não há o que fazer.
                ui_logger.warning("Instância da página não disponível para call_soon_threadsafe. Encerrando loop de UI.")
                break
        except queue.Empty:
            continue # Normal, timeout para permitir verificação do stop_event
        except Exception as e:
            ui_logger.error(f"Exceção no loop de atualização da UI: {e}", exc_info=True)
            time.sleep(0.5) # Evita spam em caso de erro contínuo
    ui_logger.info("Thread de processamento de UI (process_ui_updates_loop) finalizada.")

# --- Lógica de Eventos da UI ---
def handle_send_command_click(e: ft.ControlEvent):
    user_command_text = ""
    if command_text_field_ref.current and command_text_field_ref.current.value:
        user_command_text = command_text_field_ref.current.value.strip()
        command_text_field_ref.current.value = ""
        command_text_field_ref.current.focus()
    if user_command_text:
        try:
            command_queue.put(user_command_text)
        except Exception as ex:
            ui_logger.error(f"Falha ao colocar comando na command_queue: {ex}")
            # Tentar enviar para a própria fila de UI para mostrar o erro.
            ui_update_queue.put({"type":"log", "sender":"Erro UI", "message":f"Falha ao enviar comando: {ex}", "color_key":"system_error"})
    if _page_instance_for_updates: _page_instance_for_updates.update()

def handle_mic_button_click(e: ft.ControlEvent):
    ui_logger.info("Botão de microfone clicado.")
    if mic_button_ref.current:
        mic_button_ref.current.icon = ICON_MAP.get("settings_voice")
        mic_button_ref.current.tooltip = "Tentando ativar microfone..."
        if _page_instance_for_updates: _page_instance_for_updates.update()
    try:
        command_queue.put(ACTIVATE_VOICE_INPUT_COMMAND)
    except Exception as ex:
        ui_logger.error(f"Falha ao enviar comando de ativação de voz: {ex}")
        ui_update_queue.put({"type":"log", "sender":"Erro UI", "message":f"Falha ao ativar microfone: {ex}", "color_key":"system_error"})
        if mic_button_ref.current: # Resetar botão
            mic_button_ref.current.icon = ICON_MAP.get("mic_off")
            mic_button_ref.current.tooltip = "Ativar Microfone"
            if _page_instance_for_updates: _page_instance_for_updates.update()

def on_window_event_handler(e: ft.ControlEvent):
    global _ui_processor_thread
    if e.data == "close":
        ui_logger.info("Evento de fechamento de janela detectado.")
        _ui_update_processor_thread_stop_event.set()
        if _ui_processor_thread and _ui_processor_thread.is_alive():
            ui_logger.info("Enviando EXIT_SIGNAL para ui_update_queue para desbloquear a thread de UI.")
            ui_update_queue.put(EXIT_SIGNAL) # Para desbloquear o get da thread de UI
            _ui_processor_thread.join(timeout=2) # Esperar a thread de UI updates
            if _ui_processor_thread.is_alive():
                ui_logger.warning("Timeout ao esperar a thread de UI updates terminar.")

        stop_jarvis_core_thread() # Sinaliza e espera pela thread do core

        ui_logger.info("Aplicação Flet desconectando e destruindo janela.")
        e.page.window_destroy()

# --- Função Principal da Aplicação Flet ---
def main_flet_app(page: ft.Page):
    global _ui_processor_thread
    set_page_instance_for_updates(page)
    page.title = "Jarvis"
    page.vertical_alignment = ft.MainAxisAlignment.STRETCH
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.window_height = 650
    page.window_width = 500
    page.on_window_event = on_window_event_handler

    status_bar = ft.Row(
        [ft.Icon(ref=status_icon_ref, name=ICON_MAP["settings_applications"], color=COLOR_MAP["system_init"], size=18),
         ft.Text(ref=status_text_ref, value="Inicializando...", weight=ft.FontWeight.BOLD, size=12)],
        alignment=ft.MainAxisAlignment.CENTER, spacing=8, height=30,
    )
    # Adicionar um Text invisível no final do log para poder rolar até ele
    scroll_target_dummy = ft.Text(value="", key="chat_log_scroll_end", size=1)

    chat_log_column = ft.Column(
        ref=chat_log_column_ref, scroll=ft.ScrollMode.ADAPTIVE, expand=True, spacing=6,
        controls=[
            ft.Text("Bem-vindo! Jarvis Core está iniciando...", italic=True, size=11, color=COLOR_MAP["system_info"]),
            scroll_target_dummy # Adicionar o dummy aqui
            ]
    )
    chat_log_container = ft.Container(
        content=chat_log_column, expand=True,
        border=ft.border.all(1, ft.colors.with_opacity(0.2, ft.colors.PRIMARY)),
        border_radius=ft.border_radius.all(5), padding=10, margin=ft.margin.symmetric(vertical=5)
    )
    command_input_field = ft.TextField(
        ref=command_text_field_ref, hint_text="Digite comando ou clique no microfone",
        expand=True, border_radius=ft.border_radius.all(5),
        on_submit=handle_send_command_click, text_size=13,
        border_color=ft.colors.PRIMARY, focused_border_color=ft.colors.SECONDARY_ACCENT,
    )
    send_command_button = ft.IconButton(
        icon=ft.icons.SEND_ROUNDED, tooltip="Enviar comando", on_click=handle_send_command_click,
        icon_color=ft.colors.PRIMARY, icon_size=20
    )
    mic_button = ft.IconButton(
        ref=mic_button_ref, icon=ICON_MAP["mic_off"], tooltip="Ativar Microfone",
        on_click=handle_mic_button_click, icon_color=ft.colors.PRIMARY, icon_size=20
    )
    input_bar = ft.Row(
        [command_input_field, send_command_button, mic_button],
        vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=5,
    )
    page.add(status_bar, ft.Divider(height=1, color=ft.colors.with_opacity(0.15, ft.colors.PRIMARY)), chat_log_container, input_bar)

    ui_logger.info("Interface Flet construída. Solicitando início do Jarvis Core...")
    start_jarvis_core_thread()

    _ui_processor_thread = threading.Thread(target=process_ui_updates_loop, args=(page, ui_update_queue), daemon=True, name="UIUpdateThread")
    _ui_processor_thread.start()

    page.update()


if __name__ == "__main__":
    ui_logger.info("Iniciando aplicação Flet Jarvis UI...")
    ft.app(target=main_flet_app)
    ui_logger.info("Aplicação Flet encerrada. Garantindo parada do Core (se ainda não parado)...")
    if not JARVIS_CORE_STOP_EVENT.is_set(): # Se on_window_event não foi chamado ou falhou em parar o core
        stop_jarvis_core_thread()
    if _ui_processor_thread and _ui_processor_thread.is_alive(): # Se a thread de UI não parou
        _ui_update_processor_thread_stop_event.set()
        ui_update_queue.put(EXIT_SIGNAL) # Para desbloquear o get
        _ui_processor_thread.join(timeout=1)
    ui_logger.info("Programa Jarvis UI finalizado.")

```
