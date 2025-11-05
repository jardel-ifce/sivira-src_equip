"""
Recuperador de Estado Principal
================================

Orquestrador que coordena todo o processo de recuperação de estado.
"""

import re
from typing import Dict, Type, Optional
from utils.recuperacao.detector_logs import DetectorLogs
from utils.recuperacao.modelos import (
    OcupacaoDTO,
    EstadoEquipamentoDTO,
    RelatorioRecuperacaoDTO
)
from utils.recuperacao.parsers import (
    ParserBase,
    ParserBancada,
    ParserCamaraRefrigerada,
    ParserFreezer,
    ParserFogao,
    ParserBalanca,
    ParserMasseira,
    ParserBatedeira,
    ParserHotMix,
    ParserFritadeira,
    ParserArmario,
    ParserDivisora,
    ParserModeladora,
    ParserEmbaladora,
    ParserForno
)
from utils.recuperacao.restauradores import (
    RestauradorBase,
    RestauradorBancada,
    RestauradorCamaraRefrigerada,
    RestauradorFreezer,
    RestauradorFogao,
    RestauradorBalanca,
    RestauradorMasseira,
    RestauradorBatedeira,
    RestauradorHotMix,
    RestauradorFritadeira,
    RestauradorArmario,
    RestauradorDivisora,
    RestauradorModeladora,
    RestauradorEmbaladora,
    RestauradorForno
)
from utils.recuperacao.validadores import ValidadorOcupacoes, ValidadorConsistencia


