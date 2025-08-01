from models.equipamentos.equipamento import Equipamento
from enums.equipamentos.tipo_equipamento import TipoEquipamento
from enums.producao.tipo_setor import TipoSetor
from typing import List, Tuple, Optional, Dict
from datetime import datetime, timedelta
from utils.logs.logger_factory import setup_logger

# 🍟 Logger exclusivo da Fritadeira
logger = setup_logger('Fritadeira')


class Fritadeira(Equipamento):
    """
    🍟 Representa uma Fritadeira com controle individual por frações.
    ✔️ Valida capacidade mínima e máxima por EQUIPAMENTO TOTAL (corrigido).
    ✔️ Controla temperatura e tempo de setup.
    ✔️ Permite múltiplas ocupações simultâneas por fração individual.
    ✔️ Cada fração é tratada de forma independente.
    ✔️ Limites de capacidade aplicados ao equipamento como um todo.
    ✅ ATUALIZADO: Acesso por índices nas tuplas para melhor performance
    ✅ MELHORADO: Validação de temperatura simultânea
    """

    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        numero_operadores: int,
        numero_fracoes: int,
        capacidade_gramas_min: int,
        capacidade_gramas_max: int,
        faixa_temperatura_min: int,
        faixa_temperatura_max: int,
        setup_minutos: int
    ):
        super().__init__(
            id=id,
            nome=nome,
            setor=setor,
            numero_operadores=numero_operadores,
            tipo_equipamento=TipoEquipamento.FRITADEIRAS,
            status_ativo=True
        )

        self.numero_fracoes = numero_fracoes
        self.capacidade_gramas_min = capacidade_gramas_min
        self.capacidade_gramas_max = capacidade_gramas_max
        self.faixa_temperatura_min = faixa_temperatura_min
        self.faixa_temperatura_max = faixa_temperatura_max
        self.setup_minutos = setup_minutos

        # 🍟 Ocupações por fração individual: cada fração é uma lista separada
        # Estrutura: (id_ordem, id_pedido, id_atividade, id_item, quantidade, temperatura, setup_minutos, inicio, fim)
        # Índices:   [0]       [1]        [2]           [3]      [4]         [5]           [6]             [7]     [8]
        self.ocupacoes_por_fracao: List[List[Tuple[int, int, int, int, int, int, int, datetime, datetime]]] = [
            [] for _ in range(numero_fracoes)
        ]

    # ==========================================================
    # 🔍 Consulta de Ocupação - ATUALIZADO com acesso por índices
    # ==========================================================
    def fracao_disponivel(self, fracao_index: int, inicio: datetime, fim: datetime) -> bool:
        """Verifica se uma fração específica está disponível no período."""
        if fracao_index < 0 or fracao_index >= self.numero_fracoes:
            return False
            
        for ocupacao in self.ocupacoes_por_fracao[fracao_index]:
            # Acesso por índices: inicio=[7], fim=[8]
            if not (fim <= ocupacao[7] or inicio >= ocupacao[8]):  # há sobreposição
                return False
        return True

    def fracoes_disponiveis_periodo(self, inicio: datetime, fim: datetime) -> List[int]:
        """Retorna lista de índices das frações disponíveis no período."""
        return [
            i for i in range(self.numero_fracoes)
            if self.fracao_disponivel(i, inicio, fim)
        ]

    def quantidade_fracoes_disponiveis(self, inicio: datetime, fim: datetime) -> int:
        """Retorna quantidade de frações disponíveis no período."""
        return len(self.fracoes_disponiveis_periodo(inicio, fim))

    def calcular_quantidade_total_periodo(self, inicio: datetime, fim: datetime) -> int:
        """Calcula a quantidade total ocupada no equipamento durante o período."""
        quantidade_total = 0
        for fracao_index in range(self.numero_fracoes):
            for ocupacao in self.ocupacoes_por_fracao[fracao_index]:
                # Acesso por índices: quantidade=[4], inicio=[7], fim=[8]
                if not (fim <= ocupacao[7] or inicio >= ocupacao[8]):  # há sobreposição temporal
                    quantidade_total += ocupacao[4]
        return quantidade_total

    def calcular_quantidade_maxima_periodo(self, inicio: datetime, fim: datetime) -> int:
        """Calcula a quantidade máxima ocupada simultaneamente durante o período."""
        # Cria lista de eventos (início e fim) com suas quantidades
        eventos = []
        for fracao_index in range(self.numero_fracoes):
            for ocupacao in self.ocupacoes_por_fracao[fracao_index]:
                # Acesso por índices: quantidade=[4], inicio=[7], fim=[8]
                if not (fim <= ocupacao[7] or inicio >= ocupacao[8]):  # há sobreposição temporal
                    eventos.append((ocupacao[7], ocupacao[4], 'inicio'))
                    eventos.append((ocupacao[8], ocupacao[4], 'fim'))
        
        # Ordena eventos por tempo
        eventos.sort()
        
        quantidade_atual = 0
        quantidade_maxima = 0
        
        for tempo, qtd, tipo in eventos:
            if tipo == 'inicio':
                quantidade_atual += qtd
                quantidade_maxima = max(quantidade_maxima, quantidade_atual)
            else:  # fim
                quantidade_atual -= qtd
        
        return quantidade_maxima

    def obter_ocupacoes_fracao(self, fracao_index: int) -> List[Tuple[int, int, int, int, int, int, int, datetime, datetime]]:
        """Retorna todas as ocupações de uma fração específica."""
        if fracao_index < 0 or fracao_index >= self.numero_fracoes:
            return []
        return self.ocupacoes_por_fracao[fracao_index].copy()

    def obter_ocupacoes_periodo(self, inicio: datetime, fim: datetime) -> List[Tuple[int, int, int, int, int, int, int, datetime, datetime, int]]:
        """Retorna todas as ocupações que se sobrepõem ao período especificado, incluindo índice da fração."""
        ocupacoes_periodo = []
        for fracao_index in range(self.numero_fracoes):
            for ocupacao in self.ocupacoes_por_fracao[fracao_index]:
                # Acesso por índices: inicio=[7], fim=[8]
                if not (fim <= ocupacao[7] or inicio >= ocupacao[8]):  # há sobreposição temporal
                    # Adicionar índice da fração no final
                    ocupacoes_periodo.append((*ocupacao, fracao_index))
        return ocupacoes_periodo

    def obter_status_fracoes(self, momento: datetime) -> List[bool]:
        """Retorna status de ocupação de cada fração em um momento específico."""
        status = []
        for fracao_index in range(self.numero_fracoes):
            ocupada = any(
                ocupacao[7] <= momento < ocupacao[8]  # inicio <= momento < fim
                for ocupacao in self.ocupacoes_por_fracao[fracao_index]
            )
            status.append(ocupada)
        return status

    def obter_todas_ocupacoes(self) -> List[Tuple[int, int, int, int, int, int, int, datetime, datetime, int]]:
        """Retorna todas as ocupações da fritadeira com índice da fração."""
        todas_ocupacoes = []
        for fracao_index in range(self.numero_fracoes):
            for ocupacao in self.ocupacoes_por_fracao[fracao_index]:
                todas_ocupacoes.append((*ocupacao, fracao_index))
        return todas_ocupacoes

    # ==========================================================
    # ✅ Validações - CORRIGIDAS PARA EQUIPAMENTO TOTAL + MELHORIAS
    # ==========================================================
    def validar_quantidade_individual(self, quantidade: int) -> bool:
        """Valida se a quantidade individual está dentro dos limites básicos."""
        if quantidade <= 0:
            logger.warning(f"❌ Quantidade {quantidade} deve ser positiva")
            return False
        return True

    def validar_quantidade_total_equipamento(self, nova_quantidade: int, inicio: datetime, fim: datetime) -> bool:
        """Valida se a nova quantidade não excede a capacidade total do equipamento."""
        quantidade_maxima_atual = self.calcular_quantidade_maxima_periodo(inicio, fim)
        quantidade_final_maxima = quantidade_maxima_atual + nova_quantidade
        
        if quantidade_final_maxima < self.capacidade_gramas_min:
            logger.warning(
                f"❌ Quantidade total {quantidade_final_maxima} ficará abaixo do mínimo "
                f"({self.capacidade_gramas_min}) do equipamento {self.nome}"
            )
            return False
        
        if quantidade_final_maxima > self.capacidade_gramas_max:
            logger.warning(
                f"❌ Quantidade total {quantidade_final_maxima} excederá o máximo "
                f"({self.capacidade_gramas_max}) do equipamento {self.nome}"
            )
            return False
        
        return True

    def validar_temperatura(self, temperatura: int) -> bool:
        """Valida se a temperatura está dentro dos limites da fritadeira."""
        if not (self.faixa_temperatura_min <= temperatura <= self.faixa_temperatura_max):
            logger.warning(
                f"❌ Temperatura {temperatura}°C fora dos limites da fritadeira "
                f"({self.faixa_temperatura_min}-{self.faixa_temperatura_max}°C) do {self.nome}"
            )
            return False
        return True

    def validar_temperatura_simultanea(self, temperatura: int, inicio: datetime, fim: datetime) -> bool:
        """
        🌡️ MELHORIA: Valida se a temperatura é compatível com ocupações simultâneas.
        
        REGRA: Todas as ocupações que se sobrepõem temporalmente devem ter a mesma temperatura,
        independente do id_item ou fração.
        
        Args:
            temperatura: Nova temperatura a ser validada
            inicio: Início do período da nova ocupação
            fim: Fim do período da nova ocupação
        
        Returns:
            bool: True se compatível, False se houver conflito
        """
        for fracao_index in range(self.numero_fracoes):
            for ocupacao in self.ocupacoes_por_fracao[fracao_index]:
                # Acesso por índices: temperatura=[5], inicio=[7], fim=[8]
                temp_ocupacao = ocupacao[5]
                inicio_ocupacao = ocupacao[7]
                fim_ocupacao = ocupacao[8]
                
                # Verifica sobreposição temporal
                if not (fim <= inicio_ocupacao or inicio >= fim_ocupacao):
                    if temp_ocupacao != temperatura:
                        logger.warning(
                            f"❌ Conflito de temperatura na {self.nome}: "
                            f"Nova ocupação {temperatura}°C vs ocupação existente {temp_ocupacao}°C "
                            f"na fração {fracao_index + 1}"
                        )
                        return False
        return True

    def verificar_disponibilidade_fracao(
        self, 
        fracao_index: int, 
        quantidade: int, 
        temperatura: int,
        inicio: datetime, 
        fim: datetime
    ) -> bool:
        """
        ✅ VERSÃO MELHORADA: Inclui validação de temperatura simultânea.
        Verifica se é possível ocupar uma fração específica com os parâmetros dados.
        """
        # Validação 1: Quantidade individual básica
        if not self.validar_quantidade_individual(quantidade):
            return False
        
        # Validação 2: Capacidade total do equipamento
        if not self.validar_quantidade_total_equipamento(quantidade, inicio, fim):
            return False
        
        # Validação 3: Temperatura individual da fritadeira
        if not self.validar_temperatura(temperatura):
            return False
        
        # 🆕 Validação 4: Temperatura em ocupações simultâneas
        if not self.validar_temperatura_simultanea(temperatura, inicio, fim):
            return False
        
        # Validação 5: Disponibilidade da fração
        if not self.fracao_disponivel(fracao_index, inicio, fim):
            return False
        
        return True

    def verificar_disponibilidade_equipamento(
        self, 
        quantidade: int, 
        temperatura: int,
        inicio: datetime, 
        fim: datetime
    ) -> bool:
        """
        ✅ VERSÃO MELHORADA: Inclui validação de temperatura simultânea.
        Verifica se é possível ocupar o equipamento (qualquer fração) com os parâmetros dados.
        """
        # Validação 1: Quantidade individual básica
        if not self.validar_quantidade_individual(quantidade):
            return False
        
        # Validação 2: Capacidade total do equipamento
        if not self.validar_quantidade_total_equipamento(quantidade, inicio, fim):
            return False
        
        # Validação 3: Temperatura individual da fritadeira
        if not self.validar_temperatura(temperatura):
            return False
        
        # 🆕 Validação 4: Temperatura em ocupações simultâneas
        if not self.validar_temperatura_simultanea(temperatura, inicio, fim):
            return False
        
        # Validação 5: Existe pelo menos uma fração disponível
        fracoes_livres = self.fracoes_disponiveis_periodo(inicio, fim)
        if not fracoes_livres:
            logger.warning(f"❌ Nenhuma fração disponível na {self.nome} no período especificado")
            return False
        
        return True

    # ==========================================================
    # 🍟 Ocupação e Atualização - ATUALIZADO com acesso por índices
    # ==========================================================
    def adicionar_ocupacao_fracao(
        self,
        fracao_index: int,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade: int,
        temperatura: int,
        setup_minutos: int,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """Adiciona uma ocupação específica a uma fração específica."""
        if fracao_index < 0 or fracao_index >= self.numero_fracoes:
            logger.warning(f"❌ Índice de fração inválido: {fracao_index}")
            return False

        if not self.verificar_disponibilidade_fracao(fracao_index, quantidade, temperatura, inicio, fim):
            return False

        self.ocupacoes_por_fracao[fracao_index].append(
            (id_ordem, id_pedido, id_atividade, id_item, quantidade, temperatura, setup_minutos, inicio, fim)
        )

        # Log com informação da capacidade total após adição
        quantidade_total_apos = self.calcular_quantidade_maxima_periodo(inicio, fim)
        logger.info(
            f"🍟 Ocupação adicionada na {self.nome} - Fração {fracao_index + 1} | "
            f"Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade} | Item {id_item} | "
            f"Quantidade: {quantidade} | Temp: {temperatura}°C | Setup: {setup_minutos}min | "
            f"{inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')} | "
            f"Capacidade total após: {quantidade_total_apos}/{self.capacidade_gramas_max}"
        )
        return True

    def sobrescrever_ocupacao_fracao(
        self,
        fracao_index: int,
        ocupacoes: List[Tuple[int, int, int, int, int, int, int, datetime, datetime]]
    ) -> bool:
        """Sobrescreve completamente as ocupações de uma fração específica com validação."""
        if fracao_index < 0 or fracao_index >= self.numero_fracoes:
            logger.warning(f"❌ Índice de fração inválido: {fracao_index}")
            return False

        # Backup das ocupações originais para rollback se necessário
        ocupacoes_backup = self.ocupacoes_por_fracao[fracao_index].copy()

        # VALIDAÇÃO 1: Verificar cada ocupação individualmente
        for i, ocupacao in enumerate(ocupacoes):
            # Acesso por índices: quantidade=[4], temperatura=[5], setup=[6], inicio=[7], fim=[8]
            qtd = ocupacao[4]
            temp = ocupacao[5]
            setup = ocupacao[6]
            ini = ocupacao[7]
            fim_ocup = ocupacao[8]
            
            # Validar quantidade individual
            if not self.validar_quantidade_individual(qtd):
                logger.error(f"❌ Ocupação {i+1}: Quantidade {qtd} inválida para {self.nome}")
                return False
            
            # Validar temperatura
            if not self.validar_temperatura(temp):
                logger.error(f"❌ Ocupação {i+1}: Temperatura {temp}°C inválida para {self.nome}")
                return False
            
            # Validar setup (deve ser positivo)
            if setup < 0:
                logger.error(f"❌ Ocupação {i+1}: Setup {setup} minutos deve ser positivo")
                return False
            
            # Validar período temporal (início antes do fim)
            if ini >= fim_ocup:
                logger.error(f"❌ Ocupação {i+1}: Período inválido {ini} >= {fim_ocup}")
                return False

        # VALIDAÇÃO 2: Verificar conflitos temporais entre ocupações da mesma fração
        for i, ocupacao1 in enumerate(ocupacoes):
            for j, ocupacao2 in enumerate(ocupacoes[i+1:], i+1):
                # Acesso por índices: inicio=[7], fim=[8]
                ini1, fim1 = ocupacao1[7], ocupacao1[8]
                ini2, fim2 = ocupacao2[7], ocupacao2[8]
                
                # Verificar sobreposição temporal
                if not (fim1 <= ini2 or ini1 >= fim2):
                    logger.error(
                        f"❌ Conflito temporal entre ocupações {i+1} e {j+1}: "
                        f"({ini1}-{fim1}) sobrepõe ({ini2}-{fim2})"
                    )
                    return False

        # VALIDAÇÃO 3: Simular a mudança e verificar capacidade total do equipamento
        # Temporariamente aplicar as novas ocupações
        self.ocupacoes_por_fracao[fracao_index] = ocupacoes.copy()
        
        # Verificar se a capacidade total será respeitada em todos os períodos
        for ocupacao in ocupacoes:
            # Acesso por índices: quantidade=[4], temperatura=[5], inicio=[7], fim=[8]
            qtd = ocupacao[4]
            temp = ocupacao[5]
            ini = ocupacao[7]
            fim_ocup = ocupacao[8]
            
            # Verificar temperatura simultânea
            if not self.validar_temperatura_simultanea(temp, ini, fim_ocup):
                # Rollback
                self.ocupacoes_por_fracao[fracao_index] = ocupacoes_backup
                logger.error(f"❌ Conflito de temperatura detectado no período {ini}-{fim_ocup}")
                return False
            
            quantidade_maxima = self.calcular_quantidade_maxima_periodo(ini, fim_ocup)
            if quantidade_maxima < self.capacidade_gramas_min or quantidade_maxima > self.capacidade_gramas_max:
                # Rollback
                self.ocupacoes_por_fracao[fracao_index] = ocupacoes_backup
                logger.error(
                    f"❌ Capacidade total do equipamento ({quantidade_maxima}) "
                    f"ficará fora dos limites ({self.capacidade_gramas_min}-{self.capacidade_gramas_max}) "
                    f"no período {ini}-{fim_ocup}"
                )
                return False

        # Se chegou até aqui, todas as validações passaram
        logger.info(
            f"✅ Ocupações da fração {fracao_index + 1} da {self.nome} foram sobrescritas com validação. "
            f"Total de ocupações: {len(ocupacoes)}"
        )
        return True

    def encontrar_fracao_para_ocupacao(self, quantidade: int, temperatura: int, inicio: datetime, fim: datetime) -> Optional[int]:
        """Encontra a primeira fração disponível para ocupação, considerando capacidade total."""
        if not self.verificar_disponibilidade_equipamento(quantidade, temperatura, inicio, fim):
            return None
        
        fracoes_livres = self.fracoes_disponiveis_periodo(inicio, fim)
        return fracoes_livres[0] if fracoes_livres else None

    def ocupar(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade: int,
        temperatura: int,
        setup_minutos: int,
        inicio: datetime,
        fim: datetime,
        fracao_index: Optional[int] = None
    ) -> bool:
        """
        Ocupa uma fração específica ou encontra automaticamente uma fração disponível.
        
        Args:
            fracao_index: Se fornecido, tenta ocupar fração específica. Se None, encontra automaticamente.
        """
        if fracao_index is None:
            fracao_index = self.encontrar_fracao_para_ocupacao(quantidade, temperatura, inicio, fim)
            if fracao_index is None:
                logger.warning(f"❌ Nenhuma fração disponível na {self.nome} entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}")
                return False

        return self.adicionar_ocupacao_fracao(
            fracao_index, id_ordem, id_pedido, id_atividade, id_item,
            quantidade, temperatura, setup_minutos, inicio, fim
        )

    # ==========================================================
    # 🔓 Liberação - ATUALIZADO com acesso por índices
    # ==========================================================
    def liberar_por_atividade(self, id_ordem: int, id_pedido: int, id_atividade: int):
        """Libera ocupações específicas por atividade."""
        total_liberadas = 0
        
        for fracao_index in range(self.numero_fracoes):
            antes = len(self.ocupacoes_por_fracao[fracao_index])
            self.ocupacoes_por_fracao[fracao_index] = [
                ocupacao for ocupacao in self.ocupacoes_por_fracao[fracao_index]
                if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido and ocupacao[2] == id_atividade)
                # Acesso por índices: id_ordem=[0], id_pedido=[1], id_atividade=[2]
            ]
            liberadas_fracao = antes - len(self.ocupacoes_por_fracao[fracao_index])
            total_liberadas += liberadas_fracao

        if total_liberadas > 0:
            logger.info(
                f"🔓 Liberadas {total_liberadas} ocupações da {self.nome} "
                f"para Atividade {id_atividade}, Pedido {id_pedido}, Ordem {id_ordem}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar na {self.nome} "
                f"para Atividade {id_atividade}, Pedido {id_pedido}, Ordem {id_ordem}."
            )

    def liberar_por_pedido(self, id_ordem: int, id_pedido: int):
        """Libera ocupações específicas por pedido."""
        total_liberadas = 0
        
        for fracao_index in range(self.numero_fracoes):
            antes = len(self.ocupacoes_por_fracao[fracao_index])
            self.ocupacoes_por_fracao[fracao_index] = [
                ocupacao for ocupacao in self.ocupacoes_por_fracao[fracao_index]
                if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido)
                # Acesso por índices: id_ordem=[0], id_pedido=[1]
            ]
            liberadas_fracao = antes - len(self.ocupacoes_por_fracao[fracao_index])
            total_liberadas += liberadas_fracao

        if total_liberadas > 0:
            logger.info(
                f"🔓 Liberadas {total_liberadas} ocupações da {self.nome} "
                f"para Pedido {id_pedido}, Ordem {id_ordem}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar na {self.nome} "
                f"para Pedido {id_pedido}, Ordem {id_ordem}."
            )

    def liberar_por_ordem(self, id_ordem: int):
        """Libera ocupações específicas por ordem."""
        total_liberadas = 0
        
        for fracao_index in range(self.numero_fracoes):
            antes = len(self.ocupacoes_por_fracao[fracao_index])
            self.ocupacoes_por_fracao[fracao_index] = [
                ocupacao for ocupacao in self.ocupacoes_por_fracao[fracao_index]
                if not (ocupacao[0] == id_ordem)
                # Acesso por índices: id_ordem=[0]
            ]
            liberadas_fracao = antes - len(self.ocupacoes_por_fracao[fracao_index])
            total_liberadas += liberadas_fracao

        if total_liberadas > 0:
            logger.info(
                f"🔓 Liberadas {total_liberadas} ocupações da {self.nome} "
                f"para Ordem {id_ordem}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar na {self.nome} "
                f"para Ordem {id_ordem}."
            )

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        """Libera ocupações que já finalizaram."""
        total_liberadas = 0
        
        for fracao_index in range(self.numero_fracoes):
            antes = len(self.ocupacoes_por_fracao[fracao_index])
            self.ocupacoes_por_fracao[fracao_index] = [
                ocupacao for ocupacao in self.ocupacoes_por_fracao[fracao_index]
                if not (ocupacao[8] <= horario_atual)  # fim=[8]
            ]
            liberadas_fracao = antes - len(self.ocupacoes_por_fracao[fracao_index])
            total_liberadas += liberadas_fracao

        if total_liberadas > 0:
            logger.info(
                f"🔓 Liberadas {total_liberadas} ocupações da {self.nome} finalizadas até {horario_atual.strftime('%H:%M')}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação finalizada encontrada para liberar na {self.nome} até {horario_atual.strftime('%H:%M')}."
            )
        return total_liberadas

    def liberar_todas_ocupacoes(self):
        """Limpa todas as ocupações de todas as frações."""
        total = sum(len(ocupacoes) for ocupacoes in self.ocupacoes_por_fracao)
        for fracao_ocupacoes in self.ocupacoes_por_fracao:
            fracao_ocupacoes.clear()
        logger.info(f"🔓 Todas as {total} ocupações da {self.nome} foram removidas.")

    def liberar_por_intervalo(self, inicio: datetime, fim: datetime):
        """Libera ocupações que se sobrepõem ao intervalo especificado."""
        total_liberadas = 0
        
        for fracao_index in range(self.numero_fracoes):
            antes = len(self.ocupacoes_por_fracao[fracao_index])
            self.ocupacoes_por_fracao[fracao_index] = [
                ocupacao for ocupacao in self.ocupacoes_por_fracao[fracao_index]
                if not (ocupacao[7] < fim and ocupacao[8] > inicio)  # inicio=[7], fim=[8] - remove qualquer sobreposição
            ]
            liberadas_fracao = antes - len(self.ocupacoes_por_fracao[fracao_index])
            total_liberadas += liberadas_fracao

        if total_liberadas > 0:
            logger.info(
                f"🔓 Liberadas {total_liberadas} ocupações da {self.nome} entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar na {self.nome} entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
            )

    def liberar_fracao_especifica(self, fracao_index: int, id_ordem: int, id_pedido: int, id_atividade: int):
        """Libera ocupação específica de uma fração."""
        if fracao_index < 0 or fracao_index >= self.numero_fracoes:
            logger.warning(f"❌ Índice de fração inválido: {fracao_index}")
            return

        antes = len(self.ocupacoes_por_fracao[fracao_index])
        self.ocupacoes_por_fracao[fracao_index] = [
            ocupacao for ocupacao in self.ocupacoes_por_fracao[fracao_index]
            if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido and ocupacao[2] == id_atividade)
            # Acesso por índices: id_ordem=[0], id_pedido=[1], id_atividade=[2]
        ]
        liberadas = antes - len(self.ocupacoes_por_fracao[fracao_index])
        
        if liberadas > 0:
            logger.info(
                f"🔓 Liberadas {liberadas} ocupações da fração {fracao_index + 1} da {self.nome} "
                f"para Atividade {id_atividade}, Pedido {id_pedido}, Ordem {id_ordem}."
            )

    # ==========================================================
    # 📅 Agenda e Relatórios - ATUALIZADO com acesso por índices
    # ==========================================================
    def mostrar_agenda(self):
        """Mostra agenda detalhada por fração."""
        logger.info("==============================================")
        logger.info(f"📅 Agenda da {self.nome}")
        logger.info(f"🔧 Capacidade: {self.capacidade_gramas_min}-{self.capacidade_gramas_max} | Frações: {self.numero_fracoes}")
        logger.info("==============================================")

        tem_ocupacao = False
        for fracao_index in range(self.numero_fracoes):
            if self.ocupacoes_por_fracao[fracao_index]:
                tem_ocupacao = True
                logger.info(f"🔹 Fração {fracao_index + 1}:")
                for ocupacao in self.ocupacoes_por_fracao[fracao_index]:
                    # Acesso por índices para mostrar informações
                    id_o, id_p, id_a, id_i = ocupacao[0], ocupacao[1], ocupacao[2], ocupacao[3]
                    qtd, temp, setup = ocupacao[4], ocupacao[5], ocupacao[6]
                    ini, fim = ocupacao[7], ocupacao[8]
                    
                    # Mostrar capacidade total no período
                    qtd_total = self.calcular_quantidade_maxima_periodo(ini, fim)
                    logger.info(
                        f"   🍟 Ordem {id_o} | Pedido {id_p} | Atividade {id_a} | Item {id_i} | "
                        f"Qtd: {qtd} | Temp: {temp}°C | Setup: {setup}min | "
                        f"{ini.strftime('%H:%M')} → {fim.strftime('%H:%M')} | "
                        f"Total equipamento: {qtd_total}/{self.capacidade_gramas_max}"
                    )

        if not tem_ocupacao:
            logger.info("🔹 Nenhuma ocupação registrada em nenhuma fração.")

    def obter_estatisticas_uso(self, inicio: datetime, fim: datetime) -> dict:
        """Retorna estatísticas de uso da fritadeira no período."""
        total_ocupacoes = 0
        total_quantidade = 0
        fracoes_utilizadas = 0
        temperaturas_utilizadas = set()
        setups_utilizados = set()
        
        for fracao_index in range(self.numero_fracoes):
            ocupacoes_fracao = []
            for ocupacao in self.ocupacoes_por_fracao[fracao_index]:
                # Acesso por índices: quantidade=[4], temperatura=[5], setup=[6], inicio=[7], fim=[8]
                qtd, temp, setup, ini, f = ocupacao[4], ocupacao[5], ocupacao[6], ocupacao[7], ocupacao[8]
                
                if not (fim <= ini or inicio >= f):  # há sobreposição temporal
                    ocupacoes_fracao.append(ocupacao)
            
            if ocupacoes_fracao:
                fracoes_utilizadas += 1
                total_ocupacoes += len(ocupacoes_fracao)
                for ocupacao in ocupacoes_fracao:
                    qtd, temp, setup = ocupacao[4], ocupacao[5], ocupacao[6]
                    total_quantidade += qtd
                    temperaturas_utilizadas.add(temp)
                    setups_utilizados.add(setup)
        
        taxa_utilizacao_fracoes = (fracoes_utilizadas / self.numero_fracoes * 100) if self.numero_fracoes > 0 else 0.0
        quantidade_maxima_periodo = self.calcular_quantidade_maxima_periodo(inicio, fim)
        taxa_utilizacao_capacidade = (quantidade_maxima_periodo / self.capacidade_gramas_max * 100) if self.capacidade_gramas_max > 0 else 0.0
        
        return {
            'fracoes_utilizadas': fracoes_utilizadas,
            'fracoes_total': self.numero_fracoes,
            'taxa_utilizacao_fracoes': taxa_utilizacao_fracoes,
            'total_ocupacoes': total_ocupacoes,
            'quantidade_total': total_quantidade,
            'quantidade_maxima_simultanea': quantidade_maxima_periodo,
            'capacidade_gramas_maxima': self.capacidade_gramas_max,
            'taxa_utilizacao_capacidade': taxa_utilizacao_capacidade,
            'quantidade_media_por_ocupacao': total_quantidade / total_ocupacoes if total_ocupacoes > 0 else 0.0,
            'temperaturas_utilizadas': list(temperaturas_utilizadas),
            'setups_utilizados': list(setups_utilizados)
        }

    # ==========================================================
    # 🆕 MÉTODOS ADICIONAIS PARA VERIFICAÇÃO DINÂMICA
    # ==========================================================
    def obter_ocupacoes_item_periodo(self, id_item: int, inicio: datetime, fim: datetime) -> List[Tuple[int, int, int, int, int, int, int, datetime, datetime, int]]:
        """Retorna ocupações de um item específico que se sobrepõem ao período, incluindo índice da fração."""
        ocupacoes_item = []
        for fracao_index in range(self.numero_fracoes):
            for ocupacao in self.ocupacoes_por_fracao[fracao_index]:
                # Acesso por índices: id_item=[3], inicio=[7], fim=[8]
                if (ocupacao[3] == id_item and 
                    not (fim <= ocupacao[7] or inicio >= ocupacao[8])):  # há sobreposição temporal
                    ocupacoes_item.append((*ocupacao, fracao_index))
        return ocupacoes_item

    def obter_ocupacoes_pedido_periodo(self, id_pedido: int, inicio: datetime, fim: datetime) -> List[Tuple[int, int, int, int, int, int, int, datetime, datetime, int]]:
        """Retorna ocupações de um pedido específico que se sobrepõem ao período, incluindo índice da fração."""
        ocupacoes_pedido = []
        for fracao_index in range(self.numero_fracoes):
            for ocupacao in self.ocupacoes_por_fracao[fracao_index]:
                # Acesso por índices: id_pedido=[1], inicio=[7], fim=[8]
                if (ocupacao[1] == id_pedido and 
                    not (fim <= ocupacao[7] or inicio >= ocupacao[8])):  # há sobreposição temporal
                    ocupacoes_pedido.append((*ocupacao, fracao_index))
        return ocupacoes_pedido

    def calcular_utilizacao_por_temperatura(self, inicio: datetime, fim: datetime) -> Dict[int, dict]:
        """Calcula estatísticas de utilização por faixa de temperatura."""
        utilizacao_por_temp = {}
        
        for fracao_index in range(self.numero_fracoes):
            for ocupacao in self.ocupacoes_por_fracao[fracao_index]:
                # Acesso por índices: quantidade=[4], temperatura=[5], inicio=[7], fim=[8]
                qtd, temp, ini, f = ocupacao[4], ocupacao[5], ocupacao[7], ocupacao[8]
                
                if not (fim <= ini or inicio >= f):  # há sobreposição temporal
                    if temp not in utilizacao_por_temp:
                        utilizacao_por_temp[temp] = {
                            'quantidade_total': 0,
                            'tempo_total_minutos': 0,
                            'numero_ocupacoes': 0,
                            'fracoes_utilizadas': set()
                        }
                    
                    utilizacao_por_temp[temp]['quantidade_total'] += qtd
                    utilizacao_por_temp[temp]['numero_ocupacoes'] += 1
                    utilizacao_por_temp[temp]['fracoes_utilizadas'].add(fracao_index)
                    
                    # Calcula tempo de sobreposição
                    inicio_efetivo = max(inicio, ini)
                    fim_efetivo = min(fim, f)
                    tempo_ocupacao = (fim_efetivo - inicio_efetivo).total_seconds() / 60
                    utilizacao_por_temp[temp]['tempo_total_minutos'] += tempo_ocupacao
        
        # Converte sets para listas
        for temp_stats in utilizacao_por_temp.values():
            temp_stats['fracoes_utilizadas'] = list(temp_stats['fracoes_utilizadas'])
            temp_stats['numero_fracoes_utilizadas'] = len(temp_stats['fracoes_utilizadas'])
        
        return utilizacao_por_temp

    def validar_consistencia_ocupacoes(self) -> List[str]:
        """Valida a consistência de todas as ocupações da fritadeira."""
        inconsistencias = []
        
        for fracao_index in range(self.numero_fracoes):
            ocupacoes_fracao = self.ocupacoes_por_fracao[fracao_index]
            
            # Verifica sobreposições temporais na mesma fração
            for i, ocupacao1 in enumerate(ocupacoes_fracao):
                for j, ocupacao2 in enumerate(ocupacoes_fracao[i+1:], i+1):
                    # Acesso por índices: inicio=[7], fim=[8]
                    ini1, fim1 = ocupacao1[7], ocupacao1[8]
                    ini2, fim2 = ocupacao2[7], ocupacao2[8]
                    
                    if not (fim1 <= ini2 or ini1 >= fim2):  # há sobreposição
                        inconsistencias.append(
                            f"Fração {fracao_index + 1}: Sobreposição temporal entre "
                            f"ocupações {i+1} ({ini1}-{fim1}) e {j+1} ({ini2}-{fim2})"
                        )
            
            # Verifica limites de capacidade para cada ocupação
            for i, ocupacao in enumerate(ocupacoes_fracao):
                # Acesso por índices: quantidade=[4], temperatura=[5], inicio=[7], fim=[8]
                qtd, temp, ini, fim_ocup = ocupacao[4], ocupacao[5], ocupacao[7], ocupacao[8]
                
                if not self.validar_quantidade_individual(qtd):
                    inconsistencias.append(
                        f"Fração {fracao_index + 1}, ocupação {i+1}: "
                        f"Quantidade {qtd} inválida"
                    )
                
                if not self.validar_temperatura(temp):
                    inconsistencias.append(
                        f"Fração {fracao_index + 1}, ocupação {i+1}: "
                        f"Temperatura {temp}°C fora dos limites"
                    )
                
                # Verifica se período é válido
                if ini >= fim_ocup:
                    inconsistencias.append(
                        f"Fração {fracao_index + 1}, ocupação {i+1}: "
                        f"Período inválido {ini} >= {fim_ocup}"
                    )
        
        # Verifica capacidade total do equipamento
        todas_ocupacoes = self.obter_todas_ocupacoes()
        if todas_ocupacoes:
            # Encontra período total
            inicio_min = min(ocupacao[7] for ocupacao in todas_ocupacoes)  # inicio=[7]
            fim_max = max(ocupacao[8] for ocupacao in todas_ocupacoes)     # fim=[8]
            
            quantidade_maxima = self.calcular_quantidade_maxima_periodo(inicio_min, fim_max)
            if quantidade_maxima > self.capacidade_gramas_max:
                inconsistencias.append(
                    f"Capacidade total excedida: {quantidade_maxima} > {self.capacidade_gramas_max}"
                )
            
            # 🆕 Verifica conflitos de temperatura simultânea
            conflitos_temp = self._verificar_conflitos_temperatura_global()
            inconsistencias.extend(conflitos_temp)
        
        return inconsistencias

    def _verificar_conflitos_temperatura_global(self) -> List[str]:
        """Verifica conflitos de temperatura em todo o equipamento."""
        conflitos = []
        todas_ocupacoes = self.obter_todas_ocupacoes()
        
        for i, ocupacao1 in enumerate(todas_ocupacoes):
            for j, ocupacao2 in enumerate(todas_ocupacoes[i+1:], i+1):
                # Acesso por índices: temperatura=[5], inicio=[7], fim=[8], fracao=[9]
                temp1, ini1, fim1, fracao1 = ocupacao1[5], ocupacao1[7], ocupacao1[8], ocupacao1[9]
                temp2, ini2, fim2, fracao2 = ocupacao2[5], ocupacao2[7], ocupacao2[8], ocupacao2[9]
                
                # Verifica sobreposição temporal e diferença de temperatura
                if not (fim1 <= ini2 or ini1 >= fim2):  # há sobreposição temporal
                    if temp1 != temp2:
                        conflitos.append(
                            f"Conflito de temperatura: Fração {fracao1 + 1} ({temp1}°C) "
                            f"vs Fração {fracao2 + 1} ({temp2}°C) "
                            f"em período sobreposto ({max(ini1, ini2)}-{min(fim1, fim2)})"
                        )
        
        return conflitos