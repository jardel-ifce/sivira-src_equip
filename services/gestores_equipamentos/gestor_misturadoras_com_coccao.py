import unicodedata
import math
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, TYPE_CHECKING, Union
from models.equipamentos.hot_mix import HotMix
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular
from enums.equipamentos.tipo_velocidade import TipoVelocidade
from enums.equipamentos.tipo_chama import TipoChama
from enums.equipamentos.tipo_pressao_chama import TipoPressaoChama
from utils.logs.logger_factory import setup_logger

logger = setup_logger("GestorMisturadorasComCoccao")


class GestorMisturadorasComCoccao:
    """
    🍳 Gestor otimizado para controle de misturadoras com cocção (HotMix).
    
    Baseado em:
    - Multiple Knapsack Problem para distribuição ótima
    - First Fit Decreasing (FFD) com restrições de capacidade mínima
    - Binary Space Partitioning para divisão eficiente
    - Backward scheduling com janelas de tempo simultâneas
    
    Funcionalidades:
    - Verificação prévia de viabilidade total
    - Distribuição otimizada respeitando capacidades mín/máx
    - Algoritmo de redistribuição com balanceamento de carga
    - JANELAS SIMULTÂNEAS: Mesmo id_item só pode ocupar períodos idênticos ou distintos
    - Priorização por FIP com backward scheduling
    - Otimização inteligente: evita tentativas individuais quando distribuição é obrigatória
    """

    def __init__(self, hotmixes: List[HotMix]):
        self.hotmixes = hotmixes
    
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
        
        for hotmix in self.hotmixes:
            # Capacidade máxima da HotMix
            cap_max = hotmix.capacidade_gramas_max
            capacidade_maxima_teorica += cap_max
            
            # Verifica se pode receber o item no período (janelas simultâneas)
            if hotmix.esta_disponivel_para_item_janelas_simultaneas(inicio, fim, id_item):
                # Calcula capacidade disponível considerando ocupações simultâneas do mesmo item
                capacidade_disponivel = hotmix.obter_capacidade_disponivel_item_simultaneo(id_item, inicio, fim)
                capacidade_disponivel_total += max(0, capacidade_disponivel)
        
        return capacidade_disponivel_total, capacidade_maxima_teorica

    def _verificar_viabilidade_quantidade(self, atividade: "AtividadeModular", quantidade_total: float,
                                        id_item: int, inicio: datetime, fim: datetime) -> Tuple[bool, str]:
        """
        📚 Multiple Knapsack Problem (MKP): Problema clássico de otimização combinatória onde
        múltiplos "recipientes" (knapsacks) têm capacidades limitadas e devem acomodar itens
        com restrições. Usado aqui para verificar se o conjunto de HotMixes pode teoricamente 
        comportar a demanda antes de tentar algoritmos de alocação mais custosos computacionalmente.
        
        Verifica se é teoricamente possível alocar a quantidade solicitada com janelas simultâneas.
        """
        cap_disponivel, cap_teorica = self._calcular_capacidade_total_sistema(
            atividade, id_item, inicio, fim
        )
        
        if quantidade_total > cap_teorica:
            return False, f"Quantidade {quantidade_total}g excede capacidade máxima teórica do sistema ({cap_teorica}g)"
        
        if quantidade_total > cap_disponivel:
            return False, f"Quantidade {quantidade_total}g excede capacidade disponível ({cap_disponivel}g) no período"
        
        # Verifica se existem HotMixes disponíveis para janelas simultâneas
        hotmixes_disponiveis = [
            h for h in self.hotmixes 
            if h.esta_disponivel_para_item_janelas_simultaneas(inicio, fim, id_item)
        ]
        
        if not hotmixes_disponiveis:
            return False, "Nenhuma HotMix disponível para o item no período (considerando janelas simultâneas)"
        
        # Verifica viabilidade com capacidades mínimas
        capacidade_minima_total = sum(h.capacidade_gramas_min for h in hotmixes_disponiveis)
        if quantidade_total < min(h.capacidade_gramas_min for h in hotmixes_disponiveis):
            if len(hotmixes_disponiveis) == 1:
                return True, "Viável com uma HotMix"
        elif quantidade_total >= capacidade_minima_total:
            return True, "Viável com múltiplas HotMixes"
        else:
            return False, f"Quantidade {quantidade_total}g insuficiente para capacidades mínimas ({capacidade_minima_total}g)"
        
        return True, "Quantidade viável"

    # ==========================================================
    # 🧮 Algoritmos de Distribuição Otimizada
    # ==========================================================
    def _algoritmo_distribuicao_balanceada(self, quantidade_total: float, 
                                          hotmixes_disponiveis: List[Tuple[HotMix, float, TipoVelocidade, TipoChama, List[TipoPressaoChama]]]) -> List[Tuple[HotMix, float, TipoVelocidade, TipoChama, List[TipoPressaoChama]]]:
        """
        Algoritmo de distribuição baseado em Binary Space Partitioning adaptado.
        
        📚 Binary Space Partitioning: Técnica que divide recursivamente o espaço de soluções,
        originalmente usada em computação gráfica. Aqui adaptada para dividir a quantidade total
        proporcionalmente entre HotMixes, considerando suas capacidades disponíveis.
        ⚡ OTIMIZADO PARA BACKWARD SCHEDULING: Evita operações lentas que conflitam com tentativas rápidas.
        
        Estratégia:
        1. Ordena HotMixes por capacidade disponível (maior primeiro)
        2. Aplica divisão proporcional otimizada
        3. Ajuste único e direto (sem iterações)
        """
        if not hotmixes_disponiveis:
            return []
        
        # Ordena por capacidade disponível (maior primeiro)
        hotmixes_ordenadas = sorted(hotmixes_disponiveis, key=lambda x: x[1], reverse=True)
        
        # Capacidade total disponível
        capacidade_total_disponivel = sum(cap for _, cap, _, _, _ in hotmixes_ordenadas)
        
        if capacidade_total_disponivel < quantidade_total:
            return []
        
        # ⚡ DISTRIBUIÇÃO PROPORCIONAL DIRETA - Sem ajustes iterativos posteriores
        distribuicao = []
        quantidade_restante = quantidade_total
        
        for i, (hotmix, cap_disponivel, velocidade, chama, pressoes) in enumerate(hotmixes_ordenadas):
            if quantidade_restante <= 0:
                break
                
            if i == len(hotmixes_ordenadas) - 1:
                # Última HotMix: recebe todo o restante (se couber)
                quantidade_hotmix = min(quantidade_restante, cap_disponivel)
            else:
                # Distribuição proporcional direta
                proporcao = cap_disponivel / capacidade_total_disponivel
                quantidade_proporcional = quantidade_total * proporcao
                
                # ⚡ AJUSTE DIRETO: Garante limites sem iterações
                quantidade_hotmix = max(
                    hotmix.capacidade_gramas_min,
                    min(quantidade_proporcional, cap_disponivel, quantidade_restante)
                )
            
            # Só adiciona se atende capacidade mínima
            if quantidade_hotmix >= hotmix.capacidade_gramas_min:
                distribuicao.append((hotmix, quantidade_hotmix, velocidade, chama, pressoes))
                quantidade_restante -= quantidade_hotmix
        
        # ⚡ VERIFICAÇÃO FINAL RÁPIDA: Se sobrou quantidade significativa, falha rápido
        if quantidade_restante > 1.0:  # Tolerância de 1g
            return []  # Falha rápida para backward scheduling tentar próxima janela
        
        return distribuicao

    def _redistribuir_excedentes(self, distribuicao: List[Tuple[HotMix, float, TipoVelocidade, TipoChama, List[TipoPressaoChama]]], 
                                quantidade_target: float) -> List[Tuple[HotMix, float, TipoVelocidade, TipoChama, List[TipoPressaoChama]]]:
        """
        📚 Fast Load Balancing: Versão otimizada para backward scheduling que evita iterações longas.
        Aplica ajuste direto em uma única passada para ser compatível com tentativas rápidas
        de janelas temporais. Prioriza velocidade sobre precisão absoluta na distribuição.
        
        Redistribui quantidades para atingir o target exato respeitando limites - OTIMIZADO PARA SPEED.
        """
        quantidade_atual = sum(qtd for _, qtd, _, _, _ in distribuicao)
        diferenca = quantidade_target - quantidade_atual
        
        # Tolerância mais flexível para evitar iterações desnecessárias
        if abs(diferenca) < 1.0:  # Tolerância de 1g para speed
            return distribuicao
        
        # 🚀 AJUSTE ÚNICO E DIRETO - Sem iterações que conflitem com backward scheduling
        if diferenca > 0:
            # Precisa adicionar quantidade - distribui o excesso proporcionalmente
            hotmixes_com_margem = [
                (i, hotmix.capacidade_gramas_max - qtd) 
                for i, (hotmix, qtd, _, _, _) in enumerate(distribuicao)
                if hotmix.capacidade_gramas_max - qtd > 0
            ]
            
            if hotmixes_com_margem:
                margem_total = sum(margem for _, margem in hotmixes_com_margem)
                
                for i, margem_disponivel in hotmixes_com_margem:
                    if diferenca <= 0:
                        break
                    
                    hotmix, qtd_atual, vel, chama, press = distribuicao[i]
                    proporcao = margem_disponivel / margem_total
                    adicionar = min(diferenca, diferenca * proporcao)
                    adicionar = min(adicionar, margem_disponivel)  # Não excede capacidade
                    
                    distribuicao[i] = (hotmix, qtd_atual + adicionar, vel, chama, press)
                    diferenca -= adicionar
        
        elif diferenca < 0:
            # Precisa remover quantidade - remove proporcionalmente das que têm margem
            diferenca = abs(diferenca)
            hotmixes_com_margem = [
                (i, qtd - hotmix.capacidade_gramas_min) 
                for i, (hotmix, qtd, _, _, _) in enumerate(distribuicao)
                if qtd - hotmix.capacidade_gramas_min > 0
            ]
            
            if hotmixes_com_margem:
                margem_total = sum(margem for _, margem in hotmixes_com_margem)
                
                for i, margem_removivel in hotmixes_com_margem:
                    if diferenca <= 0:
                        break
                    
                    hotmix, qtd_atual, vel, chama, press = distribuicao[i]
                    proporcao = margem_removivel / margem_total
                    remover = min(diferenca, diferenca * proporcao)
                    remover = min(remover, margem_removivel)  # Não fica abaixo do mínimo
                    
                    distribuicao[i] = (hotmix, qtd_atual - remover, vel, chama, press)
                    diferenca -= remover
        
        # Remove HotMixes com quantidade abaixo do mínimo (ajuste final rápido)
        distribuicao_final = [
            (hotmix, qtd, vel, chama, press) for hotmix, qtd, vel, chama, press in distribuicao
            if qtd >= hotmix.capacidade_gramas_min
        ]
        
        return distribuicao_final

    def _algoritmo_first_fit_decreasing(self, quantidade_total: float,
                                      hotmixes_disponiveis: List[Tuple[HotMix, float, TipoVelocidade, TipoChama, List[TipoPressaoChama]]]) -> List[Tuple[HotMix, float, TipoVelocidade, TipoChama, List[TipoPressaoChama]]]:
        """
        📚 First Fit Decreasing (FFD): Algoritmo clássico de Bin Packing que ordena itens
        por tamanho decrescente e aloca cada item no primeiro recipiente que couber.
        Garante aproximação de 11/9 do ótimo e é amplamente usado em problemas de otimização.
        Adaptado aqui para respeitar capacidades mínimas das HotMixes, evitando
        distribuições que violem restrições operacionais.
        
        Implementação do algoritmo First Fit Decreasing adaptado para capacidades mínimas.
        """
        # Ordena HotMixes por capacidade disponível (maior primeiro)
        hotmixes_ordenadas = sorted(hotmixes_disponiveis, key=lambda x: x[1], reverse=True)
        
        distribuicao = []
        quantidade_restante = quantidade_total
        
        for hotmix, cap_disponivel, velocidade, chama, pressoes in hotmixes_ordenadas:
            if quantidade_restante <= 0:
                break
            
            # Calcula quanto alocar nesta HotMix
            if quantidade_restante >= hotmix.capacidade_gramas_min:
                quantidade_alocar = min(quantidade_restante, cap_disponivel)
                
                # Garante que não fica quantidade insuficiente para próximas HotMixes
                hotmixes_restantes = [h for h, _, _, _, _ in hotmixes_ordenadas 
                                    if h != hotmix and (quantidade_restante - quantidade_alocar) > 0]
                
                if hotmixes_restantes:
                    cap_min_restantes = min(h.capacidade_gramas_min for h in hotmixes_restantes)
                    if quantidade_restante - quantidade_alocar < cap_min_restantes and quantidade_restante - quantidade_alocar > 0:
                        # Ajusta para deixar quantidade suficiente
                        quantidade_alocar = quantidade_restante - cap_min_restantes
                
                if quantidade_alocar >= hotmix.capacidade_gramas_min:
                    distribuicao.append((hotmix, quantidade_alocar, velocidade, chama, pressoes))
                    quantidade_restante -= quantidade_alocar
        
        return distribuicao if quantidade_restante <= 0.1 else []

    def _calcular_distribuicao_otima(self, quantidade_total: float, 
                                   hotmixes_disponiveis: List[Tuple[HotMix, float, TipoVelocidade, TipoChama, List[TipoPressaoChama]]]) -> List[Tuple[HotMix, float, TipoVelocidade, TipoChama, List[TipoPressaoChama]]]:
        """
        ⚡ OTIMIZADO PARA BACKWARD SCHEDULING: Calcula distribuição ótima com limite de tempo.
        Testa algoritmos rapidamente e retorna a primeira solução viável para não atrasar
        o backward scheduling que precisa testar muitas janelas temporais.
        """
        # 🚀 ESTRATÉGIA 1: Tenta distribuição balanceada (mais rápida)
        dist_balanceada = self._algoritmo_distribuicao_balanceada(quantidade_total, hotmixes_disponiveis)
        
        if dist_balanceada and sum(qtd for _, qtd, _, _, _ in dist_balanceada) >= quantidade_total * 0.98:
            logger.debug(f"📊 Distribuição balanceada aceita com {len(dist_balanceada)} HotMixes")
            return dist_balanceada
        
        # 🚀 ESTRATÉGIA 2: Se balanceada falhou, tenta FFD
        dist_ffd = self._algoritmo_first_fit_decreasing(quantidade_total, hotmixes_disponiveis)
        
        if dist_ffd and sum(qtd for _, qtd, _, _, _ in dist_ffd) >= quantidade_total * 0.98:
            logger.debug(f"📊 Distribuição FFD aceita com {len(dist_ffd)} HotMixes")
            return dist_ffd
        
        # ❌ Nenhuma estratégia funcionou - falha rápida para backward scheduling continuar
        logger.debug("📊 Nenhuma distribuição viável encontrada - prosseguindo backward scheduling")
        return []

    def _calcular_balanceamento(self, distribuicao: List[Tuple[HotMix, float, TipoVelocidade, TipoChama, List[TipoPressaoChama]]]) -> float:
        """
        Calcula score de balanceamento da distribuição (maior = mais balanceado).
        """
        if len(distribuicao) <= 1:
            return 1.0
        
        quantidades = [qtd for _, qtd, _, _, _ in distribuicao]
        media = sum(quantidades) / len(quantidades)
        variancia = sum((qtd - media) ** 2 for qtd in quantidades) / len(quantidades)
        
        # Score inversamente proporcional à variância
        return 1.0 / (1.0 + variancia / media**2) if media > 0 else 0.0

    # ==========================================================
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
    # ==========================================================  
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[HotMix]:
        """Ordena HotMixes por fator de importância de prioridade."""
        ordenadas = sorted(
            self.hotmixes,
            key=lambda m: atividade.fips_equipamentos.get(m, 999)
        )
        return ordenadas
    
    # ==========================================================
    # 🔍 Leitura dos parâmetros via JSON
    # ==========================================================
    @staticmethod
    def _normalizar_nome(nome: str) -> str:
        """Normaliza nome para busca no JSON de configurações."""
        return unicodedata.normalize("NFKD", nome.lower()).encode("ASCII", "ignore").decode().replace(" ", "_")

    def _obter_ids_atividade(self, atividade: "AtividadeModular") -> Tuple[int, int, int, int]:
        """
        Extrai os IDs da atividade de forma consistente.
        Retorna: (id_ordem, id_pedido, id_atividade, id_item)
        """
        id_ordem = getattr(atividade, 'id_ordem', None) or getattr(atividade, 'ordem_id', 0)
        id_pedido = getattr(atividade, 'id_pedido', None) or getattr(atividade, 'pedido_id', 0)
        id_atividade = getattr(atividade, 'id_atividade', 0)
        # id_item é o produto/subproduto que está sendo produzido
        id_item = getattr(atividade, 'id_produto', 0)
        
        return id_ordem, id_pedido, id_atividade, id_item

    def _obter_velocidade(self, atividade: "AtividadeModular", hotmix: HotMix) -> Optional[TipoVelocidade]:
        """Obtém a velocidade necessária para a atividade."""
        chave = self._normalizar_nome(hotmix.nome)
        config = getattr(atividade, "configuracoes_equipamentos", {}).get(chave)
        valor = config.get("velocidade") if config else None
        try:
            return TipoVelocidade[valor] if valor else None
        except Exception:
            return None

    def _obter_chama(self, atividade: "AtividadeModular", hotmix: HotMix) -> Optional[TipoChama]:
        """Obtém o tipo de chama necessário para a atividade."""
        chave = self._normalizar_nome(hotmix.nome)
        config = getattr(atividade, "configuracoes_equipamentos", {}).get(chave)
        valor = config.get("tipo_chama") if config else None
        try:
            return TipoChama[valor] if valor else None
        except Exception:
            return None

    def _obter_pressoes(self, atividade: "AtividadeModular", hotmix: HotMix) -> List[TipoPressaoChama]:
        """Obtém as pressões de chama necessárias para a atividade."""
        chave = self._normalizar_nome(hotmix.nome)
        config = getattr(atividade, "configuracoes_equipamentos", {}).get(chave)
        valores = config.get("pressao_chama") if config else []
        pressoes = []
        for p in valores:
            try:
                pressoes.append(TipoPressaoChama[p])
            except Exception:
                continue
        return pressoes

    def _verificar_compatibilidade_parametros(self, hotmix: HotMix, id_item: int, velocidade: TipoVelocidade, chama: TipoChama, pressoes: List[TipoPressaoChama], inicio: datetime, fim: datetime) -> bool:
        """
        Verifica se os parâmetros são compatíveis com ocupações existentes do mesmo produto.
        🎯 REGRA DE SOBREPOSIÇÃO: Permite apenas simultaneidade exata ou períodos distintos.
        """
        
        for ocupacao in hotmix.obter_ocupacoes_item_periodo(id_item, inicio, fim):
            # ocupacao = (id_ordem, id_pedido, id_atividade, id_item, quantidade, velocidade, chama, pressoes, inicio, fim)
            inicio_existente = ocupacao[8]
            fim_existente = ocupacao[9]
            vel_existente = ocupacao[5]
            chama_existente = ocupacao[6]
            press_existentes = ocupacao[7]
            
            # 🎯 REGRA DE JANELA TEMPORAL: Só permite simultaneidade exata ou períodos distintos
            simultaneidade_exata = (inicio == inicio_existente and fim == fim_existente)
            periodos_distintos = (fim <= inicio_existente or inicio >= fim_existente)
            
            if not (simultaneidade_exata or periodos_distintos):
                logger.debug(f"❌ Sobreposição temporal inválida: período {inicio.strftime('%H:%M')}-{fim.strftime('%H:%M')} conflita com ocupação existente {inicio_existente.strftime('%H:%M')}-{fim_existente.strftime('%H:%M')}")
                return False
            
            # Se há simultaneidade exata, verifica compatibilidade de parâmetros
            if simultaneidade_exata:
                # Verificar se velocidade é compatível
                if vel_existente != velocidade:
                    logger.debug(f"❌ Velocidade incompatível: existente={vel_existente.name}, nova={velocidade.name}")
                    return False
                
                # Verificar se chama é compatível
                if chama_existente != chama:
                    logger.debug(f"❌ Chama incompatível: existente={chama_existente.name}, nova={chama.name}")
                    return False
                
                # Verificar se pressões são compatíveis
                if set(press_existentes) != set(pressoes):
                    logger.debug(f"❌ Pressões incompatíveis: existentes={[p.name for p in press_existentes]}, novas={[p.name for p in pressoes]}")
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
        quantidade_gramas: int,
        hotmixes_ordenados: List[HotMix],
        id_ordem: int, id_pedido: int, id_atividade: int, id_item: int
    ) -> Optional[Tuple[HotMix, datetime, datetime]]:
        """
        Tenta alocar toda a quantidade em uma única HotMix.
        🎯 JANELAS SIMULTÂNEAS: Permite sobreposição do mesmo id_item apenas com janelas idênticas.
        """
        for hotmix in hotmixes_ordenados:
            # Obter configurações técnicas
            velocidade = self._obter_velocidade(atividade, hotmix)
            chama = self._obter_chama(atividade, hotmix)
            pressoes = self._obter_pressoes(atividade, hotmix)
            
            if velocidade is None or chama is None or not pressoes:
                logger.debug(f"❌ {hotmix.nome}: configurações incompletas")
                continue
            
            # Verifica se pode alocar considerando janelas simultâneas
            if not hotmix.esta_disponivel_para_item_janelas_simultaneas(inicio_tentativa, fim_tentativa, id_item):
                logger.debug(f"❌ {hotmix.nome}: ocupada por item diferente ou janela temporal conflitante")
                continue
            
            # Verifica se quantidade individual está nos limites da HotMix
            if not hotmix.validar_capacidade(quantidade_gramas):
                logger.debug(f"❌ {hotmix.nome}: quantidade {quantidade_gramas}g fora dos limites")
                continue
            
            # Verifica compatibilidade de parâmetros com ocupações existentes do mesmo item
            if not self._verificar_compatibilidade_parametros(hotmix, id_item, velocidade, chama, pressoes, inicio_tentativa, fim_tentativa):
                logger.debug(f"❌ {hotmix.nome}: parâmetros incompatíveis com ocupações existentes do item {id_item}")
                continue
            
            # Tenta adicionar a ocupação (validação dinâmica de capacidade interna com janelas simultâneas)
            sucesso = hotmix.ocupar_janelas_simultaneas(
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                id_atividade=id_atividade,
                id_item=id_item,
                quantidade=quantidade_gramas,
                velocidade=velocidade,
                chama=chama,
                pressao_chamas=pressoes,
                inicio=inicio_tentativa,
                fim=fim_tentativa
            )
            
            if sucesso:
                logger.debug(f"✅ {hotmix.nome}: alocação individual bem-sucedida para item {id_item} (janelas simultâneas)")
                return hotmix, inicio_tentativa, fim_tentativa
            else:
                logger.debug(f"❌ {hotmix.nome}: falha na validação de capacidade dinâmica com janelas simultâneas")
        
        return None

    def _tentar_alocacao_distribuida_otimizada(
        self, 
        inicio_tentativa: datetime, 
        fim_tentativa: datetime,
        atividade: "AtividadeModular",
        quantidade_gramas: int,
        hotmixes_ordenados: List[HotMix],
        id_ordem: int, id_pedido: int, id_atividade: int, id_item: int
    ) -> Optional[Tuple[List[HotMix], datetime, datetime]]:
        """
        NOVA IMPLEMENTAÇÃO: Tenta alocação distribuída usando algoritmos otimizados.
        🎯 JANELAS SIMULTÂNEAS: Aplica verificação de janelas simultâneas para múltiplas HotMixes.
        """
        # Fase 1: Verificação de viabilidade com janelas simultâneas
        viavel, motivo = self._verificar_viabilidade_quantidade(
            atividade, float(quantidade_gramas), id_item, inicio_tentativa, fim_tentativa
        )
        
        if not viavel:
            logger.debug(f"❌ Inviável no horário {inicio_tentativa.strftime('%H:%M')}: {motivo}")
            return None

        # Fase 2: Coleta HotMixes com configurações técnicas válidas e janelas simultâneas
        hotmixes_com_capacidade = []
        
        for hotmix in hotmixes_ordenados:
            # Verifica disponibilidade para o item específico com janelas simultâneas
            if not hotmix.esta_disponivel_para_item_janelas_simultaneas(inicio_tentativa, fim_tentativa, id_item):
                logger.debug(f"❌ {hotmix.nome}: ocupada por item diferente ou janela temporal conflitante")
                continue
            
            # Obter configurações técnicas
            velocidade = self._obter_velocidade(atividade, hotmix)
            chama = self._obter_chama(atividade, hotmix)
            pressoes = self._obter_pressoes(atividade, hotmix)
            
            if velocidade is None or chama is None or not pressoes:
                logger.debug(f"❌ {hotmix.nome}: configurações incompletas")
                continue
            
            # Verifica compatibilidade de parâmetros
            if not self._verificar_compatibilidade_parametros(hotmix, id_item, velocidade, chama, pressoes, inicio_tentativa, fim_tentativa):
                logger.debug(f"❌ {hotmix.nome}: parâmetros incompatíveis")
                continue
            
            # Calcula capacidade disponível real para o item específico com janelas simultâneas
            capacidade_disponivel = hotmix.obter_capacidade_disponivel_item_simultaneo(
                id_item, inicio_tentativa, fim_tentativa
            )
            
            # Deve ter pelo menos capacidade mínima disponível
            if capacidade_disponivel >= hotmix.capacidade_gramas_min:
                hotmixes_com_capacidade.append((hotmix, capacidade_disponivel, velocidade, chama, pressoes))
                logger.debug(f"🔍 {hotmix.nome}: {capacidade_disponivel}g disponível para item {id_item} (janelas simultâneas)")

        if not hotmixes_com_capacidade:
            logger.debug("❌ Nenhuma HotMix com capacidade mínima disponível (janelas simultâneas)")
            return None

        # Fase 3: Aplica algoritmos de distribuição otimizada
        distribuicao = self._calcular_distribuicao_otima(float(quantidade_gramas), hotmixes_com_capacidade)
        
        if not distribuicao:
            logger.debug("❌ Algoritmos de distribuição não encontraram solução viável (janelas simultâneas)")
            return None

        # Fase 4: Executa alocação múltipla com janelas simultâneas
        sucesso = self._executar_alocacao_multipla_hotmix(
            distribuicao, inicio_tentativa, fim_tentativa, 
            id_ordem, id_pedido, id_atividade, id_item
        )
        
        if sucesso:
            hotmixes_alocadas = [h for h, _, _, _, _ in distribuicao]
            logger.debug(f"✅ Alocação múltipla otimizada: {len(hotmixes_alocadas)} HotMixes para item {id_item} (janelas simultâneas)")
            return hotmixes_alocadas, inicio_tentativa, fim_tentativa
        
        return None

    def _executar_alocacao_multipla_hotmix(self, distribuicao: List[Tuple[HotMix, float, TipoVelocidade, TipoChama, List[TipoPressaoChama]]], 
                                         inicio: datetime, fim: datetime,
                                         id_ordem: int, id_pedido: int, id_atividade: int, id_item: int) -> bool:
        """
        Executa alocação em múltiplas HotMixes conforme distribuição calculada.
        🎯 JANELAS SIMULTÂNEAS: Usa método específico para janelas simultâneas.
        """
        # Lista para rollback em caso de falha
        alocacoes_realizadas = []
        
        try:
            for hotmix, quantidade, velocidade, chama, pressoes in distribuicao:
                sucesso = hotmix.ocupar_janelas_simultaneas(
                    id_ordem=id_ordem,
                    id_pedido=id_pedido,
                    id_atividade=id_atividade,
                    id_item=id_item,
                    quantidade=quantidade,
                    velocidade=velocidade,
                    chama=chama,
                    pressao_chamas=pressoes,
                    inicio=inicio,
                    fim=fim
                )
                
                if not sucesso:
                    # Rollback das alocações já realizadas
                    for h_rollback in alocacoes_realizadas:
                        h_rollback.liberar_por_atividade(id_ordem, id_pedido, id_atividade)
                    return False
                
                alocacoes_realizadas.append(hotmix)
                logger.info(f"🔹 Alocado {quantidade}g na {hotmix.nome} (janelas simultâneas)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na alocação múltipla com janelas simultâneas: {e}")
            # Rollback em caso de erro
            for h_rollback in alocacoes_realizadas:
                h_rollback.liberar_por_atividade(id_ordem, id_pedido, id_atividade)
            return False

    # ==========================================================
    # 🎯 Alocação Principal com Backward Scheduling e Janelas Simultâneas
    # ==========================================================    
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade_gramas: int,
        **kwargs
    ) -> Tuple[bool, Optional[List[HotMix]], Optional[datetime], Optional[datetime]]:
        """
        Aloca HotMixes seguindo a estratégia otimizada com janelas de tempo simultâneas:
        1. Verificação de viabilidade total usando Multiple Knapsack Problem
        2. Verificação de capacidade total do sistema primeiro
        3. Tenta alocação individual por FIP 
        4. Tenta distribuição otimizada usando algoritmos inteligentes
        5. Usa backward scheduling minuto a minuto
        6. 🎯 JANELAS SIMULTÂNEAS: Mesmo id_item só pode ocupar períodos idênticos ou distintos
        """
        duracao = atividade.duracao
        hotmixes_ordenados = self._ordenar_por_fip(atividade)
        horario_final_tentativa = fim
        
        # Obter IDs da atividade de forma consistente
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)

        if quantidade_gramas <= 0:
            logger.warning(f"❌ Quantidade inválida para atividade {id_atividade}: {quantidade_gramas}")
            return False, None, None, None

        logger.info(f"🎯 Iniciando alocação otimizada atividade {id_atividade}: {quantidade_gramas}g do item {id_item} (JANELAS SIMULTÂNEAS)")
        logger.debug(f"📅 Janela: {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} (duração: {duracao})")
        
        # 🔍 DIAGNÓSTICO: Verifica capacidades disponíveis
        capacidades_individuais = [h.capacidade_gramas_max for h in hotmixes_ordenados]
        capacidade_total_sistema = sum(capacidades_individuais)
        capacidade_maxima_individual = max(capacidades_individuais)
        
        logger.debug(f"🔍 DIAGNÓSTICO: Quantidade necessária {quantidade_gramas}g")
        logger.debug(f"🔍 DIAGNÓSTICO: Capacidades individuais: {capacidades_individuais}")
        logger.debug(f"🔍 DIAGNÓSTICO: Capacidade total sistema: {capacidade_total_sistema}g")
        logger.debug(f"🔍 DIAGNÓSTICO: Capacidade máxima individual: {capacidade_maxima_individual}g")
        
        # 📋 REGRA PRINCIPAL: Primeiro verifica se capacidade total do sistema atende
        if quantidade_gramas > capacidade_total_sistema:
            logger.warning(f"❌ Quantidade {quantidade_gramas}g > capacidade total {capacidade_total_sistema}g - IMPOSSÍVEL")
            return False, None, None, None
        
        logger.info(f"✅ Capacidade total do sistema ({capacidade_total_sistema}g) atende a demanda ({quantidade_gramas}g)")

        # ==========================================================
        # 🔄 BACKWARD SCHEDULING COM JANELAS SIMULTÂNEAS - MINUTO A MINUTO
        # ==========================================================
        tentativas = 0
        while horario_final_tentativa - duracao >= inicio:
            tentativas += 1
            horario_inicio_tentativa = horario_final_tentativa - duracao
            
            logger.debug(f"⏰ Tentativa {tentativas}: {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}")

            # 1️⃣ PRIMEIRA ESTRATÉGIA: Tenta alocação integral em uma HotMix
            logger.debug(f"🔍 Tentando alocação individual - quantidade {quantidade_gramas}g")
            sucesso_individual = self._tentar_alocacao_individual(
                horario_inicio_tentativa, horario_final_tentativa,
                atividade, quantidade_gramas, hotmixes_ordenados,
                id_ordem, id_pedido, id_atividade, id_item
            )
            
            if sucesso_individual:
                hotmix_usada, inicio_real, fim_real = sucesso_individual
                atividade.equipamento_alocado = hotmix_usada
                atividade.equipamentos_selecionados = [hotmix_usada]
                atividade.alocada = True
                
                minutos_retrocedidos = int((fim - fim_real).total_seconds() / 60)
                logger.info(
                    f"✅ Atividade {id_atividade} (Item {id_item}) alocada INTEIRAMENTE na {hotmix_usada.nome} "
                    f"({quantidade_gramas}g) de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')} "
                    f"(retrocedeu {minutos_retrocedidos} minutos) [JANELAS SIMULTÂNEAS]"
                )
                return True, [hotmix_usada], inicio_real, fim_real

            # 2️⃣ SEGUNDA ESTRATÉGIA: Tenta alocação distribuída otimizada entre múltiplas HotMixes
            logger.debug(f"🔍 Tentando alocação distribuída para {quantidade_gramas}g")
            sucesso_distribuido = self._tentar_alocacao_distribuida_otimizada(
                horario_inicio_tentativa, horario_final_tentativa,
                atividade, quantidade_gramas, hotmixes_ordenados,
                id_ordem, id_pedido, id_atividade, id_item
            )
            
            if sucesso_distribuido:
                hotmixes_usadas, inicio_real, fim_real = sucesso_distribuido
                atividade.equipamento_alocado = None  # Múltiplas HotMixes
                atividade.equipamentos_selecionados = hotmixes_usadas
                atividade.alocada = True
                
                # Adiciona informação de alocação múltipla se disponível
                if hasattr(atividade, 'alocacao_multipla'):
                    atividade.alocacao_multipla = True
                
                minutos_retrocedidos = int((fim - fim_real).total_seconds() / 60)
                logger.info(
                    f"🧩 Atividade {id_atividade} (Item {id_item}) DIVIDIDA OTIMIZADA entre "
                    f"{', '.join(h.nome for h in hotmixes_usadas)} "
                    f"({quantidade_gramas}g total) de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')} "
                    f"(retrocedeu {minutos_retrocedidos} minutos) [JANELAS SIMULTÂNEAS]"
                )
                return True, hotmixes_usadas, inicio_real, fim_real

            # 3️⃣ Falhou nesta janela: RETROCEDE 1 MINUTO
            horario_final_tentativa -= timedelta(minutes=1)
            
            # Log ocasional para evitar spam
            if tentativas % 10 == 0:
                logger.debug(f"⏪ Tentativa {tentativas}: retrocedendo para {horario_final_tentativa.strftime('%H:%M')}")

        # Não conseguiu alocar em nenhuma janela válida
        minutos_total_retrocedidos = int((fim - (inicio + duracao)).total_seconds() / 60)
        logger.warning(
            f"❌ Atividade {id_atividade} (Item {id_item}) não pôde ser alocada após {tentativas} tentativas "
            f"dentro da janela entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}. "
            f"Quantidade necessária: {quantidade_gramas}g "
            f"(retrocedeu até o limite de {minutos_total_retrocedidos} minutos) [JANELAS SIMULTÂNEAS]"
        )
        return False, None, None, None
    
    # ==========================================================
    # 🔓 Liberações (mantidas do original)
    # ==========================================================
    def liberar_por_atividade(self, atividade: "AtividadeModular"):
        """Libera ocupações específicas por atividade."""
        id_ordem, id_pedido, id_atividade, _ = self._obter_ids_atividade(atividade)
        for hotmix in self.hotmixes:
            hotmix.liberar_por_atividade(
                id_ordem=id_ordem, 
                id_pedido=id_pedido, 
                id_atividade=id_atividade
            )
    
    def liberar_por_pedido(self, atividade: "AtividadeModular"):
        """Libera ocupações específicas por pedido."""
        id_ordem, id_pedido, _, _ = self._obter_ids_atividade(atividade)
        for hotmix in self.hotmixes:
            hotmix.liberar_por_pedido(
                id_ordem=id_ordem, 
                id_pedido=id_pedido
            )

    def liberar_por_ordem(self, atividade: "AtividadeModular"):
        """Libera ocupações específicas por ordem."""
        id_ordem, _, _, _ = self._obter_ids_atividade(atividade)
        for hotmix in self.hotmixes:
            hotmix.liberar_por_ordem(id_ordem=id_ordem)
      
    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        """Libera ocupações que já finalizaram."""
        for hotmix in self.hotmixes:
            hotmix.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        """Limpa todas as ocupações de todas as HotMixes."""
        for hotmix in self.hotmixes:
            hotmix.liberar_todas_ocupacoes()

    # ==========================================================
    # 📅 Agenda e Relatórios (mantidos do original)
    # ==========================================================
    def mostrar_agenda(self):
        """Mostra agenda consolidada de todas as HotMixes."""
        logger.info("==============================================")
        logger.info("📅 Agenda das Misturadoras com Cocção (HotMix) - JANELAS SIMULTÂNEAS")
        logger.info("==============================================")
        for hotmix in self.hotmixes:
            hotmix.mostrar_agenda()

    def obter_status_hotmixes(self) -> dict:
        """Retorna o status atual de todas as HotMixes."""
        status = {}
        for hotmix in self.hotmixes:
            ocupacoes_ativas = [
                {
                    'id_ordem': oc[0],
                    'id_pedido': oc[1],
                    'id_atividade': oc[2],
                    'id_item': oc[3],
                    'quantidade': oc[4],
                    'velocidade': oc[5].name,
                    'chama': oc[6].name,
                    'pressoes': [p.name for p in oc[7]],
                    'inicio': oc[8].strftime('%H:%M'),
                    'fim': oc[9].strftime('%H:%M')
                }
                for oc in hotmix.ocupacoes
            ]
            
            status[hotmix.nome] = {
                'capacidade_minima': hotmix.capacidade_gramas_min,
                'capacidade_maxima': hotmix.capacidade_gramas_max,
                'total_ocupacoes': len(hotmix.ocupacoes),
                'ocupacoes_ativas': ocupacoes_ativas
            }
        
        return status

    def verificar_disponibilidade(
        self,
        inicio: datetime,
        fim: datetime,
        id_item: Optional[int] = None,
        quantidade: Optional[int] = None
    ) -> List[HotMix]:
        """
        Verifica quais HotMixes estão disponíveis no período para um item específico.
        🎯 JANELAS SIMULTÂNEAS: Considera regras de janelas simultâneas.
        """
        disponiveis = []
        
        for hotmix in self.hotmixes:
            if id_item is not None:
                if hotmix.esta_disponivel_para_item_janelas_simultaneas(inicio, fim, id_item):
                    if quantidade is None:
                        disponiveis.append(hotmix)
                    else:
                        # Verifica se pode adicionar a quantidade especificada com janelas simultâneas
                        if hotmix.validar_nova_ocupacao_item_simultaneo(id_item, quantidade, inicio, fim):
                            disponiveis.append(hotmix)
            else:
                # Comportamento original para compatibilidade
                if hotmix.esta_disponivel(inicio, fim):
                    if quantidade is None or hotmix.validar_capacidade(quantidade):
                        disponiveis.append(hotmix)
        
        return disponiveis

    def obter_utilizacao_por_item(self, id_item: int) -> dict:
        """
        📊 Retorna informações de utilização de um item específico em todas as HotMixes.
        """
        utilizacao = {}
        
        for hotmix in self.hotmixes:
            ocupacoes_item = [
                oc for oc in hotmix.ocupacoes if oc[3] == id_item
            ]
            
            if ocupacoes_item:
                quantidade_total = sum(oc[4] for oc in ocupacoes_item)
                periodo_inicio = min(oc[8] for oc in ocupacoes_item)
                periodo_fim = max(oc[9] for oc in ocupacoes_item)
                
                utilizacao[hotmix.nome] = {
                    'quantidade_total': quantidade_total,
                    'num_ocupacoes': len(ocupacoes_item),
                    'periodo_inicio': periodo_inicio.strftime('%H:%M'),
                    'periodo_fim': periodo_fim.strftime('%H:%M'),
                    'ocupacoes': [
                        {
                            'id_ordem': oc[0],
                            'id_pedido': oc[1],
                            'quantidade': oc[4],
                            'inicio': oc[8].strftime('%H:%M'),
                            'fim': oc[9].strftime('%H:%M')
                        }
                        for oc in ocupacoes_item
                    ]
                }
        
        return utilizacao

    def calcular_pico_utilizacao_item(self, id_item: int) -> dict:
        """
        📈 Calcula o pico de utilização de um item específico em cada HotMix.
        """
        picos = {}
        
        for hotmix in self.hotmixes:
            ocupacoes_item = [oc for oc in hotmix.ocupacoes if oc[3] == id_item]
            
            if not ocupacoes_item:
                continue
                
            # Usa método da própria HotMix para calcular pico considerando janelas simultâneas
            periodo_inicio = min(oc[8] for oc in ocupacoes_item)
            periodo_fim = max(oc[9] for oc in ocupacoes_item)
            
            pico_quantidade = hotmix.obter_quantidade_maxima_item_periodo_simultaneo(
                id_item, periodo_inicio, periodo_fim
            )
            
            if pico_quantidade > 0:
                picos[hotmix.nome] = {
                    'pico_quantidade': pico_quantidade,
                    'periodo_analise': f"{periodo_inicio.strftime('%H:%M')} - {periodo_fim.strftime('%H:%M')}",
                    'percentual_capacidade': (pico_quantidade / hotmix.capacidade_gramas_max) * 100
                }
        
        return picos

    def obter_relatorio_detalhado_item(self, id_item: int) -> dict:
        """
        Gera relatório detalhado de um item específico em todas as HotMixes.
        """
        relatorio = {
            'id_item': id_item,
            'resumo_geral': {
                'total_hotmixes_utilizadas': 0,
                'quantidade_total_alocada': 0,
                'periodo_global': None
            },
            'detalhes_por_hotmix': {}
        }
        
        hotmixes_utilizadas = 0
        quantidade_total = 0
        periodo_global_inicio = None
        periodo_global_fim = None
        
        for hotmix in self.hotmixes:
            ocupacoes_item = [oc for oc in hotmix.ocupacoes if oc[3] == id_item]
            
            if ocupacoes_item:
                hotmixes_utilizadas += 1
                quantidade_hotmix = sum(oc[4] for oc in ocupacoes_item)
                quantidade_total += quantidade_hotmix
                
                periodo_inicio = min(oc[8] for oc in ocupacoes_item)
                periodo_fim = max(oc[9] for oc in ocupacoes_item)
                
                if periodo_global_inicio is None or periodo_inicio < periodo_global_inicio:
                    periodo_global_inicio = periodo_inicio
                if periodo_global_fim is None or periodo_fim > periodo_global_fim:
                    periodo_global_fim = periodo_fim
                
                pico_quantidade = hotmix.obter_quantidade_maxima_item_periodo_simultaneo(
                    id_item, periodo_inicio, periodo_fim
                )
                
                relatorio['detalhes_por_hotmix'][hotmix.nome] = {
                    'quantidade_total': quantidade_hotmix,
                    'pico_simultaneo': pico_quantidade,
                    'num_ocupacoes': len(ocupacoes_item),
                    'periodo': f"{periodo_inicio.strftime('%H:%M')} - {periodo_fim.strftime('%H:%M')}",
                    'percentual_capacidade': (pico_quantidade / hotmix.capacidade_gramas_max) * 100,
                    'capacidade_disponivel': hotmix.capacidade_gramas_max - pico_quantidade
                }
        
        relatorio['resumo_geral'] = {
            'total_hotmixes_utilizadas': hotmixes_utilizadas,
            'quantidade_total_alocada': quantidade_total,
            'periodo_global': f"{periodo_global_inicio.strftime('%H:%M')} - {periodo_global_fim.strftime('%H:%M')}" if periodo_global_inicio else None
        }
        
        return relatorio

    # ==========================================================
    # 🆕 Métodos Adicionais para Compatibilidade e Análise
    # ==========================================================
    def obter_detalhes_alocacao_atividade(self, atividade: "AtividadeModular") -> dict:
        """
        🔍 Retorna detalhes completos da alocação de uma atividade,
        incluindo informações de múltiplas HotMixes se aplicável.
        """
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)
        
        detalhes = {
            'id_atividade': id_atividade,
            'id_item': id_item,
            'alocacao_multipla': len(atividade.equipamentos_selecionados) > 1 if hasattr(atividade, 'equipamentos_selecionados') else False,
            'hotmixes_utilizadas': [],
            'quantidade_total': 0.0
        }
        
        # Coleta informações de todas as HotMixes que processam esta atividade
        for hotmix in self.hotmixes:
            ocupacoes_atividade = [
                oc for oc in hotmix.ocupacoes 
                if oc[0] == id_ordem and oc[1] == id_pedido and oc[2] == id_atividade
            ]
            
            if ocupacoes_atividade:
                quantidade_hotmix = sum(oc[4] for oc in ocupacoes_atividade)
                detalhes['hotmixes_utilizadas'].append({
                    'nome': hotmix.nome,
                    'quantidade': quantidade_hotmix,
                    'ocupacoes': len(ocupacoes_atividade)
                })
                detalhes['quantidade_total'] += quantidade_hotmix
        
        return detalhes

    def listar_alocacoes_multiplas(self) -> List[dict]:
        """
        📊 Lista todas as atividades que utilizaram múltiplas HotMixes.
        """
        alocacoes_multiplas = []
        atividades_processadas = set()
        
        for hotmix in self.hotmixes:
            for ocupacao in hotmix.ocupacoes:
                id_ordem, id_pedido, id_atividade = ocupacao[0], ocupacao[1], ocupacao[2]
                chave_atividade = (id_ordem, id_pedido, id_atividade)
                
                if chave_atividade not in atividades_processadas:
                    # Conta quantas HotMixes diferentes processam esta atividade
                    hotmixes_atividade = []
                    quantidade_total = 0.0
                    
                    for h in self.hotmixes:
                        ocupacoes_atividade = [
                            oc for oc in h.ocupacoes
                            if oc[0] == id_ordem and oc[1] == id_pedido and oc[2] == id_atividade
                        ]
                        if ocupacoes_atividade:
                            qtd_hotmix = sum(oc[4] for oc in ocupacoes_atividade)
                            hotmixes_atividade.append({
                                'nome': h.nome,
                                'quantidade': qtd_hotmix
                            })
                            quantidade_total += qtd_hotmix
                    
                    if len(hotmixes_atividade) > 1:
                        alocacoes_multiplas.append({
                            'id_ordem': id_ordem,
                            'id_pedido': id_pedido,
                            'id_atividade': id_atividade,
                            'id_item': ocupacao[3],
                            'quantidade_total': quantidade_total,
                            'num_hotmixes': len(hotmixes_atividade),
                            'hotmixes': hotmixes_atividade,
                            'inicio': ocupacao[8].strftime('%H:%M [%d/%m]'),
                            'fim': ocupacao[9].strftime('%H:%M [%d/%m]')
                        })
                    
                    atividades_processadas.add(chave_atividade)
        
        return alocacoes_multiplas