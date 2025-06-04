# Assistente de Voz para Controle de Computador - Jarvis

Este projeto visa criar um assistente de voz chamado Jarvis, capaz de entender comandos falados e executá-los no sistema operacional do usuário. Ele utiliza reconhecimento de voz, uma arquitetura baseada em habilidades (skills) e um Modelo de Linguagem de Grande Escala (LLM) do Google (Gemini Pro) para interpretar comandos e executar as ações correspondentes.

## Visão Geral da Arquitetura

Jarvis é construído sobre uma arquitetura modular baseada em habilidades:

*   **`jarvis_core.py`**: O coração do sistema. Orquestra o fluxo principal: ouve a palavra de ativação, captura o comando, interage com o `llm_interpreter` para decidir qual habilidade usar, e então com o `skill_manager` para executar a habilidade escolhida.
*   **`skill_interface.py`**: Define a estrutura de dados (`dataclass Skill`) que todas as habilidades devem seguir. Isso garante consistência e facilita o gerenciamento.
*   **`skill_manager.py`**: Responsável por carregar, registrar e fornecer acesso às habilidades disponíveis. Ele pode carregar habilidades "nativas" (definidas em Python) de diretórios e habilidades "aprendidas" (comandos de terminal) de um arquivo JSON.
*   **`llm_interpreter.py`**: Contém a lógica para interagir com a API do Google Gemini. Ele recebe o comando do usuário e uma lista de habilidades disponíveis (fornecida pelo `SkillManager`) e retorna qual habilidade o LLM acredita ser a mais apropriada, junto com quaisquer parâmetros extraídos do comando.
*   **`voice_recognizer.py`**: Encapsula a funcionalidade de reconhecimento de voz (speech-to-text), convertendo a fala do usuário em texto.
*   **`core_skills/`**: Um diretório designado para armazenar módulos Python que definem as "habilidades nativas" de Jarvis. Cada arquivo `.py` aqui pode definir uma ou mais habilidades.
    *   **`core_skills/system_interaction_skills.py`**: Exemplo de módulo de habilidade nativa, contendo skills como `open_application` e `search_web`.
    *   **`core_skills/learning_skills.py`**: Contém a habilidade especial `learn_new_terminal_skill`, que permite ensinar novos comandos de terminal para Jarvis.
*   **`learned_terminal_skills.json`**: Um arquivo JSON onde as definições de habilidades de terminal ensinadas a Jarvis são armazenadas e persistidas.

## Funcionalidades Atuais

*   Reconhecimento de voz com palavra de ativação ("Jarvis").
*   Arquitetura baseada em habilidades para fácil extensibilidade.
*   Interpretação de comandos de voz para escolher a habilidade apropriada e extrair parâmetros usando LLM.
*   Habilidades nativas para abrir aplicativos e pesquisar na web.
*   Mecanismo para ensinar, aprender e executar novas habilidades baseadas em comandos de terminal.

## Configuração Inicial do Ambiente

Siga estes passos para configurar seu ambiente antes de executar o Jarvis.

### 1. Pré-requisitos

*   Python 3.10 ou superior.
*   Acesso a um microfone.
*   Acesso à internet (para reconhecimento de voz e API LLM).

### 2. Obtenha o Código

Clone o repositório (se ainda não o fez):
```bash
# git clone <URL_DO_REPOSITORIO_AQUI> # Substitua se necessário
# cd <NOME_DO_DIRETORIO_DO_PROJETO>
```

### 3. Instale as Dependências Python

