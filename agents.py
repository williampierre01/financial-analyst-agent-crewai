"""
Agentes CrewAI do pipeline de due diligence financeira.

Topologia sequencial: Data Gatherer -> Quant Analyst -> CIO.
Cada agente consome o mcp_server.py (Etapa 1) via o campo nativo `mcps` do
CrewAI, transporte stdio.
"""

from __future__ import annotations

import os
import sys

from crewai import Agent, Crew, Process, Task
from crewai.mcp import MCPServerStdio
from dotenv import load_dotenv

from llm_provider import get_llm

load_dotenv()

MCP_SERVER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_server.py")


def _build_mcp_connection() -> MCPServerStdio:
    return MCPServerStdio(
        command=sys.executable,  # usa o mesmo interpretador Python do processo atual
        args=[MCP_SERVER_PATH],
        env={**os.environ},
    )


def build_crew(ticker: str) -> Crew:
    deepseek_key = os.environ["DEEPSEEK_API_KEY"]
    groq_key = os.environ["GROQ_API_KEY"]
    llm = get_llm(deepseek_api_key=deepseek_key, groq_api_key=groq_key)

    mcp_connection = _build_mcp_connection()

    data_gatherer = Agent(
        role="Data Gatherer",
        goal=(
            f"Coletar todos os dados financeiros disponiveis para o ticker {ticker}: "
            "DRE, Balanco, Fluxo de Caixa, cotacao atual e as noticias mais recentes."
        ),
        backstory=(
            "Voce e um analista de dados metodico. Sua unica responsabilidade e "
            "extrair dados brutos via as ferramentas MCP disponiveis e organiza-los "
            "claramente para o proximo agente. Voce NUNCA interpreta ou opina sobre "
            "os dados -- apenas coleta e reporta, incluindo explicitamente quando "
            "algum dado nao estiver disponivel (fundamentals_available=false)."
        ),
        mcps=[mcp_connection],
        llm=llm,
        verbose=True,
    )

    quant_analyst = Agent(
        role="Quant Analyst",
        goal=(
            "Calcular metricas fundamentalistas (P/L, ROE, Margem Liquida) e uma "
            "projecao de DCF simplificada a partir dos dados coletados."
        ),
        backstory=(
            "Voce e um analista quantitativo rigoroso. Trabalha exclusivamente com "
            "os dados que o Data Gatherer forneceu -- nunca inventa numeros que nao "
            "estao la. Ao apresentar o DCF, voce SEMPRE deixa explicito que e um "
            "modelo didatico simplificado (WACC fixo, sem analise de sensibilidade), "
            "nao uma ferramenta de precificacao real. Se fundamentals_available for "
            "false, voce reporta que a analise quantitativa nao pode ser realizada "
            "por falta de dados, em vez de estimar valores."
        ),
        llm=llm,
        verbose=True,
    )

    cio = Agent(
        role="CIO (Chief Investment Officer)",
        goal=(
            "Sintetizar a analise quantitativa com o sentimento das noticias recentes "
            "e produzir um relatorio final em Markdown com recomendacao de "
            "Compra/Venda/Manutencao."
        ),
        backstory=(
            "Voce e um CIO experiente e cauteloso. Seu relatorio final SEMPRE inclui "
            "um disclaimer de que esta analise e um projeto de portfolio/demonstracao "
            "tecnica, nao uma recomendacao de investimento real, e que o DCF usado e "
            "simplificado. Voce e direto: recomendacao clara, mas sempre ancorada nos "
            "dados apresentados, nunca em suposicoes."
        ),
        llm=llm,
        verbose=True,
    )

    gather_task = Task(
        description=(
            f"Use as ferramentas MCP disponiveis para coletar DRE, Balanco, Fluxo de "
            f"Caixa, cotacao atual e noticias recentes do ticker {ticker}. Reporte os "
            "dados brutos organizados, sem interpretacao."
        ),
        expected_output=(
            "Um resumo estruturado com os dados financeiros e as noticias coletadas, "
            "incluindo o status de fundamentals_available."
        ),
        agent=data_gatherer,
    )

    quant_task = Task(
        description=(
            "Com base nos dados coletados, calcule P/L, ROE, Margem Liquida e uma "
            "projecao de DCF simplificada. Se os dados fundamentais nao estiverem "
            "disponiveis, reporte isso claramente em vez de estimar."
        ),
        expected_output=(
            "Metricas calculadas com os valores usados em cada formula, e a "
            "projecao de DCF com o disclaimer de que e um modelo didatico."
        ),
        agent=quant_analyst,
        context=[gather_task],
    )

    cio_task = Task(
        description=(
            f"Produza o relatorio final em Markdown para {ticker}, combinando a "
            "analise quantitativa com o sentimento das noticias recentes. Inclua "
            "recomendacao de Compra/Venda/Manutencao e os disclaimers necessarios."
        ),
        expected_output=(
            "Relatorio em Markdown com: resumo executivo, metricas principais, "
            "sentimento de mercado, recomendacao final e disclaimers."
        ),
        agent=cio,
        context=[gather_task, quant_task],
    )

    return Crew(
        agents=[data_gatherer, quant_analyst, cio],
        tasks=[gather_task, quant_task, cio_task],
        process=Process.sequential,
        verbose=True,
    )


if __name__ == "__main__":
    ticker_arg = sys.argv[1] if len(sys.argv) > 1 else "AAPL"
    crew = build_crew(ticker_arg)
    result = crew.kickoff()
    print("\n\n=== RELATORIO FINAL ===\n")
    print(result)
