# llm_interpreter.py
"""
Este módulo é responsável por interagir com o Modelo de Linguagem de Grande Escala (LLM)
do Google (Gemini Pro) para interpretar os comandos do usuário, levando em consideração
o histórico da conversa e a possibilidade de retornar múltiplas ações (plano de tarefas).
"""
import google.generativeai as genai
import os
import json
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional, Union # Adicionado Union

# Carregar variáveis de ambiente do arquivo .env (ex: GOOGLE_API_KEY)
load_dotenv()

GOOGLE_API_KEY_LOADED = False
try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        GOOGLE_API_KEY_LOADED = True
    else:
        if __name__ == '__main__':
            print("AVISO [LLM Interpreter]: GOOGLE_API_KEY não encontrada no .env.")
except Exception as e:
    if __name__ == '__main__':
        print(f"ERRO [LLM Interpreter]: Falha ao configurar API Google: {e}")

def get_command_interpretation(
    text_input: str,
    skill_summaries: List[Dict[str, str]],
    history: Optional[List[Dict[str, str]]] = None
) -> Optional[List[Dict[str, Any]]]: # Alterado para sempre retornar uma LISTA de ações ou None
    """
    Envia o comando do usuário, um resumo das skills e o histórico da conversa para o LLM.
    O LLM deve escolher uma skill (ou uma sequência de skills) e extrair parâmetros.

    Args:
        text_input (str): O comando atual do usuário.
        skill_summaries (List[Dict[str, str]]): Resumos das skills disponíveis.
        history (Optional[List[Dict[str, str]]]): Histórico da conversa.

    Returns:
        Optional[List[Dict[str, Any]]]]: Uma LISTA de dicionários, onde cada dicionário
                                         contém "chosen_skill" e "provided_parameters".
                                         Retorna None se ocorrer um erro crítico.
                                         Retorna uma lista com um item se for uma única ação.
    """
    if not GOOGLE_API_KEY_LOADED:
        print("ERRO [LLM Interpreter]: API Key do Google não configurada.")
        return None

    try:
        model = genai.GenerativeModel('gemini-pro')
    except Exception as e:
        print(f"ERRO [LLM Interpreter]: Falha ao inicializar GenerativeModel: {e}")
        return None

    skills_json_string = json.dumps(skill_summaries, indent=2, ensure_ascii=False)

    # TODO: Refinar este prompt. A capacidade do LLM de seguir instruções complexas
    # sobre formatos de saída (objeto único OU lista de objetos) pode variar.
    # Testar exaustivamente e simplificar se necessário.
    current_prompt_instruction = f"""
    Analise o "Comando do usuário" MAIS RECENTE no contexto do "Histórico da Conversa" (se fornecido).
    Sua tarefa é determinar qual(is) "Habilidade(s) disponível(is)" são as mais adequadas.
    Extraia quaisquer parâmetros mencionados no comando que sejam relevantes para a(s) habilidade(s) escolhida(s).

    Habilidades disponíveis (escolha uma ou mais destas, ou "desconhecida"):
    ```json
    {skills_json_string}
    ```

    Instruções de Resposta:
    1.  Foque no COMANDO DO USUÁRIO MAIS RECENTE. Use o HISTÓRICO para contexto.
    2.  Se o comando puder ser satisfeito por uma ÚNICA HABILIDADE, responda com um único objeto JSON.
    3.  Se o comando exigir MÚLTIPLAS HABILIDADES em sequência, responda com uma LISTA de objetos JSON,
        onde cada objeto representa uma etapa da sequência.
    4.  Se nenhuma habilidade for adequada, "chosen_skill" deve ser "desconhecida" ou `null` (em um único objeto JSON ou dentro de um item da lista).
    5.  "provided_parameters" deve ser um dicionário JSON vazio (`{{}}`) se nenhum parâmetro for aplicável.
    6.  Responda APENAS com o objeto JSON ou a lista de objetos JSON. Não inclua texto adicional.

    Formato da Resposta JSON (para uma única ação):
    {{
      "chosen_skill": "<nome_da_skill_ou_null_ou_desconhecida>",
      "provided_parameters": {{ "<param1>": "<valor1>" }}
    }}

    Formato da Resposta JSON (para múltiplas ações):
    [
      {{ "chosen_skill": "<skill_etapa_1>", "provided_parameters": {{ "<param_a>": "<valor_a>" }} }},
      {{ "chosen_skill": "<skill_etapa_2>", "provided_parameters": {{ "<param_b>": "<valor_b>" }} }}
    ]

    Exemplo de múltiplas ações para "Jarvis, crie uma pasta chamada 'projetos' e depois abra ela.":
    [
        {{"chosen_skill": "criar_pasta", "provided_parameters": {{"nome_da_pasta": "projetos"}}}},
        {{"chosen_skill": "abrir_pasta", "provided_parameters": {{"caminho_da_pasta": "projetos"}}}}
    ]
    """

    full_conversation_context: List[Dict[str, Any]] = []
    if history:
        for entry in history:
            full_conversation_context.append({
                "role": entry["role"],
                "parts": [{"text": entry["content"]}]
            })

    full_conversation_context.append({
        "role": "user",
        "parts": [{"text": current_prompt_instruction.replace("{text_input}", text_input)}]
    })

    raw_response_text_for_debugging = ""
    try:
        # print(f"DEBUG [LLM Interpreter]: Enviando contexto para LLM: {json.dumps(full_conversation_context, indent=2, ensure_ascii=False)}")
        response = model.generate_content(full_conversation_context)

        if not hasattr(response, 'text') or not response.text:
            print("ERRO [LLM Interpreter]: Resposta do LLM não contém 'text' ou está vazia.")
            if hasattr(response, 'prompt_feedback'): print(f"  Feedback (API): {response.prompt_feedback}")
            if hasattr(response, 'candidates'): print(f"  Candidates (API): {response.candidates}")
            else: print(f"  Resposta completa (API): {response}")
            return None

        raw_response_text_for_debugging = response.text
        cleaned_text = raw_response_text_for_debugging.strip()

        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[len("```json"):].strip()
        elif cleaned_text.startswith("```"):
            cleaned_text = cleaned_text[len("```"):].strip()
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-len("```")].strip()

        # Tentar decodificar como lista primeiro, depois como objeto único.
        parsed_response: Any
        try:
            parsed_response = json.loads(cleaned_text)
        except json.JSONDecodeError as e_list:
            # Se falhou como lista, não há fallback para objeto único se o formato esperado é estritamente JSON.
            # O LLM deve sempre retornar JSON válido, seja um objeto ou uma lista.
            print(f"ERRO [LLM Interpreter]: Falha ao decodificar JSON. Erro: {e_list}")
            print(f"Resposta bruta que causou erro: '{raw_response_text_for_debugging.strip()}'")
            return None

        actions: List[Dict[str, Any]] = []
        if isinstance(parsed_response, list):
            actions.extend(parsed_response)
        elif isinstance(parsed_response, dict):
            actions.append(parsed_response)
        else:
            print(f"ERRO [LLM Interpreter]: Resposta JSON não é nem um objeto nem uma lista. Resposta: {cleaned_text}")
            return None

        # Validar cada ação na lista
        validated_actions: List[Dict[str, Any]] = []
        for action_dict in actions:
            if not isinstance(action_dict, dict): # Checar se cada item da lista é um dict
                print(f"AVISO [LLM Interpreter]: Item na lista de ações não é um dicionário: {action_dict}. Ignorando.")
                continue
            if "chosen_skill" not in action_dict:
                print(f"AVISO [LLM Interpreter]: Ação na lista não contém 'chosen_skill'. Ação: {action_dict}. Ignorando.")
                continue
            if "provided_parameters" not in action_dict or not isinstance(action_dict["provided_parameters"], dict):
                print(f"AVISO [LLM Interpreter]: 'provided_parameters' ausente/inválido na ação {action_dict.get('chosen_skill')}. Usando {{}}.")
                action_dict["provided_parameters"] = {}
            validated_actions.append(action_dict)

        if not validated_actions and actions: # Se havia ações mas nenhuma foi validada
             print(f"ERRO [LLM Interpreter]: Nenhuma ação válida encontrada após processar a resposta do LLM que era: {cleaned_text}")
             return None # Ou retornar uma lista vazia se for preferível para o core lidar? Por ora, None.

        return validated_actions if validated_actions else None


    except Exception as e: # Captura outras exceções (ex: da API do Google, AttributeError)
        error_type = str(type(e))
        print(f"ERRO [LLM Interpreter]: Exceção. Tipo: {error_type}. Erro: {e}")
        if 'response' in locals() and hasattr(response, 'prompt_feedback'):
             print(f"  Feedback do prompt: {response.prompt_feedback}")
        if "APIError" in error_type or "GoogleAPIError" in error_type or hasattr(e, 'response'):
            print(f"  Detalhes API: {getattr(e, 'response', 'N/A')}")
        return None

