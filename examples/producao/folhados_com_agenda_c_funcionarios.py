import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../../'))
from datetime import datetime, timedelta
from models.atividades.pedido_de_producao import PedidoDeProducao
from models.almoxarifado.almoxarifado import Almoxarifado
from services.gestores.almoxarifado.gestor_almoxarifado import GestorAlmoxarifado
from services.gestores.funcionarios.gestor_tipo_funcionarios import GestorTipoFuncionarios
from factory.fabrica_funcionarios import funcionarios_disponiveis
from parser.carregador_json_itens_almoxarifado import carregar_itens_almoxarifado
from utils.logs.gerenciador_logs import limpar_todos_os_logs, limpar_logs_erros, limpar_logs_inicializacao
from services.gestores.comandas.gestor_comandas import gerar_comanda_reserva
from utils.comandas.limpador_comandas import apagar_todas_as_comandas
from utils.ordenador.ordenador_pedidos import ordenar_pedidos_por_restricoes
from enums.producao.tipo_item import TipoItem


class TesteGestorTipoFuncionarios:
    """
    Teste específico para validar o GestorTipoFuncionarios.
    Executa alguns pedidos de folhados e coleta os requisitos de funcionários.
    """

    def __init__(self):
        self.almoxarifado = None
        self.gestor_almoxarifado = None
        self.pedidos = []
        self.gestor_funcionarios = GestorTipoFuncionarios(id_ordem=1)

        self.mapeamento_produtos = {
            "Folhado de Frango": 1072,
            "Folhado de Camarão": 1073
        }

    def inicializar_almoxarifado(self):
        """Carrega e inicializa o almoxarifado"""
        print("🔄 Carregando itens do almoxarifado...")

        # Carregar itens do arquivo JSON
        itens = carregar_itens_almoxarifado("data/almoxarifado/itens_almoxarifado.json")

        # Limpar dados anteriores
        apagar_todas_as_comandas()
        limpar_todos_os_logs()
        limpar_logs_erros()
        limpar_logs_inicializacao()

        # Inicializar almoxarifado
        self.almoxarifado = Almoxarifado()
        for item in itens:
            self.almoxarifado.adicionar_item(item)

        # Criar gestor
        self.gestor_almoxarifado = GestorAlmoxarifado(self.almoxarifado)

        print("✅ Almoxarifado carregado com sucesso!")

    def criar_pedidos_teste(self):
        """Cria pedidos simplificados para teste"""
        print("🔄 Criando pedidos de teste...")
        self.pedidos = []

        # Data base para os cálculos
        data_base = datetime(2025, 6, 26)

        # Configurações simples
        configuracoes_pedidos = [
            {"produto": "Folhado de Frango", "quantidade": 10, "hora_fim": 8},
            {"produto": "Folhado de Camarão", "quantidade": 8, "hora_fim": 9},
        ]

        id_pedido_counter = 1

        for config in configuracoes_pedidos:
            print(f"   Criando pedido {id_pedido_counter}: {config['produto']} - {config['quantidade']} unidades...")

            try:
                # Calcular datas
                fim_jornada = data_base.replace(hour=config['hora_fim'], minute=0, second=0, microsecond=0)
                inicio_jornada = fim_jornada - timedelta(days=1)  # 1 dia para simplicidade

                # Obter ID do produto
                id_produto = self.mapeamento_produtos.get(config['produto'])
                if id_produto is None:
                    print(f"   ⚠️ Produto '{config['produto']}' não encontrado!")
                    continue

                pedido = PedidoDeProducao(
                    id_ordem=1,
                    id_pedido=id_pedido_counter,
                    id_produto=id_produto,
                    tipo_item=TipoItem.PRODUTO,
                    quantidade=config['quantidade'],
                    inicio_jornada=inicio_jornada,
                    fim_jornada=fim_jornada,
                    todos_funcionarios=funcionarios_disponiveis
                )

                # Configurar gestor de funcionários no pedido
                pedido.gestor_tipo_funcionarios = self.gestor_funcionarios

                pedido.montar_estrutura()
                self.pedidos.append(pedido)
                print(f"   ✅ Pedido {id_pedido_counter} criado com sucesso!")

                id_pedido_counter += 1

            except Exception as e:
                print(f"   ⚠️ Erro ao criar pedido {id_pedido_counter}: {e}")
                id_pedido_counter += 1

        print(f"✅ Total de {len(self.pedidos)} pedidos criados!")

    def executar_pedidos(self):
        """Executa os pedidos e coleta requisitos de funcionários"""
        print("🔄 Executando pedidos...")

        for idx, pedido in enumerate(self.pedidos, 1):
            nome_produto = self._obter_nome_produto_por_id(pedido.id_produto)

            print(f"\n   Executando pedido {idx}/{len(self.pedidos)} (ID: {pedido.id_pedido})...")
            print(f"   📋 {nome_produto} - {pedido.quantidade} unidades")

            try:
                # Gerar comanda de reserva
                gerar_comanda_reserva(
                    id_ordem=pedido.id_ordem,
                    id_pedido=pedido.id_pedido,
                    ficha=pedido.ficha_tecnica_modular,
                    gestor=self.gestor_almoxarifado,
                    data_execucao=pedido.inicio_jornada
                )

                # Mostrar estrutura
                pedido.mostrar_estrutura()

                # Criar atividades modulares
                pedido.criar_atividades_modulares_necessarias()

                # Executar atividades
                pedido.executar_atividades_em_ordem()

                print(f"   ✅ Pedido {pedido.id_pedido} executado com sucesso!")

            except Exception as e:
                print(f"   ⚠️ Erro ao executar pedido {pedido.id_pedido}: {e}")

    def _obter_nome_produto_por_id(self, id_produto):
        """Obtém nome do produto pelo ID"""
        return next((nome for nome, id_prod in self.mapeamento_produtos.items()
                    if id_prod == id_produto), f"Produto {id_produto}")

    def exibir_requisitos_coletados(self):
        """Exibe os requisitos de funcionários coletados"""
        print("\n" + "=" * 80)
        print("📋 REQUISITOS DE FUNCIONÁRIOS COLETADOS")
        print("=" * 80)

        # Estatísticas gerais
        stats = self.gestor_funcionarios.obter_estatisticas()
        print(f"📊 ESTATÍSTICAS GERAIS:")
        print(f"   Total de requisitos: {stats['total_requisitos']}")
        print(f"   Tipos profissionais únicos: {stats['tipos_unicos']}")
        print(f"   Atividades únicas: {stats['atividades_unicas']}")

        if stats['periodo_cobertura']['inicio']:
            print(f"   Período: {stats['periodo_cobertura']['inicio']} → {stats['periodo_cobertura']['fim']}")

        # Requisitos por tipo
        requisitos_por_tipo = self.gestor_funcionarios.obter_requisitos_por_tipo()

        print(f"\n👥 REQUISITOS POR TIPO PROFISSIONAL:")
        for tipo, requisitos in requisitos_por_tipo.items():
            print(f"\n🔸 {tipo.name} ({len(requisitos)} requisitos):")
            for req in requisitos:
                print(f"   • Atividade {req.id_atividade}: {req.nome_atividade}")
                print(f"     ⏰ {req.inicio.strftime('%H:%M')} - {req.fim.strftime('%H:%M')}")
                print(f"     👥 {req.quantidade} funcionários necessários")
                if req.fips:
                    print(f"     🎯 FIPs: {req.fips}")
                print()

        # Requisitos ordenados por horário
        requisitos_ordenados = self.gestor_funcionarios.obter_requisitos_por_horario()

        print(f"\n⏰ LINHA DO TEMPO DOS REQUISITOS:")
        for req in requisitos_ordenados:
            print(f"   {req.inicio.strftime('%H:%M')} - {req.fim.strftime('%H:%M')}: "
                  f"{req.tipo_profissional.name} para {req.nome_atividade} "
                  f"(Atividade {req.id_atividade})")

        print("\n" + "=" * 80)

    def executar_teste_completo(self):
        """Executa o teste completo"""
        try:
            print("🧪 TESTE DO GESTOR DE TIPOS DE FUNCIONÁRIOS")
            print("=" * 60)

            # Fase 1: Configuração
            self.inicializar_almoxarifado()

            # Fase 2: Criação dos pedidos
            self.criar_pedidos_teste()

            # Fase 3: Execução
            self.executar_pedidos()

            # Fase 4: Análise dos resultados
            self.exibir_requisitos_coletados()

            print("\n🎉 TESTE CONCLUÍDO COM SUCESSO!")
            return True

        except Exception as e:
            print(f"\n❌ ERRO NO TESTE: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Função principal"""
    teste = TesteGestorTipoFuncionarios()
    sucesso = teste.executar_teste_completo()

    if sucesso:
        print("\n✅ Teste executado com sucesso!")
        print("🔍 Verifique os requisitos coletados acima para validar o funcionamento.")
    else:
        print("\n❌ Teste falhou!")

    return sucesso


if __name__ == "__main__":
    main()