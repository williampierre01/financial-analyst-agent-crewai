"""Gradio adapter: render structured updates from a background analysis.

Financial data is published before interpretation, keeping the table visible
while the agents work. The service has no dependency on this UI.
"""

from __future__ import annotations

import os
import queue
import threading

import gradio as gr

from agents import run_analysis_result
from presentation import STAGE_LABELS, render_analysis_report
from financial_data import normalize_ticker


def analyze(ticker: str):
    try:
        ticker = normalize_ticker(ticker)
    except ValueError as exc:
        yield f"⚠️ {exc}"
        return

    update_queue = queue.Queue()

    def worker() -> None:
        try:
            run_analysis_result(
                ticker,
                on_update=lambda result: update_queue.put(("update", result)),
            )
        except Exception:
            update_queue.put(("error", None))
        finally:
            update_queue.put(("done", None))

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    last_report = STAGE_LABELS["gathering"]
    yield last_report
    while True:
        kind, payload = update_queue.get()
        if kind == "update":
            last_report = render_analysis_report(payload)
            yield last_report
        elif kind == "error":
            yield last_report + "\n\n❌ A análise foi interrompida. Tente novamente em alguns instantes."
        elif kind == "done":
            break
    thread.join()


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