if __name__ == '__main__':
    if not GOOGLE_API_KEY_LOADED:
        print("-" * 70 + "\nATENÇÃO: GOOGLE_API_KEY não configurada. Testes de API não funcionarão.\n" + "-" * 70)
    else:
        print("Chave GOOGLE_API_KEY encontrada. Testando llm_interpreter com histórico e potencial multi-ação...")
        print("-" * 70)

        example_skill_summaries = [
            {"name": "create_directory", "description_for_llm": "Cria um novo diretório (pasta). Parâmetro: 'directory_name'."},
            {"name": "open_application", "description_for_llm": "Abre um aplicativo. Parâmetro: 'app_name'."},
            {"name": "search_web", "description_for_llm": "Pesquisa na web. Parâmetro: 'query'."},
        ]

        example_history: List[Dict[str, str]] = [
            {"role": "user", "content": "Jarvis, você pode me ajudar com algumas coisas?"},
            {"role": "model", "content": "Claro, como posso ajudar?"}
        ]

        test_commands = [
            ("Jarvis, crie uma pasta chamada 'meus_documentos_importantes'", example_history),
            ("Jarvis, por favor, abra a calculadora e depois pesquise por 'piadas engraçadas'", None),
            ("Jarvis, qual o clima hoje?", example_history) # Deveria retornar "desconhecida"
        ]

        for command, hist in test_commands:
            print(f"\n>>> Comando de Teste: \"{command}\"")
            if hist: print(f"    Histórico: {hist}")

            interpretations = get_command_interpretation(command, example_skill_summaries, history=hist)

            if interpretations:
                print(f"<<< Interpretação(ões) LLM ({len(interpretations)} ação(ões)):")
                for i, interp in enumerate(interpretations):
                    print(f"  Ação {i+1}: {json.dumps(interp, indent=2, ensure_ascii=False)}")
            else:
                print("<<< Não foi possível obter a interpretação para este comando.")
            print("-" * 70)

```
