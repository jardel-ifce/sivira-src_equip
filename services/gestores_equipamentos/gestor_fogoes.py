import unicodedata
from datetime import datetime, timedelta
from typing import List, Optional, Tuple, TYPE_CHECKING
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
    🔥 Gerenciador de fogões com algoritmo de escalabilidade e agrupamento.
    Utiliza backward scheduling com teste de viabilidade antes de alocar.
    Suporta alocação individual, combinações múltiplas e agrupamento por compatibilidade.
    Respeita capacidades mínimas e máximas por boca.
    """
    
    def __init__(self, fogoes: List[Fogao]):
        self.fogoes = fogoes
        self.debug_mode = True  # Ativar debug por padrão

    # ==========================================================
    # 🔄 MÉTODOS DE AGRUPAMENTO
    # ==========================================================
    def encontrar_ocupacao_compativel(
        self, 
        atividade: "AtividadeModular", 
        quantidade_adicional: int,
        inicio: datetime, 
        fim: datetime
    ) -> Optional[Tuple[Fogao, int, float]]:
        """
        Encontra uma ocupação existente compatível onde pode adicionar mais quantidade
        
        Critérios de compatibilidade:
        - Mesmo período temporal (início e fim exatos)
        - Mesma duração
        - Mesmo id_item
        - Espaço disponível na boca
        
        Returns: (fogao, boca_index, quantidade_atual) ou None
        """
        
        duracao_atividade = atividade.duracao
        id_item_atividade = getattr(atividade, 'id_item', getattr(atividade, 'id_produto', 0))
        
        for fogao in self.fogoes:
            for boca_idx in range(fogao.numero_bocas):
                # Verificar todas as ocupações desta boca
                for ocupacao in fogao.ocupacoes_por_boca[boca_idx]:
                    (id_o_exist, id_p_exist, id_a_exist, id_i_exist, qtd_exist, chama_exist, pressoes_exist, ini_exist, fim_exist) = ocupacao
                    
                    # CRITÉRIO 1: Sobreposição temporal exata
                    if ini_exist != inicio or fim_exist != fim:
                        continue
                    
                    # CRITÉRIO 2: Mesma duração (fim - início)
                    duracao_existente = fim_exist - ini_exist
                    if duracao_existente != duracao_atividade:
                        continue
                    
                    # CRITÉRIO 3: Mesmo id_item (produto/subproduto)
                    if id_i_exist != id_item_atividade:
                        continue
                    
                    # CRITÉRIO 4: Verificar se há espaço para mais quantidade
                    quantidade_total_seria = qtd_exist + quantidade_adicional
                    
                    if quantidade_total_seria <= fogao.capacidade_por_boca_gramas_max:
                        if self.debug_mode:
                            logger.debug(
                                f"🔍 Compatibilidade encontrada: {fogao.nome} Boca {boca_idx+1} | "
                                f"Atual: {qtd_exist}g + Nova: {quantidade_adicional}g = {quantidade_total_seria}g"
                            )
                        return fogao, boca_idx, qtd_exist
        
        return None

    def atualizar_ocupacao_existente(
        self,
        fogao: Fogao,
        boca_idx: int,
        atividade: "AtividadeModular",
        nova_quantidade_total: float,
        inicio: datetime,
        fim: datetime,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int
    ) -> bool:
        """
        Atualiza uma ocupação existente combinando com nova quantidade
        """
        
        # Encontrar a ocupação específica para atualizar
        for i, ocupacao in enumerate(fogao.ocupacoes_por_boca[boca_idx]):
            (id_o_exist, id_p_exist, id_a_exist, id_i_exist, qtd_exist, chama_exist, pressoes_exist, ini_exist, fim_exist) = ocupacao
            
            if (ini_exist == inicio and fim_exist == fim and id_i_exist == id_item):
                
                # Remover ocupação antiga
                ocupacao_removida = fogao.ocupacoes_por_boca[boca_idx].pop(i)
                
                # Adicionar ocupação atualizada (mantém as configurações originais)
                fogao.ocupacoes_por_boca[boca_idx].append((
                    id_ordem,  # ← Ordem do novo pedido (mais recente)
                    id_pedido, # ← Pedido do novo pedido (mais recente)
                    id_atividade,
                    id_item,
                    nova_quantidade_total,  # ← Quantidade combinada
                    chama_exist,    # ← Mantém configurações originais
                    pressoes_exist, # ← Mantém configurações originais
                    inicio,
                    fim
                ))
                
                logger.info(
                    f"🔄 Agrupamento realizado: {fogao.nome} Boca {boca_idx+1} | "
                    f"Quantidade anterior: {qtd_exist:.0f}g → Nova: {nova_quantidade_total:.0f}g | "
                    f"Pedidos combinados: {id_p_exist} + {id_pedido}"
                )
                
                return True
        
        return False

    # ==========================================================
    # 🐛 MÉTODOS DE DEBUG
    # ==========================================================
    def debug_mapeamento_nomes_fogoes(self, atividade: "AtividadeModular"):
        """Debug do mapeamento de nomes entre JSON e objetos"""
        if not self.debug_mode:
            return
            
        print("🔍 DEBUG - Mapeamento de Nomes dos Fogões:")
        print("=" * 60)
        
        # Configurações da atividade
        config_equipamentos = getattr(atividade, "configuracoes_equipamentos", {})
        print(f"📋 Configurações no JSON: {list(config_equipamentos.keys())}")
        
        for fogao in self.fogoes:
            print(f"\n🔥 FOGÃO: {fogao.nome}")
            
            # Processo de normalização (igual ao código original)
            chave_normalizada = unicodedata.normalize("NFKD", fogao.nome.lower()).encode("ASCII", "ignore").decode().replace(" ", "_")
            print(f"   📝 Nome original: '{fogao.nome}'")
            print(f"   🔑 Chave normalizada: '{chave_normalizada}'")
            
            # Verifica se existe configuração
            config_fogao = config_equipamentos.get(chave_normalizada, {})
            print(f"   ⚙️ Configuração encontrada: {config_fogao}")
            
            # Testa obtenção de tipo de chama
            tipo_chama_raw = config_fogao.get("tipo_chama")
            print(f"   🔥 tipo_chama raw: {tipo_chama_raw} (tipo: {type(tipo_chama_raw)})")
            
            if tipo_chama_raw:
                # Simula o processo do código original
                if isinstance(tipo_chama_raw, list):
                    tipo_chama_raw = tipo_chama_raw[0] if tipo_chama_raw else None
                    print(f"   🔥 Após extrair da lista: {tipo_chama_raw}")
                
                if tipo_chama_raw:
                    try:
                        tipo_chama = TipoChama[tipo_chama_raw.upper()]
                        print(f"   ✅ TipoChama obtido: {tipo_chama}")
                    except Exception as e:
                        print(f"   ❌ Erro ao converter TipoChama: {e}")
                else:
                    print(f"   ❌ tipo_chama_raw é None após processamento")
            else:
                print(f"   ❌ Não encontrou tipo_chama na configuração")
            
            # Testa obtenção de pressões
            pressoes_raw = config_fogao.get("pressao_chama", [])
            print(f"   💨 pressao_chama raw: {pressoes_raw} (tipo: {type(pressoes_raw)})")
            
            if isinstance(pressoes_raw, str):
                pressoes_raw = [pressoes_raw]
                
            pressoes = []
            for p in pressoes_raw:
                try:
                    pressoes.append(TipoPressaoChama[p.upper()])
                    print(f"   ✅ Pressão convertida: {p} -> {TipoPressaoChama[p.upper()]}")
                except Exception as e:
                    print(f"   ❌ Erro ao converter pressão '{p}': {e}")
            
            print(f"   💨 Pressões finais: {pressoes}")
            
            # Resultado final
            tem_config_valida = bool(tipo_chama_raw and pressoes)
            print(f"   📊 Configuração válida: {tem_config_valida}")

    def debug_capacidade_step_by_step(self, atividade: "AtividadeModular", inicio: datetime, fim: datetime):
        """Debug passo a passo do cálculo de capacidade"""
        if not self.debug_mode:
            return
            
        print("\n🔍 DEBUG - Cálculo de Capacidade Passo a Passo:")
        print("=" * 60)
        
        capacidade_total = 0
        
        for i, fogao in enumerate(self.fogoes):
            print(f"\n📊 ETAPA {i+1}: {fogao.nome}")
            
            # Passo 1: Obter configurações
            print("   🔥 Passo 1: Obtendo tipo de chama...")
            tipo_chama = self._obter_tipo_chama_para_fogao(atividade, fogao)
            print(f"      Resultado: {tipo_chama}")
            
            print("   💨 Passo 2: Obtendo pressões...")
            pressoes = self._obter_pressoes_chama_para_fogao(atividade, fogao)
            print(f"      Resultado: {pressoes}")
            
            # Passo 2: Verificar se passa no filtro
            if tipo_chama is None or not pressoes:
                print("   ❌ REJEITADO: configurações inválidas")
                continue
            else:
                print("   ✅ ACEITO: configurações válidas")
            
            # Passo 3: Contar bocas disponíveis
            print("   🔢 Passo 3: Contando bocas disponíveis...")
            bocas_disponiveis = fogao.bocas_disponiveis_periodo(inicio, fim)
            print(f"      Bocas totais: {fogao.numero_bocas}")
            print(f"      Bocas disponíveis: {len(bocas_disponiveis)}")
            print(f"      Índices das bocas: {bocas_disponiveis}")
            
            # Passo 4: Calcular capacidade
            capacidade_fogao = len(bocas_disponiveis) * fogao.capacidade_por_boca_gramas_max
            capacidade_total += capacidade_fogao
            
            print(f"   📊 Capacidade deste fogão: {len(bocas_disponiveis)} × {fogao.capacidade_por_boca_gramas_max}g = {capacidade_fogao}g")
            print(f"   📊 Capacidade acumulada: {capacidade_total}g")
        
        print(f"\n📊 RESULTADO FINAL: {capacidade_total}g")
        return capacidade_total

    def ativar_debug(self):
        """Ativa modo debug"""
        self.debug_mode = True
        logger.info("🐛 Modo debug ATIVADO")

    def desativar_debug(self):
        """Desativa modo debug"""
        self.debug_mode = False
        logger.info("🔇 Modo debug DESATIVADO")

    # ==========================================================
    # 📊 Ordenação e IDs
    # ==========================================================    
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[Fogao]:
        """Ordena fogões por FIP (menor = maior prioridade)."""
        return sorted(
            self.fogoes,
            key=lambda f: atividade.fips_equipamentos.get(f, 999)
        )

    def _obter_ids_atividade(self, atividade: "AtividadeModular") -> Tuple[int, int, int, int]:
        """Extrai IDs da atividade de forma consistente."""
        id_ordem = getattr(atividade, 'id_ordem', 0)
        id_pedido = getattr(atividade, 'id_pedido', 0) 
        id_atividade = getattr(atividade, 'id_atividade', 0)
        id_item = getattr(atividade, 'id_item', getattr(atividade, 'id_produto', 0))
        
        return id_ordem, id_pedido, id_atividade, id_item

    # ==========================================================
    # 🔧 Configurações JSON
    # ==========================================================   
    def _obter_tipo_chama_para_fogao(self, atividade: "AtividadeModular", fogao: Fogao) -> Optional[TipoChama]:
        """Obtém tipo de chama do JSON de configurações."""
        try:
            chave = unicodedata.normalize("NFKD", fogao.nome.lower()).encode("ASCII", "ignore").decode().replace(" ", "_")
            config = getattr(atividade, "configuracoes_equipamentos", {}).get(chave, {})
            tipo_chama_raw = config.get("tipo_chama")
            
            if self.debug_mode:
                logger.debug(f"🔥 {fogao.nome}: chave='{chave}', config={config}, tipo_chama_raw={tipo_chama_raw}")
            
            if not tipo_chama_raw:
                if self.debug_mode:
                    logger.debug(f"⚠️ Tipo de chama não definido para {fogao.nome}")
                return None
                
            # Trata lista ou string
            if isinstance(tipo_chama_raw, list):
                tipo_chama_raw = tipo_chama_raw[0] if tipo_chama_raw else None
                
            if not tipo_chama_raw:
                return None
                
            resultado = TipoChama[tipo_chama_raw.upper()]
            if self.debug_mode:
                logger.debug(f"✅ {fogao.nome}: TipoChama = {resultado}")
            return resultado
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter tipo de chama para {fogao.nome}: {e}")
            return None

    def _obter_pressoes_chama_para_fogao(self, atividade: "AtividadeModular", fogao: Fogao) -> List[TipoPressaoChama]:
        """Obtém pressões de chama do JSON de configurações."""
        try:
            chave = unicodedata.normalize("NFKD", fogao.nome.lower()).encode("ASCII", "ignore").decode().replace(" ", "_")
            config = getattr(atividade, "configuracoes_equipamentos", {}).get(chave, {})
            pressoes_raw = config.get("pressao_chama", [])
            
            if self.debug_mode:
                logger.debug(f"💨 {fogao.nome}: chave='{chave}', pressoes_raw={pressoes_raw}")
            
            if isinstance(pressoes_raw, str):
                pressoes_raw = [pressoes_raw]
                
            pressoes = []
            for p in pressoes_raw:
                try:
                    pressao = TipoPressaoChama[p.upper()]
                    pressoes.append(pressao)
                    if self.debug_mode:
                        logger.debug(f"✅ {fogao.nome}: Pressão '{p}' -> {pressao}")
                except Exception:
                    logger.warning(f"⚠️ Pressão inválida: '{p}' para fogão {fogao.nome}")
            
            if self.debug_mode:
                logger.debug(f"💨 {fogao.nome}: Pressões finais = {pressoes}")
            return pressoes
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter pressões para {fogao.nome}: {e}")
            return []

    # ==========================================================
    # 🧮 Cálculos de Capacidade e Distribuição
    # ==========================================================
    def _calcular_capacidade_total_disponivel(
        self, 
        atividade: "AtividadeModular",
        inicio: datetime, 
        fim: datetime
    ) -> int:
        """Calcula capacidade total disponível de todos os fogões."""
        if self.debug_mode:
            logger.info(f"🔍 Calculando capacidade total para atividade {atividade.id_atividade}")
            logger.info(f"📅 Período: {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}")
        
        capacidade_total = 0
        
        for fogao in self.fogoes:
            if self.debug_mode:
                logger.debug(f"\n🔥 Analisando {fogao.nome}:")
            
            # Verifica configurações básicas
            tipo_chama = self._obter_tipo_chama_para_fogao(atividade, fogao)
            pressoes = self._obter_pressoes_chama_para_fogao(atividade, fogao)
            
            if tipo_chama is None or not pressoes:
                if self.debug_mode:
                    logger.debug(f"❌ {fogao.nome}: configurações inválidas (tipo_chama={tipo_chama}, pressoes={pressoes})")
                else:
                    logger.debug(f"❌ {fogao.nome}: configurações inválidas")
                continue
            
            # Conta bocas disponíveis
            bocas_disponiveis = fogao.bocas_disponiveis_periodo(inicio, fim)
            capacidade_fogao = len(bocas_disponiveis) * fogao.capacidade_por_boca_gramas_max
            capacidade_total += capacidade_fogao
            
            if self.debug_mode:
                logger.debug(f"✅ {fogao.nome}: {len(bocas_disponiveis)} bocas × {fogao.capacidade_por_boca_gramas_max}g = {capacidade_fogao}g")
            else:
                logger.debug(f"📊 {fogao.nome}: {len(bocas_disponiveis)} bocas × {fogao.capacidade_por_boca_gramas_max}g = {capacidade_fogao}g")
        
        if self.debug_mode:
            logger.info(f"📊 CAPACIDADE TOTAL CALCULADA: {capacidade_total}g")
        
        return capacidade_total

    def _calcular_bocas_necessarias(self, quantidade_produto: int, fogao: Fogao) -> int:
        """Calcula quantas bocas são necessárias para um fogão específico."""
        return ceil(quantidade_produto / fogao.capacidade_por_boca_gramas_max)

    def _distribuir_quantidade_entre_bocas(
        self, 
        quantidade_total: int, 
        num_bocas: int, 
        capacidade_min: float, 
        capacidade_max: float
    ) -> List[float]:
        """
        Distribui quantidade entre bocas respeitando limites mínimo e máximo.
        Garante que nenhuma boca fique abaixo do mínimo.
        """
        if num_bocas <= 0:
            return []
        
        # Verifica se é possível distribuir respeitando o mínimo
        if quantidade_total < num_bocas * capacidade_min:
            if self.debug_mode:
                logger.warning(f"❌ Quantidade {quantidade_total}g insuficiente para {num_bocas} bocas (mín {capacidade_min}g cada)")
            return []
        
        # Verifica se é possível distribuir sem exceder o máximo
        if quantidade_total > num_bocas * capacidade_max:
            if self.debug_mode:
                logger.warning(f"❌ Quantidade {quantidade_total}g excede capacidade de {num_bocas} bocas (máx {capacidade_max}g cada)")
            return []
        
        # Distribuição inteligente
        distribuicao = []
        quantidade_restante = quantidade_total
        
        for i in range(num_bocas):
            bocas_restantes = num_bocas - i
            
            if bocas_restantes == 1:
                # Última boca: coloca o que sobrou
                quantidade_boca = quantidade_restante
            else:
                # Calcula máximo que pode colocar nesta boca
                # sem inviabilizar as próximas (que precisam do mínimo)
                max_nesta_boca = min(
                    capacidade_max,
                    quantidade_restante - (bocas_restantes - 1) * capacidade_min
                )
                quantidade_boca = min(quantidade_restante, max_nesta_boca)
            
            # Valida limites
            if quantidade_boca < capacidade_min or quantidade_boca > capacidade_max:
                if self.debug_mode:
                    logger.warning(f"❌ Distribuição inválida: boca {i+1} teria {quantidade_boca}g (limites: {capacidade_min}-{capacidade_max}g)")
                return []
            
            distribuicao.append(quantidade_boca)
            quantidade_restante -= quantidade_boca
        
        if self.debug_mode:
            logger.debug(f"📊 Distribuição: {[f'{q:.0f}g' for q in distribuicao]} (total: {sum(distribuicao):.0f}g)")
        return distribuicao

    # ==========================================================
    # 🎯 Alocação Principal com Algoritmo de Escalabilidade + Agrupamento
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
        Aloca atividade nos fogões usando algoritmo de escalabilidade com agrupamento:
        0. Tenta agrupamento com ocupações existentes
        1. Verifica capacidade total
        2. Testa fogões individuais  
        3. Testa combinações múltiplas
        4. Backward scheduling como fallback
        """
        duracao = atividade.duracao
        id_ordem, id_pedido, id_atividade, id_item = self._obter_ids_atividade(atividade)
        
        logger.info(f"🔥 Iniciando alocação atividade {id_atividade}: {quantidade_produto}g")
        logger.info(f"📅 Janela: {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')} (duração: {duracao})")
        
        # ==========================================================
        # 🚨 VALIDAÇÃO PRÉVIA
        # ==========================================================
        logger.info("🔍 Executando validações prévias...")
        
        valido, mensagem = self.validar_viabilidade_basica(atividade, quantidade_produto)
        
        if not valido:
            logger.error(f"❌ VALIDAÇÃO FALHOU: {mensagem}")
            return False, None, None, None
        
        logger.info(f"✅ Validações prévias aprovadas: {mensagem}")

        # ==========================================================
        # 🔄 ETAPA 0: TENTATIVA DE AGRUPAMENTO
        # ==========================================================
        logger.info("🔍 Verificando possibilidade de agrupamento...")
        
        ocupacao_compativel = self.encontrar_ocupacao_compativel(
            atividade, quantidade_produto, inicio, fim
        )
        
        if ocupacao_compativel:
            fogao, boca_idx, quantidade_existente = ocupacao_compativel
            quantidade_nova_total = quantidade_existente + quantidade_produto
            
            logger.info(
                f"✅ Ocupação compatível encontrada: {fogao.nome} Boca {boca_idx+1} "
                f"({quantidade_existente:.0f}g + {quantidade_produto}g = {quantidade_nova_total:.0f}g)"
            )
            
            # Atualizar a ocupação existente com a nova quantidade
            sucesso = self.atualizar_ocupacao_existente(
                fogao, boca_idx, atividade, quantidade_nova_total, inicio, fim,
                id_ordem, id_pedido, id_atividade, id_item
            )
            
            if sucesso:
                logger.info(f"🔄 Agrupamento bem-sucedido: {quantidade_produto}g adicionado à ocupação existente")
                return True, fogao, inicio, fim
            else:
                logger.warning("⚠️ Falha no agrupamento, tentando alocação normal...")
        else:
            logger.info("📊 Nenhuma ocupação compatível encontrada para agrupamento")

        # ==========================================================
        # 🐛 DEBUG AUTOMÁTICO
        # ==========================================================
        if self.debug_mode:
            self.debug_mapeamento_nomes_fogoes(atividade)
            self.debug_capacidade_step_by_step(atividade, inicio, fim)

        # ==========================================================
        # 📊 ETAPA 1: VERIFICAÇÃO DE CAPACIDADE TOTAL
        # ==========================================================
        capacidade_total_disponivel = self._calcular_capacidade_total_disponivel(atividade, inicio, fim)
        
        if capacidade_total_disponivel < quantidade_produto:
            logger.warning(
                f"❌ Capacidade total insuficiente: necessário {quantidade_produto}g, "
                f"disponível {capacidade_total_disponivel}g"
            )
            return False, None, None, None

        logger.info(f"✅ Capacidade total suficiente: {capacidade_total_disponivel}g >= {quantidade_produto}g")

        # ==========================================================
        # 🔄 ETAPA 2: TESTA ALOCAÇÃO DIRETA (sem backward scheduling)
        # ==========================================================
        sucesso_direto = self._tentar_alocacao_direta(
            atividade, quantidade_produto, inicio, fim, id_ordem, id_pedido, id_atividade, id_item
        )
        
        if sucesso_direto:
            fogao_usado, inicio_real, fim_real = sucesso_direto
            atividade.equipamento_alocado = fogao_usado
            atividade.equipamentos_selecionados = [fogao_usado] if not isinstance(fogao_usado, list) else fogao_usado
            atividade.alocada = True
            
            logger.info(
                f"✅ Atividade {id_atividade} alocada diretamente "
                f"de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')}"
            )
            return True, fogao_usado, inicio_real, fim_real

        # ==========================================================
        # ⏰ ETAPA 3: BACKWARD SCHEDULING
        # ==========================================================
        logger.info(f"🔄 Iniciando backward scheduling para atividade {id_atividade}")
        
        horario_final_tentativa = fim
        tentativas = 0
        
        while horario_final_tentativa - duracao >= inicio:
            tentativas += 1
            horario_inicio_tentativa = horario_final_tentativa - duracao

            if tentativas % 10 == 0:
                logger.debug(f"⏰ Tentativa {tentativas}: {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}")

            # Tenta alocação nesta janela específica
            sucesso_janela = self._tentar_alocacao_direta(
                atividade, quantidade_produto, horario_inicio_tentativa, horario_final_tentativa,
                id_ordem, id_pedido, id_atividade, id_item
            )
            
            if sucesso_janela:
                fogao_usado, inicio_real, fim_real = sucesso_janela
                atividade.equipamento_alocado = fogao_usado
                atividade.equipamentos_selecionados = [fogao_usado] if not isinstance(fogao_usado, list) else fogao_usado
                atividade.alocada = True
                
                minutos_retrocedidos = int((fim - fim_real).total_seconds() / 60)
                logger.info(
                    f"✅ Atividade {id_atividade} alocada via backward scheduling "
                    f"de {inicio_real.strftime('%H:%M')} até {fim_real.strftime('%H:%M')} "
                    f"(retrocedeu {minutos_retrocedidos} minutos)"
                )
                return True, fogao_usado, inicio_real, fim_real

            # Retrocede 1 minuto
            horario_final_tentativa -= timedelta(minutes=1)

        logger.error(
            f"❌ ERRO: Atividade {id_atividade} não pôde ser alocada após {tentativas} tentativas, "
            f"mesmo com capacidade confirmada!"
        )
        return False, None, None, None
    
    def validar_viabilidade_basica(self, atividade: "AtividadeModular", quantidade_produto: int) -> tuple[bool, str]:
        """
        Validação rápida ANTES de tentar alocação ou backward scheduling
        """
        
        # VALIDAÇÃO 1: Quantidade positiva
        if quantidade_produto <= 0:
            return False, f"Quantidade inválida: {quantidade_produto}g (deve ser > 0)"
        
        # VALIDAÇÃO 2: Verificar se há fogões elegíveis
        fogoes_elegiveis = []
        for fogao in self.fogoes:
            tipo_chama = self._obter_tipo_chama_para_fogao(atividade, fogao)
            pressoes = self._obter_pressoes_chama_para_fogao(atividade, fogao)
            
            if tipo_chama is not None and pressoes:
                fogoes_elegiveis.append(fogao)
        
        if not fogoes_elegiveis:
            return False, "Nenhum fogão tem configuração válida para esta atividade"
        
        # VALIDAÇÃO 3: Capacidade mínima por boca
        capacidade_min_global = min(f.capacidade_por_boca_gramas_min for f in fogoes_elegiveis)
        
        if quantidade_produto < capacidade_min_global:
            return False, (
                f"Quantidade {quantidade_produto}g abaixo do mínimo por boca "
                f"({capacidade_min_global}g). Quantidade mínima necessária: {capacidade_min_global}g"
            )
        
        # VALIDAÇÃO 4: Capacidade máxima teórica total
        capacidade_max_teorica = sum(
            f.numero_bocas * f.capacidade_por_boca_gramas_max 
            for f in fogoes_elegiveis
        )
        
        if quantidade_produto > capacidade_max_teorica:
            return False, (
                f"Quantidade {quantidade_produto}g excede capacidade máxima teórica "
                f"({capacidade_max_teorica}g). Sistema não pode processar esta quantidade."
            )
        
        # ✅ Todas as validações passaram
        return True, "Validações básicas aprovadas"

    def _tentar_alocacao_direta(
        self,
        atividade: "AtividadeModular",
        quantidade_produto: int,
        inicio: datetime,
        fim: datetime,
        id_ordem: int,
        id_pedido: int, 
        id_atividade: int,
        id_item: int
    ) -> Optional[Tuple[Fogao, datetime, datetime]]:
        """
        Tenta alocação direta seguindo estratégia de escalabilidade:
        1. Fogões individuais (por FIP)
        2. Combinações de 2, 3, ..., N fogões
        """
        from itertools import combinations
        
        fogoes_ordenados = self._ordenar_por_fip(atividade)
        
        # ESTRATÉGIA 1: Fogões individuais
        if self.debug_mode:
            logger.debug("🔍 Testando fogões individuais...")
        for fogao in fogoes_ordenados:
            if self._testar_viabilidade_fogao_individual(fogao, atividade, quantidade_produto, inicio, fim):
                if self._alocar_fogao_individual(
                    fogao, atividade, quantidade_produto, inicio, fim,
                    id_ordem, id_pedido, id_atividade, id_item
                ):
                    logger.info(f"✅ Alocação individual bem-sucedida: {fogao.nome}")
                    return fogao, inicio, fim
        
        # ESTRATÉGIA 2: Combinações múltiplas
        for num_fogoes in range(2, len(fogoes_ordenados) + 1):
            if self.debug_mode:
                logger.debug(f"🔍 Testando combinações de {num_fogoes} fogões...")
            
            for combinacao in combinations(fogoes_ordenados, num_fogoes):
                if self._testar_viabilidade_combinacao_fogoes(list(combinacao), atividade, quantidade_produto, inicio, fim):
                    if self._alocar_combinacao_fogoes(
                        list(combinacao), atividade, quantidade_produto, inicio, fim,
                        id_ordem, id_pedido, id_atividade, id_item
                    ):
                        logger.info(f"✅ Alocação múltipla bem-sucedida: {[f.nome for f in combinacao]}")
                        return list(combinacao), inicio, fim
        
        if self.debug_mode:
            logger.debug("❌ Nenhuma combinação de fogões foi bem-sucedida")
        return None

    # ==========================================================
    # 🧪 Testes de Viabilidade (sem alocar)
    # ==========================================================
    def _testar_viabilidade_fogao_individual(
        self,
        fogao: Fogao,
        atividade: "AtividadeModular", 
        quantidade_produto: int,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """Testa se um fogão individual pode comportar toda a produção."""
        
        # Verifica configurações
        tipo_chama = self._obter_tipo_chama_para_fogao(atividade, fogao)
        pressoes = self._obter_pressoes_chama_para_fogao(atividade, fogao)
        
        if tipo_chama is None or not pressoes:
            if self.debug_mode:
                logger.debug(f"❌ {fogao.nome}: configurações inválidas")
            return False
        
        # Calcula bocas necessárias
        bocas_necessarias = self._calcular_bocas_necessarias(quantidade_produto, fogao)
        bocas_disponiveis = fogao.bocas_disponiveis_periodo(inicio, fim)
        
        if len(bocas_disponiveis) < bocas_necessarias:
            if self.debug_mode:
                logger.debug(f"❌ {fogao.nome}: necessárias {bocas_necessarias} bocas, disponíveis {len(bocas_disponiveis)}")
            return False
        
        # Testa distribuição de peso
        distribuicao = self._distribuir_quantidade_entre_bocas(
            quantidade_produto, bocas_necessarias,
            fogao.capacidade_por_boca_gramas_min, fogao.capacidade_por_boca_gramas_max
        )
        
        if not distribuicao:
            if self.debug_mode:
                logger.debug(f"❌ {fogao.nome}: impossível distribuir {quantidade_produto}g em {bocas_necessarias} bocas")
            return False
        
        if self.debug_mode:
            logger.debug(f"✅ {fogao.nome}: viável ({bocas_necessarias} bocas)")
        return True

    def _testar_viabilidade_combinacao_fogoes(
        self,
        fogoes: List[Fogao],
        atividade: "AtividadeModular",
        quantidade_produto: int,
        inicio: datetime,
        fim: datetime
    ) -> bool:
        """Testa se uma combinação de fogões pode comportar a produção."""
        
        bocas_totais_disponiveis = 0
        capacidade_total = 0
        
        for fogao in fogoes:
            # Verifica configurações básicas
            tipo_chama = self._obter_tipo_chama_para_fogao(atividade, fogao)
            pressoes = self._obter_pressoes_chama_para_fogao(atividade, fogao)
            
            if tipo_chama is None or not pressoes:
                if self.debug_mode:
                    logger.debug(f"❌ Combinação inválida: {fogao.nome} sem configuração")
                return False
            
            bocas_disponiveis = fogao.bocas_disponiveis_periodo(inicio, fim)
            bocas_totais_disponiveis += len(bocas_disponiveis)
            capacidade_total += len(bocas_disponiveis) * fogao.capacidade_por_boca_gramas_max
        
        # Verifica capacidade total
        if capacidade_total < quantidade_produto:
            if self.debug_mode:
                logger.debug(f"❌ Combinação: capacidade {capacidade_total}g < necessário {quantidade_produto}g")
            return False
        
        # Verifica se é possível distribuir respeitando mínimos
        # (aproximação conservadora - usa menor capacidade mínima)
        capacidade_min_conservadora = min(f.capacidade_por_boca_gramas_min for f in fogoes)
        if quantidade_produto < bocas_totais_disponiveis * capacidade_min_conservadora:
            if self.debug_mode:
                logger.debug(f"❌ Combinação: {quantidade_produto}g insuficiente para {bocas_totais_disponiveis} bocas (mín {capacidade_min_conservadora}g cada)")
            return False
        
        if self.debug_mode:
            logger.debug(f"✅ Combinação viável: {[f.nome for f in fogoes]} ({bocas_totais_disponiveis} bocas, {capacidade_total}g)")
        return True

    # ==========================================================
    # 🎯 Execução de Alocação (após testes)
    # ==========================================================
    def _alocar_fogao_individual(
        self,
        fogao: Fogao,
        atividade: "AtividadeModular",
        quantidade_produto: int,
        inicio: datetime,
        fim: datetime,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int
    ) -> bool:
        """Aloca produção em um fogão individual."""
        
        tipo_chama = self._obter_tipo_chama_para_fogao(atividade, fogao)
        pressoes = self._obter_pressoes_chama_para_fogao(atividade, fogao)
        
        bocas_necessarias = self._calcular_bocas_necessarias(quantidade_produto, fogao)
        bocas_disponiveis = fogao.bocas_disponiveis_periodo(inicio, fim)
        
        distribuicao = self._distribuir_quantidade_entre_bocas(
            quantidade_produto, bocas_necessarias,
            fogao.capacidade_por_boca_gramas_min, fogao.capacidade_por_boca_gramas_max
        )
        
        if not distribuicao:
            return False
        
        # Aloca bocas
        bocas_usadas = bocas_disponiveis[:bocas_necessarias]
        sucesso_total = True
        
        for i, boca_idx in enumerate(bocas_usadas):
            sucesso = fogao.adicionar_ocupacao_boca(
                boca_index=boca_idx,
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                id_atividade=id_atividade,
                id_item=id_item,
                quantidade_alocada=distribuicao[i],
                tipo_chama=tipo_chama,
                pressoes_chama=pressoes,
                inicio=inicio,
                fim=fim
            )
            
            if not sucesso:
                sucesso_total = False
                logger.warning(f"❌ Falha ao ocupar boca {boca_idx} do {fogao.nome}")
                break
        
        if sucesso_total:
            logger.info(f"🔥 {fogao.nome}: {bocas_necessarias} bocas ocupadas com {quantidade_produto}g total")
        
        return sucesso_total

    
    def _alocar_combinacao_fogoes(
        self,
        fogoes: List[Fogao],
        atividade: "AtividadeModular",
        quantidade_produto: int,
        inicio: datetime,
        fim: datetime,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        id_item: int
    ) -> bool:
        """
        Aloca produção distribuindo proporcionalmente entre fogões
        """
        
        # Calcular capacidade total e proporções
        capacidades_fogoes = []
        capacidade_total = 0
        
        for fogao in fogoes:
            tipo_chama = self._obter_tipo_chama_para_fogao(atividade, fogao)
            pressoes = self._obter_pressoes_chama_para_fogao(atividade, fogao)
            
            if tipo_chama is None or not pressoes:
                continue
                
            bocas_disponiveis = fogao.bocas_disponiveis_periodo(inicio, fim)
            capacidade_fogao = len(bocas_disponiveis) * fogao.capacidade_por_boca_gramas_max
            
            capacidades_fogoes.append({
                'fogao': fogao,
                'capacidade': capacidade_fogao,
                'bocas_disponiveis': bocas_disponiveis,
                'tipo_chama': tipo_chama,
                'pressoes': pressoes
            })
            capacidade_total += capacidade_fogao
        
        if capacidade_total < quantidade_produto:
            logger.warning(f"❌ Capacidade total insuficiente: {capacidade_total}g < {quantidade_produto}g")
            return False
        
        # Distribuir quantidade proporcionalmente
        alocacoes = []
        quantidade_restante = quantidade_produto
        
        logger.info(f"🔄 Distribuindo {quantidade_produto}g entre {len(capacidades_fogoes)} fogões:")
        
        for i, info in enumerate(capacidades_fogoes):
            fogao = info['fogao']
            capacidade_fogao = info['capacidade']
            bocas_disponiveis = info['bocas_disponiveis']
            
            # Calcular proporção deste fogão
            if i == len(capacidades_fogoes) - 1:
                # Último fogão: aloca tudo que sobrou
                quantidade_fogao = quantidade_restante
            else:
                proporcao = capacidade_fogao / capacidade_total
                quantidade_fogao = min(quantidade_produto * proporcao, quantidade_restante, capacidade_fogao)
            
            quantidade_restante -= quantidade_fogao
            
            logger.info(f"   🔥 {fogao.nome}: {quantidade_fogao:.0f}g ({quantidade_fogao/quantidade_produto*100:.1f}%)")
            
            # Distribuir entre as bocas deste fogão
            bocas_necessarias = min(
                len(bocas_disponiveis),
                max(1, int(quantidade_fogao / fogao.capacidade_por_boca_gramas_max) + 1)
            )
            
            distribuicao = self._distribuir_quantidade_entre_bocas(
                quantidade_fogao, bocas_necessarias,
                fogao.capacidade_por_boca_gramas_min, fogao.capacidade_por_boca_gramas_max
            )
            
            if not distribuicao:
                # Fallback: distribuir uniformemente
                quantidade_por_boca = quantidade_fogao / bocas_necessarias
                distribuicao = [quantidade_por_boca] * bocas_necessarias
            
            # Alocar bocas
            for j, quantidade_boca in enumerate(distribuicao):
                if j >= len(bocas_disponiveis):
                    break
                    
                boca_idx = bocas_disponiveis[j]
                alocacoes.append({
                    'fogao': fogao,
                    'boca_idx': boca_idx,
                    'quantidade': quantidade_boca,
                    'tipo_chama': info['tipo_chama'],
                    'pressoes': info['pressoes']
                })
        
        # Executar alocações
        sucesso_total = True
        fogoes_usados = set()
        
        for alocacao in alocacoes:
            sucesso = alocacao['fogao'].adicionar_ocupacao_boca(
                boca_index=alocacao['boca_idx'],
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                id_atividade=id_atividade,
                id_item=id_item,
                quantidade_alocada=alocacao['quantidade'],
                tipo_chama=alocacao['tipo_chama'],
                pressoes_chama=alocacao['pressoes'],
                inicio=inicio,
                fim=fim
            )
            
            if sucesso:
                fogoes_usados.add(alocacao['fogao'])
                if self.debug_mode:
                    logger.debug(f"🔥 {alocacao['fogao'].nome} boca {alocacao['boca_idx']}: {alocacao['quantidade']:.0f}g")
            else:
                sucesso_total = False
                logger.warning(f"❌ Falha ao ocupar boca {alocacao['boca_idx']} do {alocacao['fogao'].nome}")
                break
        
        if sucesso_total:
            total_alocado = sum(a['quantidade'] for a in alocacoes)
            logger.info(f"✅ Distribuição: {len(alocacoes)} bocas em {len(fogoes_usados)} fogões, {total_alocado:.0f}g total")
        
        return sucesso_total
    
    
    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade: "AtividadeModular"):
        """Libera ocupações específicas por atividade."""
        id_ordem, id_pedido, id_atividade, _ = self._obter_ids_atividade(atividade)
        for fogao in self.fogoes:
            fogao.liberar_por_atividade(id_ordem, id_pedido, id_atividade)
    
    def liberar_por_pedido(self, atividade: "AtividadeModular"):
        """Libera ocupações específicas por pedido."""
        id_ordem, id_pedido, _, _ = self._obter_ids_atividade(atividade)
        for fogao in self.fogoes:
            fogao.liberar_por_pedido(id_ordem, id_pedido)

    def liberar_por_ordem(self, atividade: "AtividadeModular"):
        """Libera ocupações específicas por ordem."""
        id_ordem, _, _, _ = self._obter_ids_atividade(atividade)
        for fogao in self.fogoes:
            fogao.liberar_por_ordem(id_ordem)

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        """Libera ocupações que já finalizaram."""
        for fogao in self.fogoes:
            fogao.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        """Libera todas as ocupações."""
        for fogao in self.fogoes:
            fogao.liberar_todas_ocupacoes()

    def liberar_por_intervalo(self, inicio: datetime, fim: datetime):
        """Libera ocupações que se sobrepõem ao intervalo especificado."""
        for fogao in self.fogoes:
            fogao.liberar_por_intervalo(inicio, fim)

    # ==========================================================
    # 📅 Agenda e Relatórios
    # ==========================================================
    def mostrar_agenda(self):
        """Mostra agenda de todos os fogões."""
        logger.info("==============================================")
        logger.info("📅 Agenda dos Fogões")
        logger.info("==============================================")
        for fogao in self.fogoes:
            fogao.mostrar_agenda()

    def obter_estatisticas_globais(self, inicio: datetime, fim: datetime) -> dict:
        """Retorna estatísticas consolidadas de todos os fogões."""
        estatisticas = {
            'total_fogoes': len(self.fogoes),
            'total_bocas': sum(f.numero_bocas for f in self.fogoes),
            'bocas_utilizadas': 0,
            'quantidade_total': 0.0,
            'fogoes_utilizados': 0,
            'detalhes_por_fogao': {}
        }

        for fogao in self.fogoes:
            stats_fogao = fogao.obter_estatisticas_uso(inicio, fim)
            
            estatisticas['detalhes_por_fogao'][fogao.nome] = stats_fogao
            estatisticas['bocas_utilizadas'] += stats_fogao['bocas_utilizadas']
            estatisticas['quantidade_total'] += stats_fogao['quantidade_total']
            
            if stats_fogao['bocas_utilizados'] > 0:
                estatisticas['fogoes_utilizados'] += 1

        # Calcula taxa de utilização global
        if estatisticas['total_bocas'] > 0:
            estatisticas['taxa_utilizacao_bocas'] = (estatisticas['bocas_utilizadas'] / estatisticas['total_bocas']) * 100
        else:
            estatisticas['taxa_utilizacao_bocas'] = 0.0

        return estatisticas