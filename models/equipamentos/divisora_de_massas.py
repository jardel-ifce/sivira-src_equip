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
    ✔️ Ocupação com soma de quantidades para mesmo id_item.
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

        # 📦 Ocupações: (id_ordem, id_pedido, id_atividade, id_item, quantidade_alocada, usa_boleadora, inicio, fim)
        self.ocupacoes: List[Tuple[int, int, int, int, float, Optional[bool], datetime, datetime]] = []

    # ==========================================================
    # ✅ Validações - ATUALIZADAS PARA SOBREPOSIÇÃO POR ITEM
    # ==========================================================
    def esta_disponivel(self, inicio: datetime, fim: datetime) -> bool:
        """
        Método original mantido para compatibilidade.
        Verifica disponibilidade sem considerar mesmo id_item.
        """
        for ocupacao in self.ocupacoes:
            if not (fim <= ocupacao[6] or inicio >= ocupacao[7]):  # início e fim
                return False
        return True

    def esta_disponivel_para_item(self, inicio: datetime, fim: datetime, id_item: int) -> bool:
        """
        Verifica se a divisora pode receber uma nova ocupação do item especificado.
        Uma divisora ocupada só pode receber nova ocupação se:
        - Mesmo id_item E mesmo horário (início e fim exatos)
        """
        for ocupacao in self.ocupacoes:
            ocupacao_id_item = ocupacao[3]
            ocupacao_inicio = ocupacao[6]  # início
            ocupacao_fim = ocupacao[7]     # fim
            
            # Se é o mesmo item E mesmo horário, permite
            if ocupacao_id_item == id_item and ocupacao_inicio == inicio and ocupacao_fim == fim:
                continue
            
            # Para qualquer outra situação, não pode haver sobreposição temporal
            if not (fim <= ocupacao_inicio or inicio >= ocupacao_fim):
                if ocupacao_id_item == id_item:
                    logger.warning(
                        f"⚠️ {self.nome}: Item {id_item} só pode ocupar no mesmo horário. "
                        f"Conflito: {inicio.strftime('%H:%M')}-{fim.strftime('%H:%M')} vs "
                        f"{ocupacao_inicio.strftime('%H:%M')}-{ocupacao_fim.strftime('%H:%M')}"
                    )
                else:
                    logger.warning(
                        f"⚠️ {self.nome} ocupada por item diferente (ID: {ocupacao_id_item}) "
                        f"entre {ocupacao_inicio.strftime('%H:%M')} e {ocupacao_fim.strftime('%H:%M')}."
                    )
                return False
        
        return True

    def validar_capacidade(self, quantidade_gramas: float) -> bool:
        """Valida se a quantidade está dentro da capacidade da divisora."""
        if quantidade_gramas < self.capacidade_gramas_min:
            logger.warning(
                f"⚠️ Quantidade {quantidade_gramas}g abaixo da capacidade mínima ({self.capacidade_gramas_min}g) da {self.nome}."
            )
            return False
        if quantidade_gramas > self.capacidade_gramas_max:
            logger.warning(
                f"⚠️ Quantidade {quantidade_gramas}g acima da capacidade máxima ({self.capacidade_gramas_max}g) da {self.nome}."
            )
            return False
        return True

    def obter_quantidade_maxima_item_periodo(self, id_item: int, inicio: datetime, fim: datetime) -> float:
        """
        Calcula a quantidade máxima de um item que estará sendo processado
        simultaneamente na divisora durante qualquer momento do período especificado.
        """
        # Lista todos os pontos temporais relevantes (inícios e fins de ocupações)
        pontos_temporais = set()
        ocupacoes_item = []
        
        # Coleta ocupações do mesmo item
        for ocupacao in self.ocupacoes:
            if ocupacao[3] == id_item:  # mesmo id_item
                ocupacoes_item.append(ocupacao)
                pontos_temporais.add(ocupacao[6])  # início
                pontos_temporais.add(ocupacao[7])  # fim
        
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
                if ocupacao[6] <= momento_meio < ocupacao[7]:  # ocupação ativa neste momento
                    quantidade_momento += ocupacao[4]  # quantidade_alocada
            
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
                pontos_temporais.add(ocupacao[6])  # início
                pontos_temporais.add(ocupacao[7])  # fim
        
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
                if ocupacao[6] <= momento_meio < ocupacao[7]:
                    quantidade_total += ocupacao[4]  # quantidade_alocada
            
            # Soma nova ocupação se ativa neste momento
            if inicio <= momento_meio < fim:
                quantidade_total += quantidade_nova
            
            # Verifica se excede capacidade
            if not self.validar_capacidade(quantidade_total):
                logger.debug(
                    f"❌ {self.nome} | Item {id_item}: Capacidade excedida no momento {momento_meio.strftime('%H:%M')} "
                    f"({quantidade_total}g > {self.capacidade_gramas_max}g)"
                )
                return False
        
        return True

    def verificar_disponibilidade(self, quantidade: float, inicio: datetime, fim: datetime, id_item: int) -> bool:
        """Verifica se é possível ocupar a divisora com a quantidade especificada no período para um item."""
        if not self.esta_disponivel_para_item(inicio, fim, id_item):
            return False
        
        return self.validar_nova_ocupacao_item(id_item, quantidade, inicio, fim)

    # ==========================================================
    # 🔍 Consulta de Ocupação (para o Gestor)
    # ==========================================================
    def obter_quantidade_alocada_periodo(self, inicio: datetime, fim: datetime) -> float:
        """Retorna a quantidade total alocada no período especificado."""
        quantidade_total = 0.0
        for ocupacao in self.ocupacoes:
            if not (fim <= ocupacao[6] or inicio >= ocupacao[7]):  # há sobreposição temporal
                quantidade_total += ocupacao[4]  # quantidade_alocada
        return quantidade_total

    def obter_ocupacoes_periodo(self, inicio: datetime, fim: datetime) -> List[Tuple[int, int, int, int, float, Optional[bool], datetime, datetime]]:
        """Retorna todas as ocupações que se sobrepõem ao período especificado."""
        ocupacoes_periodo = []
        for ocupacao in self.ocupacoes:
            if not (fim <= ocupacao[6] or inicio >= ocupacao[7]):  # há sobreposição temporal
                ocupacoes_periodo.append(ocupacao)
        return ocupacoes_periodo

    def obter_proxima_liberacao(self, momento_atual: datetime) -> Optional[datetime]:
        """Retorna próximo horário de liberação da divisora."""
        proximas_liberacoes = [
            ocupacao[7]  # fim
            for ocupacao in self.ocupacoes
            if ocupacao[7] > momento_atual
        ]
        return min(proximas_liberacoes) if proximas_liberacoes else None

    def obter_todas_ocupacoes(self) -> List[Tuple[int, int, int, int, float, Optional[bool], datetime, datetime]]:
        """Retorna todas as ocupações da divisora."""
        return self.ocupacoes.copy()

    # ==========================================================
    # 🔄 Ocupação - ATUALIZADA COM VALIDAÇÃO POR ITEM
    # ==========================================================
    def ocupar(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade: float,
        inicio: datetime,
        fim: datetime,
        usar_boleadora: Optional[bool] = None
    ) -> bool:
        """
        Método principal de ocupação com validação por item.
        """
        # Verifica disponibilidade (só impede se for item diferente com sobreposição)  
        if not self.esta_disponivel_para_item(inicio, fim, id_item):
            logger.warning(
                f"❌ {self.nome} | Ocupada por item diferente entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
            )
            return False

        # Valida se a nova ocupação respeita capacidade em todos os momentos
        if not self.validar_nova_ocupacao_item(id_item, quantidade, inicio, fim):
            quantidade_atual = self.obter_quantidade_maxima_item_periodo(id_item, inicio, fim)
            logger.error(
                f"❌ {self.nome} | Item {id_item}: Nova quantidade {quantidade}g + "
                f"máximo atual {quantidade_atual}g excederia capacidade máxima ({self.capacidade_gramas_max}g)"
            )
            return False

        # Define se usa boleadora (se disponível e quantidade mínima atendida)
        usa_boleadora = False
        if usar_boleadora is not None:
            usa_boleadora = usar_boleadora and self.boleadora
        else:
            usa_boleadora = self.boleadora and quantidade >= self.capacidade_gramas_min

        # Cria nova ocupação
        self.ocupacoes.append(
            (id_ordem, id_pedido, id_atividade, id_item, quantidade, usa_boleadora, inicio, fim)
        )

        # Log informativo
        quantidade_maxima_apos = self.obter_quantidade_maxima_item_periodo(id_item, inicio, fim) + quantidade
        logger.info(
            f"🔪 {self.nome} | Item {id_item}: Nova ocupação {quantidade}g "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} "
            f"(Pico máximo do item: {quantidade_maxima_apos}g) "
            f"(Ordem {id_ordem}, Pedido {id_pedido}, Atividade {id_atividade}) | "
            f"Boleadora: {'Sim' if usa_boleadora else 'Não'}"
        )
        
        return True

    def adicionar_ocupacao(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade: float,
        inicio: datetime,
        fim: datetime,
        usar_boleadora: Optional[bool] = None
    ) -> bool:
        """Método de compatibilidade que usa a validação por item."""
        return self.ocupar(
            id_ordem, id_pedido, id_atividade, id_item, 
            quantidade, inicio, fim, usar_boleadora
        )

    def sobrescrever_ocupacoes(
        self,
        ocupacoes: List[Tuple[int, int, int, int, float, Optional[bool], datetime, datetime]]
    ) -> bool:
        """Sobrescreve completamente as ocupações da divisora."""
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
        novo_inicio: datetime,
        novo_fim: datetime,
        nova_boleadora: Optional[bool] = None
    ) -> bool:
        """Atualiza uma ocupação específica da divisora."""
        for i, ocupacao in enumerate(self.ocupacoes):
            if ocupacao[0] == id_ordem and ocupacao[1] == id_pedido and ocupacao[2] == id_atividade:
                id_item = ocupacao[3]  # Mantém o id_item original
                
                # Remove temporariamente a ocupação atual para validação
                ocupacao_original = self.ocupacoes.pop(i)
                
                # Valida a nova ocupação
                if not self.validar_nova_ocupacao_item(id_item, nova_quantidade, novo_inicio, novo_fim):
                    # Restaura a ocupação original se validação falhar
                    self.ocupacoes.insert(i, ocupacao_original)
                    return False
                
                # Define nova configuração de boleadora
                nova_usa_boleadora = False
                if nova_boleadora is not None:
                    nova_usa_boleadora = nova_boleadora and self.boleadora
                else:
                    nova_usa_boleadora = self.boleadora and nova_quantidade >= self.capacidade_gramas_min

                # Adiciona a ocupação atualizada
                self.ocupacoes.insert(i, (
                    id_ordem, id_pedido, id_atividade, id_item, nova_quantidade, 
                    nova_usa_boleadora, novo_inicio, novo_fim
                ))
                
                logger.info(
                    f"🔄 Ocupação atualizada na {self.nome} | "
                    f"Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade} | Item {id_item} | "
                    f"Nova quantidade: {nova_quantidade:.2f}g | {novo_inicio.strftime('%H:%M')} → {novo_fim.strftime('%H:%M')} | "
                    f"Boleadora: {'Sim' if nova_usa_boleadora else 'Não'}"
                )
                return True

        logger.warning(
            f"❌ Ocupação não encontrada para atualizar na {self.nome} | "
            f"Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade}"
        )
        return False

    # ==========================================================
    # 🔓 Liberação (métodos mantidos iguais)
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

    def liberar_por_item(self, id_item: int):
        """Libera ocupações vinculadas a um item específico."""
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if ocupacao[3] != id_item
        ]
        liberadas = antes - len(self.ocupacoes)
        
        if liberadas > 0:
            logger.info(
                f"🔓 {self.nome} | Liberadas {liberadas} ocupações do item {id_item}."
            )
        else:
            logger.info(
                f"ℹ️ Nenhuma ocupação da {self.nome} estava associada ao item {id_item}."
            )

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        """Libera ocupações que já finalizaram."""
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if ocupacao[7] > horario_atual  # fim > horario_atual
        ]
        liberadas = antes - len(self.ocupacoes)
        
        if liberadas > 0:
            logger.info(
                f"🟩 {self.nome} | Liberou {liberadas} ocupações finalizadas até {horario_atual.strftime('%H:%M')}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação finalizada encontrada para liberar na {self.nome} até {horario_atual.strftime('%H:%M')}."
            )
        return liberadas

    def liberar_todas_ocupacoes(self):
        """Limpa todas as ocupações da divisora."""
        total = len(self.ocupacoes)
        self.ocupacoes.clear()
        logger.info(f"🔓 Todas as {total} ocupações da {self.nome} foram removidas.")

    def liberar_por_intervalo(self, inicio: datetime, fim: datetime):
        """Libera ocupações que se sobrepõem ao intervalo especificado."""
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if not (ocupacao[6] < fim and ocupacao[7] > inicio)  # remove qualquer sobreposição
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
        """Mostra agenda detalhada da divisora."""
        logger.info("==============================================")
        logger.info(f"📅 Agenda da {self.nome}")
        logger.info("==============================================")

        if not self.ocupacoes:
            logger.info("🔹 Nenhuma ocupação registrada.")
            return

        for ocupacao in self.ocupacoes:
            logger.info(
                f"🔪 Ordem {ocupacao[0]} | Pedido {ocupacao[1]} | Atividade {ocupacao[2]} | Item {ocupacao[3]} | "
                f"{ocupacao[4]:.2f}g | Boleadora: {'Sim' if ocupacao[5] else 'Não'} | "
                f"{ocupacao[6].strftime('%H:%M')} → {ocupacao[7].strftime('%H:%M')}"
            )

    def obter_estatisticas_uso(self, inicio: datetime, fim: datetime) -> Dict[str, float]:
        """Retorna estatísticas de uso da divisora no período."""
        ocupacoes_periodo = self.obter_ocupacoes_periodo(inicio, fim)
        
        if not ocupacoes_periodo:
            return {
                'quantidade_total': 0.0,
                'tempo_ocupado_minutos': 0.0,
                'uso_boleadora_count': 0,
                'quantidade_media_por_ocupacao': 0.0
            }
        
        quantidade_total = sum(ocupacao[4] for ocupacao in ocupacoes_periodo)  # quantidade_alocada
        uso_boleadora_count = sum(1 for ocupacao in ocupacoes_periodo if ocupacao[5])  # usa_boleadora
        
        # Calcular tempo total ocupado (em minutos)
        tempo_ocupado_total = 0.0
        for ocupacao in ocupacoes_periodo:
            # Considerar apenas a sobreposição com o período solicitado
            inicio_efetivo = max(inicio, ocupacao[6])
            fim_efetivo = min(fim, ocupacao[7])
            if inicio_efetivo < fim_efetivo:
                tempo_ocupado_total += (fim_efetivo - inicio_efetivo).total_seconds() / 60
        
        return {
            'quantidade_total': quantidade_total,
            'tempo_ocupado_minutos': tempo_ocupado_total,
            'uso_boleadora_count': uso_boleadora_count,
            'quantidade_media_por_ocupacao': quantidade_total / len(ocupacoes_periodo) if ocupacoes_periodo else 0.0
        }

    # ==========================================================
    # 📊 Métodos de Análise por Item (novos)
    # ==========================================================
    def obter_utilizacao_por_item(self, id_item: int) -> dict:
        """
        📊 Retorna informações de utilização de um item específico na divisora.
        """
        ocupacoes_item = [
            oc for oc in self.ocupacoes if oc[3] == id_item
        ]
        
        if ocupacoes_item:
            quantidade_total = sum(oc[4] for oc in ocupacoes_item)
            periodo_inicio = min(oc[6] for oc in ocupacoes_item)
            periodo_fim = max(oc[7] for oc in ocupacoes_item)
            
            return {
                'quantidade_total': quantidade_total,
                'num_ocupacoes': len(ocupacoes_item),
                'periodo_inicio': periodo_inicio.strftime('%H:%M'),
                'periodo_fim': periodo_fim.strftime('%H:%M'),
                'ocupacoes': [
                    {
                        'id_ordem': oc[0],
                        'id_pedido': oc[1],
                        'quantidade': oc[4],
                        'inicio': oc[6].strftime('%H:%M'),
                        'fim': oc[7].strftime('%H:%M'),
                        'usa_boleadora': oc[5]
                    }
                    for oc in ocupacoes_item
                ]
            }
        
        return {}

    def calcular_pico_utilizacao_item(self, id_item: int) -> dict:
        """
        📈 Calcula o pico de utilização de um item específico na divisora.
        """
        ocupacoes_item = [oc for oc in self.ocupacoes if oc[3] == id_item]
        
        if not ocupacoes_item:
            return {}
            
        # Coleta todos os pontos temporais
        pontos_temporais = set()
        for oc in ocupacoes_item:
            pontos_temporais.add(oc[6])  # início
            pontos_temporais.add(oc[7])  # fim
        
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
                if oc[6] <= momento_meio < oc[7]:
                    quantidade_momento += oc[4]
            
            if quantidade_momento > pico_quantidade:
                pico_quantidade = quantidade_momento
                momento_pico = momento_meio
        
        if momento_pico:
            return {
                'pico_quantidade': pico_quantidade,
                'momento_pico': momento_pico.strftime('%H:%M'),
                'percentual_capacidade': (pico_quantidade / self.capacidade_gramas_max) * 100
            }
        
        return {}