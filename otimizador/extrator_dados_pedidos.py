"""
Extrator de Dados dos Pedidos para Otimização - VERSÃO OTIMIZADA
===============================================================

✅ OTIMIZADO: Extração mais eficiente de equipamentos
✅ CORRIGIDO: Evita equipamentos duplicados desnecessários
"""
import sys
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass


@dataclass
class DadosAtividade:
    """Dados de uma atividade individual"""
    id_atividade: int
    nome: str
    duracao: timedelta
    equipamentos_necessarios: List[str]
    tempo_maximo_espera: timedelta
    ordem_execucao: int  # 0 = primeira, 1 = segunda, etc.


@dataclass
class DadosPedido:
    """Dados completos de um pedido para otimização"""
    id_pedido: int
    nome_produto: str
    quantidade: int
    inicio_jornada: datetime
    fim_jornada: datetime
    duracao_total: timedelta
    atividades: List[DadosAtividade]
    

class ExtratorDadosPedidos:
    """
    ✅ VERSÃO OTIMIZADA: Extrai dados de forma mais eficiente
    """
    
    def __init__(self):
        self.dados_extraidos = []
        self.equipamentos_unicos = set()
        self.logs_debug = []
        
        # ✅ CACHE para evitar reprocessamento
        self.cache_equipamentos = {}
        self.cache_duracao = {}
    
    def extrair_dados(self, pedidos) -> List[DadosPedido]:
        """
        Extrai dados de uma lista de PedidoDeProducao de forma otimizada.
        """
        self.dados_extraidos = []
        self.equipamentos_unicos = set()
        self.logs_debug = []
        
        print(f"🔄 Extraindo dados de {len(pedidos)} pedidos (VERSÃO OTIMIZADA)...")
        
        for pedido in pedidos:
            try:
                dados_pedido = self._extrair_pedido_individual(pedido)
                self.dados_extraidos.append(dados_pedido)
                print(f"✅ Pedido {pedido.id_pedido} extraído: {len(dados_pedido.atividades)} atividades, duração: {dados_pedido.duracao_total}")
                
            except Exception as e:
                print(f"❌ Erro ao extrair pedido {pedido.id_pedido}: {e}")
                self.logs_debug.append(f"Erro pedido {pedido.id_pedido}: {e}")
        
        print(f"📊 Extração concluída: {len(self.dados_extraidos)} pedidos, {len(self.equipamentos_unicos)} equipamentos únicos")
        return self.dados_extraidos
    
    def _extrair_pedido_individual(self, pedido) -> DadosPedido:
        """Extrai dados de um pedido individual de forma otimizada"""
        
        # Dados básicos do pedido
        dados_basicos = {
            'id_pedido': pedido.id_pedido,
            'nome_produto': self._obter_nome_produto(pedido),
            'quantidade': pedido.quantidade,
            'inicio_jornada': pedido.inicio_jornada,
            'fim_jornada': pedido.fim_jornada,
        }
        
        # ✅ OTIMIZAÇÃO: Usar cache para duração se disponível
        cache_key = f"{pedido.id_produto}_{pedido.quantidade}"
        if cache_key in self.cache_duracao:
            duracao_total = self.cache_duracao[cache_key]
            atividades_extraidas = self._criar_atividades_estimadas_cache(pedido)
            print(f"   🚀 Cache hit para duração do pedido {pedido.id_pedido}")
        else:
            # Extração normal
            atividades_extraidas = self._extrair_ou_criar_atividades(pedido)
            duracao_total = sum([a.duracao for a in atividades_extraidas], timedelta())
            
            # ✅ FALLBACK: Se duração for 0, estima baseado na quantidade
            if duracao_total == timedelta(0):
                duracao_total = self._estimar_duracao_por_produto(pedido)
                print(f"   🔧 Duração estimada para pedido {pedido.id_pedido}: {duracao_total}")
            
            # Salvar no cache
            self.cache_duracao[cache_key] = duracao_total
        
        return DadosPedido(
            **dados_basicos,
            duracao_total=duracao_total,
            atividades=atividades_extraidas
        )
    
    def _extrair_ou_criar_atividades(self, pedido) -> List[DadosAtividade]:
        """
        Extrai atividades do pedido ou cria atividades estimadas.
        """
        atividades_extraidas = []
        
        # TENTATIVA 1: Extrair de atividades_modulares (se existem)
        if hasattr(pedido, 'atividades_modulares') and pedido.atividades_modulares:
            print(f"   📋 Encontradas {len(pedido.atividades_modulares)} atividades modulares")
            atividades_extraidas = self._extrair_atividades_modulares(pedido.atividades_modulares)
        
        # TENTATIVA 2: Criar atividades forçando criação
        elif hasattr(pedido, 'criar_atividades_modulares_necessarias'):
            print(f"   🔧 Forçando criação de atividades modulares para pedido {pedido.id_pedido}")
            try:
                pedido.criar_atividades_modulares_necessarias()
                if hasattr(pedido, 'atividades_modulares') and pedido.atividades_modulares:
                    atividades_extraidas = self._extrair_atividades_modulares(pedido.atividades_modulares)
                    print(f"   ✅ Criadas {len(atividades_extraidas)} atividades")
                else:
                    print(f"   ⚠️ Atividades não foram criadas adequadamente")
            except Exception as e:
                print(f"   ❌ Erro ao criar atividades: {e}")
                self.logs_debug.append(f"Erro criação atividades pedido {pedido.id_pedido}: {e}")
        
        # FALLBACK: Criar atividades estimadas
        if not atividades_extraidas:
            print(f"   🆘 Criando atividades estimadas para pedido {pedido.id_pedido}")
            atividades_extraidas = self._criar_atividades_estimadas(pedido)
        
        return atividades_extraidas
    
    def _extrair_atividades_modulares(self, atividades_modulares) -> List[DadosAtividade]:
        """Extrai dados das atividades modulares existentes com otimização"""
        atividades_extraidas = []
        
        for i, atividade in enumerate(atividades_modulares):
            try:
                # ✅ OTIMIZAÇÃO: Cache de equipamentos por atividade
                cache_key = f"{getattr(atividade, 'id_atividade', i)}"
                if cache_key in self.cache_equipamentos:
                    equipamentos_necessarios = self.cache_equipamentos[cache_key]
                else:
                    equipamentos_necessarios = self._extrair_equipamentos_otimizado(atividade)
                    self.cache_equipamentos[cache_key] = equipamentos_necessarios
                
                dados_atividade = DadosAtividade(
                    id_atividade=getattr(atividade, 'id_atividade', f"ativ_{i}"),
                    nome=self._obter_nome_atividade(atividade),
                    duracao=getattr(atividade, 'duracao', timedelta(minutes=30)),
                    equipamentos_necessarios=equipamentos_necessarios,
                    tempo_maximo_espera=self._extrair_tempo_maximo_espera(atividade),
                    ordem_execucao=i
                )
                
                atividades_extraidas.append(dados_atividade)
                self.equipamentos_unicos.update(dados_atividade.equipamentos_necessarios)
                
            except Exception as e:
                self.logs_debug.append(f"Erro atividade {i}: {e}")
        
        return atividades_extraidas
    
    def _extrair_equipamentos_otimizado(self, atividade) -> List[str]:
        """✅ VERSÃO OTIMIZADA: Extrai equipamentos de forma mais eficiente"""
        equipamentos = set()  # Usar set para evitar duplicatas
        
        try:
            # Estratégia 1: Equipamentos elegíveis
            if hasattr(atividade, 'equipamentos_elegiveis') and atividade.equipamentos_elegiveis:
                for equipamento in atividade.equipamentos_elegiveis:
                    nome_equipamento = self._obter_nome_equipamento(equipamento)
                    if nome_equipamento:
                        equipamentos.add(nome_equipamento)
            
            # Estratégia 2: Tipos de equipamento (mais genérico)
            elif hasattr(atividade, '_quantidade_por_tipo_equipamento'):
                for tipo_eq in atividade._quantidade_por_tipo_equipamento.keys():
                    # ✅ SIMPLIFICAÇÃO: Usar categoria ao invés de equipamentos específicos
                    equipamentos.add(f"categoria_{tipo_eq.name.lower()}")
            
            # Fallback: Equipamento genérico baseado no ID da atividade
            if not equipamentos:
                equipamentos.add(f"equipamento_generico")
                
        except Exception as e:
            equipamentos.add(f"equipamento_erro")
        
        return list(equipamentos)
    
    def _criar_atividades_estimadas_cache(self, pedido) -> List[DadosAtividade]:
        """✅ VERSÃO CACHE: Cria atividades usando dados em cache"""
        nome_produto = self._obter_nome_produto(pedido)
        
        # Usar apenas 3 atividades genéricas para simplificar
        atividades_genericas = [
            DadosAtividade(
                id_atividade=f"{pedido.id_pedido}_preparo",
                nome="Preparação Geral",
                duracao=timedelta(minutes=30),
                equipamentos_necessarios=["categoria_bancadas"],
                tempo_maximo_espera=timedelta(minutes=10),
                ordem_execucao=0
            ),
            DadosAtividade(
                id_atividade=f"{pedido.id_pedido}_processamento",
                nome="Processamento Principal",
                duracao=timedelta(minutes=90),
                equipamentos_necessarios=["categoria_fornos", "categoria_misturadoras"],
                tempo_maximo_espera=timedelta(0),
                ordem_execucao=1
            ),
            DadosAtividade(
                id_atividade=f"{pedido.id_pedido}_finalizacao",
                nome="Finalização",
                duracao=timedelta(minutes=20),
                equipamentos_necessarios=["categoria_bancadas"],
                tempo_maximo_espera=timedelta(minutes=15),
                ordem_execucao=2
            )
        ]
        
        # Adicionar equipamentos ao conjunto global
        for atividade in atividades_genericas:
            self.equipamentos_unicos.update(atividade.equipamentos_necessarios)
        
        return atividades_genericas
    
    def _criar_atividades_estimadas(self, pedido) -> List[DadosAtividade]:
        """
        Cria atividades estimadas SIMPLIFICADAS baseadas no tipo de produto.
        """
        nome_produto = self._obter_nome_produto(pedido).lower()
        
        # ✅ SIMPLIFICAÇÃO: Todas as atividades usam equipamentos por categoria
        if any(palavra in nome_produto for palavra in ["frances", "francês"]):
            return self._criar_atividades_simplificadas(pedido, "pao_frances")
        elif any(palavra in nome_produto for palavra in ["hamburguer", "hambúrguer"]):
            return self._criar_atividades_simplificadas(pedido, "pao_hamburguer")
        elif "forma" in nome_produto:
            return self._criar_atividades_simplificadas(pedido, "pao_forma")
        elif "baguete" in nome_produto:
            return self._criar_atividades_simplificadas(pedido, "pao_baguete")
        elif any(palavra in nome_produto for palavra in ["tranca", "queijo"]):
            return self._criar_atividades_simplificadas(pedido, "pao_tranca")
        else:
            return self._criar_atividades_simplificadas(pedido, "generico")
    
    def _criar_atividades_simplificadas(self, pedido, tipo_produto: str) -> List[DadosAtividade]:
        """✅ Cria atividades simplificadas por categoria"""
        
        # Fator baseado na quantidade (limitado para evitar durações extremas)
        fator_quantidade = min(3.0, max(0.5, pedido.quantidade / 100))
        
        # ✅ TEMPLATE SIMPLIFICADO: 4 atividades genéricas
        template_atividades = [
            {
                "nome": "Preparação e Pesagem",
                "duracao_base": 20,
                "equipamentos": ["categoria_bancadas", "categoria_balancas"],
                "tempo_espera": 10
            },
            {
                "nome": "Mistura e Processamento",
                "duracao_base": 30,
                "equipamentos": ["categoria_misturadoras"],
                "tempo_espera": 5
            },
            {
                "nome": "Fermentação e Modelagem",
                "duracao_base": 120,  # Tempo fixo
                "equipamentos": ["categoria_armarios_fermentacao", "categoria_bancadas"],
                "tempo_espera": 0
            },
            {
                "nome": "Cocção e Finalização",
                "duracao_base": 40,
                "equipamentos": ["categoria_fornos"],
                "tempo_espera": 0
            }
        ]
        
        atividades_criadas = []
        
        for i, template in enumerate(template_atividades):
            # Calcular duração (fermentação não escala com quantidade)
            if "Fermentação" in template["nome"]:
                duracao = timedelta(minutes=template["duracao_base"])
            else:
                duracao = timedelta(minutes=int(template["duracao_base"] * fator_quantidade))
            
            atividade = DadosAtividade(
                id_atividade=f"{pedido.id_pedido}_{tipo_produto}_{i}",
                nome=template["nome"],
                duracao=duracao,
                equipamentos_necessarios=template["equipamentos"],
                tempo_maximo_espera=timedelta(minutes=template["tempo_espera"]),
                ordem_execucao=i
            )
            
            atividades_criadas.append(atividade)
            self.equipamentos_unicos.update(atividade.equipamentos_necessarios)
        
        return atividades_criadas
    
    def _estimar_duracao_por_produto(self, pedido) -> timedelta:
        """Estima duração baseada no tipo de produto e quantidade"""
        nome_produto = self._obter_nome_produto(pedido).lower()
        quantidade = pedido.quantidade
        
        # Tempos base mais conservadores (em horas)
        tempos_base = {
            "frances": 4.0,
            "hamburguer": 3.5,
            "forma": 4.5,
            "baguete": 3.0,
            "tranca": 5.0,
            "queijo": 5.0
        }
        
        # Tempo base
        tempo_base = 3.0  # 3 horas padrão
        for palavra, tempo in tempos_base.items():
            if palavra in nome_produto:
                tempo_base = tempo
                break
        
        # Adicionar tempo variável baseado na quantidade (limitado)
        fator_quantidade = min(2.0, quantidade / 100)  # Máximo 2x o tempo base
        tempo_total = tempo_base * (0.8 + 0.2 * fator_quantidade)  # Entre 80% e 100% + variável
        
        return timedelta(hours=tempo_total)
    
    def _obter_nome_produto(self, pedido) -> str:
        """Obtém nome do produto do pedido"""
        try:
            if hasattr(pedido, 'ficha_tecnica_modular') and pedido.ficha_tecnica_modular:
                nome = getattr(pedido.ficha_tecnica_modular, 'nome', None)
                if nome:
                    return nome
            
            # Mapeamento por ID do produto
            mapeamento_ids = {
                1001: "pao_frances",
                1002: "pao_hamburger", 
                1003: "pao_de_forma",
                1004: "pao_baguete",
                1005: "pao_tranca_de_queijo_finos"
            }
            
            if hasattr(pedido, 'id_produto') and pedido.id_produto in mapeamento_ids:
                return mapeamento_ids[pedido.id_produto]
            
            return f'produto_{getattr(pedido, "id_produto", pedido.id_pedido)}'
            
        except Exception as e:
            return f'produto_{pedido.id_pedido}'
    
    def _obter_nome_atividade(self, atividade) -> str:
        """Obtém nome da atividade"""
        if hasattr(atividade, 'nome_atividade'):
            return atividade.nome_atividade
        elif hasattr(atividade, 'nome'):
            return atividade.nome
        else:
            return f'atividade_{getattr(atividade, "id_atividade", "desconhecida")}'
    
    def _obter_nome_equipamento(self, equipamento) -> str:
        """Obtém nome do equipamento de forma otimizada"""
        if hasattr(equipamento, 'nome'):
            return equipamento.nome
        elif hasattr(equipamento, 'id'):
            return f"equipamento_{equipamento.id}"
        else:
            return str(equipamento)
    
    def _extrair_tempo_maximo_espera(self, atividade) -> timedelta:
        """Extrai tempo máximo de espera da atividade"""
        try:
            if hasattr(atividade, 'tempo_maximo_de_espera') and atividade.tempo_maximo_de_espera:
                return atividade.tempo_maximo_de_espera
            else:
                return timedelta(minutes=15)  # Padrão: 15 min de espera
        except:
            return timedelta(minutes=15)
    
    def obter_relatorio_extracao(self) -> Dict[str, Any]:
        """Retorna relatório detalhado da extração"""
        return {
            'total_pedidos': len(self.dados_extraidos),
            'total_atividades': sum(len(p.atividades) for p in self.dados_extraidos),
            'equipamentos_unicos': sorted(list(self.equipamentos_unicos)),
            'total_equipamentos_unicos': len(self.equipamentos_unicos),
            'duracao_media_pedido': self._calcular_duracao_media(),
            'logs_debug': self.logs_debug,
            'pedidos_por_nome': {p.nome_produto: p.id_pedido for p in self.dados_extraidos},
            'duracao_por_pedido': {p.id_pedido: str(p.duracao_total) for p in self.dados_extraidos},
            'cache_hits_duracao': len(self.cache_duracao),
            'cache_hits_equipamentos': len(self.cache_equipamentos)
        }
    
    def _calcular_duracao_media(self) -> timedelta:
        """Calcula duração média dos pedidos"""
        if not self.dados_extraidos:
            return timedelta(0)
        
        total_duracao = sum([p.duracao_total for p in self.dados_extraidos], timedelta())
        return total_duracao / len(self.dados_extraidos)
    
    def imprimir_resumo(self):
        """Imprime resumo legível da extração"""
        print("\n" + "="*60)
        print("📋 RESUMO DA EXTRAÇÃO DE DADOS (OTIMIZADA)")
        print("="*60)
        
        relatorio = self.obter_relatorio_extracao()
        
        print(f"📊 Total de pedidos: {relatorio['total_pedidos']}")
        print(f"📊 Total de atividades: {relatorio['total_atividades']}")
        print(f"🔧 Equipamentos únicos: {relatorio['total_equipamentos_unicos']}")
        print(f"⏱️ Duração média: {relatorio['duracao_media_pedido']}")
        print(f"🚀 Cache hits duração: {relatorio['cache_hits_duracao']}")
        print(f"🚀 Cache hits equipamentos: {relatorio['cache_hits_equipamentos']}")
        
        print(f"\n🭭 Pedidos extraídos:")
        for pedido in self.dados_extraidos:
            print(f"  • {pedido.nome_produto} (ID {pedido.id_pedido}): {len(pedido.atividades)} atividades, {pedido.duracao_total}")
        
        print(f"\n🛠️ Categorias de equipamentos:")
        equipamentos_categoria = [eq for eq in self.equipamentos_unicos if eq.startswith('categoria_')]
        for equipamento in sorted(equipamentos_categoria):
            print(f"  • {equipamento}")
        
        if relatorio['logs_debug']:
            print(f"\n⚠️ Avisos/Erros ({len(relatorio['logs_debug'])}):")
            for log in relatorio['logs_debug'][:3]:  # Apenas primeiros 3
                print(f"  • {log}")
            if len(relatorio['logs_debug']) > 3:
                print(f"  • ... e mais {len(relatorio['logs_debug']) - 3} avisos")
        
        print("="*60)


