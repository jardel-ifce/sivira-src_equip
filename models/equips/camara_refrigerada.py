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

        self.ocupacao_niveis: List[Tuple[int, datetime, datetime, int]] = []
        self.ocupacao_caixas: List[Tuple[int, datetime, datetime, int]] = []

        self.faixa_temperatura_min = faixa_temperatura_min
        self.faixa_temperatura_max = faixa_temperatura_max
        self.faixa_temperatura_atual = faixa_temperatura_min

        self.historico_temperatura: List[Tuple[datetime, datetime, Optional[int]]] = []

    # ==========================================================
    # 🔥 Controle de Temperatura por Período
    # ==========================================================
    def registrar_temperatura(self, inicio: datetime, fim: datetime):
        self.historico_temperatura.append((inicio, fim, self.faixa_temperatura_atual))
        logger.info(
            f"🌡️ Temperatura {self.faixa_temperatura_atual}°C registrada de {inicio.strftime('%H:%M')} "
            f"até {fim.strftime('%H:%M')} na {self.nome}."
        )

    def verificar_compatibilidade_de_temperatura(
        self,
        inicio: datetime,
        fim: datetime,
        temperatura_desejada: int
    ) -> bool:
        """
        ✔️ Verifica se é possível utilizar a câmara na temperatura desejada no intervalo.
        ✔️ Se não houver registros de temperatura no intervalo, entende-se que a câmara está livre.
        """
        # 🔎 Filtra registros que colidem com o intervalo
        ocupacoes = [
            (ini, f, temp) for (ini, f, temp) in self.historico_temperatura
            if not (fim <= ini or inicio >= f)  # Verifica sobreposição
        ]

        # ✔️ Se não há registros no intervalo, considera livre
        if not ocupacoes:
            return True

        # ✔️ Verifica se todas as temperaturas no intervalo são compatíveis
        for _, _, temp in ocupacoes:
            if temp != temperatura_desejada:
                return False

        return True


    def selecionar_faixa_temperatura(self, temperatura_desejada: int) -> bool:
        """
        ✔️ Seleciona ou mantém a temperatura desejada se possível.
        ✔️ Só permite alterar se não houver ocupações conflitantes no momento.
        """
        if self.faixa_temperatura_atual == temperatura_desejada:
            return True

        # 🔎 Verifica se há ocupações ativas no momento da mudança
        ocupacoes_ativas = [
            (qtd, ini, fim, a_id) for (qtd, ini, fim, a_id) in self.ocupacao_caixas + self.ocupacao_niveis
            if ini <= datetime.now() <= fim
        ]

        if ocupacoes_ativas:
            logger.warning(
                f"⚠️ Não é possível ajustar a temperatura da {self.nome} para {temperatura_desejada}°C. "
                f"Temperatura atual: {self.faixa_temperatura_atual}°C, há ocupações ativas."
            )
            return False

        # ✔️ Se não há ocupações no momento, pode ajustar
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
            qtd for (qtd, ini, f, _) in self.ocupacao_caixas
            if not (fim <= ini or inicio >= f)
        )
        return (ocupadas + quantidade_caixas) <= self.capacidade_caixa_30kg

    def ocupar_caixas(self, quantidade_caixas: int, inicio: datetime, fim: datetime, atividade_id: int) -> bool:
        if not self.verificar_espaco_caixas(quantidade_caixas, inicio, fim):
            return False

        self.ocupacao_caixas.append((quantidade_caixas, inicio, fim, atividade_id))
        self.registrar_temperatura(inicio, fim)
        return True

    # ==========================================================
    # 🗂️ Ocupação por Níveis
    # ==========================================================
    def verificar_espaco_niveis(self, quantidade_niveis: int, inicio: datetime, fim: datetime) -> bool:
        ocupadas = sum(
            qtd for (qtd, ini, f, _) in self.ocupacao_niveis
            if not (fim <= ini or inicio >= f)
        )
        return (ocupadas + quantidade_niveis) <= self.capacidade_niveis_tela

    def ocupar_niveis(self, quantidade_niveis: int, inicio: datetime, fim: datetime, atividade_id: int) -> bool:
        if not self.verificar_espaco_niveis(quantidade_niveis, inicio, fim):
            return False

        self.ocupacao_niveis.append((quantidade_niveis, inicio, fim, atividade_id))
        self.registrar_temperatura(inicio, fim)
        return True

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade_id: int):
        self.ocupacao_niveis = [
            (qtd, ini, fim, a_id) for (qtd, ini, fim, a_id) in self.ocupacao_niveis if a_id != atividade_id
        ]
        self.ocupacao_caixas = [
            (qtd, ini, fim, a_id) for (qtd, ini, fim, a_id) in self.ocupacao_caixas if a_id != atividade_id
        ]

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        self.ocupacao_niveis = [
            (qtd, ini, fim, a_id) for (qtd, ini, fim, a_id) in self.ocupacao_niveis if fim > horario_atual
        ]
        self.ocupacao_caixas = [
            (qtd, ini, fim, a_id) for (qtd, ini, fim, a_id) in self.ocupacao_caixas if fim > horario_atual
        ]
        self.historico_temperatura = [
            (ini, fim, temp) for (ini, fim, temp) in self.historico_temperatura if fim > horario_atual
        ]

    def liberar_todas_ocupacoes(self):
        self.ocupacao_niveis.clear()
        self.ocupacao_caixas.clear()
        self.historico_temperatura.clear()

    def liberar_intervalo(self, inicio: datetime, fim: datetime):
        self.ocupacao_niveis = [
            (qtd, ini, f, a_id) for (qtd, ini, f, a_id) in self.ocupacao_niveis
            if not (ini >= inicio and f <= fim)
        ]
        self.ocupacao_caixas = [
            (qtd, ini, f, a_id) for (qtd, ini, f, a_id) in self.ocupacao_caixas
            if not (ini >= inicio and f <= fim)
        ]
        self.historico_temperatura = [
            (ini, f, temp) for (ini, f, temp) in self.historico_temperatura
            if not (ini >= inicio and f <= fim)
        ]

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info(f"\n📅 Agenda da {self.nome}")

        for (qtd, ini, fim, a_id) in self.ocupacao_caixas:
            logger.info(
                f"📦 {qtd} caixas | {ini.strftime('%H:%M')} - {fim.strftime('%H:%M')} | Atividade {a_id}"
            )
        for (qtd, ini, fim, a_id) in self.ocupacao_niveis:
            logger.info(
                f"🗂️ {qtd} níveis | {ini.strftime('%H:%M')} - {fim.strftime('%H:%M')} | Atividade {a_id}"
            )

        for (ini, fim, temp) in self.historico_temperatura:
            logger.info(
                f"🌡️ Temperatura {temp}°C | {ini.strftime('%H:%M')} - {fim.strftime('%H:%M')}"
            )
