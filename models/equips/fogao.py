from models.equips.equipamento import Equipamento
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_setor import TipoSetor
from enums.tipo_chama import TipoChama
from enums.tipo_pressao_chama import TipoPressaoChama
from typing import List, Tuple
from datetime import datetime
from utils.logger_factory import setup_logger

# 🔥 Logger específico para Fogão
logger = setup_logger('Fogao')


class Fogao(Equipamento):
    """
    🔥 Fogão com controle de ocupação por boca, permitindo múltiplas atividades simultâneas,
    desde que cada boca esteja livre no intervalo desejado.
    """

    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        numero_operadores: int,
        chamas_suportadas: List[TipoChama],
        capacidade_por_boca_gramas_min: int,
        capacidade_por_boca_gramas_max: int,
        numero_bocas: int,
        pressao_chamas_suportadas: List[TipoPressaoChama],
    ):
        super().__init__(
            id=id,
            nome=nome,
            setor=setor,
            numero_operadores=numero_operadores,
            tipo_equipamento=TipoEquipamento.FOGOES,
            status_ativo=True
        )

        self.chamas_suportadas = chamas_suportadas
        self.capacidade_por_boca_gramas_min = capacidade_por_boca_gramas_min
        self.capacidade_por_boca_gramas_max = capacidade_por_boca_gramas_max
        self.numero_bocas = numero_bocas
        self.pressao_chamas_suportadas = pressao_chamas_suportadas

        # (ordem_id, atividade_id, quantidade, inicio, fim, tipo_chama, pressao_chama[])
        self.ocupacoes_por_boca: List[List[Tuple[int, int, int, datetime, datetime, TipoChama, List[TipoPressaoChama]]]] = [
            [] for _ in range(numero_bocas)
        ]

    # ==========================================================
    # 🔍 Consulta de disponibilidade
    # ==========================================================
    def boca_disponivel(self, boca_index: int, inicio: datetime, fim: datetime) -> bool:
        for _, _, _, ini, f, _, _ in self.ocupacoes_por_boca[boca_index]:
            if not (fim <= ini or inicio >= f):
                return False
        return True

    def bocas_disponiveis(self, inicio: datetime, fim: datetime) -> List[int]:
        return [
            i for i in range(self.numero_bocas)
            if self.boca_disponivel(i, inicio, fim)
        ]

    # ==========================================================
    # 🔐 Ocupação
    # ==========================================================
    def ocupar_boca(
        self,
        ordem_id: int,
        atividade_id: int,
        quantidade: int,
        inicio: datetime,
        fim: datetime,
        tipo_chama: TipoChama,
        pressao_chama: List[TipoPressaoChama],
        boca: int
    ) -> bool:
        if not self.boca_disponivel(boca, inicio, fim):
            return False

        if not (self.capacidade_por_boca_gramas_min <= quantidade <= self.capacidade_por_boca_gramas_max):
            logger.warning(
                f"❌ Quantidade {quantidade}g fora dos limites da boca ({self.capacidade_por_boca_gramas_min}-{self.capacidade_por_boca_gramas_max})g"
            )
            return False

        self.ocupacoes_por_boca[boca].append(
            (ordem_id, atividade_id, quantidade, inicio, fim, tipo_chama, pressao_chama)
        )

        pressoes_formatadas = ", ".join([p.value for p in pressao_chama])

        logger.info(
            f"🔥 Ocupou a boca {boca + 1} do fogão {self.nome} com {quantidade}g "
            f"para ordem {ordem_id} | atividade {atividade_id} de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} "
            f"| Chama: {tipo_chama.value} | Pressão: {pressoes_formatadas}"
        )
        return True

    # ==========================================================
    # 🧹 Liberação
    # ==========================================================
    def liberar_bocas_terminadas(self, horario_atual: datetime):
        total_liberadas = 0
        for i in range(self.numero_bocas):
            antes = len(self.ocupacoes_por_boca[i])
            self.ocupacoes_por_boca[i] = [
                (oid, aid, qtd, ini, fim, chama, pressao)
                for (oid, aid, qtd, ini, fim, chama, pressao) in self.ocupacoes_por_boca[i]
                if fim > horario_atual
            ]
            total_liberadas += antes - len(self.ocupacoes_por_boca[i])

        if total_liberadas > 0:
            logger.info(f"🟩 Liberou {total_liberadas} ocupações finalizadas no fogão {self.nome}.")

    def liberar_por_atividade(self, atividade_id: int, ordem_id: int):
        liberadas = 0
        for i in range(self.numero_bocas):
            antes = len(self.ocupacoes_por_boca[i])
            self.ocupacoes_por_boca[i] = [
                (oid, aid, qtd, ini, fim, chama, pressao)
                for (oid, aid, qtd, ini, fim, chama, pressao) in self.ocupacoes_por_boca[i]
                if not (aid == atividade_id and oid == ordem_id)
            ]
            liberadas += antes - len(self.ocupacoes_por_boca[i])
        logger.info(f"🟩 Liberou {liberadas} ocupações da atividade {atividade_id} da ordem {ordem_id} no fogão {self.nome}.")

    def liberar_por_ordem(self, ordem_id: int):
        total = 0
        for i in range(self.numero_bocas):
            antes = len(self.ocupacoes_por_boca[i])
            self.ocupacoes_por_boca[i] = [
                (oid, aid, qtd, ini, fim, chama, pressao)
                for (oid, aid, qtd, ini, fim, chama, pressao) in self.ocupacoes_por_boca[i]
                if oid != ordem_id
            ]
            total += antes - len(self.ocupacoes_por_boca[i])
        logger.info(f"🟩 Liberou {total} ocupações da ordem {ordem_id} no fogão {self.nome}.")

    def liberar_boca(self, boca: int, atividade_id: int, ordem_id: int):
        antes = len(self.ocupacoes_por_boca[boca])
        self.ocupacoes_por_boca[boca] = [
            (oid, aid, qtd, ini, fim, chama, pressao)
            for (oid, aid, qtd, ini, fim, chama, pressao) in self.ocupacoes_por_boca[boca]
            if not (aid == atividade_id and oid == ordem_id)
        ]
        depois = len(self.ocupacoes_por_boca[boca])
        if antes != depois:
            logger.info(f"🟩 Liberou atividade {atividade_id} da ordem {ordem_id} da boca {boca + 1} no fogão {self.nome}.")

    def liberar_todas_bocas(self):
        total = sum(len(ocupacoes) for ocupacoes in self.ocupacoes_por_boca)
        self.ocupacoes_por_boca = [[] for _ in range(self.numero_bocas)]
        logger.info(f"🟩 Liberou todas as {total} ocupações do fogão {self.nome}.")

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info(f"📅 Agenda do {self.nome}")
        logger.info("==============================================")

        todas_ocupacoes = []
        for boca_idx, ocupacoes in enumerate(self.ocupacoes_por_boca):
            for (ordem_id, atividade_id, quantidade, inicio, fim, tipo_chama, pressoes) in ocupacoes:
                todas_ocupacoes.append({
                    "boca": boca_idx + 1,
                    "ordem_id": ordem_id,
                    "atividade_id": atividade_id,
                    "quantidade": quantidade,
                    "inicio": inicio,
                    "fim": fim,
                    "chama": tipo_chama,
                    "pressoes": pressoes
                })

        todas_ocupacoes.sort(key=lambda o: (o["ordem_id"], o["atividade_id"], o["boca"]))

        for o in todas_ocupacoes:
            pressoes_formatadas = ", ".join([p.value for p in o["pressoes"]])
            logger.info(
                f"🔥 Ordem {o['ordem_id']} | Atividade {o['atividade_id']} | Boca: {o['boca']} "
                f"| Quantidade: {o['quantidade']}g | {o['inicio'].strftime('%H:%M')} → {o['fim'].strftime('%H:%M')} "
                f"| Chama: {o['chama'].value} | Pressão: {pressoes_formatadas}"
            )
