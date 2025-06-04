# skill_interface.py
"""
Define a interface e a estrutura de dados para todas as habilidades (Skills)
que podem ser gerenciadas e executadas por Jarvis.
Isto inclui a definição da `Skill` em si e dos parâmetros que ela espera.
"""
from dataclasses import dataclass, field
from typing import Callable, Any, List, Dict, TypedDict # TypedDict já estava sendo usado, apenas explicitando na importação geral

class ParameterDefinition(TypedDict):
    """
    Define a estrutura para um parâmetro esperado por uma Skill.
    """
    name: str  # Nome do parâmetro (ex: "app_name", "query").
    type: str  # Tipo de dado esperado para o parâmetro (ex: "string", "int", "boolean", "list_of_string").
               # Usado para informação e potencialmente para validação futura.
    description: str  # Descrição do parâmetro, útil para o LLM entender o que fornecer.
    required: bool    # Indica se o parâmetro é obrigatório para a execução da skill.
    # enum_values: List[str] # Opcional: Se o tipo for "enum", esta lista conteria os valores permitidos.

@dataclass
class Skill:
    """
    Representa uma habilidade que Jarvis pode aprender e executar.
    Cada habilidade tem um nome, uma descrição para o LLM, uma lista de parâmetros
    que espera, e uma função Python que executa sua lógica.
    """
    name: str  # Identificador único da habilidade (ex: "open_application", "search_web").
               # Deve ser uma string concisa e sem espaços, preferencialmente.

    description_for_llm: str  # Descrição concisa para o LLM entender quando e como usar esta habilidade.
                               # Ex: "Abre um aplicativo especificado no computador."
                               # ou "Ensina a Jarvis um novo comando de terminal."

    parameters_expected: List[ParameterDefinition] = field(default_factory=list) # Lista de definições de parâmetros que a habilidade espera.
                                                                              # O LLM tentará extrair valores para estes parâmetros do comando do usuário.

    execute: Callable[[Dict[str, Any]], str]  # A função Python a ser chamada para executar a lógica da habilidade.
                                             # Recebe um dicionário de parâmetros (nome_parametro: valor) e
                                             # deve retornar uma string de resultado/feedback para o usuário.

    def __post_init__(self):
        """
        Realiza validações básicas após a inicialização da instância.
        """
        if not callable(self.execute):
            raise ValueError(f"Erro na Skill '{self.name}': O atributo 'execute' deve ser uma função (callable). Recebido: {type(self.execute)}")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Erro na Skill: O atributo 'name' deve ser uma string não vazia.")
        if not isinstance(self.description_for_llm, str) or not self.description_for_llm.strip():
            raise ValueError(f"Erro na Skill '{self.name}': O atributo 'description_for_llm' deve ser uma string não vazia.")
        if not isinstance(self.parameters_expected, list):
            raise ValueError(f"Erro na Skill '{self.name}': O atributo 'parameters_expected' deve ser uma lista.")
        for param_def in self.parameters_expected:
            if not isinstance(param_def, dict) or \
               not all(key in param_def for key in ['name', 'type', 'description', 'required']) or \
               not isinstance(param_def['name'], str) or \
               not isinstance(param_def['type'], str) or \
               not isinstance(param_def['description'], str) or \
               not isinstance(param_def['required'], bool):
                raise ValueError(f"Erro na Skill '{self.name}': Parâmetro esperado malformado: {param_def}. Deve ser um dict com 'name', 'type', 'description', 'required' dos tipos corretos.")


# Exemplo de uso (apenas para ilustração, não será executado quando importado):
if __name__ == '__main__':
    # Este bloco é útil para testar rapidamente a definição da Skill e ParameterDefinition.

    def example_skill_execution_func(params: Dict[str, Any]) -> str:
        app_name = params.get("app_name", "aplicativo padrão")
        message = params.get("message", "")
        return f"Habilidade de exemplo executada para '{app_name}'. Mensagem: '{message}'"

    # Definição de parâmetros para a skill de exemplo
    example_params: List[ParameterDefinition] = [
        {
            "name": "app_name",
            "type": "string",
            "description": "O nome do aplicativo a ser manipulado.",
            "required": True
        },
        {
            "name": "message",
            "type": "string",
            "description": "Uma mensagem opcional a ser usada pela habilidade.",
            "required": False
        }
    ]

    # Criando uma instância de Skill de exemplo
    example_skill_instance = Skill(
        name="manipular_aplicativo_exemplo",
        description_for_llm="Manipula um aplicativo com uma mensagem opcional.",
        parameters_expected=example_params,
        execute=example_skill_execution_func
    )

    print(f"--- Exemplo de Habilidade ---")
    print(f"Nome: {example_skill_instance.name}")
    print(f"Descrição para LLM: {example_skill_instance.description_for_llm}")
    print(f"Parâmetros Esperados:")
    for p in example_skill_instance.parameters_expected:
        print(f"  - {p['name']} (tipo: {p['type']}, obrigatório: {p['required']}): {p['description']}")

    print(f"\nExecutando com app_name='TesteApp', message='Olá':")
    print(f"Resultado: {example_skill_instance.execute({'app_name': 'TesteApp', 'message': 'Olá'})}")

    print(f"\nExecutando com app_name='OutroApp' (sem message):")
    print(f"Resultado: {example_skill_instance.execute({'app_name': 'OutroApp'})}")

    print("\n--- Testes de Validação ---")
    try:
        Skill(name="", description_for_llm="desc", execute=lambda x: "")
    except ValueError as e:
        print(f"OK: Erro ao criar skill com nome vazio: {e}")

    try:
        # MyPy não pegaria isso facilmente sem Callable[[Dict[str, Any]], str]
        Skill(name="teste_callable", description_for_llm="desc", execute="nao_e_callable") # type: ignore
    except ValueError as e:
        print(f"OK: Erro ao criar skill com 'execute' não callable: {e}")

    try:
        Skill(name="teste_param_malformado", description_for_llm="desc", execute=lambda x: "", parameters_expected=[{"name":"p1"}]) # type: ignore
    except ValueError as e:
        print(f"OK: Erro ao criar skill com parâmetro malformado: {e}")
```
