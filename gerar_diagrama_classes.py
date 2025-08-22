#!/usr/bin/env python3
"""
Gerador de Diagrama de Classes - SIVIRA Sistema de Produção
===========================================================
Este script analisa a estrutura do projeto e gera uma representação visual
das principais classes e suas relações.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

def create_class_diagram():
    # Configurar figura
    fig, ax = plt.subplots(1, 1, figsize=(20, 16))
    ax.set_xlim(0, 20)
    ax.set_ylim(0, 16)
    ax.axis('off')
    
    # Cores para diferentes categorias
    colors = {
        'model': '#E3F2FD',           # Azul claro - Modelos
        'service': '#E8F5E8',         # Verde claro - Serviços  
        'optimizer': '#FFF3E0',       # Laranja claro - Otimizador
        'factory': '#F3E5F5',         # Roxo claro - Factory
        'enum': '#FFEBEE',            # Rosa claro - Enums
        'controller': '#E0F2F1',      # Verde água - Controladores
        'utils': '#F5F5F5'            # Cinza claro - Utilitários
    }
    
    # Função para criar uma caixa de classe
    def create_class_box(ax, x, y, width, height, title, methods, color_key):
        # Caixa principal
        box = FancyBboxPatch(
            (x, y), width, height,
            boxstyle="round,pad=0.05",
            facecolor=colors[color_key],
            edgecolor='black',
            linewidth=1.5
        )
        ax.add_patch(box)
        
        # Título da classe
        ax.text(x + width/2, y + height - 0.3, title, 
                ha='center', va='center', fontsize=11, fontweight='bold')
        
        # Linha separadora
        ax.plot([x + 0.1, x + width - 0.1], 
                [y + height - 0.6, y + height - 0.6], 'k-', linewidth=0.5)
        
        # Métodos principais
        method_y = y + height - 0.9
        for method in methods[:6]:  # Limitar a 6 métodos por classe
            ax.text(x + 0.1, method_y, f"• {method}", 
                    ha='left', va='center', fontsize=8)
            method_y -= 0.25
            
        if len(methods) > 6:
            ax.text(x + 0.1, method_y, f"... +{len(methods)-6} outros", 
                    ha='left', va='center', fontsize=8, style='italic')
    
    # Função para criar conexões
    def create_connection(ax, x1, y1, x2, y2, style='->'):
        if style == '->':
            ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                       arrowprops=dict(arrowstyle='->', lw=1.5, color='#666'))
        elif style == '--':
            ax.plot([x1, x2], [y1, y2], '--', color='#666', linewidth=1)

    # ========================================================================
    # MODELOS DE DOMÍNIO - Coluna da esquerda
    # ========================================================================
    
    # Equipamento (superclasse)
    create_class_box(ax, 0.5, 13, 3.5, 2.5, 
                     'Equipamento (Abstract)', 
                     ['__init__(id, nome, setor)', 'esta_disponivel()', 
                      'registrar_ocupacao()', 'liberar_ocupacao()',
                      'mostrar_agenda()', 'validar_capacidade()'],
                     'model')
    
    # Equipamentos específicos
    create_class_box(ax, 0.5, 10, 3.5, 2.5,
                     'Masseira', 
                     ['adicionar_ocupacao()', 'obter_capacidade_disponivel()',
                      'esta_disponivel_para_item()', 'validar_nova_ocupacao()',
                      'liberar_por_atividade()', 'verificar_compatibilidade()'],
                     'model')
    
    create_class_box(ax, 0.5, 7, 3.5, 2.5,
                     'Forno', 
                     ['alocar_compartimento()', 'calcular_energia_necessaria()',
                      'verificar_disponibilidade()', 'registrar_ocupacao()',
                      'obter_temperatura_atual()', 'validar_capacidade()'],
                     'model')
    
    # PedidoDeProducao - Classe central
    create_class_box(ax, 5, 11, 4, 3.5,
                     'PedidoDeProducao', 
                     ['montar_estrutura()', 'criar_atividades_modulares()',
                      'executar_atividades_em_ordem()', 'verificar_disponibilidade_estoque()',
                      'gerar_comanda_de_reserva()', '_executar_produto_e_capturar_inicio()',
                      '_executar_subprodutos_com_timing_perfeito()', 'rollback_pedido()'],
                     'model')
    
    # AtividadeModular
    create_class_box(ax, 5, 7, 4, 3.5,
                     'AtividadeModular', 
                     ['tentar_alocar_e_iniciar_equipamentos()', '_alocar_equipamentos_e_funcionarios()',
                      '_tentar_alocacao_no_horario()', '_verificar_sequenciamento()',
                      '_alocar_funcionarios()', '_registrar_sucesso_equipamentos()'],
                     'model')
    
    # Almoxarifado
    create_class_box(ax, 0.5, 4, 3.5, 2.5,
                     'Almoxarifado', 
                     ['adicionar_item()', 'buscar_item_por_id()',
                      'verificar_disponibilidade_multiplos_itens()', 'reservar_multiplos_itens()',
                      'cancelar_reservas_pedido()', 'obter_estoque_atual_item()'],
                     'model')
    
    # ========================================================================
    # GESTORES E SERVIÇOS - Coluna central
    # ========================================================================
    
    # GestorProducao
    create_class_box(ax, 10, 13, 4, 2.5,
                     'GestorProducao', 
                     ['executar_sequencial()', 'executar_otimizado()',
                      '_inicializar_sistema()', '_converter_pedidos()',
                      'testar_sistema()', 'obter_estatisticas()'],
                     'controller')
    
    # GestorMisturadoras  
    create_class_box(ax, 10, 10, 4, 2.5,
                     'GestorMisturadoras', 
                     ['alocar()', '_verificar_viabilidade_rapida()',
                      '_algoritmo_distribuicao_balanceada()', '_tentar_alocacao_individual()',
                      '_executar_alocacao_multipla()', 'liberar_por_atividade()'],
                     'service')
    
    # GestorAlmoxarifado
    create_class_box(ax, 10, 7, 4, 2.5,
                     'GestorAlmoxarifado', 
                     ['obter_item_por_id()', 'verificar_estoque_atual_suficiente()',
                      'verificar_disponibilidade_multiplos_itens()', 'processar_reserva()',
                      'obter_estoque_atual()', 'validar_integridade()'],
                     'service')
    
    # ExecutorPedidos
    create_class_box(ax, 10, 4, 4, 2.5,
                     'ExecutorPedidos', 
                     ['executar_sequencial()', 'executar_otimizado()',
                      '_executar_pedido_individual()', 'obter_estatisticas()',
                      'configurar()', '_limpar_sistema()'],
                     'service')

    # ========================================================================
    # OTIMIZADOR - Coluna da direita
    # ========================================================================
    
    # OtimizadorIntegrado
    create_class_box(ax, 15.5, 13, 4, 2.5,
                     'OtimizadorIntegrado', 
                     ['executar_pedidos_otimizados()', '_analisar_restricoes_temporais()',
                      '_executar_pedidos_hibridamente()', 'obter_cronograma_otimizado()',
                      '_calcular_estatisticas_execucao()', 'restaurar_horarios_originais()'],
                     'optimizer')
    
    # ModeloPLOtimizador
    create_class_box(ax, 15.5, 10, 4, 2.5,
                     'ModeloPLOtimizador', 
                     ['resolver()', '_criar_variaveis()',
                      '_adicionar_restricoes()', '_configurar_objetivo()',
                      'extrair_solucao()', '_validar_solucao()'],
                     'optimizer')
    
    # ExtratorDadosPedidos
    create_class_box(ax, 15.5, 7, 4, 2.5,
                     'ExtratorDadosPedidos', 
                     ['extrair_dados()', 'processar_pedido()',
                      'validar_dados_entrada()', 'calcular_duracao_total()',
                      'identificar_dependencias()', 'gerar_relatorio()'],
                     'optimizer')
    
    # GeradorJanelasTemporais
    create_class_box(ax, 15.5, 4, 4, 2.5,
                     'GeradorJanelasTemporais', 
                     ['gerar_janelas_todos_pedidos()', 'gerar_janelas_pedido()',
                      'calcular_janelas_validas()', 'aplicar_restricoes_temporais()',
                      'validar_janela()', 'otimizar_distribuicao()'],
                     'optimizer')

    # ========================================================================
    # ENUMS E UTILITÁRIOS - Parte inferior
    # ========================================================================
    
    # TipoItem
    create_class_box(ax, 5, 2.5, 2, 1.5,
                     'TipoItem (Enum)', 
                     ['PRODUTO', 'SUBPRODUTO', 'INSUMO'],
                     'enum')
    
    # TipoEquipamento  
    create_class_box(ax, 7.5, 2.5, 2, 1.5,
                     'TipoEquipamento (Enum)', 
                     ['MISTURADORAS', 'FORNOS', 'BATEDEIRAS'],
                     'enum')
    
    # TipoProfissional
    create_class_box(ax, 10, 2.5, 2, 1.5,
                     'TipoProfissional (Enum)', 
                     ['PADEIRO', 'CONFEITEIRO', 'AUXILIAR'],
                     'enum')
    
    # Funcionario
    create_class_box(ax, 12.5, 2.5, 2, 1.5,
                     'Funcionario', 
                     ['registrar_ocupacao()', 'esta_disponivel()'],
                     'model')
    
    # Logger
    create_class_box(ax, 0.5, 1, 3, 1,
                     'Logger System', 
                     ['setup_logger()', 'log_quantity_error()'],
                     'utils')

    # ========================================================================
    # CONEXÕES E RELACIONAMENTOS
    # ========================================================================
    
    # Herança - Equipamentos específicos herdam de Equipamento
    create_connection(ax, 2.25, 13, 2.25, 12.5)  # Equipamento -> Masseira
    create_connection(ax, 2.25, 13, 2.25, 9.5)   # Equipamento -> Forno
    
    # Composição - PedidoDeProducao contém AtividadeModular
    create_connection(ax, 7, 11, 7, 10.5)
    
    # Dependência - PedidoDeProducao usa Almoxarifado
    create_connection(ax, 5, 12.5, 4, 5.5, '--')
    
    # Uso - AtividadeModular usa Gestores de Equipamentos
    create_connection(ax, 9, 8.5, 10, 10.5, '--')
    
    # Composição - GestorProducao usa ExecutorPedidos
    create_connection(ax, 12, 13, 12, 6.5)
    
    # Uso - OtimizadorIntegrado usa outros componentes do otimizador
    create_connection(ax, 17.5, 13, 17.5, 12.5)  # -> ModeloPL
    create_connection(ax, 17.5, 10, 17.5, 9.5)   # -> ExtratorDados
    create_connection(ax, 17.5, 7, 17.5, 6.5)    # -> GeradorJanelas

    # ========================================================================
    # TÍTULO E LEGENDA
    # ========================================================================
    
    ax.text(10, 15.5, 'SIVIRA - Diagrama de Classes do Sistema de Produção', 
            ha='center', va='center', fontsize=18, fontweight='bold')
    
    # Legenda
    legend_elements = [
        mpatches.Patch(color=colors['model'], label='Modelos de Domínio'),
        mpatches.Patch(color=colors['service'], label='Gestores/Serviços'),  
        mpatches.Patch(color=colors['controller'], label='Controladores'),
        mpatches.Patch(color=colors['optimizer'], label='Otimizador'),
        mpatches.Patch(color=colors['enum'], label='Enums'),
        mpatches.Patch(color=colors['utils'], label='Utilitários')
    ]
    
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(0, 1))
    
    # Adicionar informações sobre relacionamentos
    ax.text(0.5, 0.3, 'Relacionamentos: → Herança/Composição   ⋯ Dependência/Uso', 
            ha='left', va='center', fontsize=10, style='italic')
    
    plt.tight_layout()
    plt.savefig('diagrama_classes_sivira.png', dpi=300, bbox_inches='tight', 
                facecolor='white', edgecolor='none')
    
    print("✅ Diagrama de classes gerado: diagrama_classes_sivira.png")
    return "diagrama_classes_sivira.png"

if __name__ == "__main__":
    print("🔄 Gerando diagrama de classes do sistema SIVIRA...")
    filename = create_class_diagram()
    print(f"📊 Arquivo gerado: {filename}")
    print("📋 Principais componentes mapeados:")
    print("   • Modelos de domínio (Equipamento, PedidoDeProducao, AtividadeModular)")
    print("   • Gestores e serviços de produção")
    print("   • Sistema de otimização com PL")
    print("   • Enums e utilitários de apoio")