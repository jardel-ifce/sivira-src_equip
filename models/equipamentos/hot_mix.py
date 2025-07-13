from models.equipamentos.equipamento import Equipamento
from enums.equipamentos.tipo_equipamento import TipoEquipamento
from enums.producao.tipo_setor import TipoSetor
from enums.equipamentos.tipo_chama import TipoChama
from enums.equipamentos.tipo_pressao_chama import TipoPressaoChama
from enums.equipamentos.tipo_velocidade import TipoVelocidade
from typing import List, Tuple
from datetime import datetime
from utils.logs.logger_factory import setup_logger

# 🔥 Logger exclusivo para HotMix
logger = setup_logger("HotMix")


class HotMix(Equipamento):
    """
    🍳 Equipamento HotMix — Misturadora com Cocção de Alta Performance.
    ✔️ Controle de ocupação por ordem, pedido, atividade e quantidade.
    ✔️ Suporta múltiplas velocidades, chamas e pressões de chama.
    ✔️ Valida capacidade mínima e máxima por atividade.
    ✔️ Ocupação exclusiva no tempo, sem sobreposição de atividades.
    """

    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        numero_operadores: int,
        capacidade_gramas_min: int,
        capacidade_gramas_max: int,
        velocidades_suportadas: List[TipoVelocidade],
        chamas_suportadas: List[TipoChama],
        pressao_chamas_suportadas: List[TipoPressaoChama]
    ):
        super().__init__(
            id=id,
            nome=nome,
            setor=setor,
            numero_operadores=numero_operadores,
            tipo_equipamento=TipoEquipamento.MISTURADORAS_COM_COCCAO,
            status_ativo=True
        )

        self.capacidade_gramas_min = capacidade_gramas_min
        self.capacidade_gramas_max = capacidade_gramas_max
        self.velocidades_suportadas = velocidades_suportadas
        self.chamas_suportadas = chamas_suportadas
        self.pressao_chamas_suportadas = pressao_chamas_suportadas

        # Tupla: (ordem_id, pedido, atividade_id, quantidade, inicio, fim, velocidade, chama, pressoes)
        self.ocupacoes: List[
            Tuple[int, int, int, int, datetime, datetime, TipoVelocidade, TipoChama, List[TipoPressaoChama]]
        ] = []

    # ==========================================================
    # ✅ Validações
    # ==========================================================
    def esta_disponivel(self, inicio: datetime, fim: datetime) -> bool:
        for _, _, _, _, ini, f, *_ in self.ocupacoes:
            if not (fim <= ini or inicio >= f):
                return False
        return True
    
    # ==========================================================
    # 🍳 Ocupações
    # =========================================================
    def ocupar(
        self,
        ordem_id: int,
        pedido_id: int,
        atividade_id: int,
        quantidade: float,
        inicio: datetime,
        fim: datetime,
        velocidade: TipoVelocidade,
        chama: TipoChama,
        pressao_chamas: List[TipoPressaoChama]
    ) -> bool:
        if not (self.capacidade_gramas_min <= quantidade <= self.capacidade_gramas_max):
            logger.warning(f"❌ Quantidade {quantidade}g fora dos limites do {self.nome}.")
            return False

        if not self.esta_disponivel(inicio, fim):
            logger.warning(f"❌ {self.nome} já ocupado entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}.")
            return False

        if velocidade not in self.velocidades_suportadas:
            logger.error(f"❌ Velocidade {velocidade.name} não suportada por {self.nome}.")
            return False

        if chama not in self.chamas_suportadas:
            logger.error(f"❌ Chama {chama.name} não suportada por {self.nome}.")
            return False

        if any(p not in self.pressao_chamas_suportadas for p in pressao_chamas):
            logger.error(f"❌ Pressões de chama não suportadas por {self.nome}.")
            return False

        self.ocupacoes.append((
            ordem_id,
            pedido_id,
            atividade_id,
            quantidade,
            inicio,
            fim,
            velocidade,
            chama,
            pressao_chamas
        ))

        logger.info(
            f"🍳 {self.nome} ocupado | Ordem {ordem_id} | Pedido {pedido_id} |Atividade {atividade_id} | {quantidade}g | "
            f"{inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')} | "
            f"Velocidade: {velocidade.name} | Chama: {chama.name} | "
            f"Pressões: {[p.name for p in pressao_chamas]}"
        )
        return True

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, ordem_id: int, pedido_id: int, atividade_id: int):
        ocupacoes_iniciais = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if not (ocupacao[0] == ordem_id and ocupacao[1] == pedido_id and ocupacao[2] == atividade_id)
        ]

        if len(self.ocupacoes) < ocupacoes_iniciais:
            logger.info(
                f"🔓 {self.nome} liberado | Ordem {ordem_id} | Pedido {pedido_id} | Atividade {atividade_id}."
            )
        else:
            logger.warning(
                f"⚠️ Nenhuma ocupação encontrada para liberar | Ordem {ordem_id} | Pedido {pedido_id} | Atividade {atividade_id}."
            )
    
    def liberar_por_pedido(self, ordem_id: int, pedido_id: int):
        ocupacoes_iniciais = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if not (ocupacao[0] == ordem_id and ocupacao[1] == pedido_id)
        ]

        if len(self.ocupacoes) < ocupacoes_iniciais:
            logger.info(
                f"🔓 {self.nome} liberado | Ordem {ordem_id} | Pedido {pedido_id}."
            )
        else:
            logger.warning(
                f"⚠️ Nenhuma ocupação encontrada para liberar | Ordem {ordem_id} | Pedido {pedido_id}."
            )
    
    def liberar_por_ordem(self, ordem_id: int):
        ocupacoes_iniciais = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if not (ocupacao[0] == ordem_id)
        ]

        if len(self.ocupacoes) < ocupacoes_iniciais:
            logger.info(f"🔓 {self.nome} liberado | Ordem {ordem_id}.")
        else:
            logger.warning(f"⚠️ Nenhuma ocupação encontrada para liberar | Ordem {ordem_id}.")

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if ocupacao[5] > horario_atual
        ]
        liberadas = antes - len(self.ocupacoes)
        if liberadas > 0:
            logger.info(f"🔓 {self.nome} liberou {liberadas} ocupações finalizadas até {horario_atual.strftime('%H:%M')}.")
        else:
            logger.warning(f"⚠️ Nenhuma ocupação finalizada encontrada para liberar | Até {horario_atual.strftime('%H:%M')}.")

    def liberar_todas_ocupacoes(self):
        total = len(self.ocupacoes)
        self.ocupacoes.clear()
        logger.info(f"🔓 {self.nome} liberou todas as {total} ocupações.")
        
    def liberar_por_intervalo(self, inicio: datetime, fim: datetime):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if not (ocupacao[4] >= inicio and ocupacao[5] <= fim)
        ]
        liberadas = antes - len(self.ocupacoes)

        if liberadas > 0:
            logger.info(
                f"🔓 {self.nome} liberou {liberadas} ocupações no intervalo de "
                f"{inicio.strftime('%H:%M')} a {fim.strftime('%H:%M')}."
            )
        else:
            logger.info(
                f"ℹ️ Nenhuma ocupação encontrada para liberar no intervalo de "
                f"{inicio.strftime('%H:%M')} a {fim.strftime('%H:%M')}."
            )
    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info(f"📅 Agenda do {self.nome}")
        logger.info("==============================================")
        if not self.ocupacoes:
            logger.info("🔹 Nenhuma ocupação registrada.")
        for (ordem_id, pedido_id, atividade_id, qtd, ini, fim, velocidade, chama, pressoes) in self.ocupacoes:
            logger.info(
                f"🔸 Ordem {ordem_id} | Pedido {pedido_id} |  Atividade {atividade_id} | {qtd}g | "
                f"{ini.strftime('%H:%M')} → {fim.strftime('%H:%M')} | "
                f"Velocidade: {velocidade.name} | Chama: {chama.name} | "
                f"Pressões: {[p.name for p in pressoes]}"
            )
