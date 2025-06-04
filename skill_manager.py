# skill_manager.py
"""
Gerenciador de Habilidades para Jarvis.

Este módulo é responsável por:
- Registrar novas habilidades (skills), tanto as nativas (definidas em Python)
  quanto as aprendidas (comandos de terminal salvos em JSON).
- Carregar habilidades nativas de um diretório especificado (ex: 'core_skills').
- Carregar habilidades de terminal aprendidas de um arquivo JSON.
- Fornecer acesso às habilidades registradas.
- Gerar resumos das habilidades para serem usados pelo LLM na escolha da skill.
- Executar habilidades aprendidas de terminal de forma segura.
"""
import os
import sys
import importlib
import json
import subprocess
from typing import Dict, List, Optional, Any
from skill_interface import Skill, ParameterDefinition

class SkillManager:
    """
    Gerencia o registro, carregamento e recuperação de habilidades (skills) para Jarvis.
    """
    def __init__(self):
        """
        Inicializa o SkillManager.
        Cria um dicionário interno para armazenar as instâncias de Skill registradas.
        """
        self._skills: Dict[str, Skill] = {}
        print("INFO [SkillManager]: SkillManager inicializado.")

    def register_skill(self, skill_instance: Skill, overwrite: bool = False) -> None:
        """
        Registra uma única instância de Skill.

        Args:
            skill_instance (Skill): A instância da habilidade (objeto Skill) a ser registrada.
            overwrite (bool): Se True, permite sobrescrever uma habilidade existente com o mesmo nome.
                              Padrão é False (não sobrescreve e emite um aviso).
        """
        if not isinstance(skill_instance, Skill):
            # Validação para garantir que apenas objetos Skill sejam registrados.
            print(f"ERRO [SkillManager]: Tentativa de registrar um objeto que não é uma Skill válida. Objeto: {type(skill_instance)}")
            return

        skill_name = skill_instance.name
        if skill_name in self._skills and not overwrite:
            print(f"AVISO [SkillManager]: Habilidade '{skill_name}' já registrada. Não foi sobrescrita. Use overwrite=True para forçar.")
        else:
            self._skills[skill_name] = skill_instance
            action = "sobrescrita" if overwrite and skill_name in self._skills else "registrada"
            print(f"INFO [SkillManager]: Habilidade '{skill_name}' {action} com sucesso.")

    def get_skill(self, skill_name: str) -> Optional[Skill]:
        """
        Recupera uma habilidade registrada pelo seu nome.

        Args:
            skill_name (str): O nome único da habilidade.

        Returns:
            Optional[Skill]: A instância da Skill se encontrada, caso contrário None.
        """
        return self._skills.get(skill_name)

    def get_all_skills(self) -> List[Skill]:
        """
        Retorna uma lista de todas as instâncias de Skill atualmente registradas.

        Returns:
            List[Skill]: Uma lista contendo todos os objetos Skill.
        """
        return list(self._skills.values())

    def get_skill_summaries_for_llm(self) -> List[Dict[str, str]]:
        """
        Gera uma lista de resumos de habilidades (nome e descrição) para o LLM.
        O LLM usará esses resumos para decidir qual habilidade é mais apropriada
        para o comando do usuário.

        Returns:
            List[Dict[str, str]]: Uma lista de dicionários, cada um contendo
                                   as chaves 'name' e 'description_for_llm' de uma skill.
        """
        summaries = []
        for skill_instance in self._skills.values(): # Iterar sobre os valores diretamente
            summaries.append({
                "name": skill_instance.name,
                "description_for_llm": skill_instance.description_for_llm
            })
        return summaries

    def load_skills_from_directory(self, directory: str) -> None:
        """
        Carrega habilidades nativas (definidas em Python) de módulos em um diretório especificado.

        Procura por arquivos .py no diretório, importa-os como módulos, e então
        procura por uma lista chamada `skills_to_register` dentro de cada módulo.
        Cada item nessa lista deve ser uma instância da classe `Skill`.

        Args:
            directory (str): O nome do diretório (ex: "core_skills") de onde carregar as skills.
                             Este diretório deve ser um pacote Python (conter um arquivo __init__.py,
                             mesmo que vazio) ou estar em um local onde o Python possa encontrá-lo.
        """
        print(f"INFO [SkillManager]: Tentando carregar skills nativas do diretório: '{directory}'")

        # Determina o caminho absoluto para o diretório de skills.
        # Assume-se que skill_manager.py está na raiz do projeto.
        project_root = os.path.dirname(os.path.abspath(__file__))
        skills_dir_path = os.path.join(project_root, directory)

        if not os.path.isdir(skills_dir_path):
            print(f"ERRO [SkillManager]: Diretório de skills nativas '{skills_dir_path}' não encontrado ou não é um diretório.")
            return

        # Garante que a raiz do projeto esteja no sys.path para que `skill_interface`
        # possa ser importado pelos módulos de skill.
        if project_root not in sys.path:
             sys.path.insert(0, project_root)

        # Adiciona o próprio diretório de skills ao path temporariamente para facilitar importações diretas se necessário,
        # embora a abordagem de `package.module` seja preferida.
        # if skills_dir_path not in sys.path:
        #    sys.path.insert(0, skills_dir_path)


        for filename in os.listdir(skills_dir_path):
            if filename.endswith(".py") and not filename.startswith("__init__"):
                module_name_without_py = filename[:-3]
                # Constrói o nome completo do módulo para importação (ex: "core_skills.system_interaction_skills")
                module_import_name = f"{directory}.{module_name_without_py}"

                try:
                    print(f"INFO [SkillManager]: Tentando importar módulo de skill nativa: '{module_import_name}'")
                    module = importlib.import_module(module_import_name)

                    if hasattr(module, "skills_to_register"):
                        skills_list = getattr(module, "skills_to_register")
                        if isinstance(skills_list, list):
                            loaded_count = 0
                            for skill_instance in skills_list:
                                if isinstance(skill_instance, Skill):
                                    self.register_skill(skill_instance)
                                    loaded_count += 1
                                else:
                                    print(f"AVISO [SkillManager]: Item em 'skills_to_register' do módulo '{module_name_without_py}' não é uma instância de Skill válida.")
                            if loaded_count > 0:
                                print(f"INFO [SkillManager]: {loaded_count} skill(s) nativa(s) registrada(s) do módulo '{module_name_without_py}'.")
                        else:
                            print(f"AVISO [SkillManager]: Atributo 'skills_to_register' em '{module_name_without_py}' não é uma lista.")
                    else:
                        print(f"AVISO [SkillManager]: Módulo '{module_name_without_py}' não possui a lista 'skills_to_register'. Nenhuma skill carregada dele.")
                except ImportError as e:
                    print(f"ERRO [SkillManager]: Falha ao importar módulo '{module_import_name}'. Verifique se o arquivo existe, não há erros de sintaxe nele, e todas as suas dependências estão corretas. Erro: {e}")
                except Exception as e:
                    print(f"ERRO [SkillManager]: Erro inesperado ao carregar skills do módulo '{module_name_without_py}'. Erro: {e}")

        # Remover o path adicionado se não for mais necessário (geralmente não é um problema para scripts de longa duração)
        # if skills_dir_path in sys.path:
        #    sys.path.remove(skills_dir_path)

    @staticmethod
    def _execute_learned_terminal_command(skill_definition: Dict[str, Any], provided_parameters: Dict[str, Any]) -> str:
        """
        Constrói e executa um comando de terminal aprendido, substituindo placeholders.

        Args:
            skill_definition (Dict[str, Any]): O dicionário da skill aprendida, contendo
                                               'shell_command_template' e 'template_parameters'.
            provided_parameters (Dict[str, Any]): Dicionário de parâmetros fornecidos pelo usuário (via LLM).

        Returns:
            str: Uma string formatada com a saída (stdout, stderr) e código de retorno do comando.
                 Ou uma mensagem de erro se a execução falhar.
        """
        template = skill_definition.get("shell_command_template", "")
        expected_param_names = skill_definition.get("template_parameters", [])
        skill_name = skill_definition.get("name", "habilidade_desconhecida")

        missing_params = [p_name for p_name in expected_param_names if p_name not in provided_parameters]
        if missing_params:
            return f"ERRO ao executar '{skill_name}': Parâmetros obrigatórios ausentes: {', '.join(missing_params)}."

        final_command = template
        try:
            # Substitui placeholders no formato {{placeholder_name}}
            for p_name in expected_param_names:
                placeholder = f"{{{{{p_name}}}}}"
                if placeholder not in final_command:
                     print(f"AVISO [SkillManager._execute]: Placeholder '{placeholder}' listado em template_parameters para '{skill_name}' mas não encontrado no template: '{template}'.")
                final_command = final_command.replace(placeholder, str(provided_parameters.get(p_name, ""))) # Usar .get para segurança, embora já tenhamos verificado missing_params

            if "{{" in final_command and "}}" in final_command: # Verifica se ainda há placeholders não substituídos
                 print(f"AVISO [SkillManager._execute]: Comando para '{skill_name}' após substituição ainda contém placeholders: '{final_command}'. Isso pode indicar um erro no template ou nos parâmetros fornecidos.")
                 return f"ERRO ao executar '{skill_name}': Falha ao preencher todos os placeholders no comando."

        except KeyError as e: # Deveria ser pego por missing_params, mas como fallback.
            return f"ERRO ao construir comando para '{skill_name}': Parâmetro template '{e}' não fornecido."
        except Exception as e:
            return f"ERRO ao construir comando para '{skill_name}': {e}"

        print(f"INFO [SkillManager._execute]: Executando comando para skill '{skill_name}': {final_command}")

        # ATENÇÃO: shell=True é um risco de segurança. Usar com extrema cautela.
        try:
            # Timeout de 30 segundos para o comando
            result = subprocess.run(final_command, shell=True, capture_output=True, text=True, check=False, timeout=30)

            output_parts = [f"Resultado da skill '{skill_name}' (comando: '{final_command}'):"]
            if result.stdout:
                output_parts.append(f"Saída Padrão:\n{result.stdout.strip()}")
            if result.stderr:
                output_parts.append(f"Saída de Erro:\n{result.stderr.strip()}")
            if result.returncode != 0:
                output_parts.append(f"Código de Saída: {result.returncode} (indica erro na execução do comando)")
            elif not result.stdout and not result.stderr : # Sem saída e sem erro, comando pode ter sido silencioso.
                 output_parts.append("Comando executado, sem saída em stdout/stderr.")

            return "\n".join(output_parts)
        except subprocess.TimeoutExpired:
            return f"ERRO ao executar '{skill_name}': Comando '{final_command}' excedeu o tempo limite de 30 segundos."
        except Exception as e:
            return f"ERRO ao executar comando para skill '{skill_name}': {e}"

    def load_skills_from_json(self, filepath: str = "learned_terminal_skills.json") -> None:
        """
        Carrega definições de skills de um arquivo JSON (geralmente skills de terminal aprendidas)
        e as registra no SkillManager.

        Args:
            filepath (str): O caminho para o arquivo JSON contendo as definições das skills.
        """
        print(f"INFO [SkillManager]: Tentando carregar skills aprendidas de '{filepath}'...")
        if not os.path.exists(filepath):
            print(f"INFO [SkillManager]: Arquivo de skills aprendidas '{filepath}' não encontrado. Nenhuma skill aprendida carregada.")
            return

        learned_skills_data: List[Dict[str, Any]] = []
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                learned_skills_data = json.load(f)
            if not isinstance(learned_skills_data, list): # O JSON principal deve ser uma lista de skills
                print(f"AVISO [SkillManager]: Conteúdo de '{filepath}' não é uma lista JSON válida. Ignorando.")
                return
        except json.JSONDecodeError as e:
            print(f"AVISO [SkillManager]: Erro ao decodificar JSON de '{filepath}'. O arquivo pode estar corrompido. Erro: {e}")
            return
        except Exception as e: # Outros erros de IO, etc.
            print(f"ERRO [SkillManager]: Falha inesperada ao ler ou processar '{filepath}': {e}.")
            return

        loaded_count = 0
        for i, skill_data in enumerate(learned_skills_data):
            if not isinstance(skill_data, dict):
                print(f"AVISO [SkillManager]: Item #{i} em '{filepath}' não é um dicionário de skill válido. Ignorando: {skill_data}")
                continue

            if skill_data.get("type") == "terminal_command":
                try:
                    name = skill_data["name"]
                    description = skill_data["description_for_llm"]
                    shell_template = skill_data["shell_command_template"] # Checar se existe
                    template_param_names = skill_data.get("template_parameters", []) # Default para lista vazia

                    if not all(isinstance(p, str) for p in template_param_names):
                         print(f"AVISO [SkillManager]: 'template_parameters' para skill '{name}' em '{filepath}' não é uma lista de strings. Ignorando skill.")
                         continue

                    # Converte nomes de parâmetros do template para a estrutura ParameterDefinition
                    params_expected = [
                        ParameterDefinition(name=p_name, type="string",
                                            description=f"Parâmetro '{p_name}' para o comando de terminal '{name}'.",
                                            required=True) # Por padrão, todos os params do template são obrigatórios
                        for p_name in template_param_names
                    ]

                    # Define a função 'execute' para esta skill aprendida.
                    # A lambda captura 'skill_data' para passar a definição correta para o executor.
                    execute_func = lambda params, current_skill_def=skill_data: \
                                   SkillManager._execute_learned_terminal_command(current_skill_def, params)

                    skill_instance = Skill(
                        name=name,
                        description_for_llm=description,
                        parameters_expected=params_expected,
                        execute=execute_func
                    )
                    self.register_skill(skill_instance) # Reutiliza a lógica de registro
                    loaded_count +=1
                except KeyError as e:
                    print(f"AVISO [SkillManager]: Skill aprendida em '{filepath}' (item #{i}) com dados ausentes. Chave faltando: {e}. Skill data: {skill_data}")
                except Exception as e:
                    print(f"ERRO [SkillManager]: Falha ao processar uma skill aprendida (item #{i}) de '{filepath}'. Erro: {e}. Skill data: {skill_data}")

        if loaded_count > 0:
            print(f"INFO [SkillManager]: {loaded_count} skill(s) aprendida(s) carregada(s) e registrada(s) de '{filepath}'.")


