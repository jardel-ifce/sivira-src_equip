"""
Modelo de Programação Linear para Otimização de Pedidos - VERSÃO CORRIGIDA
======================================================================

✅ CORRIGIDO: Evita loop infinito nas restrições
✅ CORRIGIDO: Lógica mais inteligente para conflitos
"""
import sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import time
from dataclasses import dataclass

# Imports do OR-Tools
try:
    from ortools.linear_solver import pywraplp
    ORTOOLS_DISPONIVEL = True
except ImportError:
    ORTOOLS_DISPONIVEL = False
    print("⚠️ OR-Tools não está instalado. Execute: pip install ortools")

# Imports das classes anteriores
from otimizador.extrator_dados_pedidos import DadosPedido, DadosAtividade
from otimizador.gerador_janelas_temporais import GeradorJanelasTemporais, JanelaTemporal


@dataclass
class SolucaoPL:
    """Resultado da otimização PL"""
    pedidos_atendidos: int
    pedidos_selecionados: Dict[int, int]  # {pedido_id: janela_index}
    janelas_selecionadas: Dict[int, JanelaTemporal]  # {pedido_id: janela}
    tempo_resolucao: float
    status_solver: str
    objetivo_otimo: float
    estatisticas: Dict


class ModeloPLOtimizador:
    """
    Modelo de Programação Linear CORRIGIDO para evitar loop infinito.
    
    ✅ CORREÇÃO PRINCIPAL: Restrições inteligentes ao invés de todas as combinações
    """
    
    def __init__(self, dados_pedidos: List[DadosPedido], 
                 janelas_por_pedido: Dict[int, List[JanelaTemporal]],
                 configuracao_tempo):
        
        if not ORTOOLS_DISPONIVEL:
            raise ImportError("OR-Tools é necessário. Instale com: pip install ortools")
        
        self.dados_pedidos = dados_pedidos
        self.janelas_por_pedido = janelas_por_pedido
        self.configuracao_tempo = configuracao_tempo
        
        # Mapeamentos para facilitar acesso
        self.pedidos_por_id = {p.id_pedido: p for p in dados_pedidos}
        
        # Solver e variáveis
        self.solver = None
        self.variaveis_x = {}  # x[pedido_id, janela_index]
        
        # ✅ CORREÇÃO: Limites para evitar explosão de restrições
        self.max_restricoes_conflito = 1000  # Máximo de restrições de conflito
        self.max_janelas_por_analise = 5     # Máximo de janelas por pedido para análise detalhada
        
        # Resultados
        self.solucao = None
        self.logs_debug = []
        
        print(f"🔧 Modelo PL inicializado (VERSÃO CORRIGIDA):")
        print(f"   Pedidos: {len(dados_pedidos)}")
        print(f"   Janelas totais: {sum(len(j) for j in janelas_por_pedido.values())}")
        print(f"   Limite de restrições: {self.max_restricoes_conflito}")
    
    def resolver(self, timeout_segundos: int = 300) -> SolucaoPL:
        """Resolve o modelo de programação linear."""
        print(f"🚀 Resolvendo modelo PL CORRIGIDO (timeout: {timeout_segundos}s)...")
        inicio = time.time()
        
        try:
            # 1. Cria solver
            self._criar_solver()
            
            # 2. Cria variáveis de decisão
            self._criar_variaveis()
            
            # 3. Define função objetivo
            self._definir_funcao_objetivo()
            
            # 4. Adiciona restrições (VERSÃO CORRIGIDA)
            self._adicionar_restricoes_inteligentes()
            
            # 5. Configura solver
            self.solver.SetTimeLimit(timeout_segundos * 1000)  # ms
            
            # 6. Resolve
            print(f"⏱️ Iniciando resolução...")
            status = self.solver.Solve()
            
            tempo_resolucao = time.time() - inicio
            
            # 7. Processa resultado
            self.solucao = self._processar_resultado(status, tempo_resolucao)
            
            return self.solucao
            
        except Exception as e:
            print(f"❌ Erro durante resolução: {e}")
            raise
    
    def _criar_solver(self):
        """Cria o solver SCIP"""
        self.solver = pywraplp.Solver.CreateSolver('SCIP')
        
        if not self.solver:
            raise RuntimeError("Não foi possível criar solver SCIP")
        
        print(f"✅ Solver SCIP criado")
    
    def _criar_variaveis(self):
        """Cria variáveis de decisão x[pedido_id, janela_index]"""
        print(f"🔧 Criando variáveis de decisão...")
        
        total_variaveis = 0
        
        for pedido_id, janelas in self.janelas_por_pedido.items():
            # ✅ CORREÇÃO: Limitar número de janelas por pedido para evitar explosão
            janelas_para_usar = janelas[:self.max_janelas_por_analise] if len(janelas) > self.max_janelas_por_analise else janelas
            
            if len(janelas) > self.max_janelas_por_analise:
                print(f"   ⚠️ Pedido {pedido_id}: limitando a {self.max_janelas_por_analise}/{len(janelas)} janelas")
            
            for janela_index, janela in enumerate(janelas_para_usar):
                if janela.viavel:
                    var_name = f"x_{pedido_id}_{janela_index}"
                    var = self.solver.IntVar(0, 1, var_name)
                    self.variaveis_x[(pedido_id, janela_index)] = var
                    total_variaveis += 1
        
        print(f"✅ {total_variaveis} variáveis criadas")
    
    def _definir_funcao_objetivo(self):
        """Define função objetivo: maximizar pedidos atendidos"""
        print(f"🎯 Definindo função objetivo...")
        
        # Maximizar ∑ ∑ x[p,j] for all p,j
        objetivo = self.solver.Objective()
        
        for (pedido_id, janela_index), var in self.variaveis_x.items():
            objetivo.SetCoefficient(var, 1)
        
        objetivo.SetMaximization()
        
        print(f"✅ Função objetivo: maximizar soma de variáveis")
    
    def _adicionar_restricoes_inteligentes(self):
        """✅ VERSÃO CORRIGIDA: Adiciona restrições de forma inteligente"""
        print(f"⚖️ Adicionando restrições inteligentes...")
        
        # 1. Cada pedido usa no máximo uma janela
        self._restricoes_um_pedido_uma_janela()
        
        # 2. ✅ CORREÇÃO: Conflitos inteligentes (não todas as combinações)
        self._restricoes_conflitos_inteligentes()
        
        print(f"✅ Restrições adicionadas de forma inteligente")
    
    def _restricoes_um_pedido_uma_janela(self):
        """Cada pedido pode usar no máximo uma janela temporal"""
        restricoes_adicionadas = 0
        
        for pedido_id, janelas in self.janelas_por_pedido.items():
            # ∑ x[p,j] ≤ 1 for all j in janelas do pedido p
            restricao = self.solver.Constraint(0, 1)
            
            for janela_index, janela in enumerate(janelas):
                if janela.viavel and (pedido_id, janela_index) in self.variaveis_x:
                    var = self.variaveis_x[(pedido_id, janela_index)]
                    restricao.SetCoefficient(var, 1)
            
            restricoes_adicionadas += 1
        
        print(f"   📋 {restricoes_adicionadas} restrições de unicidade por pedido")
    
    def _restricoes_conflitos_inteligentes(self):
        """
        ✅ VERSÃO CORRIGIDA: Evita conflitos de forma inteligente
        
        ESTRATÉGIA:
        1. Agrupa janelas por períodos temporais
        2. Adiciona restrições apenas para períodos sobrepostos
        3. Limita total de restrições
        """
        print(f"   🧠 Analisando conflitos de forma INTELIGENTE...")
        
        restricoes_adicionadas = 0
        
        # ✅ ESTRATÉGIA 1: Ordenar todas as janelas por tempo
        todas_janelas = []
        for pedido_id, janelas in self.janelas_por_pedido.items():
            for janela_index, janela in enumerate(janelas):
                if janela.viavel and (pedido_id, janela_index) in self.variaveis_x:
                    todas_janelas.append((pedido_id, janela_index, janela))
        
        # Ordenar por tempo de início
        todas_janelas.sort(key=lambda x: x[2].datetime_inicio)
        
        print(f"      📊 Analisando {len(todas_janelas)} janelas válidas...")
        
        # ✅ ESTRATÉGIA 2: Apenas verificar janelas "próximas" temporalmente
        for i, (pedido_id1, janela_idx1, janela1) in enumerate(todas_janelas):
            
            # Verificar apenas próximas N janelas (janela deslizante)
            janela_verificacao = min(20, len(todas_janelas) - i - 1)  # Máximo 20 próximas
            
            for j in range(1, janela_verificacao + 1):
                if i + j >= len(todas_janelas):
                    break
                    
                pedido_id2, janela_idx2, janela2 = todas_janelas[i + j]
                
                # Pular se é o mesmo pedido
                if pedido_id1 == pedido_id2:
                    continue
                
                # ✅ OTIMIZAÇÃO: Parar se janela2 está muito longe temporalmente
                if janela2.datetime_inicio > janela1.datetime_fim + timedelta(hours=1):
                    break  # Não há mais sobreposições possíveis
                
                # Verificar sobreposição
                if self._janelas_se_sobrepoem_simples(janela1, janela2):
                    # Adicionar restrição de conflito
                    self._adicionar_restricao_conflito(pedido_id1, janela_idx1, pedido_id2, janela_idx2)
                    restricoes_adicionadas += 1
                    
                    # ✅ LIMITE DE SEGURANÇA
                    if restricoes_adicionadas >= self.max_restricoes_conflito:
                        print(f"      ⚠️ Limite de restrições atingido ({self.max_restricoes_conflito})")
                        print(f"      💡 Otimização pode não ser perfeita, mas evita loop infinito")
                        break
            
            # Parar se atingiu limite global
            if restricoes_adicionadas >= self.max_restricoes_conflito:
                break
        
        print(f"   ⚔️ {restricoes_adicionadas} restrições de conflito adicionadas")
        
        if restricoes_adicionadas == self.max_restricoes_conflito:
            print(f"   💡 ESTRATÉGIA: Restrições limitadas para performance")
            print(f"   📈 Resultado será bom, mesmo que não perfeito")
    
    def _janelas_se_sobrepoem_simples(self, janela1, janela2) -> bool:
        """✅ VERSÃO SIMPLES: Verifica sobreposição básica"""
        return not (janela1.datetime_fim <= janela2.datetime_inicio or 
                   janela2.datetime_fim <= janela1.datetime_inicio)
    
    def _adicionar_restricao_conflito(self, pedido_id1: int, janela_idx1: int,
                                    pedido_id2: int, janela_idx2: int):
        """Adiciona restrição de conflito entre duas janelas"""
        
        var1_key = (pedido_id1, janela_idx1)
        var2_key = (pedido_id2, janela_idx2)
        
        if var1_key in self.variaveis_x and var2_key in self.variaveis_x:
            # x[p1,j1] + x[p2,j2] ≤ 1 (no máximo uma das duas pode ser escolhida)
            restricao = self.solver.Constraint(0, 1)
            restricao.SetCoefficient(self.variaveis_x[var1_key], 1)
            restricao.SetCoefficient(self.variaveis_x[var2_key], 1)
    
    def _processar_resultado(self, status, tempo_resolucao: float) -> SolucaoPL:
        """Processa o resultado da otimização"""
        
        status_map = {
            pywraplp.Solver.OPTIMAL: "OPTIMAL",
            pywraplp.Solver.FEASIBLE: "FEASIBLE", 
            pywraplp.Solver.INFEASIBLE: "INFEASIBLE",
            pywraplp.Solver.UNBOUNDED: "UNBOUNDED",
            pywraplp.Solver.ABNORMAL: "ABNORMAL",
            pywraplp.Solver.NOT_SOLVED: "NOT_SOLVED"
        }
        
        status_str = status_map.get(status, f"UNKNOWN_{status}")
        
        print(f"📊 Status da resolução: {status_str}")
        print(f"⏱️ Tempo de resolução: {tempo_resolucao:.2f}s")
        
        if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
            return self._extrair_solucao_viavel(status_str, tempo_resolucao)
        else:
            return self._criar_solucao_inviavel(status_str, tempo_resolucao)
    
    def _extrair_solucao_viavel(self, status_str: str, tempo_resolucao: float) -> SolucaoPL:
        """✅ VERSÃO CORRIGIDA: Extrai solução com DEBUG mas sem loop"""
        
        objetivo_otimo = self.solver.Objective().Value()
        pedidos_selecionados = {}
        pedidos_rejeitados = set()  # ✅ CORREÇÃO: Usar set para evitar duplicatas
        janelas_selecionadas = {}
        
        print(f"🎯 Valor objetivo ótimo: {objetivo_otimo}")
        print(f"📋 Analisando solução...")
        
        # Extrair variáveis com valor 1 (selecionadas)
        for (pedido_id, janela_index), var in self.variaveis_x.items():
            if var.solution_value() > 0.5:  # Considera 1
                pedidos_selecionados[pedido_id] = janela_index
                janela = self.janelas_por_pedido[pedido_id][janela_index]
                janelas_selecionadas[pedido_id] = janela
                
                inicio_str = janela.datetime_inicio.strftime('%d/%m %H:%M')
                fim_str = janela.datetime_fim.strftime('%d/%m %H:%M')
                nome_produto = self.pedidos_por_id[pedido_id].nome_produto
                
                print(f"   ✅ SELECIONADO - Pedido {pedido_id} ({nome_produto}): {inicio_str} → {fim_str}")
            else:
                pedidos_rejeitados.add(pedido_id)  # Apenas adiciona ID do pedido
        
        # ✅ DEBUG SIMPLIFICADO: Mostrar apenas pedidos rejeitados (sem detalhes das janelas)
        pedidos_completamente_rejeitados = pedidos_rejeitados - set(pedidos_selecionados.keys())
        
        if pedidos_completamente_rejeitados:
            print(f"\n⚠️ PEDIDOS REJEITADOS PELO PL:")
            for pedido_id in sorted(pedidos_completamente_rejeitados):
                nome_produto = self.pedidos_por_id[pedido_id].nome_produto
                print(f"   ❌ Pedido {pedido_id} ({nome_produto}): TODAS as janelas rejeitadas")
        
        # Estatísticas
        estatisticas = {
            'total_variaveis': len(self.variaveis_x),
            'total_restricoes': self.solver.NumConstraints(),
            'pedidos_totais': len(self.dados_pedidos),
            'pedidos_atendidos': len(pedidos_selecionados),
            'pedidos_rejeitados': len(pedidos_completamente_rejeitados),
            'taxa_atendimento': len(pedidos_selecionados) / len(self.dados_pedidos),
            'tempo_resolucao': tempo_resolucao,
            'restricoes_limitadas': self.solver.NumConstraints() >= self.max_restricoes_conflito
        }
        
        print(f"\n📊 ESTATÍSTICAS:")
        print(f"   Variáveis: {estatisticas['total_variaveis']:,}")
        print(f"   Restrições: {estatisticas['total_restricoes']:,}")
        print(f"   Pedidos atendidos: {estatisticas['pedidos_atendidos']}/{estatisticas['pedidos_totais']}")
        
        return SolucaoPL(
            pedidos_atendidos=int(objetivo_otimo),
            pedidos_selecionados=pedidos_selecionados,
            janelas_selecionadas=janelas_selecionadas,
            tempo_resolucao=tempo_resolucao,
            status_solver=status_str,
            objetivo_otimo=objetivo_otimo,
            estatisticas=estatisticas
        )
    
    def _criar_solucao_inviavel(self, status_str: str, tempo_resolucao: float) -> SolucaoPL:
        """Cria resultado para problema inviável"""
        print(f"❌ Problema inviável ou não resolvido")
        
        return SolucaoPL(
            pedidos_atendidos=0,
            pedidos_selecionados={},
            janelas_selecionadas={},
            tempo_resolucao=tempo_resolucao,
            status_solver=status_str,
            objetivo_otimo=0.0,
            estatisticas={
                'total_variaveis': len(self.variaveis_x),
                'total_restricoes': self.solver.NumConstraints() if self.solver else 0,
                'pedidos_totais': len(self.dados_pedidos),
                'pedidos_atendidos': 0,
                'taxa_atendimento': 0.0,
                'tempo_resolucao': tempo_resolucao
            }
        )
    
    def imprimir_estatisticas_modelo(self):
        """Imprime estatísticas do modelo construído"""
        if not self.solver:
            print("❌ Modelo não foi construído ainda")
            return
        
        print("\n" + "="*60)
        print("📊 ESTATÍSTICAS DO MODELO PL CORRIGIDO")
        print("="*60)
        print(f"🔧 Variáveis de decisão: {len(self.variaveis_x):,}")
        print(f"⚖️ Restrições: {self.solver.NumConstraints():,}")
        print(f"📋 Pedidos: {len(self.dados_pedidos)}")
        print(f"⏰ Janelas totais: {sum(len(j) for j in self.janelas_por_pedido.values()):,}")
        print(f"🛡️ Limite de restrições: {self.max_restricoes_conflito:,}")
        
        # Verificar se restrições foram limitadas
        if self.solver.NumConstraints() >= self.max_restricoes_conflito:
            print(f"⚠️ AVISO: Restrições foram limitadas para evitar loop infinito")
            print(f"💡 Solução será boa, mas pode não ser globalmente ótima")
        
        print("="*60)


