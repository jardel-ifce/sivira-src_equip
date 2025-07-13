from models.equipamentos.equipamento import Equipamento
from enums.producao.tipo_setor import TipoSetor
from enums.equipamentos.tipo_equipamento import TipoEquipamento
from typing import List, Dict, Tuple
from datetime import datetime
from utils.logs.logger_factory import setup_logger

logger = setup_logger('ModeladoraDePaes')

class ModeladoraDePaes(Equipamento):
    """
    🍞 Classe que representa uma Modeladora de Pães.
    ✔️ Capacidade de produção por minuto validada.
    ✔️ Ocupação exclusiva por atividade, sem sobreposição.
    """

    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        numero_operadores: int,
        capacidade_min_unidades_por_minuto: int,
        capacidade_max_unidades_por_minuto: int
    ):
        super().__init__(
            id=id,
            nome=nome,
            setor=setor,
            numero_operadores=numero_operadores,
            tipo_equipamento=TipoEquipamento.MODELADORAS,
            status_ativo=True
        )

        self.capacidade_min_unidades_por_minuto = capacidade_min_unidades_por_minuto
        self.capacidade_max_unidades_por_minuto = capacidade_max_unidades_por_minuto

        # Ocupações registradas: (ordem_id, pedido_id, atividade_id, quantidade, inicio, fim)
        self.ocupacoes: List[Tuple[int, int, int, int, datetime, datetime]] = []
    # ==========================================================
    # ✅ Validações
    # ==========================================================
    def esta_disponivel(self, inicio: datetime, fim: datetime) -> bool:
        for ocupacao in self.ocupacoes:
            if not (fim <= ocupacao[4] or inicio >= ocupacao[5]):
                logger.warning(f"❌ {self.nome} | Ocupação conflitante: entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}")
                return False
        return True
    
    # ==========================================================
    # 🔒 Ocupação
    # ==========================================================
    def ocupar(
        self,
        ordem_id: int,
        pedido_id: int,
        atividade_id: int,
        quantidade: int,
        inicio: datetime,
        fim: datetime,
        **kwargs
    ) -> bool:
       
        if not self.esta_disponivel(inicio, fim):
            logger.warning(f"🚫 {self.nome} | Ocupação não disponível para {atividade_id} entre {inicio} e {fim}.")
            return False
        
        else: 
            self.ocupacoes.append((ordem_id, pedido_id, atividade_id, quantidade, inicio, fim))
            logger.info(f"✅ {self.nome} | Ocupação registrada: {atividade_id} de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}.")
            return True

    # ==========================================================
    # 🔓 Liberações
    # ==========================================================
    def liberar_por_atividade(self, ordem_id: int, pedido_id: int, atividade_id: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            o for o in self.ocupacoes
            if not (o[0] == ordem_id and o[1] == pedido_id and o[2] == atividade_id)
        ]
        depois = len(self.ocupacoes)
        if antes != depois:
            logger.info(f"🔓 {self.nome} | Ocupações da atividade {atividade_id} removidas ({antes - depois} entradas).")
        else:
            logger.warning(f"🚫 {self.nome} | Não há ocupações para liberar para a atividade {atividade_id}.")

    def liberar_por_pedido(self, ordem_id: int, pedido_id: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            o for o in self.ocupacoes
            if not (o[0] == ordem_id and o[1] == pedido_id)
        ]
        depois = len(self.ocupacoes)
        if antes != depois:
            logger.info(f"🔓 {self.nome} | Ocupações do pedido {pedido_id} removidas ({antes - depois} entradas).")
        else:
            logger.warning(f"🚫 {self.nome} | Não há ocupações para liberar para o pedido {pedido_id}.")

    def liberar_por_ordem(self, ordem_id: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            o for o in self.ocupacoes
            if not (o[0] == ordem_id)
        ]
        depois = len(self.ocupacoes)
        if antes != depois:
            logger.info(f"🔓 {self.nome} | Ocupações da ordem {ordem_id} removidas ({antes - depois} entradas).")
        else:
            logger.warning(f"🚫 {self.nome} | Não há ocupações para liberar para a ordem {ordem_id}.")
    
    def liberar_todas_ocupacoes(self):
        total = len(self.ocupacoes)
        self.ocupacoes.clear()
        logger.info(f"🔓 {self.nome} liberou todas as {total} ocupações.")
    
    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            o for o in self.ocupacoes
            if not (o[5] <= horario_atual)
        ]
        liberadas = antes - len(self.ocupacoes)
        if liberadas > 0:
            logger.info(f"🔓 {self.nome} | Liberadas {liberadas} ocupações finalizadas até {horario_atual.strftime('%H:%M')}.")
        else:
            logger.info(f"ℹ️ {self.nome} | Nenhuma ocupação finalizada encontrada para liberar até {horario_atual.strftime('%H:%M')}.")
    
    def liberar_por_intervalo(self, inicio: datetime, fim: datetime):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            o for o in self.ocupacoes
            if not (o[4] >= inicio and o[5] <= fim)
        ]
        liberadas = antes - len(self.ocupacoes)

        logger.info(
            f"🔓 {self.nome} | Liberadas {liberadas} ocupações no intervalo de "
            f"{inicio.strftime('%H:%M')} a {fim.strftime('%H:%M')}."
        )
    
    
    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info(f"📅 Agenda da {self.nome}")
        logger.info("==============================================")
        if not self.ocupacoes:
            logger.info("Nenhuma ocupação registrada.")
            return
        
        for ocupacao in self.ocupacoes:
            ordem_id, pedido_id, atividade_id, quantidade, inicio, fim = ocupacao
            logger.info(
                f"Atividade {atividade_id} | Pedido {pedido_id} | Ordem {ordem_id} | "
                f"Quantidade: {quantidade} | Início: {inicio.strftime('%H:%M')} | Fim: {fim.strftime('%H:%M')}"
            )


