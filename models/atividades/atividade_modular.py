import os
from datetime import datetime, timedelta
from enums.equipamentos.tipo_equipamento import TipoEquipamento
from enums.producao.tipo_item import TipoItem
from enums.funcionarios.tipo_profissional import TipoProfissional
from factory import fabrica_equipamentos
from models.funcionarios.funcionario import Funcionario
from parser.carregador_json_atividades import buscar_dados_por_id_atividade
from services.gestores.funcionarios.gestor_funcionarios import GestorFuncionarios
from utils.logs.registrador_funcionarios import registrador_funcionarios
from services.mapas.mapa_gestor_equipamento import MAPA_GESTOR
from services.rollback.rollback import rollback_equipamentos, rollback_funcionarios
from typing import List, Tuple, Optional
from utils.producao.calculadora_duracao import consultar_duracao_por_faixas
from utils.time.conversores_temporais import converter_para_timedelta
from utils.logs.logger_factory import setup_logger
from utils.commons.normalizador_de_nomes import normalizar_nome
from utils.logs.gerenciador_logs import registrar_log_equipamentos, registrar_log_funcionarios, remover_log_funcionarios, remover_log_equipamentos
from utils.logs.quantity_exceptions import QuantityError
from utils.logs.timing_exceptions import IntraActivityTimingError
from utils.logs.error_logger_utils import log_configuration_range_error
from utils.logs.timing_logger import log_intra_activity_timing_error
import traceback

logger = setup_logger('Atividade_Modular')

# Configurações globais
TIPOS_SEM_QUANTIDADE = {TipoEquipamento.BANCADAS}
# Configuração: Sistema apenas registra tipos de funcionários necessários (sem alocação real)


