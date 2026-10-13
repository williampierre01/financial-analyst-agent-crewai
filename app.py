"""
Interface Gradio do analista financeiro autonomo (Etapa 3).

crew.kickoff() e uma chamada sincrona e bloqueante -- para mostrar progresso
enquanto os agentes trabalham (em vez de travar a tela por 1-2 minutos), a
execucao roda numa thread separada, e os callbacks de mudanca de estagio
(ver agents.py::on_stage) empurram atualizacoes por uma fila thread-safe que
o generator do Gradio consome e transforma em `yield`.
"""

from __future__ import annotations

import os
import queue
import threading

import gradio as gr

from agents import run_analysis
from financial_data import normalize_ticker

STAGE_LABELS = {
    "gathering": "🔎 **Data Gatherer** coletando dados financeiros e noticias...",
    "quant": "📊 **Quant Analyst** calculando P/L, ROE, Margem Liquida e DCF...",
    "cio": "📝 **CIO** sintetizando o relatorio final...",
}


def analyze(ticker: str):
    try:
        ticker = normalize_ticker(ticker)
    except ValueError as exc:
        yield f"⚠️ {exc}"
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
            result_holder["error"] = True
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
            "Isso pode acontecer por indisponibilidade temporaria dos "
            "provedores de LLM (DeepSeek/Groq) ou de dados de mercado "
            "(Yahoo Finance). Confira a configuração ou tente novamente."
        )
    else:
        yield result_holder["report"]


with gr.Blocks(title="Analista Financeiro Autonomo") as demo:
    gr.Markdown(
        "# 📈 Análise de ações brasileiras\n"
        "Informe o código da ação na B3. Dados financeiros do Yahoo Finance.\n\n"
        "Sistema multi-agente (CrewAI + MCP) que coleta dados de mercado, "
        "calcula metricas fundamentalistas e gera um relatorio de due "
        "diligence. **Projeto de portfolio/demonstracao tecnica -- nao e "
        "recomendacao de investimento real.**"
    )

    with gr.Row():
        ticker_input = gr.Textbox(
            label="Código da ação",
            placeholder="Ex: PETR4, VALE3, ITUB4",
            scale=3,
        )
        submit_btn = gr.Button("Analisar", variant="primary", scale=1)

    output = gr.Markdown(label="Resultado")

    submit_btn.click(fn=analyze, inputs=[ticker_input], outputs=output)
    ticker_input.submit(fn=analyze, inputs=[ticker_input], outputs=output)

    gr.Examples(
        examples=["PETR4", "VALE3", "ITUB4"],
        inputs=ticker_input,
    )


if __name__ == "__main__":
    # Plataformas como Render definem a porta via variavel de ambiente PORT.
    # Localmente (Codespace), cai no 7860 de sempre.
    port = int(os.environ.get("PORT", 7860))
    demo.queue().launch(server_name="0.0.0.0", server_port=port)
