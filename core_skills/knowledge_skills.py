# core_skills/knowledge_skills.py
"""
Este módulo define habilidades (skills) para Jarvis relacionadas à gestão
de uma base de conhecimento simples, baseada em fatos chave-valor.

Habilidades implementadas:
- learn_fact: Permite ao usuário ensinar um novo fato (par chave-valor) a Jarvis.
- recall_fact: Permite ao usuário perguntar a Jarvis sobre um fato previamente aprendido.

Os fatos são armazenados em um arquivo JSON para persistência.
"""
import json
import os
from typing import Dict, Any, List

# Tenta importar a interface Skill. Ajustes de path são geralmente tratados pelo SkillManager.
try:
    from skill_interface import Skill, ParameterDefinition
except ImportError:
    # Fallback para o caso de execução direta do script ou problemas de path não resolvidos.
    print("AVISO [knowledge_skills]: Não foi possível importar 'Skill' de 'skill_interface'. "
          "Isso é esperado se executado diretamente fora do contexto do projeto principal.")
    # Definir dummies para permitir que o script seja pelo menos parsable se executado isoladamente.
    class ParameterDefinition(dict): pass
    from dataclasses import dataclass
    @dataclass
    class Skill: name: str; description_for_llm: str; parameters_expected: List; execute: Any

# --- Constantes e Funções Utilitárias para a Base de Conhecimento ---
KNOWLEDGE_BASE_FILE = "user_knowledge_base.json"