def testar_extrator_otimizado():
    """Teste do extrator otimizado"""
    print("🧪 Testando ExtratorDadosPedidos OTIMIZADO...")
    
    # Mock de dados para teste
    class MockPedido:
        def __init__(self, id_pedido, id_produto, nome, quantidade):
            self.id_pedido = id_pedido
            self.id_produto = id_produto
            self.quantidade = quantidade
            self.inicio_jornada = datetime(2025, 6, 22, 7, 0)
            self.fim_jornada = datetime(2025, 6, 26, 7, 0)
            self.atividades_modulares = None  # Simula ausência de atividades
            
            class MockFicha:
                def __init__(self, nome):
                    self.nome = nome
            
            self.ficha_tecnica_modular = MockFicha(nome)
    
    # Criar pedidos mock
    pedidos_mock = [
        MockPedido(1, 1001, "pao_frances", 450),
        MockPedido(2, 1002, "pao_hamburguer", 120),
        MockPedido(3, 1003, "pao_de_forma", 60),
        MockPedido(4, 1004, "pao_baguete", 20),
        MockPedido(5, 1005, "pao_tranca_queijo", 10)
    ]
    
    # Testar extração
    extrator = ExtratorDadosPedidos()
    dados_extraidos = extrator.extrair_dados(pedidos_mock)
    
    # Imprimir resultado
    extrator.imprimir_resumo()
    
    # Verificar se funcionou
    print(f"\n🧪 TESTE CONCLUÍDO:")
    print(f"   Pedidos processados: {len(dados_extraidos)}")
    print(f"   Equipamentos únicos: {len(extrator.equipamentos_unicos)}")
    
    return len(dados_extraidos) == len(pedidos_mock)


if __name__ == "__main__":
    testar_extrator_otimizado()