"""
Analisador de Conflitos de Equipamentos
======================================

Analisa conflitos específicos de equipamentos mostrando:
- Quais equipamentos foram tentados
- Período exato de ocupação necessário
- Ocupações existentes que impedem a alocação
- Sugestões para resolução

Criado em: 16/09/2025
"""

import gc
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from utils.logs.logger_factory import setup_logger

logger = setup_logger('EquipmentConflictAnalyzer')


class EquipmentConflictAnalyzer:
    """
    Analisa conflitos específicos de equipamentos com base nas ocupações reais.
    """

    def __init__(self):
        self.equipamentos_sistema = {}
        self._descobrir_equipamentos()

    def _descobrir_equipamentos(self):
        """Descobre equipamentos ativos no sistema via garbage collector."""
        try:
            from factory.fabrica_equipamentos import FabricaEquipamentos
            fabrica = FabricaEquipamentos()
            self.equipamentos_sistema = fabrica.obter_todos_equipamentos()
            logger.debug(f"✅ {len(self.equipamentos_sistema)} equipamentos descobertos via fábrica")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao descobrir equipamentos via fábrica: {e}")
            self.equipamentos_sistema = {}

    def analisar_conflito_atividade(
        self,
        equipamentos_tentados: List[str],
        periodo_inicio: datetime,
        periodo_fim: datetime,
        id_atividade: int,
        nome_atividade: str,
        quantidade_necessaria: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Analisa conflito específico de uma atividade.

        Args:
            equipamentos_tentados: Lista de equipamentos que deveriam ser usados
            periodo_inicio: Início do período necessário
            periodo_fim: Fim do período necessário
            id_atividade: ID da atividade que falhou
            nome_atividade: Nome da atividade
            quantidade_necessaria: Quantidade a ser processada

        Returns:
            Dicionário com análise detalhada do conflito
        """
        try:
            conflito_info = {
                "periodo_solicitado": {
                    "inicio": periodo_inicio.strftime("%d/%m/%Y %H:%M:%S"),
                    "fim": periodo_fim.strftime("%d/%m/%Y %H:%M:%S"),
                    "duracao_minutos": int((periodo_fim - periodo_inicio).total_seconds() / 60)
                },
                "equipamentos_analisados": equipamentos_tentados,
                "conflitos_por_equipamento": {},
                "disponibilidade_alternativa": [],
                "sugestoes": []
            }

            total_equipamentos_ocupados = 0
            equipamentos_livres = []

            # Analisar cada equipamento tentado
            for nome_equipamento in equipamentos_tentados:
                conflito_equip = self._analisar_equipamento_especifico(
                    nome_equipamento, periodo_inicio, periodo_fim
                )

                if conflito_equip:
                    conflito_info["conflitos_por_equipamento"][nome_equipamento] = conflito_equip
                    if conflito_equip["ocupado"]:
                        total_equipamentos_ocupados += 1
                    else:
                        equipamentos_livres.append(nome_equipamento)

            # Resumo do conflito
            conflito_info["resumo"] = {
                "equipamentos_tentados": len(equipamentos_tentados),
                "equipamentos_ocupados": total_equipamentos_ocupados,
                "equipamentos_livres": len(equipamentos_livres),
                "conflito_total": total_equipamentos_ocupados == len(equipamentos_tentados)
            }

            # Gerar sugestões
            conflito_info["sugestoes"] = self._gerar_sugestoes_resolucao(
                conflito_info, periodo_inicio, periodo_fim, equipamentos_livres
            )

            # Buscar horários alternativos
            conflito_info["horarios_alternativos"] = self._buscar_horarios_alternativos(
                equipamentos_tentados, periodo_inicio, periodo_fim
            )

            return conflito_info

        except Exception as e:
            logger.error(f"❌ Erro ao analisar conflito: {e}")
            return {
                "erro": f"Falha na análise: {e}",
                "periodo_solicitado": {
                    "inicio": periodo_inicio.strftime("%d/%m/%Y %H:%M:%S"),
                    "fim": periodo_fim.strftime("%d/%m/%Y %H:%M:%S")
                }
            }

    def _analisar_equipamento_especifico(
        self,
        nome_equipamento: str,
        periodo_inicio: datetime,
        periodo_fim: datetime
    ) -> Optional[Dict[str, Any]]:
        """
        Analisa um equipamento específico para conflitos.
        """
        try:
            # Buscar equipamento no sistema
            equipamento = self.equipamentos_sistema.get(nome_equipamento)
            if not equipamento:
                return {
                    "equipamento": nome_equipamento,
                    "status": "NAO_ENCONTRADO",
                    "ocupado": False,
                    "ocupacoes_conflitantes": [],
                    "motivo": f"Equipamento '{nome_equipamento}' não encontrado no sistema"
                }

            # Verificar ocupações no período
            ocupacoes_conflitantes = []
            equipamento_ocupado = False

            # Verificar se tem agenda/ocupações
            if hasattr(equipamento, 'agenda_ocupacoes'):
                for ocupacao in equipamento.agenda_ocupacoes:
                    inicio_ocupacao = ocupacao.get('inicio')
                    fim_ocupacao = ocupacao.get('fim')

                    if inicio_ocupacao and fim_ocupacao:
                        # Verificar sobreposição
                        if self._periodos_se_sobrepoe(
                            periodo_inicio, periodo_fim,
                            inicio_ocupacao, fim_ocupacao
                        ):
                            equipamento_ocupado = True
                            ocupacoes_conflitantes.append({
                                "pedido": ocupacao.get('id_pedido', 'N/A'),
                                "atividade": ocupacao.get('id_atividade', 'N/A'),
                                "inicio": inicio_ocupacao.strftime("%d/%m/%Y %H:%M"),
                                "fim": fim_ocupacao.strftime("%d/%m/%Y %H:%M"),
                                "item": ocupacao.get('id_item', 'N/A'),
                                "sobreposicao_percentual": self._calcular_sobreposicao_percentual(
                                    periodo_inicio, periodo_fim,
                                    inicio_ocupacao, fim_ocupacao
                                )
                            })

            return {
                "equipamento": nome_equipamento,
                "status": "DISPONIVEL" if not equipamento_ocupado else "OCUPADO",
                "ocupado": equipamento_ocupado,
                "ocupacoes_conflitantes": ocupacoes_conflitantes,
                "tipo_equipamento": type(equipamento).__name__,
                "detalhes_equipamento": self._extrair_detalhes_equipamento(equipamento)
            }

        except Exception as e:
            logger.error(f"❌ Erro ao analisar equipamento {nome_equipamento}: {e}")
            return {
                "equipamento": nome_equipamento,
                "status": "ERRO_ANALISE",
                "ocupado": True,  # Assumir ocupado em caso de erro
                "motivo": f"Erro na análise: {e}"
            }

    def _periodos_se_sobrepoe(
        self,
        inicio1: datetime, fim1: datetime,
        inicio2: datetime, fim2: datetime
    ) -> bool:
        """Verifica se dois períodos se sobrepõem."""
        return not (fim1 <= inicio2 or fim2 <= inicio1)

    def _calcular_sobreposicao_percentual(
        self,
        inicio_solicitado: datetime, fim_solicitado: datetime,
        inicio_ocupacao: datetime, fim_ocupacao: datetime
    ) -> float:
        """Calcula percentual de sobreposição entre dois períodos."""
        try:
            # Calcular interseção
            inicio_intersecao = max(inicio_solicitado, inicio_ocupacao)
            fim_intersecao = min(fim_solicitado, fim_ocupacao)

            if inicio_intersecao >= fim_intersecao:
                return 0.0

            duracao_intersecao = (fim_intersecao - inicio_intersecao).total_seconds()
            duracao_solicitada = (fim_solicitado - inicio_solicitado).total_seconds()

            if duracao_solicitada == 0:
                return 0.0

            percentual = (duracao_intersecao / duracao_solicitada) * 100
            return round(percentual, 1)

        except Exception:
            return 0.0

    def _extrair_detalhes_equipamento(self, equipamento) -> Dict[str, Any]:
        """Extrai detalhes relevantes do equipamento."""
        detalhes = {}

        try:
            if hasattr(equipamento, 'nome'):
                detalhes['nome'] = equipamento.nome

            if hasattr(equipamento, 'capacidade'):
                detalhes['capacidade'] = equipamento.capacidade

            if hasattr(equipamento, 'numero_fracoes'):
                detalhes['fracoes'] = equipamento.numero_fracoes

            if hasattr(equipamento, 'numero_bocas'):
                detalhes['bocas'] = equipamento.numero_bocas

            if hasattr(equipamento, 'numero_caixas'):
                detalhes['caixas'] = equipamento.numero_caixas

        except Exception as e:
            detalhes['erro_detalhes'] = str(e)

        return detalhes

    def _gerar_sugestoes_resolucao(
        self,
        conflito_info: Dict[str, Any],
        periodo_inicio: datetime,
        periodo_fim: datetime,
        equipamentos_livres: List[str]
    ) -> List[str]:
        """Gera sugestões para resolver o conflito."""
        sugestoes = []

        try:
            resumo = conflito_info["resumo"]

            # Sugestão de equipamentos livres
            if equipamentos_livres:
                sugestoes.append(
                    f"✅ Usar equipamentos disponíveis: {', '.join(equipamentos_livres)}"
                )

            # Sugestão temporal
            if resumo["conflito_total"]:
                sugestoes.append(
                    "⏰ Reagendar atividade para horário com menor conflito"
                )

                # Sugerir horário específico se possível
                duracao = periodo_fim - periodo_inicio
                horario_sugerido = periodo_fim + timedelta(minutes=5)
                sugestoes.append(
                    f"📅 Sugestão: executar após {horario_sugerido.strftime('%H:%M')} "
                    f"(duração: {int(duracao.total_seconds()/60)} min)"
                )

            # Sugestão de capacidade
            total_tentados = resumo["equipamentos_tentados"]
            if total_tentados > 3:
                sugestoes.append(
                    "📊 Considerar dividir atividade em lotes menores para usar menos equipamentos"
                )

            # Sugestão de equipamentos adicionais
            sugestoes.append(
                "🔧 Verificar se há equipamentos similares não listados nos elegíveis"
            )

        except Exception as e:
            sugestoes.append(f"⚠️ Erro ao gerar sugestões: {e}")

        return sugestoes

    def _buscar_horarios_alternativos(
        self,
        equipamentos_tentados: List[str],
        periodo_inicio: datetime,
        periodo_fim: datetime
    ) -> List[Dict[str, Any]]:
        """Busca horários alternativos onde os equipamentos estariam livres."""
        horarios_alternativos = []

        try:
            duracao_necessaria = periodo_fim - periodo_inicio

            # Verificar slots de 30 em 30 minutos nas próximas 4 horas
            for offset_minutos in range(30, 240, 30):
                novo_inicio = periodo_inicio + timedelta(minutes=offset_minutos)
                novo_fim = novo_inicio + duracao_necessaria

                equipamentos_livres_slot = 0
                detalhes_slot = []

                for equipamento in equipamentos_tentados:
                    analise = self._analisar_equipamento_especifico(
                        equipamento, novo_inicio, novo_fim
                    )

                    if analise and not analise["ocupado"]:
                        equipamentos_livres_slot += 1
                        detalhes_slot.append(equipamento)

                if equipamentos_livres_slot > 0:
                    percentual_livre = (equipamentos_livres_slot / len(equipamentos_tentados)) * 100

                    horarios_alternativos.append({
                        "inicio": novo_inicio.strftime("%d/%m/%Y %H:%M"),
                        "fim": novo_fim.strftime("%d/%m/%Y %H:%M"),
                        "equipamentos_livres": equipamentos_livres_slot,
                        "total_equipamentos": len(equipamentos_tentados),
                        "percentual_disponibilidade": round(percentual_livre, 1),
                        "equipamentos_disponiveis": detalhes_slot
                    })

                # Parar se encontrou slot 100% livre
                if equipamentos_livres_slot == len(equipamentos_tentados):
                    break

        except Exception as e:
            logger.error(f"❌ Erro ao buscar horários alternativos: {e}")

        return horarios_alternativos[:3]  # Retornar apenas os 3 melhores

    def gerar_relatorio_textual(self, analise_conflito: Dict[str, Any]) -> str:
        """
        Gera relatório textual detalhado do conflito.
        """
        try:
            relatorio = []
            relatorio.append("🚨 ANÁLISE DETALHADA DE CONFLITO DE EQUIPAMENTOS")
            relatorio.append("=" * 60)

            # Período solicitado
            periodo = analise_conflito["periodo_solicitado"]
            relatorio.append(f"⏰ Período necessário: {periodo['inicio']} → {periodo['fim']}")
            relatorio.append(f"⏱️ Duração: {periodo['duracao_minutos']} minutos")
            relatorio.append("")

            # Resumo
            resumo = analise_conflito.get("resumo", {})
            relatorio.append("📊 RESUMO DO CONFLITO:")
            relatorio.append(f"   • Equipamentos analisados: {resumo.get('equipamentos_tentados', 0)}")
            relatorio.append(f"   • Equipamentos ocupados: {resumo.get('equipamentos_ocupados', 0)}")
            relatorio.append(f"   • Equipamentos livres: {resumo.get('equipamentos_livres', 0)}")
            relatorio.append(f"   • Conflito total: {'SIM' if resumo.get('conflito_total') else 'NÃO'}")
            relatorio.append("")

            # Conflitos por equipamento
            conflitos = analise_conflito.get("conflitos_por_equipamento", {})
            if conflitos:
                relatorio.append("🔧 ANÁLISE POR EQUIPAMENTO:")
                for nome_equip, detalhes in conflitos.items():
                    status = "🔴 OCUPADO" if detalhes["ocupado"] else "🟢 LIVRE"
                    relatorio.append(f"   📋 {nome_equip}: {status}")

                    # Ocupações conflitantes
                    ocupacoes = detalhes.get("ocupacoes_conflitantes", [])
                    for ocupacao in ocupacoes:
                        relatorio.append(
                            f"      🚫 Pedido {ocupacao['pedido']} | "
                            f"Atividade {ocupacao['atividade']} | "
                            f"{ocupacao['inicio']} → {ocupacao['fim']} | "
                            f"Sobreposição: {ocupacao['sobreposicao_percentual']}%"
                        )
                relatorio.append("")

            # Horários alternativos
            horarios = analise_conflito.get("horarios_alternativos", [])
            if horarios:
                relatorio.append("📅 HORÁRIOS ALTERNATIVOS DISPONÍVEIS:")
                for i, horario in enumerate(horarios, 1):
                    relatorio.append(
                        f"   {i}. {horario['inicio']} → {horario['fim']} "
                        f"({horario['percentual_disponibilidade']}% livre)"
                    )
                relatorio.append("")

            # Sugestões
            sugestoes = analise_conflito.get("sugestoes", [])
            if sugestoes:
                relatorio.append("💡 SUGESTÕES DE RESOLUÇÃO:")
                for sugestao in sugestoes:
                    relatorio.append(f"   • {sugestao}")

            return "\n".join(relatorio)

        except Exception as e:
            return f"❌ Erro ao gerar relatório: {e}"


# Função de conveniência para uso direto
def analisar_conflito_equipamentos(
    equipamentos_tentados: List[str],
    periodo_inicio: datetime,
    periodo_fim: datetime,
    id_atividade: int,
    nome_atividade: str,
    quantidade_necessaria: Optional[float] = None
) -> Tuple[Dict[str, Any], str]:
    """
    Função de conveniência para analisar conflitos.

    Returns:
        Tupla com (dados_analise, relatorio_textual)
    """
    analyzer = EquipmentConflictAnalyzer()

    analise = analyzer.analisar_conflito_atividade(
        equipamentos_tentados=equipamentos_tentados,
        periodo_inicio=periodo_inicio,
        periodo_fim=periodo_fim,
        id_atividade=id_atividade,
        nome_atividade=nome_atividade,
        quantidade_necessaria=quantidade_necessaria
    )

    relatorio = analyzer.gerar_relatorio_textual(analise)

    return analise, relatorio