#!/usr/bin/env python3
"""
Teste Standalone da Correção - Gerador de Janelas Temporais
===========================================================

Teste independente para verificar se a correção resolve o problema
do otimizador PL que não gera janelas para fins obrigatórios.
"""

import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict
from dataclasses import dataclass

# Adiciona o caminho do projeto
sys.path.append("/Users/jardelrodrigues/Desktop/SIVIRA/src_equip")


@dataclass
class DadosPedidoTeste:
    """Classe simplificada para teste"""
    id_pedido: int
    nome_produto: str
    quantidade: int
    inicio_jornada: datetime
    fim_jornada: datetime
    duracao_total: timedelta
    atividades: List = None


def testar_problema_original():
    """
    Testa exatamente o problema encontrado no log de erro.
    """
    print("🔍 TESTE: Reproduzindo problema original...")
    print("="*60)
    
    # ✅ DADOS EXATOS DO LOG DE ERRO
    dados_pedido = DadosPedidoTeste(
        id_pedido=1,
        nome_produto="pao_frances",
        quantidade=450,
        inicio_jornada=datetime(2025, 6, 26, 2, 35),  # 26/06 02:35
        fim_jornada=datetime(2025, 6, 26, 7, 0),     # 26/06 07:00
        duracao_total=timedelta(hours=4, minutes=25), # 4:25:00
        atividades=[]
    )
    
    print(f"📋 Dados do teste:")
    print(f"   Pedido: {dados_pedido.nome_produto} (ID {dados_pedido.id_pedido})")
    print(f"   Quantidade: {dados_pedido.quantidade}")
    print(f"   Janela: {dados_pedido.inicio_jornada.strftime('%d/%m %H:%M')} → {dados_pedido.fim_jornada.strftime('%d/%m %H:%M')}")
    print(f"   Duração: {dados_pedido.duracao_total}")
    
    # Calcula a janela disponível
    janela_disponivel = dados_pedido.fim_jornada - dados_pedido.inicio_jornada
    print(f"   Janela disponível: {janela_disponivel}")
    
    # Verifica se teoricamente é possível
    if dados_pedido.duracao_total <= janela_disponivel:
        print(f"   ✅ Teoricamente VIÁVEL (duração <= janela)")
        
        # Para fim obrigatório, calcula o início necessário
        inicio_necessario = dados_pedido.fim_jornada - dados_pedido.duracao_total
        print(f"   🎯 Para FIM OBRIGATÓRIO às {dados_pedido.fim_jornada.strftime('%H:%M')}:")
        print(f"      Deve começar às: {inicio_necessario.strftime('%H:%M')}")
        print(f"      Início mínimo disponível: {dados_pedido.inicio_jornada.strftime('%H:%M')}")
        
        if inicio_necessario >= dados_pedido.inicio_jornada:
            print(f"      ✅ PERFEITAMENTE VIÁVEL!")
            print(f"      📊 Janela única possível: {inicio_necessario.strftime('%H:%M')} → {dados_pedido.fim_jornada.strftime('%H:%M')}")
        else:
            print(f"      ❌ IMPOSSÍVEL - início necessário anterior ao mínimo")
    else:
        print(f"   ❌ Teoricamente IMPOSSÍVEL (duração > janela)")
    
    return dados_pedido


