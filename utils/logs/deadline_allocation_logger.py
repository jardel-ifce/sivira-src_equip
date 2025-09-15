# utils/logs/deadline_allocation_logger.py
"""
Sistema de logs específico para erros de alocação por prazo expirado.
Registra falhas quando atividades não conseguem ser alocadas dentro do prazo estabelecido.
"""

import os
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from utils.logs.logger_factory import setup_logger

logger = setup_logger('DeadlineAllocationLogger')


class DeadlineAllocationLogger:
    """
    Logger especializado para erros de alocação devido a prazos.
    Registra quando atividades não conseguem ser alocadas dentro do tempo limite.
    """
    
    def __init__(self, base_dir: str = "logs/erros"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
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
        janela_disponivel: tuple[datetime, datetime],
        motivo_falha: str,
        equipamentos_tentados: Optional[List[str]] = None,
        contexto_adicional: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Registra erro de alocação por prazo no formato limpo e estruturado.
        
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
            equipamentos_tentados: Lista de equipamentos que foram tentados
            contexto_adicional: Informações extras relevantes
            
        Returns:
            Caminho do arquivo de log criado
        """
        timestamp = datetime.now()
        
        # Gerar log no formato limpo
        log_formatado = self._formatar_log_limpo(
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
        nome_arquivo = f"ordem: {id_ordem} | pedido: {id_pedido}.log"
        arquivo_path = self.base_dir / nome_arquivo
        
        # Se já existe um arquivo, adicionar ao conteúdo existente
        if arquivo_path.exists():
            with open(arquivo_path, 'r', encoding='utf-8') as f:
                conteudo_existente = f.read()
            log_formatado = conteudo_existente + "\n\n" + log_formatado
        
        with open(arquivo_path, 'w', encoding='utf-8') as f:
            f.write(log_formatado)
        
        logger.info(f"📝 Log de erro de prazo criado: {arquivo_path}")
        
        # Também salvar versão JSON para processamento automatizado
        self._salvar_versao_json(
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
        
        return str(arquivo_path)
    
    def _formatar_log_limpo(
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
        janela_disponivel: tuple[datetime, datetime],
        motivo_falha: str,
        equipamentos_tentados: Optional[List[str]] = None,
        contexto_adicional: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Formata o log no padrão limpo e legível.
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
        log += f"   • Tempo Total Disponível: {self._formatar_duracao(janela_total)}\n\n"
        
        # Motivo da falha
        log += "🔍 MOTIVO DA FALHA:\n"
        log += f"   {motivo_falha}\n\n"
        
        # Equipamentos tentados
        if equipamentos_tentados:
            log += "🏭 EQUIPAMENTOS TENTADOS:\n"
            for equipamento in equipamentos_tentados:
                log += f"   • {equipamento}\n"
            log += "\n"
        
        # Análise do problema
        log += "📊 ANÁLISE:\n"
        
        # Verificar se é problema de bateladas
        if contexto_adicional and 'bateladas_necessarias' in contexto_adicional:
            bateladas = contexto_adicional['bateladas_necessarias']
            tempo_por_batelada = contexto_adicional.get('tempo_por_batelada', timedelta(minutes=16))
            tempo_total_bateladas = tempo_por_batelada * bateladas
            
            log += f"   • Bateladas necessárias: {bateladas}\n"
            log += f"   • Tempo por batelada: {self._formatar_duracao(tempo_por_batelada)}\n"
            log += f"   • Tempo total necessário: {self._formatar_duracao(tempo_total_bateladas)}\n"
            
            if tempo_total_bateladas > duracao_atividade:
                excesso = tempo_total_bateladas - duracao_atividade
                log += f"   • ⚠️ Tempo de bateladas excede duração prevista em {self._formatar_duracao(excesso)}\n"
        
        # Verificar se houve tentativa de alocação após o prazo
        if contexto_adicional and 'fim_real_tentado' in contexto_adicional:
            fim_real = contexto_adicional['fim_real_tentado']
            if isinstance(fim_real, str):
                fim_real = datetime.fromisoformat(fim_real)
            
            if fim_real > prazo_final:
                atraso = fim_real - prazo_final
                log += f"   • ⚠️ Alocação terminaria às {fim_real.strftime('%H:%M')}\n"
                log += f"   • Atraso de {self._formatar_duracao(atraso)} em relação ao prazo\n"
        
        log += "\n"
        
        # Sugestões
        log += "💡 SUGESTÕES:\n"
        sugestoes = self._gerar_sugestoes(
            quantidade_necessaria=quantidade_necessaria,
            duracao_atividade=duracao_atividade,
            janela_disponivel=janela_disponivel,
            contexto_adicional=contexto_adicional
        )
        for sugestao in sugestoes:
            log += f"   • {sugestao}\n"
        
        # Contexto adicional relevante
        if contexto_adicional:
            itens_relevantes = {
                'capacidade_maxima': 'Capacidade máxima do equipamento',
                'unidades_por_cesta': 'Unidades por cesta',
                'temperatura_necessaria': 'Temperatura necessária',
                'conflitos_detectados': 'Conflitos de agenda detectados'
            }
            
            contexto_mostrar = {
                itens_relevantes[k]: v 
                for k, v in contexto_adicional.items() 
                if k in itens_relevantes
            }
            
            if contexto_mostrar:
                log += "\n📎 INFORMAÇÕES ADICIONAIS:\n"
                for chave, valor in contexto_mostrar.items():
                    log += f"   • {chave}: {valor}\n"
        
        log += "\n" + "=" * 50
        
        return log
    
    def _formatar_duracao(self, duracao: timedelta) -> str:
        """
        Formata duração de forma legível.
        """
        total_segundos = int(duracao.total_seconds())
        horas = total_segundos // 3600
        minutos = (total_segundos % 3600) // 60
        
        if horas > 0:
            return f"{horas}h {minutos}min"
        else:
            return f"{minutos} minutos"
    
    def _gerar_sugestoes(
        self,
        quantidade_necessaria: int,
        duracao_atividade: timedelta,
        janela_disponivel: tuple[datetime, datetime],
        contexto_adicional: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Gera sugestões baseadas no contexto do erro.
        """
        sugestoes = []
        
        # Sugestão baseada em bateladas
        if contexto_adicional and 'bateladas_necessarias' in contexto_adicional:
            bateladas = contexto_adicional['bateladas_necessarias']
            if bateladas > 2:
                sugestoes.append(f"Reduzir quantidade para processar em menos bateladas (atual: {bateladas})")
                sugestoes.append("Considerar uso de múltiplos equipamentos em paralelo")
        
        # Sugestão de janela temporal
        janela_total = janela_disponivel[1] - janela_disponivel[0]
        if janela_total < timedelta(hours=4):
            sugestoes.append("Aumentar janela de produção iniciando mais cedo")
        
        # Sugestão de prazo
        sugestoes.append("Ajustar prazo de entrega para um horário mais realista")
        
        # Sugestão de quantidade
        if quantidade_necessaria > 50:
            sugestoes.append(f"Dividir pedido em lotes menores (atual: {quantidade_necessaria} unidades)")
        
        # Sugestão baseada em capacidade
        if contexto_adicional and 'capacidade_maxima' in contexto_adicional:
            capacidade = contexto_adicional['capacidade_maxima']
            if quantidade_necessaria > capacidade:
                num_lotes = (quantidade_necessaria + capacidade - 1) // capacidade
                sugestoes.append(f"Processar em {num_lotes} lotes de até {capacidade} unidades cada")
        
        return sugestoes
    
    def _salvar_versao_json(
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
        janela_disponivel: tuple[datetime, datetime],
        motivo_falha: str,
        equipamentos_tentados: Optional[List[str]] = None,
        contexto_adicional: Optional[Dict[str, Any]] = None
    ):
        """
        Salva versão JSON do erro para processamento automatizado.
        """
        erro_data = {
            "timestamp": timestamp.isoformat(),
            "tipo_erro": "DEADLINE_ALLOCATION",
            "identificacao": {
                "id_ordem": id_ordem,
                "id_pedido": id_pedido,
                "id_atividade": id_atividade,
                "nome_atividade": nome_atividade
            },
            "detalhes": {
                "tipo_equipamento": tipo_equipamento,
                "quantidade_necessaria": quantidade_necessaria,
                "prazo_final": prazo_final.isoformat(),
                "duracao_atividade": str(duracao_atividade),
                "janela_disponivel": {
                    "inicio": janela_disponivel[0].isoformat(),
                    "fim": janela_disponivel[1].isoformat()
                },
                "motivo_falha": motivo_falha,
                "equipamentos_tentados": equipamentos_tentados or []
            },
            "contexto_adicional": contexto_adicional or {},
            "sugestoes": self._gerar_sugestoes(
                quantidade_necessaria=quantidade_necessaria,
                duracao_atividade=duracao_atividade,
                janela_disponivel=janela_disponivel,
                contexto_adicional=contexto_adicional
            )
        }
        
        # Salvar JSON
        json_filename = f"ordem_{id_ordem}_pedido_{id_pedido}_deadline_errors.json"
        json_path = self.base_dir / json_filename
        
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


# Função auxiliar para facilitar o uso
def log_deadline_allocation_error(
    id_ordem: int,
    id_pedido: int, 
    id_atividade: int,
    nome_atividade: str,
    tipo_equipamento: str,
    quantidade_necessaria: int,
    prazo_final: datetime,
    duracao_atividade: timedelta,
    janela_disponivel: tuple[datetime, datetime],
    motivo_falha: str,
    equipamentos_tentados: Optional[List[str]] = None,
    contexto_adicional: Optional[Dict[str, Any]] = None
) -> str:
    """
    Função auxiliar para registrar erro de alocação por prazo.
    """
    logger_instance = DeadlineAllocationLogger()
    return logger_instance.log_deadline_allocation_error(
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