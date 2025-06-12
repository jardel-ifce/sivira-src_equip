# src/utils/data_utils.py

from datetime import datetime, timedelta, time
from enums.dia_semana import DiaSemana

mapa_dia_semana = {
    "Segunda-feira": 0,
    "Terça-feira": 1,
    "Quarta-feira": 2,
    "Quinta-feira": 3,
    "Sexta-feira": 4,   
    "Sábado": 5,
    "Domingo": 6
}

DIAS_SEMANA_PT = {
    "Monday": "Segunda-feira",
    "Tuesday": "Terça-feira",
    "Wednesday": "Quarta-feira",
    "Thursday": "Quinta-feira",
    "Friday": "Sexta-feira",
    "Saturday": "Sábado",
    "Sunday": "Domingo"
}

def proxima_data_para_dia_semana(dia_semana: DiaSemana) -> datetime:
    hoje = datetime.today()
    dias_a_adicionar = (mapa_dia_semana[dia_semana.value] - hoje.weekday()) % 7
    return hoje.replace(hour=8, minute=0, second=0, microsecond=0) + timedelta(days=dias_a_adicionar)


def formatar_data_e_hora(data: datetime) -> tuple[str, str, str]:
    dia_semana_pt = DIAS_SEMANA_PT[data.strftime("%A")]
    data_formatada = data.strftime("%d/%m/%Y")
    hora_formatada = data.strftime("%H:%M")
    return dia_semana_pt, data_formatada, hora_formatada

def formatar_hora_e_min(data: time) -> tuple[str, str]:
    hora_formatada = data.strftime("%H:%M")
    return hora_formatada

# def dias_em_ordem_ciclica_a_partir(dia_referencia: DiaSemana) -> list[DiaSemana]:
#     todos = list(DiaSemana)
#     i = todos.index(dia_referencia)
#     return todos[i:] + todos[:i]

def ordem_dias(self, dia: DiaSemana):
        ORDENACAO_DIAS = [
            DiaSemana.SEGUNDA,
            DiaSemana.TERCA,
            DiaSemana.QUARTA,
            DiaSemana.QUINTA,
            DiaSemana.SEXTA,
            DiaSemana.SABADO,
            DiaSemana.DOMINGO,
        ]
        try:
            return ORDENACAO_DIAS.index(dia)
        except ValueError:
            raise ValueError(f"O dia {dia} não é válido, deve ser um dos seguintes: {ORDENACAO_DIAS}")