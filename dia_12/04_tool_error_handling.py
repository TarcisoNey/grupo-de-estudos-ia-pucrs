"""Dia 12 - Bloco 5: a ferramenta pode falhar, o programa nao pode cair."""
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
MODEL = "gemini-3.8-flash"
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


def dividir_metricas(numerador: float, denominador: float) -> dict:
    """Divide duas metricas e retorna a razao (por exemplo, erros por requisicao)."""
    return {"razao": numerador / denominador}


def consultar_servico_externo(servico: str) -> dict:
    """Consulta o status de um servico externo pelo nome."""
    raise ConnectionError(f"Servico '{servico}' temporariamente indisponivel")


FERRAMENTAS = {
    "dividir_metricas": dividir_metricas,
    "consultar_servico_externo": consultar_servico_externo,
}

config = types.GenerateContentConfig(
    tools=list(FERRAMENTAS.values()),
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
)


def executar_com_seguranca(nome: str, args: dict) -> dict:
    """Executa a ferramenta e transforma qualquer excecao em um resultado estruturado."""
    try:
        funcao = FERRAMENTAS[nome]  # KeyError se o modelo inventar um nome
        return {"status": "sucesso", "resultado": funcao(**args)}
    except KeyError:
        return {"status": "falha", "error": f"Ferramenta desconhecida: {nome}"}
    except ZeroDivisionError:
        return {"status": "falha", "error": "Divisao por zero nao permitida"}
    except Exception as erro:
        # Mensagem curta (tipo + texto), sem traceback completo
        return {"status": "falha", "error": f"{type(erro).__name__}: {erro}"}


def responder(pergunta: str) -> str:
    contents = [types.Content(role="user", parts=[types.Part(text=pergunta)])]
    response = client.models.generate_content(model=MODEL, contents=contents, config=config)
    if not response.function_calls:
        return response.text

    contents.append(response.candidates[0].content)
    partes_resposta = []
    for chamada in response.function_calls:
        resultado = executar_com_seguranca(chamada.name, dict(chamada.args))
        print(f"  [ferramenta] {chamada.name}({dict(chamada.args)}) -> {resultado}")
        partes_resposta.append(
            types.Part.from_function_response(name=chamada.name, response=resultado)
        )
    contents.append(types.Content(role="user", parts=partes_resposta))

    response = client.models.generate_content(model=MODEL, contents=contents, config=config)
    return response.text


PERGUNTAS = [
    "Qual a razao entre 50 erros e 0 requisicoes?",
    "O servico de pagamentos esta no ar?",
]

if __name__ == "__main__":
    for pergunta in PERGUNTAS:
        print("PERGUNTA:", pergunta)
        print("RESPOSTA:", responder(pergunta), "\n")
