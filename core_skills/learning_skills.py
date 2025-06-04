# core_skills/learning_skills.py
"""
Este módulo define a habilidade (skill) nativa que permite a Jarvis "aprender"
novos comandos de terminal.

A habilidade 'learn_new_terminal_skill' recebe do usuário (via LLM) os detalhes
de um novo comando, como seu nome, descrição, o template do comando shell
e os parâmetros que esse template espera. Essas informações são então salvas
em um arquivo JSON (`learned_terminal_skills.json`) para persistência.

O SkillManager pode, posteriormente, carregar essas habilidades aprendidas do
arquivo JSON e torná-las executáveis, tratando-as de forma semelhante às
habilidades nativas.
"""
import json
import os
from typing import Dict, Any, List, cast

# Tenta importar a interface Skill. Ajustes de path são geralmente tratados pelo SkillManager.
try:
    from skill_interface import Skill, ParameterDefinition
except ImportError:
    print("AVISO [learning_skills]: Não foi possível importar 'Skill' de 'skill_interface'.")
    # Dummies para permitir parsing se executado isoladamente.
    class ParameterDefinition(dict): pass
    from dataclasses import dataclass
    @dataclass
    class Skill: name: str; description_for_llm: str; parameters_expected: List; execute: Any


LEARNED_SKILLS_FILE = "learned_terminal_skills.json" # Arquivo para armazenar habilidades de terminal aprendidas.

