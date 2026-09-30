"""Dia 12 - Bloco 4: Multi-Tool Router (4 ferramentas, 6 prompts, placar de roteamento)."""
import os
import re
import statistics

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
MODEL = "gemini-3.8-flash"
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def obter_temperatura_servidor(datacenter: str) -> dict:
    """Retorna a temperatura atual em graus Celsius de um datacenter especifico (sp-01, rs-02 ou rj-03).
    Use apenas quando o usuario pedir a leitura atual de um datacenter nomeado."""
    tabela = {"sp-01": 24.5, "rs-02": 21.0, "rj-03": 27.8}
    return {"datacenter": datacenter, "celsius": tabela[datacenter]}


def verificar_status_banco(cluster: str) -> dict:
    """Retorna o status operacional atual de um cluster de banco de dados especifico (prod, homolog ou analytics).
    Use apenas para consultar o estado de um cluster nomeado; nao use para explicar o que e um cluster."""
    tabela = {"prod": "saudavel", "homolog": "degradado", "analytics": "offline"}
    return {"cluster": cluster, "status": tabela[cluster]}


def calcular_desvio_padrao(valores: list[float]) -> float:
    """Calcula o desvio padrao amostral de uma lista concreta com pelo menos 2 numeros.
    Use apenas quando o usuario fornecer os valores numericos; nao use para explicar o conceito."""
    return round(statistics.stdev(valores), 2)


def validar_formato_documento(cnpj: str) -> dict:
    """Confere apenas o FORMATO de um CNPJ (14 digitos, com ou sem pontuacao); nao consulta a Receita."""
    digitos = re.sub(r"\D", "", cnpj)  # remove . / - e espacos
    return {"cnpj": cnpj, "formato_valido": len(digitos) == 14}


FERRAMENTAS = {
    "obter_temperatura_servidor": obter_temperatura_servidor,
    "verificar_status_banco": verificar_status_banco,
    "calcular_desvio_padrao": calcular_desvio_padrao,
    "validar_formato_documento": validar_formato_documento,
}


def responder(pergunta: str) -> tuple[str, str | None]:
    """Mesmo ciclo do 02, mas retorna (texto_final, nome_da_primeira_ferramenta_ou_None)."""
    config = types.GenerateContentConfig(
        tools=list(FERRAMENTAS.values()),
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    contents = [types.Content(role="user", parts=[types.Part(text=pergunta)])]

    response = client.models.generate_content(model=MODEL, contents=contents, config=config)
    if not response.function_calls:
        return response.text, None

    primeira = response.function_calls[0].name
    contents.append(response.candidates[0].content)

    partes_resposta = []
    for chamada in response.function_calls:
        resultado = FERRAMENTAS[chamada.name](**chamada.args)
        partes_resposta.append(
            types.Part.from_function_response(name=chamada.name, response={"result": resultado})
        )
    contents.append(types.Content(role="user", parts=partes_resposta))

    response = client.models.generate_content(model=MODEL, contents=contents, config=config)
    return response.text, primeira


# (prompt, ferramenta_esperada ou None quando NAO deve chamar ferramenta)
BATERIA = [
    ("Qual a temperatura do datacenter rs-02?", "obter_temperatura_servidor"),
    ("O cluster analytics esta funcionando?", "verificar_status_banco"),
    ("Qual o desvio padrao de 10, 12, 9, 15 e 11?", "calcular_desvio_padrao"),
    ("O CNPJ 12.345.678/0001-95 tem formato valido?", "validar_formato_documento"),
    ("Explique em duas frases o que e um cluster de banco de dados.", None),
    ("Para que serve o desvio padrao em monitoramento de servidores?", None),
]

if __name__ == "__main__":
    acertos = 0
    for pergunta, esperada in BATERIA:
        texto, chamada = responder(pergunta)
        ok = chamada == esperada
        acertos += ok
        print(f"[{'OK' if ok else 'ERRO'}] {pergunta}")
        print(f"   esperada={esperada} | chamada={chamada}")
        print(f"   resposta: {texto.strip()[:200]}\n")
    print(f"Roteamento correto: {acertos}/{len(BATERIA)}")
