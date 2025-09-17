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
from utils.logs.quantity_logger import quantity_logger
from utils.logs.timing_exceptions import (
    TimingError, 
    InterActivityTimingError, 
    IntraActivityTimingError,
    MaximumWaitTimeExceededError  # Para compatibilidade
)
from utils.logs.timing_logger import timing_logger
from utils.logs.formatador_timing_limpo import reformatar_erro_timing_para_novo_formato
from services.gestor_comandas.gestor_comandas import gerar_comanda_reserva as gerar_comanda_reserva_modulo

logger = setup_logger("PedidoDeProducao")

# Debug - Sistema de debug para rastreamento
from datetime import datetime
import json

# ====================================================================
#                   SISTEMA DE RASTREAMENTO DE FALHAS
# ====================================================================

class RegistroTentativasFalhadas:
    """
    Classe para registrar todas as tentativas de alocação que falharam
    durante a execução de um pedido.
    """
    def __init__(self):
        self.tentativas_falhadas = []
        self.equipamentos_tentados = set()

    def adicionar_falha(self, equipamento: str, motivo: str, horario_tentativa: str = "", detalhes: str = ""):
        """Adiciona uma tentativa de alocação que falhou"""
        self.tentativas_falhadas.append({
            'equipamento': equipamento,
            'motivo': motivo,
            'horario_tentativa': horario_tentativa,
            'detalhes': detalhes,
            'timestamp': datetime.now().isoformat()
        })
        self.equipamentos_tentados.add(equipamento)

    def obter_resumo_falhas(self) -> str:
        """Retorna um resumo das falhas para incluir no log"""
        if not self.tentativas_falhadas:
            return "Nenhuma tentativa específica registrada"

        resumo = "Equipamentos que falharam na alocação:\n"
        for falha in self.tentativas_falhadas:
            resumo += f"   ❌ {falha['equipamento']}: {falha['motivo']}\n"
            if falha['horario_tentativa']:
                resumo += f"      ⏰ Tentativa em: {falha['horario_tentativa']}\n"
            if falha['detalhes']:
                resumo += f"      📋 {falha['detalhes']}\n"

        return resumo.strip()

    def obter_lista_equipamentos(self) -> list:
        """Retorna lista de equipamentos que falharam"""
        return list(self.equipamentos_tentados)

    def limpar(self):
        """Limpa o registro para um novo pedido"""
        self.tentativas_falhadas.clear()
        self.equipamentos_tentados.clear()

# Instância global para o pedido atual
_registro_falhas_atual = RegistroTentativasFalhadas()

class DebugAtividades:
    def __init__(self):
        self.logs = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def log(self, categoria, item_id, item_nome, dados):
        evento = {
            "timestamp": datetime.now().isoformat(),
            "categoria": categoria,
            "item_id": item_id,
            "item_nome": item_nome,
            "dados": dados
        }
        self.logs.append(evento)
        print(f"DEBUG [{categoria}] Item {item_id} ({item_nome}): {dados}")
    
    def salvar_logs(self):
        arquivo = f"debug_pedido_producao_{self.timestamp}.json"
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump({"eventos": self.logs}, f, indent=2, ensure_ascii=False)
        print(f"Debug salvo em: {arquivo}")
        return arquivo

debug_atividades = DebugAtividades()


