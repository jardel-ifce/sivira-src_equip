from models.equipamentos.equipamento import Equipamento
from enums.producao.tipo_setor import TipoSetor
from enums.equipamentos.tipo_equipamento import TipoEquipamento
from typing import List, Tuple, Optional
from datetime import datetime
from utils.logs.logger_factory import setup_logger

logger = setup_logger('Freezer')


class Freezer(Equipamento):
    """
    ❄️ Representa um Freezer com controle de ocupação exclusivamente por caixas de 30kg,
    considerando períodos de tempo e controle de temperatura.
    ✔️ Capacidade de caixas de 30kg.
    ✔️ Controle de temperatura com faixa mínima e máxima.
    ✔️ Ocupação exclusiva por caixa, com sobreposição de atividades, caso temperatura seja compatível.
    """

    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        capacidade_caixa_30kg: int,
        faixa_temperatura_min: int,
        faixa_temperatura_max: int
    ):
        super().__init__(
            id=id,
            nome=nome,
            tipo_equipamento=TipoEquipamento.REFRIGERACAO_CONGELAMENTO,
            setor=setor,
            numero_operadores=0,
            status_ativo=True
        )

        self.capacidade_caixa_30kg = capacidade_caixa_30kg

        # 📦 Ocupações: (ordem_id, pedido_id, quantidade, inicio, fim)
        self.ocupacao_caixas: List[Tuple[int, int, datetime, datetime]] = []  
        
        # 📦 Ocupações: (ordem_id, pedido_id, atividade_id, quantidade, inicio, fim, temperatura)
        self.ocupacoes: List[Tuple[int, int, int, int, datetime, datetime, Optional[int]]] = []  

        self.faixa_temperatura_min = faixa_temperatura_min
        self.faixa_temperatura_max = faixa_temperatura_max
        self.faixa_temperatura_atual = None

    # ==========================================================
    # 🌡️ Validação de Temperatura
    # ==========================================================
    def verificar_compatibilidade_de_temperatura(
        self,
        inicio: datetime,
        fim: datetime,
        temperatura_desejada: int
    ) -> bool:
        conflitos = [
            temp for (_, _, _, _, ini, f, temp) in self.ocupacoes
            if not (fim <= ini or inicio >= f)
        ]
        return all(temp == temperatura_desejada for temp in conflitos) if conflitos else True

    def selecionar_faixa_temperatura(
        self,
        temperatura_desejada: int,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        # Se já está na temperatura desejada, não precisa alterar
        if self.faixa_temperatura_atual == temperatura_desejada and self.faixa_temperatura_atual is not None:
            return True

        # Verifica se há ocupações planejadas no mesmo intervalo (colisão)
        ocupacoes_ativas = [
            (_, _, qtd, ini, f) for (_, _, qtd, ini, f) in self.ocupacao_caixas
            if not (fim <= ini or inicio >= f)
        ]

        if ocupacoes_ativas:
            logger.warning(
                f"⚠️ Não é possível ajustar a temperatura do {self.nome} para {temperatura_desejada}°C. "
                f"Temperatura atual: {self.faixa_temperatura_atual}°C, há ocupações no período "
                f"{inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')}."
            )
            return False

        self.faixa_temperatura_atual = temperatura_desejada
        logger.info(
            f"🌡️ Freezer {self.nome} estava vazio no período {inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')}. "
            f"Temperatura ajustada para {temperatura_desejada}°C."
        )
        return True

    # ==========================================================
    # ✅ Validações
    # ==========================================================
    def verificar_espaco_caixas(self, quantidade_caixas: int, inicio: datetime, fim: datetime) -> bool:
        ocupadas = sum(
            qtd for (_, _, qtd, ini, f) in self.ocupacao_caixas
            if not (fim <= ini or inicio >= f)
        )
        return (ocupadas + quantidade_caixas) <= self.capacidade_caixa_30kg

    # ==========================================================
    # 📦 Ocupação por caixas
    # ==========================================================
    def ocupar_caixas(
        self,
        ordem_id: int,
        pedido_id: int,
        atividade_id: int,
        quantidade: int,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        if not self.verificar_espaco_caixas(quantidade, inicio, fim):
            return False

        self.ocupacao_caixas.append((quantidade, inicio, fim, ordem_id))
        self.ocupacoes.append((ordem_id, pedido_id, atividade_id, quantidade, inicio, fim, self.faixa_temperatura_atual))

        logger.info(
            f"📦 {self.nome} alocado para Atividade {atividade_id} | Ordem {ordem_id} | Pedido {pedido_id} "
            f"| Caixas: {quantidade} | {inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')} "
            f"| Temperatura: {self.faixa_temperatura_atual}°C"
        )
        return True

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade_id: int, pedido_id: int, ordem_id: int, ):

        antes = len(self.ocupacoes)
        self.ocupacoes = [
            (oid, pid, aid, qtd, ini, fim, temp)
            for (oid, pid, aid, qtd, ini, fim, temp) in self.ocupacoes
            if not (aid == atividade_id and pid == pedido_id and oid == ordem_id)
        ]

        self.ocupacao_caixas = [
            (oid, pid, qtd, ini, fim)
            for (oid, pid, qtd, ini, fim) in self.ocupacao_caixas
            if not (oid == ordem_id and pid == pedido_id)
        ]
        depois = antes - len(self.ocupacoes)
        if depois > 0:
            logger.info(
                f"🔓 Liberadas {depois} ocupações do Freezer {self.nome} "
                f"para Atividade {atividade_id}, Pedido {pedido_id}, Ordem {ordem_id}."
            )
        else:
            logger.info(
                f"ℹ️ Nenhuma ocupação do Freezer {self.nome} foi liberada "
                f"para Atividade {atividade_id}, Pedido {pedido_id}, Ordem {ordem_id}."
            )

    def liberar_por_pedido(self, pedido_id: int, ordem_id: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            (oid, pid, aid, qtd, ini, fim, temp)
            for (oid, pid, aid, qtd, ini, fim, temp) in self.ocupacoes
            if not (pid == pedido_id and oid == ordem_id)
        ]

        self.ocupacao_caixas = [
            (oid, pid, qtd, ini, fim)
            for (oid, pid, qtd, ini, fim) in self.ocupacao_caixas
            if not (oid == ordem_id and pid == pedido_id)
        ]
        depois = antes - len(self.ocupacoes)
        if depois > 0:
            logger.info(
                f"🔓 Liberadas {depois} ocupações do Freezer {self.nome} "
                f"para Pedido {pedido_id}, Ordem {ordem_id}."
            )
        else:
            logger.info(
                f"ℹ️ Nenhuma ocupação do Freezer {self.nome} foi liberada "
                f"para Pedido {pedido_id}, Ordem {ordem_id}."
            )

    def liberar_por_ordem(self, ordem_id: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            (oid, pid, aid, qtd, ini, fim, temp)
            for (oid, pid, aid, qtd, ini, fim, temp) in self.ocupacoes
            if not (oid == ordem_id)
        ]

        self.ocupacao_caixas = [
            (oid, pid, qtd, ini, fim)
            for (oid, pid, qtd, ini, fim) in self.ocupacao_caixas
            if not (oid == ordem_id)
        ]
        depois = antes - len(self.ocupacoes)
        if depois > 0:
            logger.info(
                f"🔓 Liberadas {depois} ocupações do Freezer {self.nome} "
                f"para Ordem {ordem_id}."
            )
        else:
            logger.info(
                f"ℹ️ Nenhuma ocupação do Freezer {self.nome} foi liberada "
                f"para Ordem {ordem_id}."
            )

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        self.ocupacoes = [
            (oid, pid, aid, qtd, ini, fim, temp)
            for (oid, pid, aid, qtd, ini, fim, temp) in self.ocupacoes if fim > horario_atual
        ]
        self.ocupacao_caixas = [
            (oid, pid, qtd, ini, fim)
            for (oid, pid, qtd, ini, fim) in self.ocupacao_caixas if fim > horario_atual
        ]

    def liberar_todas_ocupacoes(self):
        self.ocupacoes.clear()
        self.ocupacao_caixas.clear()

    def liberar_por_intervalo(self, inicio: datetime, fim: datetime):
        self.ocupacoes = [
            (oid, pid, aid, qtd, ini, f, temp)
            for (oid, pid,  aid, qtd, ini, f, temp) in self.ocupacoes
            if not (ini >= inicio and f <= fim)
        ]
        self.ocupacao_caixas = [
            (oid, pid, qtd, ini, f)
            for (oid, pid, qtd, ini, f) in self.ocupacao_caixas
            if not (ini >= inicio and f <= fim)
        ]

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info(f"📅 Agenda do {self.nome}")
        logger.info("==============================================")

        if not self.ocupacoes:
            logger.info("🔹 Nenhuma ocupação registrada.")
            return

        for (ordem_id, pedido_id,atividade_id, quantidade, inicio, fim, temp) in self.ocupacoes:
            logger.info(
                f"📦 Ordem {ordem_id} | Pedido {pedido_id} | Atividade {atividade_id} | Caixas: {quantidade} | "
                f"{inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')} | Temp: {temp}°C"
            )