class RecuperadorEstado:
    """
    🔄 Orquestrador principal de recuperação de estado

    Processo de recuperação:
    1. Detecta e valida log
    2. Para cada equipamento no log:
       a. Identifica tipo do equipamento
       b. Seleciona parser apropriado
       c. Extrai ocupações (parsing)
       d. Seleciona restaurador apropriado
       e. Restaura estado no objeto
    3. Valida recuperação
    4. Retorna relatório
    """

    # Mapeamento de tipos de equipamento para parsers
    PARSERS: Dict[str, Type[ParserBase]] = {
        'Bancada': ParserBancada,
        'CamaraRefrigerada': ParserCamaraRefrigerada,
        'Freezer': ParserFreezer,
        'Fogao': ParserFogao,
        'BalancaDigital': ParserBalanca,
        'Masseira': ParserMasseira,
        'BatedeiraIndustrial': ParserBatedeira,
        'BatedeiraPlanetaria': ParserBatedeira,
        'HotMix': ParserHotMix,
        'Fritadeira': ParserFritadeira,
        'ArmarioEsqueleto': ParserArmario,
        'ArmarioFermentador': ParserArmario,
        'DivisoraDeMassas': ParserDivisora,
        'ModeladoraDePaes': ParserModeladora,
        'ModeladoraDeSalgados': ParserModeladora,
        'Embaladora': ParserEmbaladora,
        'Forno': ParserForno
    }

    # Mapeamento de tipos de equipamento para restauradores
    RESTAURADORES: Dict[str, Type[RestauradorBase]] = {
        'Bancada': RestauradorBancada,
        'CamaraRefrigerada': RestauradorCamaraRefrigerada,
        'Freezer': RestauradorFreezer,
        'Fogao': RestauradorFogao,
        'BalancaDigital': RestauradorBalanca,
        'Masseira': RestauradorMasseira,
        'BatedeiraIndustrial': RestauradorBatedeira,
        'BatedeiraPlanetaria': RestauradorBatedeira,
        'HotMix': RestauradorHotMix,
        'Fritadeira': RestauradorFritadeira,
        'ArmarioEsqueleto': RestauradorArmario,
        'ArmarioFermentador': RestauradorArmario,
        'DivisoraDeMassas': RestauradorDivisora,
        'ModeladoraDePaes': RestauradorModeladora,
        'ModeladoraDeSalgados': RestauradorModeladora,
        'Embaladora': RestauradorEmbaladora,
        'Forno': RestauradorForno
    }

    def __init__(self, gestor_producao=None):
        """
        Inicializa recuperador

        Args:
            gestor_producao: Instância do GestorProducao para acesso aos equipamentos
        """
        self.gestor_producao = gestor_producao
        self.detector = DetectorLogs()
        self.validador_ocupacoes = ValidadorOcupacoes()
        self.validador_consistencia = ValidadorConsistencia()

    def recuperar_de_log(
        self,
        caminho_log: str,
        aplicar_restauracao: bool = True
    ) -> RelatorioRecuperacaoDTO:
        """
        Recupera estado a partir de um arquivo de log

        Args:
            caminho_log: Caminho do arquivo de log
            aplicar_restauracao: Se deve aplicar restauração nos objetos
                                (False = apenas parsing e validação)

        Returns:
            RelatorioRecuperacaoDTO com resultado da recuperação
        """
        relatorio = RelatorioRecuperacaoDTO(caminho_log=caminho_log)

        try:
            print(f"\n🔄 Iniciando recuperação de estado...")
            print(f"📄 Log: {caminho_log}")

            # 1. Validar log
            print("\n1️⃣ Validando estrutura do log...")
            valido, erros = self.detector.validar_estrutura_log(caminho_log)
            if not valido:
                for erro in erros:
                    relatorio.adicionar_erro_global(f"Validação de log: {erro}")
                relatorio.sucesso = False
                return relatorio

            relatorio.adicionar_mensagem("Estrutura do log validada com sucesso")

            # 2. Extrair lista de equipamentos
            print("\n2️⃣ Extraindo lista de equipamentos...")
            equipamentos_log = self.detector.extrair_equipamentos_do_log(caminho_log)
            print(f"   Encontrados {len(equipamentos_log)} equipamentos")
            relatorio.adicionar_mensagem(f"Encontrados {len(equipamentos_log)} equipamentos no log")

            # 3. Ler conteúdo do log
            with open(caminho_log, 'r', encoding='utf-8') as f:
                conteudo_log = f.read()

            # 4. Processar cada equipamento
            print("\n3️⃣ Processando equipamentos...")
            for nome_equip, tipo_equip in equipamentos_log:
                estado = self._processar_equipamento(
                    nome_equip,
                    tipo_equip,
                    conteudo_log,
                    aplicar_restauracao
                )
                relatorio.adicionar_equipamento(estado)

            # 5. Validar recuperação
            print("\n4️⃣ Validando recuperação...")
            self._validar_recuperacao(relatorio)

            # 6. Definir sucesso
            relatorio.sucesso = not relatorio.tem_erros

            # Mensagem final
            if relatorio.sucesso:
                print(f"\n✅ Recuperação concluída com sucesso!")
                print(f"   • {relatorio.equipamentos_restaurados} equipamentos restaurados")
                print(f"   • {relatorio.total_ocupacoes_recuperadas} ocupações recuperadas")
            else:
                print(f"\n⚠️ Recuperação concluída com erros")
                print(f"   • {relatorio.total_erros} erro(s) encontrado(s)")

        except Exception as e:
            erro = f"Erro inesperado durante recuperação: {e}"
            relatorio.adicionar_erro_global(erro)
            relatorio.sucesso = False
            print(f"\n❌ {erro}")

        return relatorio

    def _processar_equipamento(
        self,
        nome_equipamento: str,
        tipo_equipamento: str,
        conteudo_log: str,
        aplicar_restauracao: bool
    ) -> EstadoEquipamentoDTO:
        """
        Processa um equipamento individual

        Args:
            nome_equipamento: Nome do equipamento
            tipo_equipamento: Tipo do equipamento
            conteudo_log: Conteúdo completo do log
            aplicar_restauracao: Se deve aplicar restauração

        Returns:
            EstadoEquipamentoDTO com resultado do processamento
        """
        print(f"\n   🔧 {nome_equipamento} ({tipo_equipamento})")
        estado = EstadoEquipamentoDTO(
            nome_equipamento=nome_equipamento,
            tipo_equipamento=tipo_equipamento
        )

        try:
            # Extrair seção do equipamento do log
            secao_equipamento = self._extrair_secao_equipamento(
                conteudo_log,
                nome_equipamento,
                tipo_equipamento
            )

            if not secao_equipamento:
                estado.adicionar_erro("Não foi possível extrair seção do log")
                print(f"      ⚠️ Seção não encontrada")
                return estado

            # Selecionar parser apropriado
            parser = self._obter_parser(tipo_equipamento)
            if not parser:
                estado.adicionar_erro(f"Parser não disponível para tipo {tipo_equipamento}")
                print(f"      ⚠️ Parser não disponível")
                return estado

            # Parsing
            print(f"      📋 Extraindo ocupações...")
            ocupacoes = parser.parse(secao_equipamento, nome_equipamento)

            # Adicionar erros do parser
            for erro in parser.obter_erros():
                estado.adicionar_erro(f"Parser: {erro}")

            # Adicionar ocupações ao estado
            for ocupacao in ocupacoes:
                estado.adicionar_ocupacao(ocupacao)

            print(f"      ✓ {len(ocupacoes)} ocupação(ões) extraída(s)")

            # Restauração (se solicitado e houver ocupações)
            if aplicar_restauracao and ocupacoes:
                print(f"      🔄 Restaurando estado...")
                restaurador = self._obter_restaurador(tipo_equipamento)
                if not restaurador:
                    estado.adicionar_erro(f"Restaurador não disponível para tipo {tipo_equipamento}")
                    print(f"      ⚠️ Restaurador não disponível")
                    return estado

                # Obter objeto equipamento
                equipamento_obj = self._obter_objeto_equipamento(nome_equipamento)
                if not equipamento_obj:
                    estado.adicionar_erro("Não foi possível localizar objeto do equipamento")
                    print(f"      ⚠️ Objeto não encontrado")
                    return estado

                # Aplicar restauração
                sucesso = restaurador.restaurar(ocupacoes, equipamento_obj)
                estado.equipamento_restaurado = sucesso

                # Adicionar erros do restaurador
                for erro in restaurador.obter_erros():
                    estado.adicionar_erro(f"Restaurador: {erro}")

                if sucesso:
                    print(f"      ✅ Estado restaurado")
                else:
                    print(f"      ❌ Falha na restauração")

        except Exception as e:
            estado.adicionar_erro(f"Erro ao processar: {e}")
            print(f"      ❌ Erro: {e}")

        return estado

    def _extrair_secao_equipamento(
        self,
        conteudo_log: str,
        nome_equipamento: str,
        tipo_equipamento: str
    ) -> Optional[str]:
        """
        Extrai a seção de um equipamento específico do log

        Args:
            conteudo_log: Conteúdo completo do log
            nome_equipamento: Nome do equipamento
            tipo_equipamento: Tipo do equipamento

        Returns:
            String com a seção do equipamento ou None
        """
        try:
            # Padrão para início da seção
            # 🔧 Nome do Equipamento (Tipo)
            # ============================================================
            pattern_inicio = rf'🔧\s+{re.escape(nome_equipamento)}\s+\({re.escape(tipo_equipamento)}\)'

            # Encontrar início
            match_inicio = re.search(pattern_inicio, conteudo_log)
            if not match_inicio:
                return None

            inicio = match_inicio.start()

            # Encontrar fim (próximo equipamento ou fim do log)
            # Procurar próximo 🔧 ou ESTATÍSTICAS RESUMIDAS
            pattern_fim = r'(?:🔧|ESTATÍSTICAS RESUMIDAS)'
            match_fim = re.search(pattern_fim, conteudo_log[inicio + len(match_inicio.group(0)):])

            if match_fim:
                fim = inicio + len(match_inicio.group(0)) + match_fim.start()
            else:
                fim = len(conteudo_log)

            return conteudo_log[inicio:fim]

        except Exception as e:
            print(f"   ⚠️ Erro ao extrair seção: {e}")
            return None

    def _obter_parser(self, tipo_equipamento: str) -> Optional[ParserBase]:
        """
        Obtém parser apropriado para o tipo de equipamento

        Args:
            tipo_equipamento: Tipo do equipamento

        Returns:
            Instância do parser ou None
        """
        parser_class = self.PARSERS.get(tipo_equipamento)
        if parser_class:
            return parser_class()
        return None

    def _obter_restaurador(self, tipo_equipamento: str) -> Optional[RestauradorBase]:
        """
        Obtém restaurador apropriado para o tipo de equipamento

        Args:
            tipo_equipamento: Tipo do equipamento

        Returns:
            Instância do restaurador ou None
        """
        restaurador_class = self.RESTAURADORES.get(tipo_equipamento)
        if restaurador_class:
            return restaurador_class()
        return None

    def _obter_objeto_equipamento(self, nome_equipamento: str):
        """
        Localiza objeto do equipamento

        Args:
            nome_equipamento: Nome do equipamento

        Returns:
            Objeto equipamento ou None
        """
        # Tentar primeiro pela fábrica de equipamentos (mais direto e confiável)
        try:
            from factory.fabrica_equipamentos import equipamentos_disponiveis

            for equipamento in equipamentos_disponiveis:
                if hasattr(equipamento, 'nome') and equipamento.nome == nome_equipamento:
                    return equipamento

        except ImportError:
            print("   ⚠️ Não foi possível importar fábrica de equipamentos")

        # Fallback: tentar pelo gestor_producao (se disponível)
        if self.gestor_producao and hasattr(self.gestor_producao, 'gestor_equipamentos'):
            try:
                # Buscar em todos os gestores de equipamentos
                for attr_name in dir(self.gestor_producao.gestor_equipamentos):
                    if not attr_name.startswith('_'):
                        attr = getattr(self.gestor_producao.gestor_equipamentos, attr_name)
                        if isinstance(attr, list):
                            for equip in attr:
                                if hasattr(equip, 'nome') and equip.nome == nome_equipamento:
                                    return equip
            except Exception as e:
                print(f"   ⚠️ Erro ao buscar no gestor: {e}")

        return None

    def _validar_recuperacao(self, relatorio: RelatorioRecuperacaoDTO):
        """
        Valida recuperação completa

        Args:
            relatorio: Relatório a validar
        """
        # Validar consistência geral
        self.validador_consistencia.validar_estados_equipamentos(relatorio.equipamentos)

        # Adicionar erros e avisos ao relatório
        for erro in self.validador_consistencia.obter_erros():
            relatorio.adicionar_erro_global(f"Validação: {erro}")

        for aviso in self.validador_consistencia.obter_avisos():
            relatorio.adicionar_mensagem(f"Aviso: {aviso}")
