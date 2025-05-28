from models.equips.equipamento import Equipamento
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_setor import TipoSetor
from enums.tipo_atividade import TipoAtividade
from datetime import datetime
from typing import List, Tuple
from utils.logger_factory import setup_logger


# 🔥 Logger exclusivo para a Batedeira Industrial
logger = setup_logger('BatedeiraIndustrial')


class BatedeiraIndustrial(Equipamento):
    """
    🏭 Classe que representa uma Batedeira Industrial.
    ✔️ Controle de velocidade (mínima e máxima).
    ✔️ Validação de capacidade por peso (mínimo e máximo).
    ✔️ Ocupação temporal (não permite sobreposição).
    ✔️ Logs completos de uso, liberações e erros operacionais.
    """

    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        numero_operadores: int,
        capacidade_gramas_min: float,
        capacidade_gramas_max: float,
        velocidade_min: int,
        velocidade_max: int,
    ):
        super().__init__(
            id=id,
            nome=nome,
            setor=setor,
            tipo_equipamento=TipoEquipamento.BATEDEIRAS,
            numero_operadores=numero_operadores,
            status_ativo=True,
        )

        self.capacidade_gramas_min = capacidade_gramas_min
        self.capacidade_gramas_max = capacidade_gramas_max
        self.velocidade_min = velocidade_min
        self.velocidade_max = velocidade_max
        self.velocidade_atual = 0

        self.ocupacoes: List[Tuple[float, datetime, datetime, int]] = []

    # ==========================================================
    # 🚦 Validação
    # ==========================================================
    def esta_disponivel(self, inicio: datetime, fim: datetime) -> bool:
        for _, ocup_inicio, ocup_fim, _ in self.ocupacoes:
            if not (fim <= ocup_inicio or inicio >= ocup_fim):
                return False
        return True

    def validar_capacidade(self, quantidade_gramas: float) -> bool:
        return self.capacidade_gramas_min <= quantidade_gramas <= self.capacidade_gramas_max

    def selecionar_velocidade(self, velocidade: int) -> bool:
        if self.velocidade_min <= velocidade <= self.velocidade_max:
            self.velocidade_atual = velocidade
            logger.info(
                f"⚙️ {self.nome} | Velocidade ajustada para {velocidade}."
            )
            return True

        logger.error(
            f"❌ Velocidade {velocidade} fora dos limites permitidos para {self.nome}. "
            f"Faixa: {self.velocidade_min} a {self.velocidade_max}."
        )
        return False

    # ==========================================================
    # 🏗️ Ocupação
    # ==========================================================
    def ocupar(self, quantidade_gramas: float, inicio: datetime, fim: datetime, atividade_id: int) -> bool:
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
            f"🏭 {self.nome} | Ocupada com {quantidade_gramas}g "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} "
            f"para atividade {atividade_id} na velocidade {self.velocidade_atual}."
        )
        return True

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar(self, inicio: datetime, fim: datetime, atividade_id: int):
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
    # 🔍 Consulta
    # ==========================================================
    def obter_ocupacoes_ativas(self, horario_atual: datetime) -> List[Tuple[float, datetime, datetime, int]]:
        return [
            (qtd, ini, fim, atv_id)
            for (qtd, ini, fim, atv_id) in self.ocupacoes
            if ini <= horario_atual < fim
        ]

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        print(f"\n============================")
        print(f"📅 Agenda da Batedeira {self.nome}")
        print(f"============================")
        if not self.ocupacoes:
            print("🔹 Nenhuma ocupação registrada.")
            return
        for i, (qtd, ini, fim, atv_id) in enumerate(self.ocupacoes, start=1):
            print(
                f"🔸 Ocupação {i}: {qtd}g | "
                f"Início: {ini.strftime('%H:%M')} | Fim: {fim.strftime('%H:%M')} | "
                f"Atividade ID: {atv_id} | Velocidade: {self.velocidade_atual}"
            )
