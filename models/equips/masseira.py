from models.equips.equipamento import Equipamento
from enums.velocidade import Velocidade
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_mistura import TipoMistura
from enums.tipo_setor import TipoSetor
from datetime import datetime
from typing import List, Tuple
from utils.logger_factory import setup_logger


# 🔥 Logger específico da Masseira
logger = setup_logger('Masseira')


class Masseira(Equipamento):
    """
    🌀 Classe que representa uma Masseira (Misturadora).
    ✔️ Controle temporal e de capacidade (mínima e máxima).
    ✔️ Ocupação exclusiva por janela de tempo.
    """

    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        capacidade_gramas_max: int,
        capacidade_gramas_min: int,
        ritmo_execucao: TipoMistura,
        velocidades_suportadas: List[Velocidade],
    ):
        super().__init__(
            id=id,
            nome=nome,
            setor=setor,
            tipo_equipamento=TipoEquipamento.MISTURADORAS,
            numero_operadores=1,
            status_ativo=True,
        )

        self.capacidade_gramas_max = capacidade_gramas_max
        self.capacidade_gramas_min = capacidade_gramas_min
        self.ritmo_execucao = ritmo_execucao
        self.velocidades_suportadas = velocidades_suportadas

        # Ocupações: (quantidade, início, fim, atividade_id)
        self.ocupacoes: List[Tuple[float, datetime, datetime, int]] = []

    # ==========================================================
    # 🚦 Validação de Disponibilidade
    # ==========================================================
    def esta_disponivel(self, inicio: datetime, fim: datetime) -> bool:
        """
        Verifica se está disponível no intervalo (sem sobreposição).
        """
        for _, ocup_inicio, ocup_fim, _ in self.ocupacoes:
            if not (fim <= ocup_inicio or inicio >= ocup_fim):
                return False
        return True

    def validar_capacidade(self, quantidade_gramas: float) -> bool:
        """
        Verifica se a quantidade está dentro dos limites da masseira.
        """
        return self.capacidade_gramas_min <= quantidade_gramas <= self.capacidade_gramas_max

    # ==========================================================
    # 🏗️ Ocupação
    # ==========================================================
    def ocupar(
        self,
        quantidade_gramas: float,
        inicio: datetime,
        fim: datetime,
        atividade_id: int
    ) -> bool:
        """
        Ocupa a masseira no intervalo, se disponível e com quantidade válida.
        """
        if not self.validar_capacidade(quantidade_gramas):
            logger.error(
                f"❌ {self.nome} | {quantidade_gramas}g fora dos limites "
                f"({self.capacidade_gramas_min}g - {self.capacidade_gramas_max}g)."
            )
            return False

        if not self.esta_disponivel(inicio, fim):
            logger.warning(
                f"❌ {self.nome} | Ocupada de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
            )
            return False

        self.ocupacoes.append((quantidade_gramas, inicio, fim, atividade_id))
        logger.info(
            f"🌀 {self.nome} | Ocupada com {quantidade_gramas}g "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} "
            f"para atividade {atividade_id}."
        )
        return True

    # ==========================================================
    # 🔓 Liberação de Ocupações
    # ==========================================================
    def liberar(
        self, inicio: datetime, fim: datetime, atividade_id: int
    ):
        """
        Libera uma ocupação específica.
        """
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            (qtd, ini, f, atv_id)
            for (qtd, ini, f, atv_id) in self.ocupacoes
            if not (ini == inicio and f == fim and atv_id == atividade_id)
        ]
        depois = len(self.ocupacoes)
        if antes != depois:
            logger.info(
                f"🟩 {self.nome} | Liberação efetuada da atividade {atividade_id} "
                f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
            )

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        """
        Libera automaticamente as ocupações finalizadas.
        """
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            (qtd, ini, fim, atv_id)
            for (qtd, ini, fim, atv_id) in self.ocupacoes
            if fim > horario_atual
        ]
        liberadas = antes - len(self.ocupacoes)
        if liberadas > 0:
            logger.info(
                f"🟩 {self.nome} | Liberou {liberadas} ocupações finalizadas até {horario_atual.strftime('%H:%M')}."
            )

    # ==========================================================
    # 🔍 Consulta de Ocupações
    # ==========================================================
    def obter_ocupacoes_ativas(
        self, horario_atual: datetime
    ) -> List[Tuple[float, datetime, datetime, int]]:
        """
        Retorna todas as ocupações ativas no momento.
        """
        return [
            (qtd, ini, fim, atv_id)
            for (qtd, ini, fim, atv_id) in self.ocupacoes
            if ini <= horario_atual < fim
        ]

    # ==========================================================
    # 📅 Visualização de Agenda
    # ==========================================================
    def mostrar_agenda(self):
        """
        Exibe a agenda da masseira.
        """
        print(f"\n============================")
        print(f"📅 Agenda da Masseira {self.nome}")
        print(f"============================")
        if not self.ocupacoes:
            print("🔹 Nenhuma ocupação registrada.")
            return
        for i, (qtd, ini, fim, atv_id) in enumerate(self.ocupacoes, start=1):
            print(
                f"🔸 Ocupação {i}: {qtd}g | "
                f"Início: {ini.strftime('%H:%M')} | Fim: {fim.strftime('%H:%M')} | Atividade ID: {atv_id}"
            )

    # ==========================================================
    # 🔄 Reset Geral
    # ==========================================================
    def resetar(self):
        """
        Reset total da masseira.
        """
        self.ocupacoes.clear()
        logger.info(f"🔄 {self.nome} | Resetada completamente.")

    # ==========================================================
    # 🔍 Visualização e Status
    # ==========================================================
    def __str__(self):
        velocidades = ', '.join(v.name for v in self.velocidades_suportadas)
        return (
            super().__str__() +
            f"\n📦 Capacidade Máxima: {self.capacidade_gramas_max}g"
            f"\n📦 Capacidade Mínima: {self.capacidade_gramas_min}g"
            f"\n🌀 Ritmo de Execução: {self.ritmo_execucao.name}"
            f"\n⚙️ Velocidades Suportadas: {velocidades}"
        )
