# jarvis_core.py
"""
Este é o script principal para o assistente de voz Jarvis.
Orquestra o fluxo da aplicação em uma thread separada, comunicando-se
com a interface do usuário (UI) através de filas thread-safe.
"""
import os
import time
import threading
import queue
import logging # Adicionado para logging
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

# Configuração básica do logging
# Em uma aplicação maior, isso viria de um arquivo de configuração.
logging.basicConfig(
    level=logging.INFO, # Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format='%(asctime)s - %(threadName)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__) # Logger específico para este módulo

# Carregar variáveis de ambiente
load_dotenv()

# --- Importações de Módulos do Projeto ---
try:
    from shared_queues import command_queue, ui_update_queue, EXIT_SIGNAL
    from skill_manager import SkillManager
    from voice_recognizer import listen_and_transcribe
    from llm_interpreter import get_command_interpretation
except ImportError as e:
    logger.critical(f"Falha ao importar módulos essenciais: {e}. Encerrando.")
    exit(1)

# --- Configurações Globais ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
LEARNED_SKILLS_FILENAME = "learned_terminal_skills.json"
WAKE_WORD = "jarvis"
MAX_CONVERSATION_HISTORY = 10
JARVIS_CORE_STOP_EVENT = threading.Event()
ACTIVATE_VOICE_INPUT_COMMAND = "ACTIVATE_VOICE_INPUT_FROM_GUI"

def _add_to_history(history: List[Dict[str, str]], role: str, content: str) -> None:
    history.append({"role": role, "content": content})
    if len(history) > MAX_CONVERSATION_HISTORY:
        del history[:len(history) - MAX_CONVERSATION_HISTORY]

def _send_ui_update(type: str, **kwargs: Any) -> None:
    """Envia uma mensagem formatada para a fila de atualização da UI."""
    # Garantir que 'icon' e 'color_key' sejam usados consistentemente se presentes
    payload = {"type": type}
    if "text" in kwargs: payload["text"] = kwargs["text"]
    if "icon" in kwargs: payload["icon"] = kwargs["icon"] # UI espera 'icon'
    if "sender" in kwargs: payload["sender"] = kwargs["sender"]
    if "message" in kwargs: payload["message"] = kwargs["message"]
    if "color_key" in kwargs: payload["color_key"] = kwargs["color_key"] # UI espera 'color_key'

    # logger.debug(f"Enviando para UI Queue: {payload}")
    ui_update_queue.put(payload)

def _voice_status_update_handler(message: str, icon_name: Optional[str]):
    _send_ui_update("status", text=message, icon=icon_name)


def jarvis_thread_main_loop():
    logger.info("Jarvis Core Thread iniciando...")
    if not GOOGLE_API_KEY:
        error_msg = "ERRO CRÍTICO: GOOGLE_API_KEY não definida. Jarvis não pode funcionar."
        _send_ui_update("status", text="ERRO: API Key Ausente!", icon="error_outline")
        _send_ui_update("log", sender="Sistema", message=error_msg, color_key="system_error")
        logger.critical("GOOGLE_API_KEY não definida. Thread encerrando.")
        return

    _send_ui_update("status", text="Inicializando Jarvis...", icon="settings_applications")

    skill_manager_instance = SkillManager()
    conversation_history: List[Dict[str, str]] = []

    skill_manager_instance.load_skills_from_directory("core_skills")
    skill_manager_instance.load_skills_from_json(LEARNED_SKILLS_FILENAME)

    num_skills = len(skill_manager_instance.get_all_skills())
    log_msg_skills = f"{num_skills} skill(s) prontas." if num_skills > 0 else "AVISO: Nenhuma skill carregada."
    _send_ui_update("log", sender="Sistema", message=log_msg_skills, color_key="system_info" if num_skills > 0 else "system_error")

    _send_ui_update("status", text="Aguardando comando...", icon="mic_none")
    logger.info("Jarvis pronto. Aguardando comandos.")

    while not JARVIS_CORE_STOP_EVENT.is_set():
        command_to_process: Optional[str] = None
        source_of_command: str = "Sistema"
        raw_command_from_queue: Optional[str] = None

        try:
            raw_command_from_queue = command_queue.get(block=True, timeout=0.5) # Reduzido timeout para checar stop_event mais frequentemente

            if raw_command_from_queue == EXIT_SIGNAL:
                logger.info("Sinal de saída recebido da command_queue. Encerrando.")
                JARVIS_CORE_STOP_EVENT.set()
                break

            if raw_command_from_queue == ACTIVATE_VOICE_INPUT_COMMAND:
                source_of_command = "Voz (UI)"
                _send_ui_update("log", sender=source_of_command, message="Ativação por voz solicitada...", color_key="user")
                try:
                    command_to_process = listen_and_transcribe(
                        status_callback=_voice_status_update_handler,
                        timeout=7, phrase_time_limit=15
                    )
                    if command_to_process:
                         _send_ui_update("log", sender=source_of_command, message=f"Comando capturado: \"{command_to_process}\"", color_key="jarvis_success") # Cor verde para sucesso
                    else:
                        # voice_recognizer já enviou status via callback
                        _send_ui_update("log", sender=source_of_command, message="Nenhum comando de voz capturado.", color_key="jarvis_warning")
                        # Status já foi resetado pelo callback do voice_recognizer para mic_off ou similar
                except Exception as e:
                    error_msg = f"Erro durante reconhecimento de voz: {e}"
                    logger.error(error_msg, exc_info=True)
                    _send_ui_update("log", sender="Sistema", message=error_msg, color_key="system_error")
                    _send_ui_update("status", text="Erro no microfone.", icon="mic_off")
            else:
                source_of_command = "Texto (UI)"
                command_to_process = raw_command_from_queue
                _send_ui_update("log", sender=source_of_command, message=f"\"{command_to_process}\"", color_key="user")

        except queue.Empty:
            pass
        except Exception as e: # Captura erro inesperado ao ler da fila
            logger.error(f"Erro ao ler da command_queue: {e}", exc_info=True)
            time.sleep(1) # Evita loop rápido em caso de erro contínuo na fila
            continue


        if JARVIS_CORE_STOP_EVENT.is_set(): break

        if command_to_process:
            try: # Bloco try para todo o processamento do comando
                logger.info(f"Processando comando '{command_to_process}' de '{source_of_command}'")
                _send_ui_update("status", text=f"Processando: {command_to_process[:25]}...", icon="hourglass_empty")
                _add_to_history(conversation_history, "user", command_to_process)

                skill_summaries = skill_manager_instance.get_skill_summaries_for_llm()
                if not skill_summaries:
                    response_text = "Desculpe, não tenho skills configuradas."
                    _send_ui_update("log", sender="Jarvis", message=response_text, color_key="jarvis_warning")
                    _add_to_history(conversation_history, "model", response_text)
                    _send_ui_update("status", text="Aguardando comando...", icon="mic_none")
                    continue

                action_list = get_command_interpretation(
                    command_to_process, skill_summaries, history=conversation_history[:-1]
                )

                final_response_parts: List[str] = []
                if action_list:
                    _send_ui_update("log", sender="Jarvis",
                                    message=f"LLM planejou {len(action_list)} ação(ões).",
                                    color_key="system_info") # Cinza para info do sistema
                    for i, action in enumerate(action_list):
                        if JARVIS_CORE_STOP_EVENT.is_set(): break

                        skill_name = action.get("chosen_skill")
                        params = action.get("provided_parameters", {})

                        action_feedback = ""
                        skill_executed_successfully = False
                        if skill_name and skill_name.lower() != "desconhecida" and skill_name is not None:
                            skill = skill_manager_instance.get_skill(skill_name)
                            if skill:
                                step_msg = f"Executando '{skill.name}' (passo {i+1}/{len(action_list)})..."
                                _send_ui_update("log", sender="Jarvis", message=step_msg, color_key="jarvis_info") # Azul para info de execução
                                _send_ui_update("status", text=f"Executando: {skill.name}", icon="play_arrow")
                                try:
                                    result = skill.execute(params)
                                    action_feedback = result # Resultado direto da skill
                                    final_response_parts.append(action_feedback)
                                    skill_executed_successfully = True
                                except Exception as e:
                                    logger.error(f"Erro executando skill '{skill.name}': {e}", exc_info=True)
                                    action_feedback = f"Desculpe, problema ao executar '{skill.name}'."
                                    final_response_parts.append(action_feedback)
                            else:
                                action_feedback = f"Habilidade '{skill_name}' planejada, mas não encontrada."
                                final_response_parts.append(action_feedback)
                        else:
                            action_feedback = f"Não entendi uma parte do seu pedido (skill: {skill_name})."
                            final_response_parts.append(action_feedback)

                        _send_ui_update("log", sender="Jarvis", message=action_feedback,
                                        color_key="jarvis_success" if skill_executed_successfully else "jarvis_warning")
                        if len(action_list) > 1 and not JARVIS_CORE_STOP_EVENT.is_set(): time.sleep(0.5)

                    overall_response = " ".join(final_response_parts) if final_response_parts else "Nenhuma ação específica foi executada."
                    if len(final_response_parts) > 1 : overall_response = "Sequência concluída. " + overall_response
                else:
                    overall_response = "Desculpe, não consegui interpretar seu comando para uma ação específica."

                _send_ui_update("log", sender="Jarvis", message=overall_response,
                                color_key="jarvis_success" if action_list and final_response_parts else "jarvis_warning")
                _add_to_history(conversation_history, "model", overall_response)

            except Exception as e: # Captura exceções do processamento do comando (LLM, Skill execution etc.)
                logger.error(f"Erro durante o processamento do comando '{command_to_process}': {e}", exc_info=True)
                error_response = f"Desculpe, ocorreu um erro inesperado ao processar seu comando: '{command_to_process[:30]}...'"
                _send_ui_update("log", sender="Jarvis", message=error_response, color_key="system_error")
                _add_to_history(conversation_history, "model", error_response) # Adicionar erro ao histórico
            finally:
                if not JARVIS_CORE_STOP_EVENT.is_set():
                    _send_ui_update("status", text="Aguardando comando...", icon="mic_none")

    logger.info("Loop principal de Jarvis encerrado.")
    _send_ui_update("status", text="Jarvis desligado.", icon="power_settings_new")
    _send_ui_update("log", sender="Sistema", message="Processo Jarvis Core finalizado.", color_key="system_info")

_jarvis_core_thread = None

def start_jarvis_core_thread():
    global _jarvis_core_thread
    if _jarvis_core_thread and _jarvis_core_thread.is_alive():
        logger.info("Thread do Jarvis Core já está em execução.")
        return
    JARVIS_CORE_STOP_EVENT.clear()
    _jarvis_core_thread = threading.Thread(target=jarvis_thread_main_loop, daemon=True, name="JarvisCoreThread")
    _jarvis_core_thread.start()
    logger.info("Thread do Jarvis Core iniciada.")

def stop_jarvis_core_thread():
    global _jarvis_core_thread
    if _jarvis_core_thread and _jarvis_core_thread.is_alive():
        logger.info("Enviando sinal de parada para a thread do Jarvis Core...")
        JARVIS_CORE_STOP_EVENT.set()
        try:
            command_queue.put_nowait(EXIT_SIGNAL) # Tenta não bloquear se a fila estiver cheia
        except queue.Full:
            logger.warning("Command queue cheia ao tentar enviar EXIT_SIGNAL. A thread pode demorar a parar.")
            # A thread ainda deve parar devido ao JARVIS_CORE_STOP_EVENT.is_set() no loop principal.

        _jarvis_core_thread.join(timeout=3) # Reduzido timeout do join
        if _jarvis_core_thread.is_alive():
            logger.warning("Timeout ao esperar a thread do Jarvis Core terminar. Pode ser necessário forçar o encerramento do programa.")
        else:
            logger.info("Thread do Jarvis Core finalizada.")
    else:
        logger.info("Thread do Jarvis Core não estava em execução ou já foi finalizada.")

if __name__ == '__main__':
    logger.info("Iniciando Jarvis Core em modo de teste de console direto.")
    start_jarvis_core_thread()
    try:
        while not JARVIS_CORE_STOP_EVENT.is_set(): # Loop principal para o teste de console
            cmd = input("Digite comando ('ACTIVATE_VOICE', 'sair', ou comando direto): ")
            if cmd.lower() == 'sair':
                break # Sai do loop de input, o finally cuidará de parar a thread
            elif cmd.upper() == ACTIVATE_VOICE_INPUT_COMMAND or cmd.lower() == 'voz': # Alias
                 command_queue.put(ACTIVATE_VOICE_INPUT_COMMAND)
            else:
                command_queue.put(cmd)

            time.sleep(0.1)
            try:
                while not ui_update_queue.empty(): # Drena a fila de UI
                    print(f"UI << {ui_update_queue.get_nowait()}")
            except queue.Empty: pass
    except KeyboardInterrupt:
        logger.info("Interrupção de teclado recebida no teste de console.")
    finally:
        logger.info("Teste de console finalizando. Solicitando parada do Jarvis Core...")
        stop_jarvis_core_thread()
        logger.info("Teste de console finalizado.")

```
