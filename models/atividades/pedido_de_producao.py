from typing import List, Optional
from datetime import datetime, timedelta
import os
from factory.fabrica_funcionarios import funcionarios_disponiveis
from models.funcionarios.funcionario import Funcionario
from models.atividades.atividade_modular import AtividadeModular
from parser.carregador_json_atividades import buscar_atividades_por_id_item
from parser.carregador_json_fichas_tecnicas import buscar_ficha_tecnica_por_id
from parser.carregador_json_tipos_profissionais import buscar_tipos_profissionais_por_id_item
from services.rollback.rollback import rollback_equipamentos, rollback_funcionarios
from models.ficha_tecnica.ficha_tecnica_modular import FichaTecnicaModular
from enums.producao.tipo_item import TipoItem
from enums.producao.politica_producao import PoliticaProducao
from services.gestor_almoxarifado.gestor_almoxarifado import GestorAlmoxarifado
from utils.logs.logger_factory import setup_logger
from utils.logs.gerenciador_logs import (
    registrar_erro_execucao_pedido, 
    apagar_logs_por_pedido_e_ordem, 
    salvar_erro_em_log
)
from services.gestor_comandas.gestor_comandas import gerar_comanda_reserva as gerar_comanda_reserva_modulo

logger = setup_logger("PedidoDeProducao")


