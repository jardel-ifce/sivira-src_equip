import unicodedata
import math
from datetime import datetime, timedelta
from typing import List, Tuple, Optional, TYPE_CHECKING
from models.equipamentos.masseira import Masseira
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular
from enums.equipamentos.tipo_velocidade import TipoVelocidade
from enums.equipamentos.tipo_mistura import TipoMistura
from utils.logs.logger_factory import setup_logger

logger = setup_logger('GestorMisturadoras')


class GestorMisturadoras:
    """
    🥣 Gestor especializado para controle de masseiras com algoritmos de distribuição otimizada,
    utilizando Backward Scheduling minuto a minuto com FIPs (Fatores de Importância de Prioridade).
    
    Baseado em:
    - Multiple Knapsack Problem para distribuição ótima
    - First Fit Decreasing (FFD) com restrições de capacidade mínima
    - Binary Space Partitioning para divisão eficiente
    - Backward scheduling com intervalos flexíveis para mesmo id_item
    
    Funcionalidades:
    - Verificação prévia de viabilidade total
    - Distribuição otimizada respeitando capacidades mín/máx
    - Algoritmo de redistribuição com balanceamento de carga
    - Permite sobreposição do mesmo id_item com validação dinâmica
    - Priorização por FIP com backward scheduling
    - Otimização inteligente: evita tentativas individuais quando distribuição é obrigatória
    """

    def __init__(self, masseiras: List[Masseira]):
        """
        Inicializa o gestor com uma lista de masseiras disponíveis.
        """
        self.masseiras = masseiras

    # ==========================================================
    # 📊 Análise de Viabilidade e Capacidades
    # ==========================================================
    def _calcular_capacidade_total_sistema(self, atividade: "AtividadeModular", id_item: int, 
                                          inicio: datetime, fim: datetime) -> Tuple[float, float]:
        """
        Calcula capacidade total disponível do sistema para um item específico.
        Retorna: (capacidade_total_disponivel, capacidade_maxima_teorica)
        """
        capacidade_disponivel_total = 0.0
        capacidade_maxima_teorica = 0.0
        
        for masseira in self.masseiras:
            # Capacidade máxima da masseira
            cap_max = masseira.capacidade_gramas_max
            capacidade_maxima_teorica += cap_max
            
            # Verifica se pode receber o item no período (permite sobreposição mesmo item)
            if masseira.esta_disponivel_para_item(inicio, fim, id_item):
                # Calcula capacidade disponível considerando ocupações existentes do mesmo item
                capacidade_disponivel = masseira.obter_capacidade_disponivel_item(id_item, inicio, fim)
                capacidade_disponivel_total += max(0, capacidade_disponivel)
        
        return capacidade_disponivel_total, capacidade_maxima_teorica

    def _verificar_viabilidade_quantidade(self, atividade: "AtividadeModular", quantidade_total: float,
                                        id_item: int, inicio: datetime, fim: datetime) -> Tuple[bool, str]:
        """
        📚 Multiple Knapsack Problem (MKP): Problema clássico de otimização combinatória onde
        múltiplos "recipientes" (knapsacks) têm capacidades limitadas e devem acomodar itens
        com restrições. Usado aqui para verificar se o conjunto de masseiras pode teoricamente 
        comportar a demanda antes de tentar algoritmos de alocação mais custosos computacionalmente.
        
        Verifica se é teoricamente possível alocar a quantidade solicitada.
        """
        cap_disponivel, cap_teorica = self._calcular_capacidade_total_sistema(
            atividade, id_item, inicio, fim
        )
        
        if quantidade_total > cap_teorica:
            return False, f"Quantidade {quantidade_total}g excede capacidade máxima teórica do sistema ({cap_teorica}g)"
        
        if quantidade_total > cap_disponivel:
            return False, f"Quantidade {quantidade_total}g excede capacidade disponível ({cap_disponivel}g) no período"
        
        # Verifica se existem masseiras disponíveis
        masseiras_disponiveis = [
            m for m in self.masseiras 
            if m.esta_disponivel_para_item(inicio, fim, id_item)
        ]
        
        if not masseiras_disponiveis:
            return False, "Nenhuma masseira disponível para o item no período"
        
        # Verifica viabilidade com capacidades mínimas
        capacidade_minima_total = sum(m.capacidade_gramas_min for m in masseiras_disponiveis)
        if quantidade_total < min(m.capacidade_gramas_min for m in masseiras_disponiveis):
            if len(masseiras_disponiveis) == 1:
                return True, "Viável com uma masseira"
        elif quantidade_total >= capacidade_minima_total:
            return True, "Viável com múltiplas masseiras"
        else:
            return False, f"Quantidade {quantidade_total}g insuficiente para capacidades mínimas ({capacidade_minima_total}g)"
        
        return True, "Quantidade viável"

    # ==========================================================
    # 🧮 Algoritmos de Distribuição Otimizada
    # ==========================================================
    def _algoritmo_distribuicao_balanceada(self, quantidade_total: float, 
                                          masseiras_disponiveis: List[Tuple[Masseira, float, List[TipoVelocidade], Optional[TipoMistura]]]) -> List[Tuple[Masseira, float, List[TipoVelocidade], Optional[TipoMistura]]]:
        """
        Algoritmo de distribuição baseado em Binary Space Partitioning adaptado.
        
        📚 Binary Space Partitioning: Técnica que divide recursivamente o espaço de soluções,
        originalmente usada em computação gráfica. Aqui adaptada para dividir a quantidade total
        proporcionalmente entre masseiras, considerando suas capacidades disponíveis.
        ⚡ OTIMIZADO PARA BACKWARD SCHEDULING: Evita operações lentas que conflitam com tentativas rápidas.
        
        Estratégia:
        1. Ordena masseiras por capacidade disponível (maior primeiro)
        2. Aplica divisão proporcional otimizada
        3. Ajuste único e direto (sem iterações)
        """
        if not masseiras_disponiveis:
            return []
        
        # Ordena por capacidade disponível (maior primeiro)
        masseiras_ordenadas = sorted(masseiras_disponiveis, key=lambda x: x[1], reverse=True)
        
        # Capacidade total disponível
        capacidade_total_disponivel = sum(cap for _, cap, _, _ in masseiras_ordenadas)
        
        if capacidade_total_disponivel < quantidade_total:
            return []
        
        # ⚡ DISTRIBUIÇÃO PROPORCIONAL DIRETA - Sem ajustes iterativos posteriores
        distribuicao = []
        quantidade_restante = quantidade_total
        
        for i, (masseira, cap_disponivel, velocidades, tipo_mistura) in enumerate(masseiras_ordenadas):
            if quantidade_restante <= 0:
                break
                
            if i == len(masseiras_ordenadas) - 1:
                # Última masseira: recebe todo o restante (se couber)
                quantidade_masseira = min(quantidade_restante, cap_disponivel)
            else:
                # Distribuição proporcional direta
                proporcao = cap_disponivel / capacidade_total_disponivel
                quantidade_proporcional = quantidade_total * proporcao
                
                # ⚡ AJUSTE DIRETO: Garante limites sem iterações
                quantidade_masseira = max(
                    masseira.capacidade_gramas_min,
                    min(quantidade_proporcional, cap_disponivel, quantidade_restante)
                )
            
            # Só adiciona se atende capacidade mínima
            if quantidade_masseira >= masseira.capacidade_gramas_min:
                distribuicao.append((masseira, quantidade_masseira, velocidades, tipo_mistura))
                quantidade_restante -= quantidade_masseira
        
        # ⚡ VERIFICAÇÃO FINAL RÁPIDA: Se sobrou quantidade significativa, falha rápido
        if quantidade_restante > 1.0:  # Tolerância de 1g
            return []  # Falha rápida para backward scheduling tentar próxima janela
        
        return distribuicao

    def _redistribuir_excedentes(self, distribuicao: List[Tuple[Masseira, float, List[TipoVelocidade], Optional[TipoMistura]]], 
                                quantidade_target: float) -> List[Tuple[Masseira, float, List[TipoVelocidade], Optional[TipoMistura]]]:
        """
        📚 Fast Load Balancing: Versão otimizada para backward scheduling que evita iterações longas.
        Aplica ajuste direto em uma única passada para ser compatível com tentativas rápidas
        de janelas temporais. Prioriza velocidade sobre precisão absoluta na distribuição.
        
        Redistribui quantidades para atingir o target exato respeitando limites - OTIMIZADO PARA SPEED.
        """
        quantidade_atual = sum(qtd for _, qtd, _, _ in distribuicao)
        diferenca = quantidade_target - quantidade_atual
        
        # Tolerância mais flexível para evitar iterações desnecessárias
        if abs(diferenca) < 1.0:  # Tolerância de 1g para speed
            return distribuicao
        
        # 🚀 AJUSTE ÚNICO E DIRETO - Sem iterações que conflitem com backward scheduling
        if diferenca > 0:
            # Precisa adicionar quantidade - distribui o excesso proporcionalmente
            masseiras_com_margem = [
                (i, masseira.capacidade_gramas_max - qtd) 
                for i, (masseira, qtd, _, _) in enumerate(distribuicao)
                if masseira.capacidade_gramas_max - qtd > 0
            ]
            
            if masseiras_com_margem:
                margem_total = sum(margem for _, margem in masseiras_com_margem)
                
                for i, margem_disponivel in masseiras_com_margem:
                    if diferenca <= 0:
                        break
                    
                    masseira, qtd_atual, vel, mistura = distribuicao[i]
                    proporcao = margem_disponivel / margem_total
                    adicionar = min(diferenca, diferenca * proporcao)
                    adicionar = min(adicionar, margem_disponivel)  # Não excede capacidade
                    
                    distribuicao[i] = (masseira, qtd_atual + adicionar, vel, mistura)
                    diferenca -= adicionar
        
        elif diferenca < 0:
            # Precisa remover quantidade - remove proporcionalmente das que têm margem
            diferenca = abs(diferenca)
            masseiras_com_margem = [
                (i, qtd - masseira.capacidade_gramas_min) 
                for i, (masseira, qtd, _, _) in enumerate(distribuicao)
                if qtd - masseira.capacidade_gramas_min > 0
            ]
            
            if masseiras_com_margem:
                margem_total = sum(margem for _, margem in masseiras_com_margem)
                
                for i, margem_removivel in masseiras_com_margem:
                    if diferenca <= 0:
                        break
                    
                    masseira, qtd_atual, vel, mistura = distribuicao[i]
                    proporcao = margem_removivel / margem_total
                    remover = min(diferenca, diferenca * proporcao)
                    remover = min(remover, margem_removivel)  # Não fica abaixo do mínimo
                    
                    distribuicao[i] = (masseira, qtd_atual - remover, vel, mistura)
                    diferenca -= remover
        
        # Remove masseiras com quantidade abaixo do mínimo (ajuste final rápido)
        distribuicao_final = [
            (masseira, qtd, vel, mistura) for masseira, qtd, vel, mistura in distribuicao
            if qtd >= masseira.capacidade_gramas_min
        ]
        
        return distribuicao_final

    def _algoritmo_first_fit_decreasing(self, quantidade_total: float,
                                      masseiras_disponiveis: List[Tuple[Masseira, float, List[TipoVelocidade], Optional[TipoMistura]]]) -> List[Tuple[Masseira, float, List[TipoVelocidade], Optional[TipoMistura]]]:
        """
        📚 First Fit Decreasing (FFD): Algoritmo clássico de Bin Packing que ordena itens
        por tamanho decrescente e aloca cada item no primeiro recipiente que couber.
        Garante aproximação de 11/9 do ótimo e é amplamente usado em problemas de otimização.
        Adaptado aqui para respeitar capacidades mínimas das masseiras, evitando
        distribuições que violem restrições operacionais.
        
        Implementação do algoritmo First Fit Decreasing adaptado para capacidades mínimas.
        """
        # Ordena masseiras por capacidade disponível (maior primeiro)
        masseiras_ordenadas = sorted(masseiras_disponiveis, key=lambda x: x[1], reverse=True)
        
        distribuicao = []
        quantidade_restante = quantidade_total
        
        for masseira, cap_disponivel, velocidades, tipo_mistura in masseiras_ordenadas:
            if quantidade_restante <= 0:
                break
            
            # Calcula quanto alocar nesta masseira
            if quantidade_restante >= masseira.capacidade_gramas_min:
                quantidade_alocar = min(quantidade_restante, cap_disponivel)
                
                # Garante que não fica quantidade insuficiente para próximas masseiras
                masseiras_restantes = [m for m, _, _, _ in masseiras_ordenadas 
                                    if m != masseira and (quantidade_restante - quantidade_alocar) > 0]
                
                if masseiras_restantes:
                    cap_min_restantes = min(m.capacidade_gramas_min for m in masseiras_restantes)
                    if quantidade_restante - quantidade_alocar < cap_min_restantes and quantidade_restante - quantidade_alocar > 0:
                        # Ajusta para deixar quantidade suficiente
                        quantidade_alocar = quantidade_restante - cap_min_restantes
                
                if quantidade_alocar >= masseira.capacidade_gramas_min:
                    distribuicao.append((masseira, quantidade_alocar, velocidades, tipo_mistura))
                    quantidade_restante -= quantidade_alocar
        
        return distribuicao if quantidade_restante <= 0.1 else []

    def _calcular_distribuicao_otima(self, quantidade_total: float, 
                                   masseiras_disponiveis: List[Tuple[Masseira, float, List[TipoVelocidade], Optional[TipoMistura]]]) -> List[Tuple[Masseira, float, List[TipoVelocidade], Optional[TipoMistura]]]:
        """
        ⚡ OTIMIZADO PARA BACKWARD SCHEDULING: Calcula distribuição ótima com limite de tempo.
        Testa algoritmos rapidamente e retorna a primeira solução viável para não atrasar
        o backward scheduling que precisa testar muitas janelas temporais.
        """
        # 🚀 ESTRATÉGIA 1: Tenta distribuição balanceada (mais rápida)
        dist_balanceada = self._algoritmo_distribuicao_balanceada(quantidade_total, masseiras_disponiveis)
        
        if dist_balanceada and sum(qtd for _, qtd, _, _ in dist_balanceada) >= quantidade_total * 0.98:
            logger.debug(f"📊 Distribuição balanceada aceita com {len(dist_balanceada)} masseiras")
            return dist_balanceada
        
        # 🚀 ESTRATÉGIA 2: Se balanceada falhou, tenta FFD
        dist_ffd = self._algoritmo_first_fit_decreasing(quantidade_total, masseiras_disponiveis)
        
        if dist_ffd and sum(qtd for _, qtd, _, _ in dist_ffd) >= quantidade_total * 0.98:
            logger.debug(f"📊 Distribuição FFD aceita com {len(dist_ffd)} masseiras")
            return dist_ffd
        
        # ❌ Nenhuma estratégia funcionou - falha rápida para backward scheduling continuar
        logger.debug("📊 Nenhuma distribuição viável encontrada - prosseguindo backward scheduling")
        return []

    def _calcular_balanceamento(self, distribuicao: List[Tuple[Masseira, float, List[TipoVelocidade], Optional[TipoMistura]]]) -> float:
        """
        Calcula score de balanceamento da distribuição (maior = mais balanceado).
        """
        if len(distribuicao) <= 1:
            return 1.0
        
        quantidades = [qtd for _, qtd, _, _ in distribuicao]
        media = sum(quantidades) / len(quantidades)
        variancia = sum((qtd - media) ** 2 for qtd in quantidades) / len(quantidades)
        
        # Score inversamente proporcional à variância
        return 1.0 / (1.0 + variancia / media**2) if media > 0 else 0.0

    # ==========================================================
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
    # ==========================================================
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[Masseira]:
        """
        Ordena as masseiras com base no FIP da atividade.
        Equipamentos com menor FIP são priorizados.
        """
        return sorted(
            self.masseiras, 
            key=lambda m: atividade.fips_equipamentos.get(m, 999)
        )

    # ==========================================================
    # 🔧 Obtenção de Configurações
    # ==========================================================
    def _obter_velocidades_para_masseira(self, atividade: "AtividadeModular", masseira: Masseira) -> List[TipoVelocidade]:
        """Obtém as velocidades configuradas para uma masseira específica."""
        try:
            if hasattr(atividade, "configuracoes_equipamentos"):
                chave = self._normalizar_nome(masseira.nome)
                config = atividade.configuracoes_equipamentos.get(chave, {})
                velocidades_raw = config.get("velocidade", [])
                
                if isinstance(velocidades_raw, str):
                    velocidades_raw = [velocidades_raw]
                
                velocidades = []
                for v in velocidades_raw:
                    try:
                        velocidades.append(TipoVelocidade[v.strip().upper()])
                    except (KeyError, AttributeError):
                        logger.warning(f"⚠️ Velocidade inválida: '{v}' para masseira {masseira.nome}")
                
                if not velocidades:
                    logger.debug(f"⚠️ Nenhuma velocidade definida para masseira {masseira.nome}")
                
                return velocidades
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter velocidades para {masseira.nome}: {e}")
        
        return []

    def _obter_tipo_mistura_para_masseira(self, atividade: "AtividadeModular", masseira: Masseira) -> Optional[TipoMistura]:
        """Obtém o tipo de mistura configurado para uma masseira específica."""
        try:
            if hasattr(atividade, "configuracoes_equipamentos"):
                chave = self._normalizar_nome(masseira.nome)
                config = atividade.configuracoes_equipamentos.get(chave, {})
                raw = config.get("tipo_mistura")
                
                if raw is None:
                    logger.debug(f"⚠️ Tipo de mistura não definido para masseira {masseira.nome}")
                    return None
                
                if isinstance(raw, list):
                    raw = raw[0] if raw else None
                
                if raw is None:
                    return None
                
                try:
                    return TipoMistura[raw.strip().upper()]
                except (KeyError, AttributeError):
                    logger.warning(f"⚠️ Tipo de mistura inválido: '{raw}' para masseira {masseira.nome}")
                    return None
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter tipo de mistura para {masseira.nome}: {e}")
        
        return None

    @staticmethod
    def _normalizar_nome(nome: str) -> str:
        """Normaliza nome do equipamento para busca em configurações."""
        return (
            unicodedata.normalize("NFKD", nome.lower())
            .encode("ASCII", "ignore")
            .decode()
            .replace(" ", "_")
        )

    def _obter_ids_atividade(self, atividade: "AtividadeModular") -> Tuple[int, int, int, int]:
        """
        Extrai os IDs da atividade de forma consistente.
        Retorna: (id_ordem, id_pedido, id_atividade, id_item)
        """
        # Tenta diferentes atributos para compatibilidade
        id_ordem = getattr(atividade, 'id_ordem', None) or getattr(atividade, 'ordem_id', 0)
        id_pedido = getattr(atividade, 'id_pedido', None) or getattr(atividade, 'pedido_id', 0)
        id_atividade = getattr(atividade, 'id_atividade', 0)
        id_item = getattr(atividade, 'id_item', 0)
        
        return id_ordem, id_pedido, id_atividade, id_item

    def _verificar_compatibilidade_parametros(self, masseira: Masseira, id_item: int, velocidades: List[TipoVelocidade], tipo_mistura: Optional[TipoMistura], inicio: datetime, fim: datetime) -> bool:
        """
        Verifica se os parâmetros são compatíveis com ocupações existentes do mesmo produto.
        🎯 REGRA DE SOBREPOSIÇÃO: Permite apenas simultaneidade exata ou períodos distintos.
        """
        
        for ocupacao in masseira.obter_ocupacoes_item_periodo(id_item, inicio, fim):
            # ocupacao = (id_ordem, id_pedido, id_atividade, id_item, quantidade, velocidades, tipo_mistura, inicio, fim)
            inicio_existente = ocupacao[7]
            fim_existente = ocupacao[8]
            vel_existentes = ocupacao[5]
            mistura_existente = ocupacao[6]
            
            # 🎯 REGRA DE JANELA TEMPORAL: Só permite simultaneidade exata ou períodos distintos
            simultaneidade_exata = (inicio == inicio_existente and fim == fim_existente)
            periodos_distintos = (fim <= inicio_existente or inicio >= fim_existente)
            
            if not (simultaneidade_exata or periodos_distintos):
                logger.debug(f"❌ Sobreposição temporal inválida: período {inicio.strftime('%H:%M')}-{fim.strftime('%H:%M')} conflita com ocupação existente {inicio_existente.strftime('%H:%M')}-{fim_existente.strftime('%H:%M')}")
                return False
            
            # Se há simultaneidade exata, verifica compatibilidade de parâmetros
            if simultaneidade_exata:
                # Verificar se velocidades são compatíveis
                if set(vel_existentes) != set(velocidades):
                    logger.debug(f"❌ Velocidades incompatíveis: existentes={[v.name for v in vel_existentes]}, novas={[v.name for v in velocidades]}")
                    return False
                
                # Verificar se tipo de mistura é compatível
                if mistura_existente != tipo_mistura:
                    logger.debug(f"❌ Tipo de mistura incompatível: existente={mistura_existente.name if mistura_existente else None}, novo={tipo_mistura.name if tipo_mistura else None}")
                    return False
        
        return True

    # ==========================================================
    # 🔄 Alocação Otimizada Individual e Distribuída
    # ==========================================================
    def _tentar_alocacao_individual(
        self, 
        inicio_tentativa: datetime, 
        fim_tentativa: datetime,
        atividade: "AtividadeModular",
        quantidade_alocada: float,
        masseiras_ordenadas: List[Masseira],
        id_ordem: int, id_pedido: int, id_atividade: int, id_item: int
    ) -> Optional[Tuple[Masseira, datetime, datetime]]:
        """
        Tenta alocar toda a quantidade em uma única masseira.
        Permite sobreposição do mesmo id_item com validação dinâmica de capacidade.
        """
        for masseira in masseiras_ordenadas:
            # Obter configurações técnicas
            velocidades = self._obter_velocidades_para_masseira(atividade, masseira)
            tipo_mistura = self._obter_tipo_mistura_para_masseira(atividade, masseira)
            
            # Verifica disponibilidade básica (parâmetros técnicos)
            if not masseira.verificar_disponibilidade(quantidade_alocada, velocidades, tipo_mistura):
                logger.debug(f"❌ {masseira.nome}: não atende requisitos técnicos")
                continue
            
            # Verifica se pode alocar considerando mesmo item (intervalos flexíveis)
            if not masseira.esta_disponivel_para_item(inicio_tentativa, fim_tentativa, id_item):
                logger.debug(f"❌ {masseira.nome}: ocupada por item diferente")
                continue
            
            # Verifica se quantidade individual está nos limites da masseira
            if not (masseira.capacidade_gramas_min <= quantidade_alocada <= masseira.capacidade_gramas_max):
                logger.debug(f"❌ {masseira.nome}: quantidade {quantidade_alocada:.2f}g fora dos limites [{masseira.capacidade_gramas_min}-{masseira.capacidade_gramas_max}]g")
                continue
            
            # Verifica compatibilidade de parâmetros com ocupações existentes do mesmo item
            if not self._verificar_compatibilidade_parametros(masseira, id_item, velocidades, tipo_mistura, inicio_tentativa, fim_tentativa):
                logger.debug(f"❌ {masseira.nome}: parâmetros incompatíveis com ocupações existentes do item {id_item}")
                continue
            
            # Tenta adicionar a ocupação (validação dinâmica de capacidade interna)
            sucesso = masseira.adicionar_ocupacao(
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                id_atividade=id_atividade,
                id_item=id_item,
                quantidade_alocada=quantidade_alocada,
                velocidades=velocidades,
                tipo_mistura=tipo_mistura,
                inicio=inicio_tentativa,
                fim=fim_tentativa
            )
            
            if sucesso:
                logger.debug(f"✅ {masseira.nome}: alocação individual bem-sucedida")
                return masseira, inicio_tentativa, fim_tentativa
            else:
                logger.debug(f"❌ {masseira.nome}: falha na validação de capacidade dinâmica")
        
        return None

    def _tentar_alocacao_distribuida_otimizada(
        self, 
        inicio_tentativa: datetime, 
        fim_tentativa: datetime,
        atividade: "AtividadeModular",
        quantidade_alocada: float,
        masseiras_ordenadas: List[Masseira],
        id_ordem: int, id_pedido: int, id_atividade: int, id_item: int
    ) -> Optional[Tuple[List[Masseira], datetime, datetime]]:
        """
        NOVA IMPLEMENTAÇÃO: Tenta alocação distribuída usando algoritmos otimizados.
        Aplica verificação prévia de viabilidade e algoritmos de distribuição inteligente.
        """
        # Fase 1: Verificação de viabilidade
        viavel, motivo = self._verificar_viabilidade_quantidade(
            atividade, quantidade_alocada, id_item, inicio_tentativa, fim_tentativa
        )
        
        if not viavel:
            logger.debug(f"❌ Inviável no horário {inicio_tentativa.strftime('%H:%M')}: {motivo}")
            return None

        # Fase 2: Coleta masseiras com configurações técnicas válidas
        masseiras_com_capacidade = []
        
        for masseira in masseiras_ordenadas:
            # Verifica disponibilidade para o item específico
            if not masseira.esta_disponivel_para_item(inicio_tentativa, fim_tentativa, id_item):
                logger.debug(f"❌ {masseira.nome}: ocupada por item diferente")
                continue
            
            # Obter configurações técnicas
            velocidades = self._obter_velocidades_para_masseira(atividade, masseira)
            tipo_mistura = self._obter_tipo_mistura_para_masseira(atividade, masseira)
            
            # Verifica compatibilidade técnica com quantidade mínima
            if not masseira.verificar_disponibilidade(masseira.capacidade_gramas_min, velocidades, tipo_mistura):
                logger.debug(f"❌ {masseira.nome}: não atende requisitos técnicos mínimos")
                continue
            
            # Verifica compatibilidade de parâmetros
            if not self._verificar_compatibilidade_parametros(masseira, id_item, velocidades, tipo_mistura, inicio_tentativa, fim_tentativa):
                logger.debug(f"❌ {masseira.nome}: parâmetros incompatíveis")
                continue
            
            # Calcula capacidade disponível real para o item específico
            capacidade_disponivel = masseira.obter_capacidade_disponivel_item(
                id_item, inicio_tentativa, fim_tentativa
            )
            
            # Deve ter pelo menos capacidade mínima disponível
            if capacidade_disponivel >= masseira.capacidade_gramas_min:
                masseiras_com_capacidade.append((masseira, capacidade_disponivel, velocidades, tipo_mistura))
                logger.debug(f"🔍 {masseira.nome}: {capacidade_disponivel:.2f}g disponível para item {id_item}")

        if not masseiras_com_capacidade:
            logger.debug("❌ Nenhuma masseira com capacidade mínima disponível")
            return None

        # Fase 3: Aplica algoritmos de distribuição otimizada
        distribuicao = self._calcular_distribuicao_otima(quantidade_alocada, masseiras_com_capacidade)
        
        if not distribuicao:
            logger.debug("❌ Algoritmos de distribuição não encontraram solução viável")
            return None

        # Fase 4: Executa alocação múltipla
        sucesso = self._executar_alocacao_multipla_masseira(
            distribuicao, inicio_tentativa, fim_tentativa, 
            id_ordem, id_pedido, id_atividade, id_item
        )
        
        if sucesso:
            masseiras_alocadas = [m for m, _, _, _ in distribuicao]
            logger.debug(f"✅ Alocação múltipla otimizada: {len(masseiras_alocadas)} masseiras para item {id_item}")
            return masseiras_alocadas, inicio_tentativa, fim_tentativa
        
        return None

    def _executar_alocacao_multipla_masseira(self, distribuicao: List[Tuple[Masseira, float, List[TipoVelocidade], Optional[TipoMistura]]], 
                                           inicio: datetime, fim: datetime,
                                           id_ordem: int, id_pedido: int, id_atividade: int, id_item: int) -> bool:
        """
        Executa alocação em múltiplas masseiras conforme distribuição calculada.
        """
        # Lista para rollback em caso de falha
        alocacoes_realizadas = []
        
        try:
            for masseira, quantidade, velocidades, tipo_mistura in distribuicao:
                sucesso = masseira.adicionar_ocupacao(
                    id_ordem=id_ordem,
                    id_pedido=id_pedido,
                    id_atividade=id_atividade,
                    id_item=id_item,
                    quantidade_alocada=quantidade,
                    velocidades=velocidades,
                    tipo_mistura=tipo_mistura,
                    inicio=inicio,
                    fim=fim
                )
                
                if not sucesso:
                    # Rollback das alocações já realizadas
                    for m_rollback in alocacoes_realizadas:
                        m_rollback.liberar_por_atividade(id_ordem, id_pedido, id_atividade)
                    return False
                
                alocacoes_realizadas.append(masseira)
                logger.info(f"🔹 Alocado {quantidade:.2f}g na {masseira.nome}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na alocação múltipla: {e}")
            # Rollback em caso de erro
            for m_rollback in alocacoes_realizadas:
                m_rollback.liberar_por_atividade(id_ordem, id_pedido, id_atividade)
            return False

    # ==========================================================
    # 🎯 Alocação Principal com Backward Scheduling Otimizado
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade_alocada: float,
        **kwargs
    ) -> Tuple[bool, Optional[List[Masseira]], Optional[datetime], Optional[datetime]]:
        """
        Aloca masseiras seguindo a estratégia otimizada com verificação prévia de viabilidade:
        1. Verificação de viabilidade total usando Multiple Knapsack Problem
        2. Tenta alocação individual por FIP (se quantidade cabe em uma masseira)
        3. Tenta distribuição otimizada usando algoritmos inteligentes
        4. Usa backward scheduling minuto a minuto (busca exaustiva)
        """
        duracao = atividade.duracao
        masseiras_ordenadas = self._ordenar_por_fip(atividade)
        horario_final_tentativa = fim

        # Obter IDs da atividade de forma consistente
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)

        if quantidade_alocada <= 0:
            logger.warning(f"❌ Quantidade inválida para atividade {id_atividade}: {quantidade_alocada}")
            return False, None, None, None

        logger.info(f"🎯 Iniciando alocação otimizada atividade {id_atividade}: {quantidade_alocada:.2f}g do item {id_item}")
        logger.debug(f"📅 Janela: {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} (duração: {duracao})")

        # 🔍 DIAGNÓSTICO: Verifica capacidades disponíveis
        capacidades_individuais = [m.capacidade_gramas_max for m in masseiras_ordenadas]
        capacidade_total_sistema = sum(capacidades_individuais)
        capacidade_maxima_individual = max(capacidades_individuais)
        
        logger.debug(f"🔍 DIAGNÓSTICO: Quantidade necessária {quantidade_alocada:.2f}g")
        logger.debug(f"🔍 DIAGNÓSTICO: Capacidades individuais: {capacidades_individuais}")
        logger.debug(f"🔍 DIAGNÓSTICO: Capacidade total sistema: {capacidade_total_sistema}g")
        logger.debug(f"🔍 DIAGNÓSTICO: Capacidade máxima individual: {capacidade_maxima_individual}g")
        
        # 📋 REGRA PRINCIPAL: Primeiro verifica se capacidade total do sistema atende
        if quantidade_alocada > capacidade_total_sistema:
            logger.warning(f"❌ Quantidade {quantidade_alocada:.2f}g > capacidade total {capacidade_total_sistema}g - IMPOSSÍVEL")
            return False, None, None, None
        
        logger.info(f"✅ Capacidade total do sistema ({capacidade_total_sistema}g) atende a demanda ({quantidade_alocada:.2f}g)")
        
        if quantidade_alocada > capacidade_maxima_individual:
            logger.info(f"📊 Quantidade {quantidade_alocada:.2f}g > capacidade individual {capacidade_maxima_individual}g - tentará individual primeiro, depois distribuição")

        # ==========================================================
        # 🔄 BACKWARD SCHEDULING OTIMIZADO - MINUTO A MINUTO (BUSCA EXAUSTIVA)
        # ==========================================================
        tentativas = 0
        while horario_final_tentativa - duracao >= inicio:
            tentativas += 1
            horario_inicio_tentativa = horario_final_tentativa - duracao
            
            logger.debug(f"⏰ Tentativa {tentativas}: {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}")

            # 1️⃣ PRIMEIRA ESTRATÉGIA: Tenta alocação integral em uma masseira
            # 🎯 SEMPRE tenta individual primeiro (independente da capacidade individual)
            logger.debug(f"🔍 Tentando alocação individual - quantidade {quantidade_alocada:.2f}g")
            sucesso_individual = self._tentar_alocacao_individual(
                horario_inicio_tentativa, horario_final_tentativa,
                atividade, quantidade_alocada, masseiras_ordenadas,
                id_ordem, id_pedido, id_atividade, id_item
            )
            
            if sucesso_individual:
                masseira_usada, inicio_real, fim_real = sucesso_individual
                atividade.equipamento_alocado = masseira_usada
                atividade.equipamentos_selecionados = [masseira_usada]
                atividade.alocada = True
                
                minutos_retrocedidos = int((fim - fim_real).total_seconds() / 60)
                logger.info(
                    f"✅ Atividade {id_atividade} (Item {id_item}) alocada INTEIRAMENTE na {masseira_usada.nome} "
                    f"({quantidade_alocada:.2f}g) de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')} "
                    f"(retrocedeu {minutos_retrocedidos} minutos)"
                )
                return True, [masseira_usada], inicio_real, fim_real

            # 2️⃣ SEGUNDA ESTRATÉGIA: Tenta alocação distribuída otimizada entre múltiplas masseiras
            logger.debug(f"🔍 Tentando alocação distribuída para {quantidade_alocada:.2f}g")
            sucesso_distribuido = self._tentar_alocacao_distribuida_otimizada(
                horario_inicio_tentativa, horario_final_tentativa,
                atividade, quantidade_alocada, masseiras_ordenadas,
                id_ordem, id_pedido, id_atividade, id_item
            )
            
            if sucesso_distribuido:
                masseiras_usadas, inicio_real, fim_real = sucesso_distribuido
                atividade.equipamento_alocado = None  # Múltiplas masseiras
                atividade.equipamentos_selecionados = masseiras_usadas
                atividade.alocada = True
                
                # Adiciona informação de alocação múltipla se disponível
                if hasattr(atividade, 'alocacao_multipla'):
                    atividade.alocacao_multipla = True
                
                minutos_retrocedidos = int((fim - fim_real).total_seconds() / 60)
                logger.info(
                    f"🧩 Atividade {id_atividade} (Item {id_item}) DIVIDIDA OTIMIZADA entre "
                    f"{', '.join(m.nome for m in masseiras_usadas)} "
                    f"({quantidade_alocada:.2f}g total) de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')} "
                    f"(retrocedeu {minutos_retrocedidos} minutos)"
                )
                return True, masseiras_usadas, inicio_real, fim_real

            # 3️⃣ Falhou nesta janela: RETROCEDE 1 MINUTO (BUSCA EXAUSTIVA)
            horario_final_tentativa -= timedelta(minutes=1)
            
            # Log ocasional para evitar spam
            if tentativas % 10 == 0:
                logger.debug(f"⏪ Tentativa {tentativas}: retrocedendo para {horario_final_tentativa.strftime('%H:%M')}")

        # Não conseguiu alocar em nenhuma janela válida
        minutos_total_retrocedidos = int((fim - (inicio + duracao)).total_seconds() / 60)
        logger.warning(
            f"❌ Atividade {id_atividade} (Item {id_item}) não pôde ser alocada após {tentativas} tentativas "
            f"dentro da janela entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}. "
            f"Quantidade necessária: {quantidade_alocada:.2f}g "
            f"(retrocedeu até o limite de {minutos_total_retrocedidos} minutos)"
        )
        return False, None, None, None

    # ==========================================================
    # 🔓 Liberação (mantidas do original)
    # ==========================================================
    def liberar_por_atividade(self, atividade: "AtividadeModular") -> None:
        """Libera ocupações específicas por atividade em todas as masseiras."""
        id_ordem, id_pedido, id_atividade, _ = self._obter_ids_atividade(atividade)
        for masseira in self.masseiras:
            masseira.liberar_por_atividade(
                id_ordem=id_ordem, 
                id_pedido=id_pedido, 
                id_atividade=id_atividade
            )

    def liberar_por_pedido(self, atividade: "AtividadeModular") -> None:
        """Libera ocupações específicas por pedido em todas as masseiras."""
        id_ordem, id_pedido, _, _ = self._obter_ids_atividade(atividade)
        for masseira in self.masseiras:
            masseira.liberar_por_pedido(
                id_ordem=id_ordem, 
                id_pedido=id_pedido
            )

    def liberar_por_ordem(self, atividade: "AtividadeModular") -> None:
        """Libera ocupações específicas por ordem em todas as masseiras."""
        id_ordem, _, _, _ = self._obter_ids_atividade(atividade)
        for masseira in self.masseiras:
            masseira.liberar_por_ordem(id_ordem)

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime) -> None:
        """Libera ocupações que já finalizaram em todas as masseiras."""
        for masseira in self.masseiras:
            masseira.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self) -> None:
        """Libera todas as ocupações de todas as masseiras."""
        for masseira in self.masseiras:
            masseira.liberar_todas_ocupacoes()

    # ==========================================================
    # 📅 Agenda e Relatórios (mantidos do original)
    # ==========================================================
    def mostrar_agenda(self) -> None:
        """Mostra agenda de todas as masseiras."""
        logger.info("==============================================")
        logger.info("📅 Agenda das Masseiras")
        logger.info("==============================================")
        for masseira in self.masseiras:
            masseira.mostrar_agenda()

    def obter_status_masseiras(self) -> dict:
        """Retorna o status atual de todas as masseiras."""
        status = {}
        for masseira in self.masseiras:
            ocupacoes_ativas = [
                {
                    'id_ordem': oc[0],
                    'id_pedido': oc[1],
                    'id_atividade': oc[2],
                    'id_item': oc[3],
                    'quantidade': oc[4],
                    'velocidades': [v.name for v in oc[5]],
                    'tipo_mistura': oc[6].name if oc[6] else None,
                    'inicio': oc[7].strftime('%H:%M'),
                    'fim': oc[8].strftime('%H:%M')
                }
                for oc in masseira.ocupacoes
            ]
            
            status[masseira.nome] = {
                'capacidade_minima': masseira.capacidade_gramas_min,
                'capacidade_maxima': masseira.capacidade_gramas_max,
                'total_ocupacoes': len(masseira.ocupacoes),
                'ocupacoes_ativas': ocupacoes_ativas
            }
        
        return status

    def verificar_disponibilidade(
        self,
        inicio: datetime,
        fim: datetime,
        id_item: Optional[int] = None,
        quantidade: Optional[float] = None
    ) -> List[Masseira]:
        """
        Verifica quais masseiras estão disponíveis no período para um item específico.
        """
        disponiveis = []
        
        for masseira in self.masseiras:
            if id_item is not None:
                if masseira.esta_disponivel_para_item(inicio, fim, id_item):
                    if quantidade is None:
                        disponiveis.append(masseira)
                    else:
                        # Verifica se pode adicionar a quantidade especificada
                        if masseira.validar_nova_ocupacao_item(id_item, quantidade, inicio, fim):
                            disponiveis.append(masseira)
            else:
                # Comportamento original para compatibilidade
                if masseira.esta_disponivel(inicio, fim):
                    if quantidade is None or masseira.validar_capacidade_individual(quantidade):
                        disponiveis.append(masseira)
        
        return disponiveis

    def obter_utilizacao_por_item(self, id_item: int) -> dict:
        """
        📊 Retorna informações de utilização de um item específico em todas as masseiras.
        """
        utilizacao = {}
        
        for masseira in self.masseiras:
            ocupacoes_item = [
                oc for oc in masseira.ocupacoes if oc[3] == id_item
            ]
            
            if ocupacoes_item:
                quantidade_total = sum(oc[4] for oc in ocupacoes_item)
                periodo_inicio = min(oc[7] for oc in ocupacoes_item)
                periodo_fim = max(oc[8] for oc in ocupacoes_item)
                
                utilizacao[masseira.nome] = {
                    'quantidade_total': quantidade_total,
                    'num_ocupacoes': len(ocupacoes_item),
                    'periodo_inicio': periodo_inicio.strftime('%H:%M'),
                    'periodo_fim': periodo_fim.strftime('%H:%M'),
                    'ocupacoes': [
                        {
                            'id_ordem': oc[0],
                            'id_pedido': oc[1],
                            'quantidade': oc[4],
                            'inicio': oc[7].strftime('%H:%M'),
                            'fim': oc[8].strftime('%H:%M')
                        }
                        for oc in ocupacoes_item
                    ]
                }
        
        return utilizacao

    def calcular_pico_utilizacao_item(self, id_item: int) -> dict:
        """
        📈 Calcula o pico de utilização de um item específico em cada masseira.
        """
        picos = {}
        
        for masseira in self.masseiras:
            ocupacoes_item = [oc for oc in masseira.ocupacoes if oc[3] == id_item]
            
            if not ocupacoes_item:
                continue
                
            # Usa método da própria masseira para calcular pico
            periodo_inicio = min(oc[7] for oc in ocupacoes_item)
            periodo_fim = max(oc[8] for oc in ocupacoes_item)
            
            pico_quantidade = masseira.obter_quantidade_maxima_item_periodo(
                id_item, periodo_inicio, periodo_fim
            )
            
            if pico_quantidade > 0:
                picos[masseira.nome] = {
                    'pico_quantidade': pico_quantidade,
                    'periodo_analise': f"{periodo_inicio.strftime('%H:%M')} - {periodo_fim.strftime('%H:%M')}",
                    'percentual_capacidade': (pico_quantidade / masseira.capacidade_gramas_max) * 100
                }
        
        return picos

    # ==========================================================
    # 🆕 Métodos Adicionais para Compatibilidade e Análise
    # ==========================================================
    def obter_detalhes_alocacao_atividade(self, atividade: "AtividadeModular") -> dict:
        """
        🔍 Retorna detalhes completos da alocação de uma atividade,
        incluindo informações de múltiplas masseiras se aplicável.
        """
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)
        
        detalhes = {
            'id_atividade': id_atividade,
            'id_item': id_item,
            'alocacao_multipla': len(atividade.equipamentos_selecionados) > 1 if hasattr(atividade, 'equipamentos_selecionados') else False,
            'masseiras_utilizadas': [],
            'quantidade_total': 0.0
        }
        
        # Coleta informações de todas as masseiras que processam esta atividade
        for masseira in self.masseiras:
            ocupacoes_atividade = [
                oc for oc in masseira.ocupacoes 
                if oc[0] == id_ordem and oc[1] == id_pedido and oc[2] == id_atividade
            ]
            
            if ocupacoes_atividade:
                quantidade_masseira = sum(oc[4] for oc in ocupacoes_atividade)
                detalhes['masseiras_utilizadas'].append({
                    'nome': masseira.nome,
                    'quantidade': quantidade_masseira,
                    'ocupacoes': len(ocupacoes_atividade)
                })
                detalhes['quantidade_total'] += quantidade_masseira
        
        return detalhes

    def listar_alocacoes_multiplas(self) -> List[dict]:
        """
        📊 Lista todas as atividades que utilizaram múltiplas masseiras.
        """
        alocacoes_multiplas = []
        atividades_processadas = set()
        
        for masseira in self.masseiras:
            for ocupacao in masseira.ocupacoes:
                id_ordem, id_pedido, id_atividade = ocupacao[0], ocupacao[1], ocupacao[2]
                chave_atividade = (id_ordem, id_pedido, id_atividade)
                
                if chave_atividade not in atividades_processadas:
                    # Conta quantas masseiras diferentes processam esta atividade
                    masseiras_atividade = []
                    quantidade_total = 0.0
                    
                    for m in self.masseiras:
                        ocupacoes_atividade = [
                            oc for oc in m.ocupacoes
                            if oc[0] == id_ordem and oc[1] == id_pedido and oc[2] == id_atividade
                        ]
                        if ocupacoes_atividade:
                            qtd_masseira = sum(oc[4] for oc in ocupacoes_atividade)
                            masseiras_atividade.append({
                                'nome': m.nome,
                                'quantidade': qtd_masseira
                            })
                            quantidade_total += qtd_masseira
                    
                    if len(masseiras_atividade) > 1:
                        alocacoes_multiplas.append({
                            'id_ordem': id_ordem,
                            'id_pedido': id_pedido,
                            'id_atividade': id_atividade,
                            'id_item': ocupacao[3],
                            'quantidade_total': quantidade_total,
                            'num_masseiras': len(masseiras_atividade),
                            'masseiras': masseiras_atividade,
                            'inicio': ocupacao[7].strftime('%H:%M [%d/%m]'),
                            'fim': ocupacao[8].strftime('%H:%M [%d/%m]')
                        })
                    
                    atividades_processadas.add(chave_atividade)
        
        return alocacoes_multiplas