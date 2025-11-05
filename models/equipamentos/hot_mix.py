from models.equipamentos.equipamento import Equipamento
from enums.equipamentos.tipo_equipamento import TipoEquipamento
from enums.producao.tipo_setor import TipoSetor
from enums.equipamentos.tipo_chama import TipoChama
from enums.equipamentos.tipo_pressao_chama import TipoPressaoChama
from enums.equipamentos.tipo_velocidade import TipoVelocidade
from typing import List, Tuple
from datetime import datetime
from utils.logs.logger_factory import setup_logger
from utils.logs.registrador_restricoes import registrador_restricoes

# 🔥 Logger exclusivo para HotMix
logger = setup_logger("HotMix")


class HotMix(Equipamento):
    """
    🍳 Equipamento HotMix — Misturadora com Cocção de Alta Performance.
    ✔️ Controle de ocupação por ordem, pedido, atividade, item e quantidade.
    ✔️ Suporta múltiplas velocidades, chamas e pressões de chama.
    ✔️ JANELAS SIMULTÂNEAS: Permite sobreposição do mesmo id_item apenas com períodos idênticos ou distintos.
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
    # 🔧 UTILITÁRIOS TEMPORAIS PRIVADOS
    # ==========================================================
    def _tem_sobreposicao_temporal(self, inicio1: datetime, fim1: datetime,
                                  inicio2: datetime, fim2: datetime) -> bool:
        """Verifica se dois períodos têm sobreposição temporal."""
        return not (fim1 <= inicio2 or inicio1 >= fim2)

    def _tem_simultaneidade_exata(self, inicio1: datetime, fim1: datetime,
                                 inicio2: datetime, fim2: datetime) -> bool:
        """Verifica se dois períodos são exatamente simultâneos."""
        return inicio1 == inicio2 and fim1 == fim2

    def _obter_ocupacoes_item_simultaneas(self, id_item: int, inicio: datetime, fim: datetime):
        """Retorna ocupações do mesmo item que são exatamente simultâneas ao período dado."""
        return [
            ocupacao for ocupacao in self.ocupacoes
            if ocupacao[3] == id_item and self._tem_simultaneidade_exata(
                inicio, fim, ocupacao[8], ocupacao[9]
            )
        ]

    def _obter_ocupacoes_item_sobrepostas(self, id_item: int, inicio: datetime, fim: datetime):
        """Retorna ocupações do mesmo item que se sobrepõem temporalmente ao período dado."""
        return [
            ocupacao for ocupacao in self.ocupacoes
            if ocupacao[3] == id_item and self._tem_sobreposicao_temporal(
                inicio, fim, ocupacao[8], ocupacao[9]
            )
        ]

    def _validar_ocupacao_completa(self, id_item: int, quantidade: int, inicio: datetime, fim: datetime,
                                  contexto: dict) -> bool:
        """
        Executa todas as validações necessárias para uma nova ocupação.
        ✅ SISTEMA SIMPLIFICADO: Aceita quantidades pequenas e registra restrições automaticamente.
        """
        # ✅ SISTEMA SIMPLIFICADO: Apenas verifica se excede o máximo absoluto (restrição de segurança)
        if quantidade > self.capacidade_gramas_max:
            logger.warning(
                f"❌ {self.nome} | Quantidade {quantidade}g excede capacidade máxima absoluta "
                f"({self.capacidade_gramas_max}g) - REJEITADO"
            )
            return False

        # Verificar se há sobreposição temporal com ocupações existentes
        quantidade_ocupada_simultanea = self.obter_quantidade_maxima_item_periodo(id_item, inicio, fim)
        quantidade_total_prevista = quantidade_ocupada_simultanea + quantidade

        # ✅ SISTEMA SIMPLIFICADO: Apenas rejeita se exceder o máximo absoluto
        if quantidade_total_prevista > self.capacidade_gramas_max:
            logger.warning(
                f"❌ {self.nome} | Item {id_item}: Capacidade máxima excedida com janelas simultâneas "
                f"({quantidade_total_prevista}g > {self.capacidade_gramas_max}g)"
            )
            return False

        # ✅ REGISTRAR RESTRIÇÕES para quantidades pequenas
        if quantidade < self.capacidade_gramas_min:
            # Registrar restrição automaticamente
            registrador_restricoes.registrar_restricao(
                id_ordem=contexto.get('id_ordem', 0),
                id_pedido=contexto.get('id_pedido', 0),
                id_atividade=contexto.get('id_atividade', 0),
                id_item=contexto.get('id_item', 0),
                equipamento_nome=self.nome,
                capacidade_atual=quantidade,
                capacidade_minima=self.capacidade_gramas_min,
                inicio=contexto.get('inicio'),
                fim=contexto.get('fim'),
                detalhes_extras={
                    "tipo_restricao": "CAPACIDADE_MINIMA",
                    "velocidade": contexto.get('velocidade'),
                    "chama": contexto.get('chama'),
                    "pressao": contexto.get('pressao')
                }
            )
            logger.info(
                f"🔧 {self.nome} | Quantidade {quantidade}g < mín {self.capacidade_gramas_min}g "
                f"(Atividade {contexto.get('id_atividade', 'N/A')}) - ACEITO com restrição registrada"
            )

        return True

    def _criar_contexto_ocupacao(self, id_ordem: int, id_pedido: int, id_atividade: int, id_item: int,
                               inicio: datetime, fim: datetime, velocidade: TipoVelocidade,
                               chama: TipoChama, pressao_chamas: List[TipoPressaoChama]) -> dict:
        """Cria o contexto de uma ocupação para logging e validação."""
        return {
            'id_ordem': id_ordem,
            'id_pedido': id_pedido,
            'id_atividade': id_atividade,
            'id_item': id_item,
            'inicio': inicio,
            'fim': fim,
            'velocidade': velocidade.name if hasattr(velocidade, 'name') else str(velocidade),
            'chama': chama.name if hasattr(chama, 'name') else str(chama),
            'pressao': [p.name if hasattr(p, 'name') else str(p) for p in pressao_chamas]
        }

    def _adicionar_ocupacao(self, id_ordem: int, id_pedido: int, id_atividade: int, id_item: int,
                          quantidade: int, velocidade: TipoVelocidade, chama: TipoChama,
                          pressao_chamas: List[TipoPressaoChama], inicio: datetime, fim: datetime):
        """Adiciona uma nova ocupação e registra log informativo."""
        self.ocupacoes.append((
            id_ordem, id_pedido, id_atividade, id_item, quantidade,
            velocidade, chama, pressao_chamas, inicio, fim
        ))

        # Log informativo com cálculo de janelas simultâneas
        quantidade_maxima_simultanea_apos = self.obter_quantidade_maxima_item_periodo(id_item, inicio, fim)
        logger.info(
            f"🍳 {self.nome} | Item {id_item}: Nova ocupação {quantidade}g "
            f"de {inicio.strftime('%Y-%m-%d %H:%M')} até {fim.strftime('%Y-%m-%d %H:%M')} "
            f"(Pico simultâneo do item: {quantidade_maxima_simultanea_apos}g) "
            f"(Ordem {id_ordem}, Pedido {id_pedido}, Atividade {id_atividade}) | "
            f"Velocidade: {velocidade.name} | Chama: {chama.name} | "
            f"Pressões: {[p.name for p in pressao_chamas]} | [JANELAS SIMULTÂNEAS]"
        )

    # ==========================================================
    # 🔍 Validação Dinâmica de Capacidade (ORIGINAL - Mantido)
    # ==========================================================
    def obter_quantidade_maxima_item_periodo(self, id_item: int, inicio: datetime, fim: datetime) -> int:
        """
        🎯 JANELAS SIMULTÂNEAS: Calcula a quantidade máxima de um item considerando apenas ocupações simultâneas.
        """
        ocupacoes_simultaneas = self._obter_ocupacoes_item_simultaneas(id_item, inicio, fim)
        return sum(ocupacao[4] for ocupacao in ocupacoes_simultaneas)


    def esta_disponivel_para_item_no_periodo(self, inicio: datetime, fim: datetime, id_item: int) -> bool:
        """
        🎯 JANELAS SIMULTÂNEAS: Verifica disponibilidade temporal do HotMix para um item específico.

        Regras de validação:
        - ❌ Itens diferentes: Não permite qualquer sobreposição temporal
        - ✅ Mesmo item: Permite simultaneidade exata (mesmo início E fim)
        - ✅ Mesmo item: Permite períodos completamente distintos (sem sobreposição)
        - ❌ Mesmo item: Bloqueia sobreposições parciais

        Args:
            inicio: Momento de início da nova ocupação
            fim: Momento de fim da nova ocupação
            id_item: ID do item a ser processado

        Returns:
            bool: True se disponível, False caso contrário
        """
        for ocupacao in self.ocupacoes:
            inicio_existente = ocupacao[8]
            fim_existente = ocupacao[9]
            id_item_existente = ocupacao[3]

            # Para itens diferentes, não pode haver sobreposição
            if id_item_existente != id_item:
                if self._tem_sobreposicao_temporal(inicio, fim, inicio_existente, fim_existente):
                    logger.debug(f"❌ {self.nome}: Ocupado por item diferente ({id_item_existente}) no período")
                    return False
            else:
                # Para o mesmo item, aplicar regra de janelas simultâneas
                simultaneidade_exata = self._tem_simultaneidade_exata(inicio, fim, inicio_existente, fim_existente)
                periodos_distintos = not self._tem_sobreposicao_temporal(inicio, fim, inicio_existente, fim_existente)

                if not (simultaneidade_exata or periodos_distintos):
                    logger.debug(f"❌ {self.nome}: Sobreposição temporal inválida para item {id_item} - período {inicio.strftime('%Y-%m-%d %H:%M')}-{fim.strftime('%Y-%m-%d %H:%M')} conflita com {inicio_existente.strftime('%Y-%m-%d %H:%M')}-{fim_existente.strftime('%Y-%m-%d %H:%M')}")
                    return False

        return True

    def obter_capacidade_disponivel_item(self, id_item: int, inicio: datetime, fim: datetime) -> int:
        """
        🎯 JANELAS SIMULTÂNEAS: Retorna a capacidade disponível para um item específico no período considerando janelas simultâneas.
        """
        quantidade_ocupada_simultanea = self.obter_quantidade_maxima_item_periodo(id_item, inicio, fim)
        capacidade_disponivel = self.capacidade_gramas_max - quantidade_ocupada_simultanea
        return max(0, capacidade_disponivel)

    # ==========================================================
    # 🎯 NOVOS MÉTODOS PARA JANELAS SIMULTÂNEAS
    # ==========================================================


    def validar_nova_ocupacao_item(self, id_item: int, quantidade_nova: int,
                                  inicio: datetime, fim: datetime) -> bool:
        """
        🎯 JANELAS SIMULTÂNEAS: Valida se uma nova ocupação pode ser aceita sem exceder capacidade.

        Considera apenas ocupações simultâneas exatas do mesmo item (mesmo início E fim).
        Ocupações com períodos diferentes não interferem na capacidade.

        Args:
            id_item: ID do item a ser processado
            quantidade_nova: Quantidade em gramas da nova ocupação
            inicio: Momento de início da nova ocupação
            fim: Momento de fim da nova ocupação

        Returns:
            bool: True se a capacidade permite, False se exceder limite
        """
        quantidade_ocupada_simultanea = self.obter_quantidade_maxima_item_periodo(id_item, inicio, fim)
        quantidade_total_prevista = quantidade_ocupada_simultanea + quantidade_nova
        
        if quantidade_total_prevista > self.capacidade_gramas_max:
            logger.debug(
                f"❌ {self.nome} | Item {id_item}: Capacidade excedida com janelas simultâneas "
                f"({quantidade_total_prevista}g > {self.capacidade_gramas_max}g)"
            )
            return False
        
        return True



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
            'periodo': f"{inicio.strftime('%Y-%m-%d %H:%M')} - {fim.strftime('%Y-%m-%d %H:%M')}",
            'ocupacoes_existentes': len(ocupacoes_item),
            'quantidade_maxima': quantidade_maxima,
            'capacidade_disponivel': capacidade_disponivel,
            'capacidade_hotmix_max': self.capacidade_gramas_max,
            'ocupacoes_detalhes': [
                {
                    'ordem': oc[0], 'pedido': oc[1], 'atividade': oc[2],
                    'quantidade': oc[4],
                    'periodo': f"{oc[8].strftime('%Y-%m-%d %H:%M')} - {oc[9].strftime('%Y-%m-%d %H:%M')}",
                    'simultaneidade': 'EXATA' if (oc[8] == inicio and oc[9] == fim) else 'DIFERENTE'
                }
                for oc in ocupacoes_item
                if not (fim <= oc[8] or inicio >= oc[9])  # sobreposição com período analisado
            ]
        }

    # ==========================================================
    # ✅ Validações (MANTIDAS)
    # ==========================================================
    def validar_capacidade(
        self,
        quantidade: int,
        contexto_restricao: dict = None
    ) -> bool:
        """
        Valida capacidade e registra restrições quando abaixo do mínimo.
        Agora todos os equipamentos permitem alocação mesmo abaixo do mínimo, registrando restrições.

        Args:
            quantidade: Quantidade a ser validada
            contexto_restricao: Dados para registrar restrição (ordem, pedido, atividade, etc.)
        """

        # Verificar se excede capacidade máxima (limite rígido)
        if quantidade > self.capacidade_gramas_max:
            logger.warning(
                f"❌ Quantidade {quantidade}g excede capacidade máxima do {self.nome} "
                f"({self.capacidade_gramas_max}g) - REJEITADO"
            )
            return False

        # 🆕 NOVA LÓGICA: Aceitar abaixo da capacidade mínima e registrar restrição
        if quantidade < self.capacidade_gramas_min:
            if contexto_restricao:
                # Registrar restrição
                registrador_restricoes.registrar_restricao(
                    id_ordem=contexto_restricao.get('id_ordem', 0),
                    id_pedido=contexto_restricao.get('id_pedido', 0),
                    id_atividade=contexto_restricao.get('id_atividade', 0),
                    id_item=contexto_restricao.get('id_item', 0),
                    equipamento_nome=self.nome,
                    capacidade_atual=quantidade,
                    capacidade_minima=self.capacidade_gramas_min,
                    inicio=contexto_restricao.get('inicio'),
                    fim=contexto_restricao.get('fim'),
                    detalhes_extras={
                        "tipo_restricao": "CAPACIDADE_MINIMA",
                        "velocidade": contexto_restricao.get('velocidade'),
                        "chama": contexto_restricao.get('chama'),
                        "pressao": contexto_restricao.get('pressao')
                    }
                )
                logger.warning(
                    f"⚠️ RESTRIÇÃO ACEITA: {self.nome} - Capacidade {quantidade}g < mín {self.capacidade_gramas_min}g "
                    f"(Atividade {contexto_restricao.get('id_atividade', 'N/A')}) - Alocação permitida com flag de restrição"
                )
            else:
                logger.warning(
                    f"⚠️ Quantidade {quantidade}g abaixo do mínimo ({self.capacidade_gramas_min}g) "
                    f"mas sem contexto para registrar restrição"
                )
            # Aceitar mesmo assim
            return True

        # Quantidade dentro da faixa normal
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
    # 🍳 Ocupações (MÉTODO ORIGINAL MANTIDO)
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
        fim: datetime,
    ) -> bool:
        """
        🎯 JANELAS SIMULTÂNEAS: Ocupa o equipamento com validação de janelas simultâneas.
        """
        contexto = self._criar_contexto_ocupacao(
            id_ordem, id_pedido, id_atividade, id_item, inicio, fim,
            velocidade, chama, pressao_chamas
        )

        if not self._validar_ocupacao_completa(id_item, quantidade, inicio, fim, contexto):
            return False

        self._adicionar_ocupacao(
            id_ordem, id_pedido, id_atividade, id_item, quantidade,
            velocidade, chama, pressao_chamas, inicio, fim
        )
        return True

    def obter_ocupacoes(self) -> List[Tuple[int, int, int, int, int, TipoVelocidade, TipoChama, List[TipoPressaoChama], datetime, datetime]]:
        """Retorna todas as ocupações do equipamento."""
        return self.ocupacoes.copy()

    def obter_ocupacoes_periodo(self, inicio: datetime, fim: datetime) -> List[Tuple[int, int, int, int, int, TipoVelocidade, TipoChama, List[TipoPressaoChama], datetime, datetime]]:
        """Retorna ocupações que se sobrepõem ao período especificado."""
        return [
            ocupacao for ocupacao in self.ocupacoes
            if self._tem_sobreposicao_temporal(inicio, fim, ocupacao[8], ocupacao[9])
        ]

    def obter_ocupacoes_item_periodo(self, id_item: int, inicio: datetime, fim: datetime) -> List[Tuple[int, int, int, int, int, TipoVelocidade, TipoChama, List[TipoPressaoChama], datetime, datetime]]:
        """Retorna ocupações de um item específico que se sobrepõem ao período."""
        return self._obter_ocupacoes_item_sobrepostas(id_item, inicio, fim)

    def esta_ocupado(self, momento: datetime) -> bool:
        """Verifica se o equipamento está ocupado em um momento específico."""
        for ocupacao in self.ocupacoes:
            if ocupacao[8] <= momento < ocupacao[9]:
                return True
        return False

    # ==========================================================
    # 🔓 Liberação (MANTIDAS)
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
            logger.info(f"🔓 {self.nome} liberou {liberadas} ocupações finalizadas até {horario_atual.strftime('%Y-%m-%d %H:%M')}.")
        else:
            logger.warning(f"⚠️ Nenhuma ocupação finalizada encontrada para liberar | Até {horario_atual.strftime('%Y-%m-%d %H:%M')}.")
        
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
                f"{inicio.strftime('%Y-%m-%d %H:%M')} a {fim.strftime('%Y-%m-%d %H:%M')}."
            )
        else:
            logger.info(
                f"ℹ️ Nenhuma ocupação encontrada para liberar no intervalo de "
                f"{inicio.strftime('%Y-%m-%d %H:%M')} a {fim.strftime('%Y-%m-%d %H:%M')}."
            )

    # ==========================================================
    # 📅 Agenda e Relatórios (MANTIDAS)
    # ==========================================================
    def mostrar_agenda(self):
        """Mostra agenda detalhada do equipamento."""
        logger.info("==============================================")
        logger.info(f"📅 Agenda do {self.nome} - JANELAS SIMULTÂNEAS")
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
                f"{ocupacao[4]}g | {ocupacao[8].strftime('%Y-%m-%d %H:%M')} → {ocupacao[9].strftime('%Y-%m-%d %H:%M')} | "
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