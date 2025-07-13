from models.equipamentos.equipamento import Equipamento
from enums.producao.tipo_setor import TipoSetor
from enums.equipamentos.tipo_equipamento import TipoEquipamento
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from utils.logs.logger_factory import setup_logger

logger = setup_logger('DivisoraDeMassas')

class DivisoraDeMassas(Equipamento):
    """
    🔪 Classe que representa uma divisora de massas com ou sem boleadora.
    ✔️ Controle de capacidade mínima e máxima por lote.
    ✔️ Permite divisão de massas em frações, com opção de boleamento.
    ✔️ Ocupação exclusiva no tempo.
    """

    # ============================================
    # 🔧 Inicialização
    # ============================================
    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        numero_operadores: int,
        capacidade_gramas_min: int,
        capacidade_gramas_max: int,
        boleadora: bool,
        capacidade_divisao_unidades_por_segundo: int,
        capacidade_boleamento_unidades_por_segundo: int
    ):
        super().__init__(
            id=id,
            nome=nome,
            setor=setor,
            numero_operadores=numero_operadores,
            tipo_equipamento=TipoEquipamento.DIVISORAS_BOLEADORAS,
            status_ativo=True
        )

        self.capacidade_gramas_min = capacidade_gramas_min
        self.capacidade_gramas_max = capacidade_gramas_max
        self.boleadora = boleadora
        self.capacidade_divisao_unidades_por_segundo = capacidade_divisao_unidades_por_segundo
        self.capacidade_boleamento_unidades_por_segundo = capacidade_boleamento_unidades_por_segundo

        # 📦 Ocupações: (ordem_id, pedido_id, atividade_id, quantidade, inicio, fim, boleadora)
        self.ocupacoes: List[Tuple[int, int, int, float, datetime, datetime, Optional[bool]]] = []

    # ==========================================================
    # ✅ Validações
    # ==========================================================
    def validar_capacidade(self, gramas: float) -> bool:
        if gramas < self.capacidade_gramas_min:
            logger.warning(
                f"⚠️ Quantidade {gramas}g abaixo da capacidade mínima ({self.capacidade_gramas_min}g) da {self.nome}."
            )
            return False
        if gramas > self.capacidade_gramas_max:
            logger.warning(
                f"⚠️ Quantidade {gramas}g acima da capacidade máxima ({self.capacidade_gramas_max}g) da {self.nome}."
            )
            return False
        return True

    def esta_disponivel(self, inicio: datetime, fim: datetime) -> bool:
        for _, _, _, _, ocup_inicio, ocup_fim, _ in self.ocupacoes:
            if not (fim <= ocup_inicio or inicio >= ocup_fim):
                logger.warning(
                    f"⚠️ {self.nome} já está ocupada entre {ocup_inicio.strftime('%H:%M')} e {ocup_fim.strftime('%H:%M')}."
                )
                return False
        return True

    # ==========================================================
    # 🔪 Ocupação
    # ==========================================================
    def ocupar(
        self,
        ordem_id: int,
        pedido_id: int,
        atividade_id: int,
        quantidade: float,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        if not self.validar_capacidade(quantidade):
            return False

        if not self.esta_disponivel(inicio, fim):
            return False

        boleadora = self.boleadora and quantidade >= self.capacidade_gramas_min
        self.ocupacoes.append(
            (ordem_id, pedido_id, atividade_id, quantidade, inicio, fim, boleadora)
        )

        logger.info(
            f"🔪 Ocupação registrada na {self.nome}: "
            f"Ordem {ordem_id}, Pedido {pedido_id}, Atividade {atividade_id}, "
            f"Quantidade {quantidade}g, Início {inicio.strftime('%H:%M')}, Fim {fim.strftime('%H:%M')}, "
            f"Boleadora: {'Sim' if boleadora else 'Não'}."
        )
        return True
    
    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade_id: int, pedido_id: int, ordem_id: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            o for o in self.ocupacoes
            if not (o[2] == atividade_id and o[1] == pedido_id and o[0] == ordem_id)
        ]
        liberadas = antes - len(self.ocupacoes)
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações da {self.nome} "
                f"para atividade {atividade_id}, pedido {pedido_id}, ordem {ordem_id}."
            )
        else:
            logger.info(
                f"🔓 Nenhuma ocupação encontrada para atividade {atividade_id}, "
                f"pedido {pedido_id}, ordem {ordem_id} na {self.nome}."
            )

    def liberar_por_pedido(self, ordem_id: int, pedido_id: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            o for o in self.ocupacoes if not (o[0] == ordem_id and o[1] == pedido_id)
        ]
        liberadas = antes - len(self.ocupacoes)
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações da {self.nome} "
                f"do pedido {pedido_id} da ordem {ordem_id}."
            )
        else:
            logger.info(
                f"🔓 Nenhuma ocupação do pedido {pedido_id} da ordem {ordem_id} encontrada na {self.nome}."
            )
    
    def liberar_por_ordem(self, ordem_id: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            o for o in self.ocupacoes if not o[0] == ordem_id
        ]
        liberadas = antes - len(self.ocupacoes)
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações da {self.nome} "
                f"da ordem {ordem_id}."
            )
        else:
            logger.info(
                f"🔓 Nenhuma ocupação da ordem {ordem_id} encontrada na {self.nome}."
            )   
            
    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            o for o in self.ocupacoes if not o[5] <= horario_atual
        ]
        liberadas = antes - len(self.ocupacoes)
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações finalizadas da {self.nome} "
                f"até {horario_atual.strftime('%H:%M')}."
            )
        else:
            logger.info(
                f"🔓 Nenhuma ocupação finalizada encontrada na {self.nome} "
                f"até {horario_atual.strftime('%H:%M')}."
            )
            
    def liberar_todas_ocupacoes(self):
        total = len(self.ocupacoes)
        self.ocupacoes.clear()
        logger.info(f"🔓 Liberadas todas as {total} ocupações da {self.nome}."
                    )
    
    def liberar_por_intervalo(self, inicio: datetime, fim: datetime):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            o for o in self.ocupacoes
            if not (o[4] < fim and o[5] > inicio)
        ]
        liberadas = antes - len(self.ocupacoes)
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações da {self.nome} "
                f"entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
            )
    

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        print("==============================================")
        print(f"📅 Agenda da {self.nome}")
        print("==============================================")
        if not self.ocupacao:
            print("🔸 Nenhuma ocupação registrada.")
            return
        
        for ocupacao in self.ocupacoes:
            ordem_id, pedido_id, atividade_id, quantidade, inicio, fim, boleadora = ocupacao
            print(
                f"🔸 Ordem {ordem_id}, Pedido {pedido_id}, Atividade {atividade_id}, "
                f"Quantidade {quantidade}g, Início {inicio.strftime('%H:%M')}, "
                f"Fim {fim.strftime('%H:%M')}, Boleadora: {'Sim' if boleadora else 'Não'}"
            )
