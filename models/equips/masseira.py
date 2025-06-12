from datetime import datetime
from typing import List, Optional
from enums.tipo_velocidade import TipoVelocidade
from enums.tipo_mistura import TipoMistura
from enums.tipo_setor import TipoSetor
from enums.tipo_equipamento import TipoEquipamento
from utils.logger_factory import setup_logger

logger = setup_logger("Masseira")


class Masseira:
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
        self.ocupacoes: List[dict] = []

    def validar_capacidade(self, quantidade: float) -> bool:
        if not (self.capacidade_gramas_min <= quantidade <= self.capacidade_gramas_max):
            logger.warning(
                f"⚠️ Quantidade {quantidade}g fora da faixa permitida pela {self.nome} "
                f"({self.capacidade_gramas_min}g - {self.capacidade_gramas_max}g)"
            )
            return False
        return True

    def esta_disponivel(self, inicio: datetime, fim: datetime) -> bool:
        for ocupacao in self.ocupacoes:
            if not (fim <= ocupacao["inicio"] or inicio >= ocupacao["fim"]):
                return False
        return True

    def ocupar(
        self,
        ordem_id: int,
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

        self.ocupacoes.append({
            "ordem_id": ordem_id,
            "atividade_id": atividade_id,
            "quantidade": quantidade_gramas,
            "inicio": inicio,
            "fim": fim,
            "velocidades": [v.name for v in velocidades] if velocidades else [],
            "tipo_mistura": tipo_mistura.name if tipo_mistura else None
        })

        logger.info(
            f"✅ Masseira {self.nome} ocupada para atividade {atividade_id} da ordem {ordem_id} "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}."
        )
        return True

    def liberar_por_ordem(self, ordem_id: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [o for o in self.ocupacoes if o["ordem_id"] != ordem_id]
        depois = len(self.ocupacoes)
        if antes != depois:
            logger.info(f"🧼 Liberadas {antes - depois} ocupações da ordem {ordem_id} na Masseira {self.nome}.")

    def liberar_por_atividade(self, atividade_id: int, ordem_id: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            o for o in self.ocupacoes
            if not (o["ordem_id"] == ordem_id and o["atividade_id"] == atividade_id)
        ]
        depois = len(self.ocupacoes)
        if antes != depois:
            logger.info(f"🧼 Liberadas ocupações da atividade {atividade_id} da ordem {ordem_id} na Masseira {self.nome}.")

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        self.ocupacoes = [o for o in self.ocupacoes if o["fim"] > horario_atual]

    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info(f"📅 Agenda da Masseira {self.nome}")
        logger.info("==============================================")

        todas_ocupacoes = sorted(self.ocupacoes, key=lambda o: o["atividade_id"])

        for o in todas_ocupacoes:
            velocidades_formatadas = ", ".join([v.replace("_", " ").title() for v in o["velocidades"]]) if o["velocidades"] else "-"
            tipo_mistura_formatado = o["tipo_mistura"].replace("_", " ").title() if o["tipo_mistura"] else "-"
            logger.info(
                f"🥣 Ordem {o['ordem_id']} | Atividade {o['atividade_id']} | Quantidade: {o['quantidade']}g | "
                f"{o['inicio'].strftime('%H:%M')} → {o['fim'].strftime('%H:%M')} | "
                f"Velocidade: {velocidades_formatadas} | Tipo Mistura: {tipo_mistura_formatado}"
            )
