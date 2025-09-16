from models.equipamentos.equipamento import Equipamento
from enums.equipamentos.tipo_equipamento import TipoEquipamento
from enums.producao.tipo_setor import TipoSetor
from enums.equipamentos.tipo_chama import TipoChama
from enums.equipamentos.tipo_pressao_chama import TipoPressaoChama
from typing import List, Tuple, Optional, Set
from datetime import datetime
from utils.logs.logger_factory import setup_logger
from utils.logs.registrador_restricoes import RegistradorRestricoes
from utils.logs.logger_ocupacao_detalhada import logger_ocupacao_detalhada

logger = setup_logger('Fogao')
registrador_restricoes = RegistradorRestricoes()


class Fogao(Equipamento):
    """
    🔥 Fogão com controle de ocupação por boca individual.
    ✔️ Suporta múltiplas chamas e pressões configuráveis.
    ✔️ Capacidade por boca validada por gramas.
    ✔️ Ocupação com soma de quantidades para mesmo id_item por boca.
    ✔️ Capacidade validada por peso com intervalos flexíveis.
    ✔️ Gestor controla capacidades via JSON.
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
        capacidade_por_boca_gramas_min: float,
        capacidade_por_boca_gramas_max: float,
        numero_bocas: int,
        chamas_suportadas: List[TipoChama],
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

        self.capacidade_por_boca_gramas_min = capacidade_por_boca_gramas_min
        self.capacidade_por_boca_gramas_max = capacidade_por_boca_gramas_max
        self.numero_bocas = numero_bocas
        self.chamas_suportadas = chamas_suportadas
        self.pressao_chamas_suportadas = pressao_chamas_suportadas

        # 🔥 Ocupações por boca: (id_ordem, id_pedido, id_atividade, id_item, quantidade_alocada, tipo_chama, pressoes_chama, inicio, fim)
        self.ocupacoes_por_boca: List[List[Tuple[int, int, int, int, float, TipoChama, List[TipoPressaoChama], datetime, datetime]]] = [
            [] for _ in range(numero_bocas)
        ]

        # 🚨 Sistema de restrições para capacidade mínima (igual ao HotMix)
        self.restricoes_registradas: List[Tuple[int, int, int, int, float, datetime, datetime, str]] = []

        # 🆕 Cache para evitar registros duplicados
        self.restricoes_ja_registradas: Set[Tuple[int, int, int]] = set()  # (id_ordem, id_pedido, id_atividade)

    # ==========================================================
    # ✅ Validações - ATUALIZADAS PARA SOBREPOSIÇÃO POR ITEM
    # ==========================================================
    def boca_disponivel(self, boca_index: int, inicio: datetime, fim: datetime) -> bool:
        """
        Método original mantido para compatibilidade.
        Verifica disponibilidade sem considerar mesmo id_item.
        """
        if boca_index < 0 or boca_index >= self.numero_bocas:
            return False
            
        for ocupacao in self.ocupacoes_por_boca[boca_index]:
            if not (fim <= ocupacao[7] or inicio >= ocupacao[8]):  # há sobreposição
                return False
        return True

    def boca_disponivel_para_item(self, boca_index: int, inicio: datetime, fim: datetime, id_item: int) -> bool:
        """
        Verifica se uma boca pode receber uma nova ocupação do item especificado.
        Para o mesmo item, sempre permite (validação de capacidade será feita separadamente).
        Para itens diferentes, não permite sobreposição.
        """
        if boca_index < 0 or boca_index >= self.numero_bocas:
            return False
            
        for ocupacao in self.ocupacoes_por_boca[boca_index]:
            # Se é o mesmo item, sempre permite (capacidade será validada depois)
            if ocupacao[3] == id_item:  # ocupacao[3] é id_item
                continue
                
            # Para itens diferentes, não pode haver sobreposição
            if not (fim <= ocupacao[7] or inicio >= ocupacao[8]):
                logger.warning(
                    f"⚠️ {self.nome} Boca {boca_index + 1} ocupada por item diferente (ID: {ocupacao[3]}) "
                    f"entre {ocupacao[7].strftime('%H:%M')} e {ocupacao[8].strftime('%H:%M')}."
                )
                return False
        
        return True

    def validar_capacidade_boca(self, quantidade: float) -> bool:
        """
        Valida se a quantidade está dentro da capacidade da boca.
        ✅ SISTEMA SIMPLIFICADO: Aceita quantidades pequenas e registra restrições automaticamente.
        """
        # Verifica apenas se excede o máximo (restrição de segurança)
        if quantidade > self.capacidade_por_boca_gramas_max:
            logger.warning(
                f"❌ Quantidade {quantidade}g excede capacidade máxima da boca "
                f"({self.capacidade_por_boca_gramas_max}g) do {self.nome}"
            )
            return False

        # ✅ ACEITA QUANTIDADES PEQUENAS: Restrição registrada automaticamente no nível superior
        if quantidade < self.capacidade_por_boca_gramas_min:
            logger.debug(f"🔧 {self.nome} - Quantidade {quantidade}g abaixo do mínimo {self.capacidade_por_boca_gramas_min}g (aceito, restrição registrada)")

        return True

    def _registrar_restricao_capacidade_minima(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade: float,
        inicio: datetime,
        fim: datetime,
        motivo: str
    ) -> None:
        """Registra uma restrição de capacidade mínima para análise posterior (apenas uma vez por atividade)."""
        # 🆕 CACHE: Evita registros duplicados
        chave_restricao = (id_ordem, id_pedido, id_atividade)
        if chave_restricao in self.restricoes_ja_registradas:
            logger.debug(f"🔧 Restrição já registrada para atividade {id_atividade} - ignorando duplicação")
            return

        self.restricoes_ja_registradas.add(chave_restricao)

        restricao = (id_ordem, id_pedido, id_atividade, id_item, quantidade, inicio, fim, motivo)
        self.restricoes_registradas.append(restricao)

        # 🆕 INTEGRAÇÃO COM SISTEMA CENTRALIZADO (igual ao HotMix)
        registrador_restricoes.registrar_restricao(
            id_ordem=id_ordem,
            id_pedido=id_pedido,
            id_atividade=id_atividade,
            id_item=id_item,
            equipamento_nome=self.nome,
            capacidade_atual=quantidade,
            capacidade_minima=self.capacidade_por_boca_gramas_min,
            inicio=inicio,
            fim=fim,
            detalhes_extras={
                "tipo_restricao": "CAPACIDADE_MINIMA",
                "motivo_especifico": motivo
            }
        )

        logger.warning(
            f"🚨 RESTRIÇÃO REGISTRADA - {self.nome} | "
            f"Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade} | Item {id_item} | "
            f"Quantidade {quantidade}g | {inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')} | "
            f"Motivo: {motivo}"
        )

    def obter_quantidade_maxima_item_boca_periodo(self, boca_index: int, id_item: int, inicio: datetime, fim: datetime) -> float:
        """
        Calcula a quantidade máxima de um item que estará sendo processado
        simultaneamente em uma boca durante qualquer momento do período especificado.
        """
        if boca_index < 0 or boca_index >= self.numero_bocas:
            return 0.0
            
        # Lista todos os pontos temporais relevantes (inícios e fins de ocupações)
        pontos_temporais = set()
        ocupacoes_item = []
        
        # Coleta ocupações do mesmo item na boca
        for ocupacao in self.ocupacoes_por_boca[boca_index]:
            if ocupacao[3] == id_item:  # mesmo id_item
                ocupacoes_item.append(ocupacao)
                pontos_temporais.add(ocupacao[7])  # início
                pontos_temporais.add(ocupacao[8])  # fim
        
        # Adiciona os pontos do novo período
        pontos_temporais.add(inicio)
        pontos_temporais.add(fim)
        
        # Ordena os pontos temporais
        pontos_ordenados = sorted(pontos_temporais)
        
        quantidade_maxima = 0.0
        
        # Verifica a quantidade em cada intervalo
        for i in range(len(pontos_ordenados) - 1):
            momento_inicio = pontos_ordenados[i]
            momento_fim = pontos_ordenados[i + 1]
            momento_meio = momento_inicio + (momento_fim - momento_inicio) / 2
            
            # Soma quantidade de todas as ocupações ativas neste momento
            quantidade_momento = 0.0
            
            # Verifica ocupações existentes
            for ocupacao in ocupacoes_item:
                if ocupacao[7] <= momento_meio < ocupacao[8]:  # ocupação ativa neste momento
                    quantidade_momento += ocupacao[4]  # quantidade_alocada
            
            quantidade_maxima = max(quantidade_maxima, quantidade_momento)
        
        return quantidade_maxima

    def validar_nova_ocupacao_item_boca(self, boca_index: int, id_item: int, quantidade_nova: float,
                                       inicio: datetime, fim: datetime) -> bool:
        """
        Simula uma nova ocupação em uma boca e verifica se a capacidade máxima será respeitada
        em todos os momentos de sobreposição.
        """
        if boca_index < 0 or boca_index >= self.numero_bocas:
            return False
            
        # Coleta todos os pontos temporais relevantes
        pontos_temporais = set()
        ocupacoes_item = []
        
        for ocupacao in self.ocupacoes_por_boca[boca_index]:
            if ocupacao[3] == id_item:
                ocupacoes_item.append(ocupacao)
                pontos_temporais.add(ocupacao[7])  # início
                pontos_temporais.add(ocupacao[8])  # fim
        
        # Adiciona pontos da nova ocupação
        pontos_temporais.add(inicio)
        pontos_temporais.add(fim)
        
        # Ordena pontos temporais
        pontos_ordenados = sorted(pontos_temporais)
        
        # Verifica quantidade em cada intervalo
        for i in range(len(pontos_ordenados) - 1):
            momento_inicio = pontos_ordenados[i]
            momento_fim = pontos_ordenados[i + 1]
            momento_meio = momento_inicio + (momento_fim - momento_inicio) / 2
            
            quantidade_total = 0.0
            
            # Soma ocupações existentes ativas neste momento
            for ocupacao in ocupacoes_item:
                if ocupacao[7] <= momento_meio < ocupacao[8]:
                    quantidade_total += ocupacao[4]  # quantidade_alocada
            
            # Soma nova ocupação se ativa neste momento
            if inicio <= momento_meio < fim:
                quantidade_total += quantidade_nova
            
            # Verifica se excede capacidade
            if not self.validar_capacidade_boca(quantidade_total):
                logger.debug(
                    f"❌ {self.nome} Boca {boca_index + 1} | Item {id_item}: Capacidade excedida no momento {momento_meio.strftime('%H:%M')} "
                    f"({quantidade_total}g > {self.capacidade_por_boca_gramas_max}g)"
                )
                return False
        
        return True

    def esta_disponivel_para_item_no_periodo(self, id_item: int, inicio: datetime, fim: datetime) -> bool:
        """
        Verifica se há bocas disponíveis para processar um item específico usando janelas simultâneas.
        Implementação similar ao HotMix para consistência.
        """
        bocas_disponiveis = self.bocas_disponiveis_para_item_periodo(inicio, fim, id_item)
        if not bocas_disponiveis:
            return False

        # Se temos bocas disponíveis, verifica restrições de capacidade
        for boca_index in bocas_disponiveis:
            # Verifica se pode processar pelo menos a capacidade mínima
            # ✅ Sempre verifica disponibilidade (bypass implícito com registro de restrições)
            if self.capacidade_por_boca_gramas_min > 0:
                return True

        return False

    def obter_quantidade_maxima_item_periodo(self, id_item: int, inicio: datetime, fim: datetime) -> float:
        """
        Calcula a máxima quantidade de um item que pode ser processada simultaneamente
        considerando todas as bocas durante o período especificado.
        """
        quantidade_maxima_total = 0.0

        for boca_index in range(self.numero_bocas):
            quantidade_boca = self.obter_quantidade_maxima_item_boca_periodo(boca_index, id_item, inicio, fim)
            quantidade_maxima_total += quantidade_boca

        return quantidade_maxima_total

    def obter_capacidade_disponivel_item(self, id_item: int, inicio: datetime, fim: datetime) -> float:
        """
        Calcula a capacidade disponível total para um item em todas as bocas.
        """
        capacidade_total = 0.0

        bocas_disponiveis = self.bocas_disponiveis_para_item_periodo(inicio, fim, id_item)
        for boca_index in bocas_disponiveis:
            quantidade_atual = self.obter_quantidade_maxima_item_boca_periodo(boca_index, id_item, inicio, fim)
            capacidade_restante = self.capacidade_por_boca_gramas_max - quantidade_atual
            capacidade_total += max(0, capacidade_restante)

        return capacidade_total

    def validar_nova_ocupacao_item(
        self,
        id_item: int,
        quantidade: float,
        inicio: datetime,
        fim: datetime,
        id_ordem: int = 0,
        id_pedido: int = 0,
        id_atividade: int = 0
    ) -> bool:
        """
        Valida se uma nova ocupação pode ser alocada usando lógica de janelas simultâneas.
        VERSÃO PARA VERIFICAÇÃO DE VIABILIDADE: Não registra restrições.
        """
        # Segunda validação: verifica se há bocas disponíveis com capacidade
        bocas_disponiveis = self.bocas_disponiveis_para_item_periodo(inicio, fim, id_item)
        if not bocas_disponiveis:
            return False

        # Terceira validação: verifica se alguma boca pode acomodar a quantidade
        for boca_index in bocas_disponiveis:
            if self.validar_nova_ocupacao_item_boca(boca_index, id_item, quantidade, inicio, fim):
                return True

        # Se chegou aqui, nenhuma boca pode acomodar
        return False

    def validar_nova_ocupacao_item_com_restricoes(
        self,
        id_item: int,
        quantidade: float,
        inicio: datetime,
        fim: datetime,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int
    ) -> bool:
        """
        Valida nova ocupação E registra restrições quando necessário.
        VERSÃO PARA ALOCAÇÃO EFETIVA: Registra restrições.
        """
        # ✅ SISTEMA SIMPLIFICADO: Registra restrição automaticamente se abaixo do mínimo
        if quantidade < self.capacidade_por_boca_gramas_min:
            self._registrar_restricao_capacidade_minima(
                id_ordem, id_pedido, id_atividade, id_item, quantidade, inicio, fim,
                f"Quantidade {quantidade}g abaixo da capacidade mínima {self.capacidade_por_boca_gramas_min}g"
            )
            logger.warning(
                f"❌ {self.nome} - Quantidade {quantidade}g abaixo da capacidade mínima por boca ({self.capacidade_por_boca_gramas_min}g)"
            )
            # ✅ CONTINUA: Sistema aceita quantidades pequenas automaticamente

        # Segunda validação: verifica se há bocas disponíveis com capacidade
        bocas_disponiveis = self.bocas_disponiveis_para_item_periodo(inicio, fim, id_item)
        if not bocas_disponiveis:
            self._registrar_restricao_capacidade_minima(
                id_ordem, id_pedido, id_atividade, id_item, quantidade, inicio, fim,
                "Nenhuma boca disponível para o período"
            )
            return False

        # Terceira validação: verifica se alguma boca pode acomodar a quantidade
        for boca_index in bocas_disponiveis:
            if self.validar_nova_ocupacao_item_boca(boca_index, id_item, quantidade, inicio, fim):
                return True

        # Se chegou aqui, nenhuma boca pode acomodar
        capacidade_disponivel = self.obter_capacidade_disponivel_item(id_item, inicio, fim)
        self._registrar_restricao_capacidade_minima(
            id_ordem, id_pedido, id_atividade, id_item, quantidade, inicio, fim,
            f"Capacidade insuficiente: {quantidade}g solicitado > {capacidade_disponivel}g disponível"
        )
        return False

    def verificar_disponibilidade_boca(
        self,
        boca_index: int,
        quantidade: float,
        inicio: datetime,
        fim: datetime,
        id_item: int
    ) -> bool:
        """Verifica se é possível ocupar uma boca específica com os parâmetros dados para um item."""
        if not self.boca_disponivel_para_item(boca_index, inicio, fim, id_item):
            return False
        
        return self.validar_nova_ocupacao_item_boca(boca_index, id_item, quantidade, inicio, fim)

    # ==========================================================
    # 🔍 Consulta de Ocupação (para o Gestor) - ATUALIZADAS
    # ==========================================================
    def bocas_disponiveis_periodo(self, inicio: datetime, fim: datetime) -> List[int]:
        """
        Método original mantido para compatibilidade.
        Retorna lista de índices das bocas disponíveis no período (ocupação exclusiva).
        """
        return [
            i for i in range(self.numero_bocas)
            if self.boca_disponivel(i, inicio, fim)
        ]

    def bocas_disponiveis_para_item_periodo(self, inicio: datetime, fim: datetime, id_item: int) -> List[int]:
        """
        Retorna lista de índices das bocas disponíveis no período para um item específico.
        """
        return [
            i for i in range(self.numero_bocas)
            if self.boca_disponivel_para_item(i, inicio, fim, id_item)
        ]

    def quantidade_bocas_disponiveis(self, inicio: datetime, fim: datetime) -> int:
        """Retorna quantidade de bocas disponíveis no período."""
        return len(self.bocas_disponiveis_periodo(inicio, fim))

    def quantidade_bocas_disponiveis_para_item(self, inicio: datetime, fim: datetime, id_item: int) -> int:
        """Retorna quantidade de bocas disponíveis no período para um item específico."""
        return len(self.bocas_disponiveis_para_item_periodo(inicio, fim, id_item))

    def obter_ocupacoes_boca(self, boca_index: int) -> List[Tuple[int, int, int, int, float, TipoChama, List[TipoPressaoChama], datetime, datetime]]:
        """Retorna todas as ocupações de uma boca específica."""
        if boca_index < 0 or boca_index >= self.numero_bocas:
            return []
        return self.ocupacoes_por_boca[boca_index].copy()

    def obter_ocupacoes_periodo(self, inicio: datetime, fim: datetime) -> List[Tuple[int, int, int, int, float, TipoChama, List[TipoPressaoChama], datetime, datetime, int]]:
        """Retorna todas as ocupações que se sobrepõem ao período especificado, incluindo índice da boca."""
        ocupacoes_periodo = []
        for boca_index in range(self.numero_bocas):
            for ocupacao in self.ocupacoes_por_boca[boca_index]:
                if not (fim <= ocupacao[7] or inicio >= ocupacao[8]):  # há sobreposição temporal
                    # Adicionar índice da boca no final
                    ocupacoes_periodo.append((*ocupacao, boca_index))
        return ocupacoes_periodo

    def obter_status_bocas(self, momento: datetime) -> List[bool]:
        """Retorna status de ocupação de cada boca em um momento específico."""
        status = []
        for boca_index in range(self.numero_bocas):
            ocupada = any(
                ocupacao[7] <= momento < ocupacao[8]  # inicio <= momento < fim
                for ocupacao in self.ocupacoes_por_boca[boca_index]
            )
            status.append(ocupada)
        return status

    def obter_proxima_liberacao(self, boca_index: int, momento_atual: datetime) -> Optional[datetime]:
        """Retorna próximo horário de liberação de uma boca específica."""
        if boca_index < 0 or boca_index >= self.numero_bocas:
            return None
        
        proximas_liberacoes = [
            ocupacao[8]  # fim
            for ocupacao in self.ocupacoes_por_boca[boca_index]
            if ocupacao[8] > momento_atual
        ]
        
        return min(proximas_liberacoes) if proximas_liberacoes else None

    def obter_todas_ocupacoes(self) -> List[Tuple[int, int, int, int, float, TipoChama, List[TipoPressaoChama], datetime, datetime, int]]:
        """Retorna todas as ocupações do fogão com índice da boca."""
        todas_ocupacoes = []
        for boca_index in range(self.numero_bocas):
            for ocupacao in self.ocupacoes_por_boca[boca_index]:
                todas_ocupacoes.append((*ocupacao, boca_index))
        return todas_ocupacoes

    # ==========================================================
    # 🔄 Ocupação - ATUALIZADA COM VALIDAÇÃO POR ITEM
    # ==========================================================
    def ocupar_boca(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade_alocada: float,
        tipo_chama: TipoChama,
        pressoes_chama: List[TipoPressaoChama],
        inicio: datetime,
        fim: datetime,
        boca_index: Optional[int] = None
    ) -> bool:
        """
        Ocupa uma boca específica ou encontra automaticamente uma boca disponível.
        Agora com validação por item.
        
        Args:
            boca_index: Se fornecido, tenta ocupar boca específica. Se None, encontra automaticamente.
        """
        if boca_index is None:
            boca_index = self.encontrar_boca_para_ocupacao_item(inicio, fim, id_item)
            if boca_index is None:
                logger.warning(f"❌ Nenhuma boca disponível no {self.nome} entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')} para item {id_item}")
                return False

        return self.adicionar_ocupacao_boca(
            boca_index, id_ordem, id_pedido, id_atividade, id_item,
            quantidade_alocada, tipo_chama, pressoes_chama, inicio, fim
        )

    def adicionar_ocupacao_boca(
        self,
        boca_index: int,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade_alocada: float,
        tipo_chama: TipoChama,
        pressoes_chama: List[TipoPressaoChama],
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """Adiciona uma ocupação específica a uma boca específica com validação por item."""
        if boca_index < 0 or boca_index >= self.numero_bocas:
            logger.warning(f"❌ Índice de boca inválido: {boca_index}")
            return False

        # ✅ SISTEMA SIMPLIFICADO: Valida e registra restrições durante a alocação efetiva
        if not self.validar_nova_ocupacao_item_com_restricoes(
            id_item, quantidade_alocada, inicio, fim,
            id_ordem, id_pedido, id_atividade
        ):
            # ✅ Ainda assim aceita a alocação (sistema implícito)
            logger.debug(f"🔧 {self.nome} - Restrição registrada mas alocação aceita (bypass implícito)")
            # Nota: O método já registrou a restrição, agora continuamos com a alocação

        # Validação final de disponibilidade da boca específica
        if not self.verificar_disponibilidade_boca(boca_index, quantidade_alocada, inicio, fim, id_item):
            quantidade_atual = self.obter_quantidade_maxima_item_boca_periodo(boca_index, id_item, inicio, fim)
            logger.error(
                f"❌ {self.nome} Boca {boca_index + 1} | Item {id_item}: Nova quantidade {quantidade_alocada}g + "
                f"máximo atual {quantidade_atual}g excederia capacidade máxima ({self.capacidade_por_boca_gramas_max}g)"
            )
            return False

        self.ocupacoes_por_boca[boca_index].append(
            (id_ordem, id_pedido, id_atividade, id_item, quantidade_alocada, tipo_chama, pressoes_chama, inicio, fim)
        )

        # Log informativo
        quantidade_maxima_apos = self.obter_quantidade_maxima_item_boca_periodo(boca_index, id_item, inicio, fim) + quantidade_alocada
        pressoes_formatadas = ", ".join([p.value for p in pressoes_chama])
        logger.info(
            f"🔥 {self.nome} Boca {boca_index + 1} | Item {id_item}: Nova ocupação {quantidade_alocada}g "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} "
            f"(Pico máximo do item: {quantidade_maxima_apos}g) "
            f"(Ordem {id_ordem}, Pedido {id_pedido}, Atividade {id_atividade}) | "
            f"Chama: {tipo_chama.value} | Pressão: {pressoes_formatadas}"
        )
        return True

    def encontrar_boca_para_ocupacao_item(self, inicio: datetime, fim: datetime, id_item: int) -> Optional[int]:
        """Encontra a primeira boca disponível para ocupação de um item específico."""
        bocas_livres = self.bocas_disponiveis_para_item_periodo(inicio, fim, id_item)
        return bocas_livres[0] if bocas_livres else None

    def encontrar_boca_para_ocupacao(self, inicio: datetime, fim: datetime) -> Optional[int]:
        """Método original mantido para compatibilidade."""
        bocas_livres = self.bocas_disponiveis_periodo(inicio, fim)
        return bocas_livres[0] if bocas_livres else None

    def sobrescrever_ocupacao_boca(
        self,
        boca_index: int,
        ocupacoes: List[Tuple[int, int, int, int, float, TipoChama, List[TipoPressaoChama], datetime, datetime]]
    ) -> bool:
        """Sobrescreve completamente as ocupações de uma boca específica."""
        if boca_index < 0 or boca_index >= self.numero_bocas:
            logger.warning(f"❌ Índice de boca inválido: {boca_index}")
            return False

        self.ocupacoes_por_boca[boca_index] = ocupacoes.copy()
        
        logger.info(
            f"🔄 Ocupações da boca {boca_index + 1} do {self.nome} foram sobrescritas. "
            f"Total de ocupações: {len(ocupacoes)}"
        )
        return True

    def atualizar_ocupacao_especifica(
        self,
        boca_index: int,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        nova_quantidade: float,
        novo_tipo_chama: TipoChama,
        novas_pressoes: List[TipoPressaoChama],
        novo_inicio: datetime,
        novo_fim: datetime
    ) -> bool:
        """Atualiza uma ocupação específica de uma boca com validação por item."""
        if boca_index < 0 or boca_index >= self.numero_bocas:
            logger.warning(f"❌ Índice de boca inválido: {boca_index}")
            return False

        for i, ocupacao in enumerate(self.ocupacoes_por_boca[boca_index]):
            if ocupacao[0] == id_ordem and ocupacao[1] == id_pedido and ocupacao[2] == id_atividade:
                id_item = ocupacao[3]  # Mantém o id_item original
                
                # Remover ocupação atual temporariamente para validação
                ocupacao_original = self.ocupacoes_por_boca[boca_index].pop(i)
                
                # Validar nova configuração
                if not self.validar_nova_ocupacao_item_boca(boca_index, id_item, nova_quantidade, novo_inicio, novo_fim):
                    # Restaurar ocupação original se validação falhar
                    self.ocupacoes_por_boca[boca_index].insert(i, ocupacao_original)
                    return False

                # Aplicar atualização
                self.ocupacoes_por_boca[boca_index].insert(i, (
                    id_ordem, id_pedido, id_atividade, id_item, nova_quantidade, 
                    novo_tipo_chama, novas_pressoes, novo_inicio, novo_fim
                ))
                
                pressoes_formatadas = ", ".join([p.value for p in novas_pressoes])
                logger.info(
                    f"🔄 Ocupação atualizada no {self.nome} - Boca {boca_index + 1} | "
                    f"Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade} | Item {id_item} | "
                    f"Nova quantidade: {nova_quantidade:.2f}g | Chama: {novo_tipo_chama.value} | "
                    f"Pressão: {pressoes_formatadas} | {novo_inicio.strftime('%H:%M')} → {novo_fim.strftime('%H:%M')}"
                )
                return True

        logger.warning(
            f"❌ Ocupação não encontrada para atualizar no {self.nome} - Boca {boca_index + 1} | "
            f"Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade}"
        )
        return False

    # ==========================================================
    # 🔓 Liberação (métodos mantidos iguais)
    # ==========================================================
    def liberar_por_atividade(self, id_ordem: int, id_pedido: int, id_atividade: int):
        """Libera ocupações específicas por atividade."""
        total_liberadas = 0
        
        for boca_index in range(self.numero_bocas):
            antes = len(self.ocupacoes_por_boca[boca_index])
            self.ocupacoes_por_boca[boca_index] = [
                ocupacao for ocupacao in self.ocupacoes_por_boca[boca_index]
                if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido and ocupacao[2] == id_atividade)
            ]
            liberadas_boca = antes - len(self.ocupacoes_por_boca[boca_index])
            total_liberadas += liberadas_boca

        if total_liberadas > 0:
            logger.info(
                f"🔓 Liberadas {total_liberadas} ocupações do {self.nome} "
                f"para Atividade {id_atividade}, Pedido {id_pedido}, Ordem {id_ordem}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar no {self.nome} "
                f"para Atividade {id_atividade}, Pedido {id_pedido}, Ordem {id_ordem}."
            )

    def liberar_por_pedido(self, id_ordem: int, id_pedido: int):
        """Libera ocupações específicas por pedido."""
        total_liberadas = 0
        
        for boca_index in range(self.numero_bocas):
            antes = len(self.ocupacoes_por_boca[boca_index])
            self.ocupacoes_por_boca[boca_index] = [
                ocupacao for ocupacao in self.ocupacoes_por_boca[boca_index]
                if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido)
            ]
            liberadas_boca = antes - len(self.ocupacoes_por_boca[boca_index])
            total_liberadas += liberadas_boca

        if total_liberadas > 0:
            logger.info(
                f"🔓 Liberadas {total_liberadas} ocupações do {self.nome} "
                f"para Pedido {id_pedido}, Ordem {id_ordem}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar no {self.nome} "
                f"para Pedido {id_pedido}, Ordem {id_ordem}."
            )

    def liberar_por_ordem(self, id_ordem: int):
        """Libera ocupações específicas por ordem."""
        total_liberadas = 0
        
        for boca_index in range(self.numero_bocas):
            antes = len(self.ocupacoes_por_boca[boca_index])
            self.ocupacoes_por_boca[boca_index] = [
                ocupacao for ocupacao in self.ocupacoes_por_boca[boca_index]
                if ocupacao[0] != id_ordem
            ]
            liberadas_boca = antes - len(self.ocupacoes_por_boca[boca_index])
            total_liberadas += liberadas_boca

        if total_liberadas > 0:
            logger.info(
                f"🔓 Liberadas {total_liberadas} ocupações do {self.nome} "
                f"para Ordem {id_ordem}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar no {self.nome} "
                f"para Ordem {id_ordem}."
            )

    def liberar_por_item(self, id_item: int):
        """Libera ocupações vinculadas a um item específico."""
        total_liberadas = 0
        
        for boca_index in range(self.numero_bocas):
            antes = len(self.ocupacoes_por_boca[boca_index])
            self.ocupacoes_por_boca[boca_index] = [
                ocupacao for ocupacao in self.ocupacoes_por_boca[boca_index]
                if ocupacao[3] != id_item
            ]
            liberadas_boca = antes - len(self.ocupacoes_por_boca[boca_index])
            total_liberadas += liberadas_boca

        if total_liberadas > 0:
            logger.info(
                f"🔓 {self.nome} | Liberadas {total_liberadas} ocupações do item {id_item}."
            )
        else:
            logger.info(
                f"ℹ️ Nenhuma ocupação do {self.nome} estava associada ao item {id_item}."
            )

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        """Libera ocupações que já finalizaram."""
        total_liberadas = 0
        
        for boca_index in range(self.numero_bocas):
            antes = len(self.ocupacoes_por_boca[boca_index])
            self.ocupacoes_por_boca[boca_index] = [
                ocupacao for ocupacao in self.ocupacoes_por_boca[boca_index]
                if ocupacao[8] > horario_atual  # fim > horario_atual
            ]
            liberadas_boca = antes - len(self.ocupacoes_por_boca[boca_index])
            total_liberadas += liberadas_boca

        if total_liberadas > 0:
            logger.info(
                f"🟩 {self.nome} | Liberou {total_liberadas} ocupações finalizadas até {horario_atual.strftime('%H:%M')}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação finalizada encontrada para liberar no {self.nome} até {horario_atual.strftime('%H:%M')}."
            )
        return total_liberadas

    def liberar_todas_ocupacoes(self):
        """Limpa todas as ocupações de todas as bocas."""
        total = sum(len(ocupacoes) for ocupacoes in self.ocupacoes_por_boca)
        for boca_ocupacoes in self.ocupacoes_por_boca:
            boca_ocupacoes.clear()
        logger.info(f"🔓 Todas as {total} ocupações do {self.nome} foram removidas.")

    def liberar_por_intervalo(self, inicio: datetime, fim: datetime):
        """Libera ocupações que se sobrepõem ao intervalo especificado."""
        total_liberadas = 0
        
        for boca_index in range(self.numero_bocas):
            antes = len(self.ocupacoes_por_boca[boca_index])
            self.ocupacoes_por_boca[boca_index] = [
                ocupacao for ocupacao in self.ocupacoes_por_boca[boca_index]
                if not (ocupacao[7] < fim and ocupacao[8] > inicio)  # remove qualquer sobreposição
            ]
            liberadas_boca = antes - len(self.ocupacoes_por_boca[boca_index])
            total_liberadas += liberadas_boca

        if total_liberadas > 0:
            logger.info(
                f"🔓 Liberadas {total_liberadas} ocupações do {self.nome} entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar no {self.nome} entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
            )

    def liberar_boca_especifica(self, boca_index: int, id_ordem: int, id_pedido: int, id_atividade: int):
        """Libera ocupação específica de uma boca."""
        if boca_index < 0 or boca_index >= self.numero_bocas:
            logger.warning(f"❌ Índice de boca inválido: {boca_index}")
            return

        antes = len(self.ocupacoes_por_boca[boca_index])
        self.ocupacoes_por_boca[boca_index] = [
            ocupacao for ocupacao in self.ocupacoes_por_boca[boca_index]
            if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido and ocupacao[2] == id_atividade)
        ]
        liberadas = antes - len(self.ocupacoes_por_boca[boca_index])
        
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações da boca {boca_index + 1} do {self.nome} "
                f"para Atividade {id_atividade}, Pedido {id_pedido}, Ordem {id_ordem}."
            )

    # ==========================================================
    # 📅 Agenda e Relatórios (métodos mantidos iguais)
    # ==========================================================
    def mostrar_agenda(self):
        """Mostra agenda detalhada por boca."""
        logger.info("==============================================")
        logger.info(f"📅 Agenda do {self.nome}")
        logger.info("==============================================")

        tem_ocupacao = False
        for boca_index in range(self.numero_bocas):
            if self.ocupacoes_por_boca[boca_index]:
                tem_ocupacao = True
                logger.info(f"🔹 Boca {boca_index + 1}:")
                for ocupacao in self.ocupacoes_por_boca[boca_index]:
                    pressoes_formatadas = ", ".join([p.value for p in ocupacao[6]])
                    logger.info(
                        f"   🔥 Ordem {ocupacao[0]} | Pedido {ocupacao[1]} | Atividade {ocupacao[2]} | Item {ocupacao[3]} | "
                        f"{ocupacao[4]:.2f}g | Chama: {ocupacao[5].value} | Pressão: {pressoes_formatadas} | "
                        f"{ocupacao[7].strftime('%H:%M')} → {ocupacao[8].strftime('%H:%M')}"
                    )

        if not tem_ocupacao:
            logger.info("🔹 Nenhuma ocupação registrada em nenhuma boca.")

    def obter_estatisticas_uso(self, inicio: datetime, fim: datetime) -> dict:
        """Retorna estatísticas de uso do fogão no período."""
        total_ocupacoes = 0
        total_quantidade = 0.0
        bocas_utilizadas = 0
        tipos_chama_utilizados = set()
        pressoes_utilizadas = set()
        
        for boca_index in range(self.numero_bocas):
            ocupacoes_boca = []
            for ocupacao in self.ocupacoes_por_boca[boca_index]:
                if not (fim <= ocupacao[7] or inicio >= ocupacao[8]):  # há sobreposição temporal
                    ocupacoes_boca.append(ocupacao)
            
            if ocupacoes_boca:
                bocas_utilizadas += 1
                total_ocupacoes += len(ocupacoes_boca)
                for ocupacao in ocupacoes_boca:
                    total_quantidade += ocupacao[4]  # quantidade_alocada
                    tipos_chama_utilizados.add(ocupacao[5].value)  # tipo_chama
                    for pressao in ocupacao[6]:  # pressoes_chama
                        pressoes_utilizadas.add(pressao.value)
        
        taxa_utilizacao_bocas = (bocas_utilizadas / self.numero_bocas * 100) if self.numero_bocas > 0 else 0.0
        
        return {
            'bocas_utilizadas': bocas_utilizadas,
            'bocas_total': self.numero_bocas,
            'taxa_utilizacao_bocas': taxa_utilizacao_bocas,
            'total_ocupacoes': total_ocupacoes,
            'quantidade_total': total_quantidade,
            'quantidade_media_por_ocupacao': total_quantidade / total_ocupacoes if total_ocupacoes > 0 else 0.0,
            'tipos_chama_utilizados': list(tipos_chama_utilizados),
            'pressoes_utilizadas': list(pressoes_utilizadas)
        }

    def obter_distribuicao_chamas_periodo(self, inicio: datetime, fim: datetime) -> dict:
        """Retorna distribuição de uso por tipo de chama no período."""
        distribuicao = {}
        
        for boca_index in range(self.numero_bocas):
            for ocupacao in self.ocupacoes_por_boca[boca_index]:
                if not (fim <= ocupacao[7] or inicio >= ocupacao[8]):  # há sobreposição temporal
                    chama_nome = ocupacao[5].value  # tipo_chama
                    if chama_nome not in distribuicao:
                        distribuicao[chama_nome] = {
                            'quantidade_total': 0.0,
                            'ocupacoes_count': 0,
                            'bocas_utilizadas': set()
                        }
                    
                    distribuicao[chama_nome]['quantidade_total'] += ocupacao[4]  # quantidade_alocada
                    distribuicao[chama_nome]['ocupacoes_count'] += 1
                    distribuicao[chama_nome]['bocas_utilizadas'].add(boca_index)
        
        # Converter sets para contadores
        for chama_nome in distribuicao:
            distribuicao[chama_nome]['bocas_utilizadas'] = len(distribuicao[chama_nome]['bocas_utilizadas'])
        
        return distribuicao

    def obter_distribuicao_pressoes_periodo(self, inicio: datetime, fim: datetime) -> dict:
        """Retorna distribuição de uso por pressão de chama no período."""
        distribuicao = {}
        
        for boca_index in range(self.numero_bocas):
            for ocupacao in self.ocupacoes_por_boca[boca_index]:
                if not (fim <= ocupacao[7] or inicio >= ocupacao[8]):  # há sobreposição temporal
                    for pressao in ocupacao[6]:  # pressoes_chama
                        pressao_nome = pressao.value
                        if pressao_nome not in distribuicao:
                            distribuicao[pressao_nome] = {
                                'quantidade_total': 0.0,
                                'ocupacoes_count': 0,
                                'bocas_utilizadas': set()
                            }
                        
                        distribuicao[pressao_nome]['quantidade_total'] += ocupacao[4]  # quantidade_alocada
                        distribuicao[pressao_nome]['ocupacoes_count'] += 1
                        distribuicao[pressao_nome]['bocas_utilizadas'].add(boca_index)
        
        # Converter sets para contadores
        for pressao_nome in distribuicao:
            distribuicao[pressao_nome]['bocas_utilizadas'] = len(distribuicao[pressao_nome]['bocas_utilizadas'])
        
        return distribuicao

    # ==========================================================
    # 📊 Métodos de Análise por Item (novos)
    # ==========================================================
    def obter_utilizacao_por_item(self, id_item: int) -> dict:
        """
        📊 Retorna informações de utilização de um item específico no fogão.
        """
        ocupacoes_item = []
        bocas_utilizadas = set()
        
        for boca_index in range(self.numero_bocas):
            for oc in self.ocupacoes_por_boca[boca_index]:
                if oc[3] == id_item:
                    ocupacoes_item.append((*oc, boca_index))
                    bocas_utilizadas.add(boca_index)
        
        if ocupacoes_item:
            quantidade_total = sum(oc[4] for oc in ocupacoes_item)
            periodo_inicio = min(oc[7] for oc in ocupacoes_item)
            periodo_fim = max(oc[8] for oc in ocupacoes_item)
            
            return {
                'quantidade_total': quantidade_total,
                'num_ocupacoes': len(ocupacoes_item),
                'bocas_utilizadas': len(bocas_utilizadas),
                'periodo_inicio': periodo_inicio.strftime('%H:%M'),
                'periodo_fim': periodo_fim.strftime('%H:%M'),
                'ocupacoes': [
                    {
                        'id_ordem': oc[0],
                        'id_pedido': oc[1],
                        'quantidade': oc[4],
                        'boca': oc[9] + 1,  # +1 para mostrar boca 1-indexed
                        'inicio': oc[7].strftime('%H:%M'),
                        'fim': oc[8].strftime('%H:%M'),
                        'tipo_chama': oc[5].value,
                        'pressoes': [p.value for p in oc[6]]
                    }
                    for oc in ocupacoes_item
                ]
            }
        
        return {}

    # ==========================================================
    # 🚨 Métodos para gerenciar restrições (igual ao HotMix)
    # ==========================================================
    def obter_restricoes_registradas(self) -> List[Tuple[int, int, int, int, float, datetime, datetime, str]]:
        """Retorna todas as restrições registradas."""
        return self.restricoes_registradas.copy()

    def limpar_restricoes_registradas(self) -> int:
        """Limpa todas as restrições registradas e retorna quantas foram removidas."""
        quantidade = len(self.restricoes_registradas)
        self.restricoes_registradas.clear()
        logger.info(f"🧹 {self.nome} - {quantidade} restrições removidas.")
        return quantidade

    def relatorio_restricoes(self) -> dict:
        """
        Gera relatório detalhado das restrições registradas.
        """
        if not self.restricoes_registradas:
            return {
                'total_restricoes': 0,
                'restricoes_por_motivo': {},
                'restricoes_por_item': {},
                'restricoes_detalhadas': []
            }

        restricoes_por_motivo = {}
        restricoes_por_item = {}
        restricoes_detalhadas = []

        for restricao in self.restricoes_registradas:
            id_ordem, id_pedido, id_atividade, id_item, quantidade, inicio, fim, motivo = restricao

            # Contabiliza por motivo
            if motivo not in restricoes_por_motivo:
                restricoes_por_motivo[motivo] = 0
            restricoes_por_motivo[motivo] += 1

            # Contabiliza por item
            if id_item not in restricoes_por_item:
                restricoes_por_item[id_item] = {
                    'quantidade_restricoes': 0,
                    'quantidade_total_afetada': 0.0
                }
            restricoes_por_item[id_item]['quantidade_restricoes'] += 1
            restricoes_por_item[id_item]['quantidade_total_afetada'] += quantidade

            # Adiciona detalhes
            restricoes_detalhadas.append({
                'id_ordem': id_ordem,
                'id_pedido': id_pedido,
                'id_atividade': id_atividade,
                'id_item': id_item,
                'quantidade': quantidade,
                'inicio': inicio.strftime('%H:%M [%d/%m]'),
                'fim': fim.strftime('%H:%M [%d/%m]'),
                'motivo': motivo
            })

        return {
            'total_restricoes': len(self.restricoes_registradas),
            'restricoes_por_motivo': restricoes_por_motivo,
            'restricoes_por_item': restricoes_por_item,
            'restricoes_detalhadas': restricoes_detalhadas
        }

    # ==========================================================
    # 🔗 CONSOLIDAÇÃO AUTOMÁTICA (similar ao HotMix)
    # ==========================================================
    def pode_consolidar_ocupacao(
        self,
        id_item: int,
        quantidade: float,
        tipo_chama: TipoChama,
        pressoes_chama: List[TipoPressaoChama],
        inicio: datetime,
        fim: datetime
    ) -> Optional[int]:
        """
        🔗 Verifica se pode consolidar uma nova ocupação com uma existente do mesmo item.
        Retorna o índice da boca que pode ser consolidada, ou None se não for possível.
        """
        for boca_index in range(self.numero_bocas):
            for ocupacao in self.ocupacoes_por_boca[boca_index]:
                # Verifica se é o mesmo item
                if ocupacao[3] != id_item:
                    continue

                # Verifica se há sobreposição temporal EXATA
                if ocupacao[7] != inicio or ocupacao[8] != fim:
                    continue

                # Verifica se as configurações são compatíveis
                if ocupacao[5] != tipo_chama:  # tipo_chama
                    continue

                if ocupacao[6] != pressoes_chama:  # pressoes_chama
                    continue

                # Verifica se a soma das quantidades não excede a capacidade máxima
                quantidade_total = ocupacao[4] + quantidade
                if quantidade_total > self.capacidade_por_boca_gramas_max:
                    continue

                logger.debug(
                    f"🔗 {self.nome} - Boca {boca_index + 1}: Pode consolidar item {id_item} "
                    f"({ocupacao[4]}g + {quantidade}g = {quantidade_total}g) "
                    f"no período {inicio.strftime('%H:%M')}-{fim.strftime('%H:%M')}"
                )

                return boca_index

        return None

    def consolidar_ocupacao(
        self,
        boca_index: int,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade_adicional: float,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """
        🔗 Consolida uma nova atividade com uma ocupação existente do mesmo item.
        """
        for i, ocupacao in enumerate(self.ocupacoes_por_boca[boca_index]):
            # Encontra a ocupação do mesmo item no mesmo período
            if (ocupacao[3] == id_item and
                ocupacao[7] == inicio and
                ocupacao[8] == fim):

                # Calcula nova quantidade total
                quantidade_original = ocupacao[4]
                quantidade_total = quantidade_original + quantidade_adicional

                # Atualiza a ocupação existente
                ocupacao_atualizada = (
                    ocupacao[0],  # id_ordem original
                    ocupacao[1],  # id_pedido original
                    ocupacao[2],  # id_atividade original
                    ocupacao[3],  # id_item
                    quantidade_total,  # quantidade atualizada
                    ocupacao[5],  # tipo_chama
                    ocupacao[6],  # pressoes_chama
                    ocupacao[7],  # inicio
                    ocupacao[8]   # fim
                )

                self.ocupacoes_por_boca[boca_index][i] = ocupacao_atualizada

                logger.info(
                    f"🔗 {self.nome} - Boca {boca_index + 1}: CONSOLIDAÇÃO AUTOMÁTICA | "
                    f"Item {id_item} | Quantidade {quantidade_original}g → {quantidade_total}g | "
                    f"Atividades: {ocupacao[2]} + {id_atividade} | "
                    f"{inicio.strftime('%H:%M')} - {fim.strftime('%H:%M')}"
                )

                return True

        return False

    def verificar_oportunidade_consolidacao(
        self,
        id_item: int,
        quantidade: float,
        tipo_chama: TipoChama,
        pressoes_chama: List[TipoPressaoChama],
        inicio: datetime,
        fim: datetime
    ) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        🔍 Verifica se há oportunidade de consolidação para uma nova ocupação.

        Returns:
            Tuple[bool, Optional[int], Optional[str]]: (pode_consolidar, boca_index, detalhes)
        """
        boca_consolidacao = self.pode_consolidar_ocupacao(
            id_item, quantidade, tipo_chama, pressoes_chama, inicio, fim
        )

        if boca_consolidacao is not None:
            # Encontra detalhes da ocupação existente
            for ocupacao in self.ocupacoes_por_boca[boca_consolidacao]:
                if (ocupacao[3] == id_item and
                    ocupacao[7] == inicio and
                    ocupacao[8] == fim and
                    ocupacao[5] == tipo_chama and
                    ocupacao[6] == pressoes_chama):

                    detalhes = (
                        f"Item {id_item} pode ser consolidado na boca {boca_consolidacao + 1} "
                        f"com ocupação existente ({ocupacao[4]}g + {quantidade}g)"
                    )
                    return True, boca_consolidacao, detalhes

        return False, None, "Nenhuma oportunidade de consolidação encontrada"

    def calcular_pico_utilizacao_item(self, id_item: int) -> dict:
        """
        📈 Calcula o pico de utilização de um item específico no fogão (considerando todas as bocas).
        """
        ocupacoes_item = []
        
        for boca_index in range(self.numero_bocas):
            for oc in self.ocupacoes_por_boca[boca_index]:
                if oc[3] == id_item:
                    ocupacoes_item.append(oc)
        
        if not ocupacoes_item:
            return {}
            
        # Coleta todos os pontos temporais
        pontos_temporais = set()
        for oc in ocupacoes_item:
            pontos_temporais.add(oc[7])  # início
            pontos_temporais.add(oc[8])  # fim
        
        pontos_ordenados = sorted(pontos_temporais)
        
        pico_quantidade = 0.0
        momento_pico = None
        
        # Analisa cada intervalo
        for i in range(len(pontos_ordenados) - 1):
            momento_inicio = pontos_ordenados[i]
            momento_fim = pontos_ordenados[i + 1]
            momento_meio = momento_inicio + (momento_fim - momento_inicio) / 2
            
            quantidade_momento = 0.0
            for oc in ocupacoes_item:
                if oc[7] <= momento_meio < oc[8]:
                    quantidade_momento += oc[4]
            
            if quantidade_momento > pico_quantidade:
                pico_quantidade = quantidade_momento
                momento_pico = momento_meio
        
        if momento_pico:
            # Calcula percentual da capacidade total do fogão
            capacidade_total_fogao = self.numero_bocas * self.capacidade_por_boca_gramas_max
            return {
                'pico_quantidade': pico_quantidade,
                'momento_pico': momento_pico.strftime('%H:%M'),
                'percentual_capacidade_total': (pico_quantidade / capacidade_total_fogao) * 100
            }
        
        return {}