def execute_learn_new_terminal_skill(parameters: Dict[str, Any]) -> str:
    """
    Função de execução para a skill 'learn_new_terminal_skill'.
    Valida os parâmetros fornecidos, cria uma nova definição de habilidade de terminal
    e a salva no arquivo JSON de habilidades aprendidas.

    Args:
        parameters (Dict[str, Any]): Dicionário contendo os detalhes da nova habilidade,
                                     incluindo 'new_skill_name', 'new_skill_description',
                                     'shell_command_template', e 'template_parameters'.

    Returns:
        str: Mensagem indicando sucesso ou o tipo de erro encontrado.
    """
    new_skill_name = parameters.get("new_skill_name")
    new_skill_description = parameters.get("new_skill_description")
    shell_command_template = parameters.get("shell_command_template")
    template_parameters_any = parameters.get("template_parameters") # Espera-se List[str]

    # --- Validação dos Parâmetros Essenciais ---
    required_params_map = {
        "new_skill_name": new_skill_name,
        "new_skill_description": new_skill_description,
        "shell_command_template": shell_command_template,
        # template_parameters é opcional para comandos sem placeholders, então é validado separadamente.
    }
    missing_essential_params = [key for key, value in required_params_map.items() if not value]
    if missing_essential_params:
        return f"ERRO [LearnSkill]: Parâmetros obrigatórios ausentes para aprender nova habilidade: {', '.join(missing_essential_params)}."

    # --- Validação de Tipos ---
    if not isinstance(new_skill_name, str) or \
       not isinstance(new_skill_description, str) or \
       not isinstance(shell_command_template, str):
        return "ERRO [LearnSkill]: 'new_skill_name', 'new_skill_description', e 'shell_command_template' devem ser strings."

    template_parameters: List[str] = [] # Inicializa com tipo correto
    if template_parameters_any is None:
        template_parameters = [] # Lista vazia é válida se não houver placeholders no template
    elif isinstance(template_parameters_any, list) and all(isinstance(item, str) for item in template_parameters_any):
        # Garante que se fornecido, é uma lista de strings.
        template_parameters = cast(List[str], template_parameters_any)
    else:
        return "ERRO [LearnSkill]: 'template_parameters' deve ser uma lista de strings (nomes dos placeholders no template) ou não ser fornecido se não houver placeholders."

    # --- Carregar Habilidades Aprendidas Existentes ---
    learned_skills: List[Dict[str, Any]] = []
    if os.path.exists(LEARNED_SKILLS_FILE):
        try:
            with open(LEARNED_SKILLS_FILE, "r", encoding="utf-8") as f:
                # Verifica se o arquivo não está vazio antes de tentar carregar JSON
                content = f.read()
                if content.strip(): # Se houver conteúdo não vazio
                    learned_skills = json.loads(content)
                    if not isinstance(learned_skills, list):
                        print(f"AVISO [LearnSkill]: Conteúdo de '{LEARNED_SKILLS_FILE}' não é uma lista JSON. Iniciando com lista vazia.")
                        learned_skills = []
                else: # Arquivo está vazio
                    learned_skills = []
        except json.JSONDecodeError:
            print(f"AVISO [LearnSkill]: Erro ao decodificar JSON de '{LEARNED_SKILLS_FILE}'. Pode estar corrompido ou malformado. Iniciando com lista vazia.")
            learned_skills = []
        except Exception as e: # Outros erros de I/O
            print(f"ERRO [LearnSkill]: Falha ao ler o arquivo '{LEARNED_SKILLS_FILE}': {e}. Iniciando com lista vazia.")
            learned_skills = []

    # --- Lógica de Negócio da Skill ---
    # Verificar se uma habilidade com o mesmo nome já existe para evitar duplicatas.
    # TODO: No futuro, permitir 'overwrite' ou 'update' como um parâmetro opcional da skill.
    if any(skill.get("name") == new_skill_name for skill in learned_skills):
        return f"ERRO [LearnSkill]: Uma habilidade de terminal com o nome '{new_skill_name}' já foi aprendida. Escolha um nome diferente."

    # Verificar se os placeholders em shell_command_template correspondem aos template_parameters
    # Ex: template "echo {{msg}} {{user}}" e params ["msg"] -> erro, "user" não está nos params
    # Ex: template "echo {{msg}}" e params ["msg", "user"] -> ok, "user" é extra mas não usado.
    # Ex: template "echo" e params ["msg"] -> erro, "msg" não está no template.
    # Esta validação ajuda a garantir que o template seja executável com os parâmetros definidos.
    import re
    placeholders_in_template = set(re.findall(r"\{\{([\w_]+)\}\}", shell_command_template))

    # Todos os placeholders no template DEVEM estar listados em template_parameters
    if not placeholders_in_template.issubset(set(template_parameters)):
        missing_in_params_list = placeholders_in_template - set(template_parameters)
        return (f"ERRO [LearnSkill]: Os seguintes placeholders estão no 'shell_command_template' mas não foram declarados em "
                f"'template_parameters': {list(missing_in_params_list)}. "
                f"Template: '{shell_command_template}', Declarados: {template_parameters}")

    # (Opcional) Avisar se há parâmetros declarados que não estão no template
    # if not set(template_parameters).issubset(placeholders_in_template):
    #     extra_in_params_list = set(template_parameters) - placeholders_in_template
    #     print(f"AVISO [LearnSkill]: Os seguintes 'template_parameters' foram declarados mas não são usados no "
    #           f"'shell_command_template': {list(extra_in_params_list)}. Eles serão ignorados.")
    #     # Filtrar template_parameters para apenas os que estão no template pode ser uma opção
    #     # template_parameters = [p for p in template_parameters if p in placeholders_in_template]


    new_skill_data = {
        "name": new_skill_name,
        "description_for_llm": new_skill_description,
        "type": "terminal_command",  # Identificador para o SkillManager saber como carregar/executar.
        "shell_command_template": shell_command_template,
        "template_parameters": sorted(list(set(template_parameters))) # Armazena a lista sanitizada.
    }

    learned_skills.append(new_skill_data)
    try:
        with open(LEARNED_SKILLS_FILE, "w", encoding="utf-8") as f:
            json.dump(learned_skills, f, indent=4, ensure_ascii=False)
        return f"Jarvis aprendeu com sucesso a nova habilidade de terminal: '{new_skill_name}'."
    except IOError as e:
        return f"ERRO [LearnSkill]: Falha ao salvar a habilidade aprendida '{new_skill_name}' no arquivo '{LEARNED_SKILLS_FILE}': {e}"
    except Exception as e: # Outros erros inesperados
        return f"ERRO [LearnSkill]: Ocorreu um erro inesperado ao salvar a habilidade '{new_skill_name}': {e}"

# --- Definição da Instância da Skill 'learn_new_terminal_skill' ---
learn_new_terminal_skill = Skill(
    name="learn_new_terminal_skill",
    description_for_llm=(
        "Ensina a Jarvis um novo comando de terminal que pode ser executado posteriormente. "
        "Esta skill é usada para adicionar novas capacidades de linha de comando ao Jarvis. "
        "Você deve fornecer um nome único para a nova habilidade (sem espaços ou caracteres especiais), "
        "uma descrição clara para que Jarvis entenda quando usá-la, "
        "o template do comando shell (com placeholders como '{{nome_do_placeholder}}' para valores dinâmicos), "
        "e uma lista dos nomes exatos desses placeholders."
    ),
    parameters_expected=[
        ParameterDefinition(name="new_skill_name", type="string", description="Nome único e descritivo para a nova habilidade de terminal (ex: 'criar_diretorio_projeto', 'listar_arquivos_grandes'). Use apenas letras, números e underscores.", required=True),
        ParameterDefinition(name="new_skill_description", type="string", description="Descrição clara da nova habilidade para Jarvis entender sua finalidade e quando utilizá-la no futuro.", required=True),
        ParameterDefinition(name="shell_command_template", type="string", description="O comando de terminal completo. Use placeholders no formato '{{placeholder_name}}' para partes que serão fornecidas em tempo de execução (ex: 'mkdir \"{{dir_name}}\"', 'ls -l \"{{caminho}}\"', 'echo \"{{texto_falado}}\" > \"{{nome_arquivo}}\"'). Certifique-se de que os placeholders sejam claramente definidos.", required=True),
        ParameterDefinition(name="template_parameters", type="list_of_string", description="Uma lista de strings contendo os nomes exatos dos placeholders usados no 'shell_command_template' (ex: ['dir_name'] para 'mkdir \"{{dir_name}}\"'; ou ['texto_falado', 'nome_arquivo'] para 'echo \"{{texto_falado}}\" > \"{{nome_arquivo}}\"'). Se não houver placeholders, forneça uma lista vazia [].", required=True)
    ],
    execute=execute_learn_new_terminal_skill
)