class PedidoDeProducao:
    """
    Classe principal para gerenciar um pedido de produção.
    Coordena a criação e execução de atividades modulares com verificação inteligente de estoque.
    CORRIGIDO: Implementa cancelamento em cascata se atividades do PRODUTO falharem.
    CORRIGIDO: Sincronização perfeita entre produto e subprodutos.
    
    SISTEMA DE TIMING INTEGRADO:
    - Detecta erros de tempo entre atividades (INTER-ATIVIDADE)
    - Detecta erros de tempo dentro de atividades (INTRA-ATIVIDADE via AtividadeModular)
    - Registra logs estruturados para ambos os tipos
    - Cancela pedidos com problemas temporais críticos
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
        self.bypass_capacidade = None  # Set de TipoEquipamento para ignorar validação de capacidade
        
        # Log de inicialização
        logger.info(
            f"Criando pedido {self.id_pedido} da ordem {self.id_ordem} | "
            f"Produto: {self.id_produto} ({self.tipo_item.name}) | "
            f"Quantidade: {self.quantidade} | "
            f"Período: {self.inicio_jornada.strftime('%d/%m %H:%M')} - {self.fim_jornada.strftime('%d/%m %H:%M')}"
        )
    
    def configurar_bypass_capacidade(self, tipos_bypass):
        """
        Configura quais tipos de equipamentos devem ignorar validação de capacidade.
        
        Args:
            tipos_bypass: Set de TipoEquipamento para ignorar, ou None para validar todos
        """
        self.bypass_capacidade = tipos_bypass
        if tipos_bypass:
            logger.info(f"🔧 BYPASS: Pedido {self.id_pedido} configurado para ignorar validação de capacidade")
            logger.info(f"📋 Tipos com bypass: {[tipo.name for tipo in tipos_bypass]}")
        else:
            logger.info(f"✅ VALIDAÇÃO: Pedido {self.id_pedido} configurado para validar capacidade normalmente")

    # =============================================================================
    #                        MONTAGEM DA ESTRUTURA
    # =============================================================================

    def montar_estrutura(self):
        """Monta a estrutura técnica do pedido baseada na ficha técnica"""
        try:
            logger.info(f"Montando estrutura técnica do pedido {self.id_pedido}")
            
            _, dados_ficha = buscar_ficha_tecnica_por_id(self.id_produto, tipo_item=self.tipo_item)
            self.ficha_tecnica_modular = FichaTecnicaModular(
                dados_ficha_tecnica=dados_ficha,
                quantidade_requerida=self.quantidade
            )
            
            # Filtrar funcionários considerando produto principal e subprodutos
            self.funcionarios_elegiveis = self._filtrar_funcionarios_abrangente()
            
            logger.info(
                f"Estrutura montada: {len(self.funcionarios_elegiveis)} funcionários elegíveis"
            )
            
        except Exception as e:
            logger.error(f"Erro ao montar estrutura do pedido {self.id_pedido}: {e}")
            raise
        
    def _filtrar_funcionarios_abrangente(self) -> List[Funcionario]:
        """
        Filtra funcionários considerando tanto o produto principal quanto os subprodutos.
        Garante que todos os tipos profissionais necessários estejam disponíveis.
        """
        if not self.ficha_tecnica_modular:
            logger.warning("Ficha técnica não montada, retornando todos os funcionários")
            return self.todos_funcionarios
            
        tipos_necessarios = set()
        
        try:
            # Adicionar tipos do produto principal
            tipos_produto = buscar_tipos_profissionais_por_id_item(self.id_produto)
            tipos_necessarios.update(tipos_produto)
            logger.debug(f"Tipos para produto principal {self.id_produto}: {tipos_produto}")
            
            # Adicionar tipos dos subprodutos
            estimativas = self.ficha_tecnica_modular.calcular_quantidade_itens()
            for item_dict, _ in estimativas:
                if item_dict.get("tipo_item") == "SUBPRODUTO":
                    sub_id = item_dict.get("id_ficha_tecnica") 
                    if sub_id:
                        tipos_sub = buscar_tipos_profissionais_por_id_item(sub_id)
                        tipos_necessarios.update(tipos_sub)
                        logger.debug(f"Tipos para subproduto {sub_id}: {tipos_sub}")
            
            funcionarios_filtrados = [
                f for f in self.todos_funcionarios 
                if f.tipo_profissional in tipos_necessarios
            ]
            
            logger.info(
                f"Funcionários filtrados: {len(funcionarios_filtrados)}/{len(self.todos_funcionarios)} "
                f"para tipos {[t.name for t in tipos_necessarios]}"
            )
            
            return funcionarios_filtrados
            
        except Exception as e:
            logger.error(f"Erro ao filtrar funcionários: {e}")
            return self.todos_funcionarios

    # =============================================================================
    #                      VERIFICAÇÃO DE ESTOQUE
    # =============================================================================

    def _verificar_estoque_suficiente(self, id_item: int, quantidade_necessaria: float) -> bool:
        """
        VERSÃO COM DEBUG: Verifica se há estoque suficiente para um item específico.
        """
        # DEBUG - Início verificação de estoque
        debug_atividades.log(
            categoria="VERIFICACAO_ESTOQUE_INICIO",
            item_id=id_item,
            item_nome=f"item_{id_item}",
            dados={
                "quantidade_necessaria": quantidade_necessaria,
                "gestor_disponivel": self.gestor_almoxarifado is not None
            }
        )
        
        if not self.gestor_almoxarifado:
            debug_atividades.log(
                categoria="ERRO_GESTOR_INDISPONIVEL",
                item_id=id_item,
                item_nome=f"item_{id_item}",
                dados={"erro": "Gestor almoxarifado não disponível"}
            )
            logger.warning("Gestor de almoxarifado não disponível. Assumindo necessidade de produção.")
            return False
        
        try:
            # Buscar item usando método otimizado do gestor
            item = self.gestor_almoxarifado.obter_item_por_id(id_item)
            if not item:
                debug_atividades.log(
                    categoria="ERRO_ITEM_NAO_ENCONTRADO",
                    item_id=id_item,
                    item_nome=f"item_{id_item}",
                    dados={"erro": "Item não encontrado no almoxarifado"}
                )
                logger.warning(f"Item {id_item} não encontrado no almoxarifado")
                return False
            
            # CORREÇÃO: Usar ENUM diretamente, não string
            politica_enum = item.politica_producao
            
            # DEBUG - Item encontrado
            debug_atividades.log(
                categoria="ITEM_ENCONTRADO",
                item_id=id_item,
                item_nome=item.descricao,
                dados={
                    "politica_enum": str(politica_enum),
                    "politica_value": politica_enum.value,
                    "estoque_atual": self.gestor_almoxarifado.obter_estoque_atual(id_item),
                    "tipo_politica": type(politica_enum).__name__
                }
            )
            
            # Para SOB_DEMANDA: sempre produzir (não verificar estoque)
            if politica_enum == PoliticaProducao.SOB_DEMANDA:
                debug_atividades.log(
                    categoria="DECISAO_SOB_DEMANDA",
                    item_id=id_item,
                    item_nome=item.descricao,
                    dados={
                        "decisao": "SEMPRE_PRODUZIR",
                        "motivo": "Política SOB_DEMANDA"
                    }
                )
                logger.debug(
                    f"Item '{item.descricao}' (ID {id_item}) é SOB_DEMANDA. "
                    f"Produção será realizada independente do estoque."
                )
                return False  # Retorna False para forçar produção
            
            # Para ESTOCADO e AMBOS: verificar estoque atual
            if politica_enum in [PoliticaProducao.ESTOCADO, PoliticaProducao.AMBOS]:
                tem_estoque_suficiente = self.gestor_almoxarifado.verificar_estoque_atual_suficiente(
                    id_item, quantidade_necessaria
                )
                
                estoque_atual = self.gestor_almoxarifado.obter_estoque_atual(id_item)
                
                # DEBUG - Decisão de estoque
                debug_atividades.log(
                    categoria="DECISAO_ESTOQUE",
                    item_id=id_item,
                    item_nome=item.descricao,
                    dados={
                        "politica": politica_enum.value,
                        "quantidade_necessaria": quantidade_necessaria,
                        "estoque_atual": estoque_atual,
                        "tem_estoque_suficiente": tem_estoque_suficiente,
                        "decisao": "NAO_PRODUZIR" if tem_estoque_suficiente else "PRODUZIR"
                    }
                )
                
                logger.info(
                    f"Item '{item.descricao}' (ID {id_item}): "
                    f"Estoque atual: {estoque_atual} | "
                    f"Necessário: {quantidade_necessaria} | "
                    f"Política: {politica_enum.value} | "
                    f"Suficiente: {'SIM' if tem_estoque_suficiente else 'NAO'}"
                )
                
                return tem_estoque_suficiente
            
            # Política desconhecida - assumir necessidade de produção
            debug_atividades.log(
                categoria="POLITICA_DESCONHECIDA",
                item_id=id_item,
                item_nome=item.descricao,
                dados={
                    "politica_desconhecida": str(politica_enum),
                    "decisao": "PRODUZIR_POR_SEGURANCA"
                }
            )
            logger.warning(f"Política de produção desconhecida '{politica_enum}' para item {id_item}")
            return False
            
        except Exception as e:
            debug_atividades.log(
                categoria="ERRO_EXCECAO",
                item_id=id_item,
                item_nome=f"item_{id_item}",
                dados={
                    "erro": str(e),
                    "tipo_erro": type(e).__name__
                }
            )
            logger.warning(f"Erro ao verificar estoque do item {id_item}: {e}")
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
            
            logger.debug(f"Verificação em lote: {len(itens_necessarios)} itens verificados")
            return resultado
            
        except Exception as e:
            logger.error(f"Erro na verificação em lote: {e}")
            return {id_item: False for id_item, _ in itens_necessarios}

    # =============================================================================
    #                      CRIAÇÃO DE ATIVIDADES
    # =============================================================================

    def criar_atividades_modulares_necessarias(self):
        """
        Cria todas as atividades modulares necessárias baseadas na ficha técnica.
        CORRIGIDO: Verifica se atividades do PRODUTO foram criadas com sucesso.
        Se nenhuma atividade do PRODUTO for criada, cancela o pedido inteiro.
        """
        if not self.ficha_tecnica_modular:
            raise ValueError("Ficha técnica ainda não foi montada")

        logger.info(f"Criando atividades modulares para pedido {self.id_pedido}")
        
        self.atividades_modulares = []
        
        # NOVA LÓGICA: Separar contadores por tipo
        atividades_produto_criadas = 0
        atividades_subproduto_criadas = 0
        
        self._criar_atividades_recursivas(self.ficha_tecnica_modular)
        
        # CONTABILIZAR ATIVIDADES POR TIPO
        for atividade in self.atividades_modulares:
            if atividade.tipo_item == TipoItem.PRODUTO:
                atividades_produto_criadas += 1
            elif atividade.tipo_item == TipoItem.SUBPRODUTO:
                atividades_subproduto_criadas += 1
        
        logger.info(
            f"Atividades criadas para pedido {self.id_pedido}: "
            f"PRODUTO: {atividades_produto_criadas}, SUBPRODUTO: {atividades_subproduto_criadas}, "
            f"Total: {len(self.atividades_modulares)}"
        )
        
        # VALIDAÇÃO CRÍTICA: Se é um pedido de PRODUTO mas nenhuma atividade foi criada
        if self.tipo_item == TipoItem.PRODUTO and atividades_produto_criadas == 0:
            erro_msg = (
                f"FALHA CRÍTICA NA CRIAÇÃO DE ATIVIDADES: "
                f"Pedido {self.id_pedido} é do tipo PRODUTO (ID {self.id_produto}) "
                f"mas NENHUMA atividade do produto foi criada com sucesso. "
                f"Isso indica incompatibilidade nas faixas de quantidade ou configuração. "
                f"CANCELANDO pedido completo incluindo {atividades_subproduto_criadas} atividade(s) de subproduto."
            )
            logger.error(erro_msg)
            
            # LIMPAR ATIVIDADES DE SUBPRODUTO JÁ CRIADAS
            self.atividades_modulares.clear()
            
            raise RuntimeError(erro_msg)

    def _criar_atividades_recursivas(self, ficha_modular: FichaTecnicaModular):
        """
        VERSÃO COM DEBUG: Cria atividades de forma recursiva para produtos e subprodutos.
        """
        try:
            # DEBUG - Início criação atividades recursivas
            debug_atividades.log(
                categoria="CRIAR_ATIVIDADES_INICIO",
                item_id=ficha_modular.id_item,
                item_nome=getattr(ficha_modular, 'nome', f'item_{ficha_modular.id_item}'),
                dados={
                    "tipo_item": ficha_modular.tipo_item.value,
                    "quantidade_requerida": ficha_modular.quantidade_requerida
                }
            )
            
            logger.info(
                f"Analisando necessidade de produção para ID {ficha_modular.id_item} "
                f"({ficha_modular.tipo_item.name}) - Quantidade: {ficha_modular.quantidade_requerida}"
            )
            
            # NOVA LÓGICA: Verificação de estoque baseada no tipo de item e política
            
            # PRODUTOS sempre devem ser produzidos (não verificar estoque para produtos finais)
            if ficha_modular.tipo_item == TipoItem.PRODUTO:
                logger.info(
                    f"PRODUTO ID {ficha_modular.id_item} será sempre produzido "
                    f"(produtos finais não usam estoque)"
                )
                deve_produzir = True
                
            # SUBPRODUTOS: verificar baseado na política de produção  
            elif ficha_modular.tipo_item == TipoItem.SUBPRODUTO:
                # Verificar se há estoque suficiente
                tem_estoque_suficiente = self._verificar_estoque_suficiente(
                    ficha_modular.id_item, 
                    ficha_modular.quantidade_requerida
                )
                
                if tem_estoque_suficiente:
                    logger.info(
                        f"Estoque suficiente para SUBPRODUTO ID {ficha_modular.id_item}. "
                        f"Produção não necessária - usando estoque disponível."
                    )
                    deve_produzir = False
                else:
                    logger.info(
                        f"Estoque insuficiente para SUBPRODUTO ID {ficha_modular.id_item}. "
                        f"Produção será realizada com quantidade total: {ficha_modular.quantidade_requerida}"
                    )
                    deve_produzir = True
                    
            else:
                # INSUMOS ou outros tipos - normalmente não deveriam chegar aqui
                logger.warning(
                    f"Tipo de item inesperado: {ficha_modular.tipo_item.name} "
                    f"para ID {ficha_modular.id_item}"
                )
                deve_produzir = True
            
            # DEBUG - Decisão de produção
            debug_atividades.log(
                categoria="DECISAO_PRODUCAO",
                item_id=ficha_modular.id_item,
                item_nome=getattr(ficha_modular, 'nome', f'item_{ficha_modular.id_item}'),
                dados={
                    "tipo_item": ficha_modular.tipo_item.value,
                    "deve_produzir": deve_produzir,
                    "motivo": "PRODUTO_SEMPRE_PRODUZ" if ficha_modular.tipo_item == TipoItem.PRODUTO else "VERIFICACAO_ESTOQUE"
                }
            )
            
            # Se não deve produzir, parar aqui
            if not deve_produzir:
                debug_atividades.log(
                    categoria="PRODUCAO_CANCELADA",
                    item_id=ficha_modular.id_item,
                    item_nome=getattr(ficha_modular, 'nome', f'item_{ficha_modular.id_item}'),
                    dados={"motivo": "Estoque suficiente disponível"}
                )
                return
            
            # PRODUÇÃO NECESSÁRIA: Buscar e criar atividades para o item atual
            atividades = buscar_atividades_por_id_item(ficha_modular.id_item, ficha_modular.tipo_item)
            
            if not atividades:
                debug_atividades.log(
                    categoria="ERRO_ATIVIDADES_NAO_ENCONTRADAS",
                    item_id=ficha_modular.id_item,
                    item_nome=getattr(ficha_modular, 'nome', f'item_{ficha_modular.id_item}'),
                    dados={"erro": "Nenhuma atividade encontrada"}
                )
                logger.warning(
                    f"Nenhuma atividade encontrada para ID {ficha_modular.id_item} "
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
                    
                    debug_atividades.log(
                        categoria="ATIVIDADE_CRIADA",
                        item_id=ficha_modular.id_item,
                        item_nome=nome_item_final,
                        dados={
                            "id_atividade": dados_atividade["id_atividade"],
                            "nome_atividade": dados_atividade.get("nome_atividade", "N/A"),
                            "quantidade": ficha_modular.quantidade_requerida
                        }
                    )
                    
                    atividade = AtividadeModular(
                        id_ordem=self.id_ordem,
                        id=len(self.atividades_modulares) + 1,
                        id_atividade=dados_atividade["id_atividade"],
                        tipo_item=ficha_modular.tipo_item,
                        quantidade=ficha_modular.quantidade_requerida,  # Quantidade total (sem subtração)
                        id_pedido=self.id_pedido,
                        id_produto=self.id_produto,
                        funcionarios_elegiveis=self.funcionarios_elegiveis,
                        peso_unitario=ficha_modular.peso_unitario,
                        dados=dados_atividade,
                        nome_item=nome_item_final
                    )
                    
                    # Configura bypass de capacidade na atividade se habilitado no pedido
                    if self.bypass_capacidade:
                        atividade.configurar_bypass_capacidade(self.bypass_capacidade)
                        logger.info(f"🔧 BYPASS propagado para atividade {atividade.id_atividade} ({atividade.nome_item})")
                    self.atividades_modulares.append(atividade)
                    atividades_criadas += 1
                    
                except Exception as e:
                    debug_atividades.log(
                        categoria="ERRO_CRIAR_ATIVIDADE",
                        item_id=ficha_modular.id_item,
                        item_nome=nome_item_para_log,
                        dados={
                            "erro": str(e),
                            "id_atividade": dados_atividade.get('id_atividade', 'N/A')
                        }
                    )
                    logger.error(
                        f"Erro ao criar atividade {dados_atividade.get('id_atividade', 'N/A')}: {e}"
                    )
                    continue

            debug_atividades.log(
                categoria="ATIVIDADES_CRIADAS_SUCESSO",
                item_id=ficha_modular.id_item,
                item_nome=nome_item_para_log,
                dados={
                    "total_atividades_criadas": atividades_criadas,
                    "quantidade_total": ficha_modular.quantidade_requerida
                }
            )
            
            logger.info(
                f"{atividades_criadas} atividades criadas para ID {ficha_modular.id_item} "
                f"({ficha_modular.tipo_item.name}) - Quantidade total: {ficha_modular.quantidade_requerida}"
            )

        except Exception as e:
            debug_atividades.log(
                categoria="ERRO_GERAL_CRIAR_ATIVIDADES",
                item_id=ficha_modular.id_item,
                item_nome=getattr(ficha_modular, 'nome', f'item_{ficha_modular.id_item}'),
                dados={
                    "erro": str(e),
                    "tipo_erro": type(e).__name__
                }
            )
            logger.error(f"Erro ao processar item {ficha_modular.id_item}: {e}")

        # PROCESSAR SUBPRODUTOS RECURSIVAMENTE (independente se o item atual será produzido)
        # Os subprodutos podem ter estoque próprio e devem ser avaliados individualmente
        try:
            estimativas = ficha_modular.calcular_quantidade_itens()
            subprodutos_processados = 0
            
            for item_dict, quantidade in estimativas:
                tipo = item_dict.get("tipo_item")
                id_ficha = item_dict.get("id_ficha_tecnica")

                if tipo == "SUBPRODUTO" and id_ficha:
                    try:
                        debug_atividades.log(
                            categoria="PROCESSANDO_SUBPRODUTO",
                            item_id=id_ficha,
                            item_nome=f"subproduto_{id_ficha}",
                            dados={
                                "quantidade": quantidade,
                                "item_pai": ficha_modular.id_item
                            }
                        )
                        
                        _, dados_ficha_sub = buscar_ficha_tecnica_por_id(id_ficha, TipoItem.SUBPRODUTO)
                        ficha_sub = FichaTecnicaModular(dados_ficha_sub, quantidade)
                        self._criar_atividades_recursivas(ficha_sub)
                        subprodutos_processados += 1
                        
                    except Exception as e:
                        debug_atividades.log(
                            categoria="ERRO_PROCESSAR_SUBPRODUTO",
                            item_id=id_ficha,
                            item_nome=f"subproduto_{id_ficha}",
                            dados={
                                "erro": str(e),
                                "item_pai": ficha_modular.id_item
                            }
                        )
                        logger.error(f"Erro ao processar subproduto {id_ficha}: {e}")
                        continue
            
            if subprodutos_processados > 0:
                logger.info(f"{subprodutos_processados} subprodutos processados recursivamente")
                
        except Exception as e:
            debug_atividades.log(
                categoria="ERRO_PROCESSAR_TODOS_SUBPRODUTOS",
                item_id=ficha_modular.id_item,
                item_nome=getattr(ficha_modular, 'nome', f'item_{ficha_modular.id_item}'),
                dados={
                    "erro": str(e),
                    "tipo_erro": type(e).__name__
                }
            )
            logger.error(f"Erro ao processar subprodutos: {e}")

    # =============================================================================
    #                        EXECUÇÃO DAS ATIVIDADES - CORRIGIDA
    # =============================================================================

    def executar_atividades_em_ordem(self):
        """
        VERSÃO CORRIGIDA: Executa atividades com agendamento temporal em cascata.

        NOVA FUNCIONALIDADE: Executa SUBPRODUTOS diretamente quando solicitados pelo usuário,
        mesmo sem PRODUTO principal.

        ESTRATÉGIA:
        1. Se há PRODUTO: Executa produto primeiro, depois subprodutos sincronizados
        2. Se há apenas SUBPRODUTOS: Executa subprodutos diretamente
        3. Garante que qualquer tipo de pedido seja executado
        """

        # Limpar registro de falhas para este pedido
        _registro_falhas_atual.limpar()


        total_atividades = len(self.atividades_modulares)
        logger.info(
            f"Iniciando execução em CASCATA CORRIGIDA do pedido {self.id_pedido} com {total_atividades} atividades"
        )
        
        if total_atividades == 0:
            logger.warning(f"Nenhuma atividade para executar no pedido {self.id_pedido}")
            return
        
        try:
            # NOVA ESTRATÉGIA: Verificar que tipos de atividades temos
            atividades_produto = [
                a for a in self.atividades_modulares 
                if a.tipo_item == TipoItem.PRODUTO
            ]
            atividades_subproduto = [
                a for a in self.atividades_modulares 
                if a.tipo_item == TipoItem.SUBPRODUTO
            ]
            
            logger.info(
                f"Composição do pedido: {len(atividades_produto)} PRODUTO(s), "
                f"{len(atividades_subproduto)} SUBPRODUTO(s)"
            )
            
            # CENÁRIO 1: Há atividades de PRODUTO - Execução em cascata tradicional
            if atividades_produto:
                logger.info("CENÁRIO: Execução em cascata (PRODUTO + SUBPRODUTOS)")
                inicio_real_produto = self._executar_produto_e_capturar_inicio()
                
                # Executar SUBPRODUTOS com timing perfeito
                if inicio_real_produto and atividades_subproduto:
                    self._executar_subprodutos_com_timing_perfeito(inicio_real_produto)
                elif not inicio_real_produto:
                    logger.warning("Produto não foi executado, não é possível sincronizar subprodutos")
            
            # CENÁRIO 2: Apenas SUBPRODUTOS - Execução direta
            elif atividades_subproduto:
                logger.info("CENÁRIO: Execução direta de SUBPRODUTOS (sem PRODUTO principal)")
                logger.info(
                    f"Executando {len(atividades_subproduto)} atividades de SUBPRODUTO "
                    f"diretamente até {self.fim_jornada.strftime('%H:%M')}"
                )
                
                # Agrupar subprodutos por dependência
                grupos_subprodutos = self._agrupar_subprodutos_por_dependencia(atividades_subproduto)
                
                # Executar cada grupo para terminar no fim da jornada
                for grupo_nome, atividades_grupo in grupos_subprodutos.items():
                    logger.info(
                        f"Executando grupo SUBPRODUTO '{grupo_nome}': {len(atividades_grupo)} atividades "
                        f"→ terminando às {self.fim_jornada.strftime('%H:%M')}"
                    )
                    
                    try:
                        self._executar_grupo_backward_scheduling(
                            atividades_grupo, 
                            self.fim_jornada,  # Usar fim da jornada como deadline
                            f'SUBPRODUTO_DIRETO_{grupo_nome}'
                        )
                        
                        logger.info(f"Grupo SUBPRODUTO '{grupo_nome}' executado com sucesso!")
                        
                    except Exception as e:
                        logger.error(f"Falha no grupo SUBPRODUTO '{grupo_nome}': {e}")
                        raise RuntimeError(
                            f"FALHA NA EXECUÇÃO DIRETA: Subproduto '{grupo_nome}' falhou: {e}"
                        )
            
            # CENÁRIO 3: Nenhuma atividade reconhecida
            else:
                logger.warning(
                    f"Nenhuma atividade de PRODUTO ou SUBPRODUTO encontrada no pedido {self.id_pedido}"
                )
                return
            
            logger.info(
                f"Pedido {self.id_pedido} executado com sucesso! "
                f"Total de atividades executadas: {len(self.atividades_executadas)}"
            )
            
        except Exception as e:
            logger.error(f"Falha na execução do pedido {self.id_pedido}: {e}")
            
            # CANCELAMENTO EM CASCATA
            self._cancelar_pedido_completo(str(e))
            raise

    def _executar_produto_e_capturar_inicio(self) -> Optional[datetime]:
        """
        NOVO MÉTODO: Executa atividades do produto e captura o horário real de início.
        Retorna o horário de início da primeira atividade do produto.
        """
        atividades_produto = [
            a for a in self.atividades_modulares 
            if a.tipo_item == TipoItem.PRODUTO
        ]
        
        if not atividades_produto:
            logger.info("Nenhuma atividade de PRODUTO para executar")
            return None
        
        logger.info(f"Executando {len(atividades_produto)} atividades de PRODUTO primeiro")
        
        # Executar em backward scheduling normal
        self._executar_grupo_backward_scheduling(
            atividades_produto, 
            self.fim_jornada, 
            'PRODUTO'
        )
        
        # CAPTURAR HORÁRIO REAL DE INÍCIO da primeira atividade executada
        atividades_produto_executadas = [
            a for a in self.atividades_executadas 
            if a.tipo_item == TipoItem.PRODUTO and hasattr(a, 'inicio_real')
        ]
        
        if atividades_produto_executadas:
            inicio_real = min([a.inicio_real for a in atividades_produto_executadas])
            logger.info(
                f"PRODUTO executado! Início real capturado: {inicio_real.strftime('%H:%M')} "
                f"(primeira atividade de {len(atividades_produto_executadas)} executadas)"
            )
            return inicio_real
        else:
            logger.warning("Nenhuma atividade de produto foi executada com sucesso")
            return None

    def _executar_subprodutos_com_timing_perfeito(self, inicio_produto: datetime):
        """
        NOVO MÉTODO: Executa subprodutos com timing perfeito.
        Todos os subprodutos terminam exatamente quando o produto começa.
        """
        atividades_subproduto = [
            a for a in self.atividades_modulares 
            if a.tipo_item == TipoItem.SUBPRODUTO
        ]
        
        if not atividades_subproduto:
            logger.info("Nenhuma atividade de SUBPRODUTO para executar")
            return
        
        logger.info(
            f"Executando {len(atividades_subproduto)} atividades de SUBPRODUTO "
            f"para terminar EXATAMENTE às {inicio_produto.strftime('%H:%M')} (timing perfeito)"
        )
        
        # Agrupar subprodutos
        grupos_subprodutos = self._agrupar_subprodutos_por_dependencia(atividades_subproduto)
        
        # Executar cada grupo para terminar no horário exato
        for grupo_nome, atividades_grupo in grupos_subprodutos.items():
            logger.info(
                f"Executando grupo SUBPRODUTO '{grupo_nome}': {len(atividades_grupo)} atividades "
                f"→ terminando às {inicio_produto.strftime('%H:%M')}"
            )
            
            try:
                self._executar_grupo_backward_scheduling(
                    atividades_grupo, 
                    inicio_produto,  # TIMING PERFEITO
                    f'SUBPRODUTO_{grupo_nome}'
                )
                
                logger.info(f"Grupo SUBPRODUTO '{grupo_nome}' executado com timing perfeito!")
                
            except Exception as e:
                logger.error(f"Falha no grupo SUBPRODUTO '{grupo_nome}': {e}")
                
                # Se produto já foi executado, falha em subproduto é crítica
                raise RuntimeError(
                    f"FALHA CRÍTICA: Subproduto '{grupo_nome}' falhou após produto ser executado: {e}"
                )

    def _executar_grupo_backward_scheduling(
        self, 
        atividades_grupo: list, 
        fim_jornada_grupo: datetime, 
        nome_grupo: str
    ):
        """
        MÉTODO REFATORADO: Executa um grupo de atividades em backward scheduling.
        """
        # Ordenar atividades em ordem reversa para backward scheduling
        atividades_ordenadas = sorted(
            atividades_grupo,
            key=lambda a: a.id_atividade,
            reverse=True
        )
        
        logger.info(
            f"Executando {len(atividades_ordenadas)} atividades do grupo '{nome_grupo}' "
            f"em backward scheduling até {fim_jornada_grupo.strftime('%H:%M')}"
        )
        
        # MARCAR A ÚLTIMA ATIVIDADE DO GRUPO (primeira na ordem reversa)
        if atividades_ordenadas:
            primeira_atividade = atividades_ordenadas[0]
            primeira_atividade.eh_ultima_atividade_grupo = True
            
            # Se for grupo PRODUTO e tem tempo_maximo_de_espera = 0, é fim obrigatório
            if (nome_grupo == 'PRODUTO' and 
                hasattr(primeira_atividade, 'tempo_maximo_de_espera') and 
                primeira_atividade.tempo_maximo_de_espera == timedelta(0)):
                primeira_atividade.fim_obrigatorio = fim_jornada_grupo
                logger.info(
                    f"Atividade {primeira_atividade.id_atividade} deve terminar "
                    f"EXATAMENTE às {fim_jornada_grupo.strftime('%H:%M')}"
                )
        
        # Executar atividades em sequência (backward scheduling)
        current_fim = fim_jornada_grupo
        inicio_prox_atividade = fim_jornada_grupo
        atividade_sucessora = None

        for i, atividade in enumerate(atividades_ordenadas):
            logger.info(
                f"Executando atividade {i+1}/{len(atividades_ordenadas)} do grupo '{nome_grupo}': "
                f"{atividade.nome_atividade} (ID {atividade.id_atividade})"
            )
            
            try:
                sucesso, inicio_atual, fim_atual = self._executar_atividade_individual(
                    atividade, current_fim, atividade_sucessora, inicio_prox_atividade
                )
                
                # VALIDAÇÃO CRÍTICA: Se falhou, cancela GRUPO
                if not sucesso:
                    # Registrar erro de alocação por prazo usando o logger unificado
                    try:
                        from utils.logs.temporal_allocation_logger import log_deadline_allocation_error
                        
                        # Coletar informações para o log
                        tipo_equipamento = "DESCONHECIDO"
                        if hasattr(atividade, 'tipo_equipamento') and atividade.tipo_equipamento:
                            # Obter o tipo de equipamento correto (ex: "BANCADAS", "FORNOS")
                            tipos_equip = list(atividade.tipo_equipamento.keys())
                            if tipos_equip:
                                tipo_equipamento = tipos_equip[0]
                        elif hasattr(atividade, 'configuracoes_equipamentos'):
                            # Fallback: usar configurações, mas buscar o tipo real
                            equipamentos_config = list(atividade.configuracoes_equipamentos.keys())
                            if equipamentos_config:
                                # Mapear equipamento específico para tipo
                                primeiro_equip = equipamentos_config[0]
                                if 'bancada' in primeiro_equip.lower():
                                    tipo_equipamento = "BANCADAS"
                                elif 'forno' in primeiro_equip.lower():
                                    tipo_equipamento = "FORNOS"
                                elif 'fritadeira' in primeiro_equip.lower():
                                    tipo_equipamento = "FRITADEIRAS"
                                elif 'fogao' in primeiro_equip.lower():
                                    tipo_equipamento = "FOGOES"
                                elif 'camara' in primeiro_equip.lower() or 'freezer' in primeiro_equip.lower():
                                    tipo_equipamento = "REFRIGERACAO_CONGELAMENTO"
                                elif 'misturadoras' in primeiro_equip.lower() or 'masseira' in primeiro_equip.lower():
                                    tipo_equipamento = "MISTURADORAS"
                                else:
                                    tipo_equipamento = primeiro_equip  # Manter original se não mapear
                        
                        # Determinar equipamentos tentados
                        equipamentos_tentados = []
                        if hasattr(atividade, 'equipamentos_elegiveis') and atividade.equipamentos_elegiveis:
                            # Verificar se são objetos ou strings
                            if hasattr(atividade.equipamentos_elegiveis[0], 'nome'):
                                equipamentos_tentados = [eq.nome for eq in atividade.equipamentos_elegiveis[:3]]
                            else:
                                # São strings diretas
                                equipamentos_tentados = atividade.equipamentos_elegiveis[:3]
                        
                        # Contexto adicional com análise de disponibilidade
                        contexto = {}
                        if hasattr(atividade, 'quantidade'):
                            contexto['quantidade_necessaria'] = atividade.quantidade

                        # 🔍 NOVA FUNCIONALIDADE: Análise detalhada de conflitos de equipamentos
                        try:
                            from utils.logs.equipment_conflict_analyzer import analisar_conflito_equipamentos

                            if equipamentos_tentados and self.inicio_jornada:
                                logger.info(f"🔍 Analisando conflitos de equipamentos para atividade {atividade.id_atividade}...")

                                # Calcular período necessário baseado no backward scheduling
                                inicio_necessario = fim_jornada_grupo - atividade.duracao
                                fim_necessario = fim_jornada_grupo

                                # Analisar conflitos específicos
                                analise_conflito, relatorio_conflito = analisar_conflito_equipamentos(
                                    equipamentos_tentados=equipamentos_tentados,
                                    periodo_inicio=inicio_necessario,
                                    periodo_fim=fim_necessario,
                                    id_atividade=atividade.id_atividade,
                                    nome_atividade=atividade.nome_atividade,
                                    quantidade_necessaria=getattr(atividade, 'quantidade', None)
                                )

                                # Adicionar análise ao contexto
                                contexto['analise_conflito_equipamentos'] = analise_conflito
                                contexto['relatorio_conflito_detalhado'] = relatorio_conflito

                                # Log resumido para debug
                                resumo = analise_conflito.get("resumo", {})
                                logger.info(
                                    f"📊 Conflito analisado: {resumo.get('equipamentos_ocupados', 0)}/"
                                    f"{resumo.get('equipamentos_tentados', 0)} equipamentos ocupados"
                                )

                        except Exception as e:
                            logger.warning(f"⚠️ Erro na análise de conflitos: {e}")
                            contexto['erro_analise_conflito'] = str(e)
                        
                        # Obter tempo máximo de espera da atividade
                        tempo_max_espera = None
                        if hasattr(atividade, 'tempo_maximo_de_espera') and atividade.tempo_maximo_de_espera:
                            tempo_max_espera = atividade.tempo_maximo_de_espera
                        
                        # Tentar obter próximo horário livre do equipamento (se possível)
                        proximo_horario_livre = None
                        try:
                            if hasattr(atividade, 'equipamentos_elegiveis') and atividade.equipamentos_elegiveis:
                                # Pegar o primeiro equipamento disponível como exemplo
                                equipamento = atividade.equipamentos_elegiveis[0]
                                if hasattr(equipamento, 'proximo_horario_disponivel'):
                                    proximo_horario_livre = equipamento.proximo_horario_disponivel(self.inicio_jornada, fim_jornada_grupo)
                                elif hasattr(equipamento, 'agenda') and equipamento.agenda:
                                    # Tentar calcular baseado na agenda
                                    # Aqui seria onde implementaríamos a lógica para encontrar o próximo slot livre
                                    # Por enquanto, usar um horário fictício baseado no fim da jornada
                                    proximo_horario_livre = fim_jornada_grupo + timedelta(hours=1)
                        except Exception:
                            # Se não conseguir obter, continuar sem essa informação
                            pass
                        
                        # Registrar o erro com análise completa
                        log_deadline_allocation_error(
                            id_ordem=atividade.id_ordem,
                            id_pedido=atividade.id_pedido,
                            id_atividade=atividade.id_atividade,
                            nome_atividade=atividade.nome_atividade,
                            tipo_equipamento=tipo_equipamento,
                            quantidade_necessaria=getattr(atividade, 'quantidade', 0),
                            prazo_final=fim_jornada_grupo,
                            duracao_atividade=atividade.duracao,
                            janela_disponivel=(self.inicio_jornada, fim_jornada_grupo),
                            motivo_falha="Não foi possível alocar a atividade dentro da janela temporal disponível",
                            tempo_maximo_espera=tempo_max_espera,
                            proximo_horario_livre=proximo_horario_livre,
                            equipamentos_tentados=equipamentos_tentados,
                            contexto_adicional=contexto
                        )
                        logger.info(f"📝 Log de erro temporal (deadline) registrado para atividade {atividade.id_atividade}")
                        
                    except Exception as log_err:
                        logger.warning(f"⚠️ Falha ao registrar log de erro temporal: {log_err}")
                    
                    erro_msg = (
                        f"FALHA NO GRUPO '{nome_grupo}': Atividade {atividade.id_atividade} "
                        f"({atividade.nome_atividade}) não pôde ser alocada."
                    )
                    logger.error(erro_msg)
                    raise RuntimeError(erro_msg)
                
                # VALIDAÇÃO DE PONTUALIDADE para última atividade de PRODUTO
                if (i == 0 and nome_grupo == 'PRODUTO' and 
                    hasattr(atividade, 'tempo_maximo_de_espera') and 
                    atividade.tempo_maximo_de_espera == timedelta(0)):
                    if fim_atual != fim_jornada_grupo:
                        diferenca = fim_jornada_grupo - fim_atual
                        erro_msg = (
                            f"FALHA DE PONTUALIDADE NO PRODUTO: Atividade {atividade.id_atividade} "
                            f"deveria terminar exatamente às {fim_jornada_grupo.strftime('%H:%M')}, "
                            f"mas terminou às {fim_atual.strftime('%H:%M')}. Diferença: {diferenca}."
                        )
                        logger.error(erro_msg)
                        raise RuntimeError(erro_msg)
                
                # REGISTRO DE SUCESSO
                self.atividades_executadas.append(atividade)
                
                # Atualizar para próxima iteração
                inicio_prox_atividade = inicio_atual
                atividade_sucessora = atividade
                current_fim = atividade.inicio_real
                
                logger.info(
                    f"Atividade do grupo '{nome_grupo}' executada: "
                    f"{atividade.id_atividade} ({inicio_atual.strftime('%H:%M')} - {fim_atual.strftime('%H:%M')})"
                )
                
            except RuntimeError as e:
                # Log do tipo de erro para estatísticas
                erro_msg_str = str(e)
                
                if any(keyword in erro_msg_str for keyword in [
                    "QUANTIDADE_ABAIXO_MINIMO", 
                    "QUANTIDADE_EXCEDE_MAXIMO",
                    "Erro de quantidade"
                ]):
                    logger.error(f"ERRO DE QUANTIDADE no grupo '{nome_grupo}' - atividade {atividade.id_atividade}")
                elif "Erro de tempo entre equipamentos" in erro_msg_str:
                    logger.error(f"ERRO DE TEMPO INTRA-ATIVIDADE no grupo '{nome_grupo}' - atividade {atividade.id_atividade}")
                elif "Tempo máximo de espera excedido" in erro_msg_str:
                    logger.error(f"ERRO DE TEMPO INTER-ATIVIDADE no grupo '{nome_grupo}' - atividade {atividade.id_atividade}")
                
                # Re-lançar para tratamento no nível superior
                raise e
        
        logger.info(
            f"Grupo '{nome_grupo}' concluído com sucesso: "
            f"{len(atividades_ordenadas)} atividades executadas"
        )

    def _agrupar_subprodutos_por_dependencia(self, atividades_subproduto: list) -> dict:
        """
        MÉTODO MANTIDO: Agrupa subprodutos por nível de dependência.
        """
        # Implementação inicial: agrupar por ID do item (diferentes subprodutos)
        grupos = {}
        
        for atividade in atividades_subproduto:
            # Identificar o subproduto pelo nome do item
            nome_subproduto = atividade.nome_item
            
            if nome_subproduto not in grupos:
                grupos[nome_subproduto] = []
            grupos[nome_subproduto].append(atividade)
        
        logger.info(f"Identificados {len(grupos)} grupos de subprodutos: {list(grupos.keys())}")
        
        return grupos

    def _executar_atividade_individual(
        self, 
        atividade: AtividadeModular, 
        current_fim: datetime, 
        atividade_sucessora: AtividadeModular, 
        inicio_prox_atividade: datetime
    ):
        """
        VERSÃO CORRIGIDA: Intercepta erros de timing e gera log limpo.
        """
        logger.debug(
            f"Tentando alocar atividade {atividade.id_atividade} "
            f"com fim em {current_fim.strftime('%H:%M')}"
        )
        
        try:
            # Tentar alocar equipamentos e funcionários
            sucesso, inicio_atual, fim_atual, _, equipamentos_alocados = atividade.tentar_alocar_e_iniciar_equipamentos(
                self.inicio_jornada, current_fim
            )

            if not sucesso:
                logger.warning(f"Falha na alocação da atividade {atividade.id_atividade}")
                return False, None, None

        except IntraActivityTimingError as intra_timing_err:
            # ERRO DE TIMING DENTRO DA ATIVIDADE - GERAR LOG E JSON
            logger.error(
                f"ERRO DE TEMPO INTRA-ATIVIDADE na atividade {atividade.id_atividade}: "
                f"{intra_timing_err.current_equipment} → {intra_timing_err.successor_equipment}"
            )

            # GERAR LOG NO FORMATO LIMPO PARA INTRA-ACTIVITY
            try:
                from utils.logs.formatador_timing_limpo import FormatadorTimingLimpo

                # Preparar dados para o formatador (adaptando para formato inter-atividade)
                atividade_atual_dados = {
                    'nome': f"{atividade.nome_atividade} - {intra_timing_err.current_equipment}",
                    'fim': intra_timing_err.current_end_time.strftime('%d/%m %H:%M:%S'),
                    'duracao_estimada': '0:12:00'
                }

                atividade_sucessora_dados = {
                    'nome': f"{atividade.nome_atividade} - {intra_timing_err.successor_equipment}",
                    'inicio': intra_timing_err.successor_start_time.strftime('%d/%m %H:%M:%S')
                }

                timing_violation_dados = {
                    'tempo_maximo': str(intra_timing_err.maximum_wait_time),
                    'excesso': str(intra_timing_err.actual_delay - intra_timing_err.maximum_wait_time)
                }

                # Obter equipamentos envolvidos
                equipamentos = [
                    {'nome': intra_timing_err.current_equipment, 'tipo': 'EQUIPAMENTO_ATUAL'},
                    {'nome': intra_timing_err.successor_equipment, 'tipo': 'EQUIPAMENTO_SUCESSOR'}
                ]

                # Gerar log limpo (equipamento conflitante é o sucessor)
                log_formatado = FormatadorTimingLimpo.formatar_erro_timing_inter_atividade(
                    id_ordem=atividade.id_ordem,
                    id_pedido=atividade.id_pedido,
                    atividade_atual=atividade_atual_dados,
                    atividade_sucessora=atividade_sucessora_dados,
                    timing_violation=timing_violation_dados,
                    equipamentos_envolvidos=equipamentos,
                    equipamento_conflitante=intra_timing_err.successor_equipment
                )

                # Salvar arquivo
                import os
                os.makedirs("logs/erros", exist_ok=True)
                nome_arquivo = f"logs/erros/ordem: {atividade.id_ordem} | pedido: {atividade.id_pedido}.log"

                with open(nome_arquivo, "w", encoding="utf-8") as f:
                    f.write(log_formatado)

                logger.info(f"Log de timing limpo (INTRA-ACTIVITY) salvo: {nome_arquivo}")

            except Exception as format_err:
                logger.warning(f"Falha ao gerar log limpo para INTRA-ACTIVITY: {format_err}")

            # GERAR JSON PARA INTRA-ACTIVITY
            try:
                import json
                import os

                # Preparar dados para JSON
                erro_data = {
                    "tipo_erro": "INTRA_ACTIVITY_TIMING",
                    "timestamp": datetime.now().isoformat(),
                    "activity": {
                        "id": intra_timing_err.activity_id,
                        "name": intra_timing_err.activity_name
                    },
                    "equipment_transition": {
                        "current": {
                            "name": intra_timing_err.current_equipment,
                            "end_time": intra_timing_err.current_end_time.isoformat()
                        },
                        "successor": {
                            "name": intra_timing_err.successor_equipment,
                            "start_time": intra_timing_err.successor_start_time.isoformat()
                        }
                    },
                    "timing_violation": {
                        "maximum_wait_time": str(intra_timing_err.maximum_wait_time),
                        "actual_delay": str(intra_timing_err.actual_delay),
                        "excess": str(intra_timing_err.actual_delay - intra_timing_err.maximum_wait_time)
                    }
                }

                # Salvar JSON
                json_filename = f"ordem_{atividade.id_ordem}_pedido_{atividade.id_pedido}_temporal_errors.json"
                json_path = os.path.join("logs/erros", json_filename)

                # Se já existe, adicionar ao array existente
                if os.path.exists(json_path):
                    with open(json_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        if not isinstance(existing_data, list):
                            existing_data = [existing_data]
                else:
                    existing_data = []

                existing_data.append(erro_data)

                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, indent=2, ensure_ascii=False)

                logger.info(f"📄 JSON de erro temporal (INTRA-ACTIVITY) salvo: {json_path}")

            except Exception as json_err:
                logger.warning(f"Falha ao salvar JSON de erro temporal (INTRA-ACTIVITY): {json_err}")

            # Retornar falha para que o pedido seja cancelado
            return False, None, None

        try:

            logger.debug(f"Equipamentos alocados: {len(equipamentos_alocados) if equipamentos_alocados else 0}")

            # Verificar tempo máximo de espera INTER-ATIVIDADE se houver atividade sucessora
            if atividade_sucessora and fim_atual and inicio_prox_atividade:
                try:
                    self._verificar_tempo_maximo_espera(
                        atividade, atividade_sucessora, fim_atual, inicio_prox_atividade
                    )
                    logger.debug("Verificação de tempo máximo de espera INTER-ATIVIDADE passou")
                    
                except (RuntimeError, IntraActivityTimingError) as timing_err:
                    # INTERCEPTAR ERRO DE TIMING E GERAR LOG LIMPO
                    erro_msg_str = str(timing_err)
                    
                    if "Tempo máximo de espera excedido entre atividades" in erro_msg_str:
                        logger.error(
                            f"ERRO DE TEMPO INTER-ATIVIDADE detectado entre atividades "
                            f"{atividade.id_atividade} → {atividade_sucessora.id_atividade}"
                        )

                        # GERAR APENAS O JSON (sem log duplicado)
                        try:
                            from utils.logs.temporal_allocation_logger import get_temporal_logger
                            import json
                            import os
                            from datetime import datetime

                            # Calcular atraso para uso no JSON
                            atraso = inicio_prox_atividade - fim_atual

                            # Preparar dados para JSON
                            erro_data = {
                                "tipo_erro": "INTER_ACTIVITY_TIMING",
                                "timestamp": datetime.now().isoformat(),
                                "current_activity": {
                                    "id": atividade.id_atividade,
                                    "name": atividade.nome_atividade,
                                    "end_time": fim_atual.isoformat()
                                },
                                "successor_activity": {
                                    "id": atividade_sucessora.id_atividade,
                                    "name": atividade_sucessora.nome_atividade,
                                    "start_time": inicio_prox_atividade.isoformat()
                                },
                                "timing_violation": {
                                    "maximum_wait_time": str(atividade_sucessora.tempo_maximo_de_espera),
                                    "actual_delay": str(atraso),
                                    "excess": str(atraso - atividade_sucessora.tempo_maximo_de_espera)
                                }
                            }

                            # Salvar JSON
                            json_filename = f"ordem_{atividade.id_ordem}_pedido_{atividade.id_pedido}_temporal_errors.json"
                            json_path = os.path.join("logs/erros", json_filename)

                            # Se já existe, adicionar ao array existente
                            if os.path.exists(json_path):
                                with open(json_path, 'r', encoding='utf-8') as f:
                                    existing_data = json.load(f)
                                    if not isinstance(existing_data, list):
                                        existing_data = [existing_data]
                            else:
                                existing_data = []

                            existing_data.append(erro_data)

                            with open(json_path, 'w', encoding='utf-8') as f:
                                json.dump(existing_data, f, indent=2, ensure_ascii=False)

                            logger.info(f"📄 JSON de erro temporal salvo: {json_path}")

                        except Exception as json_err:
                            logger.warning(f"Falha ao salvar JSON de erro temporal: {json_err}")

                    # Tratar erro de timing DENTRO DA ATIVIDADE (INTRA-ACTIVITY)
                    elif isinstance(timing_err, IntraActivityTimingError) or "Erro de tempo entre equipamentos" in erro_msg_str:
                        logger.error(
                            f"ERRO DE TEMPO INTRA-ATIVIDADE detectado na atividade {atividade.id_atividade}"
                        )

                        # GERAR LOG NO FORMATO LIMPO PARA INTRA-ACTIVITY
                        try:
                            from utils.logs.formatador_timing_limpo import FormatadorTimingLimpo

                            # Extrair informações do erro IntraActivityTimingError
                            if isinstance(timing_err, IntraActivityTimingError):
                                current_equipment = timing_err.current_equipment
                                successor_equipment = timing_err.successor_equipment
                                current_end_time = timing_err.current_end_time
                                successor_start_time = timing_err.successor_start_time
                                maximum_wait_time = timing_err.maximum_wait_time
                                actual_delay = timing_err.actual_delay
                            else:
                                # Fallback se for RuntimeError
                                current_equipment = "Equipamento_Atual_Desconhecido"
                                successor_equipment = "Equipamento_Sucessor_Desconhecido"
                                current_end_time = datetime.now()
                                successor_start_time = datetime.now()
                                maximum_wait_time = timedelta(0)
                                actual_delay = timedelta(minutes=12)

                            # Preparar dados para o formatador (adaptando para formato inter-atividade)
                            atividade_atual_dados = {
                                'nome': f"{atividade.nome_atividade} - {current_equipment}",
                                'fim': current_end_time.strftime('%d/%m %H:%M:%S'),
                                'duracao_estimada': '0:12:00'
                            }

                            atividade_sucessora_dados = {
                                'nome': f"{atividade.nome_atividade} - {successor_equipment}",
                                'inicio': successor_start_time.strftime('%d/%m %H:%M:%S')
                            }

                            timing_violation_dados = {
                                'tempo_maximo': str(maximum_wait_time),
                                'excesso': str(actual_delay - maximum_wait_time)
                            }

                            # Obter equipamentos envolvidos
                            equipamentos = [
                                {'nome': current_equipment, 'tipo': 'EQUIPAMENTO_ATUAL'},
                                {'nome': successor_equipment, 'tipo': 'EQUIPAMENTO_SUCESSOR'}
                            ]

                            # Gerar log limpo (equipamento conflitante é o sucessor)
                            log_formatado = FormatadorTimingLimpo.formatar_erro_timing_inter_atividade(
                                id_ordem=atividade.id_ordem,
                                id_pedido=atividade.id_pedido,
                                atividade_atual=atividade_atual_dados,
                                atividade_sucessora=atividade_sucessora_dados,
                                timing_violation=timing_violation_dados,
                                equipamentos_envolvidos=equipamentos,
                                equipamento_conflitante=successor_equipment
                            )

                            # Salvar arquivo
                            import os
                            os.makedirs("logs/erros", exist_ok=True)
                            nome_arquivo = f"logs/erros/ordem: {atividade.id_ordem} | pedido: {atividade.id_pedido}.log"

                            with open(nome_arquivo, "w", encoding="utf-8") as f:
                                f.write(log_formatado)

                            logger.info(f"Log de timing limpo (INTRA-ACTIVITY) salvo: {nome_arquivo}")

                        except Exception as format_err:
                            logger.warning(f"Falha ao gerar log limpo para INTRA-ACTIVITY: {format_err}")

                        # GERAR JSON PARA INTRA-ACTIVITY
                        try:
                            import json
                            import os

                            # Preparar dados para JSON
                            if isinstance(timing_err, IntraActivityTimingError):
                                erro_data = {
                                    "tipo_erro": "INTRA_ACTIVITY_TIMING",
                                    "timestamp": datetime.now().isoformat(),
                                    "activity": {
                                        "id": timing_err.activity_id,
                                        "name": timing_err.activity_name
                                    },
                                    "equipment_transition": {
                                        "current": {
                                            "name": timing_err.current_equipment,
                                            "end_time": timing_err.current_end_time.isoformat()
                                        },
                                        "successor": {
                                            "name": timing_err.successor_equipment,
                                            "start_time": timing_err.successor_start_time.isoformat()
                                        }
                                    },
                                    "timing_violation": {
                                        "maximum_wait_time": str(timing_err.maximum_wait_time),
                                        "actual_delay": str(timing_err.actual_delay),
                                        "excess": str(timing_err.actual_delay - timing_err.maximum_wait_time)
                                    }
                                }
                            else:
                                # Fallback para RuntimeError
                                erro_data = {
                                    "tipo_erro": "INTRA_ACTIVITY_TIMING",
                                    "timestamp": datetime.now().isoformat(),
                                    "activity": {
                                        "id": atividade.id_atividade,
                                        "name": atividade.nome_atividade
                                    },
                                    "error_message": erro_msg_str
                                }

                            # Salvar JSON
                            json_filename = f"ordem_{atividade.id_ordem}_pedido_{atividade.id_pedido}_temporal_errors.json"
                            json_path = os.path.join("logs/erros", json_filename)

                            # Se já existe, adicionar ao array existente
                            if os.path.exists(json_path):
                                with open(json_path, 'r', encoding='utf-8') as f:
                                    existing_data = json.load(f)
                                    if not isinstance(existing_data, list):
                                        existing_data = [existing_data]
                            else:
                                existing_data = []

                            existing_data.append(erro_data)

                            with open(json_path, 'w', encoding='utf-8') as f:
                                json.dump(existing_data, f, indent=2, ensure_ascii=False)

                            logger.info(f"📄 JSON de erro temporal (INTRA-ACTIVITY) salvo: {json_path}")

                        except Exception as json_err:
                            logger.warning(f"Falha ao salvar JSON de erro temporal (INTRA-ACTIVITY): {json_err}")

                    # Re-lançar exceção para tratamento no nível superior
                    raise timing_err

            # Registrar equipamentos alocados no pedido
            if sucesso and equipamentos_alocados:
                self.equipamentos_alocados_no_pedido.extend(equipamentos_alocados)
                logger.debug(f"Total de equipamentos no pedido: {len(self.equipamentos_alocados_no_pedido)}")
            
            return sucesso, inicio_atual, fim_atual
            
        except RuntimeError as e:
            # Detectar automaticamente diferentes tipos de erro baseado na mensagem
            erro_msg = str(e)
            
            # Outros tipos de erro...
            logger.error(f"Erro na atividade {atividade.id_atividade}: {e}")
            
            # Re-lançar exceção para tratamento no nível superior
            raise e

    def _verificar_tempo_maximo_espera(
        self,
        atividade_atual: AtividadeModular,
        atividade_sucessora: AtividadeModular,
        fim_atual: datetime,
        inicio_prox_atividade: datetime
    ):
        """
        VERSÃO CORRIGIDA: Gera log no formato limpo ANTES de lançar exceção.
        """
        logger.info(f"🔍 DEBUG: Verificando tempo máximo entre atividades {atividade_atual.id_atividade} → {atividade_sucessora.id_atividade}")
        logger.info(f"🔍 DEBUG: Fim atual: {fim_atual.strftime('%H:%M:%S')}, Início sucessora: {inicio_prox_atividade.strftime('%H:%M:%S')}")

        if not hasattr(atividade_sucessora, 'tempo_maximo_de_espera') or atividade_sucessora.tempo_maximo_de_espera is None:
            logger.debug("Atividade sucessora não possui tempo máximo de espera definido")
            return
        
        tempo_max_espera = atividade_sucessora.tempo_maximo_de_espera
        atraso = inicio_prox_atividade - fim_atual

        logger.debug(
            f"Verificação de tempo ENTRE atividades:\n"
            f"   Atual: {atividade_atual.id_atividade} (fim: {fim_atual.strftime('%H:%M:%S')})\n"
            f"   Sucessora: {atividade_sucessora.id_atividade} (início: {inicio_prox_atividade.strftime('%H:%M:%S')})\n"
            f"   Atraso: {atraso} | Máximo permitido: {tempo_max_espera}"
        )

        if atraso > tempo_max_espera:
            # PRIMEIRO: Gerar log no formato limpo ANTES de qualquer exceção
            try:
                from utils.logs.formatador_timing_limpo import FormatadorTimingLimpo
                
                # Preparar dados para o formatador
                atividade_atual_dados = {
                    'nome': atividade_atual.nome_atividade,
                    'fim': fim_atual.strftime('%d/%m %H:%M:%S'),
                    'duracao_estimada': str(getattr(atividade_atual, 'duracao', timedelta(minutes=30)))
                }
                
                atividade_sucessora_dados = {
                    'nome': atividade_sucessora.nome_atividade,
                    'inicio': inicio_prox_atividade.strftime('%d/%m %H:%M:%S')
                }
                
                timing_violation_dados = {
                    'tempo_maximo': str(tempo_max_espera),
                    'excesso': str(atraso - tempo_max_espera)
                }
                
                # Obter equipamentos
                equipamentos = FormatadorTimingLimpo.obter_equipamentos_atividade(atividade_atual)
                if len(equipamentos) < 3:
                    equipamentos.extend(FormatadorTimingLimpo.obter_equipamentos_atividade(atividade_sucessora))

                # Equipamentos apenas da atividade atual para o log (não misturar com sucessora)
                equipamentos_para_log = FormatadorTimingLimpo.obter_equipamentos_atividade(atividade_atual)

                # Identificar equipamento conflitante (geralmente o da atividade sucessora que não pôde ser alocado)
                equipamento_conflitante = None
                try:
                    if hasattr(atividade_sucessora, 'equipamentos_elegiveis') and atividade_sucessora.equipamentos_elegiveis:
                        # Primeiro equipamento elegível da sucessora é o mais provável conflitante
                        equipamento_conflitante = atividade_sucessora.equipamentos_elegiveis[0].nome
                    elif hasattr(atividade_sucessora, 'equipamento_alocado') and atividade_sucessora.equipamento_alocado:
                        if isinstance(atividade_sucessora.equipamento_alocado, list):
                            equipamento_conflitante = atividade_sucessora.equipamento_alocado[0].nome
                        else:
                            equipamento_conflitante = atividade_sucessora.equipamento_alocado.nome
                    elif equipamentos:
                        # Fallback: último equipamento da lista (mais provável ser da sucessora)
                        equipamento_conflitante = equipamentos[-1].get('nome', 'Equipamento_Desconhecido')
                except (AttributeError, IndexError):
                    equipamento_conflitante = "Equipamento_Desconhecido"

                # Obter resumo das tentativas falhadas
                resumo_falhas = _registro_falhas_atual.obter_resumo_falhas()

                # Gerar log limpo
                log_formatado = FormatadorTimingLimpo.formatar_erro_timing_inter_atividade(
                    id_ordem=atividade_atual.id_ordem,
                    id_pedido=atividade_atual.id_pedido,
                    atividade_atual=atividade_atual_dados,
                    atividade_sucessora=atividade_sucessora_dados,
                    timing_violation=timing_violation_dados,
                    equipamentos_envolvidos=equipamentos_para_log,
                    equipamento_conflitante=equipamento_conflitante,
                    tentativas_falhadas=resumo_falhas
                )
                
                # Salvar arquivo
                import os
                os.makedirs("logs/erros", exist_ok=True)
                nome_arquivo = f"logs/erros/ordem: {atividade_atual.id_ordem} | pedido: {atividade_atual.id_pedido}.log"
                
                with open(nome_arquivo, "w", encoding="utf-8") as f:
                    f.write(log_formatado)
                
                logger.info(f"Log de timing limpo salvo com sucesso: {nome_arquivo}")
                
            except Exception as format_err:
                logger.warning(f"Falha ao gerar log limpo: {format_err}")
            
            # SEGUNDO: Criar exceção estruturada para sistema JSON (opcional)
            timing_error = InterActivityTimingError(
                current_activity_id=atividade_atual.id_atividade,
                current_activity_name=atividade_atual.nome_atividade,
                successor_activity_id=atividade_sucessora.id_atividade,
                successor_activity_name=atividade_sucessora.nome_atividade,
                current_end_time=fim_atual,
                successor_start_time=inicio_prox_atividade,
                maximum_wait_time=tempo_max_espera,
                actual_delay=atraso
            )
            
            # TERCEIRO: Lançar exceção original (mantém compatibilidade)
            raise RuntimeError(
                f"Tempo máximo de espera excedido entre atividades:\n"
                f"   Atividade atual: {atividade_atual.id_atividade} ({atividade_atual.nome_atividade})\n"
                f"   Atividade sucessora: {atividade_sucessora.id_atividade} ({atividade_sucessora.nome_atividade})\n"
                f"   Fim da atual: {fim_atual.strftime('%d/%m %H:%M:%S')}\n"
                f"   Início da sucessora: {inicio_prox_atividade.strftime('%d/%m %H:%M:%S')}\n"
                f"   Atraso detectado: {atraso}\n"
                f"   Máximo permitido: {tempo_max_espera}\n"
                f"   Excesso: {atraso - tempo_max_espera}"
            ) from timing_error
        else:
            logger.debug(f"Tempo de espera ENTRE atividades dentro do limite permitido")

    def _cancelar_pedido_completo(self, motivo: str):
        """
        NOVO MÉTODO: Cancela o pedido completo fazendo rollback de todas as atividades.
        """
        logger.error(
            f"CANCELANDO PEDIDO COMPLETO {self.id_pedido} - Motivo: {motivo}"
        )
        
        self.pedido_cancelado = True
        
        # Fazer rollback de todas as atividades executadas com sucesso até agora
        if self.atividades_executadas:
            logger.info(
                f"Fazendo rollback de {len(self.atividades_executadas)} atividades já executadas"
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
                        logger.debug(f"Rollback equipamentos atividade {atividade.id_atividade}")
                    
                    # Marcar atividade como não alocada
                    atividade.alocada = False
                    
                except Exception as e:
                    logger.error(f"Erro no rollback da atividade {atividade.id_atividade}: {e}")
        
        # Rollback completo adicional
        self._executar_rollback_completo()
        
        logger.error(
            f"PEDIDO {self.id_pedido} CANCELADO COMPLETAMENTE. "
            f"Motivo: {motivo}"
        )

    # =============================================================================
    #                           ROLLBACK
    # =============================================================================

    def _executar_rollback_completo(self):
        """Executa rollback completo do pedido com logs detalhados"""
        logger.info(f"Executando rollback completo do pedido {self.id_pedido} da ordem {self.id_ordem}")

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
                f"Rollback concluído: "
                f"{equipamentos_liberados} equipamentos e {funcionarios_liberados} funcionários liberados"
            )
            
        except Exception as e:
            logger.error(f"Erro durante rollback: {e}")

    def rollback_pedido(self):
        """Método público para rollback manual"""
        logger.info(f"Rollback manual solicitado para pedido {self.id_pedido}")
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
            logger.warning("Gestor de almoxarifado não disponível - pulando verificação de estoque")
            return

        logger.info(f"Verificando disponibilidade de estoque para pedido {self.id_pedido}")

        itens_insuficientes = []
        estimativas = self.ficha_tecnica_modular.calcular_quantidade_itens()

        for item_dict, quantidade in estimativas:
            id_item = item_dict["id_item"]
            tipo_item = item_dict["tipo_item"]
            nome_item = item_dict["descricao"]
            politica = item_dict.get("politica_producao", "ESTOCADO")

            logger.debug(
                f"Verificando item '{nome_item}' (ID {id_item}) | "
                f"Tipo: {tipo_item} | Política: {politica} | Quantidade: {quantidade}"
            )

            # Itens SOB_DEMANDA não precisam verificação de estoque
            if tipo_item in {"SUBPRODUTO", "PRODUTO"} and politica == "SOB_DEMANDA":
                logger.debug(f"Item {id_item} é SOB_DEMANDA - pulando verificação")
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
                    logger.error(f"Erro ao verificar estoque do item {id_item}: {e}")
                    itens_insuficientes.append({
                        "id": id_item,
                        "descricao": nome_item,
                        "quantidade_necessaria": quantidade,
                        "disponivel": 0,
                        "erro": str(e)
                    })

        # Reportar itens insuficientes
        if itens_insuficientes:
            logger.error(f"Encontrados {len(itens_insuficientes)} itens com estoque insuficiente:")
            
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
            logger.info(f"Estoque suficiente para todos os itens do pedido {self.id_pedido}")

    def gerar_comanda_de_reserva(self, data_execucao: datetime):
        """
        Gera comanda de reserva para o pedido usando gestor otimizado.
        """
        if not self.ficha_tecnica_modular:
            raise ValueError("Ficha técnica ainda não foi montada")

        if not self.gestor_almoxarifado:
            logger.warning("Gestor de almoxarifado não disponível - pulando geração de comanda")
            return

        logger.info(f"Gerando comanda de reserva para pedido {self.id_pedido}")

        try:
            gerar_comanda_reserva_modulo(
                id_ordem=self.id_ordem,
                id_pedido=self.id_pedido,
                ficha=self.ficha_tecnica_modular,
                gestor=self.gestor_almoxarifado,
                data_execucao=data_execucao
            )
            
            logger.info(f"Comanda de reserva gerada com sucesso para pedido {self.id_pedido}")
            
        except Exception as e:
            logger.error(f"Erro ao gerar comanda de reserva: {e}")
            raise

    # =============================================================================
    #                           UTILITÁRIOS
    # =============================================================================

    def exibir_historico_de_funcionarios(self):
        """Exibe histórico de ocupação de todos os funcionários"""
        logger.info("Exibindo histórico de funcionários")
        
        try:
            for funcionario in funcionarios_disponiveis:
                funcionario.mostrar_agenda()
        except Exception as e:
            logger.error(f"Erro ao exibir histórico de funcionários: {e}")

    def mostrar_estrutura(self):
        """Mostra a estrutura da ficha técnica"""
        if self.ficha_tecnica_modular:
            logger.info(f"Mostrando estrutura da ficha técnica do pedido {self.id_pedido}")
            self.ficha_tecnica_modular.mostrar_estrutura()
        else:
            logger.warning(f"Ficha técnica não montada para pedido {self.id_pedido}")

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
                f"Funcionários filtrados para item {id_item}: "
                f"{len(funcionarios_filtrados)}/{len(self.todos_funcionarios)}"
            )
            
            return funcionarios_filtrados
            
        except Exception as e:
            logger.error(f"Erro ao filtrar funcionários para item {id_item}: {e}")
            return self.todos_funcionarios

    def salvar_debug_logs(self):
        """Salva os logs de debug em arquivo"""
        return debug_atividades.salvar_logs()

    def __repr__(self):
        status = f"{len([a for a in self.atividades_modulares if a.alocada])}/{len(self.atividades_modulares)} alocadas"
        cancelado = " [CANCELADO]" if self.pedido_cancelado else ""
        return (
            f"<PedidoDeProducao {self.id_pedido} | "
            f"Produto {self.id_produto} | "
            f"Qtd {self.quantidade} | "
            f"Atividades: {status}{cancelado}>"
        )