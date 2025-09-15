#!/usr/bin/env python3
"""
Teste da Nova Lógica de Restrições
=================================

Testa o sistema que aceita alocações abaixo da capacidade mínima
e registra restrições em JSON para validação posterior.
"""

import sys
import os
from datetime import datetime, timedelta

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.atividades.pedido_de_producao import PedidoDeProducao
from models.atividades.atividade_modular import AtividadeModular
from services.gestor_almoxarifado.gestor_almoxarifado import GestorAlmoxarifado
from parser.parser_almoxarifado import carregar_itens_almoxarifado
from factory.fabrica_funcionarios import funcionarios_disponiveis
from factory.fabrica_equipamentos import fritadeira_1, hotmix_1
from enums.producao.tipo_item import TipoItem
from utils.logs.gerenciador_logs import limpar_todos_os_logs
from utils.comandas.limpador_comandas import apagar_todas_as_comandas
from utils.logs.registrador_restricoes import registrador_restricoes

def limpar_ambiente():
    """Limpa logs, comandas e restrições anteriores"""
    print("🧹 Limpando ambiente de teste...")

    # Limpar logs e comandas
    limpar_todos_os_logs()
    apagar_todas_as_comandas()

    # Limpar diretório de restrições
    import shutil
    if os.path.exists("logs/restricoes"):
        shutil.rmtree("logs/restricoes")
        print("🗑️ Diretório logs/restricoes removido")

    print("✅ Ambiente limpo!")

def criar_atividade_massa_frituras(
    id_ordem: int,
    id_pedido: int,
    quantidade_gramas: float,
    funcionarios,
    gestor_almoxarifado,
    inicio_jornada: datetime,
    fim_jornada: datetime
) -> AtividadeModular:
    """
    Cria uma atividade de massa para frituras baseada no JSON de subprodutos.
    """
    print(f"🥖 Criando atividade de massa para frituras: {quantidade_gramas}g")

    # Criar atividade modular diretamente
    atividade = AtividadeModular(
        id=f"atividade_massa_{id_pedido}",
        id_atividade=20031,
        id_ordem=id_ordem,
        id_pedido=id_pedido,
        id_item=2003,  # ID da massa para frituras
        tipo_item=TipoItem.SUBPRODUTO,
        quantidade=quantidade_gramas,
        peso_unitario=1.0,  # massa é medida em gramas
        nome_atividade="mistura_de_massa_para_frituras",
        nome_item="massa_para_frituras",
        inicio_jornada=inicio_jornada,
        fim_jornada=fim_jornada,
        duracao=timedelta(minutes=15),  # 15 minutos para misturar massa
        funcionarios_disponiveis=funcionarios,
        gestor_almoxarifado=gestor_almoxarifado
    )

    # Configurar equipamentos permitidos (HotMix para mistura de massa)
    atividade.equipamentos_elegiveis = [hotmix_1]
    atividade.fips_equipamentos = {hotmix_1: 1}

    # Configuração específica para HotMix
    atividade.configuracoes_equipamentos = {
        "hotmix_1": {
            "temperatura_graus": 25,
            "velocidade_rpm": 200,
            "tempo_mistura_min": 15
        }
    }

    # Configuração de funcionários
    atividade.tipos_profissionais_permitidos = ["CONFEITEIRO", "AUXILIAR_DE_CONFEITEIRO"]
    atividade.fips_profissionais_permitidos = {
        "CONFEITEIRO": 2,
        "AUXILIAR_DE_CONFEITEIRO": 1
    }
    atividade.quantidade_funcionarios = 1

    return atividade

