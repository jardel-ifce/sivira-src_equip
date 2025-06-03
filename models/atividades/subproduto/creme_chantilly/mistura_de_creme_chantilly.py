from models.atividade_base import Atividade
from models.equips.batedeira_planetaria import BatedeiraPlanetaria
from enums.tipo_equipamento import TipoEquipamento
from datetime import timedelta, datetime
from utils.logger_factory import setup_logger

# 🌀 Logger específico para essa atividade
logger = setup_logger('AtividadeMisturaCremeChantilly')


class MisturaDeCremeChantilly(Atividade):
    """
    🌀 Atividade que representa a mistura de creme chantilly.
    ✔️ Utiliza batedeiras planetárias.
    ✔️ Sempre na velocidade 10.
    ✔️ Ocupação feita via backward scheduling com gestor.
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
        """
        📏 Define a duração com base na faixa de quantidade.
        """
        q = self.quantidade_produto

        if 500 <= q <= 1000:
            self.duracao = timedelta(minutes=10)
        elif 1001 <= q <= 2000:
            self.duracao = timedelta(minutes=20)
        elif 2001 <= q <= 5000:
            self.duracao = timedelta(minutes=30)
        else:
            logger.error(
                f"❌ Quantidade {q} fora das faixas válidas para MISTURA DE CREME CHANTILLY."
            )
            raise ValueError(
                f"❌ Quantidade {q} fora das faixas válidas para MISTURA DE CREME CHANTILLY."
            )

        logger.info(
            f"🕒 Duração calculada: {self.duracao} para {q}g de creme chantilly."
        )

    def tentar_alocar_e_iniciar(
        self,
        gestor_batedeiras,
        inicio_jornada: datetime,
        fim_jornada: datetime
    ) -> bool:
        """
        🧠 Executa backward scheduling e tenta alocar uma batedeira disponível.
        """
        self.calcular_duracao()

        logger.info(
            f"🚀 Tentando alocar mistura ID {self.id} ({self.quantidade_produto}g) "
            f"entre {inicio_jornada.strftime('%H:%M')} e {fim_jornada.strftime('%H:%M')}."
        )

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

            logger.warning(
                f"⚠️ Falha na alocação da atividade {self.id} entre "
                f"{horario_inicio_tentativa.strftime('%H:%M')} e {horario_final_tentativa.strftime('%H:%M')}. "
                f"Retrocedendo..."
            )
            horario_final_tentativa -= timedelta(minutes=5)

        logger.error(
            f"❌ Não foi possível alocar a mistura {self.id} dentro da janela definida."
        )
        return False

    def _registrar_sucesso(self, batedeira: BatedeiraPlanetaria, inicio: datetime, fim: datetime):
        """
        ✅ Registra a alocação bem-sucedida da batedeira.
        """
        self.inicio_real = inicio
        self.fim_real = fim
        self.batedeira_alocada = batedeira
        self.equipamento_alocado = batedeira
        self.equipamentos_selecionados = [batedeira]
        self.alocada = True

        logger.info(
            f"✅ Atividade {self.id} alocada com sucesso na {batedeira.nome}.\n"
            f"🌀 Período: {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}"
        )
        print(
            f"✅ Mistura de creme chantilly alocada na {batedeira.nome} "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
        )

    def iniciar(self):
        """
        🟢 Inicia oficialmente a atividade de mistura.
        """
        if not self.alocada or not self.batedeira_alocada:
            logger.error("❌ Atividade não alocada. Impossível iniciar.")
            raise Exception("❌ Atividade de mistura não alocada.")

        sucesso = self.batedeira_alocada.selecionar_velocidade(10)

        if not sucesso:
            raise Exception(
                f"❌ Falha ao configurar velocidade da batedeira {self.batedeira_alocada.nome}."
            )

        logger.info(
            f"🚀 Atividade {self.id} iniciada na {self.batedeira_alocada.nome} "
            f"de {self.inicio_real.strftime('%H:%M')} até {self.fim_real.strftime('%H:%M')}."
        )
        print(
            f"🚀 Mistura de creme chantilly iniciada na {self.batedeira_alocada.nome} "
            f"de {self.inicio_real.strftime('%H:%M')} até {self.fim_real.strftime('%H:%M')}."
        )
