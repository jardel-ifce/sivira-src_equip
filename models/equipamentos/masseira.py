from datetime import datetime
from typing import List, Optional, Tuple
from enums.equipamentos.tipo_velocidade import TipoVelocidade
from enums.equipamentos.tipo_mistura import TipoMistura
from enums.producao.tipo_setor import TipoSetor
from enums.equipamentos.tipo_equipamento import TipoEquipamento
from utils.logs.logger_factory import setup_logger

logger = setup_logger("Masseira")


class Masseira:
    """🥣 Classe que representa uma Masseira.
    ✔️ Controle de capacidade por peso.
    ✔️ Ocupação exclusiva no tempo.
    ✔️ Suporta múltiplas velocidades e tipos de mistura.
    """
    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        capacidade_gramas_min: float,
        capacidade_gramas_max: float,
        velocidades_suportadas: Optional[List[TipoVelocidade]] = None,
        tipos_de_mistura_suportados: Optional[List[TipoMistura]] = None
    ):
        self.id = id
        self.nome = nome
        self.setor = setor
        self.tipo_equipamento = TipoEquipamento.MISTURADORAS
        self.capacidade_gramas_min = capacidade_gramas_min
        self.capacidade_gramas_max = capacidade_gramas_max
        self.velocidades_suportadas = velocidades_suportadas or []
        self.tipos_de_mistura_suportados = tipos_de_mistura_suportados or []

        # Lista de ocupações (ordem_id, pedido_id, atividade_id, quantidade, inicio, fim, velocidades, tipo_mistura)
        self.ocupacoes: List[Tuple[int, int, int, float, datetime, datetime, List[TipoVelocidade], TipoMistura]] = []

    # ==========================================================
    # ✅ Validações
    # ==========================================================
    def validar_capacidade(self, quantidade: float) -> bool:
        if not (self.capacidade_gramas_min <= quantidade <= self.capacidade_gramas_max):
            logger.warning(
                f"⚠️ Quantidade {quantidade}g fora da faixa permitida pela {self.nome} "
                f"({self.capacidade_gramas_min}g - {self.capacidade_gramas_max}g)"
            )
            return False
        return True

    def esta_disponivel(self, inicio: datetime, fim: datetime) -> bool:
        for _, _, _, _, ocup_inicio, ocup_fim, *_ in self.ocupacoes:
            if not (fim <= ocup_inicio or inicio >= ocup_fim):
                logger.warning(
                    f"⚠️ Masseira {self.nome} não disponível entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
                )
                return False
        return True
    
    # ==========================================================
    # 🥣 Ocupação
    # ==========================================================
    def ocupar(
        self,
        ordem_id: int,
        pedido_id: int,
        atividade_id: int,
        quantidade_gramas: float,
        inicio: datetime,
        fim: datetime,
        velocidades: Optional[List[TipoVelocidade]] = None,
        tipo_mistura: Optional[TipoMistura] = None
    ) -> bool:
        if not self.validar_capacidade(quantidade_gramas):
            return False

        if velocidades:
            for v in velocidades:
                if v not in self.velocidades_suportadas:
                    logger.warning(f"⚠️ Velocidade {v.name} não suportada pela {self.nome}.")
                    return False

        if tipo_mistura is not None:
            if not isinstance(tipo_mistura, TipoMistura):
                logger.error(f"❌ tipo_mistura inválido recebido: {tipo_mistura} ({type(tipo_mistura)})")
                return False

            if tipo_mistura not in self.tipos_de_mistura_suportados:
                logger.warning(f"⚠️ Tipo de mistura {tipo_mistura.name} não suportado pela {self.nome}.")
                return False

        self.ocupacoes.append(
            (ordem_id, pedido_id, atividade_id, quantidade_gramas, inicio, fim, velocidades or [], tipo_mistura)
        )

        logger.info(
            f"✅ {self.nome} ocupada para atividade {atividade_id} da ordem {ordem_id} "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
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
        depois = len(self.ocupacoes)
        if antes != depois:
            logger.info(
                f"🔓 Ocupação liberada na {self.nome} para atividade {atividade_id}, "
                f"pedido {pedido_id}, ordem {ordem_id}."
            )
        else:
            logger.warning(
                f"⚠️ Nenhuma ocupação encontrada na {self.nome} para atividade {atividade_id}, "
                f"pedido {pedido_id}, ordem {ordem_id}."
            )

    def liberar_por_pedido(self, ordem_id: int, pedido_id: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            o for o in self.ocupacoes
            if not (o[0] == ordem_id and o[1] == pedido_id)
        ]
        depois = len(self.ocupacoes)
        if antes != depois:
            logger.info(f"🔓 Ocupação liberada na {self.nome} para pedido {pedido_id}, ordem {ordem_id}.")
        else:
            logger.warning(f"⚠️ Nenhuma ocupação encontrada na {self.nome} para pedido {pedido_id}, ordem {ordem_id}.") 

    def liberar_por_ordem(self, ordem_id: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            o for o in self.ocupacoes
            if not (o[0] == ordem_id)
        ]
        depois = len(self.ocupacoes)
        if antes != depois:
            logger.info(f"🔓 Ocupação liberada na {self.nome} para ordem {ordem_id}.")
        else:
            logger.warning(f"⚠️ Nenhuma ocupação encontrada na {self.nome} para ordem {ordem_id}.")
    
    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            o for o in self.ocupacoes
            if o[5] > horario_atual
        ]
        liberadas = antes - len(self.ocupacoes)
        if liberadas > 0:
            logger.info(f"🔓 {self.nome} liberou {liberadas} ocupações finalizadas até {horario_atual.strftime('%H:%M')}.")
        else:
            logger.info(f"ℹ️ Nenhuma ocupação finalizada encontrada para liberar na {self.nome} até {horario_atual.strftime('%H:%M')}.")

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info(f"📅 Agenda da {self.nome}")
        logger.info("==============================================")

        if not self.ocupacoes:
            logger.info("ℹ️ Nenhuma ocupação agendada.")
            return
        
        for ordem_id, pedido_id, atividade_id, quantidade, inicio, fim, velocidades, tipo_mistura in self.ocupacoes:
            velocidades_str = ", ".join([v.name for v in velocidades]) if velocidades else "Nenhuma"
            logger.info(
                f"📦 Ordem {ordem_id} | Pedido {pedido_id} | Atividade {atividade_id} | "
                f"Quantidade: {quantidade}g | Início: {inicio.strftime('%H:%M')} | "
                f"Fim: {fim.strftime('%H:%M')} | Velocidades: {velocidades_str} | "
                f"Tipo de Mistura: {tipo_mistura.name if tipo_mistura else 'Nenhum'}"
            )