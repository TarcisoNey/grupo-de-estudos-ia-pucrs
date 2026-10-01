import asyncio
import os
import sys

from dotenv import load_dotenv
from google import genai
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()
MODEL = "gemini-3.5-flash-lite"
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
PARAMS = StdioServerParameters(
    command=sys.executable,
    args=["server_demo.py"],
    cwd=os.path.dirname(os.path.abspath(__file__)),
)


async def main() -> None:
    async with stdio_client(PARAMS) as (leitura, escrita):
        async with ClientSession(leitura, escrita) as sessao:
            await sessao.initialize()

            catalogo = await sessao.list_resources()
            for recurso in catalogo.resources:
                print(f"- {recurso.uri} ({recurso.name})")

            conteudo = await sessao.read_resource("file:///docs/regras.md")
            regras = conteudo.contents[0].text
            print(regras)

            pergunta = (
                f"Com base nas regras abaixo, responda: posso rodar um DELETE em producao?\n\n"
                f"Regras:\n{regras}"
            )
            response = await client.aio.models.generate_content(model=MODEL, contents=pergunta)
            print(response.text)


if __name__ == "__main__":
    asyncio.run(main())