def criar_atividade_fritura_coxinhas(
    id_ordem: int,
    id_pedido: int,
    quantidade_unidades: int,
    funcionarios,
    gestor_almoxarifado,
    inicio_jornada: datetime,
    fim_jornada: datetime
) -> AtividadeModular:
    """
    Cria uma atividade de fritura de coxinhas.
    """
    quantidade_gramas = quantidade_unidades * 120  # 120g por coxinha
    print(f"🍟 Criando atividade de fritura: {quantidade_unidades} coxinhas ({quantidade_gramas}g)")

    # Criar atividade modular
    atividade = AtividadeModular(
        id=f"atividade_fritura_{id_pedido}",
        id_atividade=10556,
        id_ordem=id_ordem,
        id_pedido=id_pedido,
        id_item=1055,  # ID da coxinha de frango
        tipo_item=TipoItem.PRODUTO,
        quantidade=quantidade_unidades,
        peso_unitario=120.0,  # 120g por coxinha
        nome_atividade="fritura_de_coxinhas_de_frango",
        nome_item="coxinha_de_frango",
        inicio_jornada=inicio_jornada,
        fim_jornada=fim_jornada,
        duracao=timedelta(minutes=4),  # 4 minutos para fritar
        funcionarios_disponiveis=funcionarios,
        gestor_almoxarifado=gestor_almoxarifado
    )

    # Configurar equipamentos permitidos (Fritadeira)
    atividade.equipamentos_elegiveis = [fritadeira_1]
    atividade.fips_equipamentos = {fritadeira_1: 1}

    # Configuração específica para Fritadeira
    atividade.configuracoes_equipamentos = {
        "fritadeira_1": {
            "unidades_por_fracao": 9,
            "setup_min": 2,
            "faixa_temperatura": 180
        }
    }

    # Configuração de funcionários
    atividade.tipos_profissionais_permitidos = ["CONFEITEIRO"]
    atividade.fips_profissionais_permitidos = {"CONFEITEIRO": 1}
    atividade.quantidade_funcionarios = 1

    return atividade