def testar_gerador_corrigido_standalone():
    """
    Testa o gerador com a correção implementada.
    """
    print(f"\n🧪 TESTE: Gerador de Janelas CORRIGIDO")
    print("="*60)
    
    try:
        # Importa a classe corrigida
        from otimizador.gerador_janelas_temporais import GeradorJanelasTemporais
        
        # Usa dados do problema original
        dados_pedido = testar_problema_original()
        dados_lista = [dados_pedido]
        
        # Define que este pedido tem fim obrigatório
        pedidos_com_fim_obrigatorio = {
            1: datetime(2025, 6, 26, 7, 0)  # Pedido 1 tem fim obrigatório às 07:00
        }
        
        print(f"\n🔧 Testando com gerador CORRIGIDO:")
        print(f"   Resolução: 30 minutos (igual ao log original)")
        print(f"   Pedidos com fim obrigatório: {list(pedidos_com_fim_obrigatorio.keys())}")
        
        # Cria gerador e testa
        gerador = GeradorJanelasTemporais(resolucao_minutos=30)
        
        # ✅ CHAMA MÉTODO CORRIGIDO passando fins obrigatórios
        janelas = gerador.gerar_janelas_todos_pedidos(
            dados_lista,
            pedidos_com_fim_obrigatorio
        )
        
        # Analisa resultado
        print(f"\n📊 RESULTADO:")
        if 1 in janelas:
            janelas_pedido_1 = janelas[1]
            print(f"   Janelas geradas para pedido 1: {len(janelas_pedido_1)}")
            
            if janelas_pedido_1:
                for i, janela in enumerate(janelas_pedido_1):
                    inicio_str = janela.datetime_inicio.strftime('%d/%m %H:%M')
                    fim_str = janela.datetime_fim.strftime('%d/%m %H:%M')
                    viavel_str = "✅ VIÁVEL" if janela.viavel else "❌ NÃO VIÁVEL"
                    
                    print(f"   Janela {i+1}: {inicio_str} → {fim_str} ({viavel_str})")
                
                # ✅ VALIDAÇÃO CRÍTICA
                if len(janelas_pedido_1) >= 1 and janelas_pedido_1[0].viavel:
                    print(f"\n🎉 CORREÇÃO FUNCIONOU!")
                    print(f"   ✅ Gerou {len(janelas_pedido_1)} janela(s) viável(eis)")
                    print(f"   ✅ Problema do log original foi RESOLVIDO")
                    return True
                else:
                    print(f"\n❌ CORREÇÃO FALHOU - janelas não viáveis")
                    return False
            else:
                print(f"   ❌ NENHUMA janela gerada (problema persiste)")
                return False
        else:
            print(f"   ❌ Pedido 1 não encontrado nos resultados")
            return False
            
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print(f"   Certifique-se de que o arquivo gerador_janelas_temporais.py foi atualizado")
        return False
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
        return False


def comparar_antes_depois():
    """
    Compara o comportamento antes e depois da correção.
    """
    print(f"\n📊 COMPARAÇÃO: Antes vs Depois da Correção")
    print("="*60)
    
    print(f"❌ ANTES (comportamento original que falhou):")
    print(f"   - Tentava gerar janelas com forward scheduling")
    print(f"   - periodo_inicio_max = 8 - 9 = -1")
    print(f"   - while 0 <= -1: NUNCA EXECUTA")
    print(f"   - Resultado: 0 janelas geradas")
    
    print(f"\n✅ DEPOIS (comportamento corrigido):")
    print(f"   - Detecta que é pedido com fim obrigatório")
    print(f"   - Calcula única janela possível: fim - duração")
    print(f"   - Valida se início calculado >= início mínimo")
    print(f"   - Resultado: 1 janela exata gerada")


def main():
    """Executa todos os testes."""
    print("🔬 TESTE COMPLETO DA CORREÇÃO - GERADOR DE JANELAS")
    print("="*80)
    
    # Teste 1: Reproduz problema original
    dados_teste = testar_problema_original()
    
    # Teste 2: Testa correção
    sucesso = testar_gerador_corrigido_standalone()
    
    # Teste 3: Mostra comparação
    comparar_antes_depois()
    
    # Resultado final
    print(f"\n" + "="*80)
    if sucesso:
        print(f"🎉 TESTE CONCLUÍDO COM SUCESSO!")
        print(f"✅ A correção resolve o problema identificado no log")
        print(f"✅ O otimizador PL agora deve funcionar para fins obrigatórios")
    else:
        print(f"❌ TESTE FALHOU!")
        print(f"❌ A correção precisa de ajustes adicionais")
    
    print(f"="*80)
    return sucesso


if __name__ == "__main__":
    main()