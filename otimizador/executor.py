"""
Executor - Otimizador com Modo Flexivel
========================================

Suporta ambos os modos:
- DETERMINISTICO: tempo_maximo_de_espera = 0 (atividades contiguas)
- FLEXIVEL: tempo_maximo_de_espera > 0 (janelas flexiveis)

Fluxo de Execucao:
1. FASE 0: Criar atividades modulares
2. FASE 1: Detectar modo (DETERMINISTICO ou FLEXIVEL)
3. FASE 2: Calcular horarios/janelas
4. FASE 3: Otimizar ordem via PL
5. FASE 4: Executar pedidos
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict
from dataclasses import dataclass
from utils.logs.logger_factory import setup_logger

logger = setup_logger('Executor')


@dataclass
class Solucao:
    """Classe de solucao para o Executor."""
    status_solver: str
    modo_detectado: str
    pedidos_atendidos: int
    tempo_resolucao: float
    makespan_minutos: float
    estatisticas: dict
    pedidos_executados: List[int]
    pedidos_com_erro: List[int]
    janelas_calculadas: Optional[Dict] = None


# Alias para compatibilidade
SolucaoV3 = Solucao


class Configurador:
    """Configurador para o Executor."""

    def __init__(self):
        self.gestor_almoxarifado = None
        self._inicializado = False

    def inicializar_almoxarifado(self):
        """Inicializa gestor de almoxarifado com dados reais."""
        try:
            from parser.parser_almoxarifado import ParserAlmoxarifado

            caminho_itens = "data/almoxarifado/itens_almoxarifado.json"
            parser_almoxarifado = ParserAlmoxarifado(caminho_itens)
            self.gestor_almoxarifado = parser_almoxarifado.criar_gestor()
            self._inicializado = True

            num_itens = len(self.gestor_almoxarifado.almoxarifado.itens)
            logger.info(f"Almoxarifado inicializado com {num_itens} itens")

            return True

        except Exception as e:
            logger.error(f"Erro ao inicializar almoxarifado: {e}")
            import traceback
            traceback.print_exc()
            return False


class Executor:
    """
    Executor - Com suporte a Modo Flexivel.

    Detecta automaticamente o modo baseado em tau_max das atividades.
    """

    def __init__(self):
        self.logger = setup_logger('Executor')
        self.configurador = Configurador()
        self._inicializado = False
        self.ultimo_resultado = None

        # Resultados das fases
        self.modo_detectado = None
        self.estatisticas_modo = None
        self.janelas_calculadas = None
        self.horarios_calculados = None
        self.ordem_execucao = None

    def inicializar(self) -> bool:
        """Inicializa o executor."""
        if self._inicializado:
            return True

        try:
            self.logger.info("Inicializando Executor...")

            if not self.configurador.inicializar_almoxarifado():
                return False

            self._inicializado = True
            self.logger.info("Executor inicializado com sucesso")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao inicializar Executor: {e}")
            return False

    def otimizar_pedidos(
        self,
        pedidos: List,
        timeout_segundos: int = 600
    ) -> Optional[Solucao]:
        """
        Otimiza e executa pedidos com suporte a modo flexivel.

        Args:
            pedidos: Lista de objetos PedidoDeProducao
            timeout_segundos: Timeout para otimizacao

        Returns:
            Solucao com resultados da execucao
        """
        if not self._inicializado:
            self.logger.error("Executor nao foi inicializado!")
            return None

        tempo_inicio = datetime.now()

        try:
            self.logger.info(f"Otimizando {len(pedidos)} pedidos...")
            self.logger.info("=" * 70)

            # ================================================================
            # FASE 0: CRIAR ATIVIDADES MODULARES
            # ================================================================
            self.logger.info("FASE 0: Criando atividades modulares...")

            for pedido in pedidos:
                # Montar estrutura se ainda nao foi montada
                if not hasattr(pedido, 'ficha_tecnica_modular') or not pedido.ficha_tecnica_modular:
                    self.logger.info(f"   Montando estrutura do pedido {pedido.id_pedido}...")
                    pedido.montar_estrutura()

                # Criar atividades se ainda nao foram criadas
                if not pedido.atividades_modulares:
                    self.logger.info(f"   Criando atividades do pedido {pedido.id_pedido}...")
                    pedido.criar_atividades_modulares_necessarias()

                self.logger.info(
                    f"   Pedido {pedido.id_pedido}: {len(pedido.atividades_modulares)} atividades criadas"
                )

            self.logger.info(f"FASE 0 concluida: Atividades modulares criadas para {len(pedidos)} pedidos")
            self.logger.info("=" * 70)

            # ================================================================
            # FASE 1: DETECTAR MODO
            # ================================================================
            self.logger.info("FASE 1: Detectando modo de otimizacao...")

            from otimizador.detector_modo import DetectorModo, ModoOtimizacao
            detector = DetectorModo()
            self.modo_detectado, self.estatisticas_modo = detector.detectar_modo(pedidos)

            self.logger.info(f"   Modo detectado: {self.modo_detectado.value}")
            self.logger.info(f"   Pedidos deterministicos: {self.estatisticas_modo['pedidos_deterministicos']}")
            self.logger.info(f"   Pedidos flexiveis: {self.estatisticas_modo['pedidos_flexiveis']}")
            self.logger.info(f"   Total atividades: {self.estatisticas_modo.get('total_atividades_analisadas', 0)}")

            # Calcular atividades com gap a partir dos detalhes
            atividades_com_gap = sum(
                d.get('atividades_com_gap', 0)
                for d in self.estatisticas_modo.get('detalhes_por_pedido', [])
            )
            self.estatisticas_modo['atividades_com_gap'] = atividades_com_gap
            self.logger.info(f"   Atividades com gap > 0: {atividades_com_gap}")
            self.logger.info("=" * 70)

            # ================================================================
            # FASE 2: CALCULAR HORARIOS/JANELAS
            # ================================================================
            inicio_jornada = pedidos[0].inicio_jornada if pedidos else datetime.now().replace(hour=6, minute=0)

            if self.modo_detectado == ModoOtimizacao.DETERMINISTICO:
                self.logger.info("FASE 2: Calculando horarios deterministicos...")
                from otimizador.calculador_horarios_deterministicos import CalculadorHorariosDeterministicos

                calculador = CalculadorHorariosDeterministicos()
                self.horarios_calculados = calculador.calcular_horarios_fixos(pedidos, inicio_jornada)
                self.logger.info("   Horarios fixos calculados (gaps = 0)")

            else:
                # Modo FLEXIVEL: Calcular janelas
                self.logger.info("FASE 2: Calculando janelas flexiveis...")
                from otimizador.calculador_janelas import CalculadorJanelas

                calculador = CalculadorJanelas()
                self.janelas_calculadas = calculador.calcular(pedidos, inicio_jornada)

                # Log das janelas
                for id_pedido, janelas_pedido in self.janelas_calculadas.items():
                    total_flex = sum(
                        j.flexibilidade.total_seconds() / 60
                        for j in janelas_pedido.values()
                    )
                    self.logger.info(
                        f"   Pedido {id_pedido}: {len(janelas_pedido)} janelas, "
                        f"flexibilidade total: {total_flex:.0f} min"
                    )

            self.logger.info("=" * 70)

            # ================================================================
            # FASE 3: OTIMIZAR ORDEM
            # ================================================================
            self.logger.info("FASE 3: Otimizando ordem de execucao...")

            from otimizador.modelo_pl_ordenacao import ModeloPLOrdenacao
            modelo_pl = ModeloPLOrdenacao()

            if self.modo_detectado == ModoOtimizacao.DETERMINISTICO:
                resultado_otim = modelo_pl.otimizar_ordem_com_conflitos(
                    pedidos, self.horarios_calculados
                )
            else:
                # Para modo flexivel, usar ordenacao por deadline como fallback
                resultado_otim = modelo_pl.otimizar_ordem_execucao(pedidos, {})

            self.ordem_execucao = resultado_otim.get('ordem_execucao', [p.id_pedido for p in pedidos])
            self.logger.info(f"   Ordem otimizada: {self.ordem_execucao}")
            self.logger.info("=" * 70)

            # ================================================================
            # FASE 4: EXECUTAR PEDIDOS
            # ================================================================
            self.logger.info("FASE 4: Executando pedidos...")

            if self.modo_detectado == ModoOtimizacao.DETERMINISTICO:
                from otimizador.aplicador_ordenacao import AplicadorOrdenacao
                aplicador = AplicadorOrdenacao()
                resultado_exec = aplicador.executar_pedidos_em_ordem(pedidos, self.ordem_execucao)
            else:
                # Usar aplicador flexivel
                from otimizador.aplicador_flexivel import AplicadorFlexivel
                aplicador = AplicadorFlexivel(self.janelas_calculadas)
                resultado_exec = aplicador.executar_pedidos(pedidos, self.ordem_execucao)

            tempo_fim = datetime.now()
            tempo_total = (tempo_fim - tempo_inicio).total_seconds()

            # ================================================================
            # CRIAR SOLUCAO
            # ================================================================
            pedidos_executados = resultado_exec.get('pedidos_executados', [])
            pedidos_com_erro = resultado_exec.get('pedidos_com_erro', [])

            solucao = Solucao(
                status_solver="OTIMO" if len(pedidos_com_erro) == 0 else "VIAVEL",
                modo_detectado=self.modo_detectado.value,
                pedidos_atendidos=len(pedidos_executados),
                tempo_resolucao=tempo_total,
                makespan_minutos=resultado_exec.get('tempo_total', 0) / 60 if resultado_exec.get('tempo_total') else tempo_total,
                estatisticas={
                    'modo': self.modo_detectado.value,
                    'pedidos_deterministicos': self.estatisticas_modo['pedidos_deterministicos'],
                    'pedidos_flexiveis': self.estatisticas_modo['pedidos_flexiveis'],
                    'atividades_com_gap': self.estatisticas_modo['atividades_com_gap'],
                    'taxa_sucesso': resultado_exec.get('taxa_sucesso', 0),
                    'ordem_execucao': self.ordem_execucao
                },
                pedidos_executados=pedidos_executados,
                pedidos_com_erro=pedidos_com_erro,
                janelas_calculadas=self.janelas_calculadas
            )

            self.ultimo_resultado = solucao

            self.logger.info("=" * 70)
            self.logger.info("EXECUCAO CONCLUIDA")
            self.logger.info(f"   Modo: {solucao.modo_detectado}")
            self.logger.info(f"   Pedidos atendidos: {solucao.pedidos_atendidos}/{len(pedidos)}")
            self.logger.info(f"   Taxa de sucesso: {solucao.estatisticas['taxa_sucesso']:.1f}%")
            self.logger.info(f"   Tempo total: {tempo_total:.2f}s")
            self.logger.info("=" * 70)

            return solucao

        except Exception as e:
            self.logger.error(f"Erro na otimizacao: {e}")
            import traceback
            traceback.print_exc()
            return None

    def imprimir_resumo_solucao(self, solucao: Solucao, pedidos: List):
        """Imprime resumo da solucao."""
        print("\n" + "=" * 70)
        print("RESUMO DA SOLUCAO PL")
        print("=" * 70)

        print(f"\nModo detectado: {solucao.modo_detectado}")
        print(f"Pedidos executados: {solucao.pedidos_atendidos}/{len(pedidos)}")

        if solucao.pedidos_executados:
            print(f"   IDs sucesso: {', '.join(map(str, solucao.pedidos_executados))}")

        if solucao.pedidos_com_erro:
            print(f"\nPedidos com erro: {len(solucao.pedidos_com_erro)}")
            print(f"   IDs erro: {', '.join(map(str, solucao.pedidos_com_erro))}")

        print(f"\nEstatisticas:")
        print(f"   Pedidos deterministicos: {solucao.estatisticas.get('pedidos_deterministicos', 0)}")
        print(f"   Pedidos flexiveis: {solucao.estatisticas.get('pedidos_flexiveis', 0)}")
        print(f"   Atividades com gap > 0: {solucao.estatisticas.get('atividades_com_gap', 0)}")
        print(f"   Taxa de sucesso: {solucao.estatisticas.get('taxa_sucesso', 0):.1f}%")

        if solucao.janelas_calculadas:
            print(f"\nJanelas flexiveis calculadas para {len(solucao.janelas_calculadas)} pedidos")

        print("\n" + "=" * 70)

    def comparar_com_baseline(self, solucao: Solucao, num_pedidos: int):
        """Compara resultado com baseline."""
        print("\n" + "=" * 70)
        print("COMPARACAO COM BASELINE")
        print("=" * 70)

        taxa_baseline_seq = 84.6  # Sistema Sequencial
        taxa_obtida = (solucao.pedidos_atendidos / num_pedidos * 100) if num_pedidos > 0 else 0

        print(f"\nSistema Sequencial (baseline): ~{taxa_baseline_seq:.1f}%")
        print(f"Otimizado PL (obtido): {taxa_obtida:.1f}%")
        print(f"Modo utilizado: {solucao.modo_detectado}")

        if solucao.modo_detectado == "FLEXIVEL":
            print("\nNota: Modo FLEXIVEL permite gaps entre atividades (tau_max > 0)")
            print("      Isso pode resultar em diferentes alocacoes de equipamentos.")

        print("\n" + "=" * 70)


# Aliases para compatibilidade
ExecutorV3 = Executor
ConfiguradorV3 = Configurador


def criar_executor() -> Executor:
    """Cria e inicializa um Executor."""
    executor = Executor()
    executor.inicializar()
    return executor


# Alias para compatibilidade
criar_executor_v3 = criar_executor
