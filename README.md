---
title: Financial Analyst Agent
emoji: 📈
colorFrom: green
colorTo: blue
sdk: gradio
sdk_version: 5.49.1
app_file: app.py
pinned: false
short_description: Autonomous AI agent for financial data analysis using CrewAI.
---

# 📊 Financial Analyst Agent: Autonomous AI com CrewAI & MCP

[![Deploy: Hugging Face](https://img.shields.io/badge/Deploy-Hugging%20Face-yellow)]([COLE_AQUI_O_LINK_DO_SEU_SPACE])
[![Stack: CrewAI](https://img.shields.io/badge/Stack-CrewAI-orange)](#)
[![Stack: Python](https://img.shields.io/badge/Stack-Python-blue)](#)

## 1. O Problema de Negócio
[Descreva em 2 linhas o que isso resolve. Ex: Sistema desenvolvido para automatizar a coleta, leitura e cruzamento de dados financeiros de mercado, reduzindo o tempo de pesquisa e gerando relatórios de investimentos precisos.]

## 2. Arquitetura da Solução
A aplicação opera baseada em um workflow de agentes autônomos para garantir raciocínio analítico estruturado e execução de tarefas em cadeia.
*   **Orquestração:** CrewAI (gerenciamento das *tasks* de extração e análise).
*   **Integração de Dados:** Model Context Protocol (MCP) para acesso em tempo real a APIs financeiras.
*   **Modelo Base (LLM):** Deepseek-R1 (selecionado pela otimização nativa em raciocínio lógico/matemático).
*   **Interface:** Gradio Web UI.

## 3. Setup e Execução Local

**Pré-requisitos:** Python 3.10+ e chaves de API válidas.

```bash
# Clone o repositório
git clone [https://github.com/williampierre01/financial-analyst-agent-crewai.git](https://github.com/williampierre01/financial-analyst-agent-crewai.git)
cd financial-analyst-agent-crewai

# Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate no Windows

# Instale as dependências
pip install -r requirements.txt
