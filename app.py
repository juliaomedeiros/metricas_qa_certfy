import streamlit as st
import base64
from dotenv import load_dotenv
import plotly.express as px

# --- IMPORTS DA NOSSA ARQUITETURA ---
from services.azure_tools import AzureMiner
from ai.agents import QACrew 
from database.database import PostgresDB
from utils.utils_logic import format_hours_to_string 

st.set_page_config(layout="wide", page_title="QA Analytics")
load_dotenv()

# --- 1. FUNÇÕES DE CARREGAMENTO DE ASSETS ---
def carregar_css(file_name):
    try:
        with open(file_name, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

def get_base64_image(path):
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return "" 

carregar_css("assets/style.css")

# --- 2. PALETA DE CORES FIXA PARA FEATURES ---
FEATURE_COLORS = {
    'captura de digitais': '#00C2FF',     
    'captura de face': '#636EFA',          
    'captura biografica': '#EF553B',       
    'captura de assinatura': '#00CC96',    
    'Análises Técnicas': '#FFA15A',
    'Admin FrontEnd': '#FF6692',        
    'Admin API': '#19D3F3',          
    'Atendimento FrontEnd': '#B6E880', 
    'Outros': '#AB63FA'                    
}

# --- CABEÇALHO ---
img_base64 = get_base64_image("assets/img/certfy.png")
if img_base64:
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <img src="data:image/png;base64,{img_base64}" width="50">
        <h2 style="margin: 0 0 0 15px; font-weight: 600;">Métricas QA - Dashboard Onboarding Presencial</h2>
    </div>
    """, unsafe_allow_html=True)
else:
    st.title("🚀 Métricas QA - Dashboard de Performance")

# --- 3. CONEXÃO E DADOS ---
if 'data' not in st.session_state:
    st.session_state.data = None

db = PostgresDB() 

col_sync, col_space = st.columns([2, 8])
with col_sync:
    if st.button("🔄 Sincronizar Dados do Azure", use_container_width=True):
        with st.status("Buscando informações no board do projeto...", expanded=True) as status:
            miner = AzureMiner()
            df_azure = miner.get_qa_metrics_data()
            db.upsert_data(df_azure) 
            status.update(label="✅ Dados Atualizados com Sucesso!", state="complete", expanded=False)
            st.rerun() 

df = db.get_all_data()

# --- 4. PREPARAÇÃO DOS DADOS ---
if df is not None and not df.empty:
    
    # Base
    df['Tempo_Total_Esforco'] = df['Tempo_QA_Pai'] + df['Tempo_Rework_Filhos']
    df['Texto_Tempo_Formatado'] = df['Tempo_Total_Esforco'].apply(format_hours_to_string)

    # Agrupamento: Features
    df_feature_summary = df.groupby('Tag_Agrupada').agg({
        'Tempo_Total_Esforco': 'sum',
        'Card_Count': 'sum',
        'Qtd_Defeitos': 'sum'
    }).reset_index()
    
    # Médias de Features
    df_feature_summary['Media_Tempo_Esforco'] = df_feature_summary['Tempo_Total_Esforco'] / df_feature_summary['Card_Count']
    df_feature_summary['Texto_Soma_Formatado'] = df_feature_summary['Tempo_Total_Esforco'].apply(format_hours_to_string)
    df_feature_summary['Texto_Media_Formatado'] = df_feature_summary['Media_Tempo_Esforco'].apply(format_hours_to_string)

    # Agrupamento: QA
    df_qa_summary = df.groupby('QA_Responsavel').agg({
        'Card_Count': 'sum',
        'Tempo_QA_Pai': 'sum',
        'Tempo_Rework_Filhos': 'sum',
        'Qtd_Defeitos': 'sum'
    }).reset_index().sort_values('Card_Count', ascending=False)
    
    df_qa_summary['Media_Teste_por_Card'] = df_qa_summary['Tempo_QA_Pai'] / df_qa_summary['Card_Count']
    df_qa_summary['Media_Rework_por_Card'] = df_qa_summary['Tempo_Rework_Filhos'] / df_qa_summary['Card_Count']


    # ==========================================
    # --- 5. RENDERIZAÇÃO: GRID ESTILO KIBANA ---
    # ==========================================
    
    # --- LINHA 1: KPIs Globais ---
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Média Tempo Teste", format_hours_to_string(df['Tempo_QA_Pai'].mean()))
    kpi2.metric("Média Tempo Rework", format_hours_to_string(df['Tempo_Rework_Filhos'].mean()))
    kpi3.metric("Total de Defeitos", int(df['Qtd_Defeitos'].sum()))
    kpi4.metric("Total de Cards", int(df['Card_Count'].sum()))

    st.markdown("<br>", unsafe_allow_html=True)


    # --- LINHA 2: Impacto Média (Teste vs Bug) | Caixas do "Custo da Qualidade" ---
    col_l2_1, col_l2_2 = st.columns(2)
    
    with col_l2_1: 
        with st.container(border=True, height=550):
            st.markdown("<h4 style='text-align: left; color: #FFFFFF; font-size: 1.1rem; margin-bottom: 5px;'>⚖️ Esforço Médio por Card (Teste vs Retrabalho)</h4>", unsafe_allow_html=True)
                        
            df_impact_melt = df_qa_summary.melt(
                id_vars=['QA_Responsavel'], 
                value_vars=['Media_Teste_por_Card', 'Media_Rework_por_Card'],
                var_name='Atividade', 
                value_name='Horas_Medias'
            )
            df_impact_melt['Texto_Formatado'] = df_impact_melt['Horas_Medias'].apply(format_hours_to_string)
            df_impact_melt['Texto_Formatado'] = df_impact_melt.apply(lambda x: "" if x['Horas_Medias'] <= 0.1 else x['Texto_Formatado'], axis=1)

            fig_impact = px.bar(
                df_impact_melt, x='QA_Responsavel', y='Horas_Medias', color='Atividade', barmode='stack',
                text='Texto_Formatado', 
                color_discrete_map={'Media_Teste_por_Card': '#00C2FF', 'Media_Rework_por_Card': '#EF553B'},
                labels={'Horas_Medias': 'Média de Horas', 'QA_Responsavel': 'Analista', 'Atividade': 'Tipo'}
            )
            new_names = {'Media_Teste_por_Card': 'Teste Limpo', 'Media_Rework_por_Card': 'Retrabalho (Espera/Reteste)'}
            fig_impact.for_each_trace(lambda t: t.update(name = new_names.get(t.name, t.name)))
            fig_impact.update_traces(textposition='inside', textfont_color='white')
            fig_impact.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'), margin=dict(t=10, b=10, l=10, r=10), yaxis=dict(showgrid=True, gridcolor='#2B2B40'))
            st.plotly_chart(fig_impact, use_container_width=True)

    with col_l2_2:
        with st.container(border=True, height=550):
            st.markdown("<h4 style='text-align: left; color: #FFFFFF; font-size: 1.1rem; margin-bottom: 5px;'>🎯 Custo da Qualidade</h4>", unsafe_allow_html=True)
            st.markdown("<p style='color: #A0A0B0; font-size: 0.85rem; margin-bottom: 15px;'>Comparativo do custo em horas quando tem cards testados sem encontrar defeitos e quando o defeito é encontrado.</p>", unsafe_allow_html=True)
            
            df_clean = df[df['Possui_Defeito'] == False]
            df_buggy = df[df['Possui_Defeito'] == True]
            media_clean = df_clean['Tempo_Total_Esforco'].mean() if not df_clean.empty else 0
            media_buggy = df_buggy['Tempo_Total_Esforco'].mean() if not df_buggy.empty else 0

            # Adicionando espaçamento extra para alinhar os cards internos com o gráfico ao lado
            st.markdown("<div style='margin-top: 80px;'></div>", unsafe_allow_html=True)

            col_cq1, col_cq2 = st.columns(2)
            with col_cq1:
                with st.container(border=True):
                    st.markdown("<p style='color: #00C2FF; font-size: 0.9rem; font-weight: bold;'>Média: Card s/ Defeito</p>", unsafe_allow_html=True)
                    st.markdown(f"<h2 style='color: white; margin: 0;'>{format_hours_to_string(media_clean)}</h2>", unsafe_allow_html=True)
            with col_cq2:
                with st.container(border=True):
                    st.markdown("<p style='color: #EF553B; font-size: 0.9rem; font-weight: bold;'>Média: Card c/ Defeito</p>", unsafe_allow_html=True)
                    st.markdown(f"<h2 style='color: white; margin: 0;'>{format_hours_to_string(media_buggy)}</h2>", unsafe_allow_html=True)


    # --- LINHA 3: Tempo Médio Gasto por Feature | Pizza de Features ---
    col_l3_1, col_l3_2 = st.columns(2)
    
    with col_l3_1:
        with st.container(border=True): 
            st.markdown("<h4 style='text-align: left; color: #FFFFFF; font-size: 1.1rem; margin-bottom: 10px;'>📊 Tempo Médio Gasto por Feature</h4>", unsafe_allow_html=True)
            
            fig_bar_feat = px.bar(
                df_feature_summary, x='Tag_Agrupada', y='Media_Tempo_Esforco', 
                color='Tag_Agrupada', color_discrete_map=FEATURE_COLORS, 
                text='Texto_Media_Formatado',
                labels={'Media_Tempo_Esforco': 'Média de Esforço (Horas)', 'Tag_Agrupada': 'Feature'}
            )
            fig_bar_feat.update_traces(hovertemplate='<b>%{x}</b><br>Tempo Médio: %{text}', textfont_color='white')
            fig_bar_feat.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'), margin=dict(t=10, b=10, l=10, r=10), showlegend=False, yaxis=dict(showgrid=True, gridcolor='#2B2B40'), xaxis=dict(showgrid=False))
            st.plotly_chart(fig_bar_feat, use_container_width=True)

    with col_l3_2:
        with st.container(border=True):
            st.markdown("<h4 style='text-align: left; color: #FFFFFF; font-size: 1.1rem; margin-bottom: 10px;'>🧩 % de Esforço por Feature</h4>", unsafe_allow_html=True)
            
            fig_pie = px.pie(
                df_feature_summary, names='Tag_Agrupada', values='Tempo_Total_Esforco', 
                hole=0.65, color='Tag_Agrupada', color_discrete_map=FEATURE_COLORS
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label', textfont_color='white')
            fig_pie.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'), margin=dict(t=10, b=10, l=10, r=10), showlegend=False)
            st.plotly_chart(fig_pie, use_container_width=True)


    # --- LINHA 4: Esforço Total por Analista | Volume de Entregas ---
    col_l4_1, col_l4_2 = st.columns(2)
    
    with col_l4_1:
        with st.container(border=True):
            st.markdown("<h4 style='text-align: left; color: #FFFFFF; font-size: 1.1rem; margin-bottom: 10px;'>⏱️ Esforço Total por Analista</h4>", unsafe_allow_html=True)
            
            fig1 = px.bar(
                df, x='QA_Responsavel', y='Tempo_Total_Esforco', color='Tag_Agrupada',
                color_discrete_map=FEATURE_COLORS, 
                labels={'Tempo_Total_Esforco': 'Horas Totais', 'QA_Responsavel': 'Analista', 'Tag_Agrupada': 'Feature'},
                text='Texto_Tempo_Formatado' 
            )
            fig1.update_traces(hovertemplate='<b>%{x}</b><br>Feature: %{data.name}<br>Tempo: %{text}', textposition='inside', textfont_color='white') 
            fig1.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'), margin=dict(t=10, b=10, l=10, r=10), yaxis=dict(showgrid=True, gridcolor='#2B2B40'), xaxis=dict(showgrid=False))
            st.plotly_chart(fig1, use_container_width=True)

    with col_l4_2:
        with st.container(border=True):
            st.markdown("<h4 style='text-align: left; color: #FFFFFF; font-size: 1.1rem; margin-bottom: 10px;'>📦 Volume de Entregas</h4>", unsafe_allow_html=True)
            
            fig_vol = px.bar(
                df_qa_summary, x='QA_Responsavel', y='Card_Count', text='Card_Count', 
                labels={'Card_Count': 'Qtd de Cards', 'QA_Responsavel': 'Analista'}
            )
            fig_vol.update_traces(marker_color='#636EFA', textposition='auto', textfont_color='white') 
            fig_vol.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='white'), margin=dict(t=10, b=10, l=10, r=10), yaxis=dict(showgrid=True, gridcolor='#2B2B40'))
            st.plotly_chart(fig_vol, use_container_width=True)


    # --- LINHA 5: Agente de IA pegando a tela toda ---
    with st.container(border=True):
        st.markdown("<h4 style='text-align: left; color: #FFFFFF; font-size: 1.1rem; margin-bottom: 10px;'>🤖 Analista Técnico (IA)</h4>", unsafe_allow_html=True)
        st.markdown("<p style='color: #A0A0B0; font-size: 0.9rem;'>Gere um relatório de análise dos dados informados no dashboard</p>", unsafe_allow_html=True)
        
        if st.button("Gerar Relatório", use_container_width=True):
            with st.spinner("Analisando dados e gerando relatório..."):
                import json
                dados_para_ia = {
                    "performance_por_qa": df_qa_summary.to_dict(orient='records'),
                    "performance_por_feature": df_feature_summary.to_dict(orient='records')
                }
                crew = QACrew(json.dumps(dados_para_ia))
                result = crew.setup_agents().kickoff()
                st.success("Análise Concluída!")
                st.info(result)

elif st.session_state.data is not None and st.session_state.data.empty:
    st.warning("⚠️ Nenhum dado encontrado. Sincronize o Azure para começar.")