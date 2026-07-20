"""
Interface Gradio do analista financeiro autonomo (Etapa 3).

crew.kickoff() e uma chamada sincrona e bloqueante -- para mostrar progresso
enquanto os agentes trabalham (em vez de travar a tela por 1-2 minutos), a
execucao roda numa thread separada, e os callbacks de mudanca de estagio
(ver agents.py::on_stage) empurram atualizacoes por uma fila thread-safe que
o generator do Gradio consome e transforma em `yield`.
"""

from __future__ import annotations

import queue
import threading

import gradio as gr

from agents import run_analysis

STAGE_LABELS = {
    "gathering": "🔎 **Data Gatherer** coletando dados financeiros e noticias...",
    "quant": "📊 **Quant Analyst** calculando P/L, ROE, Margem Liquida e DCF...",
    "cio": "📝 **CIO** sintetizando o relatorio final...",
}


def analyze(ticker: str):
    ticker = (ticker or "").strip().upper()
    if not ticker:
        yield "⚠️ Digite um ticker antes de analisar (ex: AAPL, PETR4.SA)."
        return

    update_queue: "queue.Queue[tuple[str, str]]" = queue.Queue()
    result_holder: dict = {}

    def on_stage(stage_key: str) -> None:
        update_queue.put(("stage", stage_key))

    def worker() -> None:
        try:
            report = run_analysis(ticker, on_stage=on_stage)
            result_holder["report"] = report
        except Exception as exc:  # noqa: BLE001
            result_holder["error"] = str(exc)
        finally:
            update_queue.put(("done", ""))

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    yield STAGE_LABELS["gathering"]

    while True:
        kind, payload = update_queue.get()
        if kind == "stage":
            yield STAGE_LABELS.get(payload, f"Processando ({payload})...")
        elif kind == "done":
            break

    thread.join()

    if "error" in result_holder:
        yield (
            "❌ **A analise falhou.**\n\n"
            f"Detalhe do erro: `{result_holder['error']}`\n\n"
            "Isso pode acontecer por indisponibilidade temporaria dos "
            "provedores de LLM (DeepSeek/Groq) ou de dados de mercado "
            "(yfinance/Stooq). Tente novamente em alguns instantes."
        )
    else:
        yield result_holder["report"]


with gr.Blocks(title="Analista Financeiro Autonomo") as demo:
    gr.Markdown(
        "# 📈 Analista Financeiro Autonomo\n"
        "Sistema multi-agente (CrewAI + MCP) que coleta dados de mercado, "
        "calcula metricas fundamentalistas e gera um relatorio de due "
        "diligence. **Projeto de portfolio/demonstracao tecnica -- nao e "
        "recomendacao de investimento real.**"
    )

    with gr.Row():
        ticker_input = gr.Textbox(
            label="Ticker",
            placeholder="Ex: AAPL, MSFT, PETR4.SA, VALE3.SA",
            scale=4,
        )
        submit_btn = gr.Button("Analisar", variant="primary", scale=1)

    output = gr.Markdown(label="Resultado")

    submit_btn.click(fn=analyze, inputs=ticker_input, outputs=output)
    ticker_input.submit(fn=analyze, inputs=ticker_input, outputs=output)

    gr.Examples(
        examples=["AAPL", "MSFT", "PETR4.SA"],
        inputs=ticker_input,
    )


if __name__ == "__main__":
    demo.queue().launch()