"""
Gerador de Janelas Temporais - VERSÃO SIMPLIFICADA SEM LOOP INFINITO
===================================================================

✅ CORRIGIDO: Gera menos janelas para evitar explosão de restrições
✅ MANTÉM: Funcionalidade completa mas com limites seguros
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class JanelaTemporal:
    """Representa uma janela temporal específica para um pedido"""
    pedido_id: int
    datetime_inicio: datetime
    datetime_fim: datetime
    viavel: bool = True


class GeradorJanelasTemporais:
    """
    ✅ VERSÃO SIMPLIFICADA: Gera número controlado de janelas
    """
    
    def __init__(self, resolucao_minutos: int = 60):  # ✅ Resolução maior por padrão
        self.resolucao_minutos = resolucao_minutos
        self.janelas_por_pedido = {}
        self.logs_debug = []
        self.pedidos_com_fim_obrigatorio = {}
        self.configuracao_tempo = None
        
        # ✅ LIMITES DE SEGURANÇA (OTIMIZADOS para maximizar pedidos atendidos)
        self.max_janelas_por_pedido = 15  # Máximo 15 janelas por pedido (aumentado de 8)
        self.resolucao_minima = 30        # Mínimo 30 minutos de resolução
        
        print(f"⏰ GeradorJanelasTemporais inicializado (VERSÃO SIMPLIFICADA):")
        print(f"   Resolução: {resolucao_minutos} minutos")
        print(f"   Máximo janelas por pedido: {self.max_janelas_por_pedido}")
        
    def gerar_janelas_todos_pedidos(self, dados_pedidos: List, 
                                   pedidos_com_fim_obrigatorio: Dict[int, datetime] = None) -> Dict[int, List[JanelaTemporal]]:
        """
        ✅ VERSÃO SIMPLIFICADA: Gera janelas com limites seguros
        """
        print(f"🔄 Gerando janelas temporais SIMPLIFICADAS para {len(dados_pedidos)} pedidos...")
        
        # Armazena informação sobre fins obrigatórios
        self.pedidos_com_fim_obrigatorio = pedidos_com_fim_obrigatorio or {}
        
        # Configurar horizonte temporal
        self._configurar_horizonte_temporal_simples(dados_pedidos)
        
        # Gerar janelas para cada pedido (com limites)
        self.janelas_por_pedido = {}
        total_janelas = 0
        
        for pedido_data in dados_pedidos:
            print(f"\n📋 Processando Pedido {pedido_data.id_pedido} ({pedido_data.nome_produto}):")
            print(f"   Duração necessária: {pedido_data.duracao_total}")
            
            # Verificar se é pedido com fim obrigatório
            eh_fim_obrigatorio = pedido_data.id_pedido in self.pedidos_com_fim_obrigatorio
            print(f"   Tipo: {'FIM OBRIGATÓRIO' if eh_fim_obrigatorio else 'FLEXÍVEL'}")
            
            # Validação básica
            janela_disponivel = pedido_data.fim_jornada - pedido_data.inicio_jornada
            print(f"   Janela disponível: {janela_disponivel}")
            
            if pedido_data.duracao_total > janela_disponivel:
                print(f"   ❌ IMPOSSÍVEL: Duração necessária > Janela disponível")
                self.janelas_por_pedido[pedido_data.id_pedido] = []
                continue
            
            # ✅ GERA JANELAS CONTROLADAS
            janelas_pedido = self._gerar_janelas_simplificadas(pedido_data, eh_fim_obrigatorio)
            
            self.janelas_por_pedido[pedido_data.id_pedido] = janelas_pedido
            total_janelas += len(janelas_pedido)
            
            print(f"   ✅ {len(janelas_pedido)} janelas possíveis geradas")
        
        print(f"\n📊 Total de janelas geradas: {total_janelas:,}")
        return self.janelas_por_pedido
    
    def _gerar_janelas_simplificadas(self, pedido_data, eh_fim_obrigatorio: bool) -> List[JanelaTemporal]:
        """
        ✅ VERSÃO SIMPLIFICADA: Gera número controlado de janelas

        CORREÇÃO CRÍTICA: Se eh_fim_obrigatorio=True, gera APENAS 1 janela que termina no deadline.
        Isso força o PL a usar a janela correta para backward scheduling.
        """
        print(f"      ✅ Gerando janelas simplificadas...")

        janelas = []

        # Calcular limites
        inicio_mais_cedo = pedido_data.inicio_jornada
        inicio_mais_tarde = pedido_data.fim_jornada - pedido_data.duracao_total

        print(f"      Início mais cedo: {inicio_mais_cedo.strftime('%d/%m %H:%M')}")
        print(f"      Início mais tarde: {inicio_mais_tarde.strftime('%d/%m %H:%M')}")

        # Validação
        if inicio_mais_tarde < inicio_mais_cedo:
            print(f"      ❌ IMPOSSÍVEL: Não há espaço suficiente")
            return []

        # ✅ CORREÇÃO CRÍTICA: Se é fim obrigatório, gerar janela AMPLA que termina no deadline
        if eh_fim_obrigatorio:
            deadline = self.pedidos_com_fim_obrigatorio[pedido_data.id_pedido]
            print(f"      🎯 Fim obrigatório: {deadline.strftime('%d/%m %H:%M')}")

            # ESTRATÉGIA: Janela ampla para dar espaço ao backward scheduling
            # Multiplicador de margem: 3x a duração do pedido (mínimo 6h)
            margem_seguranca = max(
                pedido_data.duracao_total * 3,  # 3x a duração
                timedelta(hours=6)  # Mínimo 6 horas
            )

            # Início: o mais cedo possível, dando margem
            inicio_para_deadline = max(
                inicio_mais_cedo,
                deadline - margem_seguranca
            )

            if inicio_para_deadline >= inicio_mais_cedo:
                print(f"      ✅ Janela AMPLA para deadline: {inicio_para_deadline.strftime('%d/%m %H:%M')} → {deadline.strftime('%d/%m %H:%M')}")
                print(f"         Margem de segurança: {margem_seguranca} (duração pedido: {pedido_data.duracao_total})")

                janela_deadline = JanelaTemporal(
                    pedido_id=pedido_data.id_pedido,
                    datetime_inicio=inicio_para_deadline,
                    datetime_fim=deadline,
                    viavel=True
                )
                janelas.append(janela_deadline)
            else:
                print(f"      ❌ IMPOSSÍVEL: Início calculado ({inicio_para_deadline.strftime('%d/%m %H:%M')}) < início mais cedo")

            # ✅ RETORNAR AQUI: Não gerar mais janelas para fins obrigatórios
            print(f"      🎯 FIM OBRIGATÓRIO: Retornando janela ampla do deadline")
            return janelas
        
        # ✅ ESTRATÉGIA AMPLA: Gerar janelas com margem de segurança para backward scheduling
        janela_total = inicio_mais_tarde - inicio_mais_cedo

        # AUMENTAR JANELAS: Adicionar margem de segurança (2x duração do pedido ou mínimo 4h)
        margem_seguranca = max(
            pedido_data.duracao_total * 2,  # 2x a duração
            timedelta(hours=4)  # Mínimo 4 horas
        )

        # Expandir início e fim com margem
        inicio_expandido = max(
            pedido_data.inicio_jornada,
            inicio_mais_cedo - margem_seguranca
        )

        fim_expandido = min(
            pedido_data.fim_jornada,
            inicio_mais_tarde + margem_seguranca
        )

        janela_total_expandida = fim_expandido - inicio_expandido

        print(f"      📏 Janela expandida com margem: {inicio_expandido.strftime('%d/%m %H:%M')} → {fim_expandido.strftime('%d/%m %H:%M')}")
        print(f"         Margem adicionada: {margem_seguranca} (duração: {pedido_data.duracao_total})")

        if janela_total_expandida.total_seconds() <= 0:
            # Janela muito pequena - só uma opção
            janela_unica = JanelaTemporal(
                pedido_id=pedido_data.id_pedido,
                datetime_inicio=inicio_mais_cedo,
                datetime_fim=inicio_mais_cedo + pedido_data.duracao_total,
                viavel=True
            )
            if janela_unica not in janelas:
                janelas.append(janela_unica)
        else:
            # ✅ Gerar janelas AMPLAS em pontos estratégicos
            # Reduzido para 5 pontos para manter PL gerenciável
            pontos_estrategicos = [0.0, 0.25, 0.5, 0.75, 1.0]  # 5 pontos (0%, 25%, 50%, 75%, 100%)

            for ponto in pontos_estrategicos:
                inicio_ponto = inicio_expandido + timedelta(
                    seconds=janela_total_expandida.total_seconds() * ponto
                )

                # Janela vai do início até o fim expandido (janela GRANDE)
                fim_ponto = min(
                    inicio_ponto + pedido_data.duracao_total + margem_seguranca,
                    fim_expandido
                )

                # Verificar se está dentro dos limites
                if inicio_ponto >= pedido_data.inicio_jornada and fim_ponto <= pedido_data.fim_jornada:
                    janela_ponto = JanelaTemporal(
                        pedido_id=pedido_data.id_pedido,
                        datetime_inicio=inicio_ponto,
                        datetime_fim=fim_ponto,
                        viavel=True
                    )

                    # ✅ Evitar duplicatas
                    if not any(abs((j.datetime_inicio - janela_ponto.datetime_inicio).total_seconds()) < 1800
                              for j in janelas):  # 30min tolerância
                        janelas.append(janela_ponto)

                        # ✅ LIMITE DE SEGURANÇA
                        if len(janelas) >= self.max_janelas_por_pedido:
                            print(f"      ⚠️ Limite de {self.max_janelas_por_pedido} janelas atingido")
                            break
        
        print(f"      ✅ {len(janelas)} janelas simplificadas geradas")
        
        # Mostrar exemplos
        if janelas:
            print(f"      📋 Janelas geradas:")
            for i, janela in enumerate(janelas):
                inicio_str = janela.datetime_inicio.strftime('%d/%m %H:%M')
                fim_str = janela.datetime_fim.strftime('%d/%m %H:%M')
                print(f"         {i+1}. {inicio_str} → {fim_str}")
        
        return janelas
    
    def _configurar_horizonte_temporal_simples(self, dados_pedidos: List):
        """Configurar horizonte temporal para o modelo PL"""
        from dataclasses import dataclass
        
        @dataclass
        class ConfiguracaoTempo:
            inicio_horizonte: datetime
            fim_horizonte: datetime