from models.equips.equipamento import Equipamento
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_setor import TipoSetor
from enums.tipo_chama import TipoChama
from enums.tipo_pressao_chama import TipoPressaoChama
from enums.tipo_velocidade import TipoVelocidade
from typing import List, Tuple
from datetime import datetime
from utils.logger_factory import setup_logger

# 🔥 Logger exclusivo para HotMix
logger = setup_logger("HotMix")


class HotMix(Equipamento):
    """
    🍳 Equipamento HotMix — Misturadora com Cocção de Alta Performance.
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

        # Tupla: (ordem_id, atividade_id, quantidade, inicio, fim, velocidade, chama, pressoes)
        self.ocupacoes: List[
            Tuple[int, int, int, datetime, datetime, TipoVelocidade, TipoChama, List[TipoPressaoChama]]
        ] = []

    def esta_disponivel(self, inicio: datetime, fim: datetime) -> bool:
        for _, _, _, ini, f, *_ in self.ocupacoes:
            if not (fim <= ini or inicio >= f):
                return False
        return True

    def ocupar(
        self,
        ordem_id: int,
        atividade_id: int,
        quantidade: int,
        inicio: datetime,
        fim: datetime,
        velocidade: TipoVelocidade,
        chama: TipoChama,
        pressao_chamas: List[TipoPressaoChama]
    ) -> bool:
        if not (self.capacidade_gramas_min <= quantidade <= self.capacidade_gramas_max):
            logger.warning(f"❌ Quantidade {quantidade}g fora dos limites do HotMix {self.nome}.")
            return False

        if not self.esta_disponivel(inicio, fim):
            logger.warning(f"❌ HotMix {self.nome} já ocupado entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}.")
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
            atividade_id,
            quantidade,
            inicio,
            fim,
            velocidade,
            chama,
            pressao_chamas
        ))

        logger.info(
            f"🍳 HotMix {self.nome} ocupado | Ordem {ordem_id} | Atividade {atividade_id} | {quantidade}g | "
            f"{inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')} | "
            f"Velocidade: {velocidade.name} | Chama: {chama.name} | "
            f"Pressões: {[p.name for p in pressao_chamas]}"
        )
        return True

    def liberar_concluidas(self, horario: datetime):
        antes = len(self.ocupacoes)
        self.ocupacoes = [o for o in self.ocupacoes if o[4] > horario]
        depois = len(self.ocupacoes)
        if antes != depois:
            logger.info(f"🟩 Liberadas {antes - depois} ocupações finalizadas do HotMix {self.nome}.")

    def liberar_por_ordem(self, ordem_id: int):
        """
        ❌ Libera todas as ocupações associadas à ordem de produção.
        """
        antes = len(self.ocupacoes)
        self.ocupacoes = [o for o in self.ocupacoes if o[0] != ordem_id]
        depois = len(self.ocupacoes)
        if antes != depois:
            logger.info(f"🟩 Liberadas ocupações da ordem {ordem_id} no HotMix {self.nome}.")

    def liberar_por_atividade(self, atividade_id: int, ordem_id: int):
        """
        ❌ Libera ocupações específicas de uma atividade dentro de uma ordem.
        """
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            o for o in self.ocupacoes
            if not (o[0] == ordem_id and o[1] == atividade_id)
        ]
        depois = len(self.ocupacoes)
        if antes != depois:
            logger.info(f"🟩 Liberadas ocupações da atividade {atividade_id} da ordem {ordem_id} no HotMix {self.nome}.")

    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info(f"📅 Agenda do HotMix {self.nome}")
        logger.info("==============================================")
        if not self.ocupacoes:
            logger.info("🔹 Nenhuma ocupação registrada.")
        for (ordem_id, atividade_id, qtd, ini, fim, velocidade, chama, pressoes) in self.ocupacoes:
            logger.info(
                f"🔸 Ordem {ordem_id} | Atividade {atividade_id} | {qtd}g | "
                f"{ini.strftime('%H:%M')} → {fim.strftime('%H:%M')} | "
                f"Velocidade: {velocidade.name} | Chama: {chama.name} | "
                f"Pressões: {[p.name for p in pressoes]}"
            )