if __name__ == '__main__':
    # Os testes aqui são para o SkillManager em si.
    # A execução completa do Jarvis com carregamento real de 'core_skills' é feita em jarvis_core.py.

    print("\n--- Testando SkillManager com Módulos e JSON ---")
    mgr = SkillManager()

    # 1. Testar carregamento de diretório (simulado)
    TEST_SKILLS_DIR = "test_skills_dir_temp_sm" # Nome diferente para evitar conflitos
    if not os.path.exists(TEST_SKILLS_DIR):
        os.makedirs(TEST_SKILLS_DIR)

    # Simular skill_interface.py na raiz para os módulos de teste importarem (se não estiver já lá)
    # Em um ambiente de execução normal, o Python path já deve estar configurado.
    if not os.path.exists("skill_interface.py"):
         with open("skill_interface.py", "w") as f: # Dummy
            f.write("from dataclasses import dataclass, field\nfrom typing import Callable, Any, List, Dict, TypedDict\nclass ParameterDefinition(TypedDict):\n    name: str\n    type: str\n    description: str\n    required: bool\n@dataclass\nclass Skill:\n    name: str\n    description_for_llm: str\n    parameters_expected: List[ParameterDefinition] = field(default_factory=list)\n    execute: Callable[[Dict[str, Any]], str]\n")


    EXAMPLE_DIR_SKILL_CONTENT = """
from skill_interface import Skill, ParameterDefinition
from typing import Dict, Any, List
def dir_skill_exec(params: Dict[str, Any]) -> str: return f"Executado dir_skill com {params}"
skills_to_register: List[Skill] = [
    Skill("skill_from_dir_module", "Descrição da skill do diretório.", [], dir_skill_exec)
]"""
    with open(os.path.join(TEST_SKILLS_DIR, "dir_module_one.py"), "w") as f:
        f.write(EXAMPLE_DIR_SKILL_CONTENT)
    # __init__.py para tornar o diretório um pacote
    with open(os.path.join(TEST_SKILLS_DIR, "__init__.py"), "w") as f:
        f.write("# Pacote de skills de teste para SkillManager\n")

    mgr.load_skills_from_directory(TEST_SKILLS_DIR)
    assert mgr.get_skill("skill_from_dir_module") is not None
    print("Resultado da dir_skill_exec:", mgr.get_skill("skill_from_dir_module").execute({}))


    # 2. Testar carregamento de JSON (simulado)
    LEARNED_SKILLS_FILE_SM_TEST = "test_learned_skills_sm_temp.json"
    example_learned_json_skills = [
        {
            "name": "json_skill_ls", "type": "terminal_command",
            "description_for_llm": "Lista arquivos (aprendida via JSON).",
            "shell_command_template": "ls -l \"{{target_dir}}\"",
            "template_parameters": ["target_dir"]
        }
    ]
    with open(LEARNED_SKILLS_FILE_SM_TEST, "w", encoding="utf-8") as f:
        json.dump(example_learned_json_skills, f, indent=2)

    mgr.load_skills_from_json(LEARNED_SKILLS_FILE_SM_TEST)
    json_skill = mgr.get_skill("json_skill_ls")
    assert json_skill is not None
    print("Resultado da json_skill_ls:", json_skill.execute({"target_dir": "."}))

    print(f"\nTotal de skills registradas: {len(mgr.get_all_skills())}")
    print("Resumos para LLM:")
    for summary in mgr.get_skill_summaries_for_llm():
        print(summary)

    # Limpeza
    import shutil
    if os.path.exists(TEST_SKILLS_DIR):
        shutil.rmtree(TEST_SKILLS_DIR)
    if os.path.exists(LEARNED_SKILLS_FILE_SM_TEST):
        os.remove(LEARNED_SKILLS_FILE_SM_TEST)
    # Não remover o skill_interface.py dummy se o original não existir,
    # mas em geral, o original deve estar presente.

    print("\n--- Testes de SkillManager (com carregamento) finalizados ---")

```
