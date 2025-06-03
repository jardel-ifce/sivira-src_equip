from datetime import timedelta, datetime
from models.atividade_base import Atividade
from models.equips.batedeira_industrial import BatedeiraIndustrial
from models.equips.batedeira_planetaria import BatedeiraPlanetaria
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger

# 🔥 Logger específico para essa atividade
logger = setup_logger('AtividadeMisturaMassaBoloBranco')


class MisturaDeMassaParaBoloBranco(Atividade):
    """
    🌀 Mistura de massas para bolo branco.
    ✔️ Utiliza batedeiras industriais ou planetárias.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tipo_ocupacao = "EXCLUSIVA"
        self.batedeira_alocada = None

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.BATEDEIRAS: 1,
        }

    def calcular_duracao(self):
        q = self.quantidade_produto
        if 3000 <= q <= 6000:
            self.duracao = timedelta(minutes=5)
        elif 6001 <= q <= 13000:
            self.duracao = timedelta(minutes=7)
        elif 13001 <= q <= 20000:
            self.duracao = timedelta(minutes=9)
        else:
            logger.error(f"❌ Quantidade {q} fora das faixas válidas.")
            raise ValueError(f"❌ Quantidade {q} fora das faixas válidas.")
        logger.info(f"🕒 Duração calculada: {self.duracao} para {q}g.")

    def tentar_alocar_e_iniciar(self, gestor_batedeiras, inicio_jornada, fim_jornada):
        self.calcular_duracao()
        logger.info(f"🚀 Tentando alocar mistura ID {self.id} ({self.quantidade_produto}g).")
        horario_final_tentativa = fim_jornada

        while horario_final_tentativa - self.duracao >= inicio_jornada:
            horario_inicio_tentativa = horario_final_tentativa - self.duracao
            sucesso, batedeira, inicio_real, fim_real = gestor_batedeiras.alocar(
                inicio=horario_inicio_tentativa,
                fim=horario_final_tentativa,
                atividade=self,
                quantidade=self.quantidade_produto
            )

            if sucesso:
                self._registrar_sucesso(batedeira, inicio_real, fim_real)
                return True

            horario_final_tentativa -= timedelta(minutes=5)

        logger.error(f"❌ Não foi possível alocar a mistura {self.id}.")
        return False

    def _registrar_sucesso(self, batedeira, inicio, fim):
        self.inicio_real = inicio
        self.fim_real = fim
        self.batedeira_alocada = batedeira
        self.equipamento_alocado = batedeira
        self.equipamentos_selecionados = [batedeira]
        self.alocada = True
        logger.info(f"✅ Mistura {self.id} alocada na {batedeira.nome} das {inicio.strftime('%H:%M')} às {fim.strftime('%H:%M')}.")

    def iniciar(self):
        if not self.alocada or not self.batedeira_alocada:
            logger.error("❌ Atividade não alocada.")
            raise Exception("❌ Atividade não alocada.")
        sucesso = self.batedeira_alocada.selecionar_velocidade(5)
        if not sucesso:
            raise Exception(f"❌ Falha ao configurar velocidade da batedeira {self.batedeira_alocada.nome}.")
        logger.info(f"🚀 Mistura iniciada na {self.batedeira_alocada.nome} das {self.inicio_real.strftime('%H:%M')} às {self.fim_real.strftime('%H:%M')}.")
