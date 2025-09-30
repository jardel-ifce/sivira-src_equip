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
    ✔️ REGRA: Mesma atividade só pode ocupar no mesmo horário (início e fim exatos).
    ✔️ Capacidade de mistura validada por peso com horários rígidos.
    ✔️ MODIFICADO: Agrupamento por id_atividade com horário exato (rigidez como batedeiras).
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
    # 🔍 Validação Dinâmica de Capacidade por ATIVIDADE
    # ==========================================================
    def obter_quantidade_maxima_atividade_periodo(self, id_atividade: int, inicio: datetime, fim: datetime) -> float:
        """
        Calcula a quantidade máxima de uma atividade que estará sendo processada
        simultaneamente na masseira durante qualquer momento do período especificado.
        ✔️ Com a nova regra, só soma ocupações com horário EXATO.
        """
        quantidade_total = 0.0

        # Com a nova regra, só considera ocupações com horário EXATO
        for ocupacao in self.ocupacoes:
            if ocupacao[2] == id_atividade and ocupacao[7] == inicio and ocupacao[8] == fim:
                quantidade_total += ocupacao[4]

        return quantidade_total

    def validar_nova_ocupacao_atividade(self, id_atividade: int, quantidade_nova: float,
                                       inicio: datetime, fim: datetime) -> bool:
        """
        Simula uma nova ocupação e verifica se a capacidade máxima será respeitada.
        ✔️ Com a nova regra, só verifica ocupações com horário exato.
        """
        quantidade_atual = self.obter_quantidade_maxima_atividade_periodo(id_atividade, inicio, fim)
        quantidade_total = quantidade_atual + quantidade_nova

        if not self.validar_capacidade(quantidade_total):
            logger.debug(
                f"❌ {self.nome} | Atividade {id_atividade}: Capacidade excedida "
                f"({quantidade_total}g > {self.capacidade_gramas_max}g)"
            )
            return False

        return True

    def esta_disponivel_para_atividade(self, inicio: datetime, fim: datetime, id_atividade: int) -> bool:
        """
        Verifica se a masseira pode receber uma nova ocupação da atividade especificada.
        ✔️ REGRA: Mesma atividade só pode ocupar no mesmo horário (início e fim exatos).
        Para atividades diferentes, não permite sobreposição.
        """
        for ocupacao in self.ocupacoes:
            ocupacao_id_atividade = ocupacao[2]
            ocupacao_inicio = ocupacao[7]  # início
            ocupacao_fim = ocupacao[8]     # fim

            # Se é a mesma atividade E mesmo horário, permite
            if ocupacao_id_atividade == id_atividade and ocupacao_inicio == inicio and ocupacao_fim == fim:
                continue

            # Para qualquer outra situação, não pode haver sobreposição temporal
            if not (fim <= ocupacao_inicio or inicio >= ocupacao_fim):
                if ocupacao_id_atividade == id_atividade:
                    logger.warning(
                        f"⚠️ {self.nome}: Atividade {id_atividade} só pode ocupar no mesmo horário. "
                        f"Conflito: {inicio.strftime('%H:%M')}-{fim.strftime('%H:%M')} vs "
                        f"{ocupacao_inicio.strftime('%H:%M')}-{ocupacao_fim.strftime('%H:%M')}"
                    )
                else:
                    logger.warning(
                        f"⚠️ {self.nome} ocupada por atividade diferente (ID: {ocupacao_id_atividade}) "
                        f"entre {ocupacao_inicio.strftime('%H:%M')} e {ocupacao_fim.strftime('%H:%M')}."
                    )
                return False

        return True

    # ==========================================================
    # 🔍 Consulta de Ocupação (para o Gestor) - ATUALIZADA
    # ==========================================================
    def atividade_ja_alocada_periodo(self, id_atividade: int, inicio: datetime, fim: datetime) -> bool:
        """Verifica se uma atividade específica já está alocada no período (para o Gestor decidir sobreposição)."""
        for ocupacao in self.ocupacoes:
            if ocupacao[2] == id_atividade and not (fim <= ocupacao[7] or inicio >= ocupacao[8]):
                return True
        return False

    def obter_quantidade_alocada_periodo(self, inicio: datetime, fim: datetime, id_atividade: Optional[int] = None) -> float:
        """
        Retorna a quantidade total alocada no período especificado, opcionalmente filtrada por atividade.
        ATENÇÃO: Para mesma atividade, retorna PICO MÁXIMO de sobreposição, não soma simples.
        """
        if id_atividade is not None:
            # Para atividade específica, retorna pico máximo de sobreposição
            return self.obter_quantidade_maxima_atividade_periodo(id_atividade, inicio, fim)
        else:
            # Para todas as atividades, soma simples (comportamento original)
            quantidade_total = 0.0
            for ocupacao in self.ocupacoes:
                if not (fim <= ocupacao[7] or inicio >= ocupacao[8]):  # há sobreposição temporal
                    quantidade_total += ocupacao[4]
            return quantidade_total

    def obter_ocupacoes_atividade_periodo(self, id_atividade: int, inicio: datetime, fim: datetime) -> List[Tuple[int, int, int, int, float, List[TipoVelocidade], TipoMistura, datetime, datetime]]:
        """Retorna ocupações de uma atividade específica que se sobrepõem ao período."""
        ocupacoes_atividade = []
        for ocupacao in self.ocupacoes:
            if ocupacao[2] == id_atividade and not (fim <= ocupacao[7] or inicio >= ocupacao[8]):
                ocupacoes_atividade.append(ocupacao)
        return ocupacoes_atividade

    def obter_capacidade_disponivel_atividade(self, id_atividade: int, inicio: datetime, fim: datetime) -> float:
        """Retorna a capacidade disponível para uma atividade específica no período."""
        quantidade_ocupada = self.obter_quantidade_maxima_atividade_periodo(id_atividade, inicio, fim)
        return max(0.0, self.capacidade_gramas_max - quantidade_ocupada)

    # Manter métodos originais para compatibilidade, mas agora usam lógica de atividade
    def obter_quantidade_maxima_item_periodo(self, id_item: int, inicio: datetime, fim: datetime) -> float:
        """DEPRECIADO: Usar obter_quantidade_maxima_atividade_periodo. Mantido para compatibilidade."""
        logger.warning("Método depreciado: use obter_quantidade_maxima_atividade_periodo")
        quantidade_total = 0.0

        # Com a nova regra, só considera ocupações com horário EXATO
        for ocupacao in self.ocupacoes:
            if ocupacao[3] == id_item and ocupacao[7] == inicio and ocupacao[8] == fim:
                quantidade_total += ocupacao[4]

        return quantidade_total

    def esta_disponivel_para_item(self, inicio: datetime, fim: datetime, id_item: int) -> bool:
        """DEPRECIADO: Usar esta_disponivel_para_atividade. Mantido para compatibilidade."""
        logger.warning("Método depreciado: use esta_disponivel_para_atividade")

        for ocupacao in self.ocupacoes:
            ocupacao_id_item = ocupacao[3]
            ocupacao_inicio = ocupacao[7]  # início
            ocupacao_fim = ocupacao[8]     # fim

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

    def validar_nova_ocupacao_item(self, id_item: int, quantidade_nova: float,
                                  inicio: datetime, fim: datetime) -> bool:
        """DEPRECIADO: Usar validar_nova_ocupacao_atividade. Mantido para compatibilidade."""
        logger.warning("Método depreciado: use validar_nova_ocupacao_atividade")
        quantidade_atual = self.obter_quantidade_maxima_item_periodo(id_item, inicio, fim)
        quantidade_total = quantidade_atual + quantidade_nova

        if not self.validar_capacidade(quantidade_total):
            logger.debug(
                f"❌ {self.nome} | Item {id_item}: Capacidade excedida "
                f"({quantidade_total}g > {self.capacidade_gramas_max}g)"
            )
            return False

        return True

    def obter_capacidade_disponivel_item(self, id_item: int, inicio: datetime, fim: datetime) -> float:
        """DEPRECIADO: Usar obter_capacidade_disponivel_atividade. Mantido para compatibilidade."""
        logger.warning("Método depreciado: use obter_capacidade_disponivel_atividade")
        quantidade_ocupada = self.obter_quantidade_maxima_item_periodo(id_item, inicio, fim)
        return max(0.0, self.capacidade_gramas_max - quantidade_ocupada)

    def esta_disponivel(self, inicio: datetime, fim: datetime) -> bool:
        """Verifica se a masseira está completamente livre no período."""
        for ocupacao in self.ocupacoes:
            if not (fim <= ocupacao[7] or inicio >= ocupacao[8]):
                logger.warning(
                    f"⚠️ {self.nome} não disponível entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')} "
                    f"devido à atividade {ocupacao[2]} do item {ocupacao[3]}."
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

    def obter_ocupacoes_periodo(self, inicio: datetime, fim: datetime) -> List[Tuple[int, int, int, int, float, List[TipoVelocidade], TipoMistura, datetime, datetime]]:
        """Retorna todas as ocupações que se sobrepõem ao período especificado."""
        ocupacoes_periodo = []
        for ocupacao in self.ocupacoes:
            if not (fim <= ocupacao[7] or inicio >= ocupacao[8]):  # há sobreposição temporal
                ocupacoes_periodo.append(ocupacao)
        return ocupacoes_periodo

    # ==========================================================
    # ✅ Validações (Parâmetros técnicos)
    # ==========================================================
    def validar_capacidade(self, quantidade_gramas: float) -> bool:
        """Valida se a quantidade está dentro da capacidade mínima e máxima."""
        return self.capacidade_gramas_min <= quantidade_gramas <= self.capacidade_gramas_max

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

    def validar_capacidade_total_atividade(self, id_atividade: int, quantidade_adicional: float, inicio: datetime, fim: datetime) -> bool:
        """
        Valida se a capacidade total da atividade não excede o limite considerando picos de sobreposição.
        """
        return self.validar_nova_ocupacao_atividade(id_atividade, quantidade_adicional, inicio, fim)

    def verificar_disponibilidade(
        self, 
        quantidade: float, 
        velocidades: List[TipoVelocidade], 
        tipo_mistura: TipoMistura
    ) -> bool:
        """Verifica se os parâmetros são válidos para a masseira (sem verificar período)."""
        return self.validar_capacidade_individual(quantidade)

    # ==========================================================
    # 🔄 Ocupação e Atualização (MODIFICADO)
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
        VERSÃO MODIFICADA: Adiciona ocupação individual com validação de capacidade para mesma atividade.
        Permite múltiplas ocupações da mesma atividade respeitando capacidade máxima.
        """
        
        # Validações básicas
        if not self.verificar_disponibilidade(quantidade_alocada, velocidades, tipo_mistura):
            return False

        # Verifica disponibilidade (só impede se for atividade diferente com sobreposição)
        if not self.esta_disponivel_para_atividade(inicio, fim, id_atividade):
            logger.warning(
                f"⛔ {self.nome} | Ocupada por atividade diferente entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
            )
            return False

        # VALIDAÇÃO CHAVE: Capacidade máxima para mesma atividade considerando sobreposições
        if not self.validar_nova_ocupacao_atividade(id_atividade, quantidade_alocada, inicio, fim):
            quantidade_atual = self.obter_quantidade_maxima_atividade_periodo(id_atividade, inicio, fim)
            logger.warning(
                f"⚠️ {self.nome} | Atividade {id_atividade}: Nova ocupação {quantidade_alocada}g + "
                f"máximo atual {quantidade_atual}g excederia capacidade máxima ({self.capacidade_gramas_max}g)"
            )
            return False

        # Adiciona ocupação individual (cada pedido tem sua própria ocupação)
        self.ocupacoes.append(
            (id_ordem, id_pedido, id_atividade, id_item, quantidade_alocada, velocidades, tipo_mistura, inicio, fim)
        )

        # Log informativo
        quantidade_maxima_apos = self.obter_quantidade_maxima_atividade_periodo(id_atividade, inicio, fim) + quantidade_alocada
        velocidades_str = ", ".join([v.name for v in velocidades]) if velocidades else "Nenhuma"
        
        # Verifica se há outras ocupações da mesma atividade no mesmo período (economia real)
        ocupacoes_simultaneas = self.obter_ocupacoes_atividade_periodo(id_atividade, inicio, fim)
        economia_msg = ""
        if len(ocupacoes_simultaneas) > 1:
            outros_pedidos = [str(oc[1]) for oc in ocupacoes_simultaneas if oc[1] != id_pedido]
            if outros_pedidos:
                economia_msg = f" | ECONOMIA: Compartilhando equipamento com pedidos {', '.join(outros_pedidos)}"

        logger.info(
            f"🥣 {self.nome} | Atividade {id_atividade}: Nova ocupação {quantidade_alocada}g "
            f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} "
            f"(Pico máximo da atividade: {quantidade_maxima_apos}g) "
            f"(Ordem {id_ordem}, Pedido {id_pedido}, Item {id_item}) | "
            f"Velocidades: {velocidades_str} | Mistura: {tipo_mistura.name if tipo_mistura else 'Nenhuma'}"
            f"{economia_msg}"
        )
        return True

    # ==========================================================
    # 📊 Métodos de Análise de Consolidação Implícita (ATUALIZADA)
    # ==========================================================
    def obter_estatisticas_economia_equipamento(self) -> dict:
        """
        Retorna estatísticas de economia de equipamento baseada em ocupações simultâneas
        da mesma atividade (consolidação implícita).
        """
        
        if not self.ocupacoes:
            return {'economia_equipamentos': 0, 'detalhes': []}
        
        # Agrupar ocupações por período e atividade
        grupos_simultaneos = {}
        
        for ocupacao in self.ocupacoes:
            id_atividade = ocupacao[2]  # Mudança aqui: usa id_atividade
            inicio = ocupacao[7]
            fim = ocupacao[8]
            chave_periodo = f"{id_atividade}_{inicio.isoformat()}_{fim.isoformat()}"
            
            if chave_periodo not in grupos_simultaneos:
                grupos_simultaneos[chave_periodo] = {
                    'id_atividade': id_atividade,
                    'inicio': inicio,
                    'fim': fim,
                    'ocupacoes': []
                }
            
            grupos_simultaneos[chave_periodo]['ocupacoes'].append(ocupacao)
        
        # Calcular economia
        economia_total = 0
        detalhes_economia = []
        
        for chave, grupo in grupos_simultaneos.items():
            num_ocupacoes = len(grupo['ocupacoes'])
            if num_ocupacoes > 1:
                economia = num_ocupacoes - 1  # N ocupações usando 1 equipamento = economia de N-1
                economia_total += economia
                
                pedidos_beneficiados = [oc[1] for oc in grupo['ocupacoes']]
                quantidade_total = sum(oc[4] for oc in grupo['ocupacoes'])
                
                detalhes_economia.append({
                    'id_atividade': grupo['id_atividade'],
                    'periodo': f"{grupo['inicio'].strftime('%H:%M')} - {grupo['fim'].strftime('%H:%M')}",
                    'pedidos_consolidados': pedidos_beneficiados,
                    'quantidade_total': quantidade_total,
                    'ocupacoes_simultâneas': num_ocupacoes,
                    'economia_equipamentos': economia
                })
        
        return {
            'economia_equipamentos': economia_total,
            'consolidações_implícitas': len(detalhes_economia),
            'detalhes': detalhes_economia
        }

    # ==========================================================
    # 🔓 Liberação (mantida - funciona com ocupações individuais)
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

    # Outros métodos de liberação permanecem iguais...
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

    def liberar_por_ordem(self, id_ordem: int):
        """Libera ocupações específicas por ordem."""
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if ocupacao[0] != id_ordem
        ]
        liberadas = antes - len(self.ocupacoes)
        
        if liberadas > 0:
            logger.info(f"🔓 Liberadas {liberadas} ocupações da {self.nome} para Ordem {id_ordem}.")

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        """Libera ocupações que já finalizaram."""
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            ocupacao for ocupacao in self.ocupacoes
            if ocupacao[8] > horario_atual
        ]
        liberadas = antes - len(self.ocupacoes)
        
        if liberadas > 0:
            logger.info(f"🔓 Liberadas {liberadas} ocupações da {self.nome} finalizadas até {horario_atual.strftime('%H:%M')}.")
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
            if not (ocupacao[7] < fim and ocupacao[8] > inicio)
        ]
        liberadas = antes - len(self.ocupacoes)
        
        if liberadas > 0:
            logger.info(f"🔓 Liberadas {liberadas} ocupações da {self.nome} entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}.")

    # ==========================================================
    # 🔓 Método de Compatibilidade
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
    # 🔄 Atualização de ocupações específicas
    # ==========================================================
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
            f"⛔ Ocupação não encontrada para atualizar na {self.nome} | "
            f"Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade}"
        )
        return False

    # ==========================================================
    # 📅 Agenda e Relatórios
    # ==========================================================
    def mostrar_agenda(self):
        """Mostra agenda detalhada da masseira."""
        logger.info("==============================================")
        logger.info(f"📅 Agenda da {self.nome}")
        logger.info("==============================================")

        if not self.ocupacoes:
            logger.info("📹 Nenhuma ocupação registrada.")
            return

        for ocupacao in self.ocupacoes:
            velocidades_str = ", ".join([v.name for v in ocupacao[5]]) if ocupacao[5] else "Nenhuma"
            
            logger.info(
                f"🥣 Ordem {ocupacao[0]} | Pedido {ocupacao[1]} | Atividade {ocupacao[2]} | Item {ocupacao[3]} | "
                f"{ocupacao[4]:.2f}g | {ocupacao[7].strftime('%H:%M')} → {ocupacao[8].strftime('%H:%M')} | "
                f"Velocidades: {velocidades_str} | Mistura: {ocupacao[6].name if ocupacao[6] else 'Nenhuma'}"
            )
        
        # Mostrar estatísticas de economia se houver
        economia_stats = self.obter_estatisticas_economia_equipamento()
        if economia_stats['economia_equipamentos'] > 0:
            logger.info("==============================================")
            logger.info(f"📊 Economia de Equipamentos: {economia_stats['economia_equipamentos']}")
            logger.info(f"📊 Consolidações Implícitas: {economia_stats['consolidações_implícitas']}")

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