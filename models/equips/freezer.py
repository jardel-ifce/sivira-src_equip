from models.equips.equipamento import Equipamento
from enums.tipo_setor import TipoSetor
from enums.tipo_equipamento import TipoEquipamento
from typing import List, Tuple, Optional
from datetime import datetime
from utils.logger_factory import setup_logger

logger = setup_logger('Freezer')


class Freezer(Equipamento):
    """
    ❄️ Representa um Freezer com controle de ocupação exclusivamente por caixas de 30kg,
    considerando períodos de tempo e controle de temperatura.
    """

    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        capacidade_caixa_30kg: int,
        faixa_temperatura_min: int,
        faixa_temperatura_max: int
    ):
        super().__init__(
            id=id,
            nome=nome,
            tipo_equipamento=TipoEquipamento.REFRIGERACAO_CONGELAMENTO,
            setor=setor,
            numero_operadores=0,
            status_ativo=True
        )

        self.capacidade_caixa_30kg = capacidade_caixa_30kg
        self.ocupacao_caixas: List[Tuple[int, datetime, datetime, Optional[int]]] = []  # (quantidade, inicio, fim, ordem_id)
        self.ocupacoes: List[Tuple[Optional[int], int, int, datetime, datetime, Optional[int]]] = []  # (ordem_id, atividade_id, quantidade, inicio, fim, temperatura)

        self.faixa_temperatura_min = faixa_temperatura_min
        self.faixa_temperatura_max = faixa_temperatura_max
        self.faixa_temperatura_atual = None

    # ==========================================================
    # 🌡️ Controle de Temperatura
    # ==========================================================
    def verificar_compatibilidade_de_temperatura(
        self,
        inicio: datetime,
        fim: datetime,
        temperatura_desejada: int
    ) -> bool:
        conflitos = [
            temp for (_, _, _, ini, f, temp) in self.ocupacoes
            if not (fim <= ini or inicio >= f)
        ]
        return all(temp == temperatura_desejada for temp in conflitos) if conflitos else True

    def selecionar_faixa_temperatura(self, temperatura_desejada: int) -> bool:
        if self.faixa_temperatura_atual == temperatura_desejada and self.faixa_temperatura_atual is not None:
            return True

        ocupacoes_ativas = [
            (qtd, ini, fim, _) for (qtd, ini, fim, _) in self.ocupacao_caixas
            if ini <= datetime.now() <= fim
        ]

        if ocupacoes_ativas:
            logger.warning(
                f"⚠️ Não é possível ajustar a temperatura do {self.nome} para {temperatura_desejada}°C. "
                f"Temperatura atual: {self.faixa_temperatura_atual}°C, há ocupações ativas."
            )
            return False

        self.faixa_temperatura_atual = temperatura_desejada
        logger.info(
            f"🌡️ Freezer {self.nome} estava vazio. Temperatura ajustada para {temperatura_desejada}°C."
        )
        return True

    # ==========================================================
    # 📦 Ocupação por Caixas
    # ==========================================================
    def verificar_espaco_caixas(self, quantidade_caixas: int, inicio: datetime, fim: datetime) -> bool:
        ocupadas = sum(
            qtd for (qtd, ini, f, _) in self.ocupacao_caixas
            if not (fim <= ini or inicio >= f)
        )
        return (ocupadas + quantidade_caixas) <= self.capacidade_caixa_30kg

    def ocupar_caixas(
        self,
        ordem_id: Optional[int],
        atividade_id: int,
        quantidade: int,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        if not self.verificar_espaco_caixas(quantidade, inicio, fim):
            return False

        self.ocupacao_caixas.append((quantidade, inicio, fim, ordem_id))
        self.ocupacoes.append((ordem_id, atividade_id, quantidade, inicio, fim, self.faixa_temperatura_atual))

        logger.info(
            f"📦 {self.nome} alocado para Atividade {atividade_id} | Ordem {ordem_id} "
            f"| Caixas: {quantidade} | {inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')} "
            f"| Temperatura: {self.faixa_temperatura_atual}°C"
        )
        return True

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade_id: int, ordem_id: Optional[int] = None):
        self.ocupacoes = [
            (oid, aid, qtd, ini, fim, temp)
            for (oid, aid, qtd, ini, fim, temp) in self.ocupacoes
            if not (aid == atividade_id and (ordem_id is None or oid == ordem_id))
        ]
        self.ocupacao_caixas = [
            (qtd, ini, fim, oid)
            for (qtd, ini, fim, oid) in self.ocupacao_caixas
            if not (oid == ordem_id and any(aid == atividade_id and oid == ordem_id for (_, aid, _, ini2, fim2, _) in self.ocupacoes))
        ]

    def liberar_por_ordem(self, ordem_id: int):
        self.ocupacoes = [
            (oid, aid, qtd, ini, fim, temp)
            for (oid, aid, qtd, ini, fim, temp) in self.ocupacoes
            if oid != ordem_id
        ]
        self.ocupacao_caixas = [
            (qtd, ini, fim, oid)
            for (qtd, ini, fim, oid) in self.ocupacao_caixas
            if oid != ordem_id
        ]

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        self.ocupacoes = [
            (oid, aid, qtd, ini, fim, temp)
            for (oid, aid, qtd, ini, fim, temp) in self.ocupacoes if fim > horario_atual
        ]
        self.ocupacao_caixas = [
            (qtd, ini, fim, oid)
            for (qtd, ini, fim, oid) in self.ocupacao_caixas if fim > horario_atual
        ]

    def liberar_todas_ocupacoes(self):
        self.ocupacoes.clear()
        self.ocupacao_caixas.clear()

    def liberar_intervalo(self, inicio: datetime, fim: datetime):
        self.ocupacoes = [
            (oid, aid, qtd, ini, f, temp)
            for (oid, aid, qtd, ini, f, temp) in self.ocupacoes
            if not (ini >= inicio and f <= fim)
        ]
        self.ocupacao_caixas = [
            (qtd, ini, f, oid)
            for (qtd, ini, f, oid) in self.ocupacao_caixas
            if not (ini >= inicio and f <= fim)
        ]

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info(f"📅 Agenda do {self.nome}")
        logger.info("==============================================")

        if not self.ocupacoes:
            logger.info("🔹 Nenhuma ocupação registrada.")
            return

        for (ordem_id, atividade_id, quantidade, inicio, fim, temp) in self.ocupacoes:
            logger.info(
                f"📦 Ordem {ordem_id} | Atividade {atividade_id} | Caixas: {quantidade} | "
                f"{inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')} | Temp: {temp}°C"
            )

