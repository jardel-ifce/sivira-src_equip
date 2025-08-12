"""
Extrator de Dados dos Pedidos para Otimização - CORRIGIDO
========================================================

Primeira classe do otimizador: extrai dados necessários dos pedidos existentes
para alimentar o modelo de Programação Linear.

VERSÃO CORRIGIDA para trabalhar com a estrutura real do sistema de produção.
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
    Extrai dados necessários dos pedidos para o modelo de PL.
    
    VERSÃO CORRIGIDA para trabalhar com PedidoDeProducao real.
    """
    
    def __init__(self):
        self.dados_extraidos = []
        self.equipamentos_unicos = set()
        self.logs_debug = []
    
    def extrair_dados(self, pedidos) -> List[DadosPedido]:
        """
        Extrai dados de uma lista de PedidoDeProducao.
        
        Args:
            pedidos: Lista de objetos PedidoDeProducao
            
        Returns:
            Lista de DadosPedido prontos para otimização
        """
        self.dados_extraidos = []
        self.equipamentos_unicos = set()
        self.logs_debug = []
        
        print(f"🔄 Extraindo dados de {len(pedidos)} pedidos...")
        
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
        """Extrai dados de um pedido individual"""
        
        # Dados básicos do pedido
        dados_basicos = {
            'id_pedido': pedido.id_pedido,
            'nome_produto': self._obter_nome_produto(pedido),
            'quantidade': pedido.quantidade,
            'inicio_jornada': pedido.inicio_jornada,
            'fim_jornada': pedido.fim_jornada,
        }
        
        # ESTRATÉGIA CORRIGIDA: Força criação das atividades se necessário
        atividades_extraidas = self._extrair_ou_criar_atividades(pedido)
        
        # Calcula duração total
        duracao_total = sum([a.duracao for a in atividades_extraidas], timedelta())
        
        # FALLBACK: Se duração for 0, estima baseado na quantidade
        if duracao_total == timedelta(0):
            duracao_total = self._estimar_duracao_por_produto(pedido)
            print(f"   🔧 Duração estimada para pedido {pedido.id_pedido}: {duracao_total}")
        
        return DadosPedido(
            **dados_basicos,
            duracao_total=duracao_total,
            atividades=atividades_extraidas
        )
    
    def _extrair_ou_criar_atividades(self, pedido) -> List[DadosAtividade]:
        """
        Extrai atividades do pedido ou cria atividades estimadas se necessário.
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
        
        # TENTATIVA 3: Extrair da ficha técnica
        if not atividades_extraidas and hasattr(pedido, 'ficha_tecnica_modular'):
            atividades_extraidas = self._extrair_atividades_da_ficha(pedido)
        
        # FALLBACK: Criar atividades estimadas
        if not atividades_extraidas:
            print(f"   🆘 Criando atividades estimadas para pedido {pedido.id_pedido}")
            atividades_extraidas = self._criar_atividades_estimadas(pedido)
        
        return atividades_extraidas
    
    def _extrair_atividades_modulares(self, atividades_modulares) -> List[DadosAtividade]:
        """Extrai dados das atividades modulares existentes"""
        atividades_extraidas = []
        
        for i, atividade in enumerate(atividades_modulares):
            try:
                dados_atividade = DadosAtividade(
                    id_atividade=getattr(atividade, 'id_atividade', f"ativ_{i}"),
                    nome=self._obter_nome_atividade(atividade),
                    duracao=getattr(atividade, 'duracao', timedelta(minutes=30)),
                    equipamentos_necessarios=self._extrair_equipamentos_necessarios(atividade),
                    tempo_maximo_espera=self._extrair_tempo_maximo_espera(atividade),
                    ordem_execucao=i
                )
                
                atividades_extraidas.append(dados_atividade)
                self.equipamentos_unicos.update(dados_atividade.equipamentos_necessarios)
                
            except Exception as e:
                self.logs_debug.append(f"Erro atividade {i}: {e}")
        
        return atividades_extraidas
    
    def _extrair_atividades_da_ficha(self, pedido) -> List[DadosAtividade]:
        """Extrai atividades da ficha técnica modular"""
        atividades_extraidas = []
        
        try:
            ficha = pedido.ficha_tecnica_modular
            if hasattr(ficha, 'atividades') and ficha.atividades:
                print(f"   📋 Extraindo {len(ficha.atividades)} atividades da ficha técnica")
                
                for i, atividade in enumerate(ficha.atividades):
                    dados_atividade = DadosAtividade(
                        id_atividade=getattr(atividade, 'id', f"ficha_ativ_{i}"),
                        nome=getattr(atividade, 'nome', f"atividade_{i}"),
                        duracao=getattr(atividade, 'duracao', timedelta(minutes=45)),
                        equipamentos_necessarios=self._extrair_equipamentos_da_atividade(atividade),
                        tempo_maximo_espera=timedelta(0),
                        ordem_execucao=i
                    )
                    
                    atividades_extraidas.append(dados_atividade)
                    self.equipamentos_unicos.update(dados_atividade.equipamentos_necessarios)
            
        except Exception as e:
            print(f"   ❌ Erro ao extrair da ficha técnica: {e}")
        
        return atividades_extraidas
    
    def _criar_atividades_estimadas(self, pedido) -> List[DadosAtividade]:
        """
        Cria atividades estimadas baseadas no tipo de produto.
        FALLBACK quando não consegue extrair atividades reais.
        """
        nome_produto = self._obter_nome_produto(pedido)
        
        # Estimativas baseadas no tipo de produto
        if "pao_frances" in nome_produto.lower() or "francês" in nome_produto.lower():
            return self._criar_atividades_pao_frances(pedido)
        elif "hamburguer" in nome_produto.lower() or "hambúrguer" in nome_produto.lower():
            return self._criar_atividades_pao_hamburguer(pedido)
        elif "forma" in nome_produto.lower():
            return self._criar_atividades_pao_forma(pedido)
        elif "baguete" in nome_produto.lower():
            return self._criar_atividades_pao_baguete(pedido)
        elif "tranca" in nome_produto.lower() or "queijo" in nome_produto.lower():
            return self._criar_atividades_pao_tranca(pedido)
        else:
            return self._criar_atividades_genericas(pedido)
    
    def _criar_atividades_pao_frances(self, pedido) -> List[DadosAtividade]:
        """Atividades estimadas para pão francês"""
        fator_quantidade = max(1, pedido.quantidade / 100)  # Base: 100 unidades
        
        atividades = [
            DadosAtividade(
                id_atividade=f"{pedido.id_pedido}_pesagem",
                nome="Pesagem de Ingredientes",
                duracao=timedelta(minutes=15 * fator_quantidade),
                equipamentos_necessarios=["balanca_digital", "bancada_preparo"],
                tempo_maximo_espera=timedelta(minutes=10),
                ordem_execucao=0
            ),
            DadosAtividade(
                id_atividade=f"{pedido.id_pedido}_mistura",
                nome="Mistura da Massa",
                duracao=timedelta(minutes=20 * fator_quantidade),
                equipamentos_necessarios=["misturador_industrial", "bancada_preparo"],
                tempo_maximo_espera=timedelta(minutes=5),
                ordem_execucao=1
            ),
            DadosAtividade(
                id_atividade=f"{pedido.id_pedido}_primeira_fermentacao",
                nome="Primeira Fermentação",
                duracao=timedelta(minutes=90),  # Tempo fixo
                equipamentos_necessarios=["camara_fermentacao"],
                tempo_maximo_espera=timedelta(minutes=15),
                ordem_execucao=2
            ),
            DadosAtividade(
                id_atividade=f"{pedido.id_pedido}_modelagem",
                nome="Modelagem dos Pães",
                duracao=timedelta(minutes=30 * fator_quantidade),
                equipamentos_necessarios=["bancada_modelagem"],
                tempo_maximo_espera=timedelta(minutes=10),
                ordem_execucao=3
            ),
            DadosAtividade(
                id_atividade=f"{pedido.id_pedido}_segunda_fermentacao",
                nome="Segunda Fermentação",
                duracao=timedelta(minutes=45),  # Tempo fixo
                equipamentos_necessarios=["camara_fermentacao"],
                tempo_maximo_espera=timedelta(minutes=10),
                ordem_execucao=4
            ),
            DadosAtividade(
                id_atividade=f"{pedido.id_pedido}_coccao",
                nome="Cocção",
                duracao=timedelta(minutes=25 * fator_quantidade),
                equipamentos_necessarios=["forno_industrial"],
                tempo_maximo_espera=timedelta(0),  # Não pode esperar
                ordem_execucao=5
            ),
            DadosAtividade(
                id_atividade=f"{pedido.id_pedido}_resfriamento",
                nome="Resfriamento",
                duracao=timedelta(minutes=20),  # Tempo fixo
                equipamentos_necessarios=["area_resfriamento"],
                tempo_maximo_espera=timedelta(minutes=30),
                ordem_execucao=6
            )
        ]
        
        # Registra equipamentos
        for atividade in atividades:
            self.equipamentos_unicos.update(atividade.equipamentos_necessarios)
        
        return atividades
    
    def _criar_atividades_pao_hamburguer(self, pedido) -> List[DadosAtividade]:
        """Atividades estimadas para pão de hambúrguer"""
        fator_quantidade = max(1, pedido.quantidade / 50)  # Base: 50 unidades
        
        return [
            DadosAtividade(f"{pedido.id_pedido}_pesagem", "Pesagem", timedelta(minutes=12 * fator_quantidade), ["balanca_digital"], timedelta(0), 0),
            DadosAtividade(f"{pedido.id_pedido}_mistura", "Mistura", timedelta(minutes=25 * fator_quantidade), ["misturador_industrial"], timedelta(0), 1),
            DadosAtividade(f"{pedido.id_pedido}_fermentacao1", "Fermentação 1", timedelta(minutes=75), ["camara_fermentacao"], timedelta(0), 2),
            DadosAtividade(f"{pedido.id_pedido}_modelagem", "Modelagem", timedelta(minutes=35 * fator_quantidade), ["bancada_modelagem"], timedelta(0), 3),
            DadosAtividade(f"{pedido.id_pedido}_fermentacao2", "Fermentação 2", timedelta(minutes=40), ["camara_fermentacao"], timedelta(0), 4),
            DadosAtividade(f"{pedido.id_pedido}_coccao", "Cocção", timedelta(minutes=30 * fator_quantidade), ["forno_industrial"], timedelta(0), 5)
        ]
    
    def _criar_atividades_pao_forma(self, pedido) -> List[DadosAtividade]:
        """Atividades estimadas para pão de forma"""
        fator_quantidade = max(1, pedido.quantidade / 20)  # Base: 20 unidades
        
        return [
            DadosAtividade(f"{pedido.id_pedido}_pesagem", "Pesagem", timedelta(minutes=10 * fator_quantidade), ["balanca_digital"], timedelta(0), 0),
            DadosAtividade(f"{pedido.id_pedido}_mistura", "Mistura", timedelta(minutes=30 * fator_quantidade), ["misturador_industrial"], timedelta(0), 1),
            DadosAtividade(f"{pedido.id_pedido}_fermentacao1", "Fermentação 1", timedelta(minutes=60), ["camara_fermentacao"], timedelta(0), 2),
            DadosAtividade(f"{pedido.id_pedido}_modelagem", "Modelagem/Formas", timedelta(minutes=40 * fator_quantidade), ["bancada_modelagem", "formas_pao"], timedelta(0), 3),
            DadosAtividade(f"{pedido.id_pedido}_fermentacao2", "Fermentação 2", timedelta(minutes=50), ["camara_fermentacao"], timedelta(0), 4),
            DadosAtividade(f"{pedido.id_pedido}_coccao", "Cocção", timedelta(minutes=35 * fator_quantidade), ["forno_industrial"], timedelta(0), 5)
        ]
    
    def _criar_atividades_pao_baguete(self, pedido) -> List[DadosAtividade]:
        """Atividades estimadas para pão baguete"""
        fator_quantidade = max(1, pedido.quantidade / 30)  # Base: 30 unidades
        
        return [
            DadosAtividade(f"{pedido.id_pedido}_pesagem", "Pesagem", timedelta(minutes=8 * fator_quantidade), ["balanca_digital"], timedelta(0), 0),
            DadosAtividade(f"{pedido.id_pedido}_mistura", "Mistura", timedelta(minutes=18 * fator_quantidade), ["misturador_industrial"], timedelta(0), 1),
            DadosAtividade(f"{pedido.id_pedido}_fermentacao1", "Fermentação 1", timedelta(minutes=80), ["camara_fermentacao"], timedelta(0), 2),
            DadosAtividade(f"{pedido.id_pedido}_modelagem", "Modelagem Baguete", timedelta(minutes=45 * fator_quantidade), ["bancada_modelagem"], timedelta(0), 3),
            DadosAtividade(f"{pedido.id_pedido}_fermentacao2", "Fermentação 2", timedelta(minutes=35), ["camara_fermentacao"], timedelta(0), 4),
            DadosAtividade(f"{pedido.id_pedido}_coccao", "Cocção", timedelta(minutes=28 * fator_quantidade), ["forno_industrial"], timedelta(0), 5)
        ]
    
    def _criar_atividades_pao_tranca(self, pedido) -> List[DadosAtividade]:
        """Atividades estimadas para pão trança de queijo"""
        fator_quantidade = max(1, pedido.quantidade / 10)  # Base: 10 unidades
        
        return [
            DadosAtividade(f"{pedido.id_pedido}_preparo_recheio", "Preparo Recheio", timedelta(minutes=20 * fator_quantidade), ["bancada_preparo"], timedelta(0), 0),
            DadosAtividade(f"{pedido.id_pedido}_pesagem", "Pesagem", timedelta(minutes=12 * fator_quantidade), ["balanca_digital"], timedelta(0), 1),
            DadosAtividade(f"{pedido.id_pedido}_mistura", "Mistura", timedelta(minutes=22 * fator_quantidade), ["misturador_industrial"], timedelta(0), 2),
            DadosAtividade(f"{pedido.id_pedido}_fermentacao1", "Fermentação 1", timedelta(minutes=70), ["camara_fermentacao"], timedelta(0), 3),
            DadosAtividade(f"{pedido.id_pedido}_trancado", "Trançado com Recheio", timedelta(minutes=50 * fator_quantidade), ["bancada_modelagem"], timedelta(0), 4),
            DadosAtividade(f"{pedido.id_pedido}_fermentacao2", "Fermentação 2", timedelta(minutes=30), ["camara_fermentacao"], timedelta(0), 5),
            DadosAtividade(f"{pedido.id_pedido}_coccao", "Cocção", timedelta(minutes=32 * fator_quantidade), ["forno_industrial"], timedelta(0), 6)
        ]
    
    def _criar_atividades_genericas(self, pedido) -> List[DadosAtividade]:
        """Atividades genéricas para produtos não reconhecidos"""
        fator_quantidade = max(1, pedido.quantidade / 50)
        
        return [
            DadosAtividade(f"{pedido.id_pedido}_preparo", "Preparação", timedelta(minutes=30 * fator_quantidade), ["bancada_preparo"], timedelta(0), 0),
            DadosAtividade(f"{pedido.id_pedido}_processamento", "Processamento", timedelta(minutes=60 * fator_quantidade), ["equipamento_generico"], timedelta(0), 1),
            DadosAtividade(f"{pedido.id_pedido}_finalizacao", "Finalização", timedelta(minutes=20 * fator_quantidade), ["bancada_finalizacao"], timedelta(0), 2)
        ]
    
    def _estimar_duracao_por_produto(self, pedido) -> timedelta:
        """Estima duração baseada no tipo de produto e quantidade"""
        nome_produto = self._obter_nome_produto(pedido).lower()
        quantidade = pedido.quantidade
        
        # Tempos base por unidade (em minutos)
        tempos_base = {
            "frances": 0.8,
            "hamburguer": 1.2,
            "forma": 2.0,
            "baguete": 1.0,
            "tranca": 3.0,
            "queijo": 3.0
        }
        
        # Tempo fixo de setup/fermentação (em horas)
        tempo_fixo = timedelta(hours=3)
        
        # Calcula tempo variável
        tempo_por_unidade = 1.0  # Padrão
        for palavra, tempo in tempos_base.items():
            if palavra in nome_produto:
                tempo_por_unidade = tempo
                break
        
        tempo_variavel = timedelta(minutes=quantidade * tempo_por_unidade)
        
        return tempo_fixo + tempo_variavel
    
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
    
    def _extrair_equipamentos_necessarios(self, atividade) -> List[str]:
        """Extrai lista de equipamentos necessários da atividade"""
        equipamentos = []
        
        try:
            # Tenta extrair de equipamentos_elegiveis
            if hasattr(atividade, 'equipamentos_elegiveis') and atividade.equipamentos_elegiveis:
                for equipamento in atividade.equipamentos_elegiveis:
                    nome_equipamento = self._obter_nome_equipamento(equipamento)
                    if nome_equipamento:
                        equipamentos.append(nome_equipamento)
            
            # Se não encontrou, tenta extrair dos tipos de equipamento
            elif hasattr(atividade, '_quantidade_por_tipo_equipamento'):
                for tipo_eq in atividade._quantidade_por_tipo_equipamento.keys():
                    equipamentos.append(f"tipo_{tipo_eq.name.lower()}")
            
            # Fallback: equipamento genérico
            if not equipamentos:
                equipamentos.append(f"equipamento_generico")
                
        except Exception as e:
            equipamentos.append(f"equipamento_erro")
        
        return equipamentos
    
    def _extrair_equipamentos_da_atividade(self, atividade) -> List[str]:
        """Extrai equipamentos de uma atividade da ficha técnica"""
        try:
            if hasattr(atividade, 'equipamentos') and atividade.equipamentos:
                return [str(eq) for eq in atividade.equipamentos]
            elif hasattr(atividade, 'equipamento'):
                return [str(atividade.equipamento)]
            else:
                return ["equipamento_ficha"]
        except:
            return ["equipamento_padrao"]
    
    def _obter_nome_equipamento(self, equipamento) -> str:
        """Obtém nome do equipamento"""
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
            'duracao_por_pedido': {p.id_pedido: str(p.duracao_total) for p in self.dados_extraidos}
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
        print("📋 RESUMO DA EXTRAÇÃO DE DADOS")
        print("="*60)
        
        relatorio = self.obter_relatorio_extracao()
        
        print(f"📊 Total de pedidos: {relatorio['total_pedidos']}")
        print(f"📊 Total de atividades: {relatorio['total_atividades']}")
        print(f"📊 Equipamentos únicos: {relatorio['total_equipamentos_unicos']}")
        print(f"⏱️ Duração média: {relatorio['duracao_media_pedido']}")
        
        print(f"\n🏭 Pedidos extraídos:")
        for pedido in self.dados_extraidos:
            print(f"  • {pedido.nome_produto} (ID {pedido.id_pedido}): {len(pedido.atividades)} atividades, {pedido.duracao_total}")
        
        print(f"\n🛠️ Equipamentos encontrados:")
        for i, equipamento in enumerate(sorted(self.equipamentos_unicos)):
            if i < 10:  # Mostra apenas os primeiros 10
                print(f"  • {equipamento}")
            elif i == 10:
                print(f"  • ... e mais {len(self.equipamentos_unicos) - 10} equipamentos")
                break
        
        if relatorio['logs_debug']:
            print(f"\n⚠️ Avisos/Erros ({len(relatorio['logs_debug'])}):")
            for log in relatorio['logs_debug'][:5]:  # Mostra apenas os primeiros 5
                print(f"  • {log}")
            if len(relatorio['logs_debug']) > 5:
                print(f"  • ... e mais {len(relatorio['logs_debug']) - 5} avisos")
        
        print("="*60)


# Função de teste para uso standalone
def testar_extrator():
    """Função de teste básico do extrator CORRIGIDO"""
    print("🧪 Testando ExtratorDadosPedidos CORRIGIDO...")
    
    # Mock de dados para teste
    class MockPedido:
        def __init__(self, id_pedido, id_produto, nome, quantidade):
            self.id_pedido = id_pedido
            self.id_produto = id_produto
            self.quantidade = quantidade
            self.inicio_jornada = datetime(2025, 6, 22, 7, 0)
            self.fim_jornada = datetime(2025, 6, 26, 7, 0)
            self.atividades_modulares = None  # Simula ausência de atividades
            
            # Mock da ficha técnica
            class MockFicha:
                def __init__(self, nome):
                    self.nome = nome
            
            self.ficha_tecnica_modular = MockFicha(nome)
    
    # Cria pedidos mock que simulam o problema real
    pedidos_mock = [
        MockPedido(1, 1001, "pao_frances", 450),
        MockPedido(2, 1002, "pao_hamburguer", 120),
        MockPedido(3, 1004, "pao_baguete", 50)
    ]
    
    # Testa extração
    extrator = ExtratorDadosPedidos()
    dados_extraidos = extrator.extrair_dados(pedidos_mock)
    
    # Imprime resultado
    extrator.imprimir_resumo()
    
    return dados_extraidos


if __name__ == "__main__":
    testar_extrator()