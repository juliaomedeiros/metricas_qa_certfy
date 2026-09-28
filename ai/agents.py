import os
from crewai import Agent, Task, Crew, LLM


class QACrew:
    def __init__(self, dataframe_json):
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("❌ ERRO: A variável GOOGLE_API_KEY não foi encontrada no arquivo .env")
        
        self.llm = LLM(
            model="gemini/gemini-2.5-flash",
            api_key=api_key,
            temperature=0.3,
            verbose=True
        )
        self.data = dataframe_json

    def setup_agents(self):
        analyst = Agent(
            role='Especialista Sênior em Performance QA e Dados',
            goal='Identificar gargalos de produtividade por Analista e investigar o custo de tempo de cada Feature testada.',
            backstory=('Você é um Arquiteto de Testes de software focado em métricas de engenharia. '
                'Sua especialidade é ler dados consolidados (tempo gasto, defeitos, volume) '
                'e extrair insights valiosos. '
                'Regras obrigatórias: '
                '1. Sempre tratar unidades de tempo como "horas de esforço". '
                '2. Avaliar obrigatoriamente o esforço e os defeitos por Feature (captura de digitais, face, biográfico, etc). '
                '3. Avaliar a performance da equipe baseada em quem entrega mais volume vs quem gasta mais tempo em reteste.'
                '4. Avaliar o impacto dos defeitos no tempo total gasto, sugerindo melhorias para reduzir retrabalho.'
                '5. Estimar o tempo médio gasto em cada Feature, considerando somente o tempo de teste funcional e a media quando incluindo também o tempo de retrabalho (defeitos).'
            ),
            llm=self.llm
        )
        
        task = Task(
            description=
            f"""Aqui estão os dados consolidados do projeto em formato JSON: {self.data}\n\n"
                "O JSON contém duas chaves: 'performance_por_qa' e 'performance_por_feature'.\n"
                "Realize uma análise detalhada e escreva um Relatório Executivo contendo:\n"
                "1. **Análise de Features:** Liste as features analisadas (ex: captura de digitais). Qual consumiu mais horas? Qual gerou a maior proporção de defeitos em relação ao tempo testado?\n"
                "2. **Gargalos e Sugestões:** Onde o time está perdendo mais tempo (Teste limpo ou Retrabalho)? O que você sugere para otimizar?",
                "3. **Estimativa** COm base nos dados, estime o tempo médio gasto por Feature, considerando somente o teste funcional e também incluindo o retrabalho. Quais features têm maior variação entre esses dois cenários?""",
            expected_output="Um relatório analítico formatado em Markdown, com cabeçalhos claros, cobrindo análise de equipe e análise detalhada por feature.",
            agent=analyst
        )

        return Crew(agents=[analyst], tasks=[task])
    
    