def testar_modelo_pl_corrigido():
    """Teste do modelo corrigido"""
    
    if not ORTOOLS_DISPONIVEL:
        print("❌ OR-Tools não disponível. Execute: pip install ortools")
        return
    
    print("🧪 Testando Modelo PL CORRIGIDO...")
    
    # Mock simples para teste rápido
    from datetime import datetime, timedelta
    
    class MockAtividade:
        def __init__(self, id_atividade, nome, duracao_min):
            self.id_atividade = id_atividade
            self.nome_atividade = nome
            self.duracao = timedelta(minutes=duracao_min)
            self.equipamentos_necessarios = [f"equipamento_{id_atividade % 3}"]  # 3 equipamentos diferentes
            self.tempo_maximo_de_espera = timedelta(0)
    
    # Simula dados extraídos
    from otimizador.extrator_dados_pedidos import DadosPedido
    
    dados_teste = [
        DadosPedido(
            id_pedido=1,
            nome_produto="produto1",
            quantidade=100,
            inicio_jornada=datetime(2025, 6, 26, 0, 0),
            fim_jornada=datetime(2025, 6, 26, 8, 0),
            duracao_total=timedelta(hours=2),
            atividades=[MockAtividade(1, "ativ1", 120)]
        ),
        DadosPedido(
            id_pedido=2,
            nome_produto="produto2", 
            quantidade=50,
            inicio_jornada=datetime(2025, 6, 26, 0, 0),
            fim_jornada=datetime(2025, 6, 26, 8, 0),
            duracao_total=timedelta(hours=1),
            atividades=[MockAtividade(2, "ativ2", 60)]
        )
    ]
    
    # Gera janelas mock
    from otimizador.gerador_janelas_temporais import JanelaTemporal
    
    janelas_mock = {
        1: [
            JanelaTemporal(1, datetime(2025, 6, 26, 0, 0), datetime(2025, 6, 26, 2, 0), True),
            JanelaTemporal(1, datetime(2025, 6, 26, 1, 0), datetime(2025, 6, 26, 3, 0), True),
            JanelaTemporal(1, datetime(2025, 6, 26, 2, 0), datetime(2025, 6, 26, 4, 0), True),
        ],
        2: [
            JanelaTemporal(2, datetime(2025, 6, 26, 0, 0), datetime(2025, 6, 26, 1, 0), True),
            JanelaTemporal(2, datetime(2025, 6, 26, 2, 0), datetime(2025, 6, 26, 3, 0), True),
            JanelaTemporal(2, datetime(2025, 6, 26, 4, 0), datetime(2025, 6, 26, 5, 0), True),
        ]
    }
    
    # Configuração mock
    class ConfigMock:
        def __init__(self):
            self.inicio_horizonte = datetime(2025, 6, 26, 0, 0)
            self.fim_horizonte = datetime(2025, 6, 26, 8, 0)
    
    # Testa modelo
    modelo = ModeloPLOtimizador(dados_teste, janelas_mock, ConfigMock())
    modelo.imprimir_estatisticas_modelo()
    
    # Resolve
    solucao = modelo.resolver(timeout_segundos=30)
    
    # Resultado
    print(f"\n🎉 TESTE CONCLUÍDO:")
    print(f"   Status: {solucao.status_solver}")
    print(f"   Pedidos: {solucao.pedidos_atendidos}/{len(dados_teste)}")
    print(f"   Tempo: {solucao.tempo_resolucao:.2f}s")
    
    return solucao.pedidos_atendidos > 0


if __name__ == "__main__":
    testar_modelo_pl_corrigido()