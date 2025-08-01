from typing import List, Tuple, Optional, TYPE_CHECKING
from models.equipamentos.balanca_digital import BalancaDigital
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular
from utils.logs.logger_factory import setup_logger
from datetime import datetime, timedelta
import unicodedata

# ⚖️ Logger específico para o gestor de balanças
logger = setup_logger('GestorBalancas')


class GestorBalancas:
    """
    ⚖️ Gestor otimizado para controle de balanças digitais com distribuição inteligente.
    
    Baseado em:
    - Multiple Knapsack Problem para verificação de viabilidade
    - First Fit Decreasing (FFD) para distribuição ótima
    - Binary Space Partitioning para balanceamento de cargas
    - Load Balancing para redistribuição eficiente
    
    Funcionalidades:
    - Verificação prévia de viabilidade total do sistema
    - Distribuição otimizada respeitando capacidades mín/máx
    - Algoritmos de otimização com múltiplas estratégias
    - Priorização por FIP com balanceamento de carga
    """

    def __init__(self, balancas: List[BalancaDigital]):
        self.balancas = balancas

    # ==========================================================
    # 📊 Análise de Viabilidade e Capacidades - CORRIGIDO
    # ==========================================================
    def _calcular_capacidade_total_sistema(self) -> Tuple[float, float]:
        """
        📚 Multiple Knapsack Problem (MKP): Calcula capacidade total do sistema.
        Premissa: Todas as balanças estão sempre disponíveis.
        
        Retorna: (capacidade_total_disponivel, capacidade_maxima_teorica)
        """
        capacidade_total = sum(balanca.capacidade_gramas_max for balanca in self.balancas)
        return capacidade_total, capacidade_total

    def _verificar_viabilidade_quantidade(self, quantidade_total: float) -> Tuple[bool, str]:
        """
        Verifica se é teoricamente possível processar a quantidade solicitada.
        Simplificado: apenas verifica capacidade total do sistema.
        """
        cap_disponivel, cap_teorica = self._calcular_capacidade_total_sistema()
        
        if quantidade_total > cap_teorica:
            return False, f"Quantidade {quantidade_total}g excede capacidade máxima teórica do sistema ({cap_teorica}g)"
        
        # Verifica se é possível respeitar capacidades mínimas
        if not self.balancas:
            return False, "Nenhuma balança disponível no sistema"
        
        # Verifica viabilidade com capacidades mínimas
        capacidade_minima_total = sum(b.capacidade_gramas_min for b in self.balancas)
        if quantidade_total < min(b.capacidade_gramas_min for b in self.balancas):
            if len(self.balancas) == 1:
                return True, "Viável com uma balança"
        elif quantidade_total >= capacidade_minima_total:
            return True, "Viável com múltiplas balanças"
        else:
            return False, f"Quantidade {quantidade_total}g insuficiente para capacidades mínimas ({capacidade_minima_total}g)"
        
        return True, "Quantidade viável"

    # ==========================================================
    # 🧮 Algoritmos de Distribuição Otimizada - CORRIGIDO
    # ==========================================================
    def _algoritmo_distribuicao_balanceada(self, quantidade_total: float, 
                                          balancas_disponiveis: List[Tuple[BalancaDigital, float]]) -> List[Tuple[BalancaDigital, float]]:
        """
        📚 Binary Space Partitioning: Técnica que divide recursivamente o espaço de soluções,
        originalmente usada em computação gráfica. Aqui adaptada para dividir a quantidade total
        proporcionalmente entre balanças, considerando suas capacidades disponíveis.
        Garante distribuição equilibrada minimizando desperdício de capacidade.
        
        Algoritmo de distribuição baseado em Binary Space Partitioning adaptado.
        """
        if not balancas_disponiveis:
            return []
        
        # Ordena por capacidade disponível (maior primeiro)
        balancas_ordenadas = sorted(balancas_disponiveis, key=lambda x: x[1], reverse=True)
        
        # Capacidade total disponível
        capacidade_total_disponivel = sum(cap for _, cap in balancas_ordenadas)
        
        if capacidade_total_disponivel < quantidade_total:
            return []
        
        # Fase 1: Distribuição proporcional inicial
        distribuicao = []
        quantidade_restante = quantidade_total
        
        for i, (balanca, cap_disponivel) in enumerate(balancas_ordenadas):
            if i == len(balancas_ordenadas) - 1:
                # Última balança recebe o restante
                quantidade_balanca = quantidade_restante
            else:
                # Distribuição proporcional
                proporcao = cap_disponivel / capacidade_total_disponivel
                quantidade_balanca = quantidade_total * proporcao
            
            # Ajusta para limites da balança (usando nomes corretos dos atributos)
            quantidade_balanca = max(balanca.capacidade_gramas_min, 
                                   min(quantidade_balanca, cap_disponivel))
            
            distribuicao.append((balanca, quantidade_balanca))
            quantidade_restante -= quantidade_balanca
            
            if quantidade_restante <= 0:
                break
        
        # Fase 2: Redistribuição de excedentes/déficits
        distribuicao = self._redistribuir_excedentes(distribuicao, quantidade_total)
        
        return distribuicao

    def _redistribuir_excedentes(self, distribuicao: List[Tuple[BalancaDigital, float]], 
                                quantidade_target: float) -> List[Tuple[BalancaDigital, float]]:
        """
        📚 Load Balancing Algorithms: Técnicas de balanceamento de carga que redistribuem
        trabalho entre recursos para otimizar utilização. Inspirado em algoritmos de
        sistemas distribuídos, realiza ajustes iterativos para equilibrar cargas respeitando
        restrições de capacidade. Fundamental para evitar subutilização de equipamentos.
        
        Redistribui quantidades para atingir o target exato respeitando limites.
        """
        MAX_ITERACOES = 10
        iteracao = 0
        
        while iteracao < MAX_ITERACOES:
            quantidade_atual = sum(qtd for _, qtd in distribuicao)
            diferenca = quantidade_target - quantidade_atual
            
            if abs(diferenca) < 0.1:  # Tolerância de 0.1g
                break
            
            if diferenca > 0:
                # Precisa adicionar quantidade
                for i, (balanca, qtd_atual) in enumerate(distribuicao):
                    margem_disponivel = balanca.capacidade_gramas_max - qtd_atual
                    
                    if margem_disponivel > 0:
                        adicionar = min(diferenca, margem_disponivel)
                        distribuicao[i] = (balanca, qtd_atual + adicionar)
                        diferenca -= adicionar
                        
                        if diferenca <= 0:
                            break
            else:
                # Precisa remover quantidade
                diferenca = abs(diferenca)
                for i, (balanca, qtd_atual) in enumerate(distribuicao):
                    margem_removivel = qtd_atual - balanca.capacidade_gramas_min
                    
                    if margem_removivel > 0:
                        remover = min(diferenca, margem_removivel)
                        distribuicao[i] = (balanca, qtd_atual - remover)
                        diferenca -= remover
                        
                        if diferenca <= 0:
                            break
            
            iteracao += 1
        
        # Remove balanças com quantidade abaixo do mínimo
        distribuicao_final = [
            (balanca, qtd) for balanca, qtd in distribuicao
            if qtd >= balanca.capacidade_gramas_min
        ]
        
        return distribuicao_final

    def _algoritmo_first_fit_decreasing(self, quantidade_total: float,
                                      balancas_disponiveis: List[Tuple[BalancaDigital, float]]) -> List[Tuple[BalancaDigital, float]]:
        """
        📚 First Fit Decreasing (FFD): Algoritmo clássico de Bin Packing que ordena itens
        por tamanho decrescente e aloca cada item no primeiro recipiente que couber.
        Garante aproximação de 11/9 do ótimo e é amplamente usado em problemas de otimização.
        Adaptado aqui para respeitar capacidades mínimas das balanças.
        
        Implementação do algoritmo First Fit Decreasing adaptado para capacidades mínimas.
        """
        # Ordena balanças por capacidade disponível (maior primeiro)
        balancas_ordenadas = sorted(balancas_disponiveis, key=lambda x: x[1], reverse=True)
        
        distribuicao = []
        quantidade_restante = quantidade_total
        
        for balanca, cap_disponivel in balancas_ordenadas:
            if quantidade_restante <= 0:
                break
            
            # Calcula quanto alocar nesta balança
            if quantidade_restante >= balanca.capacidade_gramas_min:
                quantidade_alocar = min(quantidade_restante, cap_disponivel)
                
                # Garante que não fica quantidade insuficiente para próximas balanças
                balancas_restantes = [b for b, _ in balancas_ordenadas 
                                    if b != balanca and (quantidade_restante - quantidade_alocar) > 0]
                
                if balancas_restantes:
                    cap_min_restantes = min(b.capacidade_gramas_min for b in balancas_restantes)
                    if quantidade_restante - quantidade_alocar < cap_min_restantes and quantidade_restante - quantidade_alocar > 0:
                        # Ajusta para deixar quantidade suficiente
                        quantidade_alocar = quantidade_restante - cap_min_restantes
                
                if quantidade_alocar >= balanca.capacidade_gramas_min:
                    distribuicao.append((balanca, quantidade_alocar))
                    quantidade_restante -= quantidade_alocar
        
        return distribuicao if quantidade_restante <= 0.1 else []

    # ==========================================================
    # 📊 Ordenação e Utilitários
    # ==========================================================
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[BalancaDigital]:
        ordenadas = sorted(
            self.balancas,
            key=lambda b: atividade.fips_equipamentos.get(b, 999)
        )
        return ordenadas

    def _obter_peso_explicito_do_json(self, atividade: "AtividadeModular") -> Optional[float]:
        try:
            config = atividade.configuracoes_equipamentos or {}
            for chave, conteudo in config.items():
                chave_normalizada = unicodedata.normalize("NFKD", chave).encode("ASCII", "ignore").decode("utf-8").lower()
                if "balanca" in chave_normalizada:
                    peso_gramas = conteudo.get("peso_gramas")
                    if peso_gramas is not None:
                        return peso_gramas
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao buscar peso_gramas no JSON da atividade: {e}")
            return None

    def _calcular_distribuicao_otima(self, quantidade_total: float, 
                                   balancas_disponiveis: List[Tuple[BalancaDigital, float]]) -> List[Tuple[BalancaDigital, float]]:
        """
        Calcula distribuição ótima usando múltiplos algoritmos e retorna o melhor resultado.
        """
        # Testa algoritmo de distribuição balanceada
        dist_balanceada = self._algoritmo_distribuicao_balanceada(quantidade_total, balancas_disponiveis)
        
        # Testa First Fit Decreasing
        dist_ffd = self._algoritmo_first_fit_decreasing(quantidade_total, balancas_disponiveis)
        
        # Avalia qual distribuição é melhor
        candidatos = []
        
        if dist_balanceada and sum(qtd for _, qtd in dist_balanceada) >= quantidade_total * 0.99:
            candidatos.append(('balanceada', dist_balanceada))
        
        if dist_ffd and sum(qtd for _, qtd in dist_ffd) >= quantidade_total * 0.99:
            candidatos.append(('ffd', dist_ffd))
        
        if not candidatos:
            return []
        
        # Escolhe a distribuição que usa menos balanças, ou a mais balanceada
        melhor_distribuicao = min(candidatos, key=lambda x: (len(x[1]), -self._calcular_balanceamento(x[1])))
        
        logger.debug(f"📊 Escolhida distribuição {melhor_distribuicao[0]} com {len(melhor_distribuicao[1])} balanças")
        
        return melhor_distribuicao[1]

    def _calcular_balanceamento(self, distribuicao: List[Tuple[BalancaDigital, float]]) -> float:
        """
        Calcula score de balanceamento da distribuição (maior = mais balanceado).
        """
        if len(distribuicao) <= 1:
            return 1.0
        
        quantidades = [qtd for _, qtd in distribuicao]
        media = sum(quantidades) / len(quantidades)
        variancia = sum((qtd - media) ** 2 for qtd in quantidades) / len(quantidades)
        
        # Score inversamente proporcional à variância
        return 1.0 / (1.0 + variancia / media**2) if media > 0 else 0.0

    # ==========================================================
    # 🎯 Alocação Otimizada Principal - CORRIGIDO
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade_gramas: float | None = None
    ) -> Tuple[bool, Optional[BalancaDigital], Optional[datetime], Optional[datetime]]:
        """
        Alocação otimizada simplificada - sem verificações temporais.
        Premissa: Todas as balanças estão sempre disponíveis.
        
        Returns:
            Para alocação simples: (True, balanca, inicio, fim)
            Para alocação múltipla: (True, [lista_balancas], inicio, fim)
        """
        # Determina quantidade final
        peso_json = self._obter_peso_explicito_do_json(atividade)
        if peso_json is not None:
            quantidade_final = peso_json
        else:
            quantidade_final = quantidade_gramas

        if quantidade_final is None:
            logger.error("❌ Nenhuma quantidade definida para balança.")
            return False, None, None, None

        logger.info(f"⚖️ Iniciando alocação otimizada: {quantidade_final}g")

        # Fase 1: Verificação de viabilidade (apenas capacidade total)
        viavel, motivo = self._verificar_viabilidade_quantidade(quantidade_final)
        
        if not viavel:
            logger.warning(f"❌ Inviável: {motivo}")
            return False, None, None, None

        # Fase 2: Preparar balanças disponíveis (todas, sempre)
        balancas_ordenadas = self._ordenar_por_fip(atividade)
        balancas_disponiveis = [(balanca, balanca.capacidade_gramas_max) for balanca in balancas_ordenadas]

        # Fase 3: Tentativa de alocação em balança única (otimização)
        for balanca, cap_max in balancas_disponiveis:
            if balanca.aceita_quantidade(quantidade_final):
                sucesso = self._executar_alocacao_simples(
                    balanca, atividade, quantidade_final, inicio, fim
                )
                if sucesso:
                    logger.info(f"✅ Alocação simples: {quantidade_final}g na {balanca.nome}")
                    return True, balanca, inicio, fim

        # Fase 4: Distribuição em múltiplas balanças
        distribuicao = self._calcular_distribuicao_otima(quantidade_final, balancas_disponiveis)
        
        if distribuicao:
            sucesso = self._executar_alocacao_multipla(
                distribuicao, atividade, inicio, fim
            )
            if sucesso:
                balancas_alocadas = [b for b, _ in distribuicao]
                logger.info(
                    f"✅ Alocação múltipla bem-sucedida em {len(balancas_alocadas)} balanças: "
                    f"{', '.join(b.nome for b in balancas_alocadas)}"
                )
                # Retorna lista de balanças para alocação múltipla
                return True, balancas_alocadas, inicio, fim

        logger.error(f"❌ Falha na alocação de {quantidade_final}g")
        return False, None, None, None

    def _executar_alocacao_simples(self, balanca: BalancaDigital, atividade: "AtividadeModular", 
                                  quantidade: float, inicio: datetime, fim: datetime) -> bool:
        """
        Executa alocação em uma única balança.
        Simplificado: sem verificações de disponibilidade.
        """
        sucesso = balanca.ocupar(
            id_ordem=atividade.id_ordem,
            id_pedido=atividade.id_pedido,
            id_atividade=atividade.id_atividade,
            id_item=0,  # Adicionado parâmetro id_item obrigatório
            quantidade=quantidade,
            inicio=inicio,
            fim=fim
        )
        
        if sucesso:
            atividade.equipamento_alocado = balanca
            atividade.equipamentos_selecionados = [balanca]
            atividade.alocada = True
        
        return sucesso

    def _executar_alocacao_multipla(self, distribuicao: List[Tuple[BalancaDigital, float]], 
                                  atividade: "AtividadeModular", inicio: datetime, fim: datetime) -> bool:
        """
        Executa alocação em múltiplas balanças conforme distribuição calculada.
        Simplificado: sem rollback, avalia antes de alocar.
        """
        # ✅ PRÉ-VALIDAÇÃO: Verifica se todas as alocações são possíveis ANTES de executar
        for balanca, quantidade in distribuicao:
            if not balanca.aceita_quantidade(quantidade):
                logger.error(f"❌ Balança {balanca.nome} não aceita {quantidade}g")
                return False
        
        # ✅ EXECUÇÃO: Se chegou aqui, todas as alocações são válidas
        sucesso_total = True
        for i, (balanca, quantidade) in enumerate(distribuicao):
            sucesso = balanca.ocupar(
                id_ordem=atividade.id_ordem,
                id_pedido=atividade.id_pedido,
                id_atividade=atividade.id_atividade,
                id_item=i,  # Adicionado parâmetro id_item obrigatório (usando índice)
                quantidade=quantidade,
                inicio=inicio,
                fim=fim
            )
            
            if not sucesso:
                logger.error(f"❌ Falha inesperada ao alocar {quantidade}g na {balanca.nome}")
                sucesso_total = False
                # Continua tentando as outras balanças mesmo com falha
            else:
                logger.info(f"🔹 Alocado {quantidade}g na {balanca.nome}")
        
        if sucesso_total:
            # Atualiza informações da atividade para alocação múltipla
            atividade.equipamentos_selecionados = [b for b, _ in distribuicao]
            atividade.equipamento_alocado = distribuicao[0][0]  # Primeira balança como principal
            atividade.alocada = True
        
        return sucesso_total

    # ==========================================================
    # 🔓 Liberação (mantidos do original)
    # ==========================================================
    def liberar_por_atividade(self, atividade: "AtividadeModular"):
        for balanca in self.balancas:
            balanca.liberar_por_atividade(id_ordem=atividade.id_ordem, id_pedido=atividade.id_pedido, id_atividade=atividade.id_atividade)

    def liberar_por_pedido(self, atividade: "AtividadeModular"):
        for balanca in self.balancas:
            balanca.liberar_por_pedido(id_ordem=atividade.id_ordem, id_pedido=atividade.id_pedido)

    def liberar_por_ordem(self, atividade: "AtividadeModular"):
        for balanca in self.balancas:
            balanca.liberar_por_ordem(id_ordem=atividade.id_ordem)

    def liberar_todas_ocupacoes(self):
        for balanca in self.balancas:
            balanca.liberar_todas_ocupacoes()

    # ==========================================================
    # 📅 Agenda e Status - CORRIGIDO
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda das Balanças")
        logger.info("==============================================")
        for balanca in self.balancas:
            balanca.mostrar_agenda()

    def obter_status_balancas(self) -> dict:
        """
        Retorna o status atual de todas as balanças.
        """
        status = {}
        for balanca in self.balancas:
            status[balanca.nome] = {
                'capacidade_minima': balanca.capacidade_gramas_min,  # Corrigido
                'capacidade_maxima': balanca.capacidade_gramas_max,  # Corrigido
                'ocupada': len(balanca.ocupacoes) > 0,  # Corrigido - baseado nas ocupações
                'total_ocupacoes': len(balanca.ocupacoes)  # Corrigido - usando ocupacoes
            }
        
        return status

    def listar_alocacoes_multiplas(self, atividade: "AtividadeModular") -> List[dict]:
        """
        📊 Lista alocações múltiplas para uma atividade específica.
        """
        alocacoes_multiplas = []
        balancas_utilizadas = []
        
        for balanca in self.balancas:
            ocupacoes_atividade = [
                oc for oc in balanca.ocupacoes
                if (oc[0] == atividade.id_ordem and 
                    oc[1] == atividade.id_pedido and 
                    oc[2] == atividade.id_atividade)
            ]
            
            if ocupacoes_atividade:
                quantidade_balanca = sum(oc[4] for oc in ocupacoes_atividade)  # Corrigido - índice 4 é quantidade
                balancas_utilizadas.append({
                    'nome': balanca.nome,
                    'quantidade': quantidade_balanca
                })
        
        if len(balancas_utilizadas) > 1:
            quantidade_total = sum(b['quantidade'] for b in balancas_utilizadas)
            alocacoes_multiplas.append({
                'id_atividade': atividade.id_atividade,
                'quantidade_total': quantidade_total,
                'num_balancas': len(balancas_utilizadas),
                'balancas': balancas_utilizadas
            })
        
        return alocacoes_multiplas