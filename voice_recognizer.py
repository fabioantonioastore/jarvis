# voice_recognizer.py
"""
Módulo responsável pela funcionalidade de reconhecimento de voz (Speech-To-Text).
Utiliza a biblioteca SpeechRecognition para capturar áudio do microfone e
transcrevê-lo usando a API do Google Speech Recognition.
"""
import speech_recognition as sr
from typing import Optional, Callable # Adicionado para o callback

# Nomes de ícones Flet (material icons) para status visuais
# Estes são apenas sugestões e podem ser mapeados para ft.icons.<NOME> na UI.
ICON_MIC_READY = "mic_none" # Microfone pronto, aguardando
ICON_LISTENING = "mic" # Microfone ativamente ouvindo
ICON_PROCESSING = "hourglass_empty" # Processando áudio
ICON_MIC_OFF = "mic_off" # Microfone desligado ou erro
ICON_ERROR = "error_outline" # Erro genérico

def listen_and_transcribe(
    timeout: int = 7,  # Tempo para esperar o início da fala
    phrase_time_limit: int = 15, # Duração máxima da frase falada
    status_callback: Optional[Callable[[str, Optional[str]], None]] = None
) -> Optional[str]:
    """
    Captura áudio do microfone, transcreve para texto em português (Brasil)
    e fornece atualizações de status através de uma callback.

    Args:
        timeout (int): Segundos para esperar o início da fala antes de desistir.
        phrase_time_limit (int): Segundos máximos que uma frase pode durar.
        status_callback (Optional[Callable[[str, Optional[str]], None]]):
            Função a ser chamada para atualizações de status.
            Recebe (mensagem_de_texto: str, nome_do_icone_flet: Optional[str]).

    Returns:
        Optional[str]: O texto transcrito, ou None se ocorrer um erro ou timeout.
    """
    r = sr.Recognizer()

    # Tentar obter uma instância do microfone. Pode falhar se nenhum microfone estiver disponível.
    try:
        with sr.Microphone() as source:
            if status_callback:
                status_callback("Ajustando para ruído ambiente...", ICON_PROCESSING)
            try:
                # Ajuste para ruído ambiente para melhor qualidade de reconhecimento.
                # A duração pode ser curta (0.5 a 1 segundo).
                r.adjust_for_ambient_noise(source, duration=0.7)
            except Exception as e:
                # Mesmo que adjust_for_ambient_noise falhe (ex: microfone virtual sem ruído),
                # a escuta ainda pode funcionar.
                message = f"Aviso: Falha ao ajustar para ruído ambiente (pode ser normal em alguns microfones): {e}"
                print(f"AVISO [VoiceRecognizer]: {message}")
                if status_callback:
                    # Informar a UI sobre o aviso, mas continuar.
                    status_callback("Problema menor com microfone, tentando ouvir...", ICON_MIC_READY)


            message = f"Ouvindo comando (timeout: {timeout}s, limite: {phrase_time_limit}s)..."
            if status_callback:
                status_callback(message, ICON_LISTENING)
            else:
                print(message)

            try:
                # Escuta o áudio da fonte (microfone).
                audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

                message = "Processando áudio capturado..."
                if status_callback:
                    status_callback(message, ICON_PROCESSING)
                else:
                    print(message)

                # Tenta transcrever o áudio usando a API do Google.
                texto_transcrito = r.recognize_google(audio, language='pt-BR')

                message = f"Texto transcrito: '{texto_transcrito}'" # Será logado pelo Jarvis Core se bem sucedido
                # Não enviar status de sucesso aqui, pois o core fará isso. Retornar o texto.
                # print(f"INFO [VoiceRecognizer]: {message}") # Log interno
                return texto_transcrito

            except sr.WaitTimeoutError:
                message = "Nenhuma fala detectada dentro do tempo limite."
                if status_callback:
                    status_callback(message, ICON_MIC_OFF)
                else:
                    print(message)
                return None
            except sr.UnknownValueError:
                message = "Não foi possível entender o áudio."
                if status_callback:
                    status_callback(message, ICON_MIC_OFF) # Ou um ícone de "confuso"?
                else:
                    print(message)
                return None
            except sr.RequestError as e:
                message = f"Erro na API de reconhecimento de voz; {e}"
                if status_callback:
                    status_callback(message, ICON_ERROR)
                else:
                    print(message)
                return None
            except Exception as e: # Outros erros durante listen/recognize
                message = f"Erro inesperado durante o reconhecimento de voz: {e}"
                if status_callback:
                    status_callback(message, ICON_ERROR)
                else:
                    print(message)
                return None

    except OSError as e: # Erro comum se o microfone não estiver disponível/configurado
        message = f"Microfone não encontrado ou não operacional. Verifique as configurações de áudio. Erro: {e}"
        if status_callback:
            status_callback(message, ICON_MIC_OFF)
        else:
            print(message)
        return None
    except Exception as e: # Outros erros ao tentar acessar o microfone
        message = f"Erro crítico ao acessar o microfone: {e}"
        if status_callback:
            status_callback(message, ICON_ERROR)
        else:
            print(message)
        return None


if __name__ == '__main__':
    # Bloco de teste para listen_and_transcribe com uma callback simulada.
    print("--- Testando Voice Recognizer com Callback Simulada ---")

    def mock_status_callback(message: str, icon: Optional[str]):
        """Callback simulada que imprime o status e o ícone."""
        print(f"CALLBACK STATUS: [{icon if icon else 'N/A'}] {message}")

    print("\nTeste 1: Tentativa de escuta normal.")
    print("Por favor, fale algo no microfone quando 'Ouvindo...' aparecer.")
    try:
        texto1 = listen_and_transcribe(timeout=5, phrase_time_limit=10, status_callback=mock_status_callback)
        if texto1:
            print(f"Resultado Final Teste 1 (Texto): '{texto1}'")
        else:
            print("Resultado Final Teste 1: Nenhuma transcrição.")
    except Exception as e:
        print(f"Erro no Teste 1: {e}")

    print("\nTeste 2: Teste de timeout (não fale nada).")
    try:
        texto2 = listen_and_transcribe(timeout=3, phrase_time_limit=5, status_callback=mock_status_callback)
        if texto2: # Não deve acontecer se o timeout funcionar
            print(f"Resultado Final Teste 2 (Texto): '{texto2}'")
        else:
            print("Resultado Final Teste 2: Nenhuma transcrição (timeout esperado).")
    except Exception as e:
        print(f"Erro no Teste 2: {e}")

    print("\n--- Testes do Voice Recognizer concluídos ---")
    print("Nota: Se nenhum microfone estiver disponível ou configurado, os testes acima podem falhar ou reportar erro de microfone.")

```
