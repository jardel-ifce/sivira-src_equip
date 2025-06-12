from datetime import date, datetime
from enums.tipo_folga import TipoFolga
from utils.data_utils import mapa_dia_semana
from enums.dia_semana import DiaSemana
import calendar

class RegraFolga:
    def __init__(self, tipo: TipoFolga, dia_semana=None, dia_mes=None, n_ocorrencia=None):
        self.tipo = tipo
        self.dia_semana = dia_semana
        self.dia_mes = dia_mes
        self.n_ocorrencia = n_ocorrencia

    def verifica(self, data) -> bool:
        # 🔁 Compatibiliza tanto datetime quanto date
        if isinstance(data, datetime):
            data = data.date()
        if self.tipo == TipoFolga.DIA_FIXO_SEMANA:
            return data.weekday() == mapa_dia_semana[self.dia_semana.value]
        elif self.tipo == TipoFolga.DIA_FIXO_MES:
            return data.day == self.dia_mes
        elif self.tipo == TipoFolga.N_DIA_SEMANA_DO_MES:
            return self._verifica_ocorrencia(data)
        return False
    
    def _verifica_ocorrencia(self, data: datetime) -> bool:
        """Verifica se a data corresponde ao 'n-ésimo' dia da semana no mês."""
        # Verifica se o dia da semana da data corresponde ao desejado
        if data.weekday() != mapa_dia_semana[self.dia_semana.value]:
            return False
        
        # Conta quantas vezes o dia da semana ocorre no mês
        dia = 1
        ocorrencia = 0
        while True:
            try:
                d = date(data.year, data.month, dia)
                if d.weekday() == mapa_dia_semana[self.dia_semana.value]:
                    ocorrencia += 1
                    if d == data:
                        return ocorrencia == self.n_ocorrencia
                dia += 1
            except ValueError:
                break
        return False