import unicodedata
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Dict, TYPE_CHECKING
from math import ceil
from models.equipamentos.fogao import Fogao
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular
from enums.equipamentos.tipo_chama import TipoChama
from enums.equipamentos.tipo_pressao_chama import TipoPressaoChama
from utils.logs.logger_factory import setup_logger

logger = setup_logger("GestorFogoes")


class GestorFogoes:
    """
    🎓 Gestor de Fogões com Algoritmos de Pesquisa Operacional Validados
    
    Baseado em:
    - Multiple Knapsack Problem para verificação de viabilidade
    - First Fit Decreasing (FFD) para distribuição ótima  
    - Binary Space Partitioning para balanceamento de cargas
    - Load Balancing para redistribuição eficiente
    - Backward Scheduling convencional
    - 🧪 Módulo de Teste Completo antes da execução
    
    Funcionalidades:
    - Verificação prévia de viabilidade total do sistema
    - Distribuição otimizada respeitando capacidades mín/máx
    - Priorização por FIP com balanceamento de carga
    - Soma quantidades do mesmo id_item em intervalos sobrepostos
    - Teste completo: divisão → validação → execução
    """
    
    def __init__(self, fogoes: List[Fogao]):
        self.fogoes = fogoes
        self.debug_mode = True

    # ==========================================================
    # 📊 Multiple Knapsack Problem - Verificação de Viabilidade
    # ==========================================================
    
    def _calcular_capacidade_total_sistema(
        self, 
        atividade: "AtividadeModular", 
        inicio: datetime, 
        fim: datetime
    ) -> Tuple[float, float]:
        """
        📚 Multiple Knapsack Problem (MKP): Calcula capacidade total disponível 
        considerando múltiplos "recipientes" (fogões) com capacidades limitadas.
        
        Retorna: (capacidade_disponivel, capacidade_maxima_teorica)
        """
        capacidade_disponivel_total = 0.0
        capacidade_maxima_teorica = 0.0
        
        for fogao in self.fogoes:
            # Verifica configurações
            tipo_chama = self._obter_tipo_chama_para_fogao(atividade, fogao)
            pressoes = self._obter_pressoes_chama_para_fogao(atividade, fogao)
            
            if tipo_chama is None or not pressoes:
                continue
            
            bocas_disponiveis = fogao.bocas_disponiveis_periodo(inicio, fim)
            capacidade_fogao = len(bocas_disponiveis) * fogao.capacidade_por_boca_gramas_max
            
            capacidade_disponivel_total += capacidade_fogao
            capacidade_maxima_teorica += fogao.numero_bocas * fogao.capacidade_por_boca_gramas_max
        
        return capacidade_disponivel_total, capacidade_maxima_teorica

    def _verificar_viabilidade_mkp(
        self, 
        atividade: "AtividadeModular", 
        quantidade_total: float,
        inicio: datetime, 
        fim: datetime
    ) -> Tuple[bool, str]:
        """
        Verificação de viabilidade usando princípios do Multiple Knapsack Problem
        """
        logger.warning(f"🎒 MKP: Verificando viabilidade para {quantidade_total}g")
        
        cap_disponivel, cap_teorica = self._calcular_capacidade_total_sistema(atividade, inicio, fim)
        
        logger.warning(f"🎒 Capacidade disponível: {cap_disponivel}g, teórica: {cap_teorica}g")
        
        if quantidade_total > cap_teorica:
            return False, f"Quantidade {quantidade_total}g excede capacidade máxima teórica ({cap_teorica}g)"
        
        if quantidade_total > cap_disponivel:
            return False, f"Quantidade {quantidade_total}g excede capacidade disponível ({cap_disponivel}g)"
        
        # Verifica se é possível respeitar capacidades mínimas
        fogoes_elegiveis = []
        for fogao in self.fogoes:
            tipo_chama = self._obter_tipo_chama_para_fogao(atividade, fogao)
            pressoes = self._obter_pressoes_chama_para_fogao(atividade, fogao)
            
            if tipo_chama is not None and pressoes:
                bocas_disponiveis = fogao.bocas_disponiveis_periodo(inicio, fim)
                if bocas_disponiveis:
                    fogoes_elegiveis.append(fogao)
        
        if not fogoes_elegiveis:
            return False, "Nenhum fogão elegível encontrado"
        
        # Verifica capacidade mínima global
        capacidade_min_global = min(f.capacidade_por_boca_gramas_min for f in fogoes_elegiveis)
        
        if quantidade_total < capacidade_min_global:
            return False, f"Quantidade {quantidade_total}g abaixo do mínimo por boca ({capacidade_min_global}g)"
        
        logger.warning(f"✅ MKP: Viabilidade confirmada com {len(fogoes_elegiveis)} fogões elegíveis")
        return True, "Sistema viável"

    # ==========================================================
    # 🧪 MÓDULO DE TESTE COMPLETO - Simulação Antes da Execução
    # ==========================================================
    
    def _testar_distribuicao_completa(
        self,
        quantidade_total: float,
        fogoes_disponiveis: List[Tuple[Fogao, float]],
        atividade: "AtividadeModular",
        inicio: datetime,
        fim: datetime
    ) -> Optional[List[Dict]]:
        """
        🧪 Módulo de teste completo que simula toda a operação:
        1. Testa divisão da quantidade entre fogões
        2. Valida distribuição nas bocas de cada fogão  
        3. Verifica se todas as bocas atendem limites mín/máx
        4. Retorna plano de alocação detalhado ou None se inviável
        
        Retorna: Lista de dicts com plano completo de alocação ou None
        """
        logger.warning(f"🧪 TESTE: Simulando distribuição completa de {quantidade_total}g")
        
        if not fogoes_disponiveis:
            logger.warning(f"❌ TESTE: Nenhum fogão disponível")
            return None
        
        # Fase 1: Testa múltiplas estratégias de distribuição
        estrategias_teste = [
            ("proporcional", self._testar_distribuicao_proporcional),
            ("ffd_melhorado", self._testar_distribuicao_ffd_melhorada),
            ("balanceada", self._testar_distribuicao_balanceada)
        ]
        
        for nome_estrategia, funcao_teste in estrategias_teste:
            logger.warning(f"🧪 Testando estratégia: {nome_estrategia}")
            
            plano_alocacao = funcao_teste(quantidade_total, fogoes_disponiveis, atividade, inicio, fim)
            
            if plano_alocacao:
                logger.warning(f"✅ TESTE: Estratégia {nome_estrategia} APROVADA")
                return plano_alocacao
            else:
                logger.warning(f"❌ TESTE: Estratégia {nome_estrategia} REJEITADA")
        
        logger.warning(f"❌ TESTE: Todas as estratégias falharam")
        return None
    
    def _testar_distribuicao_proporcional(
        self,
        quantidade_total: float,
        fogoes_disponiveis: List[Tuple[Fogao, float]],
        atividade: "AtividadeModular",
        inicio: datetime,
        fim: datetime
    ) -> Optional[List[Dict]]:
        """Testa distribuição proporcional pura"""
        capacidade_total = sum(cap for _, cap in fogoes_disponiveis)
        plano = []
        
        for fogao, cap_disponivel in fogoes_disponiveis:
            proporcao = cap_disponivel / capacidade_total
            quantidade_fogao = quantidade_total * proporcao
            
            # Testa se quantidade atende mínimo
            if quantidade_fogao < fogao.capacidade_por_boca_gramas_min:
                logger.warning(f"   ❌ {fogao.nome}: {quantidade_fogao:.1f}g < mínimo {fogao.capacidade_por_boca_gramas_min}g")
                return None
            
            # Testa distribuição nas bocas
            plano_fogao = self._testar_distribuicao_bocas_fogao(
                fogao, quantidade_fogao, atividade, inicio, fim
            )
            
            if not plano_fogao:
                logger.warning(f"   ❌ {fogao.nome}: falha na distribuição das bocas")
                return None
            
            plano.extend(plano_fogao)
            logger.warning(f"   ✅ {fogao.nome}: {quantidade_fogao:.1f}g em {len(plano_fogao)} bocas")
        
        return plano
    
    def _testar_distribuicao_ffd_melhorada(
        self,
        quantidade_total: float,
        fogoes_disponiveis: List[Tuple[Fogao, float]],
        atividade: "AtividadeModular",
        inicio: datetime,
        fim: datetime
    ) -> Optional[List[Dict]]:
        """Testa FFD com redistribuição inteligente de sobras"""
        fogoes_ordenados = sorted(fogoes_disponiveis, key=lambda x: x[1], reverse=True)
        plano = []
        quantidade_restante = quantidade_total
        
        # Distribui sequencialmente, mas deixa espaço para o último
        for i, (fogao, cap_disponivel) in enumerate(fogoes_ordenados):
            if quantidade_restante <= 0:
                break
            
            if i == len(fogoes_ordenados) - 1:
                # Último fogão: recebe tudo que sobrou
                quantidade_fogao = quantidade_restante
            else:
                # Calcula quanto pode alocar sem inviabilizar o último
                fogoes_restantes = fogoes_ordenados[i+1:]
                capacidade_min_restantes = min(f.capacidade_por_boca_gramas_min for f, _ in fogoes_restantes)
                
                # Deixa pelo menos o mínimo para os próximos
                quantidade_maxima = quantidade_restante - capacidade_min_restantes
                quantidade_fogao = min(cap_disponivel, quantidade_maxima)
            
            # Testa se quantidade é viável
            if quantidade_fogao < fogao.capacidade_por_boca_gramas_min:
                logger.warning(f"   ❌ FFD: {fogao.nome} ficaria com {quantidade_fogao:.1f}g < mínimo")
                return None
            
            # Testa distribuição nas bocas
            plano_fogao = self._testar_distribuicao_bocas_fogao(
                fogao, quantidade_fogao, atividade, inicio, fim
            )
            
            if not plano_fogao:
                logger.warning(f"   ❌ FFD: {fogao.nome} falha na distribuição das bocas")
                return None
            
            plano.extend(plano_fogao)
            quantidade_restante -= quantidade_fogao
            logger.warning(f"   ✅ FFD: {fogao.nome} {quantidade_fogao:.1f}g, restam {quantidade_restante:.1f}g")
        
        if quantidade_restante > 1:
            logger.warning(f"   ❌ FFD: Restaram {quantidade_restante:.1f}g não alocados")
            return None
        
        return plano
    
    def _testar_distribuicao_balanceada(
        self,
        quantidade_total: float,
        fogoes_disponiveis: List[Tuple[Fogao, float]],
        atividade: "AtividadeModular",
        inicio: datetime,
        fim: datetime
    ) -> Optional[List[Dict]]:
        """Testa distribuição balanceada com ajuste iterativo"""
        # Inicia com distribuição uniforme simples
        num_fogoes = len(fogoes_disponiveis)
        quantidade_media = quantidade_total / num_fogoes
        
        plano = []
        quantidade_distribuida = 0
        
        for i, (fogao, cap_disponivel) in enumerate(fogoes_disponiveis):
            if i == len(fogoes_disponiveis) - 1:
                # Último fogão: recebe o que sobrou para garantir total exato
                quantidade_fogao = quantidade_total - quantidade_distribuida
            else:
                # Ajusta quantidade média para limites do fogão
                quantidade_fogao = max(
                    fogao.capacidade_por_boca_gramas_min,
                    min(quantidade_media, cap_disponivel)
                )
            
            # Testa se quantidade é viável
            if quantidade_fogao < fogao.capacidade_por_boca_gramas_min:
                logger.warning(f"   ❌ Balanceada: {fogao.nome} ficaria com {quantidade_fogao:.1f}g < mínimo")
                return None
            
            if quantidade_fogao > cap_disponivel:
                logger.warning(f"   ❌ Balanceada: {fogao.nome} ficaria com {quantidade_fogao:.1f}g > capacidade {cap_disponivel}g")
                return None
            
            # Testa distribuição nas bocas
            plano_fogao = self._testar_distribuicao_bocas_fogao(
                fogao, quantidade_fogao, atividade, inicio, fim
            )
            
            if not plano_fogao:
                logger.warning(f"   ❌ Balanceada: {fogao.nome} falha na distribuição das bocas")
                return None
            
            plano.extend(plano_fogao)
            quantidade_distribuida += quantidade_fogao
            logger.warning(f"   ✅ Balanceada: {fogao.nome} {quantidade_fogao:.1f}g")
        
        # Verifica se quantidade total está correta
        if abs(quantidade_distribuida - quantidade_total) > 1:
            logger.warning(f"   ❌ Balanceada: diferença {abs(quantidade_distribuida - quantidade_total):.1f}g")
            return None
        
        return plano
    
    def _testar_distribuicao_bocas_fogao(
        self,
        fogao: Fogao,
        quantidade_fogao: float,
        atividade: "AtividadeModular",
        inicio: datetime,
        fim: datetime
    ) -> Optional[List[Dict]]:
        """
        Testa distribuição da quantidade nas bocas de um fogão específico
        
        Retorna: Lista de alocações por boca ou None se inviável
        """
        bocas_disponiveis = fogao.bocas_disponiveis_periodo(inicio, fim)
        
        if not bocas_disponiveis:
            return None
        
        # Calcula bocas necessárias
        bocas_necessarias = ceil(quantidade_fogao / fogao.capacidade_por_boca_gramas_max)
        bocas_necessarias = min(bocas_necessarias, len(bocas_disponiveis))
        
        # Testa se é possível distribuir
        if quantidade_fogao < bocas_necessarias * fogao.capacidade_por_boca_gramas_min:
            return None
        if quantidade_fogao > bocas_necessarias * fogao.capacidade_por_boca_gramas_max:
            return None
        
        # Calcula distribuição entre bocas
        distribuicao_bocas = self._distribuir_quantidade_entre_bocas(
            quantidade_fogao, bocas_necessarias,
            fogao.capacidade_por_boca_gramas_min, fogao.capacidade_por_boca_gramas_max
        )
        
        if not distribuicao_bocas:
            return None
        
        # Cria plano de alocação detalhado
        plano_fogao = []
        tipo_chama = self._obter_tipo_chama_para_fogao(atividade, fogao)
        pressoes = self._obter_pressoes_chama_para_fogao(atividade, fogao)
        
        for i, quantidade_boca in enumerate(distribuicao_bocas):
            boca_idx = bocas_disponiveis[i]
            
            plano_fogao.append({
                'fogao': fogao,
                'boca_idx': boca_idx,
                'quantidade': quantidade_boca,
                'tipo_chama': tipo_chama,
                'pressoes': pressoes,
                'inicio': inicio,
                'fim': fim
            })
        
        return plano_fogao
    
    def _executar_plano_alocacao(
        self,
        plano_alocacao: List[Dict],
        atividade: "AtividadeModular"
    ) -> bool:
        """
        Executa o plano de alocação testado e aprovado
        """
        logger.warning(f"🚀 EXECUTANDO plano com {len(plano_alocacao)} alocações")
        
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)
        alocacoes_realizadas = []
        
        try:
            for i, alocacao in enumerate(plano_alocacao):
                fogao = alocacao['fogao']
                boca_idx = alocacao['boca_idx']
                quantidade = alocacao['quantidade']
                tipo_chama = alocacao['tipo_chama']
                pressoes = alocacao['pressoes']
                inicio = alocacao['inicio']
                fim = alocacao['fim']
                
                logger.warning(f"   🎯 {i+1}/{len(plano_alocacao)}: {fogao.nome} Boca {boca_idx} = {quantidade:.1f}g")
                
                sucesso = fogao.adicionar_ocupacao_boca(
                    boca_index=boca_idx,
                    id_ordem=id_ordem,
                    id_pedido=id_pedido,
                    id_atividade=id_atividade,
                    id_item=id_item,
                    quantidade_alocada=quantidade,
                    tipo_chama=tipo_chama,
                    pressoes_chama=pressoes,
                    inicio=inicio,
                    fim=fim
                )
                
                if not sucesso:
                    raise Exception(f"Falha na alocação {fogao.nome} Boca {boca_idx}")
                
                alocacoes_realizadas.append(alocacao)
            
            # Atualiza atividade
            fogoes_utilizados = list(set(a['fogao'] for a in plano_alocacao))
            
            atividade.equipamentos_selecionados = fogoes_utilizados
            atividade.equipamento_alocado = fogoes_utilizados[0] if len(fogoes_utilizados) == 1 else fogoes_utilizados
            atividade.alocada = True
            
            logger.warning(f"✅ EXECUÇÃO COMPLETA: {len(fogoes_utilizados)} fogões utilizados")
            return True
            
        except Exception as e:
            logger.error(f"❌ ERRO NA EXECUÇÃO: {e}")
            
            # Rollback de todas as alocações realizadas
            logger.warning(f"🔄 ROLLBACK: Desfazendo {len(alocacoes_realizadas)} alocações")
            for alocacao in alocacoes_realizadas:
                fogao = alocacao['fogao']
                fogao.liberar_por_atividade(id_ordem, id_pedido, id_atividade)
            
            return False

    # ==========================================================
    # 🎯 Alocação Principal com Backward Scheduling
    # ==========================================================
    
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade_produto: int,
        **kwargs
    ) -> Tuple[bool, Optional[Fogao], Optional[datetime], Optional[datetime]]:
        """
        Alocação otimizada com algoritmos de pesquisa operacional e backward scheduling convencional
        """
        duracao = atividade.duracao
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)
        quantidade_total = float(quantidade_produto)
        
        logger.info(f"🎯 Iniciando alocação acadêmica: {quantidade_total}g")
        logger.info(f"📅 Janela: {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}")
        
        # Tenta primeiro agrupamento por id_item
        sucesso_agrupamento = self._tentar_agrupamento_id_item(
            atividade, quantidade_total, inicio, fim, id_ordem, id_pedido, id_atividade, id_item
        )
        
        if sucesso_agrupamento:
            return sucesso_agrupamento
        
        # Backward scheduling convencional
        horario_final_tentativa = fim
        
        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao
            
            # Fase 1: Verificação MKP
            viavel, motivo = self._verificar_viabilidade_mkp(
                atividade, quantidade_total, horario_inicio_tentativa, horario_final_tentativa
            )
            
            if not viavel:
                logger.debug(f"❌ MKP inviável em {horario_inicio_tentativa.strftime('%H:%M')}: {motivo}")
                horario_final_tentativa -= timedelta(minutes=1)
                continue
            
            # Fase 2: Identifica fogões disponíveis
            fogoes_disponiveis = self._obter_fogoes_disponiveis(
                atividade, horario_inicio_tentativa, horario_final_tentativa
            )
            
            if not fogoes_disponiveis:
                horario_final_tentativa -= timedelta(minutes=1)
                continue
            
            # Fase 3: Tenta alocação em fogão único (otimização)
            for fogao, cap_disponivel in fogoes_disponiveis:
                if cap_disponivel >= quantidade_total:
                    sucesso = self._tentar_alocacao_individual(
                        fogao, atividade, quantidade_total,
                        horario_inicio_tentativa, horario_final_tentativa
                    )
                    if sucesso:
                        logger.info(f"✅ Alocação individual: {fogao.nome}")
                        return True, fogao, horario_inicio_tentativa, horario_final_tentativa
            
            # Fase 4: Usa módulo de teste completo para distribuição múltipla
            sucesso_multipla = self._tentar_alocacao_multipla_com_teste(
                quantidade_total, fogoes_disponiveis, atividade, 
                horario_inicio_tentativa, horario_final_tentativa
            )
            
            if sucesso_multipla:
                fogoes_utilizados = sucesso_multipla
                logger.info(f"✅ Alocação múltipla: {[f.nome for f in fogoes_utilizados]}")
                return True, fogoes_utilizados, horario_inicio_tentativa, horario_final_tentativa
            
            horario_final_tentativa -= timedelta(minutes=1)
        
        logger.error(f"❌ Falha na alocação após backward scheduling completo")
        return False, None, None, None

    def _tentar_alocacao_multipla_com_teste(
        self,
        quantidade_total: float,
        fogoes_disponiveis: List[Tuple[Fogao, float]],
        atividade: "AtividadeModular",
        inicio: datetime,
        fim: datetime
    ) -> Optional[List[Fogao]]:
        """
        🧪 Usa módulo de teste completo para alocação múltipla
        """
        logger.warning(f"🧪 INICIANDO TESTE COMPLETO para alocação múltipla")
        
        # Usa módulo de teste completo
        plano_alocacao = self._testar_distribuicao_completa(
            quantidade_total, fogoes_disponiveis, atividade, inicio, fim
        )
        
        if not plano_alocacao:
            logger.warning(f"❌ TESTE: Nenhuma estratégia de distribuição foi aprovada")
            return None
        
        # Se teste passou, executa o plano
        sucesso = self._executar_plano_alocacao(plano_alocacao, atividade)
        
        if sucesso:
            fogoes_utilizados = list(set(a['fogao'] for a in plano_alocacao))
            return fogoes_utilizados
        
        return None

    # ==========================================================
    # 🔄 Agrupamento por ID Item
    # ==========================================================
    
    def _tentar_agrupamento_id_item(
        self,
        atividade: "AtividadeModular",
        quantidade_adicional: float,
        inicio: datetime,
        fim: datetime,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int
    ) -> Optional[Tuple[bool, Fogao, datetime, datetime]]:
        """
        Tenta agrupar com ocupações existentes do mesmo id_item em intervalos sobrepostos
        """
        logger.warning(f"🔄 Tentando agrupamento para id_item {id_item}")
        
        for fogao in self.fogoes:
            for boca_idx in range(fogao.numero_bocas):
                for ocupacao in fogao.ocupacoes_por_boca[boca_idx]:
                    (_, _, _, id_i_exist, qtd_exist, _, _, ini_exist, fim_exist) = ocupacao
                    
                    # Mesmo item?
                    if id_i_exist != id_item:
                        continue
                    
                    # Verifica sobreposição temporal
                    if not (fim_exist <= inicio or ini_exist >= fim):
                        # Há sobreposição - verifica se pode somar
                        quantidade_total = qtd_exist + quantidade_adicional
                        
                        if quantidade_total <= fogao.capacidade_por_boca_gramas_max:
                            # Calcula novo período (união dos intervalos)
                            novo_inicio = min(inicio, ini_exist)
                            novo_fim = max(fim, fim_exist)
                            
                            # Atualiza ocupação existente
                            sucesso = self._atualizar_ocupacao_existente(
                                fogao, boca_idx, quantidade_total, novo_inicio, novo_fim,
                                id_ordem, id_pedido, id_atividade, id_item, ocupacao
                            )
                            
                            if sucesso:
                                logger.info(f"✅ Agrupamento realizado: {fogao.nome} Boca {boca_idx+1}")
                                return True, fogao, novo_inicio, novo_fim
        
        logger.warning(f"📊 Nenhum agrupamento disponível para id_item {id_item}")
        return None

    def _atualizar_ocupacao_existente(
        self,
        fogao: Fogao,
        boca_idx: int,
        nova_quantidade: float,
        novo_inicio: datetime,
        novo_fim: datetime,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int,
        ocupacao_original: tuple
    ) -> bool:
        """Atualiza ocupação existente com nova quantidade e período"""
        try:
            # Remove ocupação original
            fogao.ocupacoes_por_boca[boca_idx].remove(ocupacao_original)
            
            # Obtém configurações da ocupação original
            tipo_chama = ocupacao_original[5]
            pressoes = ocupacao_original[6]
            
            # Adiciona nova ocupação atualizada
            fogao.ocupacoes_por_boca[boca_idx].append((
                id_ordem, id_pedido, id_atividade, id_item, nova_quantidade,
                tipo_chama, pressoes, novo_inicio, novo_fim
            ))
            
            return True
        except Exception as e:
            logger.error(f"❌ Erro ao atualizar ocupação: {e}")
            return False

    # ==========================================================
    # 🔧 Métodos Auxiliares
    # ==========================================================
    
    def _obter_fogoes_disponiveis(
        self, 
        atividade: "AtividadeModular", 
        inicio: datetime, 
        fim: datetime
    ) -> List[Tuple[Fogao, float]]:
        """Obtém fogões disponíveis com suas capacidades"""
        fogoes_disponiveis = []
        fogoes_ordenados = self._ordenar_por_fip(atividade)
        
        for fogao in fogoes_ordenados:
            tipo_chama = self._obter_tipo_chama_para_fogao(atividade, fogao)
            pressoes = self._obter_pressoes_chama_para_fogao(atividade, fogao)
            
            if tipo_chama is not None and pressoes:
                bocas_disponiveis = fogao.bocas_disponiveis_periodo(inicio, fim)
                if bocas_disponiveis:
                    capacidade_disponivel = len(bocas_disponiveis) * fogao.capacidade_por_boca_gramas_max
                    fogoes_disponiveis.append((fogao, capacidade_disponivel))
        
        return fogoes_disponiveis

    def _tentar_alocacao_individual(
        self,
        fogao: Fogao,
        atividade: "AtividadeModular",
        quantidade: float,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """Tenta alocação em um único fogão"""
        tipo_chama = self._obter_tipo_chama_para_fogao(atividade, fogao)
        pressoes = self._obter_pressoes_chama_para_fogao(atividade, fogao)
        
        bocas_necessarias = ceil(quantidade / fogao.capacidade_por_boca_gramas_max)
        bocas_disponiveis = fogao.bocas_disponiveis_periodo(inicio, fim)
        
        if len(bocas_disponiveis) < bocas_necessarias:
            return False
        
        # Distribui quantidade entre bocas
        distribuicao = self._distribuir_quantidade_entre_bocas(
            quantidade, bocas_necessarias,
            fogao.capacidade_por_boca_gramas_min, fogao.capacidade_por_boca_gramas_max
        )
        
        if not distribuicao:
            return False
        
        # Executa alocação
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)
        
        for i, qtd_boca in enumerate(distribuicao):
            boca_idx = bocas_disponiveis[i]
            
            sucesso = fogao.adicionar_ocupacao_boca(
                boca_index=boca_idx,
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                id_atividade=id_atividade,
                id_item=id_item,
                quantidade_alocada=qtd_boca,
                tipo_chama=tipo_chama,
                pressoes_chama=pressoes,
                inicio=inicio,
                fim=fim
            )
            
            if not sucesso:
                return False
        
        # Atualiza atividade
        atividade.equipamento_alocado = fogao
        atividade.equipamentos_selecionados = [fogao]
        atividade.alocada = True
        
        return True

    def _distribuir_quantidade_entre_bocas(
        self, 
        quantidade_total: float, 
        num_bocas: int,
        capacidade_min: float, 
        capacidade_max: float
    ) -> List[float]:
        """Distribui quantidade entre bocas respeitando limites"""
        if num_bocas <= 0:
            return []
        
        if quantidade_total < num_bocas * capacidade_min:
            return []
        if quantidade_total > num_bocas * capacidade_max:
            return []
        
        distribuicao = []
        quantidade_restante = quantidade_total
        
        for i in range(num_bocas):
            bocas_restantes = num_bocas - i
            
            if bocas_restantes == 1:
                quantidade_boca = quantidade_restante
            else:
                max_nesta_boca = min(
                    capacidade_max,
                    quantidade_restante - (bocas_restantes - 1) * capacidade_min
                )
                quantidade_boca = min(quantidade_restante, max_nesta_boca)
            
            if quantidade_boca < capacidade_min or quantidade_boca > capacidade_max:
                return []
            
            distribuicao.append(quantidade_boca)
            quantidade_restante -= quantidade_boca
        
        return distribuicao

    # ==========================================================
    # 🔧 Métodos de Configuração (do código original)
    # ==========================================================
    
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[Fogao]:
        """Ordena fogões por FIP (menor = maior prioridade)"""
        return sorted(self.fogoes, key=lambda f: atividade.fips_equipamentos.get(f, 999))

    def _obter_ids_atividade(self, atividade: "AtividadeModular") -> Tuple[int, int, int, int]:
        """Extrai IDs da atividade"""
        id_ordem = getattr(atividade, 'id_ordem', 0)
        id_pedido = getattr(atividade, 'id_pedido', 0) 
        id_atividade = getattr(atividade, 'id_atividade', 0)
        id_item = getattr(atividade, 'id_item', getattr(atividade, 'id_produto', 0))
        return id_ordem, id_pedido, id_atividade, id_item

    def _obter_tipo_chama_para_fogao(self, atividade: "AtividadeModular", fogao: Fogao) -> Optional[TipoChama]:
        """Obtém tipo de chama do JSON de configurações"""
        try:
            chave = unicodedata.normalize("NFKD", fogao.nome.lower()).encode("ASCII", "ignore").decode().replace(" ", "_")
            config = getattr(atividade, "configuracoes_equipamentos", {}).get(chave, {})
            tipo_chama_raw = config.get("tipo_chama")
            
            if not tipo_chama_raw:
                return None
                
            if isinstance(tipo_chama_raw, list):
                tipo_chama_raw = tipo_chama_raw[0] if tipo_chama_raw else None
                
            if not tipo_chama_raw:
                return None
                
            return TipoChama[tipo_chama_raw.upper()]
        except Exception:
            return None

    def _obter_pressoes_chama_para_fogao(self, atividade: "AtividadeModular", fogao: Fogao) -> List[TipoPressaoChama]:
        """Obtém pressões de chama do JSON de configurações"""
        try:
            chave = unicodedata.normalize("NFKD", fogao.nome.lower()).encode("ASCII", "ignore").decode().replace(" ", "_")
            config = getattr(atividade, "configuracoes_equipamentos", {}).get(chave, {})
            pressoes_raw = config.get("pressao_chama", [])
            
            if isinstance(pressoes_raw, str):
                pressoes_raw = [pressoes_raw]
                
            pressoes = []
            for p in pressoes_raw:
                try:
                    pressoes.append(TipoPressaoChama[p.upper()])
                except Exception:
                    pass
            
            return pressoes
        except Exception:
            return []

    # ==========================================================
    # 🔓 Métodos de Liberação
    # ==========================================================
    
    def liberar_por_atividade(self, atividade: "AtividadeModular"):
        """Libera ocupações por atividade"""
        id_ordem, id_pedido, id_atividade, _ = self._obter_ids_atividade(atividade)
        for fogao in self.fogoes:
            fogao.liberar_por_atividade(id_ordem, id_pedido, id_atividade)
    
    def liberar_por_pedido(self, atividade: "AtividadeModular"):
        """Libera ocupações por pedido"""
        id_ordem, id_pedido, _, _ = self._obter_ids_atividade(atividade)
        for fogao in self.fogoes:
            fogao.liberar_por_pedido(id_ordem, id_pedido)

    def liberar_todas_ocupacoes(self):
        """Libera todas as ocupações"""
        for fogao in self.fogoes:
            fogao.liberar_todas_ocupacoes()

    def mostrar_agenda(self):
        """Mostra agenda de todos os fogões"""
        logger.info("📅 Agenda dos Fogões")
        for fogao in self.fogoes:
            fogao.mostrar_agenda()