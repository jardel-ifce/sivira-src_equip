"""
Modelo de Programação Linear para Otimização de Pedidos - VERSÃO FINAL
======================================================================

✅ CORRIGIDO: Funciona com gerador simplificado usando datetime direto
✅ CORRIGIDO: Não usa mais atributos de períodos inexistentes
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
    Modelo de Programação Linear para maximizar pedidos atendidos.
    ✅ VERSÃO FINAL compatível com gerador simplificado.
    
    Variáveis de decisão:
    - x[p,j] = 1 se pedido p usa janela j, 0 caso contrário
    
    Função objetivo:
    - maximize ∑ ∑ x[p,j] for all p,j
    
    Restrições:
    - ∑ x[p,j] ≤ 1 for all p (cada pedido usa no máximo uma janela)
    - Conflitos de equipamentos entre janelas
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
        
        # Resultados
        self.solucao = None
        self.logs_debug = []
        
        print(f"🔧 Modelo PL inicializado:")
        print(f"   Pedidos: {len(dados_pedidos)}")
        print(f"   Janelas totais: {sum(len(j) for j in janelas_por_pedido.values())}")
    
    def resolver(self, timeout_segundos: int = 300) -> SolucaoPL:
        """
        Resolve o modelo de programação linear.
        
        Args:
            timeout_segundos: Tempo limite para resolução
            
        Returns:
            SolucaoPL com a solução ótima
        """
        print(f"🚀 Resolvendo modelo PL (timeout: {timeout_segundos}s)...")
        inicio = time.time()
        
        try:
            # 1. Cria solver
            self._criar_solver()
            
            # 2. Cria variáveis de decisão
            self._criar_variaveis()
            
            # 3. Define função objetivo
            self._definir_funcao_objetivo()
            
            # 4. Adiciona restrições
            self._adicionar_restricoes()
            
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
        """Cria o solver SCIP (padrão do OR-Tools)"""
        self.solver = pywraplp.Solver.CreateSolver('SCIP')
        
        if not self.solver:
            raise RuntimeError("Não foi possível criar solver SCIP")
        
        print(f"✅ Solver SCIP criado")
    
    def _criar_variaveis(self):
        """Cria variáveis de decisão x[pedido_id, janela_index]"""
        print(f"🔧 Criando variáveis de decisão...")
        
        total_variaveis = 0
        
        for pedido_id, janelas in self.janelas_por_pedido.items():
            for janela_index, janela in enumerate(janelas):
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
    
    def _adicionar_restricoes(self):
        """Adiciona todas as restrições do modelo"""
        print(f"⚖️ Adicionando restrições...")
        
        # 1. Cada pedido usa no máximo uma janela
        self._restricoes_um_pedido_uma_janela()
        
        # 2. Conflitos de equipamentos
        self._restricoes_conflitos_equipamentos()
        
        print(f"✅ Restrições adicionadas")
    
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
    
    def _restricoes_conflitos_equipamentos(self):
        """✅ CORRIGIDO: Evita conflitos usando datetime direto"""
        print(f"   🔍 Analisando conflitos de equipamentos...")
        
        restricoes_adicionadas = 0
        conflitos_detectados = 0
        
        # Para cada par de janelas de pedidos diferentes
        pedidos_ids = list(self.janelas_por_pedido.keys())
        
        for i, pedido_id1 in enumerate(pedidos_ids):
            for j, pedido_id2 in enumerate(pedidos_ids[i+1:], i+1):
                
                janelas1 = self.janelas_por_pedido[pedido_id1]
                janelas2 = self.janelas_por_pedido[pedido_id2]
                
                for idx1, janela1 in enumerate(janelas1):
                    for idx2, janela2 in enumerate(janelas2):
                        
                        if not (janela1.viavel and janela2.viavel):
                            continue
                        
                        # ✅ CORRIGIDO: Verifica sobreposição temporal usando datetime
                        if self._janelas_se_sobrepoem(janela1, janela2):
                            # Se há conflito de equipamentos, adiciona restrição
                            if self._janelas_conflitam_equipamentos(pedido_id1, pedido_id2):
                                self._adicionar_restricao_conflito(
                                    pedido_id1, idx1, pedido_id2, idx2
                                )
                                restricoes_adicionadas += 1
                                conflitos_detectados += 1
        
        print(f"   ⚔️ {conflitos_detectados} conflitos detectados")
        print(f"   📋 {restricoes_adicionadas} restrições de conflito adicionadas")
    
    def _janelas_se_sobrepoem(self, janela1, janela2) -> bool:
        """✅ CORRIGIDO: Verifica sobreposição usando datetime direto"""
        return not (janela1.datetime_fim <= janela2.datetime_inicio or 
                   janela2.datetime_fim <= janela1.datetime_inicio)
    
    def _janelas_conflitam_equipamentos(self, pedido_id1: int, pedido_id2: int) -> bool:
        """
        Verifica se dois pedidos usam equipamentos em comum.
        
        Simplificação: assume que todos os pedidos conflitam entre si
        pois usam equipamentos compartilhados (bancadas, fornos, etc.)
        """
        # Em implementação completa, compararia listas de equipamentos
        return True  # Conservativo: assume conflito sempre
    
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
        """Extrai solução viável do solver"""
        
        objetivo_otimo = self.solver.Objective().Value()
        pedidos_selecionados = {}
        janelas_selecionadas = {}
        
        print(f"🎯 Valor objetivo ótimo: {objetivo_otimo}")
        print(f"📋 Pedidos atendidos:")
        
        # Extrai variáveis com valor 1
        for (pedido_id, janela_index), var in self.variaveis_x.items():
            if var.solution_value() > 0.5:  # Considera 1
                pedidos_selecionados[pedido_id] = janela_index
                janela = self.janelas_por_pedido[pedido_id][janela_index]
                janelas_selecionadas[pedido_id] = janela
                
                inicio_str = janela.datetime_inicio.strftime('%d/%m %H:%M')
                fim_str = janela.datetime_fim.strftime('%d/%m %H:%M')
                nome_produto = self.pedidos_por_id[pedido_id].nome_produto
                
                print(f"   ✅ Pedido {pedido_id} ({nome_produto}): {inicio_str} → {fim_str}")
        
        # Estatísticas
        estatisticas = {
            'total_variaveis': len(self.variaveis_x),
            'total_restricoes': self.solver.NumConstraints(),
            'pedidos_totais': len(self.dados_pedidos),
            'pedidos_atendidos': len(pedidos_selecionados),
            'taxa_atendimento': len(pedidos_selecionados) / len(self.dados_pedidos),
            'tempo_resolucao': tempo_resolucao
        }
        
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
        print("📊 ESTATÍSTICAS DO MODELO PL")
        print("="*60)
        print(f"🔧 Variáveis de decisão: {len(self.variaveis_x):,}")
        print(f"⚖️ Restrições: {self.solver.NumConstraints():,}")
        print(f"📋 Pedidos: {len(self.dados_pedidos)}")
        print(f"⏰ Janelas totais: {sum(len(j) for j in self.janelas_por_pedido.values()):,}")
        
        # Estatísticas por pedido
        print(f"\n📋 Janelas por pedido:")
        for pedido_id, janelas in self.janelas_por_pedido.items():
            janelas_viaveis = sum(1 for j in janelas if j.viavel)
            nome_produto = self.pedidos_por_id[pedido_id].nome_produto
            print(f"   Pedido {pedido_id} ({nome_produto}): {janelas_viaveis:,} janelas")
        
        print("="*60)


def testar_modelo_pl():
    """Teste básico do modelo PL com dados mock"""
    
    if not ORTOOLS_DISPONIVEL:
        print("❌ OR-Tools não disponível. Execute: pip install ortools")
        return
    
    print("🧪 Testando Modelo PL...")
    
    # Importa classes necessárias
    from extrator_dados_pedidos import ExtratorDadosPedidos
    
    # Usa dados mock simples para teste rápido
    class MockAtividade:
        def __init__(self, id_atividade, nome, duracao_min):
            self.id_atividade = id_atividade
            self.nome_atividade = nome
            self.duracao = timedelta(minutes=duracao_min)
            self.equipamentos_elegiveis = [f"equipamento_{id_atividade}"]
            self.tempo_maximo_de_espera = timedelta(0)
    
    class MockPedido:
        def __init__(self, id_pedido, id_produto, nome):
            self.id_pedido = id_pedido
            self.id_produto = id_produto
            self.quantidade = 100
            self.inicio_jornada = datetime(2025, 6, 26, 0, 0)  # Janela menor para teste
            self.fim_jornada = datetime(2025, 6, 26, 8, 0)    # 8h total
            
            self.atividades_modulares = [
                MockAtividade(f"{id_produto}1", f"atividade1_{nome}", 60),  # 1h
                MockAtividade(f"{id_produto}2", f"atividade2_{nome}", 60)   # 1h
            ]
            
            class MockFicha:
                def __init__(self, nome):
                    self.nome = nome
            
            self.ficha_tecnica_modular = MockFicha(nome)
    
    # Cria pedidos mock
    pedidos_mock = [
        MockPedido(1, 1001, "produto1"),
        MockPedido(2, 1002, "produto2")
    ]
    
    # 1. Extrai dados
    extrator = ExtratorDadosPedidos()
    dados_extraidos = extrator.extrair_dados(pedidos_mock)
    
    # 2. Gera janelas (resolução maior para teste rápido)
    gerador = GeradorJanelasTemporais(resolucao_minutos=30)
    janelas = gerador.gerar_janelas_todos_pedidos(dados_extraidos)
    
    # 3. Cria e resolve modelo PL
    modelo = ModeloPLOtimizador(dados_extraidos, janelas, gerador.configuracao_tempo)
    modelo.imprimir_estatisticas_modelo()
    
    # 4. Resolve
    solucao = modelo.resolver(timeout_segundos=30)
    
    # 5. Mostra resultado
    print(f"\n🎉 RESULTADO:")
    print(f"   Pedidos atendidos: {solucao.pedidos_atendidos}/{len(dados_extraidos)}")
    print(f"   Status: {solucao.status_solver}")
    print(f"   Tempo: {solucao.tempo_resolucao:.2f}s")
    
    return solucao


if __name__ == "__main__":
    testar_modelo_pl()