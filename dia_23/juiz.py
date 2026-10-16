import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv()
MODEL = "gemini-3.5-flash-lite"

class JulgamentoAuditoria(BaseModel):
    nota_groundedness: float = Field(ge=0.0, le=1.0, description="Nota de 0 a 1 indicando quanto a resposta e suportada apenas pela evidencia")
    nota_precisao: float = Field(ge=0.0, le=1.0, description="Nota de 0 a 1 indicando veracidade factual em relacao a verdade de referencia")
    trechos_da_evidencia_usados: list[str] = Field(description="Citacoes literais curtas da evidencia que sustentam a resposta")
    alucinacoes_detectadas: list[str] = Field(description="Afirmacoes feitas na resposta que nao possuem comprovacao na evidencia")
    veredito_final: str = Field(description="Justificativa sintetica do julgamento")

def julgar_resposta(evidencia: str, resposta_candidata: str, verdade_referencia: str) -> JulgamentoAuditoria:
    cliente = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    
    # TODO: Escreva a instrucao do sistema que ensina o Juiz a ser estrito e nao perdoar adivinhacoes.
    system_instruction = (
        "Voce e um Juiz Auditor Implacavel de Inteligencia Artificial (LLM-as-a-Judge). "
        "Sua missao e avaliar friamente a resposta candidata contra a evidencia fornecida. "
        "Regra 1: Se a resposta afirmar qualquer dado que nao esteja explicitamente legivel ou audivel na evidencia, "
        "classifique como alucinacao e reduza nota_groundedness proporcionalmente. "
        "Regra 2: Cite sempre trechos literais da evidencia em trechos_da_evidencia_usados."
        "Regra 3: nota_precisao mede APENAS se as afirmacoes batem com a verdade_absoluta_referencia, "
        "independente de estarem na evidencia. Uma afirmacao pode ser verdadeira e ainda assim alucinada. "
        "Regra 4: Divida a resposta em afirmacoes atomicas e calcule cada nota como (afirmacoes aprovadas) / (total)."

    )
    
    payload = json.dumps({
        "evidencia_fornecida": evidencia,
        "resposta_candidata": resposta_candidata,
        "verdade_absoluta_referencia": verdade_referencia
    }, ensure_ascii=False)
    
    resposta = cliente.models.generate_content(
        model=MODEL,
        contents=[payload],
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=JulgamentoAuditoria
        )
    )
    
    return JulgamentoAuditoria.model_validate_json(resposta.text or "{}")

if __name__ == "__main__":
    evidencia = "A imagem do print mostra: Erro 504 no servico auth-service as 14:10."
    resposta_teste = "Ocorreu um erro 504 no servico de autenticacao as 14:10, e 500 usuarios foram desconectados."
    verdade = "Log oficial: Erro 504 Gateway Timeout em auth-service as 14:10. Total real de desconexoes: 500."
    
    julgamento = julgar_resposta(evidencia, resposta_teste, verdade)
    print(julgamento.model_dump_json(indent=2))