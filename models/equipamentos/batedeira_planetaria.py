from models.equipamentos.equipamento import Equipamento
from enums.equipamentos.tipo_equipamento import TipoEquipamento
from enums.producao.tipo_setor import TipoSetor
from datetime import datetime
from typing import List, Tuple
from utils.logs.logger_factory import setup_logger

# 🪐 Logger específico para a Batedeira Planetária
logger = setup_logger('BatedeiraPlanetaria')


class BatedeiraPlanetaria(Equipamento):
    """
    🪐 Representa uma Batedeira Planetária.
    ✔️ Controle de velocidade mínima e máxima.
    ✔️ Ocupação com soma de quantidades para mesmo id_item.
    ✔️ REGRA: Mesmo item só pode ocupar no mesmo horário (início e fim exatos).
    ✔️ Capacidade de mistura validada por peso com intervalos flexíveis.
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
            status_ativo=True
        )
        self.capacidade_gramas_min = capacidade_gramas_min
        self.capacidade_gramas_max = capacidade_gramas_max
        self.velocidade_min = velocidade_min
        self.velocidade_max = velocidade_max

        # 📦 Ocupações: (id_ordem, id_pedido, id_atividade, id_item, quantidade, velocidade, inicio, fim)
        self.ocupacoes: List[Tuple[int, int, int, int, float, int, datetime, datetime]] = []

    # ==========================================================
    # ✅ Validações
    # ==========================================================
    def esta_disponivel(self, inicio: datetime, fim: datetime) -> bool:
        for ocupacao in self.ocupacoes:
            if not (fim <= ocupacao[6] or inicio >= ocupacao[7]):
                return False
        return True

    def esta_disponivel_para_item(self, inicio: datetime, fim: datetime, id_item: int) -> bool:
        """
        Verifica se a batedeira pode receber uma nova ocupação do item especificado.
        Uma batedeira ocupada só pode receber nova ocupação se:
        - Mesmo id_item E mesmo horário (início e fim exatos)
        """
        for ocupacao in self.ocupacoes:
            ocupacao_id_item = ocupacao[3]
            ocupacao_inicio = ocupacao[6]  # início  
            ocupacao_fim = ocupacao[7]     # fim
            
            # Se é o mesmo item E mesmo horário, permite
            if ocupacao_id_item == id_item and ocupacao_inicio == inicio and ocupacao_fim == fim:
                continue
            
            # Para qualquer outra situação, não pode haver sobreposição temporal
            if not (fim <= ocupacao_inicio or inicio >= ocupacao_fim):
                if ocupacao_id_item == id_item:
                    logger.warning(
                        f"⚠️ {self.nome}: Item {id_item} só pode ocupar no mesmo horário. "
                        f"Conflito: {inicio.strftime('%Y-%m-%d %H:%M')}-{fim.strftime('%Y-%m-%d %H:%M')} vs "
                        f"{ocupacao_inicio.strftime('%Y-%m-%d %H:%M')}-{ocupacao_fim.strftime('%Y-%m-%d %H:%M')}"
                    )
                else:
                    logger.warning(
                        f"⚠️ {self.nome} ocupada por item diferente (ID: {ocupacao_id_item}) "
                        f"entre {ocupacao_inicio.strftime('%Y-%m-%d %H:%M')} e {ocupacao_fim.strftime('%Y-%m-%d %H:%M')}."
                    )
                return False
        
        return True

    def validar_capacidade(self, quantidade_gramas: float) -> bool:
        return self.capacidade_gramas_min <= quantidade_gramas <= self.capacidade_gramas_max

    def validar_velocidade(self, velocidade: int) -> bool:
        return self.velocidade_min <= velocidade <= self.velocidade_max

    def obter_quantidade_maxima_item_periodo(self, id_item: int, inicio: datetime, fim: datetime) -> float:
        """
        Calcula a quantidade máxima de um item que estará sendo processado
        simultaneamente na batedeira durante qualquer momento do período especificado.
        Com a nova regra, só soma ocupações com horário exato.
        """
        quantidade_total = 0.0
        
        # Com a nova regra, só considera ocupações com horário EXATO
        for ocupacao in self.ocupacoes:
            if ocupacao[3] == id_item and ocupacao[6] == inicio and ocupacao[7] == fim:
                quantidade_total += ocupacao[4]
        
        return quantidade_total

    def validar_nova_ocupacao_item(self, id_item: int, quantidade_nova: float, 
                                  inicio: datetime, fim: datetime) -> bool:
        """
        Simula uma nova ocupação e verifica se a capacidade máxima será respeitada.
        Com a nova regra, só verifica ocupações com horário exato.
        """
        quantidade_atual = self.obter_quantidade_maxima_item_periodo(id_item, inicio, fim)
        quantidade_total = quantidade_atual + quantidade_nova
        
        if not self.validar_capacidade(quantidade_total):
            logger.debug(
                f"❌ {self.nome} | Item {id_item}: Capacidade excedida "
                f"({quantidade_total}g > {self.capacidade_gramas_max}g)"
            )
            return False
        
        return True

    # ==========================================================
    # 🏗️ Ocupação
    # ==========================================================
    def ocupar(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade_gramas: float,
        inicio: datetime,
        fim: datetime,
        velocidade: int
    ) -> bool:
        
        if velocidade is None:
            logger.error(f"❌ Velocidade não fornecida para ocupação da batedeira {self.nome}.")
            return False

        if not self.validar_velocidade(velocidade):
            logger.error(
                f"❌ Velocidade {velocidade} fora da faixa da batedeira {self.nome} "
                f"({self.velocidade_min} - {self.velocidade_max})."
            )
            return False

        if not self.esta_disponivel_para_item(inicio, fim, id_item):
            logger.warning(
                f"❌ {self.nome} | Não disponível para item {id_item} entre {inicio.strftime('%Y-%m-%d %H:%M')} e {fim.strftime('%Y-%m-%d %H:%M')}."
            )
            return False

        if not self.validar_nova_ocupacao_item(id_item, quantidade_gramas, inicio, fim):
            quantidade_atual = self.obter_quantidade_maxima_item_periodo(id_item, inicio, fim)
            logger.error(
                f"❌ {self.nome} | Item {id_item}: Nova quantidade {quantidade_gramas}g + "
                f"atual {quantidade_atual}g excederia capacidade máxima ({self.capacidade_gramas_max}g)"
            )
            return False

        self.ocupacoes.append((id_ordem, id_pedido, id_atividade, id_item, quantidade_gramas, velocidade, inicio, fim))
        
        # ✅ CORREÇÃO: Calcula total atual que já inclui a nova ocupação
        quantidade_total_atual = self.obter_quantidade_maxima_item_periodo(id_item, inicio, fim)
        
        # Log informativo com quantidade correta
        logger.info(
            f"🪐 {self.nome} | Item {id_item}: Nova ocupação {quantidade_gramas}g "
            f"de {inicio.strftime('%Y-%m-%d %H:%M')} até {fim.strftime('%Y-%m-%d %H:%M')} "
            f"(Total do item no horário: {quantidade_total_atual}g) "
            f"(Ordem {id_ordem}, Pedido {id_pedido}, Atividade {id_atividade}), "
            f"velocidade {velocidade}."
        )
        
        return True


    # ==========================================================
    # 🔓 Liberação (métodos idênticos à BatedeiraIndustrial)
    # ==========================================================
    def liberar_por_atividade(self, id_ordem: int, id_pedido: int, id_atividade: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido and ocupacao[2] == id_atividade)
        ]
        liberadas = antes - len(self.ocupacoes)
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações da batedeira {self.nome} "
                f"para atividade {id_atividade}, pedido {id_pedido}, ordem {id_ordem}."
            )
    
    def liberar_por_pedido(self, id_ordem: int, id_pedido: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido)
        ]
        liberadas = antes - len(self.ocupacoes)
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações da batedeira {self.nome} "
                f"do pedido {id_pedido} e ordem {id_ordem}."
            )

    def liberar_por_ordem(self, id_ordem: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if ocupacao[0] != id_ordem
        ]
        liberadas = antes - len(self.ocupacoes)
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações da batedeira {self.nome} "
                f"da ordem {id_ordem}."
            )

    def liberar_por_item(self, id_item: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if ocupacao[3] != id_item
        ]
        liberadas = antes - len(self.ocupacoes)
        if liberadas > 0:
            logger.info(
                f"🔓 {self.nome} | Liberadas {liberadas} ocupações do item {id_item}."
            )

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if ocupacao[7] > horario_atual
        ]
        liberadas = antes - len(self.ocupacoes)
        if liberadas > 0:
            logger.info(
                f"🟩 {self.nome} | Liberou {liberadas} ocupações finalizadas até {horario_atual.strftime('%Y-%m-%d %H:%M')}."
            )
        return liberadas

    def liberar_todas_ocupacoes(self):
        total = len(self.ocupacoes)
        self.ocupacoes.clear()
        logger.info(f"🔓 Liberou todas as {total} ocupações da batedeira {self.nome}.")
    
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info(f"📅 Agenda da {self.nome}")
        logger.info("==============================================")

        if not self.ocupacoes:
            logger.info("🔹 Nenhuma ocupação registrada.")
            return

        for ocupacao in self.ocupacoes:
            logger.info(
                f"🌀 Ordem: {ocupacao[0]} | Pedido: {ocupacao[1]} | Atividade: {ocupacao[2]} | Item: {ocupacao[3]} | "
                f"Quantidade: {ocupacao[4]}g | {ocupacao[6].strftime('%Y-%m-%d %H:%M')} → {ocupacao[7].strftime('%Y-%m-%d %H:%M')} | "
                f"Velocidade: {ocupacao[5]}"
            )