def _load_knowledge_base() -> Dict[str, Any]:
    """
    Carrega a base de conhecimento do arquivo JSON.

    Returns:
        Dict[str, Any]: O dicionário da base de conhecimento. Retorna um dicionário
                        vazio se o arquivo não existir ou em caso de erro de parsing.
    """
    if os.path.exists(KNOWLEDGE_BASE_FILE):
        try:
            with open(KNOWLEDGE_BASE_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                if not content.strip(): # Arquivo vazio
                    return {}
                return json.loads(content)
        except FileNotFoundError: # Embora os.path.exists deva pegar isso, como segurança.
            print(f"INFO [KnowledgeBase]: Arquivo '{KNOWLEDGE_BASE_FILE}' não encontrado. Iniciando com base vazia.")
            return {}
        except json.JSONDecodeError:
            print(f"AVISO [KnowledgeBase]: Erro ao decodificar JSON de '{KNOWLEDGE_BASE_FILE}'. O arquivo pode estar corrompido. Iniciando com base vazia.")
            return {}
        except Exception as e:
            print(f"ERRO [KnowledgeBase]: Falha inesperada ao ler '{KNOWLEDGE_BASE_FILE}': {e}. Iniciando com base vazia.")
            return {}
    return {}

def _save_knowledge_base(data: Dict[str, Any]) -> bool:
    """
    Salva o dicionário da base de conhecimento no arquivo JSON.

    Args:
        data (Dict[str, Any]): O dicionário da base de conhecimento a ser salvo.

    Returns:
        bool: True se salvo com sucesso, False caso contrário.
    """
    try:
        with open(KNOWLEDGE_BASE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except IOError as e:
        print(f"ERRO [KnowledgeBase]: Falha ao salvar a base de conhecimento em '{KNOWLEDGE_BASE_FILE}': {e}")
        return False
    except Exception as e:
        print(f"ERRO [KnowledgeBase]: Ocorreu um erro inesperado ao salvar a base de conhecimento: {e}")
        return False

# --- Implementação das Funções de Execução das Habilidades ---

def execute_learn_fact(parameters: Dict[str, Any]) -> str:
    """
    Função de execução para a skill 'learn_fact'.
    Adiciona um par chave-valor à base de conhecimento.
    """
    fact_key = parameters.get("fact_key")
    fact_value = parameters.get("fact_value")

    if not fact_key or not isinstance(fact_key, str):
        return "AVISO [LearnFact]: O parâmetro 'fact_key' (chave do fato) é obrigatório e deve ser uma string."
    if fact_value is None or not isinstance(fact_value, str): # Permitir string vazia, mas não None ou outro tipo
        return f"AVISO [LearnFact]: O parâmetro 'fact_value' (valor do fato) para '{fact_key}' é obrigatório e deve ser uma string."

    knowledge_base = _load_knowledge_base()

    # Verificar se a chave já existe e o valor é o mesmo para evitar reescrever desnecessariamente
    # ou para potencialmente adicionar lógica de confirmação de sobrescrita no futuro.
    if fact_key in knowledge_base and knowledge_base[fact_key] == fact_value:
        return f"Eu já sabia que '{fact_key}' é '{fact_value}'. Não precisei aprender de novo."

    old_value_message = ""
    if fact_key in knowledge_base:
        old_value_message = f" (o valor anterior era '{knowledge_base[fact_key]}')"


    knowledge_base[fact_key] = fact_value
    if _save_knowledge_base(knowledge_base):
        return f"Entendido. Eu vou lembrar que '{fact_key}' é '{fact_value}'{old_value_message}."
    else:
        return f"Desculpe, tive um problema ao tentar aprender que '{fact_key}' é '{fact_value}'. O fato não foi salvo."

def execute_recall_fact(parameters: Dict[str, Any]) -> str:
    """
    Função de execução para a skill 'recall_fact'.
    Recupera um valor da base de conhecimento usando uma chave.
    """
    fact_key = parameters.get("fact_key")

    if not fact_key or not isinstance(fact_key, str):
        return "AVISO [RecallFact]: O parâmetro 'fact_key' (chave do fato) é obrigatório e deve ser uma string para que eu possa lembrar."

    knowledge_base = _load_knowledge_base()

    if fact_key in knowledge_base:
        return f"Lembrei que '{fact_key}' é '{knowledge_base[fact_key]}'."
    else:
        # Tentar uma busca case-insensitive como fallback simples
        for key_in_kb, value_in_kb in knowledge_base.items():
            if key_in_kb.lower() == fact_key.lower():
                return f"Lembrei que '{key_in_kb}' (correspondência insensível a maiúsculas/minúsculas) é '{value_in_kb}'."
        return f"Desculpe, eu não tenho um fato registrado para '{fact_key}'."

# --- Definição das Instâncias de Skill ---

learn_fact_skill = Skill(
    name="learn_fact",
    description_for_llm=(
        "Permite ensinar um fato específico a Jarvis. "
        "O fato é armazenado como um par chave-valor (ex: chave='cor favorita', valor='azul'). "
        "Jarvis poderá lembrar desse fato no futuro usando a chave."
    ),
    parameters_expected=[
        ParameterDefinition(name="fact_key", type="string", description="A chave ou nome do fato a ser aprendido (ex: 'meu carro', 'aniversário da mamãe', 'senha do wifi de convidados').", required=True),
        ParameterDefinition(name="fact_value", type="string", description="O valor ou a informação associada à chave do fato (ex: 'Toyota Corolla', '15 de março', 'convidado123').", required=True)
    ],
    execute=execute_learn_fact
)

recall_fact_skill = Skill(
    name="recall_fact",
    description_for_llm=(
        "Recupera e informa um fato específico que Jarvis aprendeu anteriormente. "
        "Você precisa fornecer a chave exata do fato que deseja que Jarvis lembre."
    ),
    parameters_expected=[
        ParameterDefinition(name="fact_key", type="string", description="A chave ou nome do fato que você quer que Jarvis recorde (ex: 'meu carro', 'cor favorita').", required=True)
    ],
    execute=execute_recall_fact
)

# --- Lista de Skills para Registro ---
skills_to_register: List[Skill] = [
    learn_fact_skill,
    recall_fact_skill,
]

# Bloco de teste para execução direta do script
if __name__ == '__main__':
    print("--- Testando as Habilidades de Conhecimento (knowledge_skills.py) ---")

    # Limpar arquivo de conhecimento para um teste limpo
    if os.path.exists(KNOWLEDGE_BASE_FILE):
        os.remove(KNOWLEDGE_BASE_FILE)
        print(f"INFO: Arquivo '{KNOWLEDGE_BASE_FILE}' removido para iniciar teste limpo.")

    # Teste 1: Aprender um fato
    params_learn1 = {"fact_key": "cor_favorita", "fact_value": "azul"}
    print(f"\nComando: Aprender Fato 1, Parâmetros: {params_learn1}")
    print(f"Resultado: {execute_learn_fact(params_learn1)}")

    # Teste 2: Aprender outro fato
    params_learn2 = {"fact_key": "cidade_natal", "fact_value": "Recife"}
    print(f"\nComando: Aprender Fato 2, Parâmetros: {params_learn2}")
    print(f"Resultado: {execute_learn_fact(params_learn2)}")

    # Teste 3: Tentar aprender o mesmo fato (deve indicar que já sabe)
    print(f"\nComando: Aprender Fato 1 novamente, Parâmetros: {params_learn1}")
    print(f"Resultado: {execute_learn_fact(params_learn1)}")

    # Teste 4: Atualizar um fato existente
    params_learn_update = {"fact_key": "cor_favorita", "fact_value": "verde"}
    print(f"\nComando: Atualizar Fato 1, Parâmetros: {params_learn_update}")
    print(f"Resultado: {execute_learn_fact(params_learn_update)}")


    # Teste 5: Recuperar o primeiro fato (atualizado)
    params_recall1 = {"fact_key": "cor_favorita"}
    print(f"\nComando: Recuperar Fato 1, Parâmetros: {params_recall1}")
    print(f"Resultado: {execute_recall_fact(params_recall1)}")

    # Teste 6: Recuperar o segundo fato
    params_recall2 = {"fact_key": "cidade_natal"}
    print(f"\nComando: Recuperar Fato 2, Parâmetros: {params_recall2}")
    print(f"Resultado: {execute_recall_fact(params_recall2)}")

    # Teste 7: Tentar recuperar um fato inexistente
    params_recall_nonexistent = {"fact_key": "comida_favorita"}
    print(f"\nComando: Recuperar Fato Inexistente, Parâmetros: {params_recall_nonexistent}")
    print(f"Resultado: {execute_recall_fact(params_recall_nonexistent)}")

    # Teste 8: Aprender fato com chave contendo espaços (deve funcionar)
    params_learn3 = {"fact_key": "nome do meu cachorro", "fact_value": "Rex"}
    print(f"\nComando: Aprender Fato 3 (chave com espaços), Parâmetros: {params_learn3}")
    print(f"Resultado: {execute_learn_fact(params_learn3)}")

    # Teste 9: Recuperar fato com chave contendo espaços
    params_recall3 = {"fact_key": "nome do meu cachorro"}
    print(f"\nComando: Recuperar Fato 3, Parâmetros: {params_recall3}")
    print(f"Resultado: {execute_recall_fact(params_recall3)}")

    # Teste 10: Recuperar fato com variação de caixa (deve encontrar se a lógica de fallback estiver ativa)
    params_recall_case = {"fact_key": "Cidade_Natal"}
    print(f"\nComando: Recuperar Fato 2 com variação de caixa, Parâmetros: {params_recall_case}")
    print(f"Resultado: {execute_recall_fact(params_recall_case)}")


    # Verificar conteúdo final do arquivo JSON
    if os.path.exists(KNOWLEDGE_BASE_FILE):
        print(f"\nConteúdo final de '{KNOWLEDGE_BASE_FILE}':")
        with open(KNOWLEDGE_BASE_FILE, "r", encoding='utf-8') as f:
            print(f.read())
```
