from models.equips.equipamento import Equipamento
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_setor import TipoSetor  
from enums.tipo_embalagem import TipoEmbalagem
from typing import List, Tuple
from datetime import datetime
from utils.logger_factory import setup_logger

logger = setup_logger('Embaladora')

class Embaladora(Equipamento):
    """
    ✉️ Classe que representa uma Embaladora.
    Operação baseada em lotes de peso dentro de capacidade máxima.
    ✔️ Controle de capacidade por lote.
    ✔️ Ocupação simultânea no tempo.
    """

    # ============================================
    # 🔧 Inicialização
    # ============================================
    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        capacidade_gramas: int,
        lista_tipo_embalagem: List[TipoEmbalagem],
        numero_operadores: int
    ):
        super().__init__(
            id=id,
            nome=nome,
            tipo_equipamento=TipoEquipamento.EMBALADORAS,
            setor=setor,
            numero_operadores=numero_operadores,
            status_ativo=True
        )

        self.capacidade_gramas = capacidade_gramas
        self.lista_tipo_embalagem = lista_tipo_embalagem

        # ✉️ Ocupações: (ordem_id, pedido_id,atividade_id, quantidade, inicio, fim, lista_tipo_embalagem)
        self.ocupacao: List[Tuple[int, int, int, float, datetime, datetime, List[TipoEmbalagem]]] = []

    # ==========================================
    # ✅ Validações
    # ============================================
    def validar_capacidade(self, gramas: int) -> bool:
        """
        Verifica se o peso está dentro da capacidade operacional da embaladora.
        """
        if gramas > self.capacidade_gramas:
            logger.warning(
                f"❌ Quantidade {gramas}g excede a capacidade máxima ({self.capacidade_gramas}g) da embaladora {self.nome}."
            )
            return False

        return True

    # ============================================
    # ✉️ Ocupação
    # ============================================
    def ocupar(self, ordem_id: int, pedido_id: int, atividade_id: int, quantidade: float, inicio: datetime, fim: datetime, lista_tipo_embalagem: List[TipoEmbalagem]) -> bool:
        """
        Registra uma ocupação na embaladora.
        """
        if not self.validar_capacidade(quantidade):
            return False


        self.ocupacao.append((ordem_id, pedido_id, atividade_id, quantidade, inicio, fim, lista_tipo_embalagem))
        logger.info(
            f"✉️ Ocupação registrada na {self.nome} para {quantidade}g entre {inicio} e {fim}."
        )
        return True
   
    # ============================================
    # 🔓 Liberação
    # ============================================
    def liberar_por_intervalo(self, inicio: datetime, fim: datetime):
        """
        Libera a ocupação da embaladora por intervalo de tempo.
        """
        self.ocupacao = [
            ocup for ocup in self.ocupacao
            if not (ocup[4] < fim and ocup[5] > inicio)
        ]
        logger.info(
            f"🔓 Ocupação liberada na {self.nome} entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )

    def liberar_por_atividade(self, atividade_id: int, ordem_id: int, pedido_id: int):
        """
        Libera a ocupação da embaladora por atividade específica.
        """
        anterior = len(self.ocupacao)
        self.ocupacao = [
            ocup for ocup in self.ocupacao
            if not (ocup[2] == atividade_id and ocup[0] == ordem_id and ocup[1] == pedido_id)
        ]
        if len(self.ocupacao) < anterior:
            logger.info(
                f"🔓 Ocupação liberada na {self.nome} para atividade {atividade_id}, ordem {ordem_id}, pedido {pedido_id}."
            )
        else:
            logger.warning(
                f"⚠️ Nenhuma ocupação encontrada na {self.nome} para atividade {atividade_id}, ordem {ordem_id}, pedido {pedido_id}."
            )

    def liberar_por_pedido(self, ordem_id: int, pedido_id: int):
        """
        Libera todas as ocupações da embaladora para um pedido específico.
        """
        anterior = len(self.ocupacao)
        self.ocupacao = [
            ocup for ocup in self.ocupacao
            if not (ocup[0] == ordem_id and ocup[1] == pedido_id)
        ]
        if len(self.ocupacao) < anterior:
            logger.info(
                f"🔓 Ocupação liberada na {self.nome} para pedido {pedido_id}, ordem {ordem_id}."
            )
        else:
            logger.warning(
                f"⚠️ Nenhuma ocupação encontrada na {self.nome} para pedido {pedido_id}, ordem {ordem_id}."
            )
    
    def liberar_por_ordem(self, ordem_id: int):
        """
        Libera todas as ocupações da embaladora para uma ordem específica.
        """
        anterior = len(self.ocupacao)
        self.ocupacao = [
            ocup for ocup in self.ocupacao
            if ocup[0] != ordem_id
        ]
        if len(self.ocupacao) < anterior:
            logger.info(
                f"🔓 Ocupação liberada na {self.nome} para ordem {ordem_id}."
            )
        else:
            logger.warning(
                f"⚠️ Nenhuma ocupação encontrada na {self.nome} para ordem {ordem_id}."
            )

    # ============================================
    # 📅 Agenda
    # ============================================
    def mostrar_agenda(self):
        """
        Exibe a agenda de ocupações da embaladora.
        """
        logger.info("==============================================")
        logger.info(f"📅 Agenda da {self.nome}")
        logger.info("==============================================")
        if not self.ocupacao:
            logger.info("🔹 Nenhuma ocupação registrada.")
            return

        for ocup in self.ocupacao:
            ordem_id, pedido_id, atividade_id, quantidade, inicio, fim, lista_tipo_embalagem = ocup
            logger.info(
                f"🔸 Ordem {ordem_id}, Pedido {pedido_id}, Atividade {atividade_id}, "
                f"Quantidade {quantidade}g, Início {inicio.strftime('%H:%M')}, Fim {fim.strftime('%H:%M')}, "
                f"Embalagens: {[emb.name for emb in lista_tipo_embalagem]}."
            )