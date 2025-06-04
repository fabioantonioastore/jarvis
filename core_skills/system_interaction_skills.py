# core_skills/system_interaction_skills.py
"""
Este módulo define habilidades (skills) nativas para Jarvis que interagem
com o sistema operacional do usuário, como abrir aplicativos e pesquisar na web.

Cada habilidade é definida como uma instância da classe `Skill` e é adicionada
à lista `skills_to_register` para que o `SkillManager` possa descobri-las
e registrá-las automaticamente.
"""
import subprocess
import webbrowser
import platform
from typing import Dict, Any, List

# Tenta importar a interface Skill. Se skill_interface.py estiver na raiz do projeto
# e core_skills for um subdiretório, esta importação pode precisar de ajuste
# no sys.path, o que é geralmente tratado pelo SkillManager ao carregar.
try:
    from skill_interface import Skill, ParameterDefinition
except ImportError:
    # Fallback para o caso de execução direta do script ou problemas de path não resolvidos.
    # Em execução normal via jarvis_core.py, o SkillManager deve ajustar o sys.path.
    print("AVISO [system_interaction_skills]: Não foi possível importar 'Skill' de 'skill_interface'. "
          "Isso é esperado se executado diretamente fora do contexto do projeto principal.")
    # Definir dummies para permitir que o script seja pelo menos parsable se executado isoladamente.
    class ParameterDefinition(dict): pass
    from dataclasses import dataclass
    @dataclass
    class Skill: name: str; description_for_llm: str; parameters_expected: List; execute: Any

# Mapeamentos de nomes amigáveis para comandos/nomes de aplicativos por SO.
# Esta lista pode ser expandida para suportar mais aplicativos e variações de nomes.
# Para Linux, os nomes dos executáveis podem variar entre distribuições e ambientes de desktop.
# Os valores aqui são sugestões comuns.
APP_MAPPINGS = {
    "Windows": {
        "calculadora": "calc.exe",
        "bloco de notas": "notepad.exe",
        "notepad": "notepad.exe",
        "chrome": "chrome.exe",
        "firefox": "firefox.exe",
        "edge": "msedge.exe",
        "navegador": "msedge.exe", # Considerado o navegador padrão para Windows.
        "explorer": "explorer.exe", # Para abrir o explorador de arquivos.
        "cmd": "cmd.exe",           # Para abrir o Prompt de Comando.
        "powershell": "powershell.exe", # Para abrir o PowerShell.
    },
    "Linux": {
        "calculadora": "gnome-calculator", # Comum no GNOME. Alternativas: kcalc (KDE), mate-calc (MATE).
        "editor de texto": "gedit",     # Comum no GNOME. Alternativas: kate (KDE), xed (Cinnamon), mousepad (XFCE).
        "terminal": "gnome-terminal", # Comum no GNOME. Alternativas: konsole (KDE), xfce4-terminal (XFCE).
        "firefox": "firefox",
        "chrome": "google-chrome",
        "chromium": "chromium-browser", # Ou apenas "chromium" em algumas distribuições.
        "navegador": "firefox",         # Define um navegador padrão se "navegador" for pedido.
                                        # Idealmente, o sistema usaria xdg-open com uma URL para o padrão real.
        "arquivos": "nautilus",         # Comum no GNOME. Alternativas: dolphin (KDE), caja (MATE).
    },
    "Darwin": { # macOS
        "calculadora": "Calculator",    # Aplicativos no macOS são referenciados pelo nome do bundle (ex: Calculator.app).
        "editor de texto": "TextEdit",  # O comando 'open -a TextEdit' os encontra.
        "textedit": "TextEdit",
        "terminal": "Terminal",
        "safari": "Safari",
        "chrome": "Google Chrome",
        "firefox": "Firefox",
        "navegador": "Safari",          # Navegador padrão do macOS.
        "finder": "Finder",             # Para abrir o Finder.
    }
}

