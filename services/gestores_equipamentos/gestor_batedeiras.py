from datetime import datetime, timedelta
from typing import Optional, Tuple, List, Union, TYPE_CHECKING
from models.equipamentos.batedeira_industrial import BatedeiraIndustrial
from models.equipamentos.batedeira_planetaria import BatedeiraPlanetaria
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular
from utils.logs.logger_factory import setup_logger
import unicodedata
import math

# 🏭 Logger específico para o gestor de batedeiras
logger = setup_logger('GestorBatedeiras')

Batedeiras = Union[BatedeiraIndustrial, BatedeiraPlanetaria]


class GestorBatedeiras:
    """
    🏭 Gestor otimizado para controle de batedeiras com algoritmo de distribuição inteligente.
    
    Baseado em:
    - Multiple Knapsack Problem para distribuição ótima
    - First Fit Decreasing (FFD) com restrições de capacidade mínima
    - Binary Space Partitioning para divisão eficiente
    
    Funcionalidades:
    - Verificação prévia de viabilidade total
    - Distribuição otimizada respeitando capacidades mín/máx
    - Algoritmo de redistribuição com backtracking
    - Priorização por FIP com balanceamento de carga
    """

    def __init__(self, batedeiras: List[Batedeiras]):
        self.batedeiras = batedeiras

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
        
        for batedeira in self.batedeiras:
            # Capacidade máxima da batedeira (JSON ou padrão)
            capacidade_gramas = self._obter_capacidade_gramas(atividade, batedeira)
            cap_max = capacidade_gramas if capacidade_gramas else batedeira.capacidade_gramas_max
            capacidade_maxima_teorica += cap_max
            
            # Verifica se pode receber o item no período
            if batedeira.esta_disponivel_para_item(inicio, fim, id_item):
                # Calcula capacidade disponível considerando ocupações existentes
                quantidade_atual = batedeira.obter_quantidade_maxima_item_periodo(id_item, inicio, fim)
                capacidade_livre = cap_max - quantidade_atual
                capacidade_disponivel_total += max(0, capacidade_livre)
        
        return capacidade_disponivel_total, capacidade_maxima_teorica

    def _verificar_viabilidade_quantidade(self, atividade: "AtividadeModular", quantidade_total: float,
                                        id_item: int, inicio: datetime, fim: datetime) -> Tuple[bool, str]:
        """
        📚 Multiple Knapsack Problem (MKP): Problema clássico de otimização combinatória onde
        múltiplos "recipientes" (knapsacks) têm capacidades limitadas e devem acomodar itens
        com restrições. Diferente do knapsack simples, considera múltiplas restrições simultâneas.
        Usado aqui para verificar se o conjunto de batedeiras pode teoricamente comportar
        a demanda antes de tentar algoritmos de alocação mais custosos computacionalmente.
        
        Verifica se é teoricamente possível alocar a quantidade solicitada.
        """
        cap_disponivel, cap_teorica = self._calcular_capacidade_total_sistema(
            atividade, id_item, inicio, fim
        )
        
        if quantidade_total > cap_teorica:
            return False, f"Quantidade {quantidade_total}g excede capacidade máxima teórica do sistema ({cap_teorica}g)"
        
        if quantidade_total > cap_disponivel:
            return False, f"Quantidade {quantidade_total}g excede capacidade disponível ({cap_disponivel}g) no período"
        
        # Verifica se é possível respeitar capacidades mínimas
        batedeiras_disponiveis = [
            b for b in self.batedeiras 
            if b.esta_disponivel_para_item(inicio, fim, id_item)
        ]
        
        if not batedeiras_disponiveis:
            return False, "Nenhuma batedeira disponível para o item no período"
        
        # Verifica viabilidade com capacidades mínimas
        capacidade_minima_total = sum(b.capacidade_gramas_min for b in batedeiras_disponiveis)
        if quantidade_total < min(b.capacidade_gramas_min for b in batedeiras_disponiveis):
            if len(batedeiras_disponiveis) == 1:
                return True, "Viável com uma batedeira"
        elif quantidade_total >= capacidade_minima_total:
            return True, "Viável com múltiplas batedeiras"
        else:
            return False, f"Quantidade {quantidade_total}g insuficiente para capacidades mínimas ({capacidade_minima_total}g)"
        
        return True, "Quantidade viável"

    # ==========================================================
    # 🧮 Algoritmos de Distribuição Otimizada
    # ==========================================================
    def _algoritmo_distribuicao_balanceada(self, quantidade_total: float, 
                                          batedeiras_disponiveis: List[Tuple[Batedeiras, float]]) -> List[Tuple[Batedeiras, float]]:
        """
        Algoritmo de distribuição baseado em Binary Space Partitioning adaptado.
        
        📚 Binary Space Partitioning: Técnica que divide recursivamente o espaço de soluções,
        originalmente usada em computação gráfica. Aqui adaptada para dividir a quantidade total
        proporcionalmente entre batedeiras, considerando suas capacidades disponíveis.
        Garante distribuição equilibrada minimizando desperdício de capacidade.
        
        Estratégia:
        1. Ordena batedeiras por capacidade disponível (maior primeiro)
        2. Aplica divisão proporcional inicial
        3. Ajusta para respeitar capacidades mín/máx
        4. Redistribui excedentes recursivamente
        """
        if not batedeiras_disponiveis:
            return []
        
        # Ordena por capacidade disponível (maior primeiro)
        batedeiras_ordenadas = sorted(batedeiras_disponiveis, key=lambda x: x[1], reverse=True)
        
        # Capacidade total disponível
        capacidade_total_disponivel = sum(cap for _, cap in batedeiras_ordenadas)
        
        if capacidade_total_disponivel < quantidade_total:
            return []
        
        # Fase 1: Distribuição proporcional inicial
        distribuicao = []
        quantidade_restante = quantidade_total
        
        for i, (batedeira, cap_disponivel) in enumerate(batedeiras_ordenadas):
            if i == len(batedeiras_ordenadas) - 1:
                # Última batedeira recebe o restante
                quantidade_batedeira = quantidade_restante
            else:
                # Distribuição proporcional
                proporcao = cap_disponivel / capacidade_total_disponivel
                quantidade_batedeira = quantidade_total * proporcao
            
            # Ajusta para limites da batedeira
            quantidade_batedeira = max(batedeira.capacidade_gramas_min, 
                                     min(quantidade_batedeira, cap_disponivel))
            
            distribuicao.append((batedeira, quantidade_batedeira))
            quantidade_restante -= quantidade_batedeira
            
            if quantidade_restante <= 0:
                break
        
        # Fase 2: Redistribuição de excedentes/déficits
        distribuicao = self._redistribuir_excedentes(distribuicao, quantidade_total)
        
        return distribuicao

    def _redistribuir_excedentes(self, distribuicao: List[Tuple[Batedeiras, float]], 
                                quantidade_target: float) -> List[Tuple[Batedeiras, float]]:
        """
        📚 Load Balancing Algorithms: Técnicas de balanceamento de carga que redistribuem
        trabalho entre recursos para otimizar utilização. Inspirado em algoritmos de
        sistemas distribuídos, realiza ajustes iterativos para equilibrar cargas respeitando
        restrições de capacidade. Fundamental para evitar subutilização de equipamentos
        e garantir distribuições mais eficientes que métodos puramente gulosos.
        
        Redistribui quantidades para atingir o target exato respeitando limites.
        """
        MAX_ITERACOES = 10000
        iteracao = 0
        
        while iteracao < MAX_ITERACOES:
            quantidade_atual = sum(qtd for _, qtd in distribuicao)
            diferenca = quantidade_target - quantidade_atual
            
            if abs(diferenca) < 0.1:  # Tolerância de 0.1g
                break
            
            if diferenca > 0:
                # Precisa adicionar quantidade
                for i, (batedeira, qtd_atual) in enumerate(distribuicao):
                    cap_gramas = self._obter_capacidade_gramas(None, batedeira)
                    cap_max = cap_gramas if cap_gramas else batedeira.capacidade_gramas_max
                    margem_disponivel = cap_max - qtd_atual
                    
                    if margem_disponivel > 0:
                        adicionar = min(diferenca, margem_disponivel)
                        distribuicao[i] = (batedeira, qtd_atual + adicionar)
                        diferenca -= adicionar
                        
                        if diferenca <= 0:
                            break
            else:
                # Precisa remover quantidade
                diferenca = abs(diferenca)
                for i, (batedeira, qtd_atual) in enumerate(distribuicao):
                    margem_removivel = qtd_atual - batedeira.capacidade_gramas_min
                    
                    if margem_removivel > 0:
                        remover = min(diferenca, margem_removivel)
                        distribuicao[i] = (batedeira, qtd_atual - remover)
                        diferenca -= remover
                        
                        if diferenca <= 0:
                            break
            
            iteracao += 1
        
        # Remove batedeiras com quantidade abaixo do mínimo
        distribuicao_final = [
            (batedeira, qtd) for batedeira, qtd in distribuicao
            if qtd >= batedeira.capacidade_gramas_min
        ]
        
        return distribuicao_final

    def _algoritmo_first_fit_decreasing(self, quantidade_total: float,
                                      batedeiras_disponiveis: List[Tuple[Batedeiras, float]]) -> List[Tuple[Batedeiras, float]]:
        """
        📚 First Fit Decreasing (FFD): Algoritmo clássico de Bin Packing que ordena itens
        por tamanho decrescente e aloca cada item no primeiro recipiente que couber.
        Garante aproximação de 11/9 do ótimo e é amplamente usado em problemas de otimização.
        Adaptado aqui para respeitar capacidades mínimas das batedeiras, evitando
        distribuições que violem restrições operacionais.
        
        Implementação do algoritmo First Fit Decreasing adaptado para capacidades mínimas.
        """
        # Ordena batedeiras por capacidade disponível (maior primeiro)
        batedeiras_ordenadas = sorted(batedeiras_disponiveis, key=lambda x: x[1], reverse=True)
        
        distribuicao = []
        quantidade_restante = quantidade_total
        
        for batedeira, cap_disponivel in batedeiras_ordenadas:
            if quantidade_restante <= 0:
                break
            
            # Calcula quanto alocar nesta batedeira
            if quantidade_restante >= batedeira.capacidade_gramas_min:
                quantidade_alocar = min(quantidade_restante, cap_disponivel)
                
                # Garante que não fica quantidade insuficiente para próximas batedeiras
                batedeiras_restantes = [b for b, _ in batedeiras_ordenadas 
                                      if b != batedeira and (quantidade_restante - quantidade_alocar) > 0]
                
                if batedeiras_restantes:
                    cap_min_restantes = min(b.capacidade_gramas_min for b in batedeiras_restantes)
                    if quantidade_restante - quantidade_alocar < cap_min_restantes and quantidade_restante - quantidade_alocar > 0:
                        # Ajusta para deixar quantidade suficiente
                        quantidade_alocar = quantidade_restante - cap_min_restantes
                
                if quantidade_alocar >= batedeira.capacidade_gramas_min:
                    distribuicao.append((batedeira, quantidade_alocar))
                    quantidade_restante -= quantidade_alocar
        
        return distribuicao if quantidade_restante <= 0.1 else []

    # ==========================================================
    # 🎯 Alocação Otimizada Principal
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade_produto: int,
        **kwargs
    ) -> Tuple[bool, Optional[Batedeiras], Optional[datetime], Optional[datetime]]:
        """
        Alocação otimizada com verificação prévia de viabilidade e distribuição inteligente.
        
        Returns:
            Para alocação simples: (True, batedeira, inicio_real, fim_real)
            Para alocação múltipla: (True, [lista_batedeiras], inicio_real, fim_real)
        """
        # Extrai IDs da atividade
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)
        
        duracao = atividade.duracao
        horario_final_tentativa = fim
        quantidade_total = float(quantidade_produto)

        logger.info(f"🎯 Iniciando alocação otimizada: {quantidade_total}g do item {id_item}")

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            # Fase 1: Verificação de viabilidade
            viavel, motivo = self._verificar_viabilidade_quantidade(
                atividade, quantidade_total, id_item, horario_inicio_tentativa, horario_final_tentativa
            )
            
            if not viavel:
                logger.debug(f"❌ Inviável no horário {horario_inicio_tentativa.strftime('%H:%M')}: {motivo}")
                horario_final_tentativa -= timedelta(minutes=1)
                continue

            # Fase 2: Identificar batedeiras disponíveis com suas capacidades
            batedeiras_disponiveis = []
            batedeiras_ordenadas = self._ordenar_por_fip(atividade)
            
            for batedeira in batedeiras_ordenadas:
                if batedeira.esta_disponivel_para_item(horario_inicio_tentativa, horario_final_tentativa, id_item):
                    # Calcula capacidade disponível
                    capacidade_gramas = self._obter_capacidade_gramas(atividade, batedeira)
                    cap_max = capacidade_gramas if capacidade_gramas else batedeira.capacidade_gramas_max
                    
                    quantidade_atual = batedeira.obter_quantidade_maxima_item_periodo(
                        id_item, horario_inicio_tentativa, horario_final_tentativa
                    )
                    capacidade_disponivel = cap_max - quantidade_atual
                    
                    if capacidade_disponivel >= batedeira.capacidade_gramas_min:
                        batedeiras_disponiveis.append((batedeira, capacidade_disponivel))

            if not batedeiras_disponiveis:
                horario_final_tentativa -= timedelta(minutes=1)
                continue

            # Fase 3: Tentativa de alocação em batedeira única (otimização)
            for batedeira, cap_disponivel in batedeiras_disponiveis:
                if cap_disponivel >= quantidade_total:
                    # Pode alocar em uma única batedeira
                    sucesso = self._tentar_alocacao_simples(
                        batedeira, atividade, quantidade_total, 
                        horario_inicio_tentativa, horario_final_tentativa
                    )
                    if sucesso:
                        logger.info(f"✅ Alocação simples: {quantidade_total}g na {batedeira.nome}")
                        return True, batedeira, horario_inicio_tentativa, horario_final_tentativa

            # Fase 4: Distribuição em múltiplas batedeiras
            distribuicao = self._calcular_distribuicao_otima(quantidade_total, batedeiras_disponiveis)
            
            if distribuicao:
                sucesso = self._executar_alocacao_multipla(
                    distribuicao, atividade, horario_inicio_tentativa, horario_final_tentativa
                )
                if sucesso:
                    batedeiras_alocadas = [b for b, _ in distribuicao]
                    logger.info(
                        f"✅ Alocação múltipla bem-sucedida em {len(batedeiras_alocadas)} batedeiras: "
                        f"{', '.join(b.nome for b in batedeiras_alocadas)}"
                    )
                    # ✅ CORREÇÃO: Retorna lista de batedeiras para alocação múltipla
                    return True, batedeiras_alocadas, horario_inicio_tentativa, horario_final_tentativa

            horario_final_tentativa -= timedelta(minutes=1)

        logger.warning(f"❌ Falha na alocação de {quantidade_total}g do item {id_item}")
        return False, None, None, None

    def _calcular_distribuicao_otima(self, quantidade_total: float, 
                                   batedeiras_disponiveis: List[Tuple[Batedeiras, float]]) -> List[Tuple[Batedeiras, float]]:
        """
        Calcula distribuição ótima usando múltiplos algoritmos e retorna o melhor resultado.
        """
        # Testa algoritmo de distribuição balanceada
        dist_balanceada = self._algoritmo_distribuicao_balanceada(quantidade_total, batedeiras_disponiveis)
        
        # Testa First Fit Decreasing
        dist_ffd = self._algoritmo_first_fit_decreasing(quantidade_total, batedeiras_disponiveis)
        
        # Avalia qual distribuição é melhor
        candidatos = []
        
        if dist_balanceada and sum(qtd for _, qtd in dist_balanceada) >= quantidade_total * 0.99:
            candidatos.append(('balanceada', dist_balanceada))
        
        if dist_ffd and sum(qtd for _, qtd in dist_ffd) >= quantidade_total * 0.99:
            candidatos.append(('ffd', dist_ffd))
        
        if not candidatos:
            return []
        
        # Escolhe a distribuição que usa menos batedeiras, ou a mais balanceada
        melhor_distribuicao = min(candidatos, key=lambda x: (len(x[1]), -self._calcular_balanceamento(x[1])))
        
        logger.debug(f"📊 Escolhida distribuição {melhor_distribuicao[0]} com {len(melhor_distribuicao[1])} batedeiras")
        
        return melhor_distribuicao[1]

    def _calcular_balanceamento(self, distribuicao: List[Tuple[Batedeiras, float]]) -> float:
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

    def _tentar_alocacao_simples(self, batedeira: Batedeiras, atividade: "AtividadeModular", 
                                quantidade: float, inicio: datetime, fim: datetime) -> bool:
        """
        Tenta alocação em uma única batedeira.
        """
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)
        velocidade = self._obter_velocidade(atividade, batedeira)
        
        sucesso = batedeira.ocupar(
            id_ordem=id_ordem,
            id_pedido=id_pedido,
            id_atividade=id_atividade,
            id_item=id_item,
            quantidade_gramas=quantidade,
            inicio=inicio,
            fim=fim,
            velocidade=velocidade
        )
        
        if sucesso:
            atividade.equipamento_alocado = batedeira
            atividade.equipamentos_selecionados = [batedeira]
            atividade.alocada = True
            atividade.inicio_planejado = inicio
            atividade.fim_planejado = fim
            
            logger.info(f"✅ Alocação simples: {quantidade}g na {batedeira.nome}")
        
        return sucesso

    def _executar_alocacao_multipla(self, distribuicao: List[Tuple[Batedeiras, float]], 
                                  atividade: "AtividadeModular", inicio: datetime, fim: datetime) -> bool:
        """
        Executa alocação em múltiplas batedeiras conforme distribuição calculada.
        """
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)
        
        # Lista para rollback em caso de falha
        alocacoes_realizadas = []
        
        try:
            for batedeira, quantidade in distribuicao:
                velocidade = self._obter_velocidade(atividade, batedeira)
                
                sucesso = batedeira.ocupar(
                    id_ordem=id_ordem,
                    id_pedido=id_pedido,
                    id_atividade=id_atividade,
                    id_item=id_item,
                    quantidade_gramas=quantidade,
                    inicio=inicio,
                    fim=fim,
                    velocidade=velocidade
                )
                
                if not sucesso:
                    # Rollback das alocações já realizadas
                    for b_rollback in alocacoes_realizadas:
                        b_rollback.liberar_por_atividade(id_atividade, id_pedido, id_ordem)
                    return False
                
                alocacoes_realizadas.append(batedeira)
                logger.info(f"🔹 Alocado {quantidade}g na {batedeira.nome}")
            
            # ✅ CORREÇÃO: Atualiza informações da atividade para alocação múltipla
            atividade.equipamentos_selecionados = [b for b, _ in distribuicao]
            atividade.equipamento_alocado = distribuicao[0][0]  # Primeira batedeira como principal
            atividade.alocada = True
            atividade.inicio_planejado = inicio
            atividade.fim_planejado = fim
            
            # Adiciona informação de alocação múltipla se disponível
            if hasattr(atividade, 'alocacao_multipla'):
                atividade.alocacao_multipla = True
                atividade.detalhes_alocacao = [
                    {'batedeira': b.nome, 'quantidade': qtd} for b, qtd in distribuicao
                ]
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na alocação múltipla: {e}")
            # Rollback em caso de erro
            for b_rollback in alocacoes_realizadas:
                b_rollback.liberar_por_atividade(id_atividade, id_pedido, id_ordem)
            return False

    # ==========================================================
    # 🔍 Métodos auxiliares (mantidos do código original)
    # ==========================================================
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[Batedeiras]:
        ordenadas = sorted(
            self.batedeiras,
            key=lambda b: atividade.fips_equipamentos.get(b, 999)
        )
        return ordenadas

    def _obter_velocidade(self, atividade: "AtividadeModular", batedeira: Batedeiras) -> Optional[int]:
        try:
            if hasattr(atividade, "configuracoes_equipamentos"):
                nome_bruto = batedeira.nome.lower().replace(" ", "_")
                nome_chave = unicodedata.normalize("NFKD", nome_bruto).encode("ASCII", "ignore").decode("utf-8")
                
                config = atividade.configuracoes_equipamentos.get(nome_chave)
                if config and "velocidade" in config:
                    velocidade = int(config["velocidade"])
                    return velocidade
        except Exception as e:
            logger.warning(f"⚠️ Erro ao tentar obter velocidade para {batedeira.nome}: {e}")
        return None

    def _obter_capacidade_gramas(self, atividade: "AtividadeModular", batedeira: Batedeiras) -> Optional[int]:
        try:
            if atividade and hasattr(atividade, "configuracoes_equipamentos"):
                nome_bruto = batedeira.nome.lower().replace(" ", "_")
                nome_chave = unicodedata.normalize("NFKD", nome_bruto).encode("ASCII", "ignore").decode("utf-8")
                
                config = atividade.configuracoes_equipamentos.get(nome_chave)
                if config and "capacidade_gramas" in config:
                    capacidade = int(config["capacidade_gramas"])
                    return capacidade
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter capacidade gramas para {batedeira.nome}: {e}")
        return None

    def _obter_ids_atividade(self, atividade: "AtividadeModular") -> Tuple[int, int, int, int]:
        id_ordem = getattr(atividade, 'id_ordem', 0)
        id_pedido = getattr(atividade, 'id_pedido', 0) 
        id_atividade = getattr(atividade, 'id_atividade', 0)
        id_item = getattr(atividade, 'id_item', 0)
        
        return id_ordem, id_pedido, id_atividade, id_item

    # ==========================================================
    # 🔓 Métodos de liberação (mantidos do original)
    # ==========================================================
    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        for batedeira in self.batedeiras:
            batedeira.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_por_atividade(self, atividade: "AtividadeModular"):
        id_ordem, id_pedido, id_atividade, _ = self._obter_ids_atividade(atividade)
        for batedeira in self.batedeiras:
            batedeira.liberar_por_atividade(id_atividade=id_atividade, id_pedido=id_pedido, id_ordem=id_ordem)
    
    def liberar_por_pedido(self, atividade: "AtividadeModular"):
        id_ordem, id_pedido, _, _ = self._obter_ids_atividade(atividade)
        for batedeira in self.batedeiras:
            batedeira.liberar_por_pedido(id_ordem=id_ordem, id_pedido=id_pedido)

    def liberar_por_ordem(self, atividade: "AtividadeModular"):
        id_ordem, _, _, _ = self._obter_ids_atividade(atividade)
        for batedeira in self.batedeiras:
            batedeira.liberar_por_ordem(id_ordem)

    def liberar_por_item(self, id_item: int):
        for batedeira in self.batedeiras:
            batedeira.liberar_por_item(id_item)

    def liberar_todas_ocupacoes(self):
        for batedeira in self.batedeiras:
            batedeira.ocupacoes.clear()

    # ==========================================================
    # 📅 Métodos de status (mantidos do original)
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda das Batedeiras")
        logger.info("==============================================")
        for batedeira in self.batedeiras:
            batedeira.mostrar_agenda()

    def obter_status_batedeiras(self) -> dict:
        status = {}
        for batedeira in self.batedeiras:
            ocupacoes_ativas = [
                {
                    'id_ordem': oc[0],
                    'id_pedido': oc[1],
                    'id_atividade': oc[2],
                    'id_item': oc[3],
                    'quantidade': oc[4],
                    'velocidade': oc[5],
                    'inicio': oc[6].strftime('%H:%M'),
                    'fim': oc[7].strftime('%H:%M')
                }
                for oc in batedeira.ocupacoes
            ]
            
            status[batedeira.nome] = {
                'capacidade_minima': batedeira.capacidade_gramas_min,
                'capacidade_maxima': batedeira.capacidade_gramas_max,
                'total_ocupacoes': len(batedeira.ocupacoes),
                'ocupacoes_ativas': ocupacoes_ativas
            }
        
        return status

    def obter_detalhes_alocacao_atividade(self, atividade: "AtividadeModular") -> dict:
        """
        🔍 Retorna detalhes completos da alocação de uma atividade,
        incluindo informações de múltiplas batedeiras se aplicável.
        """
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)
        
        detalhes = {
            'id_atividade': id_atividade,
            'id_item': id_item,
            'alocacao_multipla': len(atividade.equipamentos_selecionados) > 1 if hasattr(atividade, 'equipamentos_selecionados') else False,
            'batedeiras_utilizadas': [],
            'quantidade_total': 0.0
        }
        
        # Coleta informações de todas as batedeiras que processam esta atividade
        for batedeira in self.batedeiras:
            ocupacoes_atividade = [
                oc for oc in batedeira.ocupacoes 
                if oc[0] == id_ordem and oc[1] == id_pedido and oc[2] == id_atividade
            ]
            
            if ocupacoes_atividade:
                quantidade_batedeira = sum(oc[4] for oc in ocupacoes_atividade)
                detalhes['batedeiras_utilizadas'].append({
                    'nome': batedeira.nome,
                    'quantidade': quantidade_batedeira,
                    'ocupacoes': len(ocupacoes_atividade)
                })
                detalhes['quantidade_total'] += quantidade_batedeira
        
        return detalhes

    def listar_alocacoes_multiplas(self) -> List[dict]:
        """
        📊 Lista todas as atividades que utilizaram múltiplas batedeiras.
        """
        alocacoes_multiplas = []
        atividades_processadas = set()
        
        for batedeira in self.batedeiras:
            for ocupacao in batedeira.ocupacoes:
                id_ordem, id_pedido, id_atividade = ocupacao[0], ocupacao[1], ocupacao[2]
                chave_atividade = (id_ordem, id_pedido, id_atividade)
                
                if chave_atividade not in atividades_processadas:
                    # Conta quantas batedeiras diferentes processam esta atividade
                    batedeiras_atividade = []
                    quantidade_total = 0.0
                    
                    for b in self.batedeiras:
                        ocupacoes_atividade = [
                            oc for oc in b.ocupacoes
                            if oc[0] == id_ordem and oc[1] == id_pedido and oc[2] == id_atividade
                        ]
                        if ocupacoes_atividade:
                            qtd_batedeira = sum(oc[4] for oc in ocupacoes_atividade)
                            batedeiras_atividade.append({
                                'nome': b.nome,
                                'quantidade': qtd_batedeira
                            })
                            quantidade_total += qtd_batedeira
                    
                    if len(batedeiras_atividade) > 1:
                        alocacoes_multiplas.append({
                            'id_ordem': id_ordem,
                            'id_pedido': id_pedido,
                            'id_atividade': id_atividade,
                            'id_item': ocupacao[3],
                            'quantidade_total': quantidade_total,
                            'num_batedeiras': len(batedeiras_atividade),
                            'batedeiras': batedeiras_atividade,
                            'inicio': ocupacao[6].strftime('%H:%M [%d/%m]'),
                            'fim': ocupacao[7].strftime('%H:%M [%d/%m]')
                        })
                    
                    atividades_processadas.add(chave_atividade)
        
        return alocacoes_multiplas