class PedidoDeProducao:
    """
    Classe principal para gerenciar um pedido de produção.
    Coordena a criação e execução de atividades modulares com verificação inteligente de estoque.
    ✅ CORRIGIDO: Implementa cancelamento em cascata se atividades do PRODUTO falharem.
    """
    
    def __init__(
        self,
        id_ordem: int,
        id_pedido: int,
        id_produto: int,
        tipo_item: TipoItem,
        quantidade: int,
        inicio_jornada: datetime,
        fim_jornada: datetime,
        todos_funcionarios: Optional[List[Funcionario]] = None,
        gestor_almoxarifado: Optional[GestorAlmoxarifado] = None
    ):
        # =============================================================================
        #                           IDENTIFICAÇÃO
        # =============================================================================
        self.id_ordem = id_ordem
        self.id_pedido = id_pedido
        self.id_produto = id_produto
        self.tipo_item = tipo_item
        self.quantidade = quantidade

        # =============================================================================
        #                        JANELA DE PRODUÇÃO
        # =============================================================================
        self.inicio_jornada = inicio_jornada
        self.fim_jornada = fim_jornada

        # =============================================================================
        #                           FUNCIONÁRIOS
        # =============================================================================
        self.todos_funcionarios = todos_funcionarios or []
        self.funcionarios_elegiveis: List[Funcionario] = []

        # =============================================================================
        #                        ESTRUTURA TÉCNICA
        # =============================================================================
        self.ficha_tecnica_modular = None
        self.atividades_modulares = []

        # =============================================================================
        #                           EQUIPAMENTOS
        # =============================================================================
        self.equipamentos_alocados = []  
        self.equipamentos_alocados_no_pedido = []

        # =============================================================================
        #                           ALMOXARIFADO
        # =============================================================================
        self.gestor_almoxarifado = gestor_almoxarifado
        
        # =============================================================================
        #                    CONTROLE DE EXECUÇÃO - NOVO
        # =============================================================================
        self.atividades_executadas = []  # Atividades já executadas com sucesso
        self.pedido_cancelado = False   # Flag para indicar se pedido foi cancelado
        
        # Log de inicialização
        logger.info(
            f"🆔 Criando pedido {self.id_pedido} da ordem {self.id_ordem} | "
            f"Produto: {self.id_produto} ({self.tipo_item.name}) | "
            f"Quantidade: {self.quantidade} | "
            f"Período: {self.inicio_jornada.strftime('%d/%m %H:%M')} - {self.fim_jornada.strftime('%d/%m %H:%M')}"
        )

    # =============================================================================
    #                        MONTAGEM DA ESTRUTURA
    # =============================================================================

    def montar_estrutura(self):
        """Monta a estrutura técnica do pedido baseada na ficha técnica"""
        try:
            logger.info(f"🔄 Montando estrutura técnica do pedido {self.id_pedido}")
            
            _, dados_ficha = buscar_ficha_tecnica_por_id(self.id_produto, tipo_item=self.tipo_item)
            self.ficha_tecnica_modular = FichaTecnicaModular(
                dados_ficha_tecnica=dados_ficha,
                quantidade_requerida=self.quantidade
            )
            
            # Filtrar funcionários considerando produto principal e subprodutos
            self.funcionarios_elegiveis = self._filtrar_funcionarios_abrangente()
            
            logger.info(
                f"✅ Estrutura montada: {len(self.funcionarios_elegiveis)} funcionários elegíveis"
            )
            
        except Exception as e:
            logger.error(f"❌ Erro ao montar estrutura do pedido {self.id_pedido}: {e}")
            raise
        
    def _filtrar_funcionarios_abrangente(self) -> List[Funcionario]:
        """
        Filtra funcionários considerando tanto o produto principal quanto os subprodutos.
        Garante que todos os tipos profissionais necessários estejam disponíveis.
        """
        if not self.ficha_tecnica_modular:
            logger.warning("⚠️ Ficha técnica não montada, retornando todos os funcionários")
            return self.todos_funcionarios
            
        tipos_necessarios = set()
        
        try:
            # Adicionar tipos do produto principal
            tipos_produto = buscar_tipos_profissionais_por_id_item(self.id_produto)
            tipos_necessarios.update(tipos_produto)
            logger.debug(f"📋 Tipos para produto principal {self.id_produto}: {tipos_produto}")
            
            # Adicionar tipos dos subprodutos
            estimativas = self.ficha_tecnica_modular.calcular_quantidade_itens()
            for item_dict, _ in estimativas:
                if item_dict.get("tipo_item") == "SUBPRODUTO":
                    sub_id = item_dict.get("id_ficha_tecnica") 
                    if sub_id:
                        tipos_sub = buscar_tipos_profissionais_por_id_item(sub_id)
                        tipos_necessarios.update(tipos_sub)
                        logger.debug(f"📋 Tipos para subproduto {sub_id}: {tipos_sub}")
            
            funcionarios_filtrados = [
                f for f in self.todos_funcionarios 
                if f.tipo_profissional in tipos_necessarios
            ]
            
            logger.info(
                f"👥 Funcionários filtrados: {len(funcionarios_filtrados)}/{len(self.todos_funcionarios)} "
                f"para tipos {[t.name for t in tipos_necessarios]}"
            )
            
            return funcionarios_filtrados
            
        except Exception as e:
            logger.error(f"❌ Erro ao filtrar funcionários: {e}")
            return self.todos_funcionarios

    # =============================================================================
    #                      VERIFICAÇÃO DE ESTOQUE
    # =============================================================================

    def _verificar_estoque_suficiente(self, id_item: int, quantidade_necessaria: float) -> bool:
        """
        Verifica se há estoque suficiente para um item específico.
        Usa métodos otimizados do gestor de almoxarifado.
        """
        if not self.gestor_almoxarifado:
            logger.warning("⚠️ Gestor de almoxarifado não disponível. Assumindo necessidade de produção.")
            return False
        
        try:
            # Buscar item usando método otimizado do gestor
            item = self.gestor_almoxarifado.obter_item_por_id(id_item)
            if not item:
                logger.warning(f"⚠️ Item {id_item} não encontrado no almoxarifado")
                return False
            
            # Para PRODUTOS e SUBPRODUTOS, verificar estoque independente da política
            # Política SOB_DEMANDA não impede usar estoque disponível
            tem_estoque_suficiente = self.gestor_almoxarifado.verificar_estoque_atual_suficiente(
                id_item, quantidade_necessaria
            )
            
            estoque_atual = self.gestor_almoxarifado.obter_estoque_atual(id_item)
            
            logger.info(
                f"📦 Item '{item.descricao}' (ID {id_item}): "
                f"Estoque atual: {estoque_atual} | "
                f"Necessário: {quantidade_necessaria} | "
                f"Política: {item.politica_producao.value} | "
                f"Suficiente: {'✅' if tem_estoque_suficiente else '❌'}"
            )
            
            return tem_estoque_suficiente
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao verificar estoque do item {id_item}: {e}")
            return False

    def _verificar_estoque_multiplos_itens(self, itens_necessarios: List[tuple]) -> dict:
        """
        Verifica estoque para múltiplos itens de uma vez usando método otimizado.
        itens_necessarios: Lista de tuplas (id_item, quantidade)
        """
        if not self.gestor_almoxarifado:
            return {id_item: False for id_item, _ in itens_necessarios}
        
        try:
            # Usar método otimizado do gestor para verificação em lote
            resultado = self.gestor_almoxarifado.verificar_disponibilidade_multiplos_itens(
                itens_necessarios, self.inicio_jornada.date()
            )
            
            logger.debug(f"📦 Verificação em lote: {len(itens_necessarios)} itens verificados")
            return resultado
            
        except Exception as e:
            logger.error(f"❌ Erro na verificação em lote: {e}")
            return {id_item: False for id_item, _ in itens_necessarios}

    # =============================================================================
    #                      CRIAÇÃO DE ATIVIDADES
    # =============================================================================

    def criar_atividades_modulares_necessarias(self):
        """
        Cria todas as atividades modulares necessárias baseadas na ficha técnica.
        ✅ CORRIGIDO: Verifica se atividades do PRODUTO foram criadas com sucesso.
        Se nenhuma atividade do PRODUTO for criada, cancela o pedido inteiro.
        """
        if not self.ficha_tecnica_modular:
            raise ValueError("Ficha técnica ainda não foi montada")

        logger.info(f"🔄 Criando atividades modulares para pedido {self.id_pedido}")
        
        self.atividades_modulares = []
        
        # ✅ NOVA LÓGICA: Separar contadores por tipo
        atividades_produto_criadas = 0
        atividades_subproduto_criadas = 0
        
        self._criar_atividades_recursivas(self.ficha_tecnica_modular)
        
        # ✅ CONTABILIZAR ATIVIDADES POR TIPO
        for atividade in self.atividades_modulares:
            if atividade.tipo_item == TipoItem.PRODUTO:
                atividades_produto_criadas += 1
            elif atividade.tipo_item == TipoItem.SUBPRODUTO:
                atividades_subproduto_criadas += 1
        
        logger.info(
            f"📊 Atividades criadas para pedido {self.id_pedido}: "
            f"PRODUTO: {atividades_produto_criadas}, SUBPRODUTO: {atividades_subproduto_criadas}, "
            f"Total: {len(self.atividades_modulares)}"
        )
        
        # ✅ VALIDAÇÃO CRÍTICA: Se é um pedido de PRODUTO mas nenhuma atividade foi criada
        if self.tipo_item == TipoItem.PRODUTO and atividades_produto_criadas == 0:
            erro_msg = (
                f"❌ FALHA CRÍTICA NA CRIAÇÃO DE ATIVIDADES: "
                f"Pedido {self.id_pedido} é do tipo PRODUTO (ID {self.id_produto}) "
                f"mas NENHUMA atividade do produto foi criada com sucesso. "
                f"Isso indica incompatibilidade nas faixas de quantidade ou configuração. "
                f"CANCELANDO pedido completo incluindo {atividades_subproduto_criadas} atividade(s) de subproduto."
            )
            logger.error(erro_msg)
            
            # ✅ LIMPAR ATIVIDADES DE SUBPRODUTO JÁ CRIADAS
            self.atividades_modulares.clear()
            
            raise RuntimeError(erro_msg)

    def criar_atividades_modulares_necessarias(self):
        """
        Cria todas as atividades modulares necessárias baseadas na ficha técnica.
        ✅ CORRIGIDO: Verifica se atividades do PRODUTO foram criadas com sucesso.
        Se nenhuma atividade do PRODUTO for criada, cancela o pedido inteiro.
        """
        if not self.ficha_tecnica_modular:
            raise ValueError("Ficha técnica ainda não foi montada")

        logger.info(f"🔄 Criando atividades modulares para pedido {self.id_pedido}")
        
        self.atividades_modulares = []
        
        # ✅ NOVA LÓGICA: Separar contadores por tipo
        atividades_produto_criadas = 0
        atividades_subproduto_criadas = 0
        
        self._criar_atividades_recursivas(self.ficha_tecnica_modular)
        
        # ✅ CONTABILIZAR ATIVIDADES POR TIPO
        for atividade in self.atividades_modulares:
            if atividade.tipo_item == TipoItem.PRODUTO:
                atividades_produto_criadas += 1
            elif atividade.tipo_item == TipoItem.SUBPRODUTO:
                atividades_subproduto_criadas += 1
        
        logger.info(
            f"📊 Atividades criadas para pedido {self.id_pedido}: "
            f"PRODUTO: {atividades_produto_criadas}, SUBPRODUTO: {atividades_subproduto_criadas}, "
            f"Total: {len(self.atividades_modulares)}"
        )
        
        # ✅ VALIDAÇÃO CRÍTICA: Se é um pedido de PRODUTO mas nenhuma atividade foi criada
        if self.tipo_item == TipoItem.PRODUTO and atividades_produto_criadas == 0:
            erro_msg = (
                f"❌ FALHA CRÍTICA NA CRIAÇÃO DE ATIVIDADES: "
                f"Pedido {self.id_pedido} é do tipo PRODUTO (ID {self.id_produto}) "
                f"mas NENHUMA atividade do produto foi criada com sucesso. "
                f"Isso indica incompatibilidade nas faixas de quantidade ou configuração. "
                f"CANCELANDO pedido completo incluindo {atividades_subproduto_criadas} atividade(s) de subproduto."
            )
            logger.error(erro_msg)
            
            # ✅ LIMPAR ATIVIDADES DE SUBPRODUTO JÁ CRIADAS
            self.atividades_modulares.clear()
            
            raise RuntimeError(erro_msg)

    def _criar_atividades_recursivas(self, ficha_modular: FichaTecnicaModular):
        """
        Cria atividades de forma recursiva para produtos e subprodutos.
        Verifica estoque antes de criar atividades.
        """
        try:
            logger.info(
                f"🔄 Analisando necessidade de produção para ID {ficha_modular.id_item} "
                f"({ficha_modular.tipo_item.name}) - Quantidade: {ficha_modular.quantidade_requerida}"
            )
            
            # Verificar se é necessário produzir baseado no estoque APENAS para SUBPRODUTOS
            # PRODUTOS sempre devem ser produzidos (usando subprodutos do estoque quando disponível)
            if ficha_modular.tipo_item == TipoItem.SUBPRODUTO:
                if self._verificar_estoque_suficiente(ficha_modular.id_item, ficha_modular.quantidade_requerida):
                    logger.info(
                        f"✅ Estoque suficiente para SUBPRODUTO ID {ficha_modular.id_item}. "
                        f"Produção não necessária."
                    )
                    return  # Não criar atividades apenas para SUBPRODUTOS com estoque suficiente
            
            # Para PRODUTOS, sempre continuar a produção (mesmo que subprodutos venham do estoque)
            if ficha_modular.tipo_item == TipoItem.PRODUTO:
                logger.info(
                    f"🔄 PRODUTO ID {ficha_modular.id_item} será produzido "
                    f"(subprodutos podem vir do estoque)"
                )
            
            # Buscar atividades para o item atual
            atividades = buscar_atividades_por_id_item(ficha_modular.id_item, ficha_modular.tipo_item)
            
            if not atividades:
                logger.warning(
                    f"⚠️ Nenhuma atividade encontrada para ID {ficha_modular.id_item} "
                    f"({ficha_modular.tipo_item.name})"
                )
                return

            # Criar atividades para o item atual
            atividades_criadas = 0
            
            # Obter nome do item da ficha técnica para usar nos logs
            nome_item_para_log = ficha_modular.id_item
            try:
                # Tentar obter um nome mais descritivo
                if hasattr(ficha_modular, 'nome'):
                    nome_item_para_log = ficha_modular.nome
                elif hasattr(ficha_modular, 'descricao'):
                    nome_item_para_log = ficha_modular.descricao
            except:
                pass
            
            for dados_gerais, dados_atividade in atividades:
                try:
                    # Usar nome do dados_gerais, senão usar da ficha técnica como fallback
                    nome_item_final = dados_gerais.get("nome_item", nome_item_para_log)
                    
                    atividade = AtividadeModular(
                        id_ordem=self.id_ordem,
                        id=len(self.atividades_modulares) + 1,
                        id_atividade=dados_atividade["id_atividade"],
                        tipo_item=ficha_modular.tipo_item,
                        quantidade=ficha_modular.quantidade_requerida,
                        id_pedido=self.id_pedido,
                        id_produto=self.id_produto,
                        funcionarios_elegiveis=self.funcionarios_elegiveis,
                        peso_unitario=ficha_modular.peso_unitario,
                        dados=dados_atividade,
                        nome_item=nome_item_final  # ✅ Nome mais robusto
                    )
                    self.atividades_modulares.append(atividade)
                    atividades_criadas += 1
                    
                except Exception as e:
                    logger.error(
                        f"❌ Erro ao criar atividade {dados_atividade.get('id_atividade', 'N/A')}: {e}"
                    )
                    continue

            logger.info(
                f"✅ {atividades_criadas} atividades criadas para ID {ficha_modular.id_item} "
                f"({ficha_modular.tipo_item.name})"
            )

        except Exception as e:
            logger.error(f"❌ Erro ao processar item {ficha_modular.id_item}: {e}")

        # Processar subprodutos recursivamente
        try:
            estimativas = ficha_modular.calcular_quantidade_itens()
            subprodutos_processados = 0
            
            for item_dict, quantidade in estimativas:
                tipo = item_dict.get("tipo_item")
                id_ficha = item_dict.get("id_ficha_tecnica")

                if tipo == "SUBPRODUTO" and id_ficha:
                    try:
                        _, dados_ficha_sub = buscar_ficha_tecnica_por_id(id_ficha, TipoItem.SUBPRODUTO)
                        ficha_sub = FichaTecnicaModular(dados_ficha_sub, quantidade)
                        self._criar_atividades_recursivas(ficha_sub)
                        subprodutos_processados += 1
                        
                    except Exception as e:
                        logger.error(f"❌ Erro ao processar subproduto {id_ficha}: {e}")
                        continue
            
            if subprodutos_processados > 0:
                logger.info(f"✅ {subprodutos_processados} subprodutos processados recursivamente")
                
        except Exception as e:
            logger.error(f"❌ Erro ao processar subprodutos: {e}")

    # =============================================================================
    #                        EXECUÇÃO DAS ATIVIDADES - CORRIGIDA
    # =============================================================================

    def executar_atividades_em_ordem(self):
        """
        ✅ CORREÇÃO PRINCIPAL: Executa todas as atividades em ordem de dependência.
        Se qualquer atividade do PRODUTO falhar, cancela o pedido inteiro incluindo SUBPRODUTOS.
        """
        total_atividades = len(self.atividades_modulares)
        logger.info(
            f"🚀 Iniciando execução do pedido {self.id_pedido} com {total_atividades} atividades"
        )
        
        if total_atividades == 0:
            logger.warning(f"⚠️ Nenhuma atividade para executar no pedido {self.id_pedido}")
            return
        
        try:
            # ✅ EXECUÇÃO SEQUENCIAL COM CANCELAMENTO EM CASCATA
            # Primeiro tenta executar todas as atividades do produto principal
            self._executar_atividades_produto()
            
            # Se chegou até aqui, produto foi executado com sucesso
            # Agora pode executar subprodutos
            self._executar_atividades_subproduto()
            
            logger.info(
                f"✅ Pedido {self.id_pedido} executado com sucesso! "
                f"Total de atividades executadas: {len(self.atividades_executadas)}"
            )
            
        except Exception as e:
            logger.error(f"❌ Falha na execução do pedido {self.id_pedido}: {e}")
            
            # ✅ CANCELAMENTO EM CASCATA
            self._cancelar_pedido_completo(str(e))
            raise

    def _executar_atividades_produto(self):
        """
        ✅ CORREÇÃO: Executa atividades do produto principal em ordem reversa.
        Se QUALQUER atividade falhar, levanta exceção para cancelar tudo.
        """
        atividades_produto = [
            a for a in self.atividades_modulares 
            if a.tipo_item == TipoItem.PRODUTO
        ]
        
        if not atividades_produto:
            logger.info(f"ℹ️ Nenhuma atividade de PRODUTO para executar no pedido {self.id_pedido}")
            return
        
        # Ordenar em ordem reversa (última atividade primeiro)
        atividades_ordenadas = sorted(
            atividades_produto,
            key=lambda a: a.id_atividade,
            reverse=True
        )
        
        logger.info(
            f"🔄 Executando {len(atividades_ordenadas)} atividades de PRODUTO "
            f"(CANCELAMENTO EM CASCATA ativado)"
        )
        
        # ✅ MARCAR A ÚLTIMA ATIVIDADE (primeira na ordem reversa)
        if atividades_ordenadas:
            atividades_ordenadas[0].eh_ultima_atividade_pedido = True
            logger.debug(f"🏁 Atividade {atividades_ordenadas[0].id_atividade} marcada como última do pedido")
        
        current_fim = self.fim_jornada
        inicio_prox_atividade = self.fim_jornada
        atividade_sucessora = None

        for i, atividade in enumerate(atividades_ordenadas):
            logger.info(
                f"🔄 Executando atividade PRODUTO {i+1}/{len(atividades_ordenadas)}: "
                f"{atividade.nome_atividade} (ID {atividade.id_atividade})"
            )
            
            # ✅ Para a última atividade com tempo_maximo_de_espera = 0
            if i == 0:  # Primeira iteração = última atividade na execução real
                if hasattr(atividade, 'tempo_maximo_de_espera') and atividade.tempo_maximo_de_espera is not None:
                    if atividade.tempo_maximo_de_espera == timedelta(0):
                        logger.info(
                            f"⏰ Última atividade {atividade.id_atividade} tem tempo_maximo_de_espera=0. "
                            f"Deve terminar EXATAMENTE às {self.fim_jornada.strftime('%H:%M')}"
                        )
                        atividade.fim_obrigatorio = self.fim_jornada
            
            try:
                sucesso, inicio_atual, fim_atual = self._executar_atividade_individual(
                    atividade, current_fim, atividade_sucessora, inicio_prox_atividade
                )
                
                # ✅ VALIDAÇÃO CRÍTICA: Se falhou, cancela TUDO
                if not sucesso:
                    erro_msg = (
                        f"❌ FALHA CRÍTICA: Atividade PRODUTO {atividade.id_atividade} "
                        f"({atividade.nome_atividade}) não pôde ser alocada. "
                        f"CANCELANDO PEDIDO COMPLETO incluindo subprodutos."
                    )
                    logger.error(erro_msg)
                    raise RuntimeError(erro_msg)
                
                # ✅ VALIDAÇÃO DE PONTUALIDADE para última atividade
                if i == 0 and hasattr(atividade, 'tempo_maximo_de_espera') and atividade.tempo_maximo_de_espera == timedelta(0):
                    if fim_atual != self.fim_jornada:
                        diferenca = self.fim_jornada - fim_atual
                        erro_msg = (
                            f"❌ FALHA DE PONTUALIDADE: Última atividade {atividade.id_atividade} "
                            f"({atividade.nome_atividade}) deveria terminar exatamente às "
                            f"{self.fim_jornada.strftime('%H:%M')}, mas terminou às "
                            f"{fim_atual.strftime('%H:%M')}. Diferença: {diferenca}. "
                            f"CANCELANDO PEDIDO COMPLETO."
                        )
                        logger.error(erro_msg)
                        raise RuntimeError(erro_msg)
                    else:
                        logger.info(
                            f"✅ Última atividade termina pontualmente às {fim_atual.strftime('%H:%M')} "
                            f"conforme exigido (tempo_maximo_de_espera=0)"
                        )
                
                # ✅ REGISTRO DE SUCESSO
                self.atividades_executadas.append(atividade)
                
                # Atualizar para próxima iteração
                inicio_prox_atividade = inicio_atual
                atividade_sucessora = atividade
                current_fim = atividade.inicio_real
                
                logger.info(
                    f"✅ Atividade PRODUTO {atividade.id_atividade} executada com sucesso: "
                    f"{inicio_atual.strftime('%H:%M')} - {fim_atual.strftime('%H:%M')}"
                )
                
            except Exception as e:
                # ✅ QUALQUER ERRO = CANCELAMENTO COMPLETO
                erro_msg = (
                    f"❌ ERRO NA ATIVIDADE PRODUTO {atividade.id_atividade} "
                    f"({atividade.nome_atividade}): {e}. "
                    f"CANCELANDO PEDIDO COMPLETO."
                )
                logger.error(erro_msg)
                registrar_erro_execucao_pedido(self.id_ordem, self.id_pedido, RuntimeError(erro_msg))
                raise RuntimeError(erro_msg) from e
        
        logger.info(
            f"✅ Todas as {len(atividades_ordenadas)} atividades de PRODUTO executadas com sucesso! "
            f"Prosseguindo para subprodutos."
        )
            
    def _executar_atividades_subproduto(self):
        """
        ✅ CORREÇÃO: Executa atividades dos subprodutos.
        Se algum SUBPRODUTO falhar, verifica se é uma falha crítica que deve cancelar o pedido.
        """
        atividades_sub = [
            a for a in self.atividades_modulares 
            if a.tipo_item == TipoItem.SUBPRODUTO
        ]
        
        if not atividades_sub:
            logger.info(f"ℹ️ Nenhuma atividade de SUBPRODUTO para executar no pedido {self.id_pedido}")
            return
        
        logger.info(
            f"🔄 Executando {len(atividades_sub)} atividades de SUBPRODUTO "
            f"(PRODUTO já executado com sucesso - VALIDAÇÃO CRÍTICA ativa)"
        )
        
        atividade_sucessora = None
        inicio_prox_atividade = self.fim_jornada
        
        # Usar o fim da última atividade de produto como limite superior
        atividades_produto_executadas = [
            a for a in self.atividades_executadas 
            if a.tipo_item == TipoItem.PRODUTO and hasattr(a, 'inicio_real')
        ]
        
        if atividades_produto_executadas:
            current_fim = min([a.inicio_real for a in atividades_produto_executadas])
            logger.debug(f"⏰ Limite superior para subprodutos: {current_fim.strftime('%H:%M')}")
        else:
            current_fim = self.fim_jornada

        # ✅ NOVA LÓGICA: Contadores para detecção de falhas críticas
        atividades_subproduto_executadas = 0
        atividades_subproduto_falharam = 0

        for i, atividade in enumerate(atividades_sub):
            logger.info(
                f"🔄 Executando atividade SUBPRODUTO {i+1}/{len(atividades_sub)}: "
                f"{atividade.nome_atividade} (ID {atividade.id_atividade})"
            )
            
            try:
                sucesso, inicio_atual, fim_atual = self._executar_atividade_individual(
                    atividade, current_fim, atividade_sucessora, inicio_prox_atividade
                )
                
                if not sucesso:
                    atividades_subproduto_falharam += 1
                    logger.error(
                        f"❌ FALHA CRÍTICA: Atividade SUBPRODUTO {atividade.id_atividade} "
                        f"({atividade.nome_atividade}) não pôde ser executada. "
                        f"Isso indica incompatibilidade de equipamentos ou recursos insuficientes."
                    )
                    
                    # ✅ VALIDAÇÃO CRÍTICA: Se PRODUTO já foi executado, mas SUBPRODUTO essencial falha
                    # Isso indica um problema grave que invalida todo o pedido
                    if len(self.atividades_executadas) > 0:  # Há atividades do PRODUTO executadas
                        erro_msg = (
                            f"❌ FALHA CRÍTICA DE DEPENDÊNCIA: "
                            f"Atividade SUBPRODUTO {atividade.id_atividade} ({atividade.nome_atividade}) "
                            f"é ESSENCIAL para o pedido mas falhou durante execução. "
                            f"Motivo provável: quantidade abaixo do mínimo de equipamento, "
                            f"conflito de recursos ou restrições técnicas. "
                            f"Como o PRODUTO já foi parcialmente executado, isso gera um estado inválido. "
                            f"CANCELANDO pedido completo e fazendo rollback de {len(self.atividades_executadas)} atividade(s) já executada(s)."
                        )
                        logger.error(erro_msg)
                        raise RuntimeError(erro_msg)
                    
                    # Se nenhum produto foi executado ainda, pode continuar
                    logger.warning(
                        f"⚠️ Atividade SUBPRODUTO {atividade.id_atividade} falhou, "
                        f"mas nenhum PRODUTO foi executado ainda. Continuando..."
                    )
                    continue
                
                # ✅ SUCESSO: Registrar e continuar
                atividades_subproduto_executadas += 1
                self.atividades_executadas.append(atividade)
                
                # Atualizar para próxima iteração
                inicio_prox_atividade = inicio_atual
                atividade_sucessora = atividade
                current_fim = atividade.inicio_real
                
                logger.info(
                    f"✅ Atividade SUBPRODUTO {atividade.id_atividade} executada: "
                    f"{inicio_atual.strftime('%H:%M')} - {fim_atual.strftime('%H:%M')}"
                )
                
            except Exception as e:
                atividades_subproduto_falharam += 1
                
                # ✅ VERIFICAR SE É FALHA CRÍTICA OU TOLERÁVEL
                if len(self.atividades_executadas) > 0:  # Há atividades do PRODUTO executadas
                    # Falha crítica - deve cancelar tudo
                    erro_msg = (
                        f"❌ FALHA CRÍTICA DE SUBPRODUTO: "
                        f"Erro na atividade SUBPRODUTO {atividade.id_atividade}: {e}. "
                        f"Como {len(self.atividades_executadas)} atividade(s) do PRODUTO já foram executadas, "
                        f"isso gera estado inválido. CANCELANDO pedido completo."
                    )
                    logger.error(erro_msg)
                    raise RuntimeError(erro_msg) from e
                else:
                    # Falha tolerável - pode continuar
                    logger.warning(
                        f"⚠️ Erro na atividade SUBPRODUTO {atividade.id_atividade}: {e}. "
                        f"Nenhum PRODUTO executado ainda. Continuando..."
                    )
                    salvar_erro_em_log(self.id_ordem, self.id_pedido, e)
                    continue

        # ✅ RELATÓRIO FINAL DOS SUBPRODUTOS
        logger.info(
            f"📊 Execução de SUBPRODUTOS concluída: "
            f"✅ {atividades_subproduto_executadas} executadas, "
            f"❌ {atividades_subproduto_falharam} falharam, "
            f"Total: {len(atividades_sub)}"
        )

    def _cancelar_pedido_completo(self, motivo: str):
        """
        ✅ NOVO MÉTODO: Cancela o pedido completo fazendo rollback de todas as atividades.
        """
        logger.error(
            f"🚫 CANCELANDO PEDIDO COMPLETO {self.id_pedido} - Motivo: {motivo}"
        )
        
        self.pedido_cancelado = True
        
        # Fazer rollback de todas as atividades executadas com sucesso até agora
        if self.atividades_executadas:
            logger.info(
                f"🔁 Fazendo rollback de {len(self.atividades_executadas)} atividades já executadas"
            )
            
            for atividade in self.atividades_executadas:
                try:
                    # Rollback de equipamentos
                    if hasattr(atividade, 'equipamentos_selecionados') and atividade.equipamentos_selecionados:
                        rollback_equipamentos(
                            equipamentos_alocados=atividade.equipamentos_selecionados,
                            id_ordem=self.id_ordem,
                            id_pedido=self.id_pedido,
                            id_atividade=atividade.id_atividade
                        )
                        logger.debug(f"🔄 Rollback equipamentos atividade {atividade.id_atividade}")
                    
                    # Marcar atividade como não alocada
                    atividade.alocada = False
                    
                except Exception as e:
                    logger.error(f"❌ Erro no rollback da atividade {atividade.id_atividade}: {e}")
        
        # Rollback completo adicional
        self._executar_rollback_completo()
        
        logger.error(
            f"🚫 PEDIDO {self.id_pedido} CANCELADO COMPLETAMENTE. "
            f"Motivo: {motivo}"
        )

    def _executar_atividade_individual(
        self, 
        atividade: AtividadeModular, 
        current_fim: datetime, 
        atividade_sucessora: AtividadeModular, 
        inicio_prox_atividade: datetime
    ):
        """
        Executa uma atividade individual verificando restrições de tempo.
        """
        logger.debug(
            f"🔧 Tentando alocar atividade {atividade.id_atividade} "
            f"com fim em {current_fim.strftime('%H:%M')}"
        )
        
        # Tentar alocar equipamentos e funcionários
        sucesso, inicio_atual, fim_atual, _, equipamentos_alocados = atividade.tentar_alocar_e_iniciar_equipamentos(
            self.inicio_jornada, current_fim
        )
        
        if not sucesso:
            logger.warning(f"❌ Falha na alocação da atividade {atividade.id_atividade}")
            return False, None, None

        logger.debug(f"📦 Equipamentos alocados: {len(equipamentos_alocados) if equipamentos_alocados else 0}")

        # Verificar tempo máximo de espera se houver atividade sucessora
        if atividade_sucessora and fim_atual and inicio_prox_atividade:
            self._verificar_tempo_maximo_espera(
                atividade, atividade_sucessora, fim_atual, inicio_prox_atividade
            )

        # Registrar equipamentos alocados no pedido
        if sucesso and equipamentos_alocados:
            self.equipamentos_alocados_no_pedido.extend(equipamentos_alocados)
            logger.debug(f"📋 Total de equipamentos no pedido: {len(self.equipamentos_alocados_no_pedido)}")
        
        return sucesso, inicio_atual, fim_atual

    def _verificar_tempo_maximo_espera(
        self, 
        atividade_atual: AtividadeModular, 
        atividade_sucessora: AtividadeModular,
        fim_atual: datetime, 
        inicio_prox_atividade: datetime
    ):
        """
        ✅ CORREÇÃO DO BUG: Verifica se o tempo de espera entre atividades não excede o limite máximo.
        Agora valida corretamente tempo_maximo_de_espera = timedelta(0)
        """
        # ✅ VERIFICAÇÃO CORRIGIDA: Verificar se o atributo existe e não é None
        if not hasattr(atividade_sucessora, 'tempo_maximo_de_espera') or atividade_sucessora.tempo_maximo_de_espera is None:
            logger.debug("ℹ️ Atividade sucessora não possui tempo máximo de espera definido")
            return
        
        tempo_max_espera = atividade_sucessora.tempo_maximo_de_espera
        atraso = inicio_prox_atividade - fim_atual

        logger.debug(
            f"⏱️ Verificação de tempo entre atividades:\n"
            f"   Atual: {atividade_atual.id_atividade} (fim: {fim_atual.strftime('%H:%M:%S')})\n"
            f"   Sucessora: {atividade_sucessora.id_atividade} (início: {inicio_prox_atividade.strftime('%H:%M:%S')})\n"
            f"   Atraso: {atraso} | Máximo permitido: {tempo_max_espera}"
        )

        # ✅ VALIDAÇÃO RIGOROSA: Agora funciona corretamente para tempo_max_espera = timedelta(0)
        if atraso > tempo_max_espera:
            raise RuntimeError(
                f"❌ Tempo máximo de espera excedido entre atividades:\n"
                f"   Atividade atual: {atividade_atual.id_atividade} ({atividade_atual.nome_atividade})\n"
                f"   Atividade sucessora: {atividade_sucessora.id_atividade} ({atividade_sucessora.nome_atividade})\n"
                f"   Fim da atual: {fim_atual.strftime('%d/%m %H:%M:%S')}\n"
                f"   Início da sucessora: {inicio_prox_atividade.strftime('%d/%m %H:%M:%S')}\n"
                f"   Atraso detectado: {atraso}\n"
                f"   Máximo permitido: {tempo_max_espera}\n"
                f"   Excesso: {atraso - tempo_max_espera}"
            )
        else:
            logger.debug(f"✅ Tempo de espera dentro do limite permitido")

    # =============================================================================
    #                           ROLLBACK
    # =============================================================================

    def _executar_rollback_completo(self):
        """Executa rollback completo do pedido com logs detalhados"""
        logger.info(f"🔁 Executando rollback completo do pedido {self.id_pedido} da ordem {self.id_ordem}")

        equipamentos_liberados = 0
        funcionarios_liberados = 0

        try:
            # Liberar equipamentos de todas as atividades
            for atividade in self.atividades_modulares:
                if hasattr(atividade, 'equipamentos_selecionados') and atividade.equipamentos_selecionados:
                    rollback_equipamentos(
                        equipamentos_alocados=atividade.equipamentos_selecionados,
                        id_ordem=self.id_ordem,
                        id_pedido=self.id_pedido,
                        id_atividade=atividade.id_atividade
                    )
                    equipamentos_liberados += len(atividade.equipamentos_selecionados)

            # Liberar funcionários
            if self.funcionarios_elegiveis:
                rollback_funcionarios(
                    funcionarios_alocados=self.funcionarios_elegiveis,
                    id_ordem=self.id_ordem,
                    id_pedido=self.id_pedido
                )
                funcionarios_liberados = len(self.funcionarios_elegiveis)

            # Limpar logs
            apagar_logs_por_pedido_e_ordem(self.id_ordem, self.id_pedido)

            logger.info(
                f"✅ Rollback concluído: "
                f"{equipamentos_liberados} equipamentos e {funcionarios_liberados} funcionários liberados"
            )
            
        except Exception as e:
            logger.error(f"❌ Erro durante rollback: {e}")

    def rollback_pedido(self):
        """Método público para rollback manual"""
        logger.info(f"🔄 Rollback manual solicitado para pedido {self.id_pedido}")
        self._cancelar_pedido_completo("Rollback manual solicitado")

    # =============================================================================
    #                    CONTROLE DE ALMOXARIFADO
    # =============================================================================

    def verificar_disponibilidade_estoque(self, data_execucao: datetime):
        """
        Verifica se há estoque suficiente para executar o pedido usando gestor otimizado.
        Considera políticas de produção (ESTOCADO vs SOB_DEMANDA).
        """
        if not self.ficha_tecnica_modular:
            raise ValueError("Ficha técnica ainda não foi montada")

        if not self.gestor_almoxarifado:
            logger.warning("⚠️ Gestor de almoxarifado não disponível - pulando verificação de estoque")
            return

        logger.info(f"🔍 Verificando disponibilidade de estoque para pedido {self.id_pedido}")

        itens_insuficientes = []
        estimativas = self.ficha_tecnica_modular.calcular_quantidade_itens()

        for item_dict, quantidade in estimativas:
            id_item = item_dict["id_item"]
            tipo_item = item_dict["tipo_item"]
            nome_item = item_dict["descricao"]
            politica = item_dict.get("politica_producao", "ESTOCADO")

            logger.debug(
                f"🧪 Verificando item '{nome_item}' (ID {id_item}) | "
                f"Tipo: {tipo_item} | Política: {politica} | Quantidade: {quantidade}"
            )

            # Itens SOB_DEMANDA não precisam verificação de estoque
            if tipo_item in {"SUBPRODUTO", "PRODUTO"} and politica == "SOB_DEMANDA":
                logger.debug(f"⏭️ Item {id_item} é SOB_DEMANDA - pulando verificação")
                continue

            # Verificar disponibilidade para itens ESTOCADOS
            if politica == "ESTOCADO":
                try:
                    disponibilidade = self.gestor_almoxarifado.verificar_disponibilidade_projetada_para_data(
                        id_item=id_item,
                        data=data_execucao.date(),
                        quantidade=quantidade
                    )

                    if not disponibilidade:
                        estoque_atual = self.gestor_almoxarifado.obter_estoque_atual(id_item)
                        itens_insuficientes.append({
                            "id": id_item,
                            "descricao": nome_item,
                            "quantidade_necessaria": quantidade,
                            "disponivel": estoque_atual
                        })
                        
                except Exception as e:
                    logger.error(f"❌ Erro ao verificar estoque do item {id_item}: {e}")
                    itens_insuficientes.append({
                        "id": id_item,
                        "descricao": nome_item,
                        "quantidade_necessaria": quantidade,
                        "disponivel": 0,
                        "erro": str(e)
                    })

        # Reportar itens insuficientes
        if itens_insuficientes:
            logger.error(f"❌ Encontrados {len(itens_insuficientes)} itens com estoque insuficiente:")
            
            for item in itens_insuficientes:
                erro_msg = (
                    f"   Item '{item['descricao']}' (ID {item['id']}): "
                    f"Necessário {item['quantidade_necessaria']}, "
                    f"Disponível {item['disponivel']}"
                )
                if 'erro' in item:
                    erro_msg += f" (Erro: {item['erro']})"
                logger.error(erro_msg)
            
            raise RuntimeError(
                f"Pedido {self.id_pedido} não pode ser executado. "
                f"{len(itens_insuficientes)} itens com estoque insuficiente."
            )
        else:
            logger.info(f"✅ Estoque suficiente para todos os itens do pedido {self.id_pedido}")

    def gerar_comanda_de_reserva(self, data_execucao: datetime):
        """
        Gera comanda de reserva para o pedido usando gestor otimizado.
        """
        if not self.ficha_tecnica_modular:
            raise ValueError("Ficha técnica ainda não foi montada")

        if not self.gestor_almoxarifado:
            logger.warning("⚠️ Gestor de almoxarifado não disponível - pulando geração de comanda")
            return

        logger.info(f"📋 Gerando comanda de reserva para pedido {self.id_pedido}")

        try:
            gerar_comanda_reserva_modulo(
                id_ordem=self.id_ordem,
                id_pedido=self.id_pedido,
                ficha=self.ficha_tecnica_modular,
                gestor=self.gestor_almoxarifado,
                data_execucao=data_execucao
            )
            
            logger.info(f"✅ Comanda de reserva gerada com sucesso para pedido {self.id_pedido}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao gerar comanda de reserva: {e}")
            raise

    # =============================================================================
    #                           UTILITÁRIOS
    # =============================================================================

    def exibir_historico_de_funcionarios(self):
        """Exibe histórico de ocupação de todos os funcionários"""
        logger.info("📊 Exibindo histórico de funcionários")
        
        try:
            for funcionario in funcionarios_disponiveis:
                funcionario.mostrar_agenda()
        except Exception as e:
            logger.error(f"❌ Erro ao exibir histórico de funcionários: {e}")

    def mostrar_estrutura(self):
        """Mostra a estrutura da ficha técnica"""
        if self.ficha_tecnica_modular:
            logger.info(f"📋 Mostrando estrutura da ficha técnica do pedido {self.id_pedido}")
            self.ficha_tecnica_modular.mostrar_estrutura()
        else:
            logger.warning(f"⚠️ Ficha técnica não montada para pedido {self.id_pedido}")

    def obter_resumo_pedido(self) -> dict:
        """Retorna um resumo completo do pedido"""
        atividades_alocadas = sum(1 for a in self.atividades_modulares if a.alocada)
        
        tempos = []
        if self.atividades_modulares:
            for atividade in self.atividades_modulares:
                if hasattr(atividade, 'inicio_real') and atividade.inicio_real:
                    tempos.append(atividade.inicio_real)
                if hasattr(atividade, 'fim_real') and atividade.fim_real:
                    tempos.append(atividade.fim_real)
        
        inicio_real = min(tempos) if tempos else None
        fim_real = max(tempos) if tempos else None
        
        return {
            "id_pedido": self.id_pedido,
            "id_ordem": self.id_ordem,
            "id_produto": self.id_produto,
            "tipo_item": self.tipo_item.name,
            "quantidade": self.quantidade,
            "inicio_jornada": self.inicio_jornada.isoformat(),
            "fim_jornada": self.fim_jornada.isoformat(),
            "inicio_real": inicio_real.isoformat() if inicio_real else None,
            "fim_real": fim_real.isoformat() if fim_real else None,
            "total_atividades": len(self.atividades_modulares),
            "atividades_alocadas": atividades_alocadas,
            "atividades_executadas": len(self.atividades_executadas),
            "funcionarios_elegiveis": len(self.funcionarios_elegiveis),
            "equipamentos_alocados": len(self.equipamentos_alocados_no_pedido),
            "tem_gestor_almoxarifado": self.gestor_almoxarifado is not None,
            "ficha_tecnica_montada": self.ficha_tecnica_modular is not None,
            "pedido_cancelado": self.pedido_cancelado
        }

    def _filtrar_funcionarios_por_item(self, id_item: int) -> List[Funcionario]:
        """Filtra funcionários por tipo necessário para um item específico"""
        try:
            tipos_necessarios = buscar_tipos_profissionais_por_id_item(id_item)
            funcionarios_filtrados = [
                f for f in self.todos_funcionarios 
                if f.tipo_profissional in tipos_necessarios
            ]
            
            logger.debug(
                f"👥 Funcionários filtrados para item {id_item}: "
                f"{len(funcionarios_filtrados)}/{len(self.todos_funcionarios)}"
            )
            
            return funcionarios_filtrados
            
        except Exception as e:
            logger.error(f"❌ Erro ao filtrar funcionários para item {id_item}: {e}")
            return self.todos_funcionarios

    def __repr__(self):
        status = f"{len([a for a in self.atividades_modulares if a.alocada])}/{len(self.atividades_modulares)} alocadas"
        cancelado = " [CANCELADO]" if self.pedido_cancelado else ""
        return (
            f"<PedidoDeProducao {self.id_pedido} | "
            f"Produto {self.id_produto} | "
            f"Qtd {self.quantidade} | "
            f"Atividades: {status}{cancelado}>"
        )