import os
from datetime import datetime, timedelta
from enums.equipamentos.tipo_equipamento import TipoEquipamento
from enums.producao.tipo_item import TipoItem
from enums.funcionarios.tipo_profissional import TipoProfissional
from factory import fabrica_equipamentos
from models.funcionarios.funcionario import Funcionario
from parser.carregador_json_atividades import buscar_dados_por_id_atividade
from services.gestor_funcionarios.gestor_funcionarios import GestorFuncionarios
from services.mapas.mapa_gestor_equipamento import MAPA_GESTOR
from services.rollback.rollback import rollback_equipamentos, rollback_funcionarios
from typing import List, Tuple, Optional
from utils.producao.calculadora_duracao import consultar_duracao_por_faixas
from utils.time.conversores_temporais import converter_para_timedelta
from utils.logs.logger_factory import setup_logger
from utils.commons.normalizador_de_nomes import normalizar_nome
from utils.logs.gerenciador_logs import registrar_log_equipamentos, registrar_log_funcionarios, remover_log_funcionarios, remover_log_equipamentos
import traceback

logger = setup_logger('Atividade_Modular')

# Configurações globais
TIPOS_SEM_QUANTIDADE = {TipoEquipamento.BANCADAS}
FUNCIONARIOS_ATIVOS = False  # Flag para ativar/desativar alocação de funcionários


class AtividadeModular:
    """
    Classe responsável por gerenciar uma atividade individual de produção.
    Controla a alocação de equipamentos e funcionários necessários para execução.
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

            # Registrar log estruturado
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

            if FUNCIONARIOS_ATIVOS:
                sucesso_funcionarios = self._alocar_funcionarios(inicio_atividade, fim_atividade)
                if not sucesso_funcionarios:
                    raise RuntimeError(
                        f"❌ Não foi possível alocar os funcionários necessários "
                        f"para a atividade {self.id_atividade}"
                    )

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

    def _tentar_alocacao_no_horario(self, horario_final: datetime):
        """Tenta alocar todos os equipamentos necessários em um horário específico"""
        equipamentos_alocados = []
        horario_fim_etapa = horario_final

        try:
            for tipo_eqp, qtd in reversed(list(self._quantidade_por_tipo_equipamento.items())):
                logger.debug(f"🔧 Tentando alocar {tipo_eqp.name} para {horario_fim_etapa.strftime('%H:%M')}")
                
                resultado_alocacao = self._alocar_tipo_equipamento(tipo_eqp, horario_fim_etapa)
                
                if not resultado_alocacao[0] or resultado_alocacao[1] is None:
                    logger.debug(f"❌ Falha na alocação de {tipo_eqp.name}")
                    return False, equipamentos_alocados
                
                equipamentos_alocados.append(resultado_alocacao)
                horario_fim_etapa = resultado_alocacao[2]  # Usar início desta etapa como fim da próxima

            # Verificar sequenciamento
            if not self._verificar_sequenciamento(equipamentos_alocados):
                logger.debug("❌ Falha no sequenciamento dos equipamentos")
                return False, equipamentos_alocados

            logger.debug("✅ Todos os equipamentos alocados com sucesso")
            return True, equipamentos_alocados
            
        except Exception as e:
            logger.error(f"❌ Erro durante tentativa de alocação: {e}")
            return False, equipamentos_alocados

    def _alocar_tipo_equipamento(self, tipo_eqp: TipoEquipamento, horario_fim_etapa: datetime):
        """Aloca um tipo específico de equipamento com tratamento robusto de erros"""
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
            
        except Exception as e:
            logger.error(f"❌ Erro ao alocar {tipo_eqp.name}: {e}")
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
        """Verifica se os equipamentos estão sequenciados corretamente com logs detalhados"""
        try:
            if len(equipamentos_alocados) <= 1:
                return True
            
            equipamentos_ordenados = sorted(equipamentos_alocados, key=lambda x: x[2])
            
            for i in range(1, len(equipamentos_ordenados)):
                fim_anterior = equipamentos_ordenados[i - 1][3]
                inicio_atual = equipamentos_ordenados[i][2]

                if fim_anterior != inicio_atual:
                    gap = abs((fim_anterior - inicio_atual).total_seconds())
                    
                    logger.warning(
                        f"🔁 Equipamentos da atividade {self.id_atividade} não estão sequenciados. "
                        f"Gap de {gap}s entre '{equipamentos_ordenados[i - 1][1].nome}' "
                        f"({fim_anterior.strftime('%H:%M:%S')}) e "
                        f"'{equipamentos_ordenados[i][1].nome}' ({inicio_atual.strftime('%H:%M:%S')})"
                    )
                    return False
            
            logger.debug("✅ Sequenciamento dos equipamentos validado")
            return True
            
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

            if FUNCIONARIOS_ATIVOS:
                sucesso_funcionarios = self._alocar_funcionarios(inicio_atividade, fim_atividade)
                if not sucesso_funcionarios:
                    raise RuntimeError(
                        f"❌ Não foi possível alocar os funcionários necessários "
                        f"para a atividade {self.id_atividade}"
                    )

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
        return gestor.alocar(inicio, fim, self, self.quantidade)
    
    def _alocar_bancada(self, gestor, inicio, fim, **kwargs): 
        return gestor.alocar(inicio, fim, self)
    
    def _alocar_fogao(self, gestor, inicio, fim, **kwargs): 
        return gestor.alocar(inicio, fim, self, self.quantidade)
    
    def _alocar_batedeira(self, gestor, inicio, fim, **kwargs): 
        return gestor.alocar(inicio, fim, self, self.quantidade)
    
    def _alocar_balanca(self, gestor, inicio, fim, **kwargs): 
        return gestor.alocar(inicio, fim, self, self.quantidade)
    
    def _alocar_forno(self, gestor, inicio, fim, **kwargs): 
        return gestor.alocar(inicio, fim, self, self.quantidade)
    
    def _alocar_misturadora(self, gestor, inicio, fim, **kwargs): 
        return gestor.alocar(inicio, fim, self, self.quantidade)
    
    def _alocar_misturadora_com_coccao(self, gestor, inicio, fim, **kwargs): 
        return gestor.alocar(inicio, fim, self, self.quantidade)
    
    def _alocar_armario_fermentacao(self, gestor, inicio, fim, **kwargs): 
        return gestor.alocar(inicio, fim, self, self.quantidade)
    
    def _alocar_modeladora(self, gestor, inicio, fim, **kwargs): 
        return gestor.alocar(inicio, fim, self, self.quantidade)
    
    def _alocar_divisora_boleadora(self, gestor, inicio, fim, **kwargs): 
        return gestor.alocar(inicio, fim, self, self.quantidade)
    
    def _alocar_embaladora(self, gestor, inicio, fim, **kwargs): 
        return gestor.alocar(inicio, fim, self, self.quantidade)

    # =============================================================================
    #                     VERIFICAÇÃO DE TEMPO MÁXIMO DE ESPERA - CORRIGIDA
    # =============================================================================

    def _verificar_tempo_maximo_espera(
        self, 
        atividade_atual: "AtividadeModular", 
        atividade_sucessora: "AtividadeModular",
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
                f"   Atraso detectado: {atraso}\n"
                f"   Máximo permitido: {tempo_max_espera}\n"
                f"   Excesso: {atraso - tempo_max_espera}"
            )
        else:
            logger.debug(f"✅ Tempo de espera dentro do limite permitido")

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