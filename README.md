# 🚀 QA Metrics Analytics & AI Dashboard para o produto Certfy Onboarding Presencial

Um dashboard interativo e inteligente projetado para extrair, processar e analisar métricas de performance da equipe de Quality Assurance (QA) diretamente do Azure DevOps to time Onboarding Presencial. 
O sistema oferece uma visão clara sobre o esforço de testes, gargalos de retrabalho e integra Inteligência Artificial para gerar relatórios executivos automatizados.

## 🎯 Objetivo do Projeto

Transformar os dados brutos de movimentação de cards do Azure DevOps em informações acionáveis. A ferramenta responde a perguntas críticas de negócio, como:
- Quanto tempo real (horas úteis) a equipe gasta em Teste Funcional vs. Retrabalho (Defeitos)?
- Qual é a produtividade e o volume de entregas por Analista de QA?
- Quais *Features* do sistema consomem mais tempo de teste e geram mais bugs?
- Quais são os principais gargalos de qualidade da sprint atual?

## ✨ Principais Funcionalidades

- **Integração Nativa com Azure DevOps:** Mineração direta via API rastreando o histórico de revisões (estado a estado) dos Work Items.
- **Cálculo Preciso de Horas Úteis:** Motor matemático customizado que converte fusos horários (UTC para Local), ignora fins de semana e considera apenas o horário comercial (08h às 18h).
- **Métricas de Retrabalho:** Rastreamento de itens "filhos" (Defeitos) atrelados às histórias, isolando o tempo de "Teste Limpo" do tempo de "Correção de Bug".
- **Agrupamento por Feature:** Categorização automática baseada em *Tags* do Azure (ex: Captura Biográfica, Captura de Face, etc).
- **Relatórios IA (CrewAI + Google Gemini):** Um agente autônomo de IA que lê os dados consolidados do dashboard e gera um resumo executivo com insights e sugestões de melhoria.

## 🛠️ Tecnologias Utilizadas

- **[Python 3.10+](https://www.python.org/):** Linguagem base do projeto.
- **[Streamlit](https://streamlit.io/):** Framework para construção rápida e reativa do frontend/dashboard em Python.
- **[Plotly Express](https://plotly.com/python/):** Biblioteca para os gráficos interativos e dinâmicos.
- **[Pandas](https://pandas.pydata.org/):** Engenharia de dados, agregações e manipulação de DataFrames.
- **[Azure DevOps Python API](https://github.com/microsoft/azure-devops-python-api):** SDK oficial para extração de Work Items e Revisions.
- **[CrewAI](https://www.crewai.com/) & [Google Generative AI](https://aistudio.google.com/):** Orquestração de agentes de IA usando o modelo `gemini-1.5-flash` para análise de dados.

## 📁 Estrutura do Projeto

```text
qa_metrics_crew/
├── app.py               # Interface do usuário (Streamlit) e renderização dos gráficos
├── azure_tools.py       # Lógica de conexão e mineração de dados do Azure DevOps
├── utils_logic.py       # Regras de negócio, cálculo de horas úteis e tratamento de tags
├── agents.py            # Configuração do CrewAI, Prompts e integração com o Gemini
├── requirements.txt     # Dependências do projeto
└── .env                 # Arquivo de variáveis de ambiente (NÃO VERSIONAR)


```text
qa_metrics_crew/
├── app.py               # Interface do usuário (Streamlit) e renderização dos gráficos
├── azure_tools.py       # Lógica de conexão e mineração de dados do Azure DevOps
├── utils_logic.py       # Regras de negócio, cálculo de horas úteis e tratamento de tags
├── agents.py            # Configuração do CrewAI, Prompts e integração com o Gemini
├── requirements.txt     # Dependências do projeto
└── .env                 # Arquivo de variáveis de ambiente (NÃO VERSIONAR)


🚀 Como Executar Localmente
1. Pré-requisitos
Certifique-se de ter o Python instalado na sua máquina. Recomenda-se o uso de um ambiente virtual (venv).

2. Instalação das Dependências
Clone o repositório e instale as bibliotecas necessárias:

git clone [https://github.com/seu-usuario/qa-metrics-analytics.git](https://github.com/seu-usuario/qa-metrics-analytics.git)
cd qa-metrics-analytics
pip install -r requirements.txt

3. Configuração das Variáveis de Ambiente
Crie um arquivo chamado .env na raiz do projeto e preencha com as suas credenciais:

Snippet de código
# Credenciais do Azure DevOps
AZURE_ORG_URL=[https://dev.azure.com/SuaOrganizacao](https://dev.azure.com/SuaOrganizacao)
AZURE_PAT=seu_personal_access_token_aqui
AZURE_PROJECT=NomeDoSeuProjeto
AZURE_AREA_PATH=Caminho\Da\Sua\Area

# Credenciais de IA (Google AI Studio)
GOOGLE_API_KEY=sua_api_key_do_gemini_aqui
Dica: O AZURE_PAT precisa ter permissão de leitura de Work Items no Azure.

4. Iniciando a Aplicação
Com tudo configurado, inicie o servidor do Streamlit:

Bash
streamlit run app.py
A aplicação abrirá automaticamente no seu navegador padrão (geralmente em http://localhost:8501).

🧠 Regras de Negócio Importantes
O tempo de um card só começa a ser contabilizado quando ele entra na coluna "Teste Funcional". A coluna "Pronto para Testes" atua apenas como fila/volume.

Se um card for reprovado e voltar de "Teste Funcional" para "Pronto para Testes", o relógio desse ciclo é zerado para manter a precisão do esforço atual.

O tempo de retrabalho é somado buscando todos os Work Items do tipo Defeito que sejam "Filhos" (Child) do card principal testado.