import os
import re
from datetime import datetime
from enum import Enum
from models.funcionarios.funcionario import Funcionario
from typing import List, Tuple, Dict, Optional
from utils.logs.logger_factory import setup_logger
from enums.funcionarios.tipo_profissional import TipoProfissional
from utils.logs.gerenciador_logs import registrar_log_funcionarios
from utils.analise.analisador_conflitos import AnalisadorConflitos
from factory.fabrica_funcionarios import FabricaFuncionarios

logger = setup_logger("GestorFuncionarios")

class RequisitoFuncionario:
    """Representa um requisito de funcionário extraído dos logs."""
    def __init__(self, id_atividade: int, nome_atividade: str, horario_inicio: str,
                 data_inicio: str, horario_fim: str, data_fim: str, funcionarios_necessarios: int,
                 tipos_permitidos: List[str], fips: Dict[str, int]):
        self.id_atividade = id_atividade
        self.nome_atividade = nome_atividade
        self.horario_inicio = horario_inicio
        self.data_inicio = data_inicio
        self.horario_fim = horario_fim
        self.data_fim = data_fim
        self.funcionarios_necessarios = funcionarios_necessarios
        self.tipos_permitidos = tipos_permitidos
        self.fips = fips


class GestorFuncionarios:
    """
    Gestor expandido para alocação automática de funcionários.
    Lê requisitos de tipos_funcionarios_requeridos e aloca usando Factory.

    ⚠️ SINGLETON: Garante que apenas uma instância do gestor existe,
    mantendo as mesmas referências dos funcionários em memória.
    """

    _instance = None

    def __new__(cls):
        """
        Implementa o padrão Singleton.
        Garante que apenas uma instância do gestor existe.
        """
        if cls._instance is None:
            cls._instance = super(GestorFuncionarios, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # Evita reinicialização se já foi inicializado
        if self._initialized:
            return

        # Carrega funcionários do JSON via FabricaFuncionarios
        fabrica = FabricaFuncionarios()
        self.funcionarios_disponiveis = fabrica.carregar_funcionarios()

        # ⚠️ NOVO: Controle de pedidos já alocados
        # Set de tuplas (id_ordem, id_pedido) que já tiveram funcionários alocados
        self.pedidos_alocados = set()

        logger.info(f"🏭 GestorFuncionarios inicializado com {len(self.funcionarios_disponiveis)} funcionários")

        self._initialized = True

    def ler_requisitos_de_arquivo(self, id_ordem: int, id_pedido: int) -> List[RequisitoFuncionario]:
        """
        Lê requisitos de funcionários do arquivo de tipos_funcionarios_requeridos.

        Args:
            id_ordem: ID da ordem
            id_pedido: ID do pedido

        Returns:
            List[RequisitoFuncionario]: Lista de requisitos extraídos
        """
        caminho_arquivo = f"logs/tipos_funcionarios_requeridos/ordem: {id_ordem} | pedido: {id_pedido}.log"

        if not os.path.exists(caminho_arquivo):
            logger.warning(f"📄 Arquivo de requisitos não encontrado: {caminho_arquivo}")
            return []

        requisitos = []
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as arquivo:
                conteudo = arquivo.read()

                # Regex para extrair atividades (com datas)
                padrao_atividade = r'🔸 ATIVIDADE (\d+): (.+?)\n.*?⏰ Horário: (\d{2}:\d{2}) \[(\d{2}/\d{2}/\d{4})\] - (\d{2}:\d{2}) \[(\d{2}/\d{2}/\d{4})\]\n.*?👥 Funcionários necessários: (\d+)\n.*?👨‍💼 Tipos permitidos: (.+?)\n.*?🎯 Prioridades \(FIPs\): (.+?)\n'

                matches = re.findall(padrao_atividade, conteudo, re.DOTALL)

                for match in matches:
                    id_atividade = int(match[0])
                    nome_atividade = match[1].strip()
                    horario_inicio = match[2].strip()
                    data_inicio = match[3].strip()
                    horario_fim = match[4].strip()
                    data_fim = match[5].strip()
                    funcionarios_necessarios = int(match[6])
                    tipos_permitidos_str = match[7].strip()
                    fips_str = match[8].strip()

                    # Processar tipos permitidos
                    tipos_permitidos = [tipo.strip() for tipo in tipos_permitidos_str.split(',')]

                    # Processar FIPs
                    fips = {}
                    for fip_pair in fips_str.split(','):
                        if ':' in fip_pair:
                            tipo, valor = fip_pair.strip().split(':')
                            fips[tipo.strip()] = int(valor.strip())

                    requisito = RequisitoFuncionario(
                        id_atividade=id_atividade,
                        nome_atividade=nome_atividade,
                        horario_inicio=horario_inicio,
                        data_inicio=data_inicio,
                        horario_fim=horario_fim,
                        data_fim=data_fim,
                        funcionarios_necessarios=funcionarios_necessarios,
                        tipos_permitidos=tipos_permitidos,
                        fips=fips
                    )

                    requisitos.append(requisito)

                logger.info(f"📋 {len(requisitos)} requisitos carregados de {caminho_arquivo}")

        except Exception as e:
            logger.error(f"❌ Erro ao ler arquivo de requisitos {caminho_arquivo}: {e}")

        return requisitos

    def alocar_funcionarios_para_ordem_pedido(self, id_ordem: int, id_pedido: int) -> bool:
        """
        Aloca funcionários para todas as atividades de uma ordem|pedido.
        Implementa prioridade: funcionários já alocados no pedido têm preferência.

        ⚠️ NOVO: Bloqueia alocação se o pedido já foi alocado anteriormente.

        Args:
            id_ordem: ID da ordem
            id_pedido: ID do pedido

        Returns:
            bool: True se todas as alocações foram bem-sucedidas
        """
        # ⚠️ NOVO: Verificar se o pedido já foi alocado
        pedido_key = (id_ordem, id_pedido)
        if pedido_key in self.pedidos_alocados:
            logger.warning(f"🚫 Ordem {id_ordem} | Pedido {id_pedido} já teve funcionários alocados anteriormente!")
            logger.warning(f"💡 Use o método limpar_alocacao_pedido({id_ordem}, {id_pedido}) para permitir nova alocação")
            return False

        logger.info(f"🎯 Iniciando alocação para Ordem {id_ordem} | Pedido {id_pedido}")

        # Limpar ocupações anteriores dos funcionários (opcional - comentar se não quiser)
        # self._limpar_ocupacoes_funcionarios()

        # Carregar requisitos
        requisitos = self.ler_requisitos_de_arquivo(id_ordem, id_pedido)
        if not requisitos:
            logger.warning(f"⚠️ Nenhum requisito encontrado para Ordem {id_ordem} | Pedido {id_pedido}")
            return False

        # ⚠️ CORREÇÃO: Manter ordem reversa do arquivo (última atividade → primeira atividade)
        # Não reordenar - manter a ordem em que aparece no log de equipamentos
        requisitos_ordenados = requisitos

        alocacoes_realizadas = []
        alocacoes_falhadas = []
        sucesso_total = True

        for requisito in requisitos_ordenados:
            logger.info(f"🔄 Processando: {requisito.nome_atividade} ({requisito.horario_inicio}-{requisito.horario_fim})")
            logger.debug(f"   📋 Tipos requeridos: {requisito.tipos_permitidos}")

            # Converter horários e datas para datetime
            data_inicio_obj = datetime.strptime(requisito.data_inicio, '%d/%m/%Y').date()
            data_fim_obj = datetime.strptime(requisito.data_fim, '%d/%m/%Y').date()
            inicio = datetime.combine(data_inicio_obj, datetime.strptime(requisito.horario_inicio, '%H:%M').time())
            fim = datetime.combine(data_fim_obj, datetime.strptime(requisito.horario_fim, '%H:%M').time())

            # Converter tipos permitidos para enum
            tipos_enum = []
            for tipo_str in requisito.tipos_permitidos:
                try:
                    tipos_enum.append(TipoProfissional[tipo_str.strip()])
                except KeyError:
                    logger.warning(f"⚠️ Tipo profissional desconhecido: {tipo_str}")

            if not tipos_enum:
                logger.error(f"❌ Nenhum tipo profissional válido para {requisito.nome_atividade}")
                sucesso_total = False
                # Adicionar falha à lista de falhadas
                alocacoes_falhadas.append({
                    'requisito': requisito,
                    'funcionarios': [],
                    'inicio': inicio,
                    'fim': fim,
                    'tipos_necessarios': []
                })
                continue

            # Usar método de priorização existente
            sucesso, funcionarios_selecionados = self.priorizar_funcionarios(
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                inicio=inicio,
                fim=fim,
                qtd_profissionais_requeridos=requisito.funcionarios_necessarios,
                tipos_necessarios=tipos_enum,
                fips_profissionais_permitidos=requisito.fips,
                funcionarios_elegiveis=self.funcionarios_disponiveis,
                nome_atividade=requisito.nome_atividade
            )

            if sucesso and len(funcionarios_selecionados) == requisito.funcionarios_necessarios:
                # Registrar ocupações nos funcionários
                for funcionario in funcionarios_selecionados:
                    funcionario.registrar_ocupacao(
                        id_ordem=id_ordem,
                        id_pedido=id_pedido,
                        id_atividade_json=requisito.id_atividade,
                        nome_atividade=requisito.nome_atividade,
                        inicio=inicio,
                        fim=fim
                    )

                # Salvar alocação para log posterior
                alocacoes_realizadas.append({
                    'requisito': requisito,
                    'funcionarios': funcionarios_selecionados,
                    'inicio': inicio,
                    'fim': fim,
                    'tipos_necessarios': tipos_enum
                })

                logger.info(f"✅ Alocados {len(funcionarios_selecionados)} funcionários para {requisito.nome_atividade}")

            else:
                logger.error(f"❌ Falha na alocação para {requisito.nome_atividade}: {len(funcionarios_selecionados)}/{requisito.funcionarios_necessarios}")

                # Gerar análise detalhada do conflito
                relatorio_conflito = self.analisar_conflito_alocacao(
                    requisito.id_atividade,
                    requisito.nome_atividade,
                    tipos_enum,
                    requisito.funcionarios_necessarios,
                    inicio,
                    fim
                )
                logger.info(f"\n{relatorio_conflito}")

                sucesso_total = False
                # Adicionar falha à lista de falhadas
                alocacoes_falhadas.append({
                    'requisito': requisito,
                    'funcionarios': [],
                    'inicio': inicio,
                    'fim': fim,
                    'tipos_necessarios': tipos_enum
                })

                # 🔥 ROLLBACK: Liberar TODAS as alocações feitas anteriormente
                logger.warning(f"🔄 ROLLBACK: Liberando {len(alocacoes_realizadas)} alocação(ões) anterior(es) devido à falha")
                for alocacao in alocacoes_realizadas:
                    for funcionario in alocacao['funcionarios']:
                        # Liberar ocupação específica desta atividade
                        requisito_anterior = alocacao['requisito']
                        funcionario.liberar_por_atividade(id_ordem, id_pedido, requisito_anterior.id_atividade)
                        logger.debug(f"   ↩️ Liberado: {funcionario.nome} da atividade {requisito_anterior.nome_atividade}")

                logger.error(f"❌ FALHA CRÍTICA: Pedido {id_ordem}|{id_pedido} NÃO será alocado (rollback completo)")
                break  # Interrompe o loop - não processa mais atividades

        # ⚠️ DECISÃO CRÍTICA: Só salvar logs e marcar como alocado se TUDO foi bem-sucedido
        if sucesso_total:
            # Salvar logs das alocações (apenas sucessos)
            if alocacoes_realizadas:
                self._salvar_logs_alocacoes(id_ordem, id_pedido, alocacoes_realizadas)

            # Marcar pedido como alocado
            self.pedidos_alocados.add(pedido_key)
            logger.info(f"✅ Pedido {id_ordem}|{id_pedido} marcado como alocado com sucesso")
        else:
            # Salvar log de erro apenas
            if alocacoes_falhadas:
                self._salvar_logs_alocacoes(id_ordem, id_pedido, alocacoes_falhadas)

            logger.warning(f"⚠️ Pedido {id_ordem}|{id_pedido} NÃO foi marcado como alocado (falha na alocação)")

        logger.info(f"🏁 Alocação finalizada para Ordem {id_ordem} | Pedido {id_pedido}. Sucesso: {sucesso_total}")
        return sucesso_total

    def _salvar_logs_alocacoes(self, id_ordem: int, id_pedido: int, alocacoes: List[Dict]):
        """
        Salva logs das alocações no formato padrão do sistema.

        Args:
            id_ordem: ID da ordem
            id_pedido: ID do pedido
            alocacoes: Lista de alocações realizadas
        """
        try:
            for alocacao in alocacoes:
                requisito = alocacao['requisito']
                funcionarios = alocacao['funcionarios']
                inicio = alocacao['inicio']
                fim = alocacao['fim']

                # Usar função existente do gerenciador_logs
                tipos_necessarios = alocacao.get('tipos_necessarios', None)
                registrar_log_funcionarios(
                    id_ordem=id_ordem,
                    id_pedido=id_pedido,
                    id_atividade=requisito.id_atividade,
                    funcionarios_alocados=funcionarios,
                    nome_item="",  # Não temos essa informação no requisito
                    nome_atividade=requisito.nome_atividade,
                    inicio=inicio,
                    fim=fim,
                    tipos_necessarios=tipos_necessarios
                )

            logger.info(f"📄 Logs salvos para {len(alocacoes)} alocações em logs/funcionarios/")

        except Exception as e:
            logger.error(f"❌ Erro ao salvar logs das alocações: {e}")

    def _limpar_ocupacoes_funcionarios(self):
        """
        Limpa todas as ocupações dos funcionários para reiniciar alocação.
        """
        for funcionario in self.funcionarios_disponiveis:
            funcionario.ocupacoes.clear()
        logger.info(f"🧹 Ocupações limpas de {len(self.funcionarios_disponiveis)} funcionários")

    def limpar_alocacao_pedido(self, id_ordem: int, id_pedido: int):
        """
        Remove o pedido do histórico de alocações, permitindo que seja alocado novamente.
        Também libera as ocupações dos funcionários para este pedido.

        Args:
            id_ordem: ID da ordem
            id_pedido: ID do pedido
        """
        pedido_key = (id_ordem, id_pedido)

        # Remove do set de pedidos alocados
        if pedido_key in self.pedidos_alocados:
            self.pedidos_alocados.remove(pedido_key)
            logger.info(f"🧹 Pedido {id_ordem}|{id_pedido} removido do histórico de alocações")

        # Libera ocupações dos funcionários
        for funcionario in self.funcionarios_disponiveis:
            funcionario.liberar_por_pedido(id_ordem, id_pedido)

        logger.info(f"✅ Alocação do pedido {id_ordem}|{id_pedido} limpa - pronto para realocar")

    def limpar_todas_alocacoes(self):
        """
        Limpa todas as alocações e ocupações.
        Útil para resetar completamente o sistema de funcionários.
        """
        # Limpar histórico de pedidos alocados
        qtd_pedidos = len(self.pedidos_alocados)
        self.pedidos_alocados.clear()

        # Limpar ocupações de todos os funcionários
        self._limpar_ocupacoes_funcionarios()

        logger.info(f"🧹 Sistema resetado: {qtd_pedidos} pedido(s) e todas as ocupações foram limpos")

    def listar_pedidos_alocados(self) -> List[tuple]:
        """
        Retorna lista de pedidos que já tiveram funcionários alocados.

        Returns:
            List[tuple]: Lista de tuplas (id_ordem, id_pedido)
        """
        return sorted(list(self.pedidos_alocados))

    def pedido_ja_alocado(self, id_ordem: int, id_pedido: int) -> bool:
        """
        Verifica se um pedido já teve funcionários alocados.

        Args:
            id_ordem: ID da ordem
            id_pedido: ID do pedido

        Returns:
            bool: True se já foi alocado, False caso contrário
        """
        return (id_ordem, id_pedido) in self.pedidos_alocados

    def analisar_conflito_alocacao(
        self,
        id_atividade: int,
        nome_atividade: str,
        tipos_necessarios: List[TipoProfissional],
        quantidade_necessaria: int,
        inicio: datetime,
        fim: datetime
    ) -> str:
        """
        Analisa e explica por que uma alocação falhou.

        Args:
            id_atividade: ID da atividade
            nome_atividade: Nome da atividade
            tipos_necessarios: Tipos profissionais necessários
            quantidade_necessaria: Quantidade de funcionários necessários
            inicio: Horário de início
            fim: Horário de fim

        Returns:
            str: Relatório detalhado do conflito
        """
        analisador = AnalisadorConflitos(self.funcionarios_disponiveis)
        analise = analisador.analisar_falha_alocacao(
            id_atividade, nome_atividade, tipos_necessarios,
            quantidade_necessaria, inicio, fim
        )
        return analisador.gerar_relatorio_conflito(analise)

    def obter_relatorio_alocacoes(self, id_ordem: int = None, id_pedido: int = None) -> str:
        """
        Gera relatório das alocações atuais dos funcionários.

        Args:
            id_ordem: Filtrar por ordem específica (opcional)
            id_pedido: Filtrar por pedido específico (opcional)

        Returns:
            str: Relatório formatado
        """
        relatorio = []
        relatorio.append("=" * 80)
        relatorio.append("📊 RELATÓRIO DE ALOCAÇÕES DE FUNCIONÁRIOS")
        relatorio.append("=" * 80)

        if id_ordem or id_pedido:
            filtro = f"Ordem {id_ordem}" if id_ordem else ""
            filtro += f" | Pedido {id_pedido}" if id_pedido else ""
            relatorio.append(f"🔍 Filtro: {filtro}")
            relatorio.append("")

        funcionarios_com_alocacao = 0
        total_atividades = 0

        for funcionario in self.funcionarios_disponiveis:
            # Filtrar ocupações se necessário
            ocupacoes_filtradas = funcionario.ocupacoes
            if id_ordem or id_pedido:
                ocupacoes_filtradas = [
                    ocup for ocup in funcionario.ocupacoes
                    if (not id_ordem or ocup[0] == id_ordem) and (not id_pedido or ocup[1] == id_pedido)
                ]

            if ocupacoes_filtradas:
                funcionarios_com_alocacao += 1
                total_atividades += len(ocupacoes_filtradas)

                tipos_str = ", ".join([t.name for t in funcionario.tipo_profissional])
                relatorio.append(f"👤 {funcionario.nome} ({tipos_str}):")
                relatorio.append(f"   📋 {len(ocupacoes_filtradas)} atividades alocadas")

                for ocup in ocupacoes_filtradas:
                    id_ordem_ocup, id_pedido_ocup, id_atividade, nome_atividade, inicio, fim = ocup
                    relatorio.append(
                        f"   • {nome_atividade} | O:{id_ordem_ocup} P:{id_pedido_ocup} | "
                        f"{inicio.strftime('%H:%M')}-{fim.strftime('%H:%M')}"
                    )
                relatorio.append("")

        # Resumo
        relatorio.append("📋 RESUMO:")
        relatorio.append(f"👥 Funcionários com alocação: {funcionarios_com_alocacao}/{len(self.funcionarios_disponiveis)}")
        relatorio.append(f"📝 Total de atividades alocadas: {total_atividades}")
        relatorio.append("=" * 80)

        return "\n".join(relatorio)

    def processar_todas_ordens_pedidos_disponiveis(self) -> Dict[Tuple[int, int], bool]:
        """
        Processa automaticamente todas as ordens|pedidos encontradas em tipos_funcionarios_requeridos.

        Returns:
            Dict[Tuple[int, int], bool]: Resultados das alocações por (ordem, pedido)
        """
        diretorio_requisitos = "logs/tipos_funcionarios_requeridos"

        if not os.path.exists(diretorio_requisitos):
            logger.warning(f"📁 Diretório não encontrado: {diretorio_requisitos}")
            return {}

        resultados = {}
        arquivos = os.listdir(diretorio_requisitos)

        # Filtrar arquivos que seguem o padrão "ordem: X | pedido: Y.log"
        padrao_arquivo = re.compile(r'ordem: (\d+) \| pedido: (\d+)\.log')

        for arquivo in arquivos:
            match = padrao_arquivo.match(arquivo)
            if match:
                id_ordem = int(match.group(1))
                id_pedido = int(match.group(2))

                logger.info(f"🔄 Processando arquivo: {arquivo}")
                sucesso = self.alocar_funcionarios_para_ordem_pedido(id_ordem, id_pedido)
                resultados[(id_ordem, id_pedido)] = sucesso

        # Resumo final
        sucessos = sum(resultados.values())
        total = len(resultados)
        logger.info(f"🏁 Processamento finalizado: {sucessos}/{total} ordens|pedidos processadas com sucesso")

        return resultados

    @staticmethod
    def priorizar_funcionarios(
        id_ordem: int,
        id_pedido: int,
        inicio: datetime,
        fim: datetime,
        qtd_profissionais_requeridos: int,
        tipos_necessarios: List[Enum],
        fips_profissionais_permitidos: dict,
        funcionarios_elegiveis: List[Funcionario],
        nome_atividade: str,
    ) -> Tuple[bool, List[Funcionario]]:
        """
        Seleciona até N profissionais com base em:
        - tipos permitidos
        - fips definidos no JSON (quanto maior, melhor)
        - engajamento no pedido (quem já está, tem prioridade)
        - disponibilidade no intervalo da atividade
        """

        if qtd_profissionais_requeridos == 0:
            # logger.info(f"ℹ️ Atividade {nome_atividade} não requer funcionários.")
            return True, []

        # logger.warning(f"🧪 [{nome_atividade}] Tipos profissionais necessários: {tipos_necessarios}")
        # logger.warning(f"🧪 [{nome_atividade}] Funcionários elegíveis na pedido:")
        # for f in funcionarios_elegiveis:
        #     logger.warning(f"   └ {f.nome} ({f.tipo_profissional.name})")

        # Filtrar funcionários que possuem pelo menos um tipo compatível
        candidatos = [
            f for f in funcionarios_elegiveis
            if any(tipo in tipos_necessarios for tipo in f.tipo_profissional)
        ]

        if not candidatos:
            logger.warning(f"⚠️ Nenhum funcionário compatível para {nome_atividade}")
            logger.debug(f"   💼 Tipos necessários: {[t.name for t in tipos_necessarios]}")
            logger.debug(f"   👥 Funcionários disponíveis:")
            for f in funcionarios_elegiveis:
                tipos_funcionario = [t.name for t in f.tipo_profissional]
                logger.debug(f"      • {f.nome}: {tipos_funcionario}")
            return False, []

        logger.debug(f"   ✅ {len(candidatos)} funcionários compatíveis encontrados")

        def chave_pedido(f: Funcionario):
            # Obter maior FIP entre todos os tipos que o funcionário possui
            fips_funcionario = [
                fips_profissionais_permitidos.get(tipo.name, 0)
                for tipo in f.tipo_profissional
                if tipo.name in fips_profissionais_permitidos
            ]
            fip_json = max(fips_funcionario) if fips_funcionario else 0

            engajado = f.ja_esta_no_pedido(id_pedido=id_pedido, id_ordem=id_ordem)
            return (-int(engajado), -fip_json, -f.fip)

        candidatos_ordenados = sorted(candidatos, key=chave_pedido)

        selecionados = []
        for f in candidatos_ordenados:
            # ✅ CORREÇÃO: Usar validação completa (folga + turno + intervalo + conflitos)
            disponivel, motivo = f.validar_disponibilidade_completa(inicio, fim)
            if disponivel:
                selecionados.append(f)
            else:
                logger.debug(
                    f"⚠️ {f.nome} não pôde ser selecionado para {nome_atividade}. Motivo: {motivo}"
                )

            if len(selecionados) == qtd_profissionais_requeridos:
                return True, selecionados            

        # logger.warning(
        #     f"⚠️ Apenas {len(selecionados)}/{qtd_profissionais_requeridos} profissionais disponíveis para {nome_atividade}"
        # )
        return False, selecionados

    def mostrar_agenda_todos_funcionarios(self) -> str:
        """
        Mostra a agenda de todos os funcionários organizada por funcionário.

        Returns:
            str: Agenda formatada de todos os funcionários
        """
        agenda = []
        agenda.append("=" * 80)
        agenda.append("📅 AGENDA COMPLETA DE FUNCIONÁRIOS (ORGANIZADA POR FUNCIONÁRIO)")
        agenda.append("=" * 80)
        agenda.append("")

        total_ocupacoes = 0
        funcionarios_ocupados = 0

        # Organizar por funcionário
        for funcionario in self.funcionarios_disponiveis:
            if not funcionario.ocupacoes:
                continue

            funcionarios_ocupados += 1
            tipos_str = ", ".join([t.name for t in funcionario.tipo_profissional])

            agenda.append(f"👤 {funcionario.nome} ({tipos_str}) - FIP: {funcionario.fip}")
            agenda.append("-" * 60)

            # Ordenar ocupações do funcionário por horário de início
            ocupacoes_ordenadas = sorted(funcionario.ocupacoes, key=lambda x: x[4])  # x[4] é o início

            # Agrupar ocupações por dia
            ocupacoes_por_dia = {}
            total_segundos_funcionario = 0

            for ocupacao in ocupacoes_ordenadas:
                id_ordem, id_pedido, id_atividade, nome_atividade, inicio, fim = ocupacao
                data_str = inicio.strftime('%d/%m/%Y')

                if data_str not in ocupacoes_por_dia:
                    ocupacoes_por_dia[data_str] = []

                ocupacoes_por_dia[data_str].append(ocupacao)

                # Acumular tempo total
                duracao = fim - inicio
                total_segundos_funcionario += duracao.total_seconds()
                total_ocupacoes += 1

            # Exibir ocupações agrupadas por dia
            for data in sorted(ocupacoes_por_dia.keys(), key=lambda x: tuple(map(int, x.split('/')[::-1]))):
                agenda.append(f"   📅 {data}")
                agenda.append("   " + "-" * 40)

                total_segundos_dia = 0

                for ocupacao in ocupacoes_por_dia[data]:
                    id_ordem, id_pedido, id_atividade, nome_atividade, inicio, fim = ocupacao

                    # Formatear informações da ocupação
                    horario = f"{inicio.strftime('%H:%M')} - {fim.strftime('%H:%M')}"
                    duracao = fim - inicio
                    duracao_segundos = duracao.total_seconds()
                    total_segundos_dia += duracao_segundos

                    # Converter duração para hh:mm:ss
                    horas = int(duracao_segundos // 3600)
                    minutos = int((duracao_segundos % 3600) // 60)
                    segundos = int(duracao_segundos % 60)
                    duracao_str = f"{horas:02d}:{minutos:02d}:{segundos:02d}"

                    objeto = f"Ordem {id_ordem} | Pedido {id_pedido}"

                    agenda.append(f"      ⏰ {horario} ({duracao_str})")
                    agenda.append(f"      🎯 {objeto}")
                    agenda.append(f"      📋 {nome_atividade} (ID: {id_atividade})")
                    agenda.append("")

                # Total do dia em hh:mm:ss
                horas_dia = int(total_segundos_dia // 3600)
                minutos_dia = int((total_segundos_dia % 3600) // 60)
                segundos_dia = int(total_segundos_dia % 60)
                total_dia_str = f"{horas_dia:02d}:{minutos_dia:02d}:{segundos_dia:02d}"

                agenda.append(f"   ⏱️ Total do dia: {total_dia_str}")
                agenda.append("")

            # Resumo geral do funcionário
            horas_total = int(total_segundos_funcionario // 3600)
            minutos_total = int((total_segundos_funcionario % 3600) // 60)
            segundos_total = int(total_segundos_funcionario % 60)
            total_funcionario_str = f"{horas_total:02d}:{minutos_total:02d}:{segundos_total:02d}"

            datas_trabalhadas = list(ocupacoes_por_dia.keys())
            agenda.append(f"   📊 RESUMO GERAL:")
            agenda.append(f"   📅 Datas trabalhadas: {', '.join(sorted(datas_trabalhadas, key=lambda x: tuple(map(int, x.split('/')[::-1]))))}")
            agenda.append(f"   ⏱️ Total geral: {total_funcionario_str}")
            agenda.append("")

        # Mostrar funcionários sem ocupações
        funcionarios_livres = [f for f in self.funcionarios_disponiveis if not f.ocupacoes]
        if funcionarios_livres:
            agenda.append("🆓 FUNCIONÁRIOS SEM OCUPAÇÕES:")
            agenda.append("-" * 40)
            for funcionario in funcionarios_livres:
                tipos_str = ", ".join([t.name for t in funcionario.tipo_profissional])
                agenda.append(f"   👤 {funcionario.nome} ({tipos_str}) - FIP: {funcionario.fip}")
            agenda.append("")

        # Estatísticas finais
        agenda.append("📊 ESTATÍSTICAS GERAIS:")
        agenda.append(f"👥 Total de funcionários: {len(self.funcionarios_disponiveis)}")
        agenda.append(f"🏃 Funcionários com ocupações: {funcionarios_ocupados}")
        agenda.append(f"🆓 Funcionários livres: {len(funcionarios_livres)}")
        agenda.append(f"📝 Total de ocupações: {total_ocupacoes}")
        agenda.append("=" * 80)

        return "\n".join(agenda)

    def carregar_alocacoes_dos_logs(self) -> bool:
        """
        Carrega as alocações de funcionários dos arquivos .log em logs/funcionarios/
        e popula as ocupações dos funcionários.

        Returns:
            bool: True se carregou com sucesso
        """
        diretorio_logs = "logs/funcionarios"

        if not os.path.exists(diretorio_logs):
            logger.warning(f"📁 Diretório não encontrado: {diretorio_logs}")
            return False

        # Limpar ocupações existentes
        self._limpar_ocupacoes_funcionarios()

        total_alocacoes = 0
        arquivos_processados = 0

        try:
            for arquivo in os.listdir(diretorio_logs):
                if not arquivo.endswith('.log'):
                    continue

                caminho_arquivo = os.path.join(diretorio_logs, arquivo)
                logger.debug(f"📄 Processando arquivo: {arquivo}")

                with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                    for linha in f:
                        linha = linha.strip()
                        if not linha or not linha[0].isdigit():
                            continue

                        partes = linha.split(' | ')
                        if len(partes) < 7:
                            continue

                        try:
                            id_ordem = int(partes[0])
                            id_pedido = int(partes[1])
                            id_atividade = int(partes[2])
                            nome_item = partes[3].strip()
                            nome_atividade = partes[4].strip()
                            funcionario_info = partes[5].strip()
                            horario_inicio_str = partes[6].strip()
                            horario_fim_str = partes[7].strip()

                            # Verificar se a alocação foi bem-sucedida (tem ✅)
                            if '✅' not in funcionario_info:
                                continue

                            # Extrair nome do funcionário
                            nome_funcionario = funcionario_info.replace(' ✅', '').strip()

                            # Encontrar o funcionário
                            funcionario = None
                            for f in self.funcionarios_disponiveis:
                                if f.nome == nome_funcionario:
                                    funcionario = f
                                    break

                            if not funcionario:
                                logger.warning(f"⚠️ Funcionário não encontrado: {nome_funcionario}")
                                continue

                            # Parsear horários - formato: HH:MM [DD/MM/YYYY]
                            inicio_match = re.match(r'(\d{2}:\d{2}) \[(\d{2}/\d{2}/\d{4})\]', horario_inicio_str)
                            fim_match = re.match(r'(\d{2}:\d{2}) \[(\d{2}/\d{2}/\d{4})\]', horario_fim_str)

                            if not inicio_match or not fim_match:
                                logger.warning(f"⚠️ Formato de horário inválido: {horario_inicio_str} - {horario_fim_str}")
                                continue

                            hora_inicio = inicio_match.group(1)
                            data_inicio = inicio_match.group(2)
                            hora_fim = fim_match.group(1)
                            data_fim = fim_match.group(2)

                            # Converter para datetime
                            inicio = datetime.strptime(f"{data_inicio} {hora_inicio}", "%d/%m/%Y %H:%M")
                            fim = datetime.strptime(f"{data_fim} {hora_fim}", "%d/%m/%Y %H:%M")

                            # Registrar ocupação no funcionário
                            funcionario.registrar_ocupacao(
                                id_ordem=id_ordem,
                                id_pedido=id_pedido,
                                id_atividade_json=id_atividade,
                                nome_atividade=nome_atividade,
                                inicio=inicio,
                                fim=fim
                            )

                            total_alocacoes += 1

                        except (ValueError, IndexError) as e:
                            logger.warning(f"⚠️ Erro ao processar linha: {linha[:50]}... Erro: {e}")
                            continue

                arquivos_processados += 1

            logger.info(f"📋 Carregadas {total_alocacoes} alocações de {arquivos_processados} arquivos")
            return True

        except Exception as e:
            logger.error(f"❌ Erro ao carregar alocações dos logs: {e}")
            return False

    def extrair_conflitos_dos_logs(self) -> List[Dict]:
        """
        Extrai automaticamente os conflitos (alocações falhadas) dos arquivos .log.

        Returns:
            List[Dict]: Lista de conflitos encontrados nos logs
        """
        diretorio_logs = "logs/funcionarios"
        conflitos = []

        if not os.path.exists(diretorio_logs):
            logger.warning(f"📁 Diretório não encontrado: {diretorio_logs}")
            return conflitos

        try:
            for arquivo in os.listdir(diretorio_logs):
                if not arquivo.endswith('.log'):
                    continue

                # Extrair ordem e pedido do nome do arquivo
                match_arquivo = re.match(r'ordem: (\d+) \| pedido: (\d+)\.log', arquivo)
                if not match_arquivo:
                    continue

                id_ordem = int(match_arquivo.group(1))
                id_pedido = int(match_arquivo.group(2))

                caminho_arquivo = os.path.join(diretorio_logs, arquivo)

                with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                    for linha in f:
                        linha = linha.strip()
                        if not linha or not linha[0].isdigit():
                            continue

                        # Procurar linhas com "❌" (alocações falhadas)
                        if '❌' not in linha:
                            continue

                        partes = linha.split(' | ')
                        if len(partes) < 7:
                            continue

                        try:
                            id_atividade = int(partes[2])
                            nome_atividade = partes[4].strip()
                            funcionario_info = partes[5].strip()
                            horario_inicio_str = partes[6].strip()
                            horario_fim_str = partes[7].strip()

                            # Extrair tipos necessários da mensagem de erro
                            tipos_necessarios = []
                            match_tipos = re.search(r'Tipos necessários: ([^)]+)\)', funcionario_info)
                            if match_tipos:
                                tipos_str = match_tipos.group(1)
                                for tipo_str in tipos_str.split(','):
                                    tipo_str = tipo_str.strip()
                                    try:
                                        tipo_enum = TipoProfissional[tipo_str]
                                        tipos_necessarios.append(tipo_enum)
                                    except KeyError:
                                        logger.warning(f"⚠️ Tipo profissional desconhecido: {tipo_str}")

                            if not tipos_necessarios:
                                continue

                            # Parsear horários - formato: HH:MM [DD/MM/YYYY]
                            inicio_match = re.match(r'(\d{2}:\d{2}) \[(\d{2}/\d{2}/\d{4})\]', horario_inicio_str)
                            fim_match = re.match(r'(\d{2}:\d{2}) \[(\d{2}/\d{2}/\d{4})\]', horario_fim_str)

                            if not inicio_match or not fim_match:
                                continue

                            hora_inicio = inicio_match.group(1)
                            data_inicio = inicio_match.group(2)
                            hora_fim = fim_match.group(1)
                            data_fim = fim_match.group(2)

                            # Converter para datetime
                            inicio = datetime.strptime(f"{data_inicio} {hora_inicio}", "%d/%m/%Y %H:%M")
                            fim = datetime.strptime(f"{data_fim} {hora_fim}", "%d/%m/%Y %H:%M")

                            # Assumir quantidade 1 se não especificado
                            quantidade = 1

                            conflito = {
                                'id_ordem': id_ordem,
                                'id_pedido': id_pedido,
                                'id_atividade': id_atividade,
                                'nome_atividade': nome_atividade,
                                'inicio': inicio,
                                'fim': fim,
                                'tipos_necessarios': tipos_necessarios,
                                'quantidade': quantidade,
                                'arquivo_origem': arquivo
                            }

                            conflitos.append(conflito)

                        except (ValueError, IndexError) as e:
                            logger.warning(f"⚠️ Erro ao processar linha de conflito: {linha[:50]}... Erro: {e}")
                            continue

            logger.info(f"🔍 Extraídos {len(conflitos)} conflitos dos logs")
            return conflitos

        except Exception as e:
            logger.error(f"❌ Erro ao extrair conflitos dos logs: {e}")
            return conflitos
