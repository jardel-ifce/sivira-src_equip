from models.atividade_base import Atividade
from datetime import timedelta, datetime
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger

# 🔥 Logger específico para esta atividade
logger = setup_logger('AtividadeArmazenamentoMassaDeBoloBranco')


class ArmazenamentoSobTemperaturaParaMassaDeBoloBranco(Atividade):
    """
    🎂 Atividade de armazenamento da massa de bolo branco em câmara refrigerada a 4°C.
    ✅ Ocupação por níveis de tela (1000g = 1 nível).
    ✅ Conversão feita pela própria câmara.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tipo_ocupacao = "NIVEIS_TELA"

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.REFRIGERACAO_CONGELAMENTO: 1,
        }

    def calcular_duracao(self):
        q = self.quantidade_produto
        if 3000 <= q <= 6000:
            self.duracao = timedelta(minutes=3)
        elif 6001 <= q <= 13000:
            self.duracao = timedelta(minutes=5)
        elif 13001 <= q <= 20000:
            self.duracao = timedelta(minutes=7)
        else:
            logger.error(f"❌ Quantidade {q} fora das faixas válidas.")
            raise ValueError(f"❌ Quantidade {q} fora das faixas válidas.")
        logger.info(f"🕒 Duração calculada: {self.duracao} para {q}g.")

    def tentar_alocar_e_iniciar(self, gestor_refrigeracao, inicio_jornada, fim_jornada, temperatura_desejada=4):
        self.calcular_duracao()
        logger.info(f"🚀 Tentando alocar atividade {self.id} ({self.quantidade_produto}g).")
        horario_final_tentativa = fim_jornada

        while horario_final_tentativa - self.duracao >= inicio_jornada:
            horario_inicio_tentativa = horario_final_tentativa - self.duracao
            status, equipamento, inicio_real, fim_real = gestor_refrigeracao.alocar(
                inicio=horario_inicio_tentativa,
                fim=horario_final_tentativa,
                atividade=self,
                temperatura_desejada=temperatura_desejada
            )
            if status == "SUCESSO":
                self._registrar_sucesso(equipamento, inicio_real, fim_real)
                return True
            horario_final_tentativa -= timedelta(minutes=1)

        logger.error(f"❌ Falha ao alocar atividade {self.id}.")
        return False

    def _registrar_sucesso(self, equipamento, inicio, fim):
        self.inicio_real = inicio
        self.fim_real = fim
        self.equipamento_alocado = equipamento
        self.equipamentos_selecionados = [equipamento]
        self.alocada = True
        logger.info(f"✅ Atividade {self.id} alocada na {equipamento.nome} das {inicio.strftime('%H:%M')} às {fim.strftime('%H:%M')}.")

    def iniciar(self):
        if not self.alocada:
            logger.error(f"❌ Atividade {self.id} não alocada.")
            raise Exception("❌ Atividade não alocada.")
        logger.info(f"🚀 Iniciada na {self.equipamento_alocado.nome} das {self.inicio_real.strftime('%H:%M')} às {self.fim_real.strftime('%H:%M')}.")
