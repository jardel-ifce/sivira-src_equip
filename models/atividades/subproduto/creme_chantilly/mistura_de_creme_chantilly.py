from models.atividade_base import Atividade
from models.equips.batedeira_planetaria import BatedeiraPlanetaria
from enums.tipo_equipamento import TipoEquipamento
from datetime import timedelta
from utils.logger_factory import setup_logger


# 🔥 Logger específico para essa atividade
logger = setup_logger('AtividadeMisturaCremeChantilly')


class MisturaDeCremeChantilly(Atividade):
    """
    🌀 Atividade que representa a mistura de creme chantilly.
    ✔️ Utiliza batedeiras planetárias.
    ✔️ Sempre na velocidade 10.
    ✔️ O gestor faz a ocupação temporal — aqui é apenas configuração operacional.
    """

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.BATEDEIRAS: 1,
        }

    def calcular_duracao(self):
        """
        🕒 Define a duração da atividade conforme a quantidade.
        Faixa oficial:
        - 500–1000g → 10 minutos
        - 1001–2000g → 20 minutos
        - 2001–5000g → 30 minutos
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

    def iniciar(self):
        """
        ⚙️ Configura a batedeira na velocidade correta e inicia o processo lógico.
        ✔️ Não faz ocupação — isso é responsabilidade do gestor.
        """
        if not self.alocada:
            logger.error("❌ Atividade não alocada ainda.")
            raise Exception("❌ Atividade não alocada ainda.")

        batedeira_alocada = None

        equipamentos_ordenados = sorted(
            self.equipamentos_selecionados,
            key=lambda e: self.fips_equipamentos.get(e, 999)
        )

        for equipamento in equipamentos_ordenados:
            if isinstance(equipamento, BatedeiraPlanetaria):
                equipamento.selecionar_velocidade(10)  # ✅ Velocidade fixa
                batedeira_alocada = equipamento
                logger.info(
                    f"🌀 Mistura de creme chantilly iniciada na {equipamento.nome} "
                    f"para {self.quantidade_produto}g na velocidade 10."
                )
                break

        if batedeira_alocada:
            logger.info(
                f"✅ Mistura de creme chantilly realizada na {batedeira_alocada.nome}."
            )
            return True

        logger.error(
            "❌ Não foi possível iniciar a mistura. Nenhuma batedeira disponível."
        )
        raise Exception(
            "❌ Não foi possível iniciar a mistura de creme chantilly."
        )
