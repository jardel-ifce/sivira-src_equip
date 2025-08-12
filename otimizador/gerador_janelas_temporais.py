"""
Gerador de Janelas Temporais - VERSÃO FINAL COMPLETA
====================================================

✅ VERSÃO FINAL: Usa apenas datetime, sem conversão para períodos
✅ FUNCIONAL: Compatível com modelo PL atualizado
✅ TESTADO: Funciona para 1 e múltiplos pedidos
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
    ✅ VERSÃO FINAL que trabalha diretamente com datetime
    """
    
    def __init__(self, resolucao_minutos: int = 30):
        self.resolucao_minutos = resolucao_minutos
        self.janelas_por_pedido = {}
        self.logs_debug = []
        self.pedidos_com_fim_obrigatorio = {}
        self.configuracao_tempo = None  # ✅ COMPATIBILIDADE: Para o modelo PL
        
    def gerar_janelas_todos_pedidos(self, dados_pedidos: List, 
                                   pedidos_com_fim_obrigatorio: Dict[int, datetime] = None) -> Dict[int, List[JanelaTemporal]]:
        """
        ✅ FINAL: Gera janelas usando apenas datetime
        """
        print(f"🔄 Gerando janelas temporais FINAIS para {len(dados_pedidos)} pedidos...")
        
        # Armazena informação sobre fins obrigatórios
        self.pedidos_com_fim_obrigatorio = pedidos_com_fim_obrigatorio or {}
        
        # ✅ COMPATIBILIDADE: Cria configuracao_tempo para o modelo PL
        self._configurar_horizonte_temporal_simples(dados_pedidos)
        
        # Gera janelas para cada pedido
        self.janelas_por_pedido = {}
        total_janelas = 0
        
        for pedido_data in dados_pedidos:
            print(f"\n📋 Processando Pedido {pedido_data.id_pedido} ({pedido_data.nome_produto}):")
            print(f"   Duração necessária: {pedido_data.duracao_total}")
            
            # Verifica se é pedido com fim obrigatório
            eh_fim_obrigatorio = pedido_data.id_pedido in self.pedidos_com_fim_obrigatorio
            print(f"   Tipo: {'FIM OBRIGATÓRIO' if eh_fim_obrigatorio else 'FLEXÍVEL'}")
            
            # Validação básica
            janela_disponivel = pedido_data.fim_jornada - pedido_data.inicio_jornada
            print(f"   Janela disponível: {janela_disponivel}")
            
            if pedido_data.duracao_total > janela_disponivel:
                print(f"   ❌ IMPOSSÍVEL: Duração necessária > Janela disponível")
                self.janelas_por_pedido[pedido_data.id_pedido] = []
                continue
            
            # ✅ GERA JANELAS MÚLTIPLAS (mesmo para fim obrigatório)
            # O PL escolherá a melhor baseado nas restrições
            janelas_pedido = self._gerar_janelas_multiplas_simples(pedido_data, eh_fim_obrigatorio)
            
            self.janelas_por_pedido[pedido_data.id_pedido] = janelas_pedido
            total_janelas += len(janelas_pedido)
            
            print(f"   ✅ {len(janelas_pedido)} janelas possíveis geradas")
        
        print(f"\n📊 Total de janelas geradas: {total_janelas:,}")
        return self.janelas_por_pedido
    
    def _gerar_janelas_multiplas_simples(self, pedido_data, eh_fim_obrigatorio: bool) -> List[JanelaTemporal]:
        """
        ✅ FINAL: Gera múltiplas janelas usando datetime simples
        """
        print(f"      ✅ Gerando janelas múltiplas (método final)...")
        
        janelas = []
        
        # Calcula limites
        inicio_mais_cedo = pedido_data.inicio_jornada
        inicio_mais_tarde = pedido_data.fim_jornada - pedido_data.duracao_total
        
        print(f"      Início mais cedo: {inicio_mais_cedo.strftime('%d/%m %H:%M')}")
        print(f"      Início mais tarde: {inicio_mais_tarde.strftime('%d/%m %H:%M')}")
        
        # Validação
        if inicio_mais_tarde < inicio_mais_cedo:
            print(f"      ❌ IMPOSSÍVEL: Não há espaço suficiente")
            return []
        
        # ✅ Se é fim obrigatório, foca nas janelas que terminam no deadline
        if eh_fim_obrigatorio:
            deadline = self.pedidos_com_fim_obrigatorio[pedido_data.id_pedido]
            print(f"      🎯 Fim obrigatório: {deadline.strftime('%d/%m %H:%M')}")
            
            # Gera janelas que terminam no deadline
            inicio_para_deadline = deadline - pedido_data.duracao_total
            
            # Verifica se é possível terminar no deadline
            if inicio_para_deadline >= inicio_mais_cedo:
                print(f"      ✅ Janela para deadline: {inicio_para_deadline.strftime('%d/%m %H:%M')} → {deadline.strftime('%d/%m %H:%M')}")
                
                janela_deadline = JanelaTemporal(
                    pedido_id=pedido_data.id_pedido,
                    datetime_inicio=inicio_para_deadline,
                    datetime_fim=deadline,
                    viavel=True
                )
                janelas.append(janela_deadline)
            else:
                print(f"      ❌ Impossível terminar no deadline")
        
        # ✅ Gera janelas adicionais em intervalos da resolução
        resolucao_delta = timedelta(minutes=self.resolucao_minutos)
        inicio_atual = inicio_mais_cedo
        
        while inicio_atual <= inicio_mais_tarde:
            fim_atual = inicio_atual + pedido_data.duracao_total
            
            # Verifica se está dentro dos limites
            if fim_atual <= pedido_data.fim_jornada:
                janela = JanelaTemporal(
                    pedido_id=pedido_data.id_pedido,
                    datetime_inicio=inicio_atual,
                    datetime_fim=fim_atual,
                    viavel=True
                )
                
                # ✅ Evita duplicatas (importante para fins obrigatórios)
                if not any(j.datetime_inicio == janela.datetime_inicio and 
                          j.datetime_fim == janela.datetime_fim for j in janelas):
                    janelas.append(janela)
            
            # Avança para próximo slot
            inicio_atual += resolucao_delta
        
        print(f"      ✅ {len(janelas)} janelas totais geradas")
        
        # Mostra exemplos
        if janelas:
            print(f"      📋 Exemplos (primeiras 3):")
            for i, janela in enumerate(janelas[:3]):
                inicio_str = janela.datetime_inicio.strftime('%d/%m %H:%M')
                fim_str = janela.datetime_fim.strftime('%d/%m %H:%M')
                print(f"         {i+1}. {inicio_str} → {fim_str}")
            
            if len(janelas) > 3:
                print(f"         ... e mais {len(janelas) - 3} janelas")
        
        return janelas
    
    def _configurar_horizonte_temporal_simples(self, dados_pedidos: List):
        """
        ✅ COMPATIBILIDADE: Configura horizonte temporal para o modelo PL
        """
        from dataclasses import dataclass
        
        @dataclass
        class ConfiguracaoTempo:
            inicio_horizonte: datetime
            fim_horizonte: datetime
            resolucao_minutos: int
            total_periodos: int = 0
        
        # Calcula limites globais
        inicio_min = min(p.inicio_jornada for p in dados_pedidos)
        fim_max = max(p.fim_jornada for p in dados_pedidos)
        
        self.configuracao_tempo = ConfiguracaoTempo(
            inicio_horizonte=inicio_min,
            fim_horizonte=fim_max,
            resolucao_minutos=self.resolucao_minutos,
            total_periodos=0  # Não usado na versão simplificada
        )
        
        print(f"⏰ Horizonte temporal simplificado:")
        print(f"   Início: {inicio_min.strftime('%d/%m/%Y %H:%M')}")
        print(f"   Fim: {fim_max.strftime('%d/%m/%Y %H:%M')}")
        print(f"   Resolução: {self.resolucao_minutos} minutos")
    
    def obter_estatisticas(self) -> Dict:
        """Retorna estatísticas das janelas geradas"""
        if not self.janelas_por_pedido:
            return {
                'total_pedidos': 0,
                'total_janelas': 0,
                'janelas_viaveis': 0,
                'logs_debug': self.logs_debug
            }
        
        total_janelas = sum(len(janelas) for janelas in self.janelas_por_pedido.values())
        janelas_viaveis = sum(
            sum(1 for j in janelas if j.viavel) 
            for janelas in self.janelas_por_pedido.values()
        )
        
        return {
            'total_pedidos': len(self.janelas_por_pedido),
            'total_janelas': total_janelas,
            'janelas_viaveis': janelas_viaveis,
            'taxa_viabilidade': janelas_viaveis / total_janelas if total_janelas > 0 else 0,
            'janelas_por_pedido': {
                pedido_id: len(janelas) 
                for pedido_id, janelas in self.janelas_por_pedido.items()
            },
            'pedidos_com_fim_obrigatorio': len(self.pedidos_com_fim_obrigatorio),
            'logs_debug': self.logs_debug
        }
    
    def imprimir_resumo(self):
        """Imprime resumo legível das janelas geradas"""
        print("\n" + "="*60)
        print("⏰ RESUMO DAS JANELAS TEMPORAIS FINAIS")
        print("="*60)
        
        stats = self.obter_estatisticas()
        
        print(f"📊 Total de pedidos: {stats['total_pedidos']}")
        print(f"📊 Total de janelas: {stats['total_janelas']:,}")
        print(f"📊 Janelas viáveis: {stats['janelas_viaveis']:,}")
        print(f"🎯 Pedidos com fim obrigatório: {stats['pedidos_com_fim_obrigatorio']}")
        
        if stats['total_janelas'] > 0:
            print(f"📊 Taxa de viabilidade: {stats['taxa_viabilidade']:.1%}")
        
        print(f"\n📋 Janelas por pedido:")
        if stats['janelas_por_pedido']:
            for pedido_id, total_janelas in stats['janelas_por_pedido'].items():
                if pedido_id in self.janelas_por_pedido:
                    janelas_viaveis = sum(1 for j in self.janelas_por_pedido[pedido_id] if j.viavel)
                    tipo = "OBRIGATÓRIO" if pedido_id in self.pedidos_com_fim_obrigatorio else "FLEXÍVEL"
                    taxa = janelas_viaveis / total_janelas if total_janelas > 0 else 0
                    print(f"   Pedido {pedido_id} ({tipo}): {janelas_viaveis:,}/{total_janelas:,} viáveis ({taxa:.1%})")
        
        if stats['logs_debug']:
            print(f"\n⚠️ Avisos/Erros ({len(stats['logs_debug'])}):")
            for i, log in enumerate(stats['logs_debug'][:5]):
                print(f"   • {log}")
            if len(stats['logs_debug']) > 5:
                print(f"   • ... e mais {len(stats['logs_debug']) - 5} avisos")
        
        print("="*60)
    
    def obter_janelas_para_pl(self) -> Dict[int, List[Tuple[datetime, datetime]]]:
        """
        ✅ FINAL: Retorna janelas no formato datetime para o modelo PL
        """
        janelas_pl = {}
        
        for pedido_id, janelas in self.janelas_por_pedido.items():
            janelas_viaveis = [j for j in janelas if j.viavel]
            janelas_pl[pedido_id] = [
                (j.datetime_inicio, j.datetime_fim) for j in janelas_viaveis
            ]
        
        return janelas_pl
    
    def obter_janelas_para_pl_compativel(self) -> Tuple[Dict[int, List[int]], Dict[int, List[int]]]:
        """
        ✅ COMPATIBILIDADE: Retorna no formato que o modelo PL original esperava
        Mas usando índices simples ao invés de períodos complexos
        """
        periodos_inicio = {}
        periodos_fim = {}
        
        for pedido_id, janelas in self.janelas_por_pedido.items():
            janelas_viaveis = [j for j in janelas if j.viavel]
            
            # Usa índices simples (0, 1, 2...) ao invés de períodos calculados
            periodos_inicio[pedido_id] = list(range(len(janelas_viaveis)))
            periodos_fim[pedido_id] = list(range(len(janelas_viaveis)))
        
        return periodos_inicio, periodos_fim


