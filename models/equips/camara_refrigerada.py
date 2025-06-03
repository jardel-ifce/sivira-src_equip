from models.equips.equipamento import Equipamento
from enums.tipo_setor import TipoSetor
from enums.tipo_equipamento import TipoEquipamento
from typing import List, Tuple, Optional
from datetime import datetime
from utils.logger_factory import setup_logger


logger = setup_logger('CamaraRefrigerada')


class CamaraRefrigerada(Equipamento):
    """
    🧊 Representa uma Câmara Refrigerada com controle de ocupação
    por caixas ou níveis de tela, considerando períodos de tempo e controle de temperatura.
    """

    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        capacidade_niveis_tela: int,
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

        self.capacidade_niveis_tela = capacidade_niveis_tela
        self.capacidade_caixa_30kg = capacidade_caixa_30kg

        # Ocupações: (ocupacao_id, atividade_id, quantidade, inicio, fim)
        self.ocupacao_niveis: List[Tuple[int, int, int, datetime, datetime]] = []
        self.ocupacao_caixas: List[Tuple[int, int, int, datetime, datetime]] = []

        # Temperatura atual
        self.faixa_temperatura_min = faixa_temperatura_min
        self.faixa_temperatura_max = faixa_temperatura_max
        self.faixa_temperatura_atual = None

        # Histórico: (ocupacao_id, atividade_id, quantidade, inicio, fim, temperatura)
        self.historico_temperatura: List[Tuple[int, int, int, datetime, datetime, Optional[int]]] = []

    # ==========================================================
    # 🌡️ Controle de Temperatura
    # ==========================================================
    def registrar_temperatura(self, ocupacao_id: int, atividade_id: int, quantidade: int, inicio: datetime, fim: datetime):
        self.historico_temperatura.append((ocupacao_id, atividade_id, quantidade, inicio, fim, self.faixa_temperatura_atual))
        logger.info(
            f"🌡️ Temperatura {self.faixa_temperatura_atual}°C registrada para Atividade {atividade_id} "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} na {self.nome}."
        )

    def verificar_compatibilidade_de_temperatura(
        self,
        inicio: datetime,
        fim: datetime,
        temperatura_desejada: int
    ) -> bool:
        conflitos = [
            temp for (_, _, _, ini, f, temp) in self.historico_temperatura
            if not (fim <= ini or inicio >= f)
        ]
        return all(temp == temperatura_desejada for temp in conflitos) if conflitos else True

    def selecionar_faixa_temperatura(self, temperatura_desejada: int) -> bool:
        if self.faixa_temperatura_atual == temperatura_desejada:
            return True

        ocupacoes_ativas = [
            (qtd, ini, fim) for (_, _, qtd, ini, fim) in self.ocupacao_caixas + self.ocupacao_niveis
            if ini <= datetime.now() <= fim
        ]

        if ocupacoes_ativas:
            logger.warning(
                f"⚠️ Não é possível ajustar a temperatura da {self.nome} para {temperatura_desejada}°C. "
                f"Temperatura atual: {self.faixa_temperatura_atual}°C, há ocupações ativas."
            )
            return False

        logger.info(
            f"🌡️ Câmara {self.nome} estava vazia. Temperatura ajustada para {temperatura_desejada}°C."
        )
        self.faixa_temperatura_atual = temperatura_desejada
        return True

    # ==========================================================
    # 📦 Ocupação por Caixas
    # ==========================================================
    def verificar_espaco_caixas(self, quantidade_caixas: int, inicio: datetime, fim: datetime) -> bool:
        ocupadas = sum(
            qtd for (_, _, qtd, ini, f) in self.ocupacao_caixas
            if not (fim <= ini or inicio >= f)
        )
        return (ocupadas + quantidade_caixas) <= self.capacidade_caixa_30kg

    def ocupar_caixas(self, ocupacao_id: int, atividade_id: int, quantidade: int, inicio: datetime, fim: datetime) -> bool:
        if not self.verificar_espaco_caixas(quantidade, inicio, fim):
            return False

        self.ocupacao_caixas.append((ocupacao_id, atividade_id, quantidade, inicio, fim))
        self.registrar_temperatura(ocupacao_id, atividade_id, quantidade, inicio, fim)
        return True

    # ==========================================================
    # 🗂️ Ocupação por Níveis
    # ==========================================================
    def verificar_espaco_niveis(self, quantidade: int, inicio: datetime, fim: datetime) -> bool:
        ocupadas = sum(
            qtd for (_, _, qtd, ini, f) in self.ocupacao_niveis
            if not (fim <= ini or inicio >= f)
        )
        return (ocupadas + quantidade) <= self.capacidade_niveis_tela

    def ocupar_niveis(self, ocupacao_id: int, atividade_id: int, quantidade: int, inicio: datetime, fim: datetime) -> bool:
        if not self.verificar_espaco_niveis(quantidade, inicio, fim):
            return False

        self.ocupacao_niveis.append((ocupacao_id, atividade_id, quantidade, inicio, fim))
        self.registrar_temperatura(ocupacao_id, atividade_id, quantidade, inicio, fim)
        return True

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade_id: int):
        self.ocupacao_niveis = [
            (oid, aid, qtd, ini, fim) for (oid, aid, qtd, ini, fim) in self.ocupacao_niveis if aid != atividade_id
        ]
        self.ocupacao_caixas = [
            (oid, aid, qtd, ini, fim) for (oid, aid, qtd, ini, fim) in self.ocupacao_caixas if aid != atividade_id
        ]

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        self.ocupacao_niveis = [
            (oid, aid, qtd, ini, fim) for (oid, aid, qtd, ini, fim) in self.ocupacao_niveis if fim > horario_atual
        ]
        self.ocupacao_caixas = [
            (oid, aid, qtd, ini, fim) for (oid, aid, qtd, ini, fim) in self.ocupacao_caixas if fim > horario_atual
        ]
        self.historico_temperatura = [
            (oid, aid, qtd, ini, fim, temp) for (oid, aid, qtd, ini, fim, temp) in self.historico_temperatura if fim > horario_atual
        ]

    def liberar_todas_ocupacoes(self):
        self.ocupacao_niveis.clear()
        self.ocupacao_caixas.clear()
        self.historico_temperatura.clear()

    def liberar_intervalo(self, inicio: datetime, fim: datetime):
        self.ocupacao_niveis = [
            (oid, aid, qtd, ini, f) for (oid, aid, qtd, ini, f) in self.ocupacao_niveis
            if not (ini >= inicio and f <= fim)
        ]
        self.ocupacao_caixas = [
            (oid, aid, qtd, ini, f) for (oid, aid, qtd, ini, f) in self.ocupacao_caixas
            if not (ini >= inicio and f <= fim)
        ]
        self.historico_temperatura = [
            (oid, aid, qtd, ini, f, temp) for (oid, aid, qtd, ini, f, temp) in self.historico_temperatura
            if not (ini >= inicio and f <= fim)
        ]

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info(f"==============================================")
        logger.info(f"📅 Agenda da {self.nome}")
        logger.info(f"==============================================")

        if not self.ocupacao_caixas and not self.ocupacao_niveis and not self.historico_temperatura:
            logger.info("🔹 Nenhuma ocupação registrada.")
            return

        for (oid, aid, qtd, ini, fim) in self.ocupacao_caixas:
            logger.info(
                f"📦 Ocupação {oid}: Atividade {aid} | {qtd} caixas | "
                f"Início: {ini.strftime('%H:%M')} | Fim: {fim.strftime('%H:%M')}"
            )

        for (oid, aid, qtd, ini, fim) in self.ocupacao_niveis:
            logger.info(
                f"🗂️ Ocupação {oid}: Atividade {aid} | {qtd} níveis | "
                f"Início: {ini.strftime('%H:%M')} | Fim: {fim.strftime('%H:%M')}"
            )