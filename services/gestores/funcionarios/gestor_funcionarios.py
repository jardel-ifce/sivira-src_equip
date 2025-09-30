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
from factory.fabrica_funcionarios import (
    funcionario_1, funcionario_2, funcionario_3, funcionario_4, funcionario_5,
    funcionario_6, funcionario_7, funcionario_8, funcionario_9
)

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
    """

    def __init__(self):
        self.funcionarios_disponiveis = [
            funcionario_1, funcionario_2, funcionario_3, funcionario_4, funcionario_5,
            funcionario_6, funcionario_7, funcionario_8, funcionario_9
        ]
        logger.info(f"🏭 GestorFuncionarios inicializado com {len(self.funcionarios_disponiveis)} funcionários")

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

        Args:
            id_ordem: ID da ordem
            id_pedido: ID do pedido

        Returns:
            bool: True se todas as alocações foram bem-sucedidas
        """
        logger.info(f"🎯 Iniciando alocação para Ordem {id_ordem} | Pedido {id_pedido}")

        # Limpar ocupações anteriores dos funcionários (opcional - comentar se não quiser)
        # self._limpar_ocupacoes_funcionarios()

        # Carregar requisitos
        requisitos = self.ler_requisitos_de_arquivo(id_ordem, id_pedido)
        if not requisitos:
            logger.warning(f"⚠️ Nenhum requisito encontrado para Ordem {id_ordem} | Pedido {id_pedido}")
            return False

        # Ordenar por horário para alocar sequencialmente
        requisitos_ordenados = sorted(requisitos, key=lambda r: r.horario_inicio)

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

        # Salvar logs das alocações (sucessos e falhas)
        if alocacoes_realizadas or alocacoes_falhadas:
            self._salvar_logs_alocacoes(id_ordem, id_pedido, alocacoes_realizadas + alocacoes_falhadas)

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
            disponivel, motivo = f.verificar_disponibilidade_no_intervalo(inicio, fim)
            if disponivel:
                selecionados.append(f)
            # else:
            #     logger.warning(
            #         f"⚠️ {f.nome} não pôde ser selecionado para {nome_atividade}. Motivo: {motivo}"
            #     )

            if len(selecionados) == qtd_profissionais_requeridos:
                return True, selecionados            

        # logger.warning(
        #     f"⚠️ Apenas {len(selecionados)}/{qtd_profissionais_requeridos} profissionais disponíveis para {nome_atividade}"
        # )
        return False, selecionados