# Lista de skills a serem registradas pelo SkillManager quando este módulo for carregado.
skills_to_register: List[Skill] = [
    learn_new_terminal_skill,
]

# Bloco de teste para execução direta do script (útil para depuração isolada da skill de aprendizado)
if __name__ == '__main__':
    print("--- Testando a Skill de Aprendizado (learning_skills.py) ---")

    # Limpar o arquivo de skills aprendidas para um teste limpo, se existir
    if os.path.exists(LEARNED_SKILLS_FILE):
        os.remove(LEARNED_SKILLS_FILE)
        print(f"INFO: Arquivo '{LEARNED_SKILLS_FILE}' removido para teste.")

    test_case_1 = {
        "new_skill_name": "criar_diretorio_teste",
        "new_skill_description": "Cria um novo diretório (pasta) com o nome especificado.",
        "shell_command_template": "mkdir \"{{nome_da_pasta}}\"",
        "template_parameters": ["nome_da_pasta"]
    }
    print(f"\nTestando aprender skill 1: {test_case_1['new_skill_name']}")
    print(f"Resultado: {execute_learn_new_terminal_skill(test_case_1)}")

    test_case_2 = {
        "new_skill_name": "saudacao_em_arquivo",
        "new_skill_description": "Escreve uma saudação personalizada em um arquivo de texto.",
        "shell_command_template": "echo \"Olá, {{nome_pessoa}}! Bem-vindo ao {{local}}.\" > \"{{nome_arquivo}}.txt\"",
        "template_parameters": ["nome_pessoa", "local", "nome_arquivo"]
    }
    print(f"\nTestando aprender skill 2: {test_case_2['new_skill_name']}")
    print(f"Resultado: {execute_learn_new_terminal_skill(test_case_2)}")

    # Tentar aprender skill com nome duplicado
    print(f"\nTentando aprender skill com nome duplicado: {test_case_1['new_skill_name']}")
    print(f"Resultado: {execute_learn_new_terminal_skill(test_case_1)}")

    # Teste com template_parameters vazio (comando sem placeholders)
    test_case_3 = {
        "new_skill_name": "listar_pasta_atual",
        "new_skill_description": "Lista o conteúdo da pasta atual.",
        "shell_command_template": "ls -lah",
        "template_parameters": [] # Lista vazia, pois não há placeholders
    }
    print(f"\nTestando aprender skill 3 (sem placeholders): {test_case_3['new_skill_name']}")
    print(f"Resultado: {execute_learn_new_terminal_skill(test_case_3)}")

    # Teste com placeholder no template mas não declarado em template_parameters
    test_case_4_bad_params = {
        "new_skill_name": "erro_placeholder_nao_declarado",
        "new_skill_description": "Skill com erro de placeholder.",
        "shell_command_template": "echo {{mensagem_secreta}}",
        "template_parameters": [] # Esqueci de declarar "mensagem_secreta"
    }
    print(f"\nTestando aprender skill 4 (placeholder não declarado): {test_case_4_bad_params['new_skill_name']}")
    print(f"Resultado: {execute_learn_new_terminal_skill(test_case_4_bad_params)}")


    # Verificar conteúdo do arquivo JSON
    if os.path.exists(LEARNED_SKILLS_FILE):
        print(f"\nConteúdo final de '{LEARNED_SKILLS_FILE}':")
        with open(LEARNED_SKILLS_FILE, "r", encoding='utf-8') as f:
            print(f.read())
    else:
        print(f"\nERRO DE TESTE: Arquivo '{LEARNED_SKILLS_FILE}' não foi criado.")
```
