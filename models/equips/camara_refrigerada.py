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

        self.ocupacao_niveis: List[Tuple[int, datetime, datetime]] = []
        self.ocupacao_caixas: List[Tuple[int, datetime, datetime]] = []

        self.faixa_temperatura_min = faixa_temperatura_min
        self.faixa_temperatura_max = faixa_temperatura_max
        self.faixa_temperatura_atual = None

        # Ocupações: (ordem_id, atividade_id, quantidade, inicio, fim, temperatura)
        self.ocupacoes: List[Tuple[int, int, int, datetime, datetime, Optional[int]]] = []

    # ==========================================================
    # 🌡️ Controle de Temperatura
    # ==========================================================
    def ocupar(self, ordem_id: int, atividade_id: int, quantidade: int, inicio: datetime, fim: datetime):
        self.ocupacoes.append((ordem_id, atividade_id, quantidade, inicio, fim, self.faixa_temperatura_atual))
        logger.info(
            f"🌡️ Temperatura {self.faixa_temperatura_atual}°C registrada para Atividade {atividade_id} "
            f"(Ordem {ordem_id}) de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} na {self.nome}."
        )

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
            (qtd, ini, fim) for (qtd, ini, fim) in self.ocupacao_caixas + self.ocupacao_niveis
            if ini <= datetime.now() <= fim
        ]

        if ocupacoes_ativas:
            logger.warning(
                f"⚠️ Não é possível ajustar a temperatura da {self.nome} para {temperatura_desejada}°C. "
                f"Temperatura atual: {self.faixa_temperatura_atual}°C, há ocupações ativas."
            )
            return False

        self.faixa_temperatura_atual = temperatura_desejada
        logger.info(
            f"🌡️ Câmara {self.nome} estava vazia. Temperatura ajustada para {temperatura_desejada}°C."
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

    def ocupar_caixas(self, ordem_id: int, atividade_id: int, quantidade: int, inicio: datetime, fim: datetime) -> bool:
        if not self.verificar_espaco_caixas(quantidade, inicio, fim):
            return False
        self.ocupacao_caixas.append((quantidade, inicio, fim))
        self.ocupar(ordem_id, atividade_id, quantidade, inicio, fim)
        return True

    # ==========================================================
    # 🗂️ Ocupação por Níveis
    # ==========================================================
    def verificar_espaco_niveis(self, quantidade: int, inicio: datetime, fim: datetime) -> bool:
        ocupadas = sum(
            qtd for (qtd, ini, f) in self.ocupacao_niveis
            if not (fim <= ini or inicio >= f)
        )
        return (ocupadas + quantidade) <= self.capacidade_niveis_tela

    def ocupar_niveis(self, ordem_id: int, atividade_id: int, quantidade: int, inicio: datetime, fim: datetime) -> bool:
        if not self.verificar_espaco_niveis(quantidade, inicio, fim):
            return False
        self.ocupacao_niveis.append((quantidade, inicio, fim))
        self.ocupar(ordem_id, atividade_id, quantidade, inicio, fim)
        return True

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_ordem(self, ordem_id: int):
        """
        ❄️ Libera todas as ocupações da ordem especificada, incluindo caixas, níveis e log de temperatura.
        """
        self.ocupacoes = [
            (oid, aid, qtd, ini, fim, temp)
            for (oid, aid, qtd, ini, fim, temp) in self.ocupacoes
            if oid != ordem_id
        ]

        self.ocupacao_niveis = [
            (qtd, ini, fim)
            for (qtd, ini, fim) in self.ocupacao_niveis
            if not any(
                oid == ordem_id and qtd == qtd and ini == ini and fim == fim
                for (oid, _, _, ini, fim, _) in self.ocupacoes
            )
        ]

        self.ocupacao_caixas = [
            (qtd, ini, fim)
            for (qtd, ini, fim) in self.ocupacao_caixas
            if not any(
                oid == ordem_id and qtd == qtd and ini == ini and fim == fim
                for (oid, _, _, ini, fim, _) in self.ocupacoes
            )
        ]

        logger.info(f"🧊 Liberadas todas as ocupações da ordem {ordem_id} na {self.nome}.")

    def liberar_por_atividade(self, ordem_id: int, atividade_id: int):
        """
        ❄️ Libera ocupações específicas da atividade dentro da ordem.
        """
        self.ocupacoes = [
            (oid, aid, qtd, ini, fim, temp)
            for (oid, aid, qtd, ini, fim, temp) in self.ocupacoes
            if not (oid == ordem_id and aid == atividade_id)
        ]

        self.ocupacao_niveis = [
            (qtd, ini, fim)
            for (qtd, ini, fim) in self.ocupacao_niveis
            if not any(
                oid == ordem_id and aid == atividade_id and qtd == qtd and ini == ini and fim == fim
                for (oid, aid, _, ini, fim, _) in self.ocupacoes
            )
        ]

        self.ocupacao_caixas = [
            (qtd, ini, fim)
            for (qtd, ini, fim) in self.ocupacao_caixas
            if not any(
                oid == ordem_id and aid == atividade_id and qtd == qtd and ini == ini and fim == fim
                for (oid, aid, _, ini, fim, _) in self.ocupacoes
            )
        ]

        logger.info(f"🧊 Liberadas ocupações da atividade {atividade_id} da ordem {ordem_id} na {self.nome}.")


    def liberar_todas_ocupacoes(self):
        self.ocupacao_niveis.clear()
        self.ocupacao_caixas.clear()
        self.ocupacoes.clear()

    def liberar_intervalo(self, inicio: datetime, fim: datetime):
        self.ocupacao_niveis = [
            (qtd, ini, f) for (qtd, ini, f) in self.ocupacao_niveis
            if not (ini >= inicio and f <= fim)
        ]
        self.ocupacao_caixas = [
            (qtd, ini, f) for (qtd, ini, f) in self.ocupacao_caixas
            if not (ini >= inicio and f <= fim)
        ]
        self.ocupacoes = [
            (oid, aid, qtd, ini, f, temp)
            for (oid, aid, qtd, ini, f, temp) in self.ocupacoes
            if not (ini >= inicio and f <= fim)
        ]

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info(f"==============================================")
        logger.info(f"📅 Agenda da {self.nome}")
        logger.info(f"==============================================")

        if not self.ocupacoes:
            logger.info("🔹 Nenhuma ocupação registrada.")
            return

        for (ordem_id, atividade_id, quantidade, inicio, fim, temp) in self.ocupacoes:
            tipo = "Caixas" if (quantidade, inicio, fim) in self.ocupacao_caixas else "Níveis Tela"
            logger.info(
                f"🧊 Ordem {ordem_id} | Atividade {atividade_id} | {tipo}: {quantidade} unidades | "
                f"{inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')} | Temperatura: {temp}°C"
            )