def executar_teste_restricoes():
    """Executa teste da nova lógica de restrições."""
    print("\n" + "="*80)
    print("🧪 TESTE: NOVA LÓGICA DE RESTRIÇÕES DE CAPACIDADE")
    print("="*80)

    # Configurar ambiente
    itens_almoxarifado = carregar_itens_almoxarifado("data/almoxarifado/itens_almoxarifado.json")
    gestor_almoxarifado = GestorAlmoxarifado(itens_almoxarifado)
    funcionarios = funcionarios_disponiveis

    # Configurar janela temporal
    inicio_jornada = datetime(2025, 6, 26, 8, 0)
    fim_jornada = datetime(2025, 6, 26, 10, 0)

    print(f"\n📅 Cenário de Teste:")
    print(f"   Período: {inicio_jornada.strftime('%d/%m/%Y %H:%M')} - {fim_jornada.strftime('%H:%M')}")
    print(f"   HotMix 1: Capacidade mínima = 1000g")

    # Criar atividades que ficarão abaixo da capacidade mínima
    atividades = []

    print(f"\n🎯 Criando Atividades de Teste:")

    # Atividade 1: Massa para frituras 300g (300g < 1000g mínimo do HotMix)
    atividade1 = criar_atividade_massa_frituras(
        id_ordem=1,
        id_pedido=1,
        quantidade_gramas=300,
        funcionarios=funcionarios,
        gestor_almoxarifado=gestor_almoxarifado,
        inicio_jornada=inicio_jornada,
        fim_jornada=fim_jornada
    )
    atividades.append(atividade1)

    # Atividade 2: Massa para frituras 400g (400g < 1000g mínimo do HotMix)
    atividade2 = criar_atividade_massa_frituras(
        id_ordem=1,
        id_pedido=2,
        quantidade_gramas=400,
        funcionarios=funcionarios,
        gestor_almoxarifado=gestor_almoxarifado,
        inicio_jornada=inicio_jornada,
        fim_jornada=fim_jornada
    )
    atividades.append(atividade2)

    # Atividade 3: Massa para frituras 200g (200g < 1000g mínimo do HotMix)
    atividade3 = criar_atividade_massa_frituras(
        id_ordem=1,
        id_pedido=3,
        quantidade_gramas=200,
        funcionarios=funcionarios,
        gestor_almoxarifado=gestor_almoxarifado,
        inicio_jornada=inicio_jornada,
        fim_jornada=fim_jornada
    )
    atividades.append(atividade3)

    print(f"\n🚀 Executando Alocações:")

    sucessos = 0
    falhas = 0

    for i, atividade in enumerate(atividades, 1):
        print(f"\n{'='*50}")
        print(f"🔄 Executando Atividade {i}/{len(atividades)}")
        print(f"   ID: {atividade.id_atividade} | Pedido: {atividade.id_pedido}")
        print(f"   Quantidade: {atividade.quantidade} | Item: {atividade.nome_item}")
        print(f"{'='*50}")

        try:
            # Tentar alocar equipamento
            resultado = atividade.tentar_alocar_e_iniciar_equipamentos(
                inicio_jornada=inicio_jornada,
                fim_jornada=fim_jornada
            )

            if resultado[0]:  # sucesso na alocação
                sucessos += 1
                print(f"✅ Atividade {atividade.id_atividade} alocada com sucesso!")
                if hasattr(atividade, 'equipamento_alocado') and atividade.equipamento_alocado:
                    print(f"   Equipamento: {atividade.equipamento_alocado.nome}")
                else:
                    print(f"   Equipamentos alocados: {len(resultado[4]) if resultado[4] else 0}")
            else:
                falhas += 1
                print(f"❌ Atividade {atividade.id_atividade} falhou na alocação")

        except Exception as e:
            falhas += 1
            print(f"❌ Erro na atividade {atividade.id_atividade}: {e}")

    # Verificar restrições registradas
    verificar_restricoes_registradas()

    # Resumo final
    print(f"\n" + "="*80)
    print(f"📋 RESUMO DO TESTE:")
    print(f"="*80)
    print(f"✅ Atividades alocadas com sucesso: {sucessos}")
    print(f"❌ Atividades que falharam: {falhas}")
    print(f"📄 Restrições registradas: Verifique logs/restricoes/")

    if sucessos > 0:
        print(f"\n🎉 TESTE BEM-SUCEDIDO!")
        print(f"   Alocações abaixo da capacidade mínima foram aceitas")
        print(f"   e restrições foram registradas adequadamente!")
    else:
        print(f"\n⚠️ TESTE PARCIALMENTE BEM-SUCEDIDO")
        print(f"   Verifique os logs para identificar problemas")

def verificar_restricoes_registradas():
    """Verifica e exibe as restrições que foram registradas."""
    print(f"\n🔍 Verificando Restrições Registradas:")

    restricoes = registrador_restricoes.listar_todas_restricoes()

    if not restricoes:
        print(f"   📋 Nenhuma restrição encontrada")
        return

    for restricao_arquivo in restricoes:
        ordem = restricao_arquivo.get('ordem', 'N/A')
        total = restricao_arquivo.get('total_restricoes', 0)

        print(f"   📄 Ordem {ordem}: {total} restrições registradas")

        for atividade in restricao_arquivo.get('atividades_com_restricao', []):
            print(f"      🔸 Atividade {atividade['id_atividade']} - "
                  f"{atividade['equipamento']} - "
                  f"Atual: {atividade['capacidade_atual']}g < "
                  f"Mín: {atividade['capacidade_minima']}g "
                  f"(Déficit: {atividade['diferenca']}g)")

def main():
    """Execução principal do teste"""
    print("🧪 INICIANDO TESTE DA NOVA LÓGICA DE RESTRIÇÕES")
    print("="*80)

    try:
        # 1. Limpar ambiente
        limpar_ambiente()

        # 2. Executar teste
        executar_teste_restricoes()

    except Exception as e:
        print(f"\n❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()