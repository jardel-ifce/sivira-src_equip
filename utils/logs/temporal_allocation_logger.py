# utils/logs/temporal_allocation_logger.py
"""
Sistema unificado de logs para erros temporais e de alocação.
Combina funcionalidades de timing_logger e deadline_allocation_logger.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from utils.logs.logger_factory import setup_logger

logger = setup_logger('TemporalAllocationLogger')


class TemporalAllocationLogger:
    """
    Logger unificado para todos os tipos de erros temporais:
    - Erros de timing entre atividades (inter-activity)
    - Erros de timing dentro de atividades (intra-activity)
    - Erros de alocação por prazo (deadline allocation)
    - Análise de disponibilidade e horários ideais
    """
    
    def __init__(self, base_dir: str = "logs/erros"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        # Inicializar analisador de conflitos
        try:
            from utils.logs.equipment_conflict_analyzer import EquipmentConflictAnalyzer
            self.conflict_analyzer = EquipmentConflictAnalyzer()
        except ImportError:
            logger.warning("EquipmentConflictAnalyzer não disponível")
            self.conflict_analyzer = None
    
    # ========================================================================
    #                    ERRO DE ALOCAÇÃO POR PRAZO
    # ========================================================================
    
    def log_deadline_allocation_error(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        nome_atividade: str,
        tipo_equipamento: str,
        quantidade_necessaria: int,
        prazo_final: datetime,
        duracao_atividade: timedelta,
        janela_disponivel: Tuple[datetime, datetime],
        motivo_falha: str,
        tempo_maximo_espera: Optional[timedelta] = None,
        proximo_horario_livre: Optional[datetime] = None,
        equipamentos_tentados: Optional[List[str]] = None,
        contexto_adicional: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Registra erro de alocação por prazo com análise completa de disponibilidade.
        
        Args:
            id_ordem: ID da ordem de produção
            id_pedido: ID do pedido
            id_atividade: ID da atividade que falhou
            nome_atividade: Nome descritivo da atividade
            tipo_equipamento: Tipo de equipamento necessário
            quantidade_necessaria: Quantidade a ser processada
            prazo_final: Deadline para conclusão da atividade
            duracao_atividade: Duração estimada da atividade
            janela_disponivel: Tupla (início, fim) da janela temporal disponível
            motivo_falha: Descrição do motivo da falha
            tempo_maximo_espera: Tempo máximo que pode esperar após o prazo
            proximo_horario_livre: Próximo horário em que o equipamento estará livre
            equipamentos_tentados: Lista de equipamentos que foram tentados
            contexto_adicional: Informações extras relevantes
            
        Returns:
            Caminho do arquivo de log criado
        """
        timestamp = datetime.now()
        
        # Adicionar tempo_maximo_espera e proximo_horario_livre ao contexto
        if contexto_adicional is None:
            contexto_adicional = {}
        
        if tempo_maximo_espera is not None:
            contexto_adicional['tempo_maximo_espera'] = tempo_maximo_espera
            
        if proximo_horario_livre is not None:
            contexto_adicional['proximo_horario_livre'] = proximo_horario_livre
        
        # Gerar log no formato limpo
        log_formatado = self._formatar_deadline_error(
            timestamp=timestamp,
            id_ordem=id_ordem,
            id_pedido=id_pedido,
            id_atividade=id_atividade,
            nome_atividade=nome_atividade,
            tipo_equipamento=tipo_equipamento,
            quantidade_necessaria=quantidade_necessaria,
            prazo_final=prazo_final,
            duracao_atividade=duracao_atividade,
            janela_disponivel=janela_disponivel,
            motivo_falha=motivo_falha,
            equipamentos_tentados=equipamentos_tentados,
            contexto_adicional=contexto_adicional
        )
        
        # Salvar arquivo de log
        return self._salvar_log(id_ordem, id_pedido, log_formatado, "DEADLINE_ALLOCATION", {
            "timestamp": timestamp.isoformat(),
            "id_atividade": id_atividade,
            "nome_atividade": nome_atividade,
            "tipo_equipamento": tipo_equipamento,
            "quantidade_necessaria": quantidade_necessaria,
            "prazo_final": prazo_final.isoformat(),
            "duracao_atividade": str(duracao_atividade),
            "janela_disponivel": {
                "inicio": janela_disponivel[0].isoformat(),
                "fim": janela_disponivel[1].isoformat()
            },
            "motivo_falha": motivo_falha,
            "tempo_maximo_espera": str(tempo_maximo_espera) if tempo_maximo_espera else None,
            "proximo_horario_livre": proximo_horario_livre.isoformat() if proximo_horario_livre else None,
            "equipamentos_tentados": equipamentos_tentados or [],
            "contexto_adicional": contexto_adicional
        })
    
    # ========================================================================
    #                    ERRO DE TIMING ENTRE ATIVIDADES
    # ========================================================================
    
    def log_inter_activity_timing_error(
        self,
        id_ordem: int,
        id_pedido: int,
        current_activity_id: int,
        current_activity_name: str,
        successor_activity_id: int,
        successor_activity_name: str,
        current_end_time: datetime,
        successor_start_time: datetime,
        maximum_wait_time: timedelta,
        current_activity_obj=None,
        successor_activity_obj=None
    ) -> str:
        """
        Registra erro de timing ENTRE atividades.
        
        Args:
            id_ordem: ID da ordem de produção
            id_pedido: ID do pedido
            current_activity_id: ID da atividade atual
            current_activity_name: Nome da atividade atual
            successor_activity_id: ID da atividade sucessora
            successor_activity_name: Nome da atividade sucessora
            current_end_time: Horário de término da atividade atual
            successor_start_time: Horário de início da atividade sucessora
            maximum_wait_time: Tempo máximo de espera permitido
            current_activity_obj: Objeto da atividade atual (opcional)
            successor_activity_obj: Objeto da atividade sucessora (opcional)
            
        Returns:
            Caminho do arquivo de log criado
        """
        timestamp = datetime.now()
        atraso = successor_start_time - current_end_time
        
        # Gerar log formatado
        log_formatado = self._formatar_inter_activity_error(
            timestamp=timestamp,
            id_ordem=id_ordem,
            id_pedido=id_pedido,
            current_activity_id=current_activity_id,
            current_activity_name=current_activity_name,
            successor_activity_id=successor_activity_id,
            successor_activity_name=successor_activity_name,
            current_end_time=current_end_time,
            successor_start_time=successor_start_time,
            maximum_wait_time=maximum_wait_time,
            actual_delay=atraso,
            current_activity_obj=current_activity_obj,
            successor_activity_obj=successor_activity_obj
        )
        
        # Preparar contexto adicional com análise de conflitos
        contexto_adicional = {
            "timestamp": timestamp.isoformat(),
            "current_activity": {
                "id": current_activity_id,
                "name": current_activity_name,
                "end_time": current_end_time.isoformat()
            },
            "successor_activity": {
                "id": successor_activity_id,
                "name": successor_activity_name,
                "start_time": successor_start_time.isoformat()
            },
            "timing_violation": {
                "maximum_wait_time": str(maximum_wait_time),
                "actual_delay": str(atraso),
                "excess": str(atraso - maximum_wait_time)
            }
        }

        # Análise de conflitos para INTER_ACTIVITY_TIMING
        try:
            if hasattr(self, 'conflict_analyzer') and self.conflict_analyzer:
                # Extrair equipamentos envolvidos
                equipamentos_necessarios = []

                # Equipamento da atividade atual
                if current_activity_obj and hasattr(current_activity_obj, 'equipamento_alocado'):
                    equipamento_atual = current_activity_obj.equipamento_alocado
                    if equipamento_atual:
                        if isinstance(equipamento_atual, list):
                            equipamentos_necessarios.extend([eq.nome for eq in equipamento_atual if hasattr(eq, 'nome')])
                        else:
                            if hasattr(equipamento_atual, 'nome'):
                                equipamentos_necessarios.append(equipamento_atual.nome)

                # Equipamento da atividade sucessora
                if successor_activity_obj and hasattr(successor_activity_obj, 'equipamento_alocado'):
                    equipamento_sucessor = successor_activity_obj.equipamento_alocado
                    if equipamento_sucessor:
                        if isinstance(equipamento_sucessor, list):
                            equipamentos_necessarios.extend([eq.nome for eq in equipamento_sucessor if hasattr(eq, 'nome')])
                        else:
                            if hasattr(equipamento_sucessor, 'nome'):
                                equipamentos_necessarios.append(equipamento_sucessor.nome)

                # Analisar conflitos no período entre atividades
                if equipamentos_necessarios:
                    relatorio_conflito = self.conflict_analyzer.analisar_conflitos_equipamentos(
                        equipamentos_necessarios,
                        current_end_time,  # período início
                        successor_start_time,  # período fim
                        duracao_atividade=atraso
                    )

                    if relatorio_conflito:
                        contexto_adicional['relatorio_conflito_detalhado'] = relatorio_conflito
                        contexto_adicional['equipamentos_envolvidos'] = equipamentos_necessarios

        except Exception as e:
            # Se houver erro na análise, não interromper o processo
            pass

        # Salvar arquivo de log
        return self._salvar_log(id_ordem, id_pedido, log_formatado, "INTER_ACTIVITY_TIMING", contexto_adicional)
    
    # ========================================================================
    #                    ERRO DE TIMING INTRA-ATIVIDADE
    # ========================================================================
    
    def log_intra_activity_timing_error(
        self,
        id_ordem: int,
        id_pedido: int,
        activity_id: int,
        activity_name: str,
        current_equipment: str,
        successor_equipment: str,
        current_end_time: datetime,
        successor_start_time: datetime,
        maximum_wait_time: timedelta
    ) -> str:
        """
        Registra erro de timing DENTRO de uma atividade (entre equipamentos).
        
        Args:
            id_ordem: ID da ordem de produção
            id_pedido: ID do pedido
            activity_id: ID da atividade
            activity_name: Nome da atividade
            current_equipment: Equipamento atual
            successor_equipment: Equipamento sucessor
            current_end_time: Fim do equipamento atual
            successor_start_time: Início do equipamento sucessor
            maximum_wait_time: Tempo máximo de espera permitido
            
        Returns:
            Caminho do arquivo de log criado
        """
        timestamp = datetime.now()
        atraso = successor_start_time - current_end_time
        
        # Gerar log formatado
        log_formatado = self._formatar_intra_activity_error(
            timestamp=timestamp,
            id_ordem=id_ordem,
            id_pedido=id_pedido,
            activity_id=activity_id,
            activity_name=activity_name,
            current_equipment=current_equipment,
            successor_equipment=successor_equipment,
            current_end_time=current_end_time,
            successor_start_time=successor_start_time,
            maximum_wait_time=maximum_wait_time,
            actual_delay=atraso
        )
        
        # Salvar arquivo de log
        return self._salvar_log(id_ordem, id_pedido, log_formatado, "INTRA_ACTIVITY_TIMING", {
            "timestamp": timestamp.isoformat(),
            "activity": {
                "id": activity_id,
                "name": activity_name
            },
            "equipment_transition": {
                "current": {
                    "name": current_equipment,
                    "end_time": current_end_time.isoformat()
                },
                "successor": {
                    "name": successor_equipment,
                    "start_time": successor_start_time.isoformat()
                }
            },
            "timing_violation": {
                "maximum_wait_time": str(maximum_wait_time),
                "actual_delay": str(atraso),
                "excess": str(atraso - maximum_wait_time)
            }
        })
    
    # ========================================================================
    #                         MÉTODOS DE FORMATAÇÃO
    # ========================================================================
    
    def _formatar_deadline_error(
        self,
        timestamp: datetime,
        id_ordem: int,
        id_pedido: int,
        id_atividade: int,
        nome_atividade: str,
        tipo_equipamento: str,
        quantidade_necessaria: int,
        prazo_final: datetime,
        duracao_atividade: timedelta,
        janela_disponivel: Tuple[datetime, datetime],
        motivo_falha: str,
        equipamentos_tentados: Optional[List[str]] = None,
        contexto_adicional: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Formata erro de deadline no padrão limpo com análise completa.
        """
        log = "=" * 50 + "\n"
        log += f"📅 Data/Hora: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        log += f"🧾 Ordem: {id_ordem} | Pedido: {id_pedido}\n"
        log += f"🚫 Tipo de Erro: ALOCAÇÃO POR PRAZO\n"
        log += "-" * 50 + "\n\n"
        
        # Título do erro
        log += f"❌ FALHA NA ALOCAÇÃO - PRAZO EXPIRADO\n\n"
        
        # Informações da atividade
        log += "📋 ATIVIDADE:\n"
        log += f"   • ID: {id_atividade}\n"
        log += f"   • Nome: {nome_atividade}\n"
        log += f"   • Tipo de Equipamento: {tipo_equipamento}\n"
        log += f"   • Quantidade: {quantidade_necessaria} unidades\n"
        log += f"   • Duração Necessária: {self._formatar_duracao(duracao_atividade)}\n\n"
        
        # Informações temporais
        log += "⏰ RESTRIÇÕES TEMPORAIS:\n"
        log += f"   • Prazo Final: {prazo_final.strftime('%d/%m/%Y %H:%M')}\n"
        log += f"   • Janela Disponível: {janela_disponivel[0].strftime('%d/%m %H:%M')} → {janela_disponivel[1].strftime('%d/%m %H:%M')}\n"
        janela_total = janela_disponivel[1] - janela_disponivel[0]
        log += f"   • Tempo Total Disponível: {self._formatar_duracao(janela_total)}\n"
        
        # Tempo máximo de espera
        if contexto_adicional and 'tempo_maximo_espera' in contexto_adicional:
            tempo_max = contexto_adicional['tempo_maximo_espera']
            if isinstance(tempo_max, timedelta) and tempo_max > timedelta(0):
                horario_mais_cedo = prazo_final - tempo_max
                horario_mais_tarde = prazo_final + tempo_max
                log += f"\n   • ⏳ Tempo Máximo de Espera: {self._formatar_duracao(tempo_max)}\n"
                log += f"   • Janela Flexível: {horario_mais_cedo.strftime('%H:%M')} → {horario_mais_tarde.strftime('%H:%M')}\n"
            else:
                log += f"\n   • ⚠️ Sem flexibilidade: deve terminar EXATAMENTE às {prazo_final.strftime('%H:%M')}\n"
        
        log += "\n"
        
        # Motivo da falha
        log += "🔍 MOTIVO DA FALHA:\n"
        log += f"   {motivo_falha}\n\n"
        
        # Equipamentos tentados
        if equipamentos_tentados:
            log += "🏭 EQUIPAMENTOS TENTADOS:\n"
            for equipamento in equipamentos_tentados:
                log += f"   • {equipamento}\n"
            log += "\n"
        
        # Análise completa
        log += "📊 ANÁLISE DETALHADA:\n"
        
        # Análise de bateladas
        if contexto_adicional and 'bateladas_necessarias' in contexto_adicional:
            bateladas = contexto_adicional['bateladas_necessarias']
            tempo_por_batelada = contexto_adicional.get('tempo_por_batelada', timedelta(minutes=16))
            tempo_total_bateladas = tempo_por_batelada * bateladas
            
            log += f"\n   📦 BATELADAS:\n"
            log += f"   • Bateladas necessárias: {bateladas}\n"
            log += f"   • Tempo por batelada: {self._formatar_duracao(tempo_por_batelada)}\n"
            log += f"   • Tempo total real necessário: {self._formatar_duracao(tempo_total_bateladas)}\n"
            
            if tempo_total_bateladas > duracao_atividade:
                excesso = tempo_total_bateladas - duracao_atividade
                log += f"   • ⚠️ Tempo real excede estimativa em: {self._formatar_duracao(excesso)}\n"
        
        # Análise de disponibilidade do equipamento
        if contexto_adicional and 'proximo_horario_livre' in contexto_adicional:
            horario_livre = contexto_adicional['proximo_horario_livre']
            if isinstance(horario_livre, str):
                horario_livre = datetime.fromisoformat(horario_livre)
            
            # Calcular quando terminaria se começasse no horário livre
            tempo_real = duracao_atividade
            if contexto_adicional and 'bateladas_necessarias' in contexto_adicional:
                tempo_por_batelada = contexto_adicional.get('tempo_por_batelada', timedelta(minutes=16))
                tempo_real = tempo_por_batelada * contexto_adicional['bateladas_necessarias']
            
            inicio_possivel = horario_livre
            fim_possivel = inicio_possivel + tempo_real
            
            log += f"\n   🏭 DISPONIBILIDADE DO EQUIPAMENTO:\n"
            log += f"   • Equipamento livre a partir de: {horario_livre.strftime('%d/%m %H:%M')}\n"
            log += f"   • Se iniciasse neste horário: {inicio_possivel.strftime('%H:%M')} → {fim_possivel.strftime('%H:%M')}\n"
            
            if fim_possivel > prazo_final:
                atraso_previsto = fim_possivel - prazo_final
                log += f"   • ❌ Resultaria em atraso de: {self._formatar_duracao(atraso_previsto)}\n"
                
                # Verificar se o tempo de espera permitiria
                if contexto_adicional and 'tempo_maximo_espera' in contexto_adicional:
                    tempo_max = contexto_adicional['tempo_maximo_espera']
                    if isinstance(tempo_max, timedelta) and atraso_previsto <= tempo_max:
                        log += f"   • ✅ Mas estaria dentro do tempo de espera permitido ({self._formatar_duracao(tempo_max)})\n"
            else:
                folga = prazo_final - fim_possivel
                log += f"   • ✅ Atenderia o prazo com {self._formatar_duracao(folga)} de folga\n"
        
        # Cenários de execução ideal
        log += "\n   📅 CENÁRIOS DE EXECUÇÃO IDEAL:\n"
        
        # Calcular tempo real necessário
        tempo_real = duracao_atividade
        if contexto_adicional and 'bateladas_necessarias' in contexto_adicional:
            tempo_por_batelada = contexto_adicional.get('tempo_por_batelada', timedelta(minutes=16))
            tempo_real = tempo_por_batelada * contexto_adicional['bateladas_necessarias']
        
        # Cenário 1: Para terminar exatamente no prazo
        inicio_ideal = prazo_final - tempo_real
        log += f"\n   1️⃣ Para terminar no prazo ({prazo_final.strftime('%H:%M')}):\n"
        log += f"      • Deveria iniciar às: {inicio_ideal.strftime('%d/%m %H:%M')}\n"
        log += f"      • Duração: {self._formatar_duracao(tempo_real)}\n"
        log += f"      • Término: {prazo_final.strftime('%d/%m %H:%M')}\n"
        
        # Cenário 2: Com tempo máximo de espera
        if contexto_adicional and 'tempo_maximo_espera' in contexto_adicional:
            tempo_max = contexto_adicional['tempo_maximo_espera']
            if isinstance(tempo_max, timedelta) and tempo_max > timedelta(0):
                # Pode começar mais cedo e terminar mais tarde
                inicio_mais_cedo = prazo_final - tempo_max - tempo_real
                fim_mais_tarde = prazo_final + tempo_max
                
                log += f"\n   2️⃣ Com flexibilidade de {self._formatar_duracao(tempo_max)}:\n"
                log += f"      • Poderia iniciar entre: {inicio_mais_cedo.strftime('%H:%M')} e {inicio_ideal.strftime('%H:%M')}\n"
                log += f"      • Poderia terminar entre: {prazo_final.strftime('%H:%M')} e {fim_mais_tarde.strftime('%H:%M')}\n"
                log += f"      • Janela total ampliada: {self._formatar_duracao(tempo_max * 2 + tempo_real)}\n"
        
        # Cenário 3: Horário necessário para não ter atraso
        if contexto_adicional and 'proximo_horario_livre' in contexto_adicional:
            horario_livre = contexto_adicional['proximo_horario_livre']
            if isinstance(horario_livre, str):
                horario_livre = datetime.fromisoformat(horario_livre)
            
            if horario_livre > inicio_ideal:
                antecipacao_necessaria = horario_livre - inicio_ideal
                log += f"\n   3️⃣ Para usar o equipamento quando livre:\n"
                log += f"      • Equipamento livre às: {horario_livre.strftime('%H:%M')}\n"
                log += f"      • Precisaria antecipar prazo em: {self._formatar_duracao(antecipacao_necessaria)}\n"
                log += f"      • Novo prazo seria: {(prazo_final + antecipacao_necessaria).strftime('%d/%m %H:%M')}\n"

        log += "\n"

        # 🔍 NOVA SEÇÃO: Análise detalhada de conflitos de equipamentos
        if contexto_adicional and 'relatorio_conflito_detalhado' in contexto_adicional:
            log += "🚨 ANÁLISE DE CONFLITOS DE EQUIPAMENTOS:\n"
            log += "-" * 50 + "\n"
            relatorio_conflito = contexto_adicional['relatorio_conflito_detalhado']
            # Indentar o relatório para melhor visualização
            linhas_relatorio = relatorio_conflito.split('\n')
            for linha in linhas_relatorio:
                if linha.strip():  # Ignorar linhas vazias
                    log += f"   {linha}\n"
                else:
                    log += "\n"
            log += "-" * 50 + "\n\n"

        # Sugestões
        log += "💡 SUGESTÕES:\n"
        sugestoes = self._gerar_sugestoes_deadline(
            quantidade_necessaria=quantidade_necessaria,
            duracao_atividade=duracao_atividade,
            tempo_real=tempo_real,
            janela_disponivel=janela_disponivel,
            prazo_final=prazo_final,
            contexto_adicional=contexto_adicional
        )
        for sugestao in sugestoes:
            log += f"   • {sugestao}\n"
        
        log += "\n" + "=" * 50
        
        return log
    
    def _formatar_inter_activity_error(
        self,
        timestamp: datetime,
        id_ordem: int,
        id_pedido: int,
        current_activity_id: int,
        current_activity_name: str,
        successor_activity_id: int,
        successor_activity_name: str,
        current_end_time: datetime,
        successor_start_time: datetime,
        maximum_wait_time: timedelta,
        actual_delay: timedelta,
        current_activity_obj=None,
        successor_activity_obj=None
    ) -> str:
        """
        Formata erro de timing entre atividades no padrão limpo.
        """
        log = "=" * 50 + "\n"
        log += f"📅 Data/Hora: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        log += f"🧾 Ordem: {id_ordem} | Pedido: {id_pedido}\n"
        log += f"⏱️ Tipo de Erro: TEMPO ENTRE ATIVIDADES\n"
        log += "-" * 50 + "\n\n"
        
        log += f"❌ TEMPO MÁXIMO DE ESPERA EXCEDIDO ENTRE ATIVIDADES\n\n"
        
        # Atividades envolvidas
        log += "📋 ATIVIDADES ENVOLVIDAS:\n"
        log += f"   Atividade Atual:\n"
        log += f"   • ID: {current_activity_id}\n"
        log += f"   • Nome: {current_activity_name}\n"
        log += f"   • Término: {current_end_time.strftime('%d/%m %H:%M:%S')}\n"
        log += f"\n"
        log += f"   Atividade Sucessora:\n"
        log += f"   • ID: {successor_activity_id}\n"
        log += f"   • Nome: {successor_activity_name}\n"
        log += f"   • Início: {successor_start_time.strftime('%d/%m %H:%M:%S')}\n\n"
        
        # Violação de tempo
        log += "⏰ VIOLAÇÃO DE TEMPO:\n"
        log += f"   • Tempo máximo permitido: {self._formatar_duracao(maximum_wait_time)}\n"
        log += f"   • Atraso real: {self._formatar_duracao(actual_delay)}\n"
        log += f"   • Excesso: {self._formatar_duracao(actual_delay - maximum_wait_time)}\n\n"
        
        # Equipamentos envolvidos (se disponível)
        if current_activity_obj or successor_activity_obj:
            log += "🏭 EQUIPAMENTOS:\n"
            if current_activity_obj and hasattr(current_activity_obj, 'equipamento_alocado'):
                equipamento_atual = current_activity_obj.equipamento_alocado
                if equipamento_atual:
                    if isinstance(equipamento_atual, list):
                        nomes = [eq.nome for eq in equipamento_atual if hasattr(eq, 'nome')]
                        nome_str = ', '.join(nomes) if nomes else 'N/A'
                    else:
                        nome_str = equipamento_atual.nome if hasattr(equipamento_atual, 'nome') else 'N/A'
                    log += f"   • Atividade atual: {nome_str}\n"
                else:
                    log += f"   • Atividade atual: N/A\n"
            if successor_activity_obj and hasattr(successor_activity_obj, 'equipamento_alocado'):
                equipamento_sucessor = successor_activity_obj.equipamento_alocado
                if equipamento_sucessor:
                    if isinstance(equipamento_sucessor, list):
                        nomes = [eq.nome for eq in equipamento_sucessor if hasattr(eq, 'nome')]
                        nome_str = ', '.join(nomes) if nomes else 'N/A'
                    else:
                        nome_str = equipamento_sucessor.nome if hasattr(equipamento_sucessor, 'nome') else 'N/A'
                    log += f"   • Atividade sucessora: {nome_str}\n"
                else:
                    log += f"   • Atividade sucessora: N/A\n"
            log += "\n"
        
        # 🚨 NOVA SEÇÃO: Análise detalhada de conflitos de equipamentos para INTER_ACTIVITY_TIMING
        try:
            if hasattr(self, 'conflict_analyzer') and self.conflict_analyzer:
                # Extrair informações dos equipamentos para análise
                equipamentos_necessarios = []

                # Equipamento da atividade atual
                if current_activity_obj and hasattr(current_activity_obj, 'equipamento_alocado'):
                    equipamento_atual = current_activity_obj.equipamento_alocado
                    if equipamento_atual:
                        if isinstance(equipamento_atual, list):
                            equipamentos_necessarios.extend([eq.nome for eq in equipamento_atual if hasattr(eq, 'nome')])
                        else:
                            if hasattr(equipamento_atual, 'nome'):
                                equipamentos_necessarios.append(equipamento_atual.nome)

                # Equipamento da atividade sucessora
                if successor_activity_obj and hasattr(successor_activity_obj, 'equipamento_alocado'):
                    equipamento_sucessor = successor_activity_obj.equipamento_alocado
                    if equipamento_sucessor:
                        if isinstance(equipamento_sucessor, list):
                            equipamentos_necessarios.extend([eq.nome for eq in equipamento_sucessor if hasattr(eq, 'nome')])
                        else:
                            if hasattr(equipamento_sucessor, 'nome'):
                                equipamentos_necessarios.append(equipamento_sucessor.nome)

                # Analisar conflitos no período entre as atividades
                if equipamentos_necessarios:
                    periodo_inicio = current_end_time
                    periodo_fim = successor_start_time

                    relatorio_conflito = self.conflict_analyzer.analisar_conflitos_equipamentos(
                        equipamentos_necessarios,
                        periodo_inicio,
                        periodo_fim,
                        duracao_atividade=actual_delay
                    )

                    if relatorio_conflito and relatorio_conflito.get('conflitos_detectados'):
                        log += "\n🚨 ANÁLISE DE CONFLITOS DE EQUIPAMENTOS:\n"
                        log += "-" * 50 + "\n"

                        log += "🔧 EQUIPAMENTOS AFETADOS:\n"
                        log += f"   • Equipamentos envolvidos: {', '.join(equipamentos_necessarios)}\n\n"

                        log += "⏱️ PERÍODO DE CONFLITO:\n"
                        log += f"   • Início do intervalo: {periodo_inicio.strftime('%d/%m %H:%M')}\n"
                        log += f"   • Fim do intervalo: {periodo_fim.strftime('%d/%m %H:%M')}\n"
                        log += f"   • Duração total: {self._formatar_duracao(actual_delay)}\n\n"

                        log += "❌ CONFLITOS DETECTADOS:\n"
                        for conflito in relatorio_conflito['conflitos_detectados']:
                            equipamento = conflito.get('equipamento', 'N/A')
                            log += f"\n   🏭 {equipamento.upper()}:\n"

                            ocupacoes = conflito.get('ocupacoes_impeditivas', [])
                            for ocupacao in ocupacoes:
                                inicio = ocupacao.get('inicio', 'N/A')
                                fim = ocupacao.get('fim', 'N/A')
                                atividade = ocupacao.get('atividade', 'N/A')
                                pedido = ocupacao.get('pedido', 'N/A')

                                log += f"      ❌ Ocupado: {inicio} → {fim}\n"
                                log += f"      📋 Atividade: {atividade}\n"
                                log += f"      🧾 Pedido: {pedido}\n"

                        # Alternativas temporais
                        alternativas = relatorio_conflito.get('alternativas_temporais', [])
                        if alternativas:
                            log += "\n⚡ ALTERNATIVAS TEMPORAIS:\n"
                            for i, alternativa in enumerate(alternativas[:3], 1):  # Máximo 3 alternativas
                                janela = alternativa.get('janela_livre', {})
                                equipamentos_disp = alternativa.get('equipamentos_disponiveis', [])

                                inicio_alt = janela.get('inicio', 'N/A')
                                fim_alt = janela.get('fim', 'N/A')

                                log += f"\n   🕐 Janela Livre {i}:\n"
                                log += f"      • Período: {inicio_alt} → {fim_alt}\n"
                                log += f"      • Equipamentos Disponíveis: {', '.join(equipamentos_disp)}\n"
                                log += f"      • Status: ✅ Viável\n"

                        log += "\n"
        except Exception as e:
            # Se houver erro na análise de conflitos, não interromper o log
            pass

        # Sugestões
        log += "💡 SUGESTÕES:\n"
        log += f"   • Reduzir tempo de processamento das atividades\n"
        log += f"   • Alocar equipamentos mais próximos\n"
        log += f"   • Revisar tempo máximo de espera (atual: {self._formatar_duracao(maximum_wait_time)})\n"
        log += f"   • Considerar equipamentos alternativos se disponíveis\n"
        log += f"   • Analisar sequenciamento de atividades para reduzir gaps\n"

        log += "\n" + "=" * 50

        return log
    
    def _formatar_intra_activity_error(
        self,
        timestamp: datetime,
        id_ordem: int,
        id_pedido: int,
        activity_id: int,
        activity_name: str,
        current_equipment: str,
        successor_equipment: str,
        current_end_time: datetime,
        successor_start_time: datetime,
        maximum_wait_time: timedelta,
        actual_delay: timedelta
    ) -> str:
        """
        Formata erro de timing intra-atividade no padrão limpo.
        """
        log = "=" * 50 + "\n"
        log += f"📅 Data/Hora: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
        log += f"🧾 Ordem: {id_ordem} | Pedido: {id_pedido}\n"
        log += f"⏱️ Tipo de Erro: TEMPO DENTRO DA ATIVIDADE\n"
        log += "-" * 50 + "\n\n"
        
        log += f"❌ TEMPO MÁXIMO EXCEDIDO ENTRE EQUIPAMENTOS\n\n"
        
        # Atividade
        log += "📋 ATIVIDADE:\n"
        log += f"   • ID: {activity_id}\n"
        log += f"   • Nome: {activity_name}\n\n"
        
        # Transição de equipamentos
        log += "🏭 TRANSIÇÃO DE EQUIPAMENTOS:\n"
        log += f"   De: {current_equipment}\n"
        log += f"   • Término: {current_end_time.strftime('%d/%m %H:%M:%S')}\n"
        log += f"\n"
        log += f"   Para: {successor_equipment}\n"
        log += f"   • Início: {successor_start_time.strftime('%d/%m %H:%M:%S')}\n\n"
        
        # Violação de tempo
        log += "⏰ VIOLAÇÃO DE TEMPO:\n"
        log += f"   • Tempo máximo permitido: {self._formatar_duracao(maximum_wait_time)}\n"
        log += f"   • Atraso real: {self._formatar_duracao(actual_delay)}\n"
        log += f"   • Excesso: {self._formatar_duracao(actual_delay - maximum_wait_time)}\n\n"
        
        # Sugestões
        log += "💡 SUGESTÕES:\n"
        log += f"   • Verificar sequenciamento dos equipamentos\n"
        log += f"   • Otimizar layout para reduzir tempo de transição\n"
        log += f"   • Considerar processamento em lote único\n"
        
        log += "\n" + "=" * 50
        
        return log
    
    # ========================================================================
    #                         MÉTODOS AUXILIARES
    # ========================================================================
    
    def _formatar_duracao(self, duracao: timedelta) -> str:
        """
        Formata duração de forma legível.
        """
        if duracao < timedelta(0):
            negativo = True
            duracao = abs(duracao)
        else:
            negativo = False
            
        total_segundos = int(duracao.total_seconds())
        dias = total_segundos // 86400
        horas = (total_segundos % 86400) // 3600
        minutos = (total_segundos % 3600) // 60
        segundos = total_segundos % 60
        
        partes = []
        if dias > 0:
            partes.append(f"{dias}d")
        if horas > 0:
            partes.append(f"{horas}h")
        if minutos > 0:
            partes.append(f"{minutos}min")
        elif not partes:  # Se não tem dias nem horas, mostrar minutos mesmo se for 0
            partes.append("0min")
            
        resultado = " ".join(partes)
        return f"-{resultado}" if negativo else resultado
    
    def _gerar_sugestoes_deadline(
        self,
        quantidade_necessaria: int,
        duracao_atividade: timedelta,
        tempo_real: timedelta,
        janela_disponivel: Tuple[datetime, datetime],
        prazo_final: datetime,
        contexto_adicional: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Gera sugestões específicas para erros de deadline.
        """
        sugestoes = []
        
        # Sugestão baseada em tempo real vs estimado
        if tempo_real > duracao_atividade:
            diferenca = tempo_real - duracao_atividade
            sugestoes.append(f"Ajustar estimativa de duração (real: {self._formatar_duracao(tempo_real)}, estimado: {self._formatar_duracao(duracao_atividade)})")
        
        # Sugestão baseada em bateladas
        if contexto_adicional and 'bateladas_necessarias' in contexto_adicional:
            bateladas = contexto_adicional['bateladas_necessarias']
            if bateladas > 2:
                sugestoes.append(f"Reduzir quantidade para processar em menos bateladas (atual: {bateladas})")
                sugestoes.append("Considerar uso de múltiplos equipamentos em paralelo")
        
        # Sugestão de antecipação
        inicio_ideal = prazo_final - tempo_real
        if inicio_ideal < janela_disponivel[0]:
            antecipacao = janela_disponivel[0] - inicio_ideal
            sugestoes.append(f"Iniciar produção {self._formatar_duracao(antecipacao)} mais cedo")
        
        # Sugestão de ajuste de prazo
        if contexto_adicional and 'proximo_horario_livre' in contexto_adicional:
            horario_livre = contexto_adicional['proximo_horario_livre']
            if isinstance(horario_livre, str):
                horario_livre = datetime.fromisoformat(horario_livre)
            
            fim_possivel = horario_livre + tempo_real
            if fim_possivel > prazo_final:
                novo_prazo = fim_possivel + timedelta(minutes=15)  # Margem de segurança
                sugestoes.append(f"Ajustar prazo para {novo_prazo.strftime('%H:%M')} ou posterior")
        
        # Sugestão de divisão de pedido
        if quantidade_necessaria > 50:
            sugestoes.append(f"Dividir pedido em lotes menores (atual: {quantidade_necessaria} unidades)")
        
        # Sugestão baseada em capacidade
        if contexto_adicional and 'capacidade_maxima' in contexto_adicional:
            capacidade = contexto_adicional['capacidade_maxima']
            if quantidade_necessaria > capacidade:
                num_lotes = (quantidade_necessaria + capacidade - 1) // capacidade
                sugestoes.append(f"Processar em {num_lotes} lotes de até {capacidade} unidades cada")
        
        return sugestoes
    
    def _salvar_log(
        self,
        id_ordem: int,
        id_pedido: int,
        log_formatado: str,
        tipo_erro: str,
        dados_json: Dict[str, Any]
    ) -> str:
        """
        Salva o log formatado e a versão JSON.
        """
        # Salvar arquivo de log formatado
        nome_arquivo = f"ordem: {id_ordem} | pedido: {id_pedido}.log"
        arquivo_path = self.base_dir / nome_arquivo
        
        # Se já existe um arquivo, adicionar ao conteúdo existente
        if arquivo_path.exists():
            with open(arquivo_path, 'r', encoding='utf-8') as f:
                conteudo_existente = f.read()
            log_formatado = conteudo_existente + "\n\n" + log_formatado
        
        with open(arquivo_path, 'w', encoding='utf-8') as f:
            f.write(log_formatado)
        
        logger.info(f"📝 Log de erro temporal criado: {arquivo_path}")
        
        # Salvar versão JSON
        json_filename = f"ordem_{id_ordem}_pedido_{id_pedido}_temporal_errors.json"
        json_path = self.base_dir / json_filename
        
        # Estrutura JSON
        erro_data = {
            "tipo_erro": tipo_erro,
            **dados_json
        }
        
        # Se já existe, adicionar ao array existente
        if json_path.exists():
            with open(json_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                if not isinstance(existing_data, list):
                    existing_data = [existing_data]
        else:
            existing_data = []
        
        existing_data.append(erro_data)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=2, ensure_ascii=False)
        
        logger.debug(f"📄 Versão JSON salva: {json_path}")
        
        return str(arquivo_path)


# ========================================================================
#                      FUNÇÕES AUXILIARES GLOBAIS
# ========================================================================

# Instância global para reutilização
_logger_instance = None

def get_temporal_logger() -> TemporalAllocationLogger:
    """
    Retorna instância singleton do logger temporal.
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = TemporalAllocationLogger()
    return _logger_instance


def log_deadline_allocation_error(
    id_ordem: int,
    id_pedido: int,
    id_atividade: int,
    nome_atividade: str,
    tipo_equipamento: str,
    quantidade_necessaria: int,
    prazo_final: datetime,
    duracao_atividade: timedelta,
    janela_disponivel: Tuple[datetime, datetime],
    motivo_falha: str,
    tempo_maximo_espera: Optional[timedelta] = None,
    proximo_horario_livre: Optional[datetime] = None,
    equipamentos_tentados: Optional[List[str]] = None,
    contexto_adicional: Optional[Dict[str, Any]] = None
) -> str:
    """
    Função auxiliar para registrar erro de alocação por prazo.
    """
    logger = get_temporal_logger()
    return logger.log_deadline_allocation_error(
        id_ordem=id_ordem,
        id_pedido=id_pedido,
        id_atividade=id_atividade,
        nome_atividade=nome_atividade,
        tipo_equipamento=tipo_equipamento,
        quantidade_necessaria=quantidade_necessaria,
        prazo_final=prazo_final,
        duracao_atividade=duracao_atividade,
        janela_disponivel=janela_disponivel,
        motivo_falha=motivo_falha,
        tempo_maximo_espera=tempo_maximo_espera,
        proximo_horario_livre=proximo_horario_livre,
        equipamentos_tentados=equipamentos_tentados,
        contexto_adicional=contexto_adicional
    )


def log_inter_activity_timing_error(
    id_ordem: int,
    id_pedido: int,
    current_activity_id: int,
    current_activity_name: str,
    successor_activity_id: int,
    successor_activity_name: str,
    current_end_time: datetime,
    successor_start_time: datetime,
    maximum_wait_time: timedelta,
    current_activity_obj=None,
    successor_activity_obj=None
) -> str:
    """
    Função auxiliar para registrar erro de timing entre atividades.
    """
    logger = get_temporal_logger()
    return logger.log_inter_activity_timing_error(
        id_ordem=id_ordem,
        id_pedido=id_pedido,
        current_activity_id=current_activity_id,
        current_activity_name=current_activity_name,
        successor_activity_id=successor_activity_id,
        successor_activity_name=successor_activity_name,
        current_end_time=current_end_time,
        successor_start_time=successor_start_time,
        maximum_wait_time=maximum_wait_time,
        current_activity_obj=current_activity_obj,
        successor_activity_obj=successor_activity_obj
    )


def log_intra_activity_timing_error(
    id_ordem: int,
    id_pedido: int,
    activity_id: int,
    activity_name: str,
    current_equipment: str,
    successor_equipment: str,
    current_end_time: datetime,
    successor_start_time: datetime,
    maximum_wait_time: timedelta
) -> str:
    """
    Função auxiliar para registrar erro de timing intra-atividade.
    """
    logger = get_temporal_logger()
    return logger.log_intra_activity_timing_error(
        id_ordem=id_ordem,
        id_pedido=id_pedido,
        activity_id=activity_id,
        activity_name=activity_name,
        current_equipment=current_equipment,
        successor_equipment=successor_equipment,
        current_end_time=current_end_time,
        successor_start_time=successor_start_time,
        maximum_wait_time=maximum_wait_time
    )