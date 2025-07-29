from models.equipamentos.equipamento import Equipamento
from enums.producao.tipo_setor import TipoSetor
from enums.equipamentos.tipo_equipamento import TipoEquipamento
from typing import List, Tuple, Optional
from datetime import datetime
from utils.logs.logger_factory import setup_logger

logger = setup_logger('Freezer')


class Freezer(Equipamento):
    """
    🧊 Representa um Freezer que armazena caixas numeradas.
    ✔️ Controle de temperatura global aplicado a todas as caixas do equipamento.
    ✔️ Cada caixa pode armazenar qualquer quantidade (definida na atividade).
    ✔️ Caixas numeradas de capacidade_caixa_min até capacidade_caixa_max.
    ✔️ Ocupação por caixa individual com registro de tempo.
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

        self.capacidade_caixa_min = capacidade_caixa_min
        self.capacidade_caixa_max = capacidade_caixa_max
        self.faixa_temperatura_min = faixa_temperatura_min
        self.faixa_temperatura_max = faixa_temperatura_max

        # Calcula a quantidade total de caixas baseada no range min-max
        self.qtd_caixas = self.capacidade_caixa_max - self.capacidade_caixa_min + 1

        # 📦 Ocupações individualizadas por caixa: (id_ordem, id_pedido, id_atividade, id_item, quantidade_alocada, inicio, fim)
        self.caixas_ocupacoes: List[List[Tuple[int, int, int, int, float, datetime, datetime]]] = [[] for _ in range(self.qtd_caixas)]

        # 🌡️ Controle de temperatura por intervalo (global para todo o freezer): (temperatura, inicio, fim)
        self.intervalos_temperatura: List[Tuple[int, datetime, datetime]] = []

    # ============================================
    # 🔍 Propriedades de Capacidade
    # ============================================
    @property
    def total_caixas_disponiveis(self) -> int:
        """Retorna o total de caixas disponíveis."""
        return self.qtd_caixas

    def obter_primeira_caixa(self) -> int:
        """Retorna o número da primeira caixa física."""
        return self.capacidade_caixa_min

    def obter_ultima_caixa(self) -> int:
        """Retorna o número da última caixa física."""
        return self.capacidade_caixa_max

    def obter_range_caixas(self) -> tuple:
        """Retorna o range de numeração das caixas (primeira, última)."""
        return (self.capacidade_caixa_min, self.capacidade_caixa_max)

    def obter_numeros_caixas_disponiveis(self) -> List[int]:
        """Retorna lista com todos os números das caixas físicas disponíveis."""
        return list(range(self.capacidade_caixa_min, self.capacidade_caixa_max + 1))

    # ============================================
    # 🌡️ Controle de Temperatura (Global)
    # ============================================
    def obter_temperatura_periodo(self, inicio: datetime, fim: datetime) -> Optional[int]:
        """Retorna a temperatura configurada para o período (se houver)."""
        for temp, ini, f in self.intervalos_temperatura:
            if not (fim <= ini or inicio >= f):  # há sobreposição
                return temp
        return None

    def verificar_compatibilidade_temperatura(self, temperatura_desejada: int, inicio: datetime, fim: datetime) -> bool:
        """Verifica se a temperatura desejada é compatível com o período."""
        temperatura_atual = self.obter_temperatura_periodo(inicio, fim)
        
        if temperatura_atual is None:
            return True  # Sem conflito
        
        if temperatura_atual != temperatura_desejada:
            logger.warning(
                f"❌ Temperatura incompatível no {self.nome} entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}. "
                f"Desejada: {temperatura_desejada}°C | Configurada: {temperatura_atual}°C"
            )
            return False
        
        return True

    def configurar_temperatura(self, temperatura: int, inicio: datetime, fim: datetime) -> bool:
        """Configura temperatura para um intervalo de tempo (aplicada a todo o freezer)."""
        if temperatura < self.faixa_temperatura_min or temperatura > self.faixa_temperatura_max:
            logger.warning(
                f"❌ Temperatura {temperatura}°C fora da faixa permitida "
                f"({self.faixa_temperatura_min}°C a {self.faixa_temperatura_max}°C) no {self.nome}"
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
                    f"❌ Não é possível alterar temperatura no {self.nome} entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}. "
                    f"Há ocupações no período com temperatura {temperatura_atual}°C."
                )
                return False

        self.intervalos_temperatura.append((temperatura, inicio, fim))
        logger.info(
            f"🌡️ Temperatura configurada no {self.nome}: {temperatura}°C "
            f"para {inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')}"
        )
        return True

    def tem_ocupacao_periodo(self, inicio: datetime, fim: datetime) -> bool:
        """Verifica se há ocupações em qualquer caixa no período."""
        return self.tem_ocupacao_caixas_periodo(inicio, fim)

    # ============================================
    # 🔍 Consulta de Ocupação - CAIXAS
    # ============================================
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

    def obter_ocupacao_caixa(self, caixa_index: int, inicio: datetime, fim: datetime) -> float:
        """Retorna a quantidade total ocupada em uma caixa no período especificado."""
        if caixa_index < 0 or caixa_index >= self.qtd_caixas:
            return 0.0
        
        ocupada = 0.0
        for ocupacao in self.caixas_ocupacoes[caixa_index]:
            if not (fim <= ocupacao[5] or inicio >= ocupacao[6]):  # há sobreposição temporal
                ocupada += ocupacao[4]  # quantidade_alocada
        return ocupada

    def obter_ocupacao_todas_caixas(self, inicio: datetime, fim: datetime) -> List[float]:
        """Retorna lista com a ocupação de todas as caixas no período especificado."""
        ocupacoes = []
        for i in range(self.qtd_caixas):
            ocupacoes.append(self.obter_ocupacao_caixa(i, inicio, fim))
        return ocupacoes

    def caixa_disponivel(self, numero_caixa: int, inicio: datetime, fim: datetime) -> bool:
        """Verifica se uma caixa está completamente livre no período."""
        caixa_index = self.obter_indice_por_caixa_fisica(numero_caixa)
        if caixa_index == -1:
            return False
        
        # Verifica se há alguma ocupação na caixa durante o período
        for ocupacao in self.caixas_ocupacoes[caixa_index]:
            if not (fim <= ocupacao[5] or inicio >= ocupacao[6]):  # há sobreposição
                return False
        
        return True

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
            if not self.caixa_disponivel(numero_caixa, inicio, fim):
                return True
        
        return False

    def obter_ocupacao_caixas_periodo_detalhada(self, inicio: datetime, fim: datetime, caixas: List[int] = None) -> dict:
        """
        Retorna informações detalhadas sobre ocupação em caixas durante um período específico.
        
        Args:
            inicio (datetime): Data de início do período
            fim (datetime): Data de fim do período
            caixas (List[int], optional): Lista de números de caixas físicas para verificar.
                                        Se None, verifica todas as caixas disponíveis.
        
        Returns:
            dict: Dicionário com informações detalhadas de ocupação por caixa
        """
        # Define as caixas a serem verificadas
        if caixas is None:
            caixas = list(range(self.capacidade_caixa_min, self.capacidade_caixa_max + 1))
        
        # Valida caixas solicitadas
        caixas_validas = [c for c in caixas if self.capacidade_caixa_min <= c <= self.capacidade_caixa_max]
        
        resultado = {
            'caixas': {},
            'total_caixas_ocupadas': 0,
            'percentual_ocupacao': 0.0
        }
        
        # Verifica ocupação por caixa
        for numero_caixa in caixas_validas:
            caixa_index = self.obter_indice_por_caixa_fisica(numero_caixa)
            ocupacoes_caixa = []
            ocupado = False
            
            # Verifica cada ocupação na caixa
            for ocupacao in self.caixas_ocupacoes[caixa_index]:
                if not (fim <= ocupacao[5] or inicio >= ocupacao[6]):  # há sobreposição
                    ocupacoes_caixa.append({
                        'id_ordem': ocupacao[0],
                        'id_pedido': ocupacao[1],
                        'id_atividade': ocupacao[2],
                        'id_item': ocupacao[3],
                        'quantidade_alocada': ocupacao[4],
                        'inicio': ocupacao[5],
                        'fim': ocupacao[6],
                        'temperatura': self.obter_temperatura_periodo(ocupacao[5], ocupacao[6])
                    })
                    ocupado = True
            
            resultado['caixas'][f'caixa_{numero_caixa}'] = {
                'ocupado': ocupado,
                'ocupacoes': ocupacoes_caixa,
                'quantidade_ocupacoes': len(ocupacoes_caixa)
            }
            
            if ocupado:
                resultado['total_caixas_ocupadas'] += 1
        
        # Calcula percentual de ocupação
        if len(caixas_validas) > 0:
            resultado['percentual_ocupacao'] = (resultado['total_caixas_ocupadas'] / len(caixas_validas)) * 100
        
        return resultado

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

        # Verificar se a caixa está disponível no período
        if not self.caixa_disponivel(numero_caixa, inicio, fim):
            logger.warning(f"❌ Caixa {numero_caixa} não está disponível no período {inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')}")
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
            f"📦 Ocupação caixa adicionada no {self.nome} - Caixa {numero_caixa} | "
            f"Ordem {id_ordem} | Pedido {id_pedido} | Atividade {id_atividade} | Item {id_item} | "
            f"{quantidade:.2f} unidades | {inicio.strftime('%H:%M')} → {fim.strftime('%H:%M')}"
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
            f"🔄 Ocupações da caixa {numero_caixa} do {self.nome} foram sobrescritas. "
            f"Total de ocupações: {len(ocupacoes)}"
        )
        return True

    # ============================================
    # 🔓 Liberação
    # ============================================
    def liberar_por_atividade(self, id_ordem: int, id_pedido: int, id_atividade: int):
        """Libera ocupações específicas por atividade."""
        total_liberadas = 0
        
        for caixa_index in range(self.qtd_caixas):
            antes = len(self.caixas_ocupacoes[caixa_index])
            self.caixas_ocupacoes[caixa_index] = [
                ocupacao for ocupacao in self.caixas_ocupacoes[caixa_index]
                if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido and ocupacao[2] == id_atividade)
            ]
            total_liberadas += antes - len(self.caixas_ocupacoes[caixa_index])

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
        
        for caixa_index in range(self.qtd_caixas):
            antes = len(self.caixas_ocupacoes[caixa_index])
            self.caixas_ocupacoes[caixa_index] = [
                ocupacao for ocupacao in self.caixas_ocupacoes[caixa_index]
                if not (ocupacao[0] == id_ordem and ocupacao[1] == id_pedido)
            ]
            total_liberadas += antes - len(self.caixas_ocupacoes[caixa_index])

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
        
        for caixa_index in range(self.qtd_caixas):
            antes = len(self.caixas_ocupacoes[caixa_index])
            self.caixas_ocupacoes[caixa_index] = [
                ocupacao for ocupacao in self.caixas_ocupacoes[caixa_index]
                if ocupacao[0] != id_ordem
            ]
            total_liberadas += antes - len(self.caixas_ocupacoes[caixa_index])

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

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        """Libera ocupações que já finalizaram."""
        total_liberadas = 0
        
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
                f"do {self.nome} finalizadas até {horario_atual.strftime('%H:%M')}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação finalizada encontrada para liberar no {self.nome} até {horario_atual.strftime('%H:%M')}."
            )
        return total_liberadas

    def liberar_todas_ocupacoes(self):
        """Limpa todas as ocupações de todas as caixas e temperaturas."""
        total_ocupacoes = sum(len(ocupacoes) for ocupacoes in self.caixas_ocupacoes)
        total_temp = len(self.intervalos_temperatura)
        
        for caixa_ocupacoes in self.caixas_ocupacoes:
            caixa_ocupacoes.clear()
        self.intervalos_temperatura.clear()
        
        logger.info(
            f"🔓 Todas as ocupações do {self.nome} foram removidas. "
            f"Ocupações: {total_ocupacoes} | Temperaturas: {total_temp}"
        )

    def liberar_por_intervalo(self, inicio: datetime, fim: datetime):
        """Libera ocupações que se sobrepõem ao intervalo especificado."""
        total_liberadas = 0
        
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
                f"do {self.nome} entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
            )
        else:
            logger.warning(
                f"🔓 Nenhuma ocupação encontrada para liberar no {self.nome} "
                f"entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
            )

    # ============================================
    # 📅 Agenda e Relatórios
    # ============================================
    def mostrar_agenda(self):
        """Mostra agenda detalhada por caixa e temperatura."""
        logger.info("==============================================")
        logger.info(f"📅 Agenda do {self.nome}")
        logger.info(f"📊 Numeração das caixas: {self.capacidade_caixa_min} a {self.capacidade_caixa_max}")
        logger.info(f"📏 Dimensões: {self.qtd_caixas} caixas totais (Caixas {self.capacidade_caixa_min} a {self.capacidade_caixa_max})")
        logger.info(f"🌡️ Faixa de temperatura: {self.faixa_temperatura_min}°C a {self.faixa_temperatura_max}°C")
        logger.info("==============================================")

        tem_ocupacao = False
        
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
                        f"{ocupacao[4]:.2f} unidades | {ocupacao[5].strftime('%H:%M')} → {ocupacao[6].strftime('%H:%M')} | {temp_info}"
                    )

        # Mostrar configurações de temperatura
        if self.intervalos_temperatura:
            logger.info("🌡️ Configurações de Temperatura:")
            for temp, ini, fim in self.intervalos_temperatura:
                logger.info(
                    f"   {temp}°C | {ini.strftime('%H:%M')} → {fim.strftime('%H:%M')}"
                )

        if not tem_ocupacao and not self.intervalos_temperatura:
            logger.info("📦 Nenhuma ocupação ou configuração de temperatura registrada.")

    def obter_temperaturas_configuradas(self) -> List[Tuple[int, datetime, datetime]]:
        """Retorna todas as configurações de temperatura."""
        return self.intervalos_temperatura.copy()

    # ============================================
    # 📈 Estatísticas e Relatórios
    # ============================================
    def obter_estatisticas_capacidade(self) -> dict:
        """Retorna estatísticas detalhadas sobre as capacidades do freezer."""
        return {
            'numeracao_caixas': {
                'primeira_caixa': self.capacidade_caixa_min,
                'ultima_caixa': self.capacidade_caixa_max,
                'range_caixas': f"{self.capacidade_caixa_min}-{self.capacidade_caixa_max}"
            },
            'estrutura': {
                'total_caixas': self.qtd_caixas,
                'caixas_disponiveis': list(range(self.capacidade_caixa_min, self.capacidade_caixa_max + 1))
            },
            'temperatura': {
                'faixa_min': self.faixa_temperatura_min,
                'faixa_max': self.faixa_temperatura_max,
                'amplitude': self.faixa_temperatura_max - self.faixa_temperatura_min
            },
            'observacao': 'A capacidade de armazenamento de cada caixa é definida pela atividade, não pelo equipamento.'
        }