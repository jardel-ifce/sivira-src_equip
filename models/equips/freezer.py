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
        self.ocupacao_caixas: List[Tuple[int, datetime, datetime]] = []

        self.faixa_temperatura_min = faixa_temperatura_min
        self.faixa_temperatura_max = faixa_temperatura_max
        self.faixa_temperatura_atual = None

        # Histórico: (atividade_id, quantidade, inicio, fim, temperatura)
        self.historico_temperatura: List[Tuple[int, int, datetime, datetime, Optional[int]]] = []

    # ==========================================================
    # 🌡️ Controle de Temperatura
    # ==========================================================
    def registrar_temperatura(self, atividade_id: int, quantidade: int, inicio: datetime, fim: datetime):
        self.historico_temperatura.append((atividade_id, quantidade, inicio, fim, self.faixa_temperatura_atual))
        logger.info(
            f"🌡️ Temperatura {self.faixa_temperatura_atual}°C registrada para Atividade {atividade_id} "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} no {self.nome}."
        )

    def verificar_compatibilidade_de_temperatura(
        self,
        inicio: datetime,
        fim: datetime,
        temperatura_desejada: int
    ) -> bool:
        conflitos = [
            temp for (_, _, ini, f, temp) in self.historico_temperatura
            if not (fim <= ini or inicio >= f)
        ]
        return all(temp == temperatura_desejada for temp in conflitos) if conflitos else True

    def selecionar_faixa_temperatura(self, temperatura_desejada: int) -> bool:
        if self.faixa_temperatura_atual == temperatura_desejada and self.faixa_temperatura_atual is not None:
            return True

        ocupacoes_ativas = [
            (qtd, ini, fim) for (qtd, ini, fim) in self.ocupacao_caixas
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
            qtd for (qtd, ini, f) in self.ocupacao_caixas
            if not (fim <= ini or inicio >= f)
        )
        return (ocupadas + quantidade_caixas) <= self.capacidade_caixa_30kg

    def ocupar_caixas(self, atividade_id: int, quantidade: int, inicio: datetime, fim: datetime) -> bool:
        if not self.verificar_espaco_caixas(quantidade, inicio, fim):
            return False
        self.ocupacao_caixas.append((quantidade, inicio, fim))
        self.registrar_temperatura(atividade_id, quantidade, inicio, fim)
        return True

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade_id: int):
        self.historico_temperatura = [
            (aid, qtd, ini, fim, temp)
            for (aid, qtd, ini, fim, temp) in self.historico_temperatura
            if aid != atividade_id
        ]

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        self.ocupacao_caixas = [(qtd, ini, fim) for (qtd, ini, fim) in self.ocupacao_caixas if fim > horario_atual]
        self.historico_temperatura = [
            (aid, qtd, ini, fim, temp)
            for (aid, qtd, ini, fim, temp) in self.historico_temperatura if fim > horario_atual
        ]

    def liberar_todas_ocupacoes(self):
        self.ocupacao_caixas.clear()
        self.historico_temperatura.clear()

    def liberar_intervalo(self, inicio: datetime, fim: datetime):
        self.ocupacao_caixas = [
            (qtd, ini, f) for (qtd, ini, f) in self.ocupacao_caixas
            if not (ini >= inicio and f <= fim)
        ]
        self.historico_temperatura = [
            (aid, qtd, ini, f, temp)
            for (aid, qtd, ini, f, temp) in self.historico_temperatura
            if not (ini >= inicio and f <= fim)
        ]

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info(f"==============================================")
        logger.info(f"📅 Agenda do {self.nome}")
        logger.info(f"==============================================")

        if not self.historico_temperatura:
            logger.info("🔹 Nenhuma ocupação registrada.")
            return

        for (atividade_id, quantidade, inicio, fim, temp) in self.historico_temperatura:
            logger.info(
                f"❄️ Atividade {atividade_id} | Caixas: {quantidade} unidades | "
                f"{inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')} | Temperatura: {temp}°C"
            )