Instale as bibliotecas Python listadas em `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 4. Instale as Dependências de Sistema para Áudio (PyAudio)

`PyAudio` é usado para captura de áudio e requer bibliotecas de sistema:

*   **Linux (Debian/Ubuntu):**
    ```bash
    sudo apt-get update
    sudo apt-get install -y python3.10-dev portaudio19-dev
    # Ajuste python3.10-dev para sua versão de Python, se diferente (ex: python3.11-dev)
    ```
*   **macOS:**
    Use Homebrew: `brew install portaudio`
*   **Windows:**
    A instalação pode ser mais complexa. Consulte a [documentação do PyAudio](https://people.csail.mit.edu/hubert/pyaudio/) ou pesquise guias específicos. Geralmente envolve a instalação de PortAudio e, possivelmente, das Ferramentas de Build do Microsoft Visual C++.

### 5. Configure a Chave da API do Google (LLM)

Jarvis usa a API do Google Gemini.

1.  **Obtenha sua chave de API:** Visite o [Google AI Studio](https://aistudio.google.com/app/apikey).
2.  **Crie o arquivo `.env`:** Copie `.env.example` para `.env`:
    ```bash
    cp .env.example .env
    ```
    Este arquivo (`.env`) **NÃO** deve ser enviado para o Git (já está no `.gitignore`).
3.  **Adicione sua chave ao `.env`:** Edite o arquivo `.env` e substitua `"SUA_CHAVE_API_AQUI"` pela sua chave real.

## Como Executar o Assistente Jarvis (`jarvis_core.py`)

1.  Navegue até o diretório raiz do projeto.
2.  Execute o script principal:
    ```bash
    python jarvis_core.py
    ```
3.  Você verá logs de inicialização, incluindo o carregamento de habilidades. Se tudo estiver correto, a mensagem "Jarvis está pronto. Diga 'Jarvis' seguido do seu comando." aparecerá.
4.  **Uso:**
    *   Diga "Jarvis".
    *   Aguarde a confirmação de que ele ouviu a palavra de ativação.
    *   Diga seu comando (ex: "abra a calculadora", "pesquise sobre a teoria da relatividade").
    *   Jarvis tentará interpretar e executar o comando.

**Observação:** Na primeira vez que usar o microfone, seu SO pode pedir permissão.

## Trabalhando com Habilidades (Skills)

Jarvis é extensível através de um sistema de habilidades.

### O que é uma Habilidade?

Uma habilidade é uma ação ou capacidade específica que Jarvis pode executar. Cada habilidade é definida pela estrutura `Skill` (em `skill_interface.py`) que inclui:
*   `name`: Um nome único para a habilidade.
*   `description_for_llm`: Uma descrição que ajuda o LLM a entender o que a habilidade faz e quando usá-la.
*   `parameters_expected`: Uma lista que define quais parâmetros a habilidade aceita (nome, tipo, descrição, se é obrigatório).
*   `execute`: A função Python que realmente executa a lógica da habilidade.

### Habilidades Nativas (Core Skills)

São habilidades definidas diretamente em código Python e localizadas no diretório `core_skills/`.

*   **Exemplos Atuais:**
    *   `open_application` (em `core_skills/system_interaction_skills.py`): Abre aplicativos.
    *   `search_web` (em `core_skills/system_interaction_skills.py`): Pesquisa na web.
    *   `learn_new_terminal_skill` (em `core_skills/learning_skills.py`): Ensina a Jarvis novos comandos de terminal.

*   **Criando Novas Habilidades Nativas:**
    1.  Crie um novo arquivo Python no diretório `core_skills/` (ex: `minha_nova_skill_module.py`).
    2.  No seu módulo, importe `Skill` e `ParameterDefinition` de `skill_interface.py`.
    3.  Defina uma função Python que conterá a lógica da sua habilidade. Esta função deve aceitar um dicionário de parâmetros e retornar uma string de resultado/feedback.
        ```python
        # Exemplo em minha_nova_skill_module.py
        from skill_interface import Skill, ParameterDefinition
        from typing import Dict, Any

        def executar_minha_acao_personalizada(parameters: Dict[str, Any]) -> str:
            nome_alvo = parameters.get("nome_alvo", "mundo")
            # ... lógica da sua skill aqui ...
            return f"Ação personalizada executada para {nome_alvo}!"
        ```
    4.  Crie uma instância da classe `Skill`, preenchendo todos os campos:
        ```python
        minha_skill_personalizada = Skill(
            name="acao_personalizada_exemplo",
            description_for_llm="Executa uma ação personalizada que cumprimenta um alvo.",
            parameters_expected=[
                ParameterDefinition(name="nome_alvo", type="string", description="O nome a ser cumprimentado.", required=False)
            ],
            execute=executar_minha_acao_personalizada
        )
        ```
    5.  Adicione a instância da sua skill a uma lista chamada `skills_to_register` no final do seu módulo:
        ```python
        skills_to_register = [minha_skill_personalizada]
        ```
    6.  O `SkillManager` automaticamente descobrirá e registrará as habilidades desta lista quando Jarvis iniciar.

### Habilidades Aprendidas (Comandos de Terminal)

Jarvis pode aprender a executar novos comandos de terminal através da habilidade `learn_new_terminal_skill`.

*   **Ensinando Novas Habilidades de Terminal:**
    Você pode ensinar Jarvis falando um comando que use a skill `learn_new_terminal_skill`. O LLM precisa entender que você quer usar *essa* skill e extrair os parâmetros corretamente.
    *   **Exemplo de Comando de Voz (detalhado):**
        `"Jarvis, use a habilidade learn_new_terminal_skill com new_skill_name igual a 'listar_arquivos_documentos', new_skill_description igual a 'Lista todos os arquivos e pastas no meu diretório Documentos', shell_command_template igual a 'ls -la ~/Documentos', e template_parameters igual a [] (uma lista vazia, pois não há placeholders no template)."`
    *   **Exemplo com Placeholders:**
        `"Jarvis, ensine o comando criar_diretorio_tmp. A descrição é 'Cria um diretório na pasta tmp'. O template do comando é 'mkdir /tmp/{{nome_pasta}}'. Os parâmetros do template são ['nome_pasta']." ` (O LLM precisaria ser treinado/prompted para formatar `template_parameters` como uma lista de strings).

    *   **Parâmetros da `learn_new_terminal_skill`:**
        *   `new_skill_name` (string): Um nome único para a nova habilidade (ex: `criar_diretorio_backup`).
        *   `new_skill_description` (string): Uma descrição clara para o LLM entender quando usar essa nova habilidade.
        *   `shell_command_template` (string): O comando de terminal a ser executado. Use placeholders no formato `{{nome_do_placeholder}}` para partes que serão fornecidas em tempo de execução.
            *   Exemplo: `echo "Backup de {{arquivo}} concluído em {{data}}"`
        *   `template_parameters` (lista de strings): Uma lista dos nomes exatos dos placeholders usados no `shell_command_template`.
            *   Exemplo para o template acima: `["arquivo", "data"]`

*   **Armazenamento:** As habilidades aprendidas são salvas no arquivo `learned_terminal_skills.json` na raiz do projeto e são recarregadas sempre que Jarvis inicia.

*   **Executando Habilidades de Terminal Aprendidas:**
    Após uma habilidade de terminal ser aprendida, você pode invocá-la como qualquer outra.
    *   Exemplo: Se você ensinou a habilidade `criar_diretorio_tmp` com o template `mkdir /tmp/{{nome_pasta}}`:
        `"Jarvis, use a habilidade criar_diretorio_tmp com nome_pasta igual a 'meu_novo_diretorio_123'."`
    Jarvis usará o LLM para identificar a habilidade `criar_diretorio_tmp`, extrair o parâmetro `nome_pasta` e executar o comando `mkdir /tmp/meu_novo_diretorio_123`.

*   **IMPORTANTE: Aviso de Segurança**
    A execução de comandos de terminal arbitrários, mesmo que aprendidos, carrega riscos de segurança significativos, especialmente se os comandos ou parâmetros puderem ser influenciados por fontes não confiáveis. Use esta funcionalidade com extrema cautela e apenas em ambientes controlados. Em um sistema de produção, seria necessário um sandboxing rigoroso e validação.

## Ajustando a Interpretação do LLM

Se Jarvis não estiver interpretando seus comandos como esperado:

1.  **Teste com `llm_interpreter.py`:**
    *   Certifique-se de que sua `GOOGLE_API_KEY` está no `.env`.
    *   Abra `llm_interpreter.py` e modifique a lista `test_commands_for_skills` com as frases que estão causando problemas.
    *   Execute `python llm_interpreter.py`. Observe a `chosen_skill` e os `provided_parameters` retornados pelo LLM.
2.  **Refine o Prompt Principal ou as Descrições das Habilidades:**
    *   **Prompt Principal:** A lógica de como o LLM escolhe habilidades e extrai parâmetros está no prompt dentro da função `get_command_interpretation` em `llm_interpreter.py`. Ajustar este prompt (ex: adicionando mais exemplos, clarificando instruções) pode melhorar significativamente a precisão.
    *   **Descrições das Habilidades:** O LLM usa o campo `description_for_llm` de cada habilidade (definido em `core_skills/*.py` ou ao aprender uma skill de terminal) para decidir qual delas é a mais relevante. Certifique-se de que estas descrições sejam claras, concisas e distintas.

## Próximos Passos e Contribuição

(Esta seção pode ser expandida com ideias futuras, como adicionar mais habilidades, melhorar a interface do usuário, etc.)

Contribuições são bem-vindas!
```
