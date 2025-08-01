from datetime import datetime, timedelta
from typing import Optional, Tuple, List, TYPE_CHECKING
from models.equipamentos.divisora_de_massas import DivisoraDeMassas
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular
from utils.logs.logger_factory import setup_logger
import unicodedata

logger = setup_logger('GestorDivisoras')


class GestorDivisorasBoleadoras:
    """
    🏭 Gestor otimizado para controle de divisoras de massas com distribuição inteligente.
    
    Baseado em:
    - Multiple Knapsack Problem para verificação de viabilidade
    - First Fit Decreasing (FFD) para distribuição ótima
    - Binary Space Partitioning para balanceamento de cargas
    - Load Balancing para redistribuição eficiente
    - Backward Scheduling Convencional (sem otimizações de salto)
    
    Funcionalidades:
    - Verificação prévia de viabilidade total do sistema
    - Distribuição otimizada respeitando capacidades mín/máx
    - Algoritmos de otimização com múltiplas estratégias
    - Priorização por FIP com balanceamento de carga
    - Soma quantidades do mesmo id_item em intervalos sobrepostos
    """

    def __init__(self, divisoras: List[DivisoraDeMassas]):
        self.divisoras = divisoras

    # ==========================================================
    # 📊 Análise de Viabilidade e Capacidades
    # ==========================================================
    def _calcular_capacidade_total_sistema(self, atividade: "AtividadeModular", id_item: int,
                                          inicio: datetime, fim: datetime) -> Tuple[float, float]:
        """
        📚 Multiple Knapsack Problem (MKP): Calcula capacidade total do sistema.
        ✅ CORRIGIDO: Só considera ocupações que realmente se sobrepõem temporalmente.
        
        Retorna: (capacidade_total_disponivel, capacidade_maxima_teorica)
        """
        capacidade_disponivel_total = 0.0
        capacidade_maxima_teorica = 0.0
        
        logger.debug(f"🧮 Calculando capacidade para período {inicio.strftime('%H:%M')}-{fim.strftime('%H:%M')}")
        
        for divisora in self.divisoras:
            # Determina capacidade máxima (JSON ou padrão)
            capacidade_gramas = self._obter_capacidade_explicita_do_json(atividade)
            cap_max = capacidade_gramas if capacidade_gramas else divisora.capacidade_gramas_max
            capacidade_maxima_teorica += cap_max
            
            # ✅ CORREÇÃO: Verifica se pode receber o item no período (sem forçar sobreposição)
            if divisora.esta_disponivel_para_item(inicio, fim, id_item):
                # ✅ CORREÇÃO: Calcula ocupação APENAS de períodos que se sobrepõem
                quantidade_atual = 0.0
                
                for ocupacao in divisora.ocupacoes:
                    if ocupacao[3] == id_item:  # mesmo item
                        ocupacao_inicio = ocupacao[6]
                        ocupacao_fim = ocupacao[7]
                        
                        # ✅ SÓ CONSIDERA SE HÁ SOBREPOSIÇÃO TEMPORAL
                        if not (fim <= ocupacao_inicio or inicio >= ocupacao_fim):
                            quantidade_atual = max(quantidade_atual, ocupacao[4])
                            logger.debug(f"   • {divisora.nome}: Ocupação sobreposta {ocupacao[4]}g ({ocupacao_inicio.strftime('%H:%M')}-{ocupacao_fim.strftime('%H:%M')})")
                        else:
                            logger.debug(f"   • {divisora.nome}: Ocupação SEM sobreposição {ocupacao[4]}g ({ocupacao_inicio.strftime('%H:%M')}-{ocupacao_fim.strftime('%H:%M')})")
                
                capacidade_livre = cap_max - quantidade_atual
                capacidade_disponivel_total += max(0, capacidade_livre)
                
                logger.debug(f"   • {divisora.nome}: Cap máx {cap_max}g, ocupado {quantidade_atual}g, disponível {capacidade_livre}g")
            else:
                logger.debug(f"   • {divisora.nome}: Indisponível para item {id_item}")
        
        logger.debug(f"📊 RESULTADO: Disponível {capacidade_disponivel_total}g / Teórica {capacidade_maxima_teorica}g")
        return capacidade_disponivel_total, capacidade_maxima_teorica

    def _verificar_viabilidade_quantidade(self, atividade: "AtividadeModular", quantidade_total: float,
                                        id_item: int, inicio: datetime, fim: datetime) -> Tuple[bool, str]:
        """
        📚 Multiple Knapsack Problem (MKP): Verifica se é teoricamente possível
        alocar a quantidade solicitada considerando capacidades e disponibilidade por item.
        """
        cap_disponivel, cap_teorica = self._calcular_capacidade_total_sistema(
            atividade, id_item, inicio, fim
        )
        
        if quantidade_total > cap_teorica:
            return False, f"Quantidade {quantidade_total}g excede capacidade máxima teórica do sistema ({cap_teorica}g)"
        
        if quantidade_total > cap_disponivel:
            return False, f"Quantidade {quantidade_total}g excede capacidade disponível ({cap_disponivel}g) no período"
        
        # Verifica se é possível respeitar capacidades mínimas
        divisoras_disponiveis = [
            d for d in self.divisoras 
            if d.esta_disponivel_para_item(inicio, fim, id_item)
        ]
        
        if not divisoras_disponiveis:
            return False, "Nenhuma divisora disponível para o item no período"
        
        # Verifica viabilidade com capacidades mínimas
        capacidade_minima_total = sum(d.capacidade_gramas_min for d in divisoras_disponiveis)
        if quantidade_total < min(d.capacidade_gramas_min for d in divisoras_disponiveis):
            if len(divisoras_disponiveis) == 1:
                return True, "Viável com uma divisora"
        elif quantidade_total >= capacidade_minima_total:
            return True, "Viável com múltiplas divisoras"
        else:
            return False, f"Quantidade {quantidade_total}g insuficiente para capacidades mínimas ({capacidade_minima_total}g)"
        
        return True, "Quantidade viável"

    # ==========================================================
    # 🧮 Algoritmos de Distribuição Otimizada
    # ==========================================================
    def _algoritmo_distribuicao_balanceada(self, quantidade_total: float, 
                                          divisoras_disponiveis: List[Tuple[DivisoraDeMassas, float]]) -> List[Tuple[DivisoraDeMassas, float]]:
        """
        ✅ SIMPLIFICADO: Baseado na lógica funcional do GestorBatedeiras.
        Distribui quantidade proporcionalmente entre divisoras disponíveis.
        """
        if not divisoras_disponiveis:
            logger.debug("❌ Nenhuma divisora disponível para distribuição")
            return []
        
        # Ordena por capacidade disponível (maior primeiro)
        divisoras_ordenadas = sorted(divisoras_disponiveis, key=lambda x: x[1], reverse=True)
        
        # Capacidade total disponível
        capacidade_total_disponivel = sum(cap for _, cap in divisoras_ordenadas)
        
        logger.debug(f"🧮 Capacidade total disponível: {capacidade_total_disponivel}g para {quantidade_total}g")
        
        if capacidade_total_disponivel < quantidade_total:
            logger.debug(f"❌ Capacidade insuficiente: {capacidade_total_disponivel}g < {quantidade_total}g")
            return []
        
        # ✅ DISTRIBUIÇÃO SIMPLES E FUNCIONAL (como GestorBatedeiras)
        distribuicao = []
        quantidade_restante = quantidade_total
        
        for i, (divisora, cap_disponivel) in enumerate(divisoras_ordenadas):
            if quantidade_restante <= 0:
                break
                
            if i == len(divisoras_ordenadas) - 1:
                # Última divisora recebe o restante
                quantidade_divisora = quantidade_restante
            else:
                # Distribuição proporcional simples
                proporcao = cap_disponivel / capacidade_total_disponivel
                quantidade_divisora = min(quantidade_total * proporcao, cap_disponivel)
            
            # ✅ VALIDAÇÃO SIMPLES: Respeita limites mín/máx
            quantidade_divisora = max(divisora.capacidade_gramas_min, 
                                    min(quantidade_divisora, cap_disponivel))
            
            if quantidade_divisora >= divisora.capacidade_gramas_min:
                distribuicao.append((divisora, quantidade_divisora))
                quantidade_restante -= quantidade_divisora
                logger.debug(f"   📋 {divisora.nome}: {quantidade_divisora}g alocado")
        
        # ✅ AJUSTE FINAL SIMPLES
        quantidade_atual = sum(qtd for _, qtd in distribuicao)
        diferenca = quantidade_total - quantidade_atual
        
        if abs(diferenca) > 0.1 and distribuicao:  # Tolerância de 0.1g
            # Ajusta na primeira divisora que tiver margem
            for i, (divisora, qtd) in enumerate(distribuicao):
                margem = divisora.capacidade_gramas_max - qtd
                if margem > abs(diferenca):
                    distribuicao[i] = (divisora, qtd + diferenca)
                    logger.debug(f"   🔧 Ajuste final: +{diferenca}g na {divisora.nome}")
                    break
        
        quantidade_final = sum(qtd for _, qtd in distribuicao)
        logger.debug(f"📊 Distribuição final: {quantidade_final}g ({len(distribuicao)} divisoras)")
        
        # ✅ ACEITA SE CONSEGUIR PELO MENOS 95% (mais flexível que 99%)
        if quantidade_final >= quantidade_total * 0.95:
            return distribuicao
        else:
            logger.debug(f"❌ Distribuição rejeitada: {quantidade_final}g < {quantidade_total * 0.95}g (95% mínimo)")
            return []

    def _redistribuir_excedentes(self, distribuicao: List[Tuple[DivisoraDeMassas, float]], 
                                quantidade_target: float) -> List[Tuple[DivisoraDeMassas, float]]:
        """
        📚 Load Balancing Algorithms: Redistribui quantidades para atingir o target exato
        respeitando limites de capacidade das divisoras.
        """
        MAX_ITERACOES = 1000
        iteracao = 0
        
        while iteracao < MAX_ITERACOES:
            quantidade_atual = sum(qtd for _, qtd in distribuicao)
            diferenca = quantidade_target - quantidade_atual
            
            if abs(diferenca) < 0.1:  # Tolerância de 0.1g
                break
            
            if diferenca > 0:
                # Precisa adicionar quantidade
                for i, (divisora, qtd_atual) in enumerate(distribuicao):
                    cap_max = divisora.capacidade_gramas_max
                    margem_disponivel = cap_max - qtd_atual
                    
                    if margem_disponivel > 0:
                        adicionar = min(diferenca, margem_disponivel)
                        distribuicao[i] = (divisora, qtd_atual + adicionar)
                        diferenca -= adicionar
                        
                        if diferenca <= 0:
                            break
            else:
                # Precisa remover quantidade
                diferenca = abs(diferenca)
                for i, (divisora, qtd_atual) in enumerate(distribuicao):
                    margem_removivel = qtd_atual - divisora.capacidade_gramas_min
                    
                    if margem_removivel > 0:
                        remover = min(diferenca, margem_removivel)
                        distribuicao[i] = (divisora, qtd_atual - remover)
                        diferenca -= remover
                        
                        if diferenca <= 0:
                            break
            
            iteracao += 1
        
        # Remove divisoras com quantidade abaixo do mínimo
        distribuicao_final = [
            (divisora, qtd) for divisora, qtd in distribuicao
            if qtd >= divisora.capacidade_gramas_min
        ]
        
        return distribuicao_final

    def _algoritmo_first_fit_decreasing(self, quantidade_total: float,
                                      divisoras_disponiveis: List[Tuple[DivisoraDeMassas, float]]) -> List[Tuple[DivisoraDeMassas, float]]:
        """
        📚 First Fit Decreasing (FFD): Algoritmo clássico que ordena divisoras por capacidade
        decrescente e aloca quantidade respeitando capacidades mínimas.
        """
        # Ordena divisoras por capacidade disponível (maior primeiro)
        divisoras_ordenadas = sorted(divisoras_disponiveis, key=lambda x: x[1], reverse=True)
        
        distribuicao = []
        quantidade_restante = quantidade_total
        
        for divisora, cap_disponivel in divisoras_ordenadas:
            if quantidade_restante <= 0:
                break
            
            # Calcula quanto alocar nesta divisora
            if quantidade_restante >= divisora.capacidade_gramas_min:
                quantidade_alocar = min(quantidade_restante, cap_disponivel)
                
                # Garante que não fica quantidade insuficiente para próximas divisoras
                divisoras_restantes = [d for d, _ in divisoras_ordenadas 
                                     if d != divisora and (quantidade_restante - quantidade_alocar) > 0]
                
                if divisoras_restantes:
                    cap_min_restantes = min(d.capacidade_gramas_min for d in divisoras_restantes)
                    if quantidade_restante - quantidade_alocar < cap_min_restantes and quantidade_restante - quantidade_alocar > 0:
                        # Ajusta para deixar quantidade suficiente
                        quantidade_alocar = quantidade_restante - cap_min_restantes
                
                if quantidade_alocar >= divisora.capacidade_gramas_min:
                    distribuicao.append((divisora, quantidade_alocar))
                    quantidade_restante -= quantidade_alocar
        
        return distribuicao if quantidade_restante <= 0.1 else []

    def _calcular_distribuicao_otima(self, quantidade_total: float, 
                                   divisoras_disponiveis: List[Tuple[DivisoraDeMassas, float]]) -> List[Tuple[DivisoraDeMassas, float]]:
        """
        Calcula distribuição ótima usando múltiplos algoritmos e retorna o melhor resultado.
        """
        logger.debug(f"🧮 _calcular_distribuicao_otima: {quantidade_total}g para {len(divisoras_disponiveis)} divisoras")
        for i, (div, cap) in enumerate(divisoras_disponiveis):
            logger.debug(f"   {i+1}. {div.nome}: {cap}g disponível")
        
        # Testa algoritmo de distribuição balanceada
        dist_balanceada = self._algoritmo_distribuicao_balanceada(quantidade_total, divisoras_disponiveis)
        logger.debug(f"🔹 Distribuição balanceada: {len(dist_balanceada)} divisoras")
        if dist_balanceada:
            soma_balanceada = sum(qtd for _, qtd in dist_balanceada)
            logger.debug(f"   Total: {soma_balanceada}g (meta: {quantidade_total}g)")
        
        # Testa First Fit Decreasing
        dist_ffd = self._algoritmo_first_fit_decreasing(quantidade_total, divisoras_disponiveis)
        logger.debug(f"🔸 Distribuição FFD: {len(dist_ffd)} divisoras")
        if dist_ffd:
            soma_ffd = sum(qtd for _, qtd in dist_ffd)
            logger.debug(f"   Total: {soma_ffd}g (meta: {quantidade_total}g)")
        
        # Avalia qual distribuição é melhor
        candidatos = []
        
        # ✅ CRITÉRIO MAIS FLEXÍVEL: Aceita 95% em vez de 99%
        if dist_balanceada and sum(qtd for _, qtd in dist_balanceada) >= quantidade_total * 0.95:
            candidatos.append(('balanceada', dist_balanceada))
            logger.debug(f"✅ Distribuição balanceada aprovada")
        else:
            logger.debug(f"❌ Distribuição balanceada rejeitada")
        
        if dist_ffd and sum(qtd for _, qtd in dist_ffd) >= quantidade_total * 0.95:
            candidatos.append(('ffd', dist_ffd))
            logger.debug(f"✅ Distribuição FFD aprovada")
        else:
            logger.debug(f"❌ Distribuição FFD rejeitada")
        
        if not candidatos:
            logger.debug(f"🚨 NENHUMA DISTRIBUIÇÃO VÁLIDA ENCONTRADA!")
            return []
        
        # Escolhe a distribuição que usa menos divisoras, ou a mais balanceada
        melhor_distribuicao = min(candidatos, key=lambda x: (len(x[1]), -self._calcular_balanceamento(x[1])))
        
        logger.debug(f"📊 Escolhida distribuição {melhor_distribuicao[0]} com {len(melhor_distribuicao[1])} divisoras")
        for i, (div, qtd) in enumerate(melhor_distribuicao[1]):
            logger.debug(f"   {i+1}. {div.nome}: {qtd}g")
        
        return melhor_distribuicao[1]

    def _calcular_balanceamento(self, distribuicao: List[Tuple[DivisoraDeMassas, float]]) -> float:
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
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
    # ==========================================================
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[DivisoraDeMassas]:
        ordenadas = sorted(
            self.divisoras,
            key=lambda d: atividade.fips_equipamentos.get(d, 999)
        )
        return ordenadas
    
    # ==========================================================
    # 🔍 Leitura dos parâmetros via JSON
    # ==========================================================  
    def _obter_capacidade_explicita_do_json(self, atividade: "AtividadeModular") -> Optional[float]:
        """
        🔍 Verifica se há um valor explícito de 'capacidade_gramas' no JSON da atividade
        para alguma chave que contenha 'divisora' no nome. Se houver, retorna esse valor.
        """
        try:
            config = atividade.configuracoes_equipamentos or {}
            for chave, conteudo in config.items():
                chave_normalizada = unicodedata.normalize("NFKD", chave).encode("ASCII", "ignore").decode("utf-8").lower()
                if "divisora" in chave_normalizada:
                    capacidade_gramas = conteudo.get("capacidade_gramas")
                    if capacidade_gramas is not None:
                        logger.info(
                            f"📦 JSON da atividade {atividade.id_atividade} define capacidade_gramas = {capacidade_gramas}g para o equipamento '{chave}'"
                        )
                        return capacidade_gramas
            logger.debug(f"ℹ️ Nenhuma capacidade_gramas definida no JSON da atividade {atividade.id_atividade}.")
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao buscar capacidade_gramas no JSON da atividade: {e}")
            return None

    def _obter_flag_boleadora(self, atividade: "AtividadeModular", divisora: DivisoraDeMassas) -> bool:
        try:
            nome_bruto = divisora.nome.lower().replace(" ", "_")
            nome_chave = unicodedata.normalize("NFKD", nome_bruto).encode("ASCII", "ignore").decode("utf-8")

            config = atividade.configuracoes_equipamentos.get(nome_chave)
            if config:
                return str(config.get("boleadora", "False")).lower() == "true"
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter flag boleadora para {divisora.nome}: {e}")
        return False
    
    # ==========================================================
    # 🔍 Métodos auxiliares para extração de dados da atividade
    # ==========================================================
    def _obter_ids_atividade(self, atividade: "AtividadeModular") -> Tuple[int, int, int, int]:
        """
        Extrai os IDs da atividade de forma consistente.
        Retorna: (id_ordem, id_pedido, id_atividade, id_item)
        """
        id_ordem = getattr(atividade, 'id_ordem', 0)
        id_pedido = getattr(atividade, 'id_pedido', 0) 
        id_atividade = getattr(atividade, 'id_atividade', 0)
        id_item = getattr(atividade, 'id_item', 0)
        
        return id_ordem, id_pedido, id_atividade, id_item

    # ==========================================================
    # 🎯 Alocação com Backward Scheduling Convencional
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade_produto: int,
        **kwargs
    ) -> Tuple[bool, Optional[List[DivisoraDeMassas]], Optional[datetime], Optional[datetime]]:
        """
        ✅ ALOCAÇÃO COM BACKWARD SCHEDULING CONVENCIONAL
        
        Implementa backward scheduling tradicional igual aos outros gestores:
        - Retrocede 1 minuto por vez quando não consegue alocar
        - Não possui otimizações de salto inteligente
        - Para apenas quando horario_final_tentativa - duracao < inicio
        
        Returns:
            Para alocação simples: (True, [divisora], inicio, fim)
            Para alocação múltipla: (True, [lista_divisoras], inicio, fim)
        """
        # Extrai IDs da atividade
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)
        
        duracao = atividade.duracao
        horario_final_tentativa = fim

        # Determina quantidade final (JSON tem prioridade)
        peso_json = self._obter_capacidade_explicita_do_json(atividade)
        if peso_json is not None:
            quantidade_total = peso_json
            logger.debug(f"📊 Usando capacidade_gramas do JSON: {quantidade_total}g")
        else:
            quantidade_total = float(quantidade_produto)

        logger.info(f"🎯 Iniciando alocação com backward scheduling convencional: {quantidade_total}g do item {id_item}")

        # 🔍 DEBUG INICIAL - Executar apenas na primeira tentativa
        self._debug_estado_inicial(atividade, quantidade_total, id_item, inicio, fim)

        # ✅ BACKWARD SCHEDULING CONVENCIONAL - Loop principal
        tentativas = 0
        while horario_final_tentativa - duracao >= inicio:
            tentativas += 1
            horario_inicio_tentativa = horario_final_tentativa - duracao

            logger.debug(f"⏱️ Tentativa #{tentativas} de alocação entre {horario_inicio_tentativa.strftime('%H:%M')} e {horario_final_tentativa.strftime('%H:%M')}")

            # 🔍 DEBUG DETALHADO - Executar apenas nas primeiras 3 tentativas
            if tentativas <= 3:
                self._debug_tentativa_detalhada(
                    tentativas, atividade, quantidade_total, id_item, 
                    horario_inicio_tentativa, horario_final_tentativa
                )

            # Fase 1: Verificação de viabilidade (apenas para casos extremos)
            viavel, motivo = self._verificar_viabilidade_quantidade(
                atividade, quantidade_total, id_item, horario_inicio_tentativa, horario_final_tentativa
            )
            
            # ✅ CORREÇÃO: Só bloqueia se for realmente impossível (ex: nenhuma divisora disponível)
            # Capacidade insuficiente não deve parar o backward scheduling
            if not viavel and "Nenhuma divisora disponível" in motivo:
                logger.debug(f"❌ Inviável no horário {horario_inicio_tentativa.strftime('%H:%M')}: {motivo}")
                # ✅ RETROCESSO CONVENCIONAL: Apenas 1 minuto
                horario_final_tentativa -= timedelta(minutes=1)
                continue
            elif not viavel:
                # Log para debug, mas continua tentando
                logger.debug(f"⚠️ Capacidade limitada no horário {horario_inicio_tentativa.strftime('%H:%M')}: {motivo} (tentando mesmo assim)")
            
            # 🔍 DEBUG: Força tentativa mesmo com capacidade limitada nas primeiras tentativas
            if tentativas <= 3:
                logger.debug(f"🧪 FORÇANDO TENTATIVA #{tentativas} mesmo com viabilidade: {'✅' if viavel else '❌'}")
                logger.debug(f"    Motivo da limitação: {motivo if not viavel else 'N/A'}")

            # Fase 2: Identificar divisoras disponíveis com suas capacidades
            divisoras_disponiveis = []
            divisoras_ordenadas = self._ordenar_por_fip(atividade)
            
            for divisora in divisoras_ordenadas:
                if divisora.esta_disponivel_para_item(horario_inicio_tentativa, horario_final_tentativa, id_item):
                    # ✅ CORREÇÃO: Usa mesma lógica do GestorBatedeiras
                    capacidade_gramas = self._obter_capacidade_explicita_do_json(atividade)
                    cap_max = capacidade_gramas if capacidade_gramas else divisora.capacidade_gramas_max
                    
                    # ✅ CORREÇÃO: Calcula quantidade atual usando mesmo método das batedeiras
                    quantidade_atual = 0.0
                    for ocupacao in divisora.ocupacoes:
                        if ocupacao[3] == id_item:  # mesmo item
                            oc_inicio = ocupacao[6]
                            oc_fim = ocupacao[7]
                            # SÓ CONSIDERA SE HÁ SOBREPOSIÇÃO TEMPORAL
                            if not (horario_final_tentativa <= oc_inicio or horario_inicio_tentativa >= oc_fim):
                                quantidade_atual = max(quantidade_atual, ocupacao[4])
                    
                    capacidade_disponivel = cap_max - quantidade_atual
                    
                    if capacidade_disponivel >= divisora.capacidade_gramas_min:
                        divisoras_disponiveis.append((divisora, capacidade_disponivel))
                        logger.debug(f"   📋 {divisora.nome}: {capacidade_disponivel}g disponível (atual: {quantidade_atual}g)")

            if not divisoras_disponiveis:
                logger.debug(f"🔄 Nenhuma divisora disponível no horário {horario_inicio_tentativa.strftime('%H:%M')}")
                # ✅ RETROCESSO CONVENCIONAL: Apenas 1 minuto
                horario_final_tentativa -= timedelta(minutes=1)
                continue

            # Fase 3: Tentativa de alocação em divisora única (otimização)
            for divisora, cap_disponivel in divisoras_disponiveis:
                if cap_disponivel >= quantidade_total:
                    # Pode alocar em uma única divisora
                    sucesso = self._tentar_alocacao_simples(
                        divisora, atividade, quantidade_total, 
                        horario_inicio_tentativa, horario_final_tentativa
                    )
                    if sucesso:
                        logger.info(f"✅ Alocação simples: {quantidade_total}g na {divisora.nome} após {tentativas} tentativas")
                        return True, [divisora], horario_inicio_tentativa, horario_final_tentativa

            # Fase 4: Distribuição em múltiplas divisoras
            if divisoras_disponiveis:
                distribuicao = self._calcular_distribuicao_otima(quantidade_total, divisoras_disponiveis)
                
                if distribuicao:
                    sucesso = self._executar_alocacao_multipla(
                        distribuicao, atividade, horario_inicio_tentativa, horario_final_tentativa
                    )
                    if sucesso:
                        divisoras_alocadas = [d for d, _ in distribuicao]
                        logger.info(
                            f"✅ Alocação múltipla bem-sucedida em {len(divisoras_alocadas)} divisoras após {tentativas} tentativas: "
                            f"{', '.join(d.nome for d in divisoras_alocadas)}"
                        )
                        return True, divisoras_alocadas, horario_inicio_tentativa, horario_final_tentativa
                    else:
                        logger.debug(f"❌ Distribuição falhou na execução (tentativa #{tentativas})")
                else:
                    logger.debug(f"❌ Não foi possível calcular distribuição (tentativa #{tentativas})")
            else:
                logger.debug(f"❌ Nenhuma divisora disponível (tentativa #{tentativas})")

            # ✅ RETROCESSO CONVENCIONAL: Falhou nesta janela, retrocede 1 minuto
            logger.debug(f"🔁 Tentativa #{tentativas} falhou. Retrocedendo 1 minuto.")
            horario_final_tentativa -= timedelta(minutes=1)

        # ✅ Saiu do loop - não conseguiu alocar em nenhum horário válido
        logger.warning(
            f"❌ Atividade {atividade.id_atividade} (item {id_item}) não alocada após {tentativas} tentativas. "
            f"Nenhum conjunto de divisoras disponível entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')} "
            f"para {quantidade_total}g."
        )
        
        # 🔍 DEBUG FINAL - Executar diagnóstico completo
        self._debug_falha_final(atividade, quantidade_total, id_item, inicio, fim, tentativas)
        
        return False, None, None, None

    def _tentar_alocacao_simples(self, divisora: DivisoraDeMassas, atividade: "AtividadeModular", 
                                quantidade: float, inicio: datetime, fim: datetime) -> bool:
        """
        Tenta alocação em uma única divisora.
        """
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)
        boleadora_flag = self._obter_flag_boleadora(atividade, divisora)
        
        sucesso = divisora.ocupar(
            id_ordem=id_ordem,
            id_pedido=id_pedido,
            id_atividade=id_atividade,
            id_item=id_item,
            quantidade=quantidade,
            inicio=inicio,
            fim=fim,
            usar_boleadora=boleadora_flag
        )
        
        if sucesso:
            atividade.equipamento_alocado = divisora
            atividade.equipamentos_selecionados = [divisora]
            atividade.alocada = True
            atividade.inicio_planejado = inicio
            atividade.fim_planejado = fim
            
            logger.info(f"✅ Alocação simples: {quantidade}g na {divisora.nome}")
        
        return sucesso

    def _executar_alocacao_multipla(self, distribuicao: List[Tuple[DivisoraDeMassas, float]], 
                                  atividade: "AtividadeModular", inicio: datetime, fim: datetime) -> bool:
        """
        Executa alocação em múltiplas divisoras conforme distribuição calculada.
        """
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)
        
        # Lista para rollback em caso de falha
        alocacoes_realizadas = []
        
        try:
            for divisora, quantidade in distribuicao:
                boleadora_flag = self._obter_flag_boleadora(atividade, divisora)
                
                sucesso = divisora.ocupar(
                    id_ordem=id_ordem,
                    id_pedido=id_pedido,
                    id_atividade=id_atividade,
                    id_item=id_item,
                    quantidade=quantidade,
                    inicio=inicio,
                    fim=fim,
                    usar_boleadora=boleadora_flag
                )
                
                if not sucesso:
                    # Rollback das alocações já realizadas
                    for d_rollback in alocacoes_realizadas:
                        d_rollback.liberar_por_atividade(id_atividade=id_atividade, id_pedido=id_pedido, id_ordem=id_ordem)
                    return False
                
                alocacoes_realizadas.append(divisora)
                logger.info(f"🔹 Alocado {quantidade}g na {divisora.nome}")
            
            # Atualiza informações da atividade para alocação múltipla
            atividade.equipamentos_selecionados = [d for d, _ in distribuicao]
            atividade.equipamento_alocado = distribuicao[0][0]  # Primeira divisora como principal
            atividade.alocada = True
            atividade.inicio_planejado = inicio
            atividade.fim_planejado = fim
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na alocação múltipla: {e}")
            # Rollback em caso de erro
            for d_rollback in alocacoes_realizadas:
                d_rollback.liberar_por_atividade(id_atividade=id_atividade, id_pedido=id_pedido, id_ordem=id_ordem)
            return False

    # ==========================================================
    # 🔓 Liberação (mantidos do original)
    # ==========================================================
    def liberar_por_atividade(self, atividade: "AtividadeModular") -> None:
        id_ordem, id_pedido, id_atividade, _ = self._obter_ids_atividade(atividade)
        for divisora in self.divisoras:
            divisora.liberar_por_atividade(id_ordem=id_ordem, id_pedido=id_pedido, id_atividade=id_atividade)

    def liberar_por_pedido(self, atividade: "AtividadeModular") -> None:
        id_ordem, id_pedido, _, _ = self._obter_ids_atividade(atividade)
        for divisora in self.divisoras:
            divisora.liberar_por_pedido(id_ordem=id_ordem, id_pedido=id_pedido)

    def liberar_por_ordem(self, atividade: "AtividadeModular") -> None:
        id_ordem, _, _, _ = self._obter_ids_atividade(atividade)
        for divisora in self.divisoras:
            divisora.liberar_por_ordem(id_ordem=id_ordem)

    def liberar_por_item(self, id_item: int):
        """
        🔓 Libera todas as ocupações de um item específico em todas as divisoras.
        """
        for divisora in self.divisoras:
            divisora.liberar_por_item(id_item)

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime) -> None:
        for divisora in self.divisoras:
            divisora.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        for divisora in self.divisoras:
            divisora.liberar_todas_ocupacoes()

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda das Divisoras")
        logger.info("==============================================")
        for divisora in self.divisoras:
            divisora.mostrar_agenda()

    # ==========================================================
    # 📊 Status e Análise
    # ==========================================================
    def obter_status_divisoras(self) -> dict:
        """
        Retorna o status atual de todas as divisoras.
        """
        status = {}
        for divisora in self.divisoras:
            ocupacoes_ativas = [
                {
                    'id_ordem': oc[0],
                    'id_pedido': oc[1],
                    'id_atividade': oc[2],
                    'id_item': oc[3],
                    'quantidade': oc[4],
                    'usa_boleadora': oc[5],
                    'inicio': oc[6].strftime('%H:%M'),
                    'fim': oc[7].strftime('%H:%M')
                }
                for oc in divisora.ocupacoes
            ]
            
            status[divisora.nome] = {
                'capacidade_minima': divisora.capacidade_gramas_min,
                'capacidade_maxima': divisora.capacidade_gramas_max,
                'tem_boleadora': divisora.boleadora,
                'total_ocupacoes': len(divisora.ocupacoes),
                'ocupacoes_ativas': ocupacoes_ativas
            }
        
        return status

    def obter_detalhes_alocacao_atividade(self, atividade: "AtividadeModular") -> dict:
        """
        🔍 Retorna detalhes completos da alocação de uma atividade,
        incluindo informações de múltiplas divisoras se aplicável.
        """
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)
        
        detalhes = {
            'id_atividade': id_atividade,
            'id_item': id_item,
            'alocacao_multipla': len(atividade.equipamentos_selecionados) > 1 if hasattr(atividade, 'equipamentos_selecionados') else False,
            'divisoras_utilizadas': [],
            'quantidade_total': 0.0
        }
        
        # Coleta informações de todas as divisoras que processam esta atividade
        for divisora in self.divisoras:
            ocupacoes_atividade = [
                oc for oc in divisora.ocupacoes 
                if oc[0] == id_ordem and oc[1] == id_pedido and oc[2] == id_atividade
            ]
            
            if ocupacoes_atividade:
                quantidade_divisora = sum(oc[4] for oc in ocupacoes_atividade)
                detalhes['divisoras_utilizadas'].append({
                    'nome': divisora.nome,
                    'quantidade': quantidade_divisora,
                    'ocupacoes': len(ocupacoes_atividade),
                    'usa_boleadora': ocupacoes_atividade[0][5] if ocupacoes_atividade else False
                })
                detalhes['quantidade_total'] += quantidade_divisora
        
        return detalhes

    def listar_alocacoes_multiplas(self) -> List[dict]:
        """
        📊 Lista todas as atividades que utilizaram múltiplas divisoras.
        """
        alocacoes_multiplas = []
        atividades_processadas = set()
        
        for divisora in self.divisoras:
            for ocupacao in divisora.ocupacoes:
                id_ordem, id_pedido, id_atividade = ocupacao[0], ocupacao[1], ocupacao[2]
                chave_atividade = (id_ordem, id_pedido, id_atividade)
                
                if chave_atividade not in atividades_processadas:
                    # Conta quantas divisoras diferentes processam esta atividade
                    divisoras_atividade = []
                    quantidade_total = 0.0
                    
                    for d in self.divisoras:
                        ocupacoes_atividade = [
                            oc for oc in d.ocupacoes
                            if oc[0] == id_ordem and oc[1] == id_pedido and oc[2] == id_atividade
                        ]
                        if ocupacoes_atividade:
                            qtd_divisora = sum(oc[4] for oc in ocupacoes_atividade)
                            divisoras_atividade.append({
                                'nome': d.nome,
                                'quantidade': qtd_divisora
                            })
                            quantidade_total += qtd_divisora
                    
                    if len(divisoras_atividade) > 1:
                        alocacoes_multiplas.append({
                            'id_ordem': id_ordem,
                            'id_pedido': id_pedido,
                            'id_atividade': id_atividade,
                            'id_item': ocupacao[3],
                            'quantidade_total': quantidade_total,
                            'num_divisoras': len(divisoras_atividade),
                            'divisoras': divisoras_atividade,
                            'inicio': ocupacao[6].strftime('%H:%M [%d/%m]'),
                            'fim': ocupacao[7].strftime('%H:%M [%d/%m]')
                        })
                    
                    atividades_processadas.add(chave_atividade)
        
        return alocacoes_multiplas

    # ==========================================================
    # 🔍 MÉTODOS DE DEBUG INTEGRADOS
    # ==========================================================
    def _debug_estado_inicial(self, atividade: "AtividadeModular", quantidade_total: float, 
                            id_item: int, inicio: datetime, fim: datetime) -> None:
        """
        🔍 Debug completo do estado inicial antes de tentar alocar.
        """
        logger.info("=" * 70)
        logger.info("🔍 DEBUG - ESTADO INICIAL DAS DIVISORAS")
        logger.info("=" * 70)
        
        logger.info(f"🎯 TENTATIVA DE ALOCAÇÃO:")
        logger.info(f"   • Atividade: {atividade.id_atividade}")
        logger.info(f"   • Item ID: {id_item}")
        logger.info(f"   • Janela solicitada: {inicio.strftime('%H:%M')} - {fim.strftime('%H:%M')}")
        logger.info(f"   • Duração: {atividade.duracao}")
        logger.info(f"   • Quantidade: {quantidade_total}g")
        
        # Status de cada divisora
        logger.info(f"\n📊 STATUS DAS DIVISORAS:")
        for i, divisora in enumerate(self.divisoras, 1):
            logger.info(f"  🏭 {i}. {divisora.nome}:")
            logger.info(f"    • Capacidade: {divisora.capacidade_gramas_min}g - {divisora.capacidade_gramas_max}g")
            logger.info(f"    • Boleadora: {'Sim' if divisora.boleadora else 'Não'}")
            logger.info(f"    • Total ocupações: {len(divisora.ocupacoes)}")
            
            if divisora.ocupacoes:
                logger.info(f"    • Ocupações existentes:")
                for j, oc in enumerate(divisora.ocupacoes, 1):
                    logger.info(f"      {j}. Item {oc[3]}: {oc[4]}g | {oc[6].strftime('%H:%M')}-{oc[7].strftime('%H:%M')} | Ordem {oc[0]}, Pedido {oc[1]}")
            else:
                logger.info(f"    • ✅ Nenhuma ocupação registrada")
        
        # Capacidade total do sistema
        cap_disponivel, cap_teorica = self._calcular_capacidade_total_sistema(
            atividade, id_item, inicio, fim
        )
        
        logger.info(f"\n📈 CAPACIDADE DO SISTEMA:")
        logger.info(f"   • Capacidade teórica total: {cap_teorica}g")
        logger.info(f"   • Capacidade disponível: {cap_disponivel}g")
        logger.info(f"   • Quantidade solicitada: {quantidade_total}g")
        logger.info(f"   • Viável pelo sistema: {'✅ SIM' if cap_disponivel >= quantidade_total else '❌ NÃO'}")
        
        # Configuração JSON
        peso_json = self._obter_capacidade_explicita_do_json(atividade)
        logger.info(f"\n⚙️ CONFIGURAÇÃO JSON:")
        logger.info(f"   • Capacidade explícita no JSON: {peso_json}g" if peso_json else "   • Nenhuma capacidade definida no JSON")
        
        logger.info("=" * 70)

    def _debug_tentativa_detalhada(self, tentativa_num: int, atividade: "AtividadeModular", 
                                 quantidade_total: float, id_item: int, 
                                 inicio_tentativa: datetime, fim_tentativa: datetime) -> None:
        """
        🔍 Debug detalhado de uma tentativa específica de alocação.
        """
        logger.info(f"\n🔍 DEBUG TENTATIVA #{tentativa_num} - {inicio_tentativa.strftime('%H:%M')}-{fim_tentativa.strftime('%H:%M')}")
        
        # Teste de viabilidade
        viavel, motivo = self._verificar_viabilidade_quantidade(
            atividade, quantidade_total, id_item, inicio_tentativa, fim_tentativa
        )
        logger.info(f"   📊 Viabilidade: {'✅' if viavel else '❌'} - {motivo}")
        
        # Análise individual das divisoras
        divisoras_ordenadas = self._ordenar_por_fip(atividade)
        divisoras_disponiveis = []
        
        logger.info(f"   🏭 ANÁLISE POR DIVISORA:")
        for i, divisora in enumerate(divisoras_ordenadas, 1):
            # Teste de disponibilidade
            disponivel_item = divisora.esta_disponivel_para_item(inicio_tentativa, fim_tentativa, id_item)
            
            logger.info(f"     {i}. {divisora.nome}:")
            logger.info(f"        • Disponível para item {id_item}: {'✅' if disponivel_item else '❌'}")
            
            if disponivel_item:
                # Calcula capacidade disponível
                capacidade_gramas = self._obter_capacidade_explicita_do_json(atividade)
                cap_max = capacidade_gramas if capacidade_gramas else divisora.capacidade_gramas_max
                
                quantidade_atual = divisora.obter_quantidade_maxima_item_periodo(
                    id_item, inicio_tentativa, fim_tentativa
                )
                capacidade_disponivel = cap_max - quantidade_atual
                
                logger.info(f"        • Capacidade máxima: {cap_max}g")
                logger.info(f"        • Já ocupado (item {id_item}): {quantidade_atual}g")
                logger.info(f"        • Disponível: {capacidade_disponivel}g")
                logger.info(f"        • Aceita quantidade solicitada: {'✅' if capacidade_disponivel >= quantidade_total else '❌'}")
                
                if capacidade_disponivel >= divisora.capacidade_gramas_min:
                    divisoras_disponiveis.append((divisora, capacidade_disponivel))
                    logger.info(f"        • ✅ Adicionada à lista de disponíveis")
                else:
                    logger.info(f"        • ❌ Capacidade abaixo do mínimo ({divisora.capacidade_gramas_min}g)")
            else:
                # Análise detalhada do porquê não está disponível
                self._debug_indisponibilidade(divisora, id_item, inicio_tentativa, fim_tentativa)
        
        logger.info(f"   📋 RESULTADO: {len(divisoras_disponiveis)} divisoras disponíveis")

    def _debug_indisponibilidade(self, divisora: DivisoraDeMassas, id_item: int, 
                               inicio: datetime, fim: datetime) -> None:
        """
        🔍 Debug específico para entender por que uma divisora não está disponível.
        """
        logger.info(f"        🔍 ANÁLISE DE INDISPONIBILIDADE:")
        
        ocupacoes_conflitantes = []
        for ocupacao in divisora.ocupacoes:
            oc_item = ocupacao[3]
            oc_inicio = ocupacao[6]
            oc_fim = ocupacao[7]
            
            # Verifica sobreposição temporal
            tem_sobreposicao = not (fim <= oc_inicio or inicio >= oc_fim)
            
            if tem_sobreposicao:
                ocupacoes_conflitantes.append({
                    'item': oc_item,
                    'quantidade': ocupacao[4],
                    'inicio': oc_inicio,
                    'fim': oc_fim,
                    'mesmo_item': oc_item == id_item
                })
        
        if ocupacoes_conflitantes:
            logger.info(f"        • 🚨 {len(ocupacoes_conflitantes)} ocupações conflitantes:")
            for j, conf in enumerate(ocupacoes_conflitantes, 1):
                tipo = "MESMO ITEM" if conf['mesmo_item'] else "ITEM DIFERENTE"
                logger.info(f"          {j}. Item {conf['item']} ({tipo}): {conf['quantidade']}g")
                logger.info(f"             {conf['inicio'].strftime('%H:%M')}-{conf['fim'].strftime('%H:%M')}")
                
                # Análise temporal detalhada
                if conf['mesmo_item']:
                    logger.info(f"             • Problema: Mesmo item em horário diferente")
                    logger.info(f"             • Lógica atual: Só permite mesmo horário exato")
                else:
                    logger.info(f"             • Problema: Item diferente com sobreposição temporal")
        else:
            logger.info(f"        • 🤔 Nenhuma ocupação conflitante detectada - verificar lógica!")

    def _debug_falha_final(self, atividade: "AtividadeModular", quantidade_total: float, 
                         id_item: int, inicio: datetime, fim: datetime, tentativas: int) -> None:
        """
        🔍 Debug completo quando a alocação falha completamente.
        """
        logger.error("=" * 70)
        logger.error("🚨 DEBUG - FALHA COMPLETA NA ALOCAÇÃO")
        logger.error("=" * 70)
        
        logger.error(f"❌ RESUMO DA FALHA:")
        logger.error(f"   • Atividade: {atividade.id_atividade} (Item {id_item})")
        logger.error(f"   • Quantidade: {quantidade_total}g")
        logger.error(f"   • Janela original: {inicio.strftime('%H:%M')} - {fim.strftime('%H:%M')}")
        logger.error(f"   • Total de tentativas: {tentativas}")
        
        # Análise final do sistema
        cap_disponivel, cap_teorica = self._calcular_capacidade_total_sistema(
            atividade, id_item, inicio, fim
        )
        
        logger.error(f"\n📊 ANÁLISE FINAL DO SISTEMA:")
        logger.error(f"   • Capacidade teórica: {cap_teorica}g")
        logger.error(f"   • Capacidade disponível: {cap_disponivel}g")
        logger.error(f"   • Déficit: {quantidade_total - cap_disponivel}g")
        
        # Estado final das divisoras
        logger.error(f"\n🏭 ESTADO FINAL DAS DIVISORAS:")
        for divisora in self.divisoras:
            logger.error(f"   • {divisora.nome}: {len(divisora.ocupacoes)} ocupações")
            if divisora.ocupacoes:
                for oc in divisora.ocupacoes:
                    logger.error(f"     - Item {oc[3]}: {oc[4]}g ({oc[6].strftime('%H:%M')}-{oc[7].strftime('%H:%M')})")
        
        # Sugestões de solução
        logger.error(f"\n💡 SUGESTÕES PARA RESOLVER:")
        
        if cap_disponivel < quantidade_total:
            logger.error(f"   1. 🔧 CAPACIDADE INSUFICIENTE:")
            logger.error(f"      • Verificar se divisoras foram liberadas após pedidos anteriores")
            logger.error(f"      • Reduzir quantidade para teste (ex: 5000g)")
            logger.error(f"      • Verificar capacidades das divisoras vs JSON")
        
        if tentativas < 10:
            logger.error(f"   2. 🔧 POUCAS TENTATIVAS:")
            logger.error(f"      • Janela temporal muito restrita")
            logger.error(f"      • Aumentar janela ou reduzir duração da atividade")
        
        logger.error(f"   3. 🔧 VERIFICAÇÕES RECOMENDADAS:")
        logger.error(f"      • Executar: gestor.liberar_todas_ocupacoes()")
        logger.error(f"      • Testar com quantidade menor")
        logger.error(f"      • Verificar lógica temporal da classe DivisoraDeMassas")
        logger.error(f"      • Analisar método esta_disponivel_para_item()")
        
        logger.error("=" * 70)

    def _debug_teste_logica_temporal(self) -> None:
        """
        🧪 Teste isolado da lógica temporal para verificar bugs.
        """
        logger.info("\n🧪 TESTE DA LÓGICA TEMPORAL:")
        
        # Simula os horários do problema
        primeiro_inicio = datetime(2025, 6, 24, 17, 48)  # 17:48
        primeiro_fim = datetime(2025, 6, 24, 18, 0)      # 18:00
        
        segundo_inicio = datetime(2025, 6, 24, 8, 0)     # 08:00
        segundo_fim = datetime(2025, 6, 24, 8, 12)       # 08:12
        
        # Teste de sobreposição
        tem_sobreposicao = not (segundo_fim <= primeiro_inicio or segundo_inicio >= primeiro_fim)
        
        logger.info(f"   • Primeiro período (existente): {primeiro_inicio.strftime('%H:%M')}-{primeiro_fim.strftime('%H:%M')}")
        logger.info(f"   • Segundo período (tentativa): {segundo_inicio.strftime('%H:%M')}-{segundo_fim.strftime('%H:%M')}")
        logger.info(f"   • Há sobreposição temporal: {'❌ ERRO!' if tem_sobreposicao else '✅ CORRETO'}")
        
        # Testa a condição específica do código
        condicao_permite = (segundo_fim <= primeiro_inicio or segundo_inicio >= primeiro_fim)
        logger.info(f"   • Condição deveria permitir: {'✅ SIM' if condicao_permite else '❌ NÃO'}")
        
        if tem_sobreposicao:
            logger.error(f"   🚨 ERRO CRÍTICO: Períodos não deveriam se sobrepor!")
        else:
            logger.info(f"   ✅ Lógica temporal OK - períodos são independentes")

    # ==========================================================
    # 📊 Métodos de análise avançada
    # ==========================================================
    def verificar_disponibilidade(
        self,
        inicio: datetime,
        fim: datetime,
        id_item: Optional[int] = None,
        quantidade: Optional[float] = None
    ) -> List[DivisoraDeMassas]:
        """
        Verifica quais divisoras estão disponíveis no período para um item específico.
        """
        disponiveis = []
        
        for divisora in self.divisoras:
            if id_item is not None:
                if divisora.esta_disponivel_para_item(inicio, fim, id_item):
                    if quantidade is None:
                        disponiveis.append(divisora)
                    else:
                        # Verifica se pode adicionar a quantidade especificada
                        if divisora.validar_nova_ocupacao_item(id_item, quantidade, inicio, fim):
                            disponiveis.append(divisora)
            else:
                # Comportamento original para compatibilidade
                if divisora.esta_disponivel(inicio, fim):
                    if quantidade is None or divisora.validar_capacidade(quantidade):
                        disponiveis.append(divisora)
        
        return disponiveis

    def obter_capacidade_total_disponivel_item(self, id_item: int, inicio: datetime, fim: datetime) -> float:
        """
        📊 Calcula a capacidade total disponível para um item específico no período.
        """
        capacidade_total_disponivel = 0.0
        
        for divisora in self.divisoras:
            if divisora.esta_disponivel_para_item(inicio, fim, id_item):
                quantidade_atual = divisora.obter_quantidade_maxima_item_periodo(id_item, inicio, fim)
                capacidade_disponivel = divisora.capacidade_gramas_max - quantidade_atual
                capacidade_total_disponivel += max(0, capacidade_disponivel)
        
        return capacidade_total_disponivel