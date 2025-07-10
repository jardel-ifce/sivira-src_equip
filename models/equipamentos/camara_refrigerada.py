from models.equipamentos.equipamento import Equipamento
from enums.producao.tipo_setor import TipoSetor
from enums.equipamentos.tipo_equipamento import TipoEquipamento
from typing import List, Tuple, Optional
from datetime import datetime
from utils.logs.logger_factory import setup_logger

logger = setup_logger('CamaraRefrigerada')


class CamaraRefrigerada(Equipamento):
    """
    🧊 Representa uma Câmara Refrigerada com controle de ocupação
    por caixas ou níveis de tela, considerando períodos de tempo e controle de temperatura.
    ✔️ Permite múltiplas alocações simultâneas, com registro de tempo e temperatura.
    ✔️ Controle de temperatura com faixa mínima e máxima.
    ✔️ Ocupação por caixas de 30kg ou níveis de tela.
    """

    # ============================================
    # 🔧 Inicialização
    # ============================================
    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        capacidade_niveis_tela: int,
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

        self.capacidade_niveis_tela = capacidade_niveis_tela
        self.capacidade_caixa_30kg = capacidade_caixa_30kg

        self.ocupacao_niveis: List[Tuple[int, datetime, datetime]] = []
        self.ocupacao_caixas: List[Tuple[int, datetime, datetime]] = []

        self.faixa_temperatura_min = faixa_temperatura_min
        self.faixa_temperatura_max = faixa_temperatura_max
        self.faixa_temperatura_atual = None

        # Ocupações: (ordem_id, pedido_id, atividade_id, quantidade, inicio, fim, temperatura)
        self.ocupacoes: List[Tuple[int, int, int, int, datetime, datetime, Optional[int]]] = []

    # ==========================================================
    # 🌡️ Controle de Temperatura
    # ==========================================================
    def verificar_compatibilidade_de_temperatura(
        self,
        inicio: datetime,
        fim: datetime,
        temperatura_desejada: int
    ) -> bool:
        """
        ✅ Verifica se já existe uma ocupação com temperatura diferente no intervalo fornecido.
        Se houver incompatibilidade de temperatura, retorna False.
        Caso contrário, retorna True.
        """
        for ocupacao in self.ocupacoes:
            if len(ocupacao) != 7:
                logger.warning(f"⚠️ Ocupação malformada em {self.nome}: {ocupacao}")
                continue

            _, _, _, _, ocup_inicio, ocup_fim, temperatura_configurada = ocupacao

            sobrepoe = not (fim <= ocup_inicio or inicio >= ocup_fim)
            temperaturas_incompativeis = temperatura_configurada != temperatura_desejada

            if sobrepoe and temperaturas_incompativeis:
                logger.info(
                    f"❌ Temperatura incompatível em {self.nome} entre "
                    f"{ocup_inicio.strftime('%H:%M')} e {ocup_fim.strftime('%H:%M')}. "
                    f"Esperado: {temperatura_desejada}°C | Já configurado: {temperatura_configurada}°C"
                )
                return False

        return True


    def selecionar_faixa_temperatura(
        self,
        temperatura_desejada: int,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        # Se já está na temperatura desejada, não precisa trocar
        if self.faixa_temperatura_atual == temperatura_desejada and self.faixa_temperatura_atual is not None:
            return True

        # Verifica se há ocupações planejadas no mesmo intervalo (colisão)
        ocupacoes_ativas = [
            (qtd, ini, f) for (qtd, ini, f) in self.ocupacao_caixas + self.ocupacao_niveis
            if not (fim <= ini or inicio >= f)
        ]

        if ocupacoes_ativas:
            logger.warning(
                f"⚠️ Não é possível ajustar a temperatura da {self.nome} para {temperatura_desejada}°C. "
                f"Temperatura atual: {self.faixa_temperatura_atual}°C, há ocupações no período de "
                f"{inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')}."
            )
            return False

        self.faixa_temperatura_atual = temperatura_desejada
        logger.info(
            f"🌡️ Câmara {self.nome} estava sem ocupações no período. Temperatura ajustada para {temperatura_desejada}°C "
            f"para {inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')}."
        )
        return True

    # ==========================================================
    # ✅ Validações
    # ==========================================================
    def verificar_disponibilidade(
        self,
        quantidade: int,
        inicio: datetime,
        fim: datetime,
        temperatura: Optional[int] = None
    ) -> bool:
        """
        🔍 Verifica se há disponibilidade na câmara para a quantidade informada,
        na janela de tempo especificada e com compatibilidade de temperatura.
        Considera o tipo de ocupação mais adequado com base na configuração atual.
        """
        # Verifica compatibilidade de temperatura
        if temperatura is not None and not self.verificar_compatibilidade_de_temperatura(inicio, fim, temperatura):
            logger.info(f"❌ Temperatura incompatível na {self.nome}.")
            return False

        # Tenta primeiro por caixas
        if self.verificar_espaco_caixas(quantidade, inicio, fim):
            return True

        # Tenta por níveis de tela
        if self.verificar_espaco_niveis(quantidade, inicio, fim):
            return True

        logger.info(f"❌ Sem espaço na {self.nome} para {quantidade} unidades entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}.")
        return False

    def verificar_espaco_caixas(self, quantidade_caixas: int, inicio: datetime, fim: datetime) -> bool:
        ocupadas = sum(
            qtd for (qtd, ini, f) in self.ocupacao_caixas
            if not (fim <= ini or inicio >= f)
        )
        return (ocupadas + quantidade_caixas) <= self.capacidade_caixa_30kg
    
    def verificar_espaco_niveis(self, quantidade: int, inicio: datetime, fim: datetime) -> bool:
        ocupadas = sum(
            qtd for (qtd, ini, f) in self.ocupacao_niveis
            if not (fim <= ini or inicio >= f)
        )
        return (ocupadas + quantidade) <= self.capacidade_niveis_tela
    
    # ==========================================================
    # 📦 | 🗂️  Ocupação
    # ==========================================================
    def ocupar(self, ordem_id: int, pedido_id, atividade_id: int, quantidade: int, inicio: datetime, fim: datetime):
        self.ocupacoes.append((ordem_id, pedido_id, atividade_id, quantidade, inicio, fim, self.faixa_temperatura_atual))
        logger.info(
            f"🧊 Ocupação registrada na {self.nome} | "
            f"Ordem {ordem_id} | Pedido {pedido_id} | Atividade {atividade_id} | "
            f"{quantidade} unidades | {inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')} | "
            f"Temperatura: {self.faixa_temperatura_atual}°C"
        )
        return True

    # ==========================================================
    # 📦 Ocupação por Caixas
    # ==========================================================
    def ocupar_caixas(self, ordem_id: int, pedido_id: int, atividade_id: int, quantidade: int, inicio: datetime, fim: datetime) -> bool:
        if not self.verificar_espaco_caixas(quantidade, inicio, fim):
            return False
        self.ocupacao_caixas.append((quantidade, inicio, fim))
        self.ocupar(ordem_id, pedido_id, atividade_id, quantidade, inicio, fim)
        return True

    # ==========================================================
    # 🗂️ Ocupação por Níveis
    # ==========================================================
    def ocupar_niveis(self, ordem_id: int, pedido_id: int, atividade_id: int, quantidade: int, inicio: datetime, fim: datetime) -> bool:
        if not self.verificar_espaco_niveis(quantidade, inicio, fim):
            return False
        self.ocupacao_niveis.append((quantidade, inicio, fim))
        self.ocupar(ordem_id, pedido_id, atividade_id, quantidade, inicio, fim)
        return True

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, ordem_id: int, pedido_id: int, atividade_id: int):
        """
        🔓 Libera ocupações específicas da atividade.
        """
        self.ocupacoes = [
            (oid, pid, aid, qtd, ini, fim, temp)
            for (oid, pid, aid, qtd, ini, fim, temp) in self.ocupacoes
            if not (aid == atividade_id and pid == pedido_id and oid == ordem_id)
        ]

        self.ocupacao_niveis = [
            (qtd, ini, fim)
            for (qtd, ini, fim) in self.ocupacao_niveis
            if not any(
                aid == atividade_id and pid == pedido_id and oid == ordem_id and qtd == qtd and ini == ini and fim == fim
                for (oid, aid, pid, _, ini, fim, _) in self.ocupacoes
            )
        ]

        self.ocupacao_caixas = [
            (qtd, ini, fim)
            for (qtd, ini, fim) in self.ocupacao_caixas
            if not any(
                aid == atividade_id and pid == pedido_id and oid == ordem_id and qtd == qtd and ini == ini and fim == fim
                for (oid, aid, pid, _, ini, fim, _) in self.ocupacoes
            )
        ]

        logger.info(f"🔓 Liberadas ocupações da atividade {atividade_id} da ordem {ordem_id} e pedido {pedido_id} na {self.nome}.")
   
    def liberar_por_pedido(self, ordem_id: int, pedido_id: int):
        """
        🔓 Libera todas as ocupações do pedido especificado (dentro da ordem),
        incluindo caixas, níveis e log de temperatura.
        """
        self.ocupacoes = [
            (oid, pid, aid, qtd, ini, fim, temp)
            for (oid, pid, aid, qtd, ini, fim, temp) in self.ocupacoes
            if not (oid == ordem_id and pid == pedido_id)
        ]

        self.ocupacao_niveis = [
            (qtd, ini, fim)
            for (qtd, ini, fim) in self.ocupacao_niveis
            if not any(
                oid == ordem_id and pid == pedido_id and qtd == qtd and ini == ini and fim == fim
                for (oid, pid, _, _, ini, fim, _) in self.ocupacoes
            )
        ]

        self.ocupacao_caixas = [
            (qtd, ini, fim)
            for (qtd, ini, fim) in self.ocupacao_caixas
            if not any(
                oid == ordem_id and pid == pedido_id and qtd == qtd and ini == ini and fim == fim
                for (oid, pid, _, _, ini, fim, _) in self.ocupacoes
            )
        ]

        logger.info(f"📦 Liberadas todas as ocupações do pedido {pedido_id} da ordem {ordem_id} na {self.nome}.")

    def liberar_por_ordem(self, ordem_id: int):
        """
        🔓 Libera todas as ocupações da ordem especificada, incluindo caixas, níveis e log de temperatura.
        """
        self.ocupacoes = [
            (oid, pid, aid, qtd, ini, fim, temp)
            for (oid, pid, aid, qtd, ini, fim, temp) in self.ocupacoes
            if not oid == ordem_id
        ]

        self.ocupacao_niveis = [
            (qtd, ini, fim)
            for (qtd, ini, fim) in self.ocupacao_niveis
            if not any(
                oid == ordem_id and qtd == qtd and ini == ini and fim == fim
                for (oid, _, _, _, ini, fim, _) in self.ocupacoes
            )
        ]

        self.ocupacao_caixas = [
            (qtd, ini, fim)
            for (qtd, ini, fim) in self.ocupacao_caixas
            if not any(
                oid == ordem_id and qtd == qtd and ini == ini and fim == fim
                for (oid, _, _, _, ini, fim, _) in self.ocupacoes
            )
        ]

        logger.info(f"🧊 Liberadas todas as ocupações da ordem {ordem_id} na {self.nome}.")


    def liberar_todas_ocupacoes(self):
        self.ocupacao_niveis.clear()
        self.ocupacao_caixas.clear()
        self.ocupacoes.clear()

    def liberar_intervalo(self, inicio: datetime, fim: datetime):
        self.ocupacao_niveis = [
            (qtd, ini, f) for (qtd, ini, f) in self.ocupacao_niveis
            if not (ini >= inicio and f <= fim)
        ]
        self.ocupacao_caixas = [
            (qtd, ini, f) for (qtd, ini, f) in self.ocupacao_caixas
            if not (ini >= inicio and f <= fim)
        ]
        self.ocupacoes = [
            (oid, aid, qtd, ini, f, temp)
            for (oid, aid, qtd, ini, f, temp) in self.ocupacoes
            if not (ini >= inicio and f <= fim)
        ]

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info(f"==============================================")
        logger.info(f"📅 Agenda da {self.nome}")
        logger.info(f"==============================================")

        if not self.ocupacoes:
            logger.info("🔹 Nenhuma ocupação registrada.")
            return

        for (ordem_id, pedido_id, atividade_id, quantidade, inicio, fim, temp) in self.ocupacoes:
            tipo = "Caixas" if (quantidade, inicio, fim) in self.ocupacao_caixas else "Níveis Tela"
            logger.info(
                f"🧊 Ordem {ordem_id} | Pedido {pedido_id} | Atividade {atividade_id} | {tipo}: {quantidade} unidades | "
                f"{inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')} | Temperatura: {temp}°C"
            )
