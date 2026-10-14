"""Markdown adapter shared by the legacy CLI and Gradio."""
from analysis_models import AnalysisResult
from financial_data import render_data_report


STAGE_LABELS = {
    "gathering": "🔎 Coletando dados financeiros e notícias...",
    "quant": "📊 Analisando os indicadores disponíveis...",
    "cio": "📝 Preparando a interpretação dos resultados...",
}


def render_analysis_report(result: AnalysisResult) -> str:
    parts = [render_data_report(result.data)] if result.data is not None else []
    if result.status == "running":
        parts.append(STAGE_LABELS.get(result.stage, "Processando..."))
    if result.interpretation is not None:
        parts.append("## Interpretação assistida por IA\n\n" + result.interpretation)
    if result.interpretation_status == "skipped":
        parts.append("Não foi possível obter dados para analisar este ativo.")
    parts.extend(error["message"] for error in result.errors)
    return "\n\n".join(parts)
