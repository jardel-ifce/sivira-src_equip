from models.equipamentos.equipamento import Equipamento
from enums.equipamentos.tipo_velocidade import TipoVelocidade
from enums.equipamentos.tipo_mistura import TipoMistura
from enums.producao.tipo_setor import TipoSetor
from enums.equipamentos.tipo_equipamento import TipoEquipamento
from typing import List, Optional, Tuple
from datetime import datetime
from utils.logs.logger_factory import setup_logger

logger = setup_logger('Masseira')


class Masseira(Equipamento):
    """
    🥣 Classe que representa uma Masseira.
    ✔️ Controle de capacidade por peso.
    ✔️ Suporte a múltiplas velocidades e tipos de mistura.
    ✔️ Permite ocupações simultâneas de mesmo item com intervalos flexíveis.
    ✔️ Validação dinâmica de capacidade considerando picos de sobreposição.
    ✔️ Gestor controla lógica de compatibilidade e capacidades.
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
        capacidade_gramas_min: float,
        capacidade_gramas_max: float,
        velocidades_suportadas: Optional[List[TipoVelocidade]] = None,
        tipos_de_mistura_suportados: Optional[List[TipoMistura]] = None
    ):
        super().__init__(
            id=id,
            nome=nome,
            tipo_equipamento=TipoEquipamento.MISTURADORAS,
            setor=setor,
            numero_operadores=numero_operadores,
            status_ativo=True
        )

        self.capacidade_gramas_min = capacidade_gramas_min
        self.capacidade_gramas_max = capacidade_gramas_max
        self.velocidades_suportadas = velocidades_suportadas or []
        self.tipos_de_mistura_suportados = tipos_de_mistura_suportados or []

        # 🗓️ Ocupações: (id_ordem, id_pedido, id_atividade, id_item, quantidade_alocada, velocidades, tipo_mistura, inicio, fim)
        self.ocupacoes: List[Tuple[int, int, int, int, float, List[TipoVelocidade], TipoMistura, datetime, datetime]] = []

    # ==========================================================
    # 🔍 Validação Dinâmica de Capacidade (NOVO)
    # ==========================================================
    def obter_quantidade_maxima_item_periodo(self, id_item: int, inicio: datetime, fim: datetime) -> float:
        """
        Calcula a quantidade máxima de um item que estará sendo processado
        simultaneamente na masseira durante qualquer momento do período especificado.
        """
        # Lista todos os pontos temporais relevantes (inícios e fins de ocupações)
        pontos_temporais = set()
        ocupacoes_item = []
        
        # Coleta ocupações do mesmo item
        for ocupacao in self.ocupacoes:
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
                    quantidade_momento += ocupacao[4]
            
            quantidade_maxima = max(quantidade_maxima, quantidade_momento)
        
        return quantidade_maxima

    def validar_nova_ocupacao_item(self, id_item: int, quantidade_nova: float, 
                                  inicio: datetime, fim: datetime) -> bool:
        """
        Simula uma nova ocupação e verifica se a capacidade máxima será respeitada
        em todos os momentos de sobreposição.
        """
        # Coleta todos os pontos temporais relevantes
        pontos_temporais = set()
        ocupacoes_item = []
        
        for ocupacao in self.ocupacoes:
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
                    quantidade_total += ocupacao[4]
            
            # Soma nova ocupação se ativa neste momento
            if inicio <= momento_meio < fim:
                quantidade_total += quantidade_nova
            
            # Verifica se excede capacidade
            if quantidade_total > self.capacidade_gramas_max:
                logger.debug(
                    f"❌ {self.nome} | Item {id_item}: Capacidade excedida no momento {momento_meio.strftime('%H:%M')} "
                    f"({quantidade_total}g > {self.capacidade_gramas_max}g)"
                )
                return False
        
        return True

    def esta_disponivel_para_item(self, inicio: datetime, fim: datetime, id_item: int) -> bool:
        """
        Verifica se a masseira pode receber uma nova ocupação do item especificado.
        Para o mesmo item, sempre permite (validação de capacidade será feita separadamente).
        Para itens diferentes, não permite sobreposição.
        """
        for ocupacao in self.ocupacoes:
            # Se é o mesmo item, sempre permite (capacidade será validada depois)
            if ocupacao[3] == id_item:
                continue
                
            # Para itens diferentes, não pode haver sobreposição
            if not (fim <= ocupacao[7] or inicio >= ocupacao[8]):
                return False
        
        return True

    # ==========================================================
    # 🔍 Consulta de Ocupação (para o Gestor)
    # ==========================================================
    def item_ja_alocado_periodo(self, id_item: int, inicio: datetime, fim: datetime) -> bool:
        """Verifica se um item específico já está alocado no período (para o Gestor decidir sobreposição)."""
        for ocupacao in self.ocupacoes:
            if ocupacao[3] == id_item and not (fim <= ocupacao[7] or inicio >= ocupacao[8]):
                return True
        return False

    def obter_quantidade_alocada_periodo(self, inicio: datetime, fim: datetime, id_item: Optional[int] = None) -> float:
        """
        Retorna a quantidade total alocada no período especificado, opcionalmente filtrada por item.
        ATENÇÃO: Para mesmo item, retorna PICO MÁXIMO de sobreposição, não soma simples.
        """
        if id_item is not None:
            # Para item específico, retorna pico máximo de sobreposição
            return self.obter_quantidade_maxima_item_periodo(id_item, inicio, fim)
        else:
            # Para todos os itens, soma simples (comportamento original)
            quantidade_total = 0.0
            for ocupacao in self.ocupacoes:
                if not (fim <= ocupacao[7] or inicio >= ocupacao[8]):  # há sobreposição temporal
                    quantidade_total += ocupacao[4]
            return quantidade_total

    def obter_ocupacoes_periodo(self, inicio: datetime, fim: datetime) -> List[Tuple[int, int, int, int, float, List[TipoVelocidade], TipoMistura, datetime, datetime]]:
        """Retorna todas as ocupações que se sobrepõem ao período especificado."""
        ocupacoes_periodo = []
        for ocupacao in self.ocupacoes:
            if not (fim <= ocupacao[7] or inicio >= ocupacao[8]):  # há sobreposição temporal
                ocupacoes_periodo.append(ocupacao)
        return ocupacoes_periodo

    def obter_ocupacoes_item_periodo(self, id_item: int, inicio: datetime, fim: datetime) -> List[Tuple[int, int, int, int, float, List[TipoVelocidade], TipoMistura, datetime, datetime]]:
        """Retorna ocupações de um item específico que se sobrepõem ao período."""
        ocupacoes_item = []
        for ocupacao in self.ocupacoes:
            if ocupacao[3] == id_item and not (fim <= ocupacao[7] or inicio >= ocupacao[8]):
                ocupacoes_item.append(ocupacao)
        return ocupacoes_item

    def obter_capacidade_disponivel_item(self, id_item: int, inicio: datetime, fim: datetime) -> float:
        """Retorna a capacidade disponível para um item específico no período."""
        quantidade_ocupada = self.obter_quantidade_maxima_item_periodo(id_item, inicio, fim)
        return max(0.0, self.capacidade_gramas_max - quantidade_ocupada)

    def esta_disponivel(self, inicio: datetime, fim: datetime) -> bool:
        """Verifica se a masseira está completamente livre no período."""
        for ocupacao in self.ocupacoes:
            if not (fim <= ocupacao[7] or inicio >= ocupacao[8]):
                logger.warning(
                    f"⚠️ {self.nome} não disponível entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')} "
                    f"devido ao item {ocupacao[3]} da atividade {ocupacao[2]}."
                )
                return False
        return True

    def obter_proxima_liberacao(self, momento_atual: datetime) -> Optional[datetime]:
        """Retorna próximo horário de liberação da masseira."""
        proximas_liberacoes = [
            ocupacao[8] for ocupacao in self.ocupacoes  # fim
            if ocupacao[8] > momento_atual
        ]
        return min(proximas_liberacoes) if proximas_liberacoes else None

    def obter_todas_ocupacoes(self) -> List[Tuple[int, int, int, int, float, List[TipoVelocidade], TipoMistura, datetime, datetime]]:
        """Retorna todas as ocupações da masseira."""
        return self.ocupacoes.copy()

    # ==========================================================
    # ✅ Validações (Parâmetros técnicos)
    # ==========================================================
    def validar_capacidade_individual(self, quantidade: float) -> bool:
        """Valida se a quantidade individual está dentro dos limites."""
        if quantidade < self.capacidade_gramas_min:
            logger.warning(
                f"⚠️ Quantidade {quantidade}g abaixo do mínimo permitido pela {self.nome} "
                f"({self.capacidade_gramas_min}g)"
            )
            return False
        if quantidade > self.capacidade_gramas_max:
            logger.warning(
                f"⚠️ Quantidade {quantidade}g acima do máximo permitido pela {self.nome} "
                f"({self.capacidade_gramas_max}g)"
            )
            return False
        return True

    def validar_capacidade_total_item(self, id_item: int, quantidade_adicional: float, inicio: datetime, fim: datetime) -> bool:
        """
        Valida se a capacidade total do item não excede o limite considerando picos de sobreposição.
        """
        return self.validar_nova_ocupacao_item(id_item, quantidade_adicional, inicio, fim)

    def verificar_disponibilidade(
        self, 
        quantidade: float, 
        velocidades: List[TipoVelocidade], 
        tipo_mistura: TipoMistura
    ) -> bool:
        """Verifica se os parâmetros são válidos para a masseira (sem verificar período)."""
        return self.validar_capacidade_individual(quantidade)
        # Validações de velocidades e tipo_mistura removidas conforme solicitado

    # ==========================================================
    # 🔄 Ocupação e Atualização (para o Gestor)
    # ==========================================================
    def adicionar_ocupacao(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade_alocada: float,
        velocidades: List[TipoVelocidade],
        tipo_mistura: TipoMistura,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """
        Adiciona uma ocupação à masseira.
        Valida capacidade considerando intervalos flexíveis do mesmo item.
        """
        # Validações básicas
        if not self.verificar_disponibilidade(quantidade_alocada, velocidades, tipo_mistura):
            return False

        # Verifica disponibilidade (só impede se for item diferente com sobreposição)
        if not self.esta_disponivel_para_item(inicio, fim, id_item):
            logger.warning(
                f"❌ {self.nome} | Ocupada por item diferente entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
            )
            return False

        # Valida se a nova ocupação respeita capacidade em todos os momentos
        if not self.validar_nova_ocupacao_item(id_item, quantidade_alocada, inicio, fim):
            quantidade_atual = self.obter_quantidade_maxima_item_periodo(id_item, inicio, fim)
            logger.error(
                f"❌ {self.nome} | Item {id_item}: Nova quantidade {quantidade_alocada}g + "
                f"máximo atual {quantidade_atual}g excederia capacidade máxima ({self.capacidade_gramas_max}g)"
            )
            return False

        # Adiciona ocupação
        self.ocupacoes.append(
            (id_ordem, id_pedido, id_atividade, id_item, quantidade_alocada, velocidades, tipo_mistura, inicio, fim)
        )

        # Log informativo
        quantidade_maxima_apos = self.obter_quantidade_maxima_item_periodo(id_item, inicio, fim) + quantidade_alocada
        velocidades_str = ", ".join([v.name for v in velocidades]) if velocidades else "Nenhuma"
        logger.info(
            f"🥣 {self.nome} | Item {id_item}: Nova ocupação {quantidade_alocada}g "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} "
            f"(Pico máximo do item: {quantidade_maxima_apos}g) "
            f"(Ordem {id_ordem}, Pedido {id_pedido}, Atividade {id_atividade}) | "
            f"Velocidades: {velocidades_str} | Mistura: {tipo_mistura.name if tipo_mistura else 'Nenhuma'}"
        )
        return True

    def sobrescrever_ocupacoes(
        self,
        ocupacoes: List[Tuple[int, int, int, int, float, List[TipoVelocidade], TipoMistura, datetime, datetime]]
    ) -> bool:
        """Sobrescreve completamente as ocupações da masseira."""
        self.ocupacoes = ocupacoes.copy()
        
        logger.info(
            f"🔄 Ocupações da {self.nome} foram sobrescritas. "
            f"Total de ocupações: {len(ocupacoes)}"
        )
        return True

    def atualizar_ocupacao_especifica(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        nova_quantidade: float,
        novas_velocidades: List[TipoVelocidade],
        novo_tipo_mistura: TipoMistura,
        novo_inicio: datetime,
        novo_fim: datetime
    ) -> bool:
        """Atualiza uma ocupação específica da masseira."""
        for i, ocupacao in enumerate(self.ocupacoes):
            if ocupacao[0] == id_ordem and ocupacao[1] == id_pedido and ocupacao[2] == id_atividade:
                # Remover ocupação atual temporariamente para validação
                ocupacao_original = self.ocupacoes.pop(i)
                
                # Validar nova configuração
                if not self.verificar_disponibilidade(nova_quantidade, novas_velocidades, novo_tipo_mistura):
                    # Restaurar ocupação original se validação falhar
                    self.ocupacoes.insert(i, ocupacao_original)
                    return False

                # Aplicar atualização
                self.ocupacoes.insert(i, (
                    id_ordem, id_pedido, id_atividade, ocupacao_original[3], nova_quantidade, 
                    novas_velocidades, novo_tipo_mistura, novo_inicio, novo_fim
                ))
                
                velocidades_str = ", ".join([v.name for v in novas_velocidades]) if novas_velocidades else "Nenhuma"
                logger.info(
                    f"🔄 Ocupação atualizada na {self.nome} | "
                    f"Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade} | "
                    f"Nova quantidade: {nova_quantidade:.2f}g | {novo_inicio.strftime('%H:%M')} → {novo_fim.strftime('%H:%M')} | "
                    f"Velocidades: {velocidades_str} | Mistura: {novo_tipo_mistura.name if novo_tipo_mistura else 'Nenhuma'}"
                )
                return True

        logger.warning(
            f"❌ Ocupação não encontrada para atualizar na {self.nome} | "
            f"Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade}"
        )
        return False

    # ==========================================================
    # 🔐 Ocupação (Método de Compatibilidade)
    # ==========================================================
    def ocupar(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade_alocada: float,
        velocidades: Optional[List[TipoVelocidade]] = None,
        tipo_mistura: Optional[TipoMistura] = None,
        inicio: datetime = None,
        fim: datetime = None
    ) -> bool:
        """Método de compatibilidade para ocupação."""
        return self.adicionar_ocupacao(
            id_ordem, id_pedido, id_atividade, id_item, quantidade_alocada,
            velocidades or [], tipo_mistura, inicio, fim
        )

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, id_ordem: int, id_pedido: int, id_atividade: int):
        """Libera ocupações específicas por atividade."""
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido and ocupacao[2] == id_atividade)
        ]
        liberadas = antes - len(self.ocupacoes)
        
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações da {self.nome} "
                f"para Atividade {id_atividade}, Pedido {id_pedido}, Ordem {id_ordem}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar na {self.nome} "
                f"para Atividade {id_atividade}, Pedido {id_pedido}, Ordem {id_ordem}."
            )

    def liberar_por_pedido(self, id_ordem: int, id_pedido: int):
        """Libera ocupações específicas por pedido."""
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido)
        ]
        liberadas = antes - len(self.ocupacoes)
        
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações da {self.nome} "
                f"para Pedido {id_pedido}, Ordem {id_ordem}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar na {self.nome} "
                f"para Pedido {id_pedido}, Ordem {id_ordem}."
            )

    def liberar_por_ordem(self, id_ordem: int):
        """Libera ocupações específicas por ordem."""
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if ocupacao[0] != id_ordem
        ]
        liberadas = antes - len(self.ocupacoes)
        
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações da {self.nome} "
                f"para Ordem {id_ordem}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar na {self.nome} "
                f"para Ordem {id_ordem}."
            )

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        """Libera ocupações que já finalizaram."""
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if ocupacao[8] > horario_atual  # fim > horario_atual
        ]
        liberadas = antes - len(self.ocupacoes)
        
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações da {self.nome} finalizadas até {horario_atual.strftime('%H:%M')}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação finalizada encontrada para liberar na {self.nome} até {horario_atual.strftime('%H:%M')}."
            )
        return liberadas

    def liberar_todas_ocupacoes(self):
        """Limpa todas as ocupações da masseira."""
        total = len(self.ocupacoes)
        self.ocupacoes.clear()
        logger.info(f"🔓 Todas as {total} ocupações da {self.nome} foram removidas.")

    def liberar_por_intervalo(self, inicio: datetime, fim: datetime):
        """Libera ocupações que se sobrepõem ao intervalo especificado."""
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if not (ocupacao[7] < fim and ocupacao[8] > inicio)  # remove qualquer sobreposição
        ]
        liberadas = antes - len(self.ocupacoes)
        
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações da {self.nome} entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar na {self.nome} entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
            )

    # ==========================================================
    # 📅 Agenda e Relatórios
    # ==========================================================
    def mostrar_agenda(self):
        """Mostra agenda detalhada da masseira."""
        logger.info("==============================================")
        logger.info(f"📅 Agenda da {self.nome}")
        logger.info("==============================================")

        if not self.ocupacoes:
            logger.info("🔹 Nenhuma ocupação registrada.")
            return

        for ocupacao in self.ocupacoes:
            velocidades_str = ", ".join([v.name for v in ocupacao[5]]) if ocupacao[5] else "Nenhuma"
            logger.info(
                f"🥣 Ordem {ocupacao[0]} | Pedido {ocupacao[1]} | Atividade {ocupacao[2]} | Item {ocupacao[3]} | "
                f"{ocupacao[4]:.2f}g | {ocupacao[7].strftime('%H:%M')} → {ocupacao[8].strftime('%H:%M')} | "
                f"Velocidades: {velocidades_str} | Mistura: {ocupacao[6].name if ocupacao[6] else 'Nenhuma'}"
            )

    def obter_estatisticas_velocidade(self, inicio: datetime, fim: datetime) -> dict:
        """Retorna estatísticas de uso por velocidade no período."""
        ocupacoes_periodo = self.obter_ocupacoes_periodo(inicio, fim)
        
        if not ocupacoes_periodo:
            return {}
        
        estatisticas_velocidade = {}
        
        for ocupacao in ocupacoes_periodo:
            for velocidade in ocupacao[5]:  # velocidades
                nome_velocidade = velocidade.name
                if nome_velocidade not in estatisticas_velocidade:
                    estatisticas_velocidade[nome_velocidade] = {
                        'quantidade_total': 0.0,
                        'ocorrencias': 0
                    }
                
                estatisticas_velocidade[nome_velocidade]['quantidade_total'] += ocupacao[4]  # quantidade
                estatisticas_velocidade[nome_velocidade]['ocorrencias'] += 1
        
        return estatisticas_velocidade

    def obter_estatisticas_mistura(self, inicio: datetime, fim: datetime) -> dict:
        """Retorna estatísticas de uso por tipo de mistura no período."""
        ocupacoes_periodo = self.obter_ocupacoes_periodo(inicio, fim)
        
        if not ocupacoes_periodo:
            return {}
        
        estatisticas_mistura = {}
        
        for ocupacao in ocupacoes_periodo:
            if ocupacao[6]:  # tipo_mistura
                nome_mistura = ocupacao[6].name
                if nome_mistura not in estatisticas_mistura:
                    estatisticas_mistura[nome_mistura] = {
                        'quantidade_total': 0.0,
                        'ocorrencias': 0
                    }
                
                estatisticas_mistura[nome_mistura]['quantidade_total'] += ocupacao[4]  # quantidade
                estatisticas_mistura[nome_mistura]['ocorrencias'] += 1
        
        return estatisticas_mistura