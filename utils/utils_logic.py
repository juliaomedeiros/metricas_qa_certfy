import pandas as pd
import pytz
from datetime import datetime, time

# Configurações fixas para sua regra de negócio
BR_TZ = pytz.timezone('America/Sao_Paulo')
BUSINESS_START = time(8, 0)
BUSINESS_END = time(18, 0)

def calculate_business_hours(start_dt, end_dt):
    """
    Calcula a duração exata em horas úteis entre duas datas.
    Respeita Fuso Horário BR e intervalo 08:00-18:00.
    """
    if not start_dt or not end_dt:
        return 0.0

    # 1. Garante que tudo esteja com Fuso Horário (Timezone Aware)
    try:
        # Se vier sem fuso (UTC do Azure), converte para Brasília
        if start_dt.tzinfo is None:
            start_dt = pytz.utc.localize(start_dt)
        if end_dt.tzinfo is None:
            end_dt = pytz.utc.localize(end_dt)
            
        # Converte ambos para a hora local do Brasil para verificar se é feriado/fds/noite corretamente
        s = start_dt.astimezone(BR_TZ)
        e = end_dt.astimezone(BR_TZ)
    except Exception:
        return 0.0

    if s >= e:
        return 0.0

    # 2. Cálculo preciso dia a dia
    total_seconds = 0.0
    current_date = s.date()
    end_date_limit = e.date()

    while current_date <= end_date_limit:
        # Pula Sábado (5) e Domingo (6)
        if current_date.weekday() < 5:
            # Define limites do dia comercial
            day_open = BR_TZ.localize(datetime.combine(current_date, BUSINESS_START))
            day_close = BR_TZ.localize(datetime.combine(current_date, BUSINESS_END))

            # Intersecção: O que aconteceu dentro do horário comercial?
            actual_start = max(day_open, s)
            actual_end = min(day_close, e)

            if actual_start < actual_end:
                total_seconds += (actual_end - actual_start).total_seconds()

        # Avança para o próximo dia
        current_date = pd.Timedelta(days=1) + current_date

    # Retorna horas com 1 casa decimal (ex: 2.5 horas)
    return round(total_seconds / 3600, 1)

def get_segment_tag(tags_string, work_item_type=None):
    """Agrupa por categorias e força Análises Técnicas se for Spike."""
    # 1. Nova regra: Se for Spike, a feature é Análises Técnicas automaticamente
    if work_item_type == 'Spike':
        return "Análises Técnicas"

    
    valid_tags = ['captura biografica', 'captura de face', 'captura de digitais', 'captura de assinatura', 'analises tecnicas', 'admin frontend', 'admin api', 'atendimento frontend']
    if not tags_string or not isinstance(tags_string, str): 
        return "Outros"
    
    tags_list = [t.strip().lower() for t in tags_string.split(';')]
    for tag in valid_tags:
        if tag in tags_list:
            if tag == 'analises tecnicas': return "Análises Técnicas"
            if tag == 'admin frontend': return "Admin FrontEnd"
            if tag == 'admin api': return "Admin API"
            if tag == 'atendimento frontend': return "Atendimento FrontEnd"
            return tag
    return "Outros"

# Adicione no final do arquivo utils/utils_logic.py

def format_hours_to_string(decimal_hours):
    """Converte horas em float (ex: 10.8) para formato de relógio (ex: '10h 48m')."""
    if pd.isna(decimal_hours) or decimal_hours == 0:
        return "0h 0m"
    
    hours = int(decimal_hours)
    # Pega a parte decimal (ex: 0.8), multiplica por 60 e arredonda
    minutes = int(round((decimal_hours - hours) * 60))
    
    if minutes == 60:
        hours += 1
        minutes = 0
        
    return f"{hours}h {minutes}m"