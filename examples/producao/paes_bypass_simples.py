#!/usr/bin/env python3
"""
🏭 PRODUÇÃO DE PÃES COM BYPASS - VERSÃO SIMPLES
==============================================

Script baseado no producao_paes.py original, mas com controle de bypass
por pedido individual. Usa apenas execução SEQUENCIAL (sem otimização).

✅ CARACTERÍSTICAS:
- Mesmo formato do producao_paes.py
- Bypass configurável por pedido
- Execução sequencial apenas
- Todos os produtos do arquivo original
"""

import sys
import os
from datetime import datetime, timedelta

# Adicionar path do projeto
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))

from menu.gerenciador_pedidos import DadosPedidoMenu
from services.gestores.producao.gestor_producao import GestorProducao
from utils.logs.gerenciador_logs import limpar_logs_inicializacao
from utils.comandas.limpador_comandas import apagar_todas_as_comandas


class ProducaoPaesComBypass:
    """Sistema de produção com bypass configurável por pedido"""
    
    def __init__(self):
        self.gestor_producao = GestorProducao()
        
        # Mapeamento de produtos (igual ao producao_paes.py)
        self.mapeamento_produtos = {
            "Pão Francês": 1001,
            "Pão Hambúrguer": 1002,
            "Pão de Forma": 1003,
            "Pão Baguete": 1004,
            "Pão Trança de Queijo finos": 1005
        }
        
        # Estatísticas
        self.pedidos_criados = []
        self.configuracao_bypass = {}
    
    def criar_configuracoes_pedidos(self):
        """
        Define os pedidos e suas configurações de bypass.
        
        MODIFIQUE AQUI para controlar o bypass de cada pedido!
        
        Formato:
        - usar_bypass=False: Pedido normal (todas as validações)
        - usar_bypass=True: Bypass completo (pula todas as validações)  
        - tipos_bypass=['MISTURADORAS']: Bypass apenas em tipos específicos
        """
        
        # CONFIGURAÇÕES DOS PEDIDOS (baseado no producao_paes.py)
        configuracoes_pedidos = [
            # CONJUNTO INICIAL 
            {"produto": "Pão Francês", "quantidade": 450, "hora_fim": 7, "usar_bypass": False},
            {"produto": "Pão Hambúrguer", "quantidade": 120, "hora_fim": 7, "usar_bypass": False},  # Bypass só nas misturadoras
            {"produto": "Pão de Forma", "quantidade": 20, "hora_fim": 7, "usar_bypass": True, "tipos_bypass": ["MISTURADORAS"]},
            {"produto": "Pão Baguete", "quantidade": 20, "hora_fim": 7, "usar_bypass": True, "tipos_bypass": ["MISTURADORAS"]},
            {"produto": "Pão Trança de Queijo finos", "quantidade": 10, "hora_fim": 7, "usar_bypass": True, "tipos_bypass": ["MISTURADORAS"]},

            # CONJUNTO ADICIONAL 
            {"produto": "Pão Francês", "quantidade": 300, "hora_fim": 9, "usar_bypass": False},
            {"produto": "Pão Baguete", "quantidade": 10, "hora_fim": 9, "usar_bypass": True, "tipos_bypass": ["MISTURADORAS"]},
            {"produto": "Pão Trança de Queijo finos", "quantidade": 10, "hora_fim": 9, "usar_bypass": True, "tipos_bypass": ["MISTURADORAS"]},

            # CONJUNTO VESPERTINO
            {"produto": "Pão Francês", "quantidade": 450, "hora_fim": 15, "usar_bypass": False},  # Bypass completo
            {"produto": "Pão Hambúrguer", "quantidade": 60, "hora_fim": 15, "usar_bypass": True, "tipos_bypass": ["MISTURADORAS"]},  # Bypass específico
            {"produto": "Pão de Forma", "quantidade": 10, "hora_fim": 15, "usar_bypass": True, "tipos_bypass": ["MISTURADORAS"]},
            {"produto": "Pão Baguete", "quantidade": 20, "hora_fim": 15, "usar_bypass": True, "tipos_bypass": ["MISTURADORAS"]},
            {"produto": "Pão Trança de Queijo finos", "quantidade": 10, "hora_fim": 15, "usar_bypass": True, "tipos_bypass": ["MISTURADORAS"]},

            # CONJUNTO NOTURNO
            {"produto": "Pão Francês", "quantidade": 300, "hora_fim": 17, "usar_bypass": False},
            {"produto": "Pão Baguete", "quantidade": 30, "hora_fim": 17, "usar_bypass": True, "tipos_bypass": ["MISTURADORAS"]},
            {"produto": "Pão Trança de Queijo finos", "quantidade": 10, "hora_fim": 17, "usar_bypass": True, "tipos_bypass": ["MISTURADORAS"]}
        ]
        
        return configuracoes_pedidos
    
    def criar_pedidos(self):
        """Cria os pedidos baseado nas configurações"""
        
        print("📋 CRIANDO PEDIDOS DE PRODUÇÃO")
        print("=" * 50)
        
        # Data base para os cálculos (igual ao producao_paes.py)
        data_base = datetime(2025, 6, 26)
        
        configuracoes = self.criar_configuracoes_pedidos()
        id_pedido_counter = 1
        
        for config in configuracoes:
            print(f"   🍞 Pedido {id_pedido_counter}: {config['produto']} ({config['quantidade']} un)")
            
            # Calcular datas (igual ao producao_paes.py)  
            fim_jornada = data_base.replace(hour=config['hora_fim'], minute=0, second=0, microsecond=0)
            inicio_jornada = fim_jornada - timedelta(days=3)  # 3 dias de flexibilidade
            
            # Obter ID do produto
            id_produto = self.mapeamento_produtos.get(config['produto'])
            if id_produto is None:
                print(f"   ⚠️ Produto '{config['produto']}' não encontrado no mapeamento!")
                continue
            
            # Criar pedido no formato do menu
            pedido = DadosPedidoMenu(
                id_ordem=1,
                id_pedido=id_pedido_counter,
                id_item=id_produto,
                nome_item=config['produto'].lower().replace(' ', '_').replace('ã', 'a').replace('ç', 'c'),
                tipo_item="PRODUTO",
                quantidade=config['quantidade'],
                inicio_jornada=inicio_jornada,
                fim_jornada=fim_jornada,
                arquivo_atividades=f"{id_produto}_{config['produto'].lower().replace(' ', '_')}.json",
                registrado_em=datetime.now()
            )
            
            self.pedidos_criados.append(pedido)
            
            # Configurar bypass se necessário
            if config.get('usar_bypass', False):
                self._configurar_bypass_pedido(id_pedido_counter, config)
                bypass_info = self._obter_info_bypass(config)
                print(f"      🔧 {bypass_info}")
            else:
                print(f"      ✅ Validação normal")
            
            id_pedido_counter += 1
        
        print(f"\n✅ {len(self.pedidos_criados)} pedidos criados")
        
        if self.configuracao_bypass:
            total_com_bypass = sum(len(pedidos) for pedidos in self.configuracao_bypass.values())
            print(f"🔧 {total_com_bypass} pedidos com bypass configurado")
    
    def _configurar_bypass_pedido(self, id_pedido: int, config: dict):
        """Configura bypass para um pedido específico"""
        
        if config.get('tipos_bypass'):
            # Bypass específico em tipos determinados
            tipos_bypass = set()
            
            from enums.equipamentos.tipo_equipamento import TipoEquipamento
            for tipo_nome in config['tipos_bypass']:
                try:
                    tipo_enum = TipoEquipamento[tipo_nome]
                    tipos_bypass.add(tipo_enum)
                except KeyError:
                    print(f"      ⚠️ Tipo de equipamento inválido: {tipo_nome}")
            
            if tipos_bypass:
                if 1 not in self.configuracao_bypass:  # id_ordem = 1
                    self.configuracao_bypass[1] = {}
                self.configuracao_bypass[1][id_pedido] = tipos_bypass
        
        else:
            # Bypass completo - descobrir todos os tipos necessários e aplicar bypass
            # Será configurado na descoberta automática de equipamentos
            if 1 not in self.configuracao_bypass:
                self.configuracao_bypass[1] = {}
            self.configuracao_bypass[1][id_pedido] = "TODOS"  # Marca especial para descobrir depois
    
    def _obter_info_bypass(self, config: dict) -> str:
        """Retorna string descritiva do bypass configurado"""
        if config.get('tipos_bypass'):
            tipos_str = ', '.join(config['tipos_bypass'])
            return f"Bypass em: {tipos_str}"
        else:
            return "Bypass completo (todos os tipos)"
    
    def _descobrir_e_configurar_bypass_completo(self):
        """Descobre equipamentos para pedidos marcados com bypass completo"""
        
        print("\n🔍 DESCOBRINDO EQUIPAMENTOS PARA BYPASS COMPLETO")
        print("=" * 50)
        
        # Usar a mesma lógica do menu para descobrir equipamentos
        from menu.main_menu import MenuPrincipal
        menu = MenuPrincipal()
        
        pedidos_para_atualizar = []
        
        # Encontrar pedidos marcados com bypass completo
        for ordem_id, pedidos_ordem in self.configuracao_bypass.items():
            for pedido_id, tipos in pedidos_ordem.items():
                if tipos == "TODOS":  # Marca especial
                    pedidos_para_atualizar.append((ordem_id, pedido_id))
        
        # Descobrir equipamentos para cada pedido
        for ordem_id, pedido_id in pedidos_para_atualizar:
            pedido = next(p for p in self.pedidos_criados if p.id_pedido == pedido_id)
            
            print(f"   🔍 Pedido {pedido_id} ({pedido.nome_item})")
            
            tipos_equipamentos = menu._descobrir_tipos_equipamentos_pedido(pedido)
            
            if tipos_equipamentos:
                self.configuracao_bypass[ordem_id][pedido_id] = set(tipos_equipamentos)
                tipos_nomes = [t.name for t in tipos_equipamentos]
                print(f"      ✅ {len(tipos_equipamentos)} tipos descobertos: {', '.join(tipos_nomes)}")
            else:
                print(f"      ⚠️ Nenhum equipamento descoberto - removendo bypass")
                del self.configuracao_bypass[ordem_id][pedido_id]
    
    def executar_producao(self):
        """Executa todos os pedidos com bypass configurado"""
        
        print(f"\n🚀 EXECUTANDO PRODUÇÃO - {len(self.pedidos_criados)} PEDIDOS")
        print("=" * 60)
        
        inicio_execucao = datetime.now()
        
        # Executar com bypass se configurado
        if self.configuracao_bypass:
            print(f"🔧 Aplicando bypass em pedidos específicos...")
            sucesso = self.gestor_producao.executar_sequencial(self.pedidos_criados, self.configuracao_bypass)
        else:
            print("ℹ️ Execução normal (sem bypass)")
            sucesso = self.gestor_producao.executar_sequencial(self.pedidos_criados)
        
        fim_execucao = datetime.now()
        tempo_total = (fim_execucao - inicio_execucao).total_seconds()
        
        # Relatório final
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL")
        print("=" * 60)
        
        if sucesso:
            print("✅ PRODUÇÃO CONCLUÍDA COM SUCESSO!")
        else:
            print("❌ PRODUÇÃO FALHOU")
        
        # Estatísticas
        stats = self.gestor_producao.obter_estatisticas()
        print(f"⏱️ Tempo total: {tempo_total:.1f}s")
        print(f"📦 Pedidos processados: {stats.get('pedidos_executados', 0)}/{stats.get('total_pedidos', 0)}")
        print(f"🎯 Modo: SEQUENCIAL (sem otimização)")
        
        if self.configuracao_bypass:
            total_bypass = sum(len(pedidos) for pedidos in self.configuracao_bypass.values())
            print(f"🔧 Pedidos com bypass: {total_bypass}")
        
        # Resumo por produto
        print(f"\n📋 RESUMO POR PRODUTO:")
        produtos_resumo = {}
        for pedido in self.pedidos_criados:
            nome_produto = next(nome for nome, id_prod in self.mapeamento_produtos.items() 
                              if id_prod == pedido.id_item)
            if nome_produto not in produtos_resumo:
                produtos_resumo[nome_produto] = 0
            produtos_resumo[nome_produto] += pedido.quantidade
        
        for produto, total in produtos_resumo.items():
            print(f"   🍞 {produto}: {total} unidades")
        
        return sucesso
    
    def executar_sistema_completo(self):
        """Executa o sistema completo de produção"""
        
        print("🏭 SISTEMA DE PRODUÇÃO DE PÃES COM BYPASS")
        print("=" * 60)
        print(f"🕐 Início: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("🎯 Modo: SEQUENCIAL (sem otimização)")
        print()
        
        try:
            # Limpeza inicial
            print("🧹 Limpando ambiente...")
            relatorio_limpeza = limpar_logs_inicializacao()
            apagar_todas_as_comandas()
            if isinstance(relatorio_limpeza, str):
                print(relatorio_limpeza)
            
            # Criar pedidos
            self.criar_pedidos()
            
            # Descobrir equipamentos para bypass completo
            if self.configuracao_bypass:
                self._descobrir_e_configurar_bypass_completo()
            
            # Executar produção
            sucesso = self.executar_producao()
            
            print(f"\n🕐 Fim: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            print("✅ Sistema finalizado!")
            
            return sucesso
            
        except Exception as e:
            print(f"\n💥 ERRO CRÍTICO: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Função principal"""
    
    try:
        sistema = ProducaoPaesComBypass()
        sucesso = sistema.executar_sistema_completo()
        
        if sucesso:
            print("\n🎉 PRODUÇÃO REALIZADA COM SUCESSO!")
        else:
            print("\n❌ PRODUÇÃO FALHOU - Verifique os logs para detalhes")
            
    except KeyboardInterrupt:
        print("\n\n🛑 Execução interrompida pelo usuário")
    except Exception as e:
        print(f"\n💥 ERRO INESPERADO: {e}")


if __name__ == "__main__":
    main()