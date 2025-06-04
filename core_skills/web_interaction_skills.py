# core_skills/web_interaction_skills.py
"""
Este módulo define habilidades (skills) nativas para Jarvis que interagem com APIs web
para buscar informações como previsão do tempo e piadas aleatórias.
"""
import requests # Para fazer requisições HTTP
from geopy.geocoders import Nominatim # Para converter nomes de locais em coordenadas
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable, GeocoderServiceError
import json # Embora requests.json() já faça o parse, pode ser útil para outras manipulações
from typing import Dict, Any, List

# Importar a estrutura base de Skill
try:
    from skill_interface import Skill, ParameterDefinition
except ImportError:
    # Fallback para execução direta ou problemas de path (SkillManager deve lidar com isso em execução normal)
    print("AVISO [web_interaction_skills]: Falha ao importar 'Skill' de 'skill_interface'.")
    class ParameterDefinition(dict): pass
    from dataclasses import dataclass
    @dataclass
    class Skill: name: str; description_for_llm: str; parameters_expected: List; execute: Any


# --- Habilidade: Obter Previsão do Tempo ---

def execute_get_weather_forecast(parameters: Dict[str, Any]) -> str:
    """
    Função de execução para a skill 'get_weather_forecast'.
    Busca a previsão do tempo para uma localização usando Open-Meteo API.
    """
    location_name = parameters.get("location_name")
    if not location_name or not isinstance(location_name, str):
        return "AVISO [GetWeather]: O nome da localização (parâmetro 'location_name') é obrigatório."

    geolocator = Nominatim(user_agent="jarvis_voice_assistant_skill") # User-agent é importante

    try:
        print(f"DEBUG [GetWeather]: Geocodificando '{location_name}'...")
        location = geolocator.geocode(location_name, timeout=10) # Timeout de 10s para geocodificação
        if not location:
            return f"Jarvis: Desculpe, não consegui encontrar coordenadas para '{location_name}'. Tente ser mais específico ou verifique o nome."

        lat, lon = location.latitude, location.longitude
        print(f"DEBUG [GetWeather]: Coordenadas para '{location.address}': Lat={lat}, Lon={lon}")

        # Usar a API Open-Meteo (não requer chave de API para uso básico)
        # Parâmetros: current_weather=true para tempo atual.
        # hourly=temperature_2m,precipitation_probability para previsão horária de temp e prob. de chuva.
        # forecast_days=1 para obter apenas a previsão para o dia atual/próximas 24h.
        weather_api_url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current_weather=true"
            f"&hourly=temperature_2m,precipitation_probability,weathercode"
            f"&daily=weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max"
            f"&timezone=auto" # Detecta o fuso horário automaticamente com base nas coordenadas
            f"&forecast_days=1"
        )

        print(f"DEBUG [GetWeather]: Consultando API de tempo: {weather_api_url}")
        response = requests.get(weather_api_url, timeout=15) # Timeout de 15s para a API de tempo
        response.raise_for_status() # Levanta uma exceção para códigos de erro HTTP (4xx ou 5xx)

        weather_data = response.json()
        # print(f"DEBUG [GetWeather]: Dados recebidos: {json.dumps(weather_data, indent=2)}")


        # Formatar a resposta para o usuário
        current_weather = weather_data.get("current_weather")
        daily_forecast = weather_data.get("daily")

        if not current_weather:
            return "Jarvis: Não consegui obter os dados do tempo atual da resposta da API."

        temp = current_weather.get("temperature")
        windspeed = current_weather.get("windspeed")
        weather_code = current_weather.get("weathercode") # Código numérico do tempo

        # Descrições simples para códigos WMO (Weather Interpretation Codes) mais comuns
        # Fonte: https://open-meteo.com/en/docs (seção WMO Weather interpretation codes)
        wmo_codes_desc = {
            0: "Céu limpo", 1: "Principalmente limpo", 2: "Parcialmente nublado", 3: "Nublado",
            45: "Nevoeiro", 48: "Nevoeiro depositando geada",
            51: "Chuvisco leve", 53: "Chuvisco moderado", 55: "Chuvisco denso",
            56: "Chuvisco gelado leve", 57: "Chuvisco gelado denso",
            61: "Chuva fraca", 63: "Chuva moderada", 65: "Chuva forte",
            66: "Chuva gelada fraca", 67: "Chuva gelada forte",
            71: "Neve fraca", 73: "Neve moderada", 75: "Neve forte",
            77: "Grãos de neve",
            80: "Aguaceiros fracos", 81: "Aguaceiros moderados", 82: "Aguaceiros violentos",
            85: "Aguaceiros de neve fracos", 86: "Aguaceiros de neve fortes",
            95: "Trovoada ligeira ou moderada",
            96: "Trovoada com granizo ligeiro", 99: "Trovoada com granizo forte"
        }
        weather_description = wmo_codes_desc.get(weather_code, "Condição desconhecida")

        response_parts = [f"O tempo atual em {location.address.split(',')[0]} é: {temp}°C com {weather_description}."]
        if windspeed is not None:
            response_parts.append(f"Vento a {windspeed} km/h.")

        if daily_forecast:
            temp_max = daily_forecast.get("temperature_2m_max", [None])[0]
            temp_min = daily_forecast.get("temperature_2m_min", [None])[0]
            precip_prob_max = daily_forecast.get("precipitation_probability_max", [None])[0]
            if temp_max is not None and temp_min is not None:
                response_parts.append(f"Máxima de {temp_max}°C e mínima de {temp_min}°C para hoje.")
            if precip_prob_max is not None:
                response_parts.append(f"Chance de precipitação hoje é de {precip_prob_max}%.")

        return " ".join(response_parts)

    except GeocoderTimedOut:
        return f"Jarvis: O serviço de geocodificação demorou muito para responder para '{location_name}'."
    except (GeocoderUnavailable, GeocoderServiceError) as e:
        return f"Jarvis: Problema com o serviço de geocodificação para '{location_name}': {e}. Tente novamente mais tarde."
    except requests.exceptions.HTTPError as e:
        return f"Jarvis: Erro ao contatar a API de previsão do tempo (HTTP {e.response.status_code})."
    except requests.exceptions.ConnectionError:
        return "Jarvis: Não consegui me conectar à API de previsão do tempo. Verifique sua conexão com a internet."
    except requests.exceptions.Timeout:
        return "Jarvis: A API de previsão do tempo demorou muito para responder."
    except requests.exceptions.RequestException as e:
        return f"Jarvis: Erro inesperado ao buscar a previsão do tempo: {e}"
    except KeyError as e:
        # print(f"DEBUG [GetWeather]: Erro de chave ao processar dados: {e}. Dados: {weather_data}")
        return f"Jarvis: Não consegui processar os dados da previsão do tempo recebidos. Chave faltando: {e}"
    except Exception as e: # Captura geral para outros erros inesperados
        print(f"ERRO INESPERADO [GetWeather]: {e}")
        return "Jarvis: Desculpe, ocorreu um erro inesperado ao buscar a previsão do tempo."

get_weather_forecast_skill = Skill(
    name="get_weather_forecast",
    description_for_llm="Obtém e informa a previsão do tempo atual para uma cidade ou localização especificada pelo usuário.",
    parameters_expected=[
        ParameterDefinition(name="location_name", type="string", description="O nome da cidade ou localização para a qual a previsão do tempo é solicitada (ex: 'Paris', 'Nova York, EUA', 'minha cidade atual').", required=True)
    ],
    execute=execute_get_weather_forecast
)

# --- Habilidade: Contar Piada Aleatória ---

def execute_tell_random_joke(parameters: Dict[str, Any]) -> str:
    """
    Função de execução para a skill 'tell_random_joke'.
    Busca uma piada aleatória de uma API pública.
    """
    # Nenhum parâmetro é esperado para esta skill, mas o argumento está lá para consistência.
    _ = parameters # Para marcar como não utilizado e evitar linting error.

    # API pública de piadas (pode haver outras, esta é uma comum)
    # Documentação não oficial, mas frequentemente usada: https://github.com/15Dkatz/official_joke_api
    joke_api_url = "https://official-joke-api.appspot.com/random_joke"
    # Outra opção, se a primeira falhar ou para variedade: https://v2.jokeapi.dev/joke/Any?type=twopart
    # (JokeAPI tem mais opções de customização mas pode ser mais complexa)

    try:
        print(f"DEBUG [TellJoke]: Consultando API de piadas: {joke_api_url}")
        response = requests.get(joke_api_url, timeout=10) # Timeout de 10s
        response.raise_for_status() # Verifica erros HTTP

        joke_data = response.json()

        if "setup" in joke_data and "punchline" in joke_data:
            return f"{joke_data['setup']} ... {joke_data['punchline']}"
        else:
            # Se o formato da piada for inesperado
            print(f"AVISO [TellJoke]: Formato de piada inesperado da API: {joke_data}")
            return "Jarvis: Encontrei uma piada, mas não no formato que eu esperava. Que sem graça!"

    except requests.exceptions.HTTPError as e:
        return f"Jarvis: Não consegui buscar uma piada no momento (Erro HTTP: {e.response.status_code})."
    except requests.exceptions.ConnectionError:
        return "Jarvis: Sem conexão para buscar piadas. Verifique a internet."
    except requests.exceptions.Timeout:
        return "Jarvis: O serviço de piadas demorou muito para responder."
    except requests.exceptions.RequestException as e:
        return f"Jarvis: Erro ao buscar uma piada: {e}"
    except Exception as e:
        print(f"ERRO INESPERADO [TellJoke]: {e}")
        return "Jarvis: Desculpe, algo deu errado enquanto eu tentava encontrar uma piada."

tell_random_joke_skill = Skill(
    name="tell_random_joke",
    description_for_llm="Conta uma piada aleatória para o usuário. Não requer parâmetros.",
    parameters_expected=[], # Nenhum parâmetro é necessário para esta habilidade.
    execute=execute_tell_random_joke
)

# --- Lista de Skills para Registro ---
skills_to_register: List[Skill] = [
    get_weather_forecast_skill,
    tell_random_joke_skill,
]

# Bloco de teste para execução direta do script
if __name__ == '__main__':
    print("--- Testando Habilidades de Interação Web (web_interaction_skills.py) ---")

    print("\n--- Teste get_weather_forecast ---")
    # Teste de previsão do tempo (pode requerer conexão com a internet para funcionar)
    weather_params_1 = {"location_name": "São Paulo, Brasil"}
    print(f"Comando: Previsão do tempo para '{weather_params_1['location_name']}'")
    print(f"Resultado: {execute_get_weather_forecast(weather_params_1)}")

    weather_params_2 = {"location_name": "London, UK"}
    print(f"\nComando: Previsão do tempo para '{weather_params_2['location_name']}'")
    print(f"Resultado: {execute_get_weather_forecast(weather_params_2)}")

    weather_params_invalid = {"location_name": "Cidade Muito Fictícia Que Não Existe 123XYZ"}
    print(f"\nComando: Previsão do tempo para '{weather_params_invalid['location_name']}'")
    print(f"Resultado: {execute_get_weather_forecast(weather_params_invalid)}")

    print(f"\nComando: Previsão do tempo sem location_name")
    print(f"Resultado: {execute_get_weather_forecast({})}")


    print("\n--- Teste tell_random_joke ---")
    # Teste de contar piada (requer conexão com a internet)
    print("Comando: Contar uma piada")
    # Executar algumas vezes para ver piadas diferentes
    for i in range(2):
        print(f"Resultado Piada {i+1}: {execute_tell_random_joke({})}")
        time.sleep(0.5) # Pequeno delay para não sobrecarregar a API se houver limite de taxa

```
