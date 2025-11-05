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
    por caixas ou níveis de tela individualizados, considerando períodos de tempo e controle de temperatura.
    ✔️ Permite múltiplas alocações simultâneas, com registro de tempo e temperatura.
    ✔️ Controle de temperatura com faixa mínima e máxima por intervalo de tempo.
    ✔️ Ocupação individualizada por caixas e níveis de tela numerados.
    ✔️ Gestor controla ocupação via leitura da atividade.
    """

    # ============================================
    # 🔧 Inicialização
    # ============================================
    def __init__(
        self,
        id: int,
        nome: str,
        setor: TipoSetor,
        capacidade_caixa_min: int,
        capacidade_caixa_max: int,
        capacidade_niveis_min: int,
        capacidade_niveis_max: int,
        nivel_tela: int,
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

        # Capacidades dos recipientes
        self.capacidade_caixa_min = capacidade_caixa_min
        self.capacidade_caixa_max = capacidade_caixa_max
        self.capacidade_niveis_min = capacidade_niveis_min
        self.capacidade_niveis_max = capacidade_niveis_max
        self.nivel_tela = nivel_tela
        self.faixa_temperatura_min = faixa_temperatura_min
        self.faixa_temperatura_max = faixa_temperatura_max

        # Cálculo dinâmico das quantidades
        self.qtd_niveis_base = self.capacidade_niveis_max - self.capacidade_niveis_min + 1
        self.qtd_niveis_total = self.qtd_niveis_base * self.nivel_tela
        self.qtd_caixas = self.capacidade_caixa_max - self.capacidade_caixa_min + 1

        # 📦 Ocupações individualizadas por nível: (id_ordem, id_pedido, id_atividade, id_item, quantidade_alocada, inicio, fim)
        self.niveis_ocupacoes: List[List[Tuple[int, int, int, int, float, datetime, datetime]]] = [[] for _ in range(self.qtd_niveis_total)]
        
        # 📦 Ocupações individualizadas por caixa: (id_ordem, id_pedido, id_atividade, id_item, quantidade_alocada, inicio, fim)
        self.caixas_ocupacoes: List[List[Tuple[int, int, int, int, float, datetime, datetime]]] = [[] for _ in range(self.qtd_caixas)]

        # 🌡️ Controle de temperatura por intervalo: (temperatura, inicio, fim)
        self.intervalos_temperatura: List[Tuple[int, datetime, datetime]] = []

    # ============================================
    # 🔍 Propriedades de Capacidade
    # ============================================
    @property
    def total_niveis_disponiveis(self) -> int:
        """Retorna o total de níveis de tela disponíveis (incluindo multiplicação por nivel_tela)."""
        return self.qtd_niveis_total

    @property
    def total_caixas_disponiveis(self) -> int:
        """Retorna o total de caixas disponíveis."""
        return self.qtd_caixas

    def obter_primeiro_nivel(self) -> int:
        """Retorna o número do primeiro nível físico."""
        return self.capacidade_niveis_min

    def obter_ultimo_nivel(self) -> int:
        """Retorna o número do último nível físico."""
        return self.capacidade_niveis_max

    def obter_primeira_caixa(self) -> int:
        """Retorna o número da primeira caixa."""
        return self.capacidade_caixa_min

    def obter_ultima_caixa(self) -> int:
        """Retorna o número da última caixa."""
        return self.capacidade_caixa_max

    def obter_range_niveis_fisicos(self) -> tuple:
        """Retorna o range de numeração dos níveis físicos (primeiro, último)."""
        return (self.capacidade_niveis_min, self.capacidade_niveis_max)

    def obter_range_caixas(self) -> tuple:
        """Retorna o range de numeração das caixas (primeira, última)."""
        return (self.capacidade_caixa_min, self.capacidade_caixa_max)

    def obter_numeros_niveis_fisicos_disponiveis(self) -> List[int]:
        """Retorna lista com todos os números dos níveis físicos disponíveis."""
        return list(range(self.capacidade_niveis_min, self.capacidade_niveis_max + 1))

    def obter_numeros_caixas_disponiveis(self) -> List[int]:
        """Retorna lista com todos os números das caixas disponíveis."""
        return list(range(self.capacidade_caixa_min, self.capacidade_caixa_max + 1))

    def obter_numeros_niveis_tela_disponiveis(self) -> List[Tuple[int, int]]:
        """Retorna lista com todos os números dos níveis de tela disponíveis (nivel_fisico, tela)."""
        niveis_tela = []
        for nivel_fisico in range(self.capacidade_niveis_min, self.capacidade_niveis_max + 1):
            for tela in range(1, self.nivel_tela + 1):
                niveis_tela.append((nivel_fisico, tela))
        return niveis_tela

    # ============================================
    # 🔧 Métodos de Conversão de Índices para Níveis de Tela
    # ============================================
    def obter_nivel_tela_por_indice(self, nivel_index: int) -> Tuple[int, int]:
        """
        Retorna o nível físico e tela baseado no índice.
        
        Args:
            nivel_index (int): Índice interno (0-based)
            
        Returns:
            Tuple[int, int]: (nivel_fisico, tela) ou (-1, -1) se inválido
        """
        if nivel_index < 0 or nivel_index >= self.qtd_niveis_total:
            return (-1, -1)
        
        # Calcular nível físico e tela
        nivel_fisico = self.capacidade_niveis_min + (nivel_index // self.nivel_tela)
        tela = (nivel_index % self.nivel_tela) + 1
        
        return (nivel_fisico, tela)

    def obter_indice_por_nivel_tela(self, numero_nivel_fisico: int, numero_tela: int) -> int:
        """
        Retorna o índice interno baseado no nível físico e número da tela.
        
        Args:
            numero_nivel_fisico (int): Número do nível físico
            numero_tela (int): Número da tela (1-based)
            
        Returns:
            int: Índice interno ou -1 se inválido
        """
        if (numero_nivel_fisico < self.capacidade_niveis_min or 
            numero_nivel_fisico > self.capacidade_niveis_max or
            numero_tela < 1 or numero_tela > self.nivel_tela):
            return -1
        
        # Calcular índice
        indice = (numero_nivel_fisico - self.capacidade_niveis_min) * self.nivel_tela + (numero_tela - 1)
        return indice

    def obter_caixa_fisica_por_indice(self, caixa_index: int) -> int:
        """Retorna o número da caixa física baseado no índice (0-based para 1-based)."""
        if caixa_index < 0 or caixa_index >= self.qtd_caixas:
            return -1
        return self.capacidade_caixa_min + caixa_index

    def obter_indice_por_caixa_fisica(self, numero_caixa: int) -> int:
        """Retorna o índice interno baseado no número da caixa física."""
        if numero_caixa < self.capacidade_caixa_min or numero_caixa > self.capacidade_caixa_max:
            return -1
        return numero_caixa - self.capacidade_caixa_min

    # ============================================
    # 🌡️ Controle de Temperatura
    # ============================================
    def obter_temperatura_periodo(self, inicio: datetime, fim: datetime) -> Optional[int]:
        """Retorna a temperatura configurada para o período (se houver)."""
        for intervalo in self.intervalos_temperatura:
            if not (fim <= intervalo[1] or inicio >= intervalo[2]):  # há sobreposição
                return intervalo[0]  # temperatura
        return None

    def verificar_compatibilidade_temperatura(self, temperatura_desejada: int, inicio: datetime, fim: datetime) -> bool:
        """Verifica se a temperatura desejada é compatível com o período."""
        temperatura_atual = self.obter_temperatura_periodo(inicio, fim)
        
        if temperatura_atual is None:
            return True  # Sem conflito
        
        if temperatura_atual != temperatura_desejada:
            logger.warning(
                f"❌ Temperatura incompatível na {self.nome} entre {inicio.strftime('%Y-%m-%d %H:%M')} e {fim.strftime('%Y-%m-%d %H:%M')}. "
                f"Desejada: {temperatura_desejada}°C | Configurada: {temperatura_atual}°C"
            )
            return False
        
        return True

    def configurar_temperatura(self, temperatura: int, inicio: datetime, fim: datetime) -> bool:
        """Configura temperatura para um intervalo de tempo."""
        if temperatura < self.faixa_temperatura_min or temperatura > self.faixa_temperatura_max:
            logger.warning(
                f"❌ Temperatura {temperatura}°C fora da faixa permitida "
                f"({self.faixa_temperatura_min}°C a {self.faixa_temperatura_max}°C) na {self.nome}"
            )
            return False

        # Verificar se há conflito com temperaturas já configuradas
        if not self.verificar_compatibilidade_temperatura(temperatura, inicio, fim):
            return False

        # Verificar se há ocupações no período que impeçam mudança de temperatura
        if self.tem_ocupacao_periodo(inicio, fim):
            temperatura_atual = self.obter_temperatura_periodo(inicio, fim)
            if temperatura_atual is not None and temperatura_atual != temperatura:
                logger.warning(
                    f"❌ Não é possível alterar temperatura na {self.nome} entre {inicio.strftime('%Y-%m-%d %H:%M')} e {fim.strftime('%Y-%m-%d %H:%M')}. "
                    f"Há ocupações no período com temperatura {temperatura_atual}°C."
                )
                return False

        self.intervalos_temperatura.append((temperatura, inicio, fim))
        logger.info(
            f"🌡️ Temperatura configurada na {self.nome}: {temperatura}°C "
            f"para {inicio.strftime('%Y-%m-%d %H:%M')} → {fim.strftime('%Y-%m-%d %H:%M')}"
        )
        return True

    def tem_ocupacao_periodo(self, inicio: datetime, fim: datetime) -> bool:
        """Verifica se há ocupação em qualquer nível ou caixa durante um período."""
        return (self.tem_ocupacao_niveis_periodo(inicio, fim) or 
                self.tem_ocupacao_caixas_periodo(inicio, fim))

    def tem_ocupacao_niveis_periodo(self, inicio: datetime, fim: datetime, niveis_tela: List[Tuple[int, int]] = None) -> bool:
        """
        Verifica se há ocupação em níveis de tela durante um período específico.
        
        Args:
            inicio (datetime): Data de início do período
            fim (datetime): Data de fim do período
            niveis_tela (List[Tuple[int, int]], optional): Lista de tuplas (nivel_fisico, tela) para verificar.
                                                         Se None, verifica todos os níveis de tela disponíveis.
        
        Returns:
            bool: True se há ocupação em pelo menos um nível de tela no período, False caso contrário
        """
        # Define os níveis de tela a serem verificados
        if niveis_tela is None:
            niveis_tela = self.obter_numeros_niveis_tela_disponiveis()
        
        # Verifica ocupação por nível de tela
        for nivel_fisico, tela in niveis_tela:
            nivel_index = self.obter_indice_por_nivel_tela(nivel_fisico, tela)
            if nivel_index == -1:
                continue
                
            # Verifica se há alguma ocupação no nível de tela durante o período
            for ocupacao in self.niveis_ocupacoes[nivel_index]:
                if not (fim <= ocupacao[5] or inicio >= ocupacao[6]):  # há sobreposição
                    return True
        
        return False

    def tem_ocupacao_caixas_periodo(self, inicio: datetime, fim: datetime, caixas: List[int] = None) -> bool:
        """
        Verifica se há ocupação em caixas durante um período específico.
        
        Args:
            inicio (datetime): Data de início do período
            fim (datetime): Data de fim do período
            caixas (List[int], optional): Lista de números de caixas físicas para verificar.
                                        Se None, verifica todas as caixas disponíveis.
        
        Returns:
            bool: True se há ocupação em pelo menos uma caixa no período, False caso contrário
        """
        # Define as caixas a serem verificadas
        if caixas is None:
            caixas = list(range(self.capacidade_caixa_min, self.capacidade_caixa_max + 1))
        
        # Verifica ocupação por caixa
        for numero_caixa in caixas:
            caixa_index = self.obter_indice_por_caixa_fisica(numero_caixa)
            if caixa_index == -1:
                continue
                
            # Verifica se há alguma ocupação na caixa durante o período
            for ocupacao in self.caixas_ocupacoes[caixa_index]:
                if not (fim <= ocupacao[5] or inicio >= ocupacao[6]):  # há sobreposição
                    return True
        
        return False

    # ============================================
    # 🔍 Consulta de Ocupação - NÍVEIS DE TELA
    # ============================================
    def obter_ocupacao_nivel_tela(self, numero_nivel_fisico: int, numero_tela: int, inicio: datetime, fim: datetime) -> float:
        """Retorna a quantidade total ocupada em um nível de tela no período especificado."""
        nivel_index = self.obter_indice_por_nivel_tela(numero_nivel_fisico, numero_tela)
        if nivel_index == -1:
            return 0.0
        
        ocupada = 0.0
        for ocupacao in self.niveis_ocupacoes[nivel_index]:
            if not (fim <= ocupacao[5] or inicio >= ocupacao[6]):  # há sobreposição temporal
                ocupada += ocupacao[4]  # quantidade_alocada
        return ocupada

    def obter_ocupacao_todos_niveis_tela(self, inicio: datetime, fim: datetime) -> List[Tuple[int, int, float]]:
        """Retorna lista com a ocupação de todos os níveis de tela no período especificado."""
        ocupacoes = []
        for nivel_fisico, tela in self.obter_numeros_niveis_tela_disponiveis():
            ocupacao = self.obter_ocupacao_nivel_tela(nivel_fisico, tela, inicio, fim)
            ocupacoes.append((nivel_fisico, tela, ocupacao))
        return ocupacoes

    def nivel_tela_disponivel(self, numero_nivel_fisico: int, numero_tela: int, inicio: datetime, fim: datetime) -> bool:
        """Verifica se um nível de tela está completamente livre no período."""
        return self.obter_ocupacao_nivel_tela(numero_nivel_fisico, numero_tela, inicio, fim) == 0.0

    def niveis_tela_disponiveis_periodo(self, inicio: datetime, fim: datetime) -> List[Tuple[int, int]]:
        """Retorna lista de tuplas (nivel_fisico, tela) completamente livres no período."""
        niveis_livres = []
        for nivel_fisico, tela in self.obter_numeros_niveis_tela_disponiveis():
            if self.nivel_tela_disponivel(nivel_fisico, tela, inicio, fim):
                niveis_livres.append((nivel_fisico, tela))
        return niveis_livres

    def obter_ocupacoes_nivel_tela(self, numero_nivel_fisico: int, numero_tela: int) -> List[Tuple[int, int, int, int, float, datetime, datetime]]:
        """Retorna todas as ocupações de um nível de tela específico."""
        nivel_index = self.obter_indice_por_nivel_tela(numero_nivel_fisico, numero_tela)
        if nivel_index == -1:
            return []
        return self.niveis_ocupacoes[nivel_index].copy()

    # ============================================
    # 🔍 Consulta de Ocupação - CAIXAS
    # ============================================
    def obter_ocupacao_caixa(self, numero_caixa: int, inicio: datetime, fim: datetime) -> float:
        """Retorna a quantidade total ocupada em uma caixa no período especificado."""
        caixa_index = self.obter_indice_por_caixa_fisica(numero_caixa)
        if caixa_index == -1:
            return 0.0
        
        ocupada = 0.0
        for ocupacao in self.caixas_ocupacoes[caixa_index]:
            if not (fim <= ocupacao[5] or inicio >= ocupacao[6]):  # há sobreposição temporal
                ocupada += ocupacao[4]  # quantidade_alocada
        return ocupada

    def obter_ocupacao_todas_caixas(self, inicio: datetime, fim: datetime) -> List[float]:
        """Retorna lista com a ocupação de todas as caixas no período especificado."""
        ocupacoes = []
        for numero_caixa in range(self.capacidade_caixa_min, self.capacidade_caixa_max + 1):
            ocupacoes.append(self.obter_ocupacao_caixa(numero_caixa, inicio, fim))
        return ocupacoes

    def caixa_disponivel(self, numero_caixa: int, inicio: datetime, fim: datetime) -> bool:
        """Verifica se uma caixa está completamente livre no período."""
        return self.obter_ocupacao_caixa(numero_caixa, inicio, fim) == 0.0

    def caixas_disponiveis_periodo(self, inicio: datetime, fim: datetime) -> List[int]:
        """Retorna lista de números das caixas físicas completamente livres no período."""
        caixas_livres = []
        for numero_caixa in range(self.capacidade_caixa_min, self.capacidade_caixa_max + 1):
            if self.caixa_disponivel(numero_caixa, inicio, fim):
                caixas_livres.append(numero_caixa)
        return caixas_livres

    def obter_ocupacoes_caixa(self, numero_caixa: int) -> List[Tuple[int, int, int, int, float, datetime, datetime]]:
        """Retorna todas as ocupações de uma caixa específica."""
        caixa_index = self.obter_indice_por_caixa_fisica(numero_caixa)
        if caixa_index == -1:
            return []
        return self.caixas_ocupacoes[caixa_index].copy()

    # ============================================
    # 🔄 Ocupação e Atualização - NÍVEIS DE TELA
    # ============================================
    def adicionar_ocupacao_nivel_tela(
        self,
        numero_nivel_fisico: int,
        numero_tela: int,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade: float,
        inicio: datetime,
        fim: datetime,
        temperatura: Optional[int] = None
    ) -> bool:
        """Adiciona uma ocupação específica a um nível de tela específico."""
        nivel_index = self.obter_indice_por_nivel_tela(numero_nivel_fisico, numero_tela)
        if nivel_index == -1:
            logger.warning(
                f"❌ Nível de tela inválido: Nível {numero_nivel_fisico}, Tela {numero_tela}. "
                f"Faixa válida: Níveis {self.capacidade_niveis_min}-{self.capacidade_niveis_max}, Telas 1-{self.nivel_tela}"
            )
            return False

        # Verificar temperatura se fornecida
        if temperatura is not None:
            if not self.verificar_compatibilidade_temperatura(temperatura, inicio, fim):
                return False
            # Configurar temperatura se não existir para o período
            temp_atual = self.obter_temperatura_periodo(inicio, fim)
            if temp_atual is None:
                if not self.configurar_temperatura(temperatura, inicio, fim):
                    return False

        self.niveis_ocupacoes[nivel_index].append(
            (id_ordem, id_pedido, id_atividade, id_item, quantidade, inicio, fim)
        )

        logger.info(
            f"📥 Ocupação nível de tela adicionada na {self.nome} - Nível {numero_nivel_fisico}, Tela {numero_tela} | "
            f"Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade} | Item {id_item} | "
            f"{quantidade:.2f} unidades | {inicio.strftime('%Y-%m-%d %H:%M')} → {fim.strftime('%Y-%m-%d %H:%M')}"
        )
        return True

    def sobrescrever_ocupacao_nivel_tela(
        self,
        numero_nivel_fisico: int,
        numero_tela: int,
        ocupacoes: List[Tuple[int, int, int, int, float, datetime, datetime]]
    ) -> bool:
        """Sobrescreve completamente as ocupações de um nível de tela específico."""
        nivel_index = self.obter_indice_por_nivel_tela(numero_nivel_fisico, numero_tela)
        if nivel_index == -1:
            logger.warning(f"❌ Nível de tela inválido: Nível {numero_nivel_fisico}, Tela {numero_tela}")
            return False

        self.niveis_ocupacoes[nivel_index] = ocupacoes.copy()
        
        logger.info(
            f"🔄 Ocupações do nível {numero_nivel_fisico}, tela {numero_tela} da {self.nome} foram sobrescritas. "
            f"Total de ocupações: {len(ocupacoes)}"
        )
        return True

    # ============================================
    # 🔄 Ocupação e Atualização - CAIXAS
    # ============================================
    def adicionar_ocupacao_caixa(
        self,
        numero_caixa: int,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        quantidade: float,
        inicio: datetime,
        fim: datetime,
        temperatura: Optional[int] = None
    ) -> bool:
        """Adiciona uma ocupação específica a uma caixa específica."""
        caixa_index = self.obter_indice_por_caixa_fisica(numero_caixa)
        if caixa_index == -1:
            logger.warning(f"❌ Número de caixa inválido: {numero_caixa}. Faixa válida: {self.capacidade_caixa_min}-{self.capacidade_caixa_max}")
            return False

        # Verificar temperatura se fornecida
        if temperatura is not None:
            if not self.verificar_compatibilidade_temperatura(temperatura, inicio, fim):
                return False
            # Configurar temperatura se não existir para o período
            temp_atual = self.obter_temperatura_periodo(inicio, fim)
            if temp_atual is None:
                if not self.configurar_temperatura(temperatura, inicio, fim):
                    return False

        self.caixas_ocupacoes[caixa_index].append(
            (id_ordem, id_pedido, id_atividade, id_item, quantidade, inicio, fim)
        )

        logger.info(
            f"📦 Ocupação caixa adicionada na {self.nome} - Caixa {numero_caixa} | "
            f"Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade} | Item {id_item} | "
            f"{quantidade:.2f} unidades | {inicio.strftime('%Y-%m-%d %H:%M')} → {fim.strftime('%Y-%m-%d %H:%M')}"
        )
        return True

    def sobrescrever_ocupacao_caixa(
        self,
        numero_caixa: int,
        ocupacoes: List[Tuple[int, int, int, int, float, datetime, datetime]]
    ) -> bool:
        """Sobrescreve completamente as ocupações de uma caixa específica."""
        caixa_index = self.obter_indice_por_caixa_fisica(numero_caixa)
        if caixa_index == -1:
            logger.warning(f"❌ Número de caixa inválido: {numero_caixa}")
            return False

        self.caixas_ocupacoes[caixa_index] = ocupacoes.copy()
        
        logger.info(
            f"🔄 Ocupações da caixa {numero_caixa} da {self.nome} foram sobrescritas. "
            f"Total de ocupações: {len(ocupacoes)}"
        )
        return True

    # ============================================
    # 🔓 Liberação
    # ============================================
    def liberar_por_atividade(self, id_ordem: int, id_pedido: int, id_atividade: int):
        """Libera ocupações específicas por atividade (níveis de tela e caixas)."""
        total_liberadas = 0
        
        # Liberar níveis de tela
        for nivel_index in range(self.qtd_niveis_total):
            antes = len(self.niveis_ocupacoes[nivel_index])
            self.niveis_ocupacoes[nivel_index] = [
                ocupacao for ocupacao in self.niveis_ocupacoes[nivel_index]
                if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido and ocupacao[2] == id_atividade)
            ]
            total_liberadas += antes - len(self.niveis_ocupacoes[nivel_index])

        # Liberar caixas
        for caixa_index in range(self.qtd_caixas):
            antes = len(self.caixas_ocupacoes[caixa_index])
            self.caixas_ocupacoes[caixa_index] = [
                ocupacao for ocupacao in self.caixas_ocupacoes[caixa_index]
                if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido and ocupacao[2] == id_atividade)
            ]
            total_liberadas += antes - len(self.caixas_ocupacoes[caixa_index])

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
        """Libera ocupações específicas por pedido (níveis de tela e caixas)."""
        total_liberadas = 0
        
        # Liberar níveis de tela
        for nivel_index in range(self.qtd_niveis_total):
            antes = len(self.niveis_ocupacoes[nivel_index])
            self.niveis_ocupacoes[nivel_index] = [
                ocupacao for ocupacao in self.niveis_ocupacoes[nivel_index]
                if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido)
            ]
            total_liberadas += antes - len(self.niveis_ocupacoes[nivel_index])

        # Liberar caixas
        for caixa_index in range(self.qtd_caixas):
            antes = len(self.caixas_ocupacoes[caixa_index])
            self.caixas_ocupacoes[caixa_index] = [
                ocupacao for ocupacao in self.caixas_ocupacoes[caixa_index]
                if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido)
            ]
            total_liberadas += antes - len(self.caixas_ocupacoes[caixa_index])

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
        """Libera ocupações específicas por ordem (níveis de tela e caixas)."""
        total_liberadas = 0
        
        # Liberar níveis de tela
        for nivel_index in range(self.qtd_niveis_total):
            antes = len(self.niveis_ocupacoes[nivel_index])
            self.niveis_ocupacoes[nivel_index] = [
                ocupacao for ocupacao in self.niveis_ocupacoes[nivel_index]
                if ocupacao[0] != id_ordem
            ]
            total_liberadas += antes - len(self.niveis_ocupacoes[nivel_index])

        # Liberar caixas
        for caixa_index in range(self.qtd_caixas):
            antes = len(self.caixas_ocupacoes[caixa_index])
            self.caixas_ocupacoes[caixa_index] = [
                ocupacao for ocupacao in self.caixas_ocupacoes[caixa_index]
                if ocupacao[0] != id_ordem
            ]
            total_liberadas += antes - len(self.caixas_ocupacoes[caixa_index])

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
        """Libera ocupações que já finalizaram (níveis de tela e caixas)."""
        total_liberadas = 0
        
        # Liberar níveis de tela
        for nivel_index in range(self.qtd_niveis_total):
            antes = len(self.niveis_ocupacoes[nivel_index])
            self.niveis_ocupacoes[nivel_index] = [
                ocupacao for ocupacao in self.niveis_ocupacoes[nivel_index]
                if ocupacao[6] > horario_atual  # fim > horario_atual
            ]
            total_liberadas += antes - len(self.niveis_ocupacoes[nivel_index])

        # Liberar caixas
        for caixa_index in range(self.qtd_caixas):
            antes = len(self.caixas_ocupacoes[caixa_index])
            self.caixas_ocupacoes[caixa_index] = [
                ocupacao for ocupacao in self.caixas_ocupacoes[caixa_index]
                if ocupacao[6] > horario_atual  # fim > horario_atual
            ]
            total_liberadas += antes - len(self.caixas_ocupacoes[caixa_index])

        # Liberar intervalos de temperatura finalizados
        antes_temp = len(self.intervalos_temperatura)
        self.intervalos_temperatura = [
            intervalo for intervalo in self.intervalos_temperatura
            if intervalo[2] > horario_atual  # fim > horario_atual
        ]
        liberadas_temp = antes_temp - len(self.intervalos_temperatura)

        if total_liberadas > 0 or liberadas_temp > 0:
            logger.info(
                f"🔓 Liberadas {total_liberadas} ocupações e {liberadas_temp} configurações de temperatura "
                f"da {self.nome} finalizadas até {horario_atual.strftime('%Y-%m-%d %H:%M')}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação finalizada encontrada para liberar na {self.nome} até {horario_atual.strftime('%Y-%m-%d %H:%M')}."
            )
        return total_liberadas

    def liberar_todas_ocupacoes(self):
        """Limpa todas as ocupações de todos os níveis de tela, caixas e temperaturas."""
        total_niveis = sum(len(ocupacoes) for ocupacoes in self.niveis_ocupacoes)
        total_caixas = sum(len(ocupacoes) for ocupacoes in self.caixas_ocupacoes)
        total_temp = len(self.intervalos_temperatura)
        
        for nivel_ocupacoes in self.niveis_ocupacoes:
            nivel_ocupacoes.clear()
        for caixa_ocupacoes in self.caixas_ocupacoes:
            caixa_ocupacoes.clear()
        self.intervalos_temperatura.clear()
        
        logger.info(
            f"🔓 Todas as ocupações da {self.nome} foram removidas. "
            f"Níveis de tela: {total_niveis} | Caixas: {total_caixas} | Temperaturas: {total_temp}"
        )

    def liberar_por_intervalo(self, inicio: datetime, fim: datetime):
        """Libera ocupações que se sobrepõem ao intervalo especificado."""
        total_liberadas = 0
        
        # Liberar níveis de tela
        for nivel_index in range(self.qtd_niveis_total):
            antes = len(self.niveis_ocupacoes[nivel_index])
            self.niveis_ocupacoes[nivel_index] = [
                ocupacao for ocupacao in self.niveis_ocupacoes[nivel_index]
                if not (ocupacao[5] < fim and ocupacao[6] > inicio)  # remove qualquer sobreposição
            ]
            total_liberadas += antes - len(self.niveis_ocupacoes[nivel_index])

        # Liberar caixas
        for caixa_index in range(self.qtd_caixas):
            antes = len(self.caixas_ocupacoes[caixa_index])
            self.caixas_ocupacoes[caixa_index] = [
                ocupacao for ocupacao in self.caixas_ocupacoes[caixa_index]
                if not (ocupacao[5] < fim and ocupacao[6] > inicio)  # remove qualquer sobreposição
            ]
            total_liberadas += antes - len(self.caixas_ocupacoes[caixa_index])

        # Liberar temperaturas no intervalo
        antes_temp = len(self.intervalos_temperatura)
        self.intervalos_temperatura = [
            intervalo for intervalo in self.intervalos_temperatura
            if not (intervalo[1] < fim and intervalo[2] > inicio)  # remove qualquer sobreposição
        ]
        liberadas_temp = antes_temp - len(self.intervalos_temperatura)

        if total_liberadas > 0 or liberadas_temp > 0:
            logger.info(
                f"🔓 Liberadas {total_liberadas} ocupações e {liberadas_temp} configurações de temperatura "
                f"da {self.nome} entre {inicio.strftime('%Y-%m-%d %H:%M')} e {fim.strftime('%Y-%m-%d %H:%M')}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar na {self.nome} "
                f"entre {inicio.strftime('%Y-%m-%d %H:%M')} e {fim.strftime('%Y-%m-%d %H:%M')}."
            )

    # ============================================
    # 📅 Agenda e Relatórios
    # ============================================
    def mostrar_agenda(self):
        """Mostra agenda detalhada por nível de tela, caixa e temperatura."""
        logger.info("==============================================")
        logger.info(f"📅 Agenda da {self.nome}")
        logger.info(f"📊 Numeração dos níveis físicos: {self.capacidade_niveis_min} a {self.capacidade_niveis_max}")
        logger.info(f"📊 Numeração das caixas: {self.capacidade_caixa_min} a {self.capacidade_caixa_max}")
        logger.info(f"📊 Telas por nível: {self.nivel_tela}")
        logger.info(f"📏 Dimensões: {self.qtd_niveis_total} níveis de tela totais | {self.qtd_caixas} caixas totais")
        logger.info(f"🌡️ Faixa de temperatura: {self.faixa_temperatura_min}°C a {self.faixa_temperatura_max}°C")
        logger.info("==============================================")

        tem_ocupacao = False
        
        # Mostrar ocupações de níveis de tela
        for nivel_index in range(self.qtd_niveis_total):
            if self.niveis_ocupacoes[nivel_index]:
                tem_ocupacao = True
                nivel_fisico, tela = self.obter_nivel_tela_por_indice(nivel_index)
                logger.info(f"🔹 Nível {nivel_fisico}, Tela {tela}:")
                for ocupacao in self.niveis_ocupacoes[nivel_index]:
                    temp = self.obter_temperatura_periodo(ocupacao[5], ocupacao[6])
                    temp_info = f"Temp: {temp}°C" if temp else "Temp: N/A"
                    logger.info(
                        f"   🗂️ Ordem {ocupacao[0]} | Pedido {ocupacao[1]} | Atividade {ocupacao[2]} | Item {ocupacao[3]} | "
                        f"{ocupacao[4]:.2f} unidades | {ocupacao[5].strftime('%Y-%m-%d %H:%M')} → {ocupacao[6].strftime('%Y-%m-%d %H:%M')} | {temp_info}"
                    )

        # Mostrar ocupações de caixas
        for caixa_index in range(self.qtd_caixas):
            if self.caixas_ocupacoes[caixa_index]:
                tem_ocupacao = True
                numero_caixa = self.obter_caixa_fisica_por_indice(caixa_index)
                logger.info(f"📦 Caixa {numero_caixa}:")
                for ocupacao in self.caixas_ocupacoes[caixa_index]:
                    temp = self.obter_temperatura_periodo(ocupacao[5], ocupacao[6])
                    temp_info = f"Temp: {temp}°C" if temp else "Temp: N/A"
                    logger.info(
                        f"   🗂️ Ordem {ocupacao[0]} | Pedido {ocupacao[1]} | Atividade {ocupacao[2]} | Item {ocupacao[3]} | "
                        f"{ocupacao[4]:.2f} unidades | {ocupacao[5].strftime('%Y-%m-%d %H:%M')} → {ocupacao[6].strftime('%Y-%m-%d %H:%M')} | {temp_info}"
                    )

        # Mostrar configurações de temperatura
        if self.intervalos_temperatura:
            logger.info("🌡️ Configurações de Temperatura:")
            for temp, ini, fim in self.intervalos_temperatura:
                logger.info(
                    f"   {temp}°C | {ini.strftime('%Y-%m-%d %H:%M')} → {fim.strftime('%Y-%m-%d %H:%M')}"
                )

        if not tem_ocupacao and not self.intervalos_temperatura:
            logger.info("🔹 Nenhuma ocupação ou configuração de temperatura registrada.")

    def obter_temperaturas_configuradas(self) -> List[Tuple[int, datetime, datetime]]:
        """Retorna todas as configurações de temperatura."""
        return self.intervalos_temperatura.copy()

    # ============================================
    # 📈 Estatísticas e Relatórios
    # ============================================
    def obter_estatisticas_capacidade(self) -> dict:
        """Retorna estatísticas detalhadas sobre as capacidades da câmara."""
        return {
            'numeracao_niveis_fisicos': {
                'primeiro_nivel': self.capacidade_niveis_min,
                'ultimo_nivel': self.capacidade_niveis_max,
                'range_niveis': f"{self.capacidade_niveis_min}-{self.capacidade_niveis_max}"
            },
            'numeracao_caixas': {
                'primeira_caixa': self.capacidade_caixa_min,
                'ultima_caixa': self.capacidade_caixa_max,
                'range_caixas': f"{self.capacidade_caixa_min}-{self.capacidade_caixa_max}"
            },
            'estrutura_telas': {
                'telas_por_nivel': self.nivel_tela,
                'niveis_fisicos_base': self.qtd_niveis_base,
                'total_niveis_tela': self.qtd_niveis_total,
                'total_caixas': self.qtd_caixas
            },
            'listas_disponiveis': {
                'niveis_fisicos_disponiveis': list(range(self.capacidade_niveis_min, self.capacidade_niveis_max + 1)),
                'caixas_disponiveis': list(range(self.capacidade_caixa_min, self.capacidade_caixa_max + 1)),
                'niveis_tela_disponiveis': self.obter_numeros_niveis_tela_disponiveis()
            },
            'temperatura': {
                'faixa_min': self.faixa_temperatura_min,
                'faixa_max': self.faixa_temperatura_max,
                'amplitude': self.faixa_temperatura_max - self.faixa_temperatura_min
            },
            'observacao': 'A capacidade de armazenamento de cada nível de tela/caixa é definida pela atividade, não pelo equipamento.'
        }