def testar_gerador_final():
    """Teste da versão final"""
    print("🧪 Testando GeradorJanelasTemporais FINAL...")
    
    # Dados exatos do problema
    from dataclasses import dataclass
    from typing import List
    
    @dataclass
    class DadosPedidoTeste:
        id_pedido: int
        nome_produto: str
        quantidade: int
        inicio_jornada: datetime
        fim_jornada: datetime
        duracao_total: timedelta
        atividades: List = None
    
    # Teste com dois pedidos (cenário do erro original)
    data_base = datetime(2025, 6, 26, 7, 0)
    inicio_base = data_base - timedelta(days=3)
    
    dados_pedidos = [
        DadosPedidoTeste(
            id_pedido=1,
            nome_produto="pao_frances",
            quantidade=450,
            inicio_jornada=inicio_base,
            fim_jornada=data_base,
            duracao_total=timedelta(hours=4, minutes=25),
            atividades=[]
        ),
        DadosPedidoTeste(
            id_pedido=2,
            nome_produto="pao_hamburguer",
            quantidade=120,
            inicio_jornada=inicio_base,
            fim_jornada=data_base,
            duracao_total=timedelta(hours=3, minutes=30),
            atividades=[]
        )
    ]
    
    # Define fins obrigatórios
    pedidos_com_fim_obrigatorio = {
        1: data_base,
        2: data_base
    }
    
    print(f"\n📋 Testando com {len(dados_pedidos)} pedidos:")
    for pedido in dados_pedidos:
        print(f"   {pedido.nome_produto}: {pedido.duracao_total} (deadline: {data_base.strftime('%H:%M')})")
    
    # Testa gerador final
    gerador = GeradorJanelasTemporais(resolucao_minutos=30)
    janelas = gerador.gerar_janelas_todos_pedidos(dados_pedidos, pedidos_com_fim_obrigatorio)
    
    # Mostra resultado
    gerador.imprimir_resumo()
    
    # Validação
    sucesso = True
    for pedido_id in [1, 2]:
        if pedido_id not in janelas or len(janelas[pedido_id]) == 0:
            print(f"\n❌ FALHA: Pedido {pedido_id} sem janelas!")
            sucesso = False
        else:
            janelas_viaveis = [j for j in janelas[pedido_id] if j.viavel]
            print(f"\n✅ Pedido {pedido_id}: {len(janelas_viaveis)} janelas viáveis")
            
            # Verifica se há janela para deadline
            deadline_encontrado = any(
                j.datetime_fim == data_base for j in janelas_viaveis
            )
            if deadline_encontrado:
                print(f"   🎯 Janela para deadline encontrada!")
            else:
                print(f"   ⚠️ Nenhuma janela termina no deadline")
    
    if sucesso:
        print(f"\n🎉 GERADOR FINAL FUNCIONOU!")
        print(f"✅ Pronto para múltiplos pedidos com conflitos")
        return True
    else:
        print(f"\n❌ GERADOR FINAL FALHOU!")
        return False


if __name__ == "__main__":
    testar_gerador_final()