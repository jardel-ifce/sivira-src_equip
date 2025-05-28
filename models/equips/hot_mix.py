from models.equips.equipamento import Equipamento
from enums.tipo_equipamento import TipoEquipamento
from enums.velocidade import Velocidade
from enums.pressao_chama import PressaoChama
from enums.tipo_atividade import TipoAtividade
from enums.tipo_setor import TipoSetor
from enums.tipo_chama import TipoChama
from typing import List, Tuple, Optional
from datetime import datetime
from utils.logger_factory import setup_logger


# 🔥 Logger
logger = setup_logger('HotMix')


class HotMix(Equipamento):
    """
    🍳 Equipamento HotMix — Misturadora com Cocção.
    ✔️ Controle de ocupação por tempo.
    ✔️ Controle de capacidade (gramas).
    ✔️ Controle de velocidade e chama.
    """

    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        numero_operadores: int,
        capacidade_gramas_min: int,
        capacidade_gramas_max: int,
        velocidades_suportadas: List[Velocidade],
        chamas_suportadas: List[TipoChama],
        pressao_chamas_suportadas: List[PressaoChama]
    ):
        super().__init__(
            id=id,
            nome=nome,
            tipo_equipamento=TipoEquipamento.MISTURADORAS_COM_COCCAO,
            setor=setor,
            numero_operadores=numero_operadores,
            status_ativo=True,
        )

        self.capacidade_gramas_min = capacidade_gramas_min
        self.capacidade_gramas_max = capacidade_gramas_max
        self.capacidade_gramas_atual = 0

        self.velocidades_suportadas = velocidades_suportadas
        self.velocidade_atual: Optional[Velocidade] = None

        self.chamas_suportadas = chamas_suportadas
        self.pressao_chamas_suportadas = pressao_chamas_suportadas
        self.pressao_chama_atual: Optional[PressaoChama] = None

        # Ocupações no tempo: (quantidade_gramas, inicio, fim, atividade_id)
        self.ocupacoes: List[Tuple[float, datetime, datetime, int]] = []

    # ==========================================================
    # 🚦 Validações
    # ==========================================================
    def validar_capacidade(self, quantidade_gramas: float) -> bool:
        return self.capacidade_gramas_min <= quantidade_gramas <= self.capacidade_gramas_max

    def esta_disponivel(self, inicio: datetime, fim: datetime) -> bool:
        for _, ocup_inicio, ocup_fim, _ in self.ocupacoes:
            if not (fim <= ocup_inicio or inicio >= ocup_fim):
                return False
        return True

    # ==========================================================
    # ⚙️ Velocidade e 🔥 Pressão de chama
    # ==========================================================
    def configurar_velocidade(self, velocidade: Velocidade) -> bool:
        if velocidade in self.velocidades_suportadas:
            self.velocidade_atual = velocidade
            logger.info(f"⚙️ {self.nome} | Velocidade ajustada para {velocidade.name}.")
            return True
        logger.error(
            f"❌ Velocidade {velocidade.name} não suportada pelo {self.nome}. "
            f"Suportadas: {[v.name for v in self.velocidades_suportadas]}"
        )
        return False

    def configurar_pressao_chama(self, pressao: PressaoChama) -> bool:
        if pressao in self.pressao_chamas_suportadas:
            self.pressao_chama_atual = pressao
            logger.info(f"🔥 {self.nome} | Pressão da chama ajustada para {pressao.name}.")
            return True
        logger.error(
            f"❌ Pressão {pressao.name} não suportada pelo {self.nome}. "
            f"Suportadas: {[p.name for p in self.pressao_chamas_suportadas]}"
        )
        return False

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
            f"🍳 {self.nome} | Ocupada com {quantidade_gramas}g "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} "
            f"para atividade {atividade_id}."
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
    # 🔍 Consultas
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
        logger.info(f"\n============================")
        logger.info(f"📅 Agenda da HotMix {self.nome}")
        logger.info(f"============================")
        if not self.ocupacoes:
            logger.info("🔹 Nenhuma ocupação registrada.")
            return
        for i, (qtd, ini, fim, atv_id) in enumerate(self.ocupacoes, start=1):
            logger.info(
                f"🔸 Ocupação {i}: {qtd}g | "
                f"Início: {ini.strftime('%H:%M')} | Fim: {fim.strftime('%H:%M')} | "
                f"Atividade ID: {atv_id} | Velocidade: {self.velocidade_atual.name if self.velocidade_atual else 'Não definida'} | "
                f"Pressão: {self.pressao_chama_atual.name if self.pressao_chama_atual else 'Não definida'}"
            )

    # ==========================================================
    # 🔄 Reset Geral
    # ==========================================================
    def resetar(self):
        self.velocidade_atual = None
        self.pressao_chama_atual = None
        self.ocupacoes.clear()
        self.capacidade_gramas_atual = 0
        logger.info(f"🔄 {self.nome} foi resetado para o estado inicial.")

    # ==========================================================
    # 📜 String Representação
    # ==========================================================
    def __str__(self):
        velocidades = ', '.join(v.name for v in self.velocidades_suportadas)
        pressoes = ', '.join(p.name for p in self.pressao_chamas_suportadas)
        return (
            super().__str__() +
            f"\n📦 Capacidade: {self.capacidade_gramas_min}g a {self.capacidade_gramas_max}g"
            f"\n⚙️ Velocidade atual: {self.velocidade_atual.name if self.velocidade_atual else 'Não definida'} | Suportadas: {velocidades}"
            f"\n🔥 Pressão atual: {self.pressao_chama_atual.name if self.pressao_chama_atual else 'Não definida'} | Suportadas: {pressoes}"
            f"\n📅 Ocupações: {len(self.ocupacoes)} registradas."
        )
