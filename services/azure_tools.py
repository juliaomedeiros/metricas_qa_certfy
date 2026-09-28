import os
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from dotenv import load_dotenv
import pandas as pd
from utils.utils_logic import calculate_business_hours, get_segment_tag
from datetime import datetime, timezone 

load_dotenv()

class AzureMiner:
    def __init__(self):
        self.personal_access_token = os.getenv("AZURE_PAT").strip()
        self.organization_url = os.getenv("AZURE_ORG_URL").strip()
        self.credentials = BasicAuthentication('', self.personal_access_token)
        self.connection = Connection(base_url=self.organization_url, creds=self.credentials)
        self.wit_client = self.connection.clients.get_work_item_tracking_client()

    def get_qa_metrics_data(self):
        project = os.getenv("AZURE_PROJECT")
        area_path = os.getenv("AZURE_AREA_PATH")
        qa_relevant_states = "('Pronto para Testes', 'Teste Funcional', 'Aprovação Negócio')"

        wiql_query = f"""
        SELECT [System.Id], [System.Title], [System.State] 
        FROM WorkItems 
        WHERE [System.TeamProject] = '{project}' 
        AND [System.AreaPath] UNDER '{area_path}'
        AND [System.WorkItemType] IN ('User Story', 'Bug', 'Spike')
        AND [System.State] IN {qa_relevant_states}
        """
        
        results = self.wit_client.query_by_wiql(wiql={"query": wiql_query}).work_items
        all_data = []

        if not results:
            return pd.DataFrame()

        for item in results:
            wi = self.wit_client.get_work_item(item.id, expand="all")
            wi_type = wi.fields.get('System.WorkItemType')
            revisions = self.wit_client.get_revisions(item.id)
            
            entrou_no_funil = False
            tempo_qa_total = 0.0
            current_chunk_start = None
            is_bloqueado = False
            
            # --- NOVA LÓGICA DE CRONÔMETRO (Pausa e Despausa) ---
            for rev in revisions:
                state = rev.fields.get('System.State')
                rev_date_str = rev.fields.get('System.ChangedDate')
                rev_date = pd.to_datetime(rev_date_str, utc=True)
                
                # Verifica se a tag 'bloqueado' está presente nesta revisão
                tags_str = rev.fields.get('System.Tags', '') or ''
                tags_list = [t.strip() for t in tags_str.split(';')]
                is_bloqueado = 'Bloqueado' in tags_list

                if state == 'Pronto para Testes':
                    entrou_no_funil = True
                    # Se voltou para cá, o relógio é ZERADO (regra anterior mantida)
                    tempo_qa_total = 0.0
                    current_chunk_start = None

                elif state == 'Teste Funcional':
                    entrou_no_funil = True
                    # REGRA 1: Controle de Bloqueio
                    if not is_bloqueado:
                        # Se não está bloqueado e o relógio está parado, INICIA o relógio
                        if not current_chunk_start:
                            current_chunk_start = rev_date
                    else:
                        # Se ficou bloqueado, PAUSA o relógio e guarda o tempo acumulado
                        if current_chunk_start:
                            tempo_qa_total += calculate_business_hours(current_chunk_start, rev_date)
                            current_chunk_start = None

                elif state in ['Aprovação Negócio']:
                    # PARA O RELÓGIO definitivamente se estava contando
                    if current_chunk_start:
                        tempo_qa_total += calculate_business_hours(current_chunk_start, rev_date)
                        current_chunk_start = None

            if not entrou_no_funil:
                continue

            # Se o card estiver AGORA em Teste Funcional e não estiver bloqueado, calcula até o momento atual
            if current_chunk_start:
                tempo_qa_total += calculate_business_hours(current_chunk_start, datetime.now(timezone.utc))

            # ... (Restante da Lógica de Retrabalho mantida idêntica) ...
            rework_time = 0
            qtd_defeitos = 0
            has_defect = False
            if wi.relations:
                child_ids = [rel.url.split('/')[-1] for rel in wi.relations if rel.attributes.get('name') == 'Child']
                if child_ids:
                    try:
                        children = self.wit_client.get_work_items(ids=child_ids)
                        for child in children:
                            if child.fields.get('System.WorkItemType') == 'Defeito':
                                has_defect = True
                                qtd_defeitos += 1
                                d_start = pd.to_datetime(child.fields.get('System.CreatedDate'), utc=True)
                                raw_end = child.fields.get('Microsoft.VSTS.Common.ClosedDate')
                                d_end = pd.to_datetime(raw_end, utc=True) if raw_end else datetime.now(timezone.utc)
                                rework_time += calculate_business_hours(d_start, d_end)
                    except: pass

                # --- NOVA LÓGICA DE RESPONSÁVEL (TRATAMENTO PARA SPIKE) ---
            if wi_type == 'Spike':
                # Para Spikes, usamos o AssignedTo
                assigned_to_field = wi.fields.get('System.AssignedTo')
                qa_name = assigned_to_field.get('displayName') if isinstance(assigned_to_field, dict) else (assigned_to_field or "Não Atribuído")
            else:
                # Para User Story e Bug, usamos o Tested By
                tested_by_field = wi.fields.get('Tested By') or wi.fields.get('Custom.TestedBy')
                qa_name = tested_by_field.get('displayName') if isinstance(tested_by_field, dict) else (tested_by_field or "Não Atribuído")

            all_data.append({
                'ID': item.id,
                'Tipo_Card': wi_type,
                'Titulo': wi.fields.get('System.Title'),
                'QA_Responsavel': qa_name,
                # Passa o tipo do card para o agrupador
                'Tag_Agrupada': get_segment_tag(wi.fields.get('System.Tags', ''), wi_type),
                'Tempo_QA_Pai': tempo_qa_total, # Agora usa o tempo acumulado com pausas
                'Tempo_Rework_Filhos': rework_time,
                'Qtd_Defeitos': qtd_defeitos,
                'Possui_Defeito': has_defect,
                'Card_Count': 1
            })
            
        return pd.DataFrame(all_data)