def execute_open_application(parameters: Dict[str, Any]) -> str:
    """
    Função de execução para a habilidade 'open_application'.
    Abre um aplicativo com base no nome fornecido e no sistema operacional.

    Args:
        parameters (Dict[str, Any]): Um dicionário esperando a chave "app_name"
                                     com o nome do aplicativo a ser aberto.

    Returns:
        str: Mensagem indicando o resultado da ação (sucesso ou tipo de erro).
    """
    app_name = parameters.get("app_name")
    if not app_name or not isinstance(app_name, str): # Validação adicional do tipo
        return "AVISO [Skill:open_application]: O nome do aplicativo (parâmetro 'app_name') não foi fornecido ou é inválido."

    current_system = platform.system()
    app_name_lower = app_name.lower() # Normalizar para minúsculas para correspondência no dicionário

    if current_system not in APP_MAPPINGS:
        return f"ERRO [Skill:open_application]: Sistema operacional '{current_system}' não é atualmente suportado para abrir aplicativos diretamente por esta skill."

    # Obter o comando/nome do aplicativo do mapeamento específico do SO
    app_command_or_name = APP_MAPPINGS[current_system].get(app_name_lower)

    if not app_command_or_name:
        # Se não houver mapeamento direto, tentar usar o nome diretamente como um comando.
        # Isso é mais provável de funcionar em Linux/macOS para executáveis no PATH.
        if current_system in ["Linux", "Darwin"]:
            app_command_or_name = app_name # Tenta o nome original (não normalizado) se desejado, ou app_name_lower
            print(f"INFO [Skill:open_application]: Aplicativo '{app_name}' não encontrado no mapeamento para '{current_system}'. Tentando executar diretamente como '{app_command_or_name}'.")
        else: # Windows geralmente requer um executável conhecido ou o uso de 'start'.
            return f"AVISO [Skill:open_application]: Aplicativo '{app_name}' não é reconhecido ou mapeado para o sistema operacional '{current_system}'."

    command_to_log = app_command_or_name # Para mensagens de log/retorno

    try:
        if current_system == "Windows":
            # Usar 'start' com shell=True é geralmente robusto para iniciar aplicativos GUI
            # e desanexar o processo. O segundo argumento vazio é um placeholder para o título da janela.
            subprocess.Popen(['start', '', app_command_or_name], shell=True)
            command_to_log = f"start '' {app_command_or_name}" # Reflete o comando real usado
        elif current_system == "Linux":
            subprocess.Popen([app_command_or_name]) # Executa o comando diretamente
        elif current_system == "Darwin": # macOS
            subprocess.Popen(['open', '-a', app_command_or_name]) # 'open -a <AppName>' é o padrão

        return f"Jarvis está tentando abrir o aplicativo '{app_name}' (comando: {command_to_log})."

    except FileNotFoundError:
        return f"ERRO [Skill:open_application]: O comando/aplicativo '{command_to_log}' não foi encontrado. Verifique se '{app_name}' está instalado e configurado corretamente no PATH do sistema."
    except Exception as e:
        return f"ERRO [Skill:open_application]: Falha inesperada ao tentar abrir o aplicativo '{app_name}' (comando: '{command_to_log}'): {e}"

def execute_search_web(parameters: Dict[str, Any]) -> str:
    """
    Função de execução para a habilidade 'search_web'.
    Abre o navegador padrão com uma pesquisa no Google.

    Args:
        parameters (Dict[str, Any]): Um dicionário esperando a chave "query"
                                     com o termo de pesquisa.

    Returns:
        str: Mensagem indicando o resultado da ação.
    """
    query = parameters.get("query")
    if not query or not isinstance(query, str): # Validação adicional
        return "AVISO [Skill:search_web]: O termo de pesquisa (parâmetro 'query') não foi fornecido ou é inválido."

    try:
        # webbrowser.open lida com a codificação da URL e a abertura no navegador padrão.
        url = f"https://www.google.com/search?q={query}"
        webbrowser.open(url)
        return f"Jarvis pesquisou por '{query}' na web e tentou abrir no seu navegador padrão."
    except Exception as e:
        return f"ERRO [Skill:search_web]: Falha ao tentar abrir o navegador para pesquisar '{query}': {e}"

# --- Definição das Instâncias de Skill ---

open_application_skill = Skill(
    name="open_application",
    description_for_llm="Abre um aplicativo especificado no computador do usuário. Use para comandos como 'abrir calculadora', 'iniciar chrome', 'executar editor de texto'.",
    parameters_expected=[
        ParameterDefinition(name="app_name", type="string", description="O nome amigável do aplicativo a ser aberto (ex: 'calculadora', 'chrome', 'bloco de notas', 'navegador', 'terminal').", required=True)
    ],
    execute=execute_open_application
)

search_web_skill = Skill(
    name="search_web",
    description_for_llm="Realiza uma pesquisa na internet usando o Google com o termo ou pergunta fornecida e abre os resultados no navegador padrão do sistema.",
    parameters_expected=[
        ParameterDefinition(name="query", type="string", description="O termo, frase ou pergunta completa a ser pesquisada na internet.", required=True)
    ],
    execute=execute_search_web
)

# --- Lista de Skills para Registro ---
# Esta lista é o que o SkillManager procurará para registrar as habilidades deste módulo.
skills_to_register: List[Skill] = [
    open_application_skill,
    search_web_skill,
]

# Bloco de teste para execução direta do script (útil para depuração isolada das skills)
if __name__ == '__main__':
    print(f"Testando habilidades de system_interaction_skills.py em: {platform.system()}")

    print("\n--- Testando a Skill 'open_application' ---")
    test_apps = ["calculadora", "navegador", "editor de texto", "aplicativo_que_nao_existe_test_123"]
    for app in test_apps:
        params = {"app_name": app}
        print(f"Comando: Abrir '{app}', Parâmetros: {params}")
        print(f"Resultado: {execute_open_application(params)}\n")

    print("Testando 'open_application' sem parâmetro 'app_name':")
    print(f"Resultado: {execute_open_application({})}\n")

    print("--- Testando a Skill 'search_web' ---")
    test_queries = ["ultimas noticias sobre IA no Brasil", "Python programming best practices"]
    for q_query in test_queries:
        params = {"query": q_query}
        print(f"Comando: Pesquisar '{q_query}', Parâmetros: {params}")
        print(f"Resultado: {execute_search_web(params)}\n")

    print("Testando 'search_web' sem parâmetro 'query':")
    print(f"Resultado: {execute_search_web({})}\n")

```