class AtividadeModular:
    """
    Classe responsável por gerenciar uma atividade individual de produção.
    Controla a alocação de equipamentos e funcionários necessários para execução.
    
    ✅ SISTEMA DE TIMING INTEGRADO:
    - Detecta erros de tempo entre equipamentos (INTRA-ATIVIDADE)
    - Registra logs estruturados para análise
    - Cancela atividades com problemas temporais críticos
    """
    
    def __init__(self, id, id_atividade: int, tipo_item: TipoItem, quantidade: float, *args, **kwargs):
        # =============================================================================
        #                           IDENTIFICAÇÃO
        # =============================================================================
        self.id = id
        self.id_atividade = id_atividade
        self.id_pedido = kwargs.get("id_pedido")
        self.id_ordem = kwargs.get("id_ordem")
        self.id_item = kwargs.get("id_produto")
        self.tipo_item = tipo_item
        self.quantidade = quantidade
        self.peso_unitario = kwargs.get("peso_unitario")
        self.alocada = False
        
        # Log inicial mais informativo
        logger.info(
            f"🆔 Criando atividade {self.id_atividade} | "
            f"Tipo: {self.tipo_item.name} | "
            f"Quantidade: {self.quantidade} u | "
            f"Peso unitário: {self.peso_unitario}g"
        )
        
        # =============================================================================
        #                        CARREGAMENTO DE DADOS
        # =============================================================================
        nome_item_fornecido = kwargs.get("nome_item")

        self._carregar_dados_atividade(kwargs.get("dados"))
        
        # =============================================================================
        #                           FUNCIONÁRIOS
        # =============================================================================
        self._configurar_funcionarios(kwargs.get("funcionarios_elegiveis", []))
        
        # =============================================================================
        #                           EQUIPAMENTOS
        # =============================================================================
        self._configurar_equipamentos()
        
        # =============================================================================
        #                              TEMPO
        # =============================================================================
        self._configurar_tempo()

    def _carregar_dados_atividade(self, dados_atividade, nome_item_fornecido=None):
        """Carrega dados da atividade do JSON ou usa dados fornecidos"""
        try:
            if not dados_atividade:
                dados_gerais, dados_atividade = buscar_dados_por_id_atividade(self.id_atividade, self.tipo_item)
                # ✅ CORREÇÃO: Usar o nome real da atividade do JSON
                self.nome_atividade = dados_gerais.get("nome_atividade", f"Atividade {self.id_atividade}")
                self.nome_item = dados_gerais.get("nome_item", "item_desconhecido")
                logger.debug(f"📋 Dados carregados do JSON para atividade {self.id_atividade}")
            else:
                # ✅ CORREÇÃO: Quando dados são fornecidos, ainda precisamos buscar o nome da atividade
                # Se não temos dados_gerais, precisamos buscá-los para obter o nome correto
                dados_gerais, _ = buscar_dados_por_id_atividade(self.id_atividade, self.tipo_item)
                self.nome_atividade = dados_gerais.get("nome_atividade", f"Atividade {self.id_atividade}")
                
                # Usar nome fornecido ou carregar dos dados gerais
                if nome_item_fornecido:
                    self.nome_item = nome_item_fornecido
                    logger.debug(f"📋 Nome do item fornecido diretamente: {self.nome_item}")
                else:
                    self.nome_item = dados_gerais.get("nome_item", "item_desconhecido")
                    logger.debug(f"📋 Nome do item carregado do JSON: {self.nome_item}")
            
            self.dados_atividade = dados_atividade
            
            # ✅ LOG MELHORADO: Mostrar o nome real carregado
            logger.info(
                f"📋 Atividade {self.id_atividade} configurada: '{self.nome_atividade}' "
                f"para item '{self.nome_item}'"
            )
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar dados da atividade {self.id_atividade}: {e}")
            # ✅ FALLBACK: Se houver erro, usar nome genérico
            self.nome_atividade = f"Atividade {self.id_atividade}"
            raise

    def _configurar_funcionarios(self, funcionarios_elegiveis):
        """Configura todos os parâmetros relacionados aos funcionários"""
        try:
            # Tipos profissionais necessários
            tipos_raw = self.dados_atividade.get("tipos_profissionais_permitidos", [])
            self.tipos_necessarios = {
                TipoProfissional[nome] for nome in tipos_raw
                if hasattr(TipoProfissional, nome)
            }
            
            if tipos_raw and not self.tipos_necessarios:
                logger.warning(f"⚠️ Nenhum tipo profissional válido encontrado para atividade {self.id_atividade}")
            
            # Lista de funcionários elegíveis
            self.funcionarios_elegiveis = funcionarios_elegiveis or []
            self.funcionarios_necessarios: List[Funcionario] = [
                f for f in self.funcionarios_elegiveis 
                if f.tipo_profissional in self.tipos_necessarios
            ]
            
            # Parâmetros de alocação
            self.qtd_profissionais_requeridos: int = int(
                self.dados_atividade.get("quantidade_funcionarios", 0)
            )
            self.fips_profissionais_permitidos: dict[str, int] = self.dados_atividade.get(
                "fips_profissionais_permitidos", {}
            )
            self.funcionarios_alocados: List[Funcionario] = []
            
            logger.debug(
                f"👥 Funcionários configurados: {len(self.funcionarios_necessarios)} disponíveis, "
                f"{self.qtd_profissionais_requeridos} necessários"
            )
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar funcionários para atividade {self.id_atividade}: {e}")
            raise
    

    def _configurar_equipamentos(self):
        """Configura todos os parâmetros relacionados aos equipamentos"""
        try:
            # Equipamentos elegíveis
            nomes_equipamentos = self.dados_atividade.get("equipamentos_elegiveis", [])
            self.equipamentos_elegiveis = []
            
            for nome in nomes_equipamentos:
                if hasattr(fabrica_equipamentos, nome):
                    equipamento = getattr(fabrica_equipamentos, nome)
                    self.equipamentos_elegiveis.append(equipamento)
                else:
                    logger.warning(f"⚠️ Equipamento '{nome}' não encontrado na fábrica")
            
            self.equipamentos_selecionados: List = []
            
            # FIPs dos equipamentos
            self.fips_equipamentos = {}
            fips_raw = self.dados_atividade.get("fips_equipamentos", {})
            
            for nome, fip in fips_raw.items():
                if hasattr(fabrica_equipamentos, nome):
                    equipamento = getattr(fabrica_equipamentos, nome)
                    self.fips_equipamentos[equipamento] = fip
                else:
                    logger.warning(f"⚠️ FIP definido para equipamento inexistente: '{nome}'")
            
            # Quantidade por tipo de equipamento
            self._quantidade_por_tipo_equipamento = {}
            tipos_raw = self.dados_atividade.get("tipo_equipamento", {})
            
            for nome, qtd in tipos_raw.items():
                if hasattr(TipoEquipamento, nome):
                    tipo = TipoEquipamento[nome]
                    self._quantidade_por_tipo_equipamento[tipo] = qtd
                else:
                    logger.warning(f"⚠️ Tipo de equipamento inválido: '{nome}'")
            
            # Configurações específicas dos equipamentos
            self.configuracoes_equipamentos = self.dados_atividade.get("configuracoes_equipamentos", {})
            
            logger.debug(
                f"🛠️ Equipamentos configurados: {len(self.equipamentos_elegiveis)} elegíveis, "
                f"{len(self._quantidade_por_tipo_equipamento)} tipos necessários"
            )
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar equipamentos para atividade {self.id_atividade}: {e}")
            raise

    def _configurar_tempo(self):
        """Configura parâmetros temporais da atividade"""
        try:
            # Duração da atividade
            self.duracao: timedelta = consultar_duracao_por_faixas(self.dados_atividade, self.quantidade)

            # Tempo máximo de espera entre atividades
            tempo_espera_raw = self.dados_atividade.get("tempo_maximo_de_espera")
            self.tempo_maximo_de_espera = converter_para_timedelta(tempo_espera_raw)

            logger.debug(
                f"⏱️ Tempo configurado: duração {self.duracao}, "
                f"espera máxima {self.tempo_maximo_de_espera}"
            )

        except ValueError as e:
            if "Nenhuma faixa compatível" in str(e):
                # Erro específico de faixa de quantidade - logar estruturadamente
                faixas_disponiveis = self.dados_atividade.get("faixas", [])

                # Tentar extrair informações do pedido
                id_ordem = getattr(self, 'id_ordem', 1)  # fallback para 1 se não disponível
                id_pedido = getattr(self, 'id_pedido', 1)  # fallback para 1 se não disponível
                nome_item = self.dados_atividade.get("nome", "item_desconhecido")
                id_item = self.dados_atividade.get("id_item", 0)

                # Determinar arquivo de configuração baseado no nome/id
                arquivo_configuracao = f"data/produtos/atividades/{id_item}_{nome_item}.json"

                # Logar erro estruturado
                log_configuration_range_error(
                    id_ordem=id_ordem,
                    id_pedido=id_pedido,
                    id_atividade=self.id_atividade,
                    nome_atividade=self.nome_atividade,
                    id_item=id_item,
                    nome_item=nome_item,
                    quantidade_solicitada=self.quantidade,
                    faixas_disponiveis=faixas_disponiveis,
                    arquivo_configuracao=arquivo_configuracao,
                    contexto_adicional={
                        "metodo_origem": "_configurar_tempo",
                        "classe": "AtividadeModular",
                        "erro_original": str(e)
                    }
                )

            logger.error(f"❌ Erro ao configurar tempo para atividade {self.id_atividade}: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Erro ao configurar tempo para atividade {self.id_atividade}: {e}")
            raise

    # =============================================================================
    #                        GESTÃO DE EQUIPAMENTOS
    # =============================================================================
    
    def _criar_gestores_por_tipo(self) -> dict[TipoEquipamento, object]:
        """Cria gestores específicos para cada tipo de equipamento"""
        gestores_por_tipo = {}

        for tipo_equipamento, _ in self._quantidade_por_tipo_equipamento.items():
            if tipo_equipamento not in MAPA_GESTOR:
                raise ValueError(
                    f"❌ Gestor não definido para o tipo de equipamento: {tipo_equipamento.name}"
                )

            gestor_cls = MAPA_GESTOR[tipo_equipamento]
            equipamentos_filtrados = [
                equipamento for equipamento in self.equipamentos_elegiveis
                if equipamento.tipo_equipamento == tipo_equipamento
            ]

            if not equipamentos_filtrados:
                raise ValueError(
                    f"⚠️ Nenhum equipamento do tipo {tipo_equipamento.name} "
                    f"associado à atividade {self.id_atividade}"
                )

            gestores_por_tipo[tipo_equipamento] = gestor_cls(equipamentos_filtrados)
            logger.debug(f"🔧 Gestor criado para {tipo_equipamento.name}: {len(equipamentos_filtrados)} equipamentos")

        return gestores_por_tipo

    def _registrar_sucesso_equipamentos(self, equipamentos_alocados, inicio: datetime, fim: datetime, **kwargs):
        """Registra o sucesso da alocação de equipamentos com logs melhorados"""
        try:
            logger.debug("🔍 Processando dados de equipamentos alocados...")
            
            # Debug detalhado dos dados recebidos
            for i, dados in enumerate(equipamentos_alocados):
                logger.debug(f"  📦 [{i}] Dados: {dados} (tipo: {type(dados)}, len: {len(dados) if hasattr(dados, '__len__') else 'N/A'})")

            self.equipamentos_selecionados = self._extrair_equipamentos_alocados(equipamentos_alocados)
            inicios, fins = self._extrair_tempos_alocacao(equipamentos_alocados, inicio, fim)

            # Log dos equipamentos selecionados
            equipamentos_nomes = []
            for eqp in self.equipamentos_selecionados:
                if hasattr(eqp, 'nome'):
                    equipamentos_nomes.append(eqp.nome)
                else:
                    equipamentos_nomes.append(str(eqp))
                    logger.warning(f"⚠️ Equipamento sem atributo 'nome': {type(eqp)}")

            logger.info(
                f"🛠️ Equipamentos alocados para atividade {self.id_atividade}: "
                f"{equipamentos_nomes}"
            )

            # Atualizar dados da atividade
            self.equipamento_alocado = self.equipamentos_selecionados
            self.inicio_real = min(inicios) if inicios else inicio
            self.fim_real = max(fins) if fins else fim
            self.alocada = True

            # Log dos tempos
            logger.info(
                f"⏰ Atividade {self.id_atividade} agendada: "
                f"{self.inicio_real.strftime('%H:%M')} - {self.fim_real.strftime('%H:%M')} "
                f"(duração: {self.fim_real - self.inicio_real})"
            )

            # Registrar log estruturado - verificar se é atividade consolidada
            if getattr(self, '_is_consolidated', False):
                # Esta é uma atividade consolidada - gerar log especial
                self._registrar_log_consolidacao(equipamentos_alocados, self.inicio_real, self.fim_real)
            else:
                # Log normal de equipamentos
                registrar_log_equipamentos(
                    id_ordem=self.id_ordem,
                    id_pedido=self.id_pedido,
                    id_atividade=self.id_atividade,
                    nome_item=self.nome_item,
                    nome_atividade=self.nome_atividade,
                    equipamentos_alocados=equipamentos_alocados
                )

            return self.inicio_real, self.fim_real

        except Exception as e:
            logger.error(f"❌ Erro ao registrar sucesso dos equipamentos: {e}")
            raise

    def _registrar_log_consolidacao(self, equipamentos_alocados, inicio, fim):
        """Registra log especial para atividades consolidadas"""
        from utils.logs.log_subprodutos_agrupados import registrar_log_subproduto_agrupado

        dados_log = getattr(self, '_dados_log_agrupado', None)
        if dados_log:
            registrar_log_subproduto_agrupado(
                ordens_e_pedidos=dados_log['ordens_e_pedidos'],
                id_atividade=self.id_atividade,
                nome_item=self.nome_item,
                nome_atividade=self.nome_atividade,
                equipamentos_alocados=equipamentos_alocados,
                quantidade_total=dados_log['quantidade_total'],
                detalhes_consolidacao=dados_log['detalhes_consolidacao']
            )

            logger.info(
                f"🔗 Log de subproduto agrupado registrado para atividade {self.id_atividade} "
                f"({len(dados_log['ordens_e_pedidos'])} pedidos consolidados)"
            )
        else:
            logger.warning(
                f"⚠️ Atividade {self.id_atividade} marcada como consolidada, mas sem dados de consolidação"
            )

    def _simular_execucao_consolidada(self):
        """
        🔗 Simula execução para atividades que foram consolidadas automaticamente.
        """
        # Calcular horários baseado na duração da atividade
        fim_simulado = datetime.now().replace(hour=6, minute=27, second=0, microsecond=0)
        inicio_simulado = fim_simulado - self.duracao

        self.inicio_real = inicio_simulado
        self.fim_real = fim_simulado

        logger.info(
            f"⚡ Simulação de execução consolidada para atividade {self.id_atividade}: "
            f"{inicio_simulado.strftime('%H:%M')} - {fim_simulado.strftime('%H:%M')} "
            f"(execução real já foi feita via consolidação automática)"
        )

        # Retornar sucesso simulado - equipamentos_alocados vazio pois já foi processado
        return True, inicio_simulado, fim_simulado, self.tempo_maximo_de_espera, []

    def _extrair_equipamentos_alocados(self, equipamentos_alocados):
        """Extrai lista de equipamentos dos dados de alocação com validação melhorada"""
        equipamentos_selecionados = []
        
        try:
            if all(isinstance(dados, (list, tuple)) and len(dados) == 4 for dados in equipamentos_alocados):
                # Formato: (sucesso, equipamentos, inicio, fim)
                for dados in equipamentos_alocados:
                    equipamentos = dados[1]
                    if isinstance(equipamentos, list):
                        equipamentos_selecionados.extend(equipamentos)
                    else:
                        equipamentos_selecionados.append(equipamentos)
            else:
                # Formato simples: (equipamento,) ou [equipamento]
                for dados in equipamentos_alocados:
                    if isinstance(dados, (list, tuple)) and len(dados) > 0:
                        equipamentos_selecionados.append(dados[0])
                    else:
                        equipamentos_selecionados.append(dados)
            
            logger.debug(f"✅ Extraídos {len(equipamentos_selecionados)} equipamentos")
            return equipamentos_selecionados
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair equipamentos alocados: {e}")
            return []

    def _extrair_tempos_alocacao(self, equipamentos_alocados, inicio_default, fim_default):
        """Extrai tempos de início e fim dos equipamentos alocados com validação"""
        try:
            if all(isinstance(dados, (list, tuple)) and len(dados) == 4 for dados in equipamentos_alocados):
                inicios = [dados[2] for dados in equipamentos_alocados if dados[2] is not None]
                fins = [dados[3] for dados in equipamentos_alocados if dados[3] is not None]
            else:
                inicios = [inicio_default]
                fins = [fim_default]
            
            # Garantir que temos pelo menos os valores default
            if not inicios:
                inicios = [inicio_default]
            if not fins:
                fins = [fim_default]
            
            logger.debug(f"⏰ Tempos extraídos: {len(inicios)} inícios, {len(fins)} fins")
            return inicios, fins
            
        except Exception as e:
            logger.error(f"❌ Erro ao extrair tempos de alocação: {e}")
            return [inicio_default], [fim_default]

    # =============================================================================
    #                         ALOCAÇÃO PRINCIPAL
    # =============================================================================

    def tentar_alocar_e_iniciar_equipamentos(
        self,
        inicio_jornada: datetime,
        fim_jornada: datetime
    ) -> Tuple[bool, Optional[datetime], Optional[datetime], Optional[timedelta], List[Tuple]]:
        """
        Método principal para alocação de equipamentos e funcionários.
        Retorna: (sucesso, inicio_real, fim_real, tempo_max_espera, equipamentos_alocados)
        """
        logger.info(f"🔄 Iniciando alocação da atividade {self.id_atividade} ({self.nome_atividade})")

        # 🔗 NOVO: Verificar se atividade já foi consolidada automaticamente
        from utils.agrupamento.cache_atividades_intervalo import cache_atividades_intervalo

        # Verificar se esta atividade já foi executada como parte de uma consolidação
        if hasattr(self, '_já_consolidada_automaticamente'):
            logger.info(f"⚡ Atividade {self.id_atividade} já foi consolidada automaticamente - simulando execução")
            return self._simular_execucao_consolidada()

        # Verificar se há grupo de consolidação pendente
        grupo_consolidacao = cache_atividades_intervalo.verificar_oportunidade_agrupamento(
            self.id_item,
            inicio_jornada - self.duracao,
            inicio_jornada,
            "MISTURADORAS_COM_COCCAO"  # TODO: Tornar dinâmico baseado no tipo de equipamento
        )

        if grupo_consolidacao:
            logger.info(f"🔗 Atividade {self.id_atividade} faz parte de grupo de consolidação pendente")
            # Marcar como consolidada para evitar execução individual
            self._já_consolidada_automaticamente = True
            return self._simular_execucao_consolidada()
        
        # ✅ VERIFICAÇÃO ESPECIAL: Se esta é a última atividade e tem fim_obrigatorio
        if hasattr(self, 'fim_obrigatorio') and self.fim_obrigatorio:
            logger.info(
                f"⏰ Atividade {self.id_atividade} tem fim obrigatório às {self.fim_obrigatorio.strftime('%H:%M')}"
            )
            # Ajustar fim_jornada para o fim obrigatório
            fim_jornada = self.fim_obrigatorio
        
        try:
            # Caso especial: atividade sem equipamentos
            if not self._quantidade_por_tipo_equipamento:
                logger.info(f"ℹ️ Atividade {self.id_atividade} não requer equipamentos")
                return self._alocar_apenas_funcionarios(inicio_jornada, fim_jornada)
            
            # Tentativa de alocação com equipamentos
            return self._alocar_equipamentos_e_funcionarios(inicio_jornada, fim_jornada)
            
        except Exception as e:
            logger.error(f"❌ Falha na alocação da atividade {self.id_atividade}: {e}")
            raise

    def _alocar_apenas_funcionarios(self, inicio_jornada: datetime, fim_jornada: datetime):
        """Aloca apenas funcionários quando não há equipamentos necessários"""
        try:
            inicio_atividade = fim_jornada - self.duracao
            fim_atividade = fim_jornada
            self.inicio_real = inicio_atividade
            self.fim_real = fim_atividade

            logger.info(
                f"👥 Alocando apenas funcionários para atividade {self.id_atividade}: "
                f"{inicio_atividade.strftime('%H:%M')} - {fim_atividade.strftime('%H:%M')}"
            )

            # Apenas registrar requisito de funcionário (sem alocação real)
            self._registrar_requisito_funcionario(inicio_atividade, fim_atividade)

            return True, inicio_atividade, fim_atividade, self.tempo_maximo_de_espera, []
            
        except Exception as e:
            logger.error(f"❌ Erro na alocação de funcionários: {e}")
            raise

    def _alocar_equipamentos_e_funcionarios(self, inicio_jornada: datetime, fim_jornada: datetime):
        """Aloca equipamentos e funcionários seguindo o algoritmo de retrocesso - VERSÃO CORRIGIDA"""
        
        # ✅ VERIFICAÇÃO: Se tem fim_obrigatorio, deve terminar exatamente nesse horário
        tem_fim_obrigatorio = hasattr(self, 'fim_obrigatorio') and self.fim_obrigatorio
        
        if tem_fim_obrigatorio:
            horario_final = self.fim_obrigatorio
            logger.info(
                f"🎯 Atividade {self.id_atividade} DEVE terminar às {self.fim_obrigatorio.strftime('%H:%M')} "
                f"(tempo_maximo_de_espera = 0)"
            )
        else:
            horario_final = fim_jornada
        
        tentativas = 0
        alocacao_exata_tentada = False
        
        # Calcular janela total para logs informativos
        janela_total = fim_jornada - inicio_jornada
        logger.info(
            f"🔄 Iniciando busca por horário disponível "
            f"de {inicio_jornada.strftime('%d/%m %H:%M')} até {fim_jornada.strftime('%d/%m %H:%M')} "
            f"(janela: {janela_total})"
        )
        
        try:
            while horario_final - self.duracao >= inicio_jornada:
                tentativas += 1
                
                # Log de progresso a cada hora de tentativas
                if tentativas % 60 == 0:
                    tempo_restante = (horario_final - self.duracao - inicio_jornada)
                    horas_restantes = tempo_restante.total_seconds() / 3600
                    logger.debug(
                        f"🔍 Tentativa {tentativas:,} - testando {horario_final.strftime('%H:%M')} "
                        f"({horas_restantes:.1f}h restantes)"
                    )
                
                try:
                    # Tentar alocação no horário atual
                    sucesso, equipamentos_alocados = self._tentar_alocacao_no_horario(horario_final)
                    
                    if sucesso:
                        # ✅ VALIDAÇÃO ESPECIAL: Se tem fim_obrigatorio, verificar se atende
                        if tem_fim_obrigatorio:
                            equipamentos_ordenados = sorted(equipamentos_alocados, key=lambda x: x[2])
                            fim_real = equipamentos_ordenados[-1][3] if equipamentos_ordenados else horario_final
                            
                            if fim_real != self.fim_obrigatorio:
                                # Esta alocação não atende a restrição de pontualidade
                                diferenca = abs((fim_real - self.fim_obrigatorio).total_seconds())
                                
                                if not alocacao_exata_tentada and diferenca <= 60:  # Tolerância de 1 minuto
                                    logger.debug(
                                        f"⚠️ Alocação próxima mas não exata: terminaria às {fim_real.strftime('%H:%M')} "
                                        f"(diferença: {diferenca}s). Continuando busca..."
                                    )
                                
                                self._fazer_rollback_tentativa(equipamentos_alocados)
                                horario_final -= timedelta(minutes=1)
                                
                                # Marcar que já tentamos a alocação exata
                                if horario_final == self.fim_obrigatorio:
                                    alocacao_exata_tentada = True
                                
                                continue
                            else:
                                logger.info(
                                    f"✅ Alocação PONTUAL conseguida! Atividade terminará exatamente às "
                                    f"{fim_real.strftime('%H:%M')} conforme requerido"
                                )
                        
                        logger.info(
                            f"✅ Alocação bem-sucedida na tentativa {tentativas:,} "
                            f"(horário: {horario_final.strftime('%H:%M')})"
                        )
                        return self._finalizar_alocacao_bem_sucedida(equipamentos_alocados)
                    else:
                        # Rollback desta tentativa e avançar para próximo horário
                        self._fazer_rollback_tentativa(equipamentos_alocados)
                        horario_final -= timedelta(minutes=1)
                        
                except QuantityError as e:
                    # 🚫 ERRO DE QUANTIDADE - CANCELAR IMEDIATAMENTE
                    logger.error(
                        f"🚫 ATIVIDADE {self.id_atividade} CANCELADA devido a erro de quantidade: "
                        f"{e.error_type} - {e}"
                    )
                    
                    # Criar mensagem detalhada para o erro
                    sugestoes_texto = ""
                    if e.suggestions:
                        sugestoes_texto = f" Sugestões: {'; '.join(e.suggestions[:3])}"
                    
                    # 🔥 LANÇAR EXCEÇÃO ESPECÍFICA PARA O PEDIDO TRATAR
                    raise RuntimeError(
                        f"Atividade {self.id_atividade} ({self.nome_atividade}) não pode ser executada. "
                        f"Erro de quantidade: {e.error_type} - {e}.{sugestoes_texto}"
                    ) from e
                    
                except IntraActivityTimingError as e:
                    # ⏰ ERRO DE TEMPO INTRA-ATIVIDADE - CANCELAR IMEDIATAMENTE
                    logger.error(
                        f"⏰ ATIVIDADE {self.id_atividade} CANCELADA devido a erro de tempo intra-atividade: "
                        f"{e.error_type} - {e}"
                    )
                    
                    # Criar mensagem detalhada para o erro
                    sugestoes_texto = ""
                    if e.suggestions:
                        sugestoes_texto = f" Sugestões: {'; '.join(e.suggestions[:3])}"
                    
                    # 🔥 LANÇAR EXCEÇÃO ESPECÍFICA PARA O PEDIDO TRATAR
                    raise RuntimeError(
                        f"Atividade {self.id_atividade} ({self.nome_atividade}) não pode ser executada. "
                        f"Erro de tempo entre equipamentos: {e.error_type} - {e}.{sugestoes_texto}"
                    ) from e

            # Se chegou aqui, esgotou toda a janela temporal disponível
            tempo_total_tentado = fim_jornada - inicio_jornada
            logger.error(
                f"🛑 Janela temporal completamente esgotada após {tentativas:,} tentativas. "
                f"Impossível alocar atividade {self.id_atividade}"
            )
            
            # Diagnóstico detalhado
            logger.error(f"📊 DIAGNÓSTICO DETALHADO DA FALHA:")
            logger.error(f"   🆔 Atividade: {self.id_atividade} ({self.nome_atividade})")
            logger.error(f"   ⏱️ Duração necessária: {self.duracao}")
            logger.error(f"   📅 Janela disponível: {tempo_total_tentado}")
            logger.error(f"   🕐 Período: {inicio_jornada.strftime('%d/%m %H:%M')} → {fim_jornada.strftime('%d/%m %H:%M')}")
            
            if tem_fim_obrigatorio:
                logger.error(f"   ⚠️ RESTRIÇÃO CRÍTICA: Atividade DEVE terminar EXATAMENTE às {self.fim_obrigatorio.strftime('%H:%M')}")
                logger.error(f"   📍 Isso significa que deve começar às {(self.fim_obrigatorio - self.duracao).strftime('%H:%M')}")

            return False, None, None, self.tempo_maximo_de_espera, []
            
        except (QuantityError, IntraActivityTimingError):
            # Re-lançar exceções específicas
            raise

    def _tentar_alocacao_no_horario(self, horario_final: datetime):
        """
        ✅ VERSÃO ATUALIZADA: Tenta alocar todos os equipamentos necessários em um horário específico.
        Trata exceções de quantidade E tempo intra-atividade de forma genérica e centralizada.
        """
        equipamentos_alocados = []
        horario_fim_etapa = horario_final

        try:
            for tipo_eqp, qtd in reversed(list(self._quantidade_por_tipo_equipamento.items())):
                logger.debug(f"🔧 Tentando alocar {tipo_eqp.name} para {horario_fim_etapa.strftime('%H:%M')}")
                
                try:
                    resultado_alocacao = self._alocar_tipo_equipamento(tipo_eqp, horario_fim_etapa)
                    
                    if not resultado_alocacao[0] or resultado_alocacao[1] is None:
                        logger.debug(f"❌ Falha na alocação de {tipo_eqp.name}")
                        return False, equipamentos_alocados
                    
                    equipamentos_alocados.append(resultado_alocacao)
                    horario_fim_etapa = resultado_alocacao[2]  # Usar início desta etapa como fim da próxima
                    
                except QuantityError as e:
                    # 🚫 ERRO DE QUANTIDADE - CANCELAR IMEDIATAMENTE SEM CONTINUAR
                    logger.error(
                        f"🚫 Cancelando alocação da atividade {self.id_atividade} "
                        f"devido a erro de quantidade em {tipo_eqp.name}: {e.error_type}"
                    )
                    
                    # 🔥 LANÇAR EXCEÇÃO PARA CANCELAR TODA A ATIVIDADE
                    raise e

            # Verificar sequenciamento (agora com detecção de erros intra-atividade)
            try:
                if not self._verificar_sequenciamento(equipamentos_alocados):
                    logger.debug("❌ Falha no sequenciamento dos equipamentos")
                    return False, equipamentos_alocados
            except IntraActivityTimingError as e:
                # ⏰ ERRO DE TEMPO INTRA-ATIVIDADE
                logger.error(
                    f"⏰ Erro de tempo intra-atividade detectado: {e.error_type}"
                )
                # Re-lançar para tratamento no nível superior
                raise e

            logger.debug("✅ Todos os equipamentos alocados com sucesso")
            return True, equipamentos_alocados
            
        except (QuantityError, IntraActivityTimingError):
            # Re-lançar exceções específicas para cancelar atividade
            raise
            
        except Exception as e:
            logger.error(f"❌ Erro durante tentativa de alocação: {e}")
            return False, equipamentos_alocados

    def _alocar_tipo_equipamento(self, tipo_eqp: TipoEquipamento, horario_fim_etapa: datetime):
        """
        Aloca um tipo específico de equipamento com tratamento robusto de erros de quantidade.
        Agora trata exceções específicas de quantidade de forma genérica.
        """
        try:
            equipamentos = [
                eqp for eqp in self.equipamentos_elegiveis 
                if eqp.tipo_equipamento == tipo_eqp
            ]

            if not equipamentos:
                logger.warning(f"⚠️ Nenhum equipamento disponível do tipo {tipo_eqp.name}")
                return (False, None, None, None)

            classe_gestor = MAPA_GESTOR.get(tipo_eqp)
            if not classe_gestor:
                logger.warning(f"⚠️ Nenhum gestor configurado para tipo {tipo_eqp.name}")
                return (False, None, None, None)

            gestor = classe_gestor(equipamentos)
            metodo_alocacao = self._resolver_metodo_alocacao(tipo_eqp)
            config = self._obter_configuracao_equipamento(equipamentos[0])
            
            inicio_previsto = horario_fim_etapa - self.duracao
            
            logger.debug(
                f"🔧 Alocando {tipo_eqp.name}: "
                f"{inicio_previsto.strftime('%H:%M')} - {horario_fim_etapa.strftime('%H:%M')}"
            )
            
            resultado = metodo_alocacao(
                gestor=gestor,
                inicio=inicio_previsto,
                fim=horario_fim_etapa,
                **config
            )
            
            if resultado[0]:  # Sucesso
                logger.debug(f"✅ {tipo_eqp.name} alocado com sucesso")
            
            return resultado
            
        except QuantityError as e:
            # 🚫 ERRO ESPECÍFICO DE QUANTIDADE - REGISTRAR E RE-LANÇAR
            logger.error(
                f"🚫 ERRO DE QUANTIDADE para {tipo_eqp.name}: {e.error_type} - {e}"
            )
            
            # 🔥 LANÇAR EXCEÇÃO PARA CANCELAR TODA A TENTATIVA DE ALOCAÇÃO
            raise e
            
        except Exception as e:
            logger.error(f"❌ Erro genérico ao alocar {tipo_eqp.name}: {e}")
            traceback.print_exc()
            return (False, None, None, None)

    def _obter_configuracao_equipamento(self, equipamento_exemplo):
        """Obtém configuração específica do equipamento com validação"""
        try:
            nome_normalizado = normalizar_nome(equipamento_exemplo.nome)
            config = self.configuracoes_equipamentos.get(nome_normalizado, {})
            
            if config:
                logger.debug(f"🔧 Configuração carregada para {equipamento_exemplo.nome}: {config}")
            
            return config
            
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter configuração do equipamento: {e}")
            return {}

    def _verificar_sequenciamento(self, equipamentos_alocados):
        """
        ✅ VERSÃO ATUALIZADA: Verifica se os equipamentos estão sequenciados corretamente 
        com logs detalhados E sistema de logging de tempo intra-atividade.
        """
        try:
            if len(equipamentos_alocados) <= 1:
                return True
            
            equipamentos_ordenados = sorted(equipamentos_alocados, key=lambda x: x[2])
            
            for i in range(1, len(equipamentos_ordenados)):
                fim_anterior = equipamentos_ordenados[i - 1][3]
                inicio_atual = equipamentos_ordenados[i][2]
                nome_anterior = getattr(equipamentos_ordenados[i - 1][1], 'nome', 'Equipamento Desconhecido')
                nome_atual = getattr(equipamentos_ordenados[i][1], 'nome', 'Equipamento Desconhecido')

                if fim_anterior != inicio_atual:
                    gap = abs((fim_anterior - inicio_atual).total_seconds())
                    atraso = inicio_atual - fim_anterior
                    
                    logger.warning(
                        f"🔁 Equipamentos da atividade {self.id_atividade} não estão sequenciados. "
                        f"Gap de {gap}s entre '{nome_anterior}' "
                        f"({fim_anterior.strftime('%H:%M:%S')}) e "
                        f"'{nome_atual}' ({inicio_atual.strftime('%H:%M:%S')})"
                    )
                    
                    # ✅ VERIFICAR SE É UM ERRO DE TEMPO MÁXIMO DE ESPERA INTRA-ATIVIDADE
                    if hasattr(self, 'tempo_maximo_de_espera') and self.tempo_maximo_de_espera is not None:
                        if atraso > self.tempo_maximo_de_espera:
                            logger.error(
                                f"⏰ ERRO DE TEMPO INTRA-ATIVIDADE: Gap de {atraso} excede "
                                f"tempo máximo de espera ({self.tempo_maximo_de_espera}) na atividade {self.id_atividade}"
                            )
                            
                            # ✅ REGISTRAR NO SISTEMA DE LOGS TEMPORAL UNIFICADO
                            try:
                                from utils.logs.temporal_allocation_logger import log_intra_activity_timing_error
                                
                                log_intra_activity_timing_error(
                                    id_ordem=self.id_ordem,
                                    id_pedido=self.id_pedido,
                                    activity_id=self.id_atividade,
                                    activity_name=self.nome_atividade,
                                    current_equipment=nome_anterior,
                                    successor_equipment=nome_atual,
                                    current_end_time=fim_anterior,
                                    successor_start_time=inicio_atual,
                                    maximum_wait_time=self.tempo_maximo_de_espera
                                )
                                
                                logger.info(
                                    f"📝 Erro de tempo intra-atividade registrado no sistema temporal unificado: "
                                    f"TEMPO_MAXIMO_ESPERA_INTRA_ATIVIDADE"
                                )
                                
                            except Exception as log_err:
                                logger.warning(f"⚠️ Falha ao registrar log temporal intra-atividade: {log_err}")
                            
                            # ✅ LANÇAR EXCEÇÃO PARA CANCELAR A ATIVIDADE
                            raise IntraActivityTimingError(
                                activity_id=self.id_atividade,
                                activity_name=self.nome_atividade,
                                current_equipment=nome_anterior,
                                successor_equipment=nome_atual,
                                current_end_time=fim_anterior,
                                successor_start_time=inicio_atual,
                                maximum_wait_time=self.tempo_maximo_de_espera,
                                actual_delay=atraso
                            )
                    
                    # Se não há restrição de tempo máximo ou está dentro do limite, só avisar
                    return False
                
            logger.debug("✅ Sequenciamento dos equipamentos validado")
            return True
            
        except IntraActivityTimingError:
            # Re-lançar exceção de timing para tratamento superior
            raise
            
        except Exception as e:
            logger.error(f"❌ Erro na verificação de sequenciamento: {e}")
            return False

    def _finalizar_alocacao_bem_sucedida(self, equipamentos_alocados):
        """Finaliza uma alocação bem-sucedida com logs informativos"""
        try:
            equipamentos_ordenados = sorted(equipamentos_alocados, key=lambda x: x[2])
            inicio_atividade = equipamentos_ordenados[0][2]
            fim_atividade = equipamentos_ordenados[-1][3]
            
            self.inicio_real = inicio_atividade
            self.fim_real = fim_atividade
            
            logger.info(
                f"✅ Atividade {self.id_atividade} alocada com sucesso: "
                f"{inicio_atividade.strftime('%H:%M')} - {fim_atividade.strftime('%H:%M')}"
            )
            
            self._registrar_sucesso_equipamentos(equipamentos_alocados, inicio_atividade, fim_atividade)

            # Registrar requisito de funcionário (apenas registro, sem alocação)
            self._registrar_requisito_funcionario(inicio_atividade, fim_atividade)

            return True, inicio_atividade, fim_atividade, self.tempo_maximo_de_espera, equipamentos_alocados
            
        except Exception as e:
            logger.error(f"❌ Erro ao finalizar alocação: {e}")
            raise

    def _fazer_rollback_tentativa(self, equipamentos_alocados):
        """Faz rollback de uma tentativa de alocação que falhou"""
        if equipamentos_alocados:
            logger.debug(f"🔄 Executando rollback de {len(equipamentos_alocados)} equipamentos")
            
            rollback_equipamentos(equipamentos_alocados, self.id_ordem, self.id_pedido, self.id_atividade)
            remover_log_equipamentos(self.id_ordem, self.id_pedido, self.id_atividade)

    # =============================================================================
    #                        ALOCAÇÃO DE FUNCIONÁRIOS
    # =============================================================================

    def _alocar_funcionarios(self, inicio: datetime, fim: datetime) -> bool:
        """Aloca funcionários para a atividade com logs melhorados"""
        try:
            logger.info(
                f"👥 Tentando alocar {self.qtd_profissionais_requeridos} funcionários "
                f"para atividade {self.id_atividade}"
            )
            
            flag, funcionarios_alocados = GestorFuncionarios.priorizar_funcionarios(
                id_ordem=self.id_ordem,
                id_pedido=self.id_pedido,
                inicio=inicio,
                fim=fim,
                qtd_profissionais_requeridos=self.qtd_profissionais_requeridos,
                tipos_necessarios=self.tipos_necessarios,
                fips_profissionais_permitidos=self.fips_profissionais_permitidos,
                funcionarios_elegiveis=self.funcionarios_elegiveis,
                nome_atividade=self.nome_atividade
            )

            if flag:
                # Registrar ocupação dos funcionários
                for funcionario in funcionarios_alocados:
                    funcionario.registrar_ocupacao(
                        id_ordem=self.id_ordem,
                        id_pedido=self.id_pedido,
                        id_atividade_json=self.id_atividade,
                        inicio=inicio,
                        fim=fim
                    )
                
                # Log estruturado
                registrar_log_funcionarios(
                    id_ordem=self.id_ordem,
                    id_pedido=self.id_pedido,
                    id_atividade=self.id_atividade,
                    nome_item=self.nome_item,
                    nome_atividade=self.nome_atividade,
                    funcionarios_alocados=funcionarios_alocados,
                    inicio=inicio,
                    fim=fim
                )
                
                logger.info(f"✅ {len(funcionarios_alocados)} funcionários alocados com sucesso")
                return True
            else:
                logger.warning(f"❌ Falha na alocação de funcionários para atividade {self.id_atividade}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro na alocação de funcionários: {e}")
            return False

    # =============================================================================
    #                    MÉTODOS DE ALOCAÇÃO POR TIPO
    # =============================================================================
    
    def _resolver_metodo_alocacao(self, tipo_equipamento):
        """Resolve o método de alocação baseado no tipo de equipamento"""
        metodos_alocacao = {
            TipoEquipamento.REFRIGERACAO_CONGELAMENTO: self._alocar_camara,
            TipoEquipamento.BANCADAS: self._alocar_bancada,
            TipoEquipamento.FOGOES: self._alocar_fogao,
            TipoEquipamento.BATEDEIRAS: self._alocar_batedeira,
            TipoEquipamento.BALANCAS: self._alocar_balanca,
            TipoEquipamento.FORNOS: self._alocar_forno,
            TipoEquipamento.FRITADEIRAS: self._alocar_fritadeira,
            TipoEquipamento.MISTURADORAS: self._alocar_misturadora,
            TipoEquipamento.MISTURADORAS_COM_COCCAO: self._alocar_misturadora_com_coccao,
            TipoEquipamento.ARMARIOS_PARA_FERMENTACAO: self._alocar_armario_fermentacao,
            TipoEquipamento.MODELADORAS: self._alocar_modeladora,
            TipoEquipamento.DIVISORAS_BOLEADORAS: self._alocar_divisora_boleadora,
            TipoEquipamento.EMBALADORAS: self._alocar_embaladora,
        }
        
        metodo = metodos_alocacao.get(tipo_equipamento)
        if not metodo:
            raise ValueError(f"❌ Nenhum método de alocação definido para {tipo_equipamento.name}")
        
        return metodo

    # Métodos específicos de alocação por tipo de equipamento
    def _alocar_camara(self, gestor, inicio, fim, **kwargs): 
        from enums.equipamentos.tipo_equipamento import TipoEquipamento
        return gestor.alocar(inicio, fim, self, self.quantidade)
    
    def _alocar_bancada(self, gestor, inicio, fim, **kwargs): 
        from enums.equipamentos.tipo_equipamento import TipoEquipamento
        return gestor.alocar(inicio, fim, self)
    
    def _alocar_fogao(self, gestor, inicio, fim, **kwargs): 
        from enums.equipamentos.tipo_equipamento import TipoEquipamento
        return gestor.alocar(inicio, fim, self, self.quantidade)
    
    def _alocar_batedeira(self, gestor, inicio, fim, **kwargs): 
        from enums.equipamentos.tipo_equipamento import TipoEquipamento
        return gestor.alocar(inicio, fim, self, self.quantidade)
    
    def _alocar_balanca(self, gestor, inicio, fim, **kwargs): 
        from enums.equipamentos.tipo_equipamento import TipoEquipamento
        return gestor.alocar(inicio, fim, self, self.quantidade)
    
    def _alocar_forno(self, gestor, inicio, fim, **kwargs): 
        from enums.equipamentos.tipo_equipamento import TipoEquipamento
        return gestor.alocar(inicio, fim, self, self.quantidade)
    
    def _alocar_fritadeira(self, gestor, inicio, fim, **kwargs): 
        from enums.equipamentos.tipo_equipamento import TipoEquipamento
        return gestor.alocar(inicio, fim, self, self.quantidade)
    
    def _alocar_misturadora(self, gestor, inicio, fim, **kwargs): 
        from enums.equipamentos.tipo_equipamento import TipoEquipamento
        return gestor.alocar(inicio, fim, self, self.quantidade)
    
    def _alocar_misturadora_com_coccao(self, gestor, inicio, fim, **kwargs): 
        from enums.equipamentos.tipo_equipamento import TipoEquipamento
        return gestor.alocar(inicio, fim, self, self.quantidade)
    
    def _alocar_armario_fermentacao(self, gestor, inicio, fim, **kwargs): 
        from enums.equipamentos.tipo_equipamento import TipoEquipamento
        return gestor.alocar(inicio, fim, self, self.quantidade)
    
    def _alocar_modeladora(self, gestor, inicio, fim, **kwargs): 
        from enums.equipamentos.tipo_equipamento import TipoEquipamento
        return gestor.alocar(inicio, fim, self, self.quantidade)
    
    def _alocar_divisora_boleadora(self, gestor, inicio, fim, **kwargs): 
        from enums.equipamentos.tipo_equipamento import TipoEquipamento
        return gestor.alocar(inicio, fim, self, self.quantidade)
    
    def _alocar_embaladora(self, gestor, inicio, fim, **kwargs): 
        from enums.equipamentos.tipo_equipamento import TipoEquipamento
        return gestor.alocar(inicio, fim, self, self.quantidade)
    

    # =============================================================================
    #                           UTILITÁRIOS
    # =============================================================================

    def mostrar_agendas_dos_gestores(self):
        """Mostra as agendas dos gestores de equipamentos"""
        try:
            gestores = self._criar_gestores_por_tipo()
            for tipo, gestor in gestores.items():
                if hasattr(gestor, "mostrar_agenda"):
                    logger.info(f"📅 Agenda do gestor {tipo.name}:")
                    gestor.mostrar_agenda()
                else:
                    logger.warning(f"⚠️ Gestor {tipo.name} não possui método mostrar_agenda")
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível mostrar agendas dos gestores: {e}")

    def _registrar_requisito_funcionario(self, inicio: datetime, fim: datetime):
        """
        Registra requisito de funcionário diretamente no registrador.

        Args:
            inicio: Horário de início da atividade
            fim: Horário de fim da atividade
        """
        try:
            logger.info(f"🔍 CHAMADA: _registrar_requisito_funcionario para atividade {self.id_atividade}")
            logger.info(f"🔍 CHECK: tipos_necessarios={self.tipos_necessarios}, qtd={self.qtd_profissionais_requeridos}")
            # Só registrar se há funcionários necessários
            if self.tipos_necessarios and self.qtd_profissionais_requeridos > 0:
                # Registrar diretamente no registrador_funcionarios
                registrador_funcionarios.registrar_requisito_funcionario(
                    id_ordem=self.id_ordem,
                    id_pedido=self.id_pedido,
                    id_atividade=self.id_atividade,
                    nome_atividade=self.nome_atividade,
                    tipos_profissionais=self.tipos_necessarios,
                    inicio=inicio,
                    fim=fim,
                    quantidade=self.qtd_profissionais_requeridos,
                    fips=self.fips_profissionais_permitidos
                )
                logger.info(f"✅ Requisito de funcionário registrado para atividade {self.id_atividade}")
            else:
                logger.debug(f"ℹ️ Atividade {self.id_atividade} não requer funcionários")

        except Exception as e:
            logger.error(f"❌ Erro ao registrar requisito de funcionário para atividade {self.id_atividade}: {e}")

    def obter_resumo_alocacao(self) -> dict:
        """Retorna um resumo da alocação da atividade"""
        return {
            "id_atividade": self.id_atividade,
            "nome_atividade": self.nome_atividade,
            "tipo_item": self.tipo_item.name,
            "quantidade": self.quantidade,
            "alocada": self.alocada,
            "inicio_real": self.inicio_real.isoformat() if self.inicio_real else None,
            "fim_real": self.fim_real.isoformat() if self.fim_real else None,
            "duracao_planejada": str(self.duracao),
            "duracao_real": str(self.fim_real - self.inicio_real) if self.inicio_real and self.fim_real else None,
            "equipamentos_alocados": len(self.equipamentos_selecionados),
            "funcionarios_necessarios": self.qtd_profissionais_requeridos,
            "tempo_maximo_espera": str(self.tempo_maximo_de_espera) if self.tempo_maximo_de_espera else None
        }

    def __repr__(self):
        status = "Alocada" if self.alocada else "Pendente"
        return (
            f"<AtividadeModular {self.id_atividade} ({self.nome_atividade}) | "
            f"{self.tipo_item.name} | {status}>"
        )