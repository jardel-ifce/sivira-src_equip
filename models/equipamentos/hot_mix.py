from models.equipamentos.equipamento import Equipamento
from enums.equipamentos.tipo_equipamento import TipoEquipamento
from enums.producao.tipo_setor import TipoSetor
from enums.equipamentos.tipo_chama import TipoChama
from enums.equipamentos.tipo_pressao_chama import TipoPressaoChama
from enums.equipamentos.tipo_velocidade import TipoVelocidade
from typing import List, Tuple
from datetime import datetime
from utils.logs.logger_factory import setup_logger

# 🔥 Logger exclusivo para HotMix
logger = setup_logger("HotMix")


class HotMix(Equipamento):
    """
    🍳 Equipamento HotMix — Misturadora com Cocção de Alta Performance.
    ✔️ Controle de ocupação por ordem, pedido, atividade, item e quantidade.
    ✔️ Suporta múltiplas velocidades, chamas e pressões de chama.
    ✔️ Permite sobreposição do mesmo id_item com intervalos flexíveis.
    ✔️ Validação dinâmica de capacidade considerando picos de sobreposição.
    ✔️ Ocupação exclusiva para itens diferentes.
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

        # Tupla: (id_ordem, id_pedido, id_atividade, id_item, quantidade, velocidade, chama, pressoes, inicio, fim)
        self.ocupacoes: List[
            Tuple[int, int, int, int, int, TipoVelocidade, TipoChama, List[TipoPressaoChama], datetime, datetime]
        ] = []

    # ==========================================================
    # 🔍 Validação Dinâmica de Capacidade (CORRIGIDO)
    # ==========================================================
    def obter_quantidade_maxima_item_periodo(self, id_item: int, inicio: datetime, fim: datetime) -> int:
        """
        Calcula a quantidade máxima de um item que estará sendo processado
        simultaneamente no HotMix durante qualquer momento do período especificado.
        """
        # Lista todos os pontos temporais relevantes (inícios e fins de ocupações)
        pontos_temporais = set()
        ocupacoes_item = []
        
        # Coleta ocupações do mesmo item
        for ocupacao in self.ocupacoes:
            if ocupacao[3] == id_item:  # mesmo id_item
                ocupacoes_item.append(ocupacao)
                pontos_temporais.add(ocupacao[8])  # início
                pontos_temporais.add(ocupacao[9])  # fim
        
        # Adiciona os pontos do novo período
        pontos_temporais.add(inicio)
        pontos_temporais.add(fim)
        
        # Ordena os pontos temporais
        pontos_ordenados = sorted(pontos_temporais)
        
        quantidade_maxima = 0
        
        # Verifica a quantidade em cada intervalo
        for i in range(len(pontos_ordenados) - 1):
            momento_inicio = pontos_ordenados[i]
            momento_fim = pontos_ordenados[i + 1]
            momento_meio = momento_inicio + (momento_fim - momento_inicio) / 2
            
            # Soma quantidade de todas as ocupações ativas neste momento
            quantidade_momento = 0
            
            # Verifica ocupações existentes
            for ocupacao in ocupacoes_item:
                if ocupacao[8] <= momento_meio < ocupacao[9]:  # ocupação ativa neste momento
                    quantidade_momento += ocupacao[4]
            
            quantidade_maxima = max(quantidade_maxima, quantidade_momento)
        
        return quantidade_maxima

    def validar_nova_ocupacao_item(self, id_item: int, quantidade_nova: int, 
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
                pontos_temporais.add(ocupacao[8])  # início
                pontos_temporais.add(ocupacao[9])  # fim
        
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
            
            quantidade_total = 0
            
            # Soma ocupações existentes ativas neste momento
            for ocupacao in ocupacoes_item:
                if ocupacao[8] <= momento_meio < ocupacao[9]:
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
        Verifica se o HotMix pode receber uma nova ocupação do item especificado.
        Para o mesmo item, sempre permite (validação de capacidade será feita separadamente).
        Para itens diferentes, não permite sobreposição.
        """
        for ocupacao in self.ocupacoes:
            # Se é o mesmo item, sempre permite (capacidade será validada depois)
            if ocupacao[3] == id_item:
                continue
                
            # Para itens diferentes, não pode haver sobreposição
            if not (fim <= ocupacao[8] or inicio >= ocupacao[9]):
                return False
        
        return True

    def obter_capacidade_disponivel_item(self, id_item: int, inicio: datetime, fim: datetime) -> int:
        """
        Retorna a capacidade disponível para um item específico no período.
        CORRIGIDO: Agora considera corretamente as ocupações existentes do mesmo item.
        """
        quantidade_ocupada_maxima = self.obter_quantidade_maxima_item_periodo(id_item, inicio, fim)
        capacidade_disponivel = self.capacidade_gramas_max - quantidade_ocupada_maxima
        return max(0, capacidade_disponivel)

    def debug_capacidade_item(self, id_item: int, inicio: datetime, fim: datetime) -> dict:
        """
        NOVO: Método de debug para análise detalhada da capacidade de um item.
        Retorna informações detalhadas sobre a ocupação de um item no período.
        """
        ocupacoes_item = [oc for oc in self.ocupacoes if oc[3] == id_item]
        quantidade_maxima = self.obter_quantidade_maxima_item_periodo(id_item, inicio, fim)
        capacidade_disponivel = self.obter_capacidade_disponivel_item(id_item, inicio, fim)
        
        return {
            'id_item': id_item,
            'periodo': f"{inicio.strftime('%H:%M')} - {fim.strftime('%H:%M')}",
            'ocupacoes_existentes': len(ocupacoes_item),
            'quantidade_maxima_periodo': quantidade_maxima,
            'capacidade_disponivel': capacidade_disponivel,
            'capacidade_hotmix_max': self.capacidade_gramas_max,
            'ocupacoes_detalhes': [
                {
                    'ordem': oc[0], 'pedido': oc[1], 'atividade': oc[2],
                    'quantidade': oc[4],
                    'periodo': f"{oc[8].strftime('%H:%M')} - {oc[9].strftime('%H:%M')}"
                }
                for oc in ocupacoes_item
                if not (fim <= oc[8] or inicio >= oc[9])  # sobreposição com período analisado
            ]
        }

    # ==========================================================
    # ✅ Validações
    # ==========================================================
    def validar_capacidade(self, quantidade: int) -> bool:
        """Valida se a quantidade está dentro dos limites de capacidade."""
        if not (self.capacidade_gramas_min <= quantidade <= self.capacidade_gramas_max):
            logger.warning(
                f"❌ Quantidade {quantidade}g fora dos limites do {self.nome} "
                f"({self.capacidade_gramas_min}-{self.capacidade_gramas_max}g)."
            )
            return False
        return True

    def esta_disponivel(self, inicio: datetime, fim: datetime) -> bool:
        """
        Verifica se o equipamento está disponível no período especificado.
        Método mantido para compatibilidade - considera todos os itens.
        """
        # Calcular quantidade total ocupada no período (todos os itens)
        quantidade_ocupada = 0
        for ocupacao in self.ocupacoes:
            if not (fim <= ocupacao[8] or inicio >= ocupacao[9]):  # há sobreposição temporal
                quantidade_ocupada += ocupacao[4]  # quantidade
        
        # Considera disponível se há capacidade livre
        capacidade_livre = self.capacidade_gramas_max - quantidade_ocupada
        return capacidade_livre >= self.capacidade_gramas_min

    def esta_disponivel_para_quantidade(self, quantidade: int, inicio: datetime, fim: datetime) -> bool:
        """
        Verifica se o equipamento pode processar uma quantidade específica no período.
        Método mantido para compatibilidade - considera todos os itens.
        """
        # Calcular quantidade total ocupada no período
        quantidade_ocupada = 0
        for ocupacao in self.ocupacoes:
            if not (fim <= ocupacao[8] or inicio >= ocupacao[9]):  # há sobreposição temporal
                quantidade_ocupada += ocupacao[4]  # quantidade
        
        # Verificar se a nova quantidade cabe
        quantidade_total = quantidade_ocupada + quantidade
        return (self.capacidade_gramas_min <= quantidade_total <= self.capacidade_gramas_max)
    
    # ==========================================================
    # 🍳 Ocupações
    # ==========================================================
    def ocupar(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade: int,
        velocidade: TipoVelocidade,
        chama: TipoChama,
        pressao_chamas: List[TipoPressaoChama],
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """
        Ocupa o equipamento com validação de capacidade considerando intervalos flexíveis.
        Permite sobreposição do mesmo id_item, impede itens diferentes.
        """
        # Validação 1: Capacidade individual
        if not self.validar_capacidade(quantidade):
            return False

        # Validação 2: Disponibilidade (só impede se for item diferente com sobreposição)
        if not self.esta_disponivel_para_item(inicio, fim, id_item):
            logger.warning(
                f"❌ {self.nome} | Ocupado por item diferente entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
            )
            return False

        # Validação 3: Se nova ocupação respeita capacidade em todos os momentos
        if not self.validar_nova_ocupacao_item(id_item, quantidade, inicio, fim):
            quantidade_atual = self.obter_quantidade_maxima_item_periodo(id_item, inicio, fim)
            logger.error(
                f"❌ {self.nome} | Item {id_item}: Nova quantidade {quantidade}g + "
                f"máximo atual {quantidade_atual}g excederia capacidade máxima ({self.capacidade_gramas_max}g)"
            )
            return False

        # Adicionar ocupação
        self.ocupacoes.append((
            id_ordem,
            id_pedido,
            id_atividade,
            id_item,
            quantidade,
            velocidade,
            chama,
            pressao_chamas,
            inicio,
            fim
        ))

        # CORRIGIDO: Log informativo com cálculo correto
        quantidade_maxima_apos = self.obter_quantidade_maxima_item_periodo(id_item, inicio, fim)
        logger.info(
            f"🍳 {self.nome} | Item {id_item}: Nova ocupação {quantidade}g "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} "
            f"(Pico máximo do item após ocupação: {quantidade_maxima_apos}g) "
            f"(Ordem {id_ordem}, Pedido {id_pedido}, Atividade {id_atividade}) | "
            f"Velocidade: {velocidade.name} | Chama: {chama.name} | "
            f"Pressões: {[p.name for p in pressao_chamas]}"
        )
        return True

    def obter_ocupacoes(self) -> List[Tuple[int, int, int, int, int, TipoVelocidade, TipoChama, List[TipoPressaoChama], datetime, datetime]]:
        """Retorna todas as ocupações do equipamento."""
        return self.ocupacoes.copy()

    def obter_ocupacoes_periodo(self, inicio: datetime, fim: datetime) -> List[Tuple[int, int, int, int, int, TipoVelocidade, TipoChama, List[TipoPressaoChama], datetime, datetime]]:
        """Retorna ocupações que se sobrepõem ao período especificado."""
        ocupacoes_periodo = []
        for ocupacao in self.ocupacoes:
            if not (fim <= ocupacao[8] or inicio >= ocupacao[9]):  # há sobreposição temporal
                ocupacoes_periodo.append(ocupacao)
        return ocupacoes_periodo

    def obter_ocupacoes_item_periodo(self, id_item: int, inicio: datetime, fim: datetime) -> List[Tuple[int, int, int, int, int, TipoVelocidade, TipoChama, List[TipoPressaoChama], datetime, datetime]]:
        """Retorna ocupações de um item específico que se sobrepõem ao período."""
        ocupacoes_item = []
        for ocupacao in self.ocupacoes:
            if ocupacao[3] == id_item and not (fim <= ocupacao[8] or inicio >= ocupacao[9]):
                ocupacoes_item.append(ocupacao)
        return ocupacoes_item

    def esta_ocupado(self, momento: datetime) -> bool:
        """Verifica se o equipamento está ocupado em um momento específico."""
        for ocupacao in self.ocupacoes:
            if ocupacao[8] <= momento < ocupacao[9]:
                return True
        return False

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, id_ordem: int, id_pedido: int, id_atividade: int):
        """Libera ocupações específicas por atividade."""
        ocupacoes_iniciais = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido and ocupacao[2] == id_atividade)
        ]

        liberadas = ocupacoes_iniciais - len(self.ocupacoes)
        if liberadas > 0:
            logger.info(
                f"🔓 {self.nome} liberado | {liberadas} ocupações | "
                f"Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade}."
            )
        else:
            logger.warning(
                f"⚠️ Nenhuma ocupação encontrada para liberar | "
                f"Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade}."
            )
    
    def liberar_por_pedido(self, id_ordem: int, id_pedido: int):
        """Libera ocupações específicas por pedido."""
        ocupacoes_iniciais = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido)
        ]

        liberadas = ocupacoes_iniciais - len(self.ocupacoes)
        if liberadas > 0:
            logger.info(
                f"🔓 {self.nome} liberado | {liberadas} ocupações | "
                f"Ordem {id_ordem} | Pedido {id_pedido}."
            )
        else:
            logger.warning(
                f"⚠️ Nenhuma ocupação encontrada para liberar | "
                f"Ordem {id_ordem} | Pedido {id_pedido}."
            )
    
    def liberar_por_ordem(self, id_ordem: int):
        """Libera ocupações específicas por ordem."""
        ocupacoes_iniciais = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if ocupacao[0] != id_ordem
        ]

        liberadas = ocupacoes_iniciais - len(self.ocupacoes)
        if liberadas > 0:
            logger.info(f"🔓 {self.nome} liberado | {liberadas} ocupações | Ordem {id_ordem}.")
        else:
            logger.warning(f"⚠️ Nenhuma ocupação encontrada para liberar | Ordem {id_ordem}.")

    def liberar_por_item(self, id_ordem: int, id_pedido: int, id_atividade: int, id_item: int):
        """Libera ocupações específicas por item."""
        ocupacoes_iniciais = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido and 
                   ocupacao[2] == id_atividade and ocupacao[3] == id_item)
        ]

        liberadas = ocupacoes_iniciais - len(self.ocupacoes)
        if liberadas > 0:
            logger.info(
                f"🔓 {self.nome} liberado | {liberadas} ocupações | "
                f"Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade} | Item {id_item}."
            )
        else:
            logger.warning(
                f"⚠️ Nenhuma ocupação encontrada para liberar | "
                f"Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade} | Item {id_item}."
            )

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        """Libera ocupações que já finalizaram."""
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if ocupacao[9] > horario_atual  # fim > horario_atual
        ]
        liberadas = antes - len(self.ocupacoes)
        
        if liberadas > 0:
            logger.info(f"🔓 {self.nome} liberou {liberadas} ocupações finalizadas até {horario_atual.strftime('%H:%M')}.")
        else:
            logger.warning(f"⚠️ Nenhuma ocupação finalizada encontrada para liberar | Até {horario_atual.strftime('%H:%M')}.")
        
        return liberadas

    def liberar_todas_ocupacoes(self):
        """Limpa todas as ocupações do equipamento."""
        total = len(self.ocupacoes)
        self.ocupacoes.clear()
        logger.info(f"🔓 {self.nome} liberou todas as {total} ocupações.")
        
    def liberar_por_intervalo(self, inicio: datetime, fim: datetime):
        """Libera ocupações que se sobrepõem ao intervalo especificado."""
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if not (ocupacao[8] < fim and ocupacao[9] > inicio)  # remove qualquer sobreposição
        ]
        liberadas = antes - len(self.ocupacoes)

        if liberadas > 0:
            logger.info(
                f"🔓 {self.nome} liberou {liberadas} ocupações no intervalo de "
                f"{inicio.strftime('%H:%M')} a {fim.strftime('%H:%M')}."
            )
        else:
            logger.info(
                f"ℹ️ Nenhuma ocupação encontrada para liberar no intervalo de "
                f"{inicio.strftime('%H:%M')} a {fim.strftime('%H:%M')}."
            )

    # ==========================================================
    # 📅 Agenda e Relatórios
    # ==========================================================
    def mostrar_agenda(self):
        """Mostra agenda detalhada do equipamento."""
        logger.info("==============================================")
        logger.info(f"📅 Agenda do {self.nome}")
        logger.info(f"🔧 Capacidade: {self.capacidade_gramas_min}-{self.capacidade_gramas_max}g")
        logger.info("==============================================")
        
        if not self.ocupacoes:
            logger.info("🔹 Nenhuma ocupação registrada.")
            return
            
        # Ordenar ocupações por horário de início
        ocupacoes_ordenadas = sorted(self.ocupacoes, key=lambda x: x[8])  # ordenar por inicio
        
        for ocupacao in ocupacoes_ordenadas:
            logger.info(
                f"🔸 Ordem {ocupacao[0]} | Pedido {ocupacao[1]} | Atividade {ocupacao[2]} | Item {ocupacao[3]} | "
                f"{ocupacao[4]}g | {ocupacao[8].strftime('%H:%M')} → {ocupacao[9].strftime('%H:%M')} | "
                f"Velocidade: {ocupacao[5].name} | Chama: {ocupacao[6].name} | "
                f"Pressões: {[p.name for p in ocupacao[7]]}"
            )

    def obter_estatisticas_uso(self, inicio: datetime, fim: datetime) -> dict:
        """Retorna estatísticas de uso do equipamento no período."""
        ocupacoes_periodo = self.obter_ocupacoes_periodo(inicio, fim)
        
        if not ocupacoes_periodo:
            return {
                'equipamento_utilizado': False,
                'total_ocupacoes': 0,
                'quantidade_total': 0,
                'quantidade_media': 0.0,
                'tempo_total_ocupado': 0,
                'taxa_utilizacao_temporal': 0.0,
                'velocidades_utilizadas': [],
                'chamas_utilizadas': [],
                'pressoes_utilizadas': []
            }
        
        # Calcular estatísticas
        total_ocupacoes = len(ocupacoes_periodo)
        quantidade_total = sum(ocupacao[4] for ocupacao in ocupacoes_periodo)  # soma das quantidades
        quantidade_media = quantidade_total / total_ocupacoes if total_ocupacoes > 0 else 0.0
        
        # Calcular tempo total ocupado
        tempo_total_ocupado = sum(
            (ocupacao[9] - ocupacao[8]).total_seconds() / 60  # fim - inicio em minutos
            for ocupacao in ocupacoes_periodo
        )
        
        # Calcular taxa de utilização temporal
        periodo_total = (fim - inicio).total_seconds() / 60  # período total em minutos
        taxa_utilizacao_temporal = (tempo_total_ocupado / periodo_total * 100) if periodo_total > 0 else 0.0
        
        # Coletar parâmetros utilizados
        velocidades_utilizadas = list(set(ocupacao[5].name for ocupacao in ocupacoes_periodo))
        chamas_utilizadas = list(set(ocupacao[6].name for ocupacao in ocupacoes_periodo))
        pressoes_utilizadas = list(set(
            p.name for ocupacao in ocupacoes_periodo for p in ocupacao[7]
        ))
        
        return {
            'equipamento_utilizado': True,
            'total_ocupacoes': total_ocupacoes,
            'quantidade_total': quantidade_total,
            'quantidade_media': quantidade_media,
            'tempo_total_ocupado': tempo_total_ocupado,
            'taxa_utilizacao_temporal': taxa_utilizacao_temporal,
            'velocidades_utilizadas': velocidades_utilizadas,
            'chamas_utilizadas': chamas_utilizadas,
            'pressoes_utilizadas': pressoes_utilizadas
        }