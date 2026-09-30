"""Dia 12 - Bloco 2: declarar ferramentas e OLHAR a intencao do modelo (sem executar nada)."""
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
MODEL = "gemini-3.8-flash"
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def calcular_faturamento(regiao: str, ano: int) -> dict:
    """Retorna o faturamento anual, em reais, de uma regiao comercial brasileira.

    Args:
        regiao: nome da regiao, por exemplo "Sul" ou "Nordeste".
        ano: ano de referencia com 4 digitos, por exemplo 2025.
    """
    base = {"Sul": 1_250_000.0, "Sudeste": 3_400_000.0, "Nordeste": 980_000.0}
    return {"regiao": regiao, "ano": ano, "faturamento": base.get(regiao, 0.0)}


def consultar_cotacao(moeda: str) -> float:
    """Retorna a cotacao atual em reais de uma moeda estrangeira (USD, EUR ou GBP)."""
    tabela = {"USD": 5.20, "EUR": 5.65, "GBP": 6.60}
    moeda = moeda.upper()
    if moeda not in tabela:
        raise ValueError(f"Moeda desconhecida: {moeda}")
    return tabela[moeda]


config = types.GenerateContentConfig(
    tools=[calcular_faturamento, consultar_cotacao],
    # Desliga a execucao automatica: queremos ver a intencao do modelo
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
)

PERGUNTAS = [
    "Quanto a regiao Sul faturou em 2025?",
    "Quanto custa um dolar hoje em reais?",
    "O que e um JOIN em SQL?",
]

if __name__ == "__main__":
    for pergunta in PERGUNTAS:
        response = client.models.generate_content(model=MODEL, contents=pergunta, config=config)
        print("PERGUNTA:", pergunta)
        if response.function_calls:
            for chamada in response.function_calls:
                # O modelo NAO executou nada: so disse qual funcao quer e com quais argumentos
                print("  ferramenta pedida:", chamada.name)
                print("  argumentos:", dict(chamada.args))
        else:
            print("  resposta em texto:", response.text)
        print()
