import json
import os
from datetime import datetime
from typing import List, Dict, Set
from enums.funcionarios.tipo_profissional import TipoProfissional
from utils.logs.logger_factory import setup_logger
from utils.logs.registrador_funcionarios import registrador_funcionarios

logger = setup_logger('GestorTipoFuncionarios')


class RequisitoFuncionario:
    """
    Representa um requisito de funcionário para uma atividade específica.
    """
    def __init__(self, id_atividade: int, nome_atividade: str, tipo_profissional: TipoProfissional,
                 inicio: datetime, fim: datetime, quantidade: int, fips: dict = None):
        self.id_atividade = id_atividade
        self.nome_atividade = nome_atividade
        self.tipo_profissional = tipo_profissional
        self.inicio = inicio
        self.fim = fim
        self.quantidade = quantidade
        self.fips = fips or {}

    def __repr__(self):
        return (f"RequisitoFuncionario(id={self.id_atividade}, tipo={self.tipo_profissional.name}, "
                f"inicio={self.inicio.strftime('%H:%M')}, fim={self.fim.strftime('%H:%M')}, qty={self.quantidade})")


class GestorTipoFuncionarios:
    """
    Gestor responsável por coletar e organizar os requisitos de funcionários das atividades.
    Armazena informações sobre quais tipos de profissionais são necessários,
    em que horários e para quais atividades.
    """

    def __init__(self, id_ordem: int = None, id_pedido: int = None):
        """
        Inicializa o gestor de tipos de funcionários.

        Args:
            id_ordem: ID da ordem (opcional para contexto)
            id_pedido: ID do pedido (opcional para contexto)
        """
        self.id_ordem = id_ordem
        self.id_pedido = id_pedido
        self.requisitos: List[RequisitoFuncionario] = []

        logger.info(f"🏭 GestorTipoFuncionarios inicializado (Ordem: {id_ordem}, Pedido: {id_pedido})")

    def registrar_requisito(self, id_atividade: int, nome_atividade: str,
                          tipos_profissionais: Set[TipoProfissional],
                          inicio: datetime, fim: datetime, quantidade: int,
                          fips: dict = None) -> None:
        """
        Registra um requisito de funcionário para uma atividade.

        Args:
            id_atividade: ID da atividade
            nome_atividade: Nome da atividade
            tipos_profissionais: Conjunto de tipos de profissionais permitidos
            inicio: Horário de início da atividade
            fim: Horário de fim da atividade
            quantidade: Quantidade total de funcionários necessários
            fips: Dicionário com fatores de prioridade por tipo
        """
        try:
            # Se não há tipos profissionais ou quantidade é 0, não registrar
            if not tipos_profissionais or quantidade == 0:
                logger.debug(f"⚠️ Atividade {id_atividade} não requer funcionários - ignorando registro")
                return

            # Registrar um requisito para cada tipo de profissional permitido
            for tipo_profissional in tipos_profissionais:
                requisito = RequisitoFuncionario(
                    id_atividade=id_atividade,
                    nome_atividade=nome_atividade,
                    tipo_profissional=tipo_profissional,
                    inicio=inicio,
                    fim=fim,
                    quantidade=quantidade,
                    fips=fips
                )

                self.requisitos.append(requisito)

                logger.debug(
                    f"📋 Requisito registrado: Atividade {id_atividade} ({nome_atividade}) "
                    f"requer {quantidade}x {tipo_profissional.name} "
                    f"de {inicio.strftime('%H:%M')} às {fim.strftime('%H:%M')}"
                )

            logger.info(
                f"✅ Atividade {id_atividade} registrada: "
                f"{len(tipos_profissionais)} tipos profissionais, "
                f"{quantidade} funcionários necessários"
            )

        except Exception as e:
            logger.error(f"❌ Erro ao registrar requisito para atividade {id_atividade}: {e}")

    def obter_requisitos_por_tipo(self, tipo_profissional: TipoProfissional = None) -> Dict[TipoProfissional, List[RequisitoFuncionario]]:
        """
        Retorna requisitos organizados por tipo profissional.

        Args:
            tipo_profissional: Tipo específico para filtrar (opcional)

        Returns:
            Dicionário com requisitos agrupados por tipo
        """
        requisitos_por_tipo = {}

        for requisito in self.requisitos:
            if tipo_profissional and requisito.tipo_profissional != tipo_profissional:
                continue

            if requisito.tipo_profissional not in requisitos_por_tipo:
                requisitos_por_tipo[requisito.tipo_profissional] = []

            requisitos_por_tipo[requisito.tipo_profissional].append(requisito)

        return requisitos_por_tipo

    def obter_requisitos_por_horario(self) -> List[RequisitoFuncionario]:
        """
        Retorna requisitos ordenados por horário de início.

        Returns:
            Lista de requisitos ordenados por tempo
        """
        return sorted(self.requisitos, key=lambda r: r.inicio)

    def obter_tipos_necessarios(self) -> Set[TipoProfissional]:
        """
        Retorna conjunto único de tipos profissionais necessários.

        Returns:
            Set com todos os tipos profissionais requeridos
        """
        return {requisito.tipo_profissional for requisito in self.requisitos}

    def obter_estatisticas(self) -> dict:
        """
        Retorna estatísticas dos requisitos coletados.

        Returns:
            Dicionário com estatísticas
        """
        if not self.requisitos:
            return {
                'total_requisitos': 0,
                'tipos_unicos': 0,
                'atividades_unicas': 0,
                'periodo_cobertura': None
            }

        tipos_unicos = self.obter_tipos_necessarios()
        atividades_unicas = {req.id_atividade for req in self.requisitos}

        inicios = [req.inicio for req in self.requisitos]
        fins = [req.fim for req in self.requisitos]

        periodo_inicio = min(inicios) if inicios else None
        periodo_fim = max(fins) if fins else None

        # Calcular duração em minutos (serializável para JSON)
        duracao_minutos = None
        if periodo_inicio and periodo_fim:
            duracao_total = periodo_fim - periodo_inicio
            duracao_minutos = int(duracao_total.total_seconds() / 60)

        return {
            'total_requisitos': len(self.requisitos),
            'tipos_unicos': len(tipos_unicos),
            'atividades_unicas': len(atividades_unicas),
            'periodo_cobertura': {
                'inicio': periodo_inicio.strftime('%d/%m %H:%M') if periodo_inicio else None,
                'fim': periodo_fim.strftime('%d/%m %H:%M') if periodo_fim else None,
                'duracao_minutos': duracao_minutos
            },
            'tipos_necessarios': [tipo.name for tipo in tipos_unicos]
        }

    def gerar_relatorio_resumido(self) -> str:
        """
        Gera um relatório resumido em formato texto.

        Returns:
            String com relatório formatado
        """
        stats = self.obter_estatisticas()
        requisitos_por_tipo = self.obter_requisitos_por_tipo()

        relatorio = []
        relatorio.append("=" * 60)
        relatorio.append("📋 RELATÓRIO DE REQUISITOS DE FUNCIONÁRIOS")
        relatorio.append("=" * 60)

        if self.id_ordem or self.id_pedido:
            relatorio.append(f"🆔 Contexto: Ordem {self.id_ordem}, Pedido {self.id_pedido}")
            relatorio.append("")

        relatorio.append(f"📊 ESTATÍSTICAS GERAIS:")
        relatorio.append(f"   Total de requisitos: {stats['total_requisitos']}")
        relatorio.append(f"   Tipos profissionais únicos: {stats['tipos_unicos']}")
        relatorio.append(f"   Atividades únicas: {stats['atividades_unicas']}")

        if stats['periodo_cobertura']['inicio']:
            relatorio.append(f"   Período de cobertura: {stats['periodo_cobertura']['inicio']} → {stats['periodo_cobertura']['fim']}")

        relatorio.append("")
        relatorio.append("👥 REQUISITOS POR TIPO PROFISSIONAL:")

        for tipo, requisitos in requisitos_por_tipo.items():
            relatorio.append(f"\n🔸 {tipo.name}:")
            relatorio.append(f"   Total de requisitos: {len(requisitos)}")

            # Mostrar os primeiros 3 requisitos como exemplo
            for i, req in enumerate(requisitos[:3]):
                relatorio.append(
                    f"   {i+1}. Atividade {req.id_atividade} ({req.nome_atividade}): "
                    f"{req.inicio.strftime('%H:%M')}-{req.fim.strftime('%H:%M')} "
                    f"({req.quantidade} funcionários)"
                )

            if len(requisitos) > 3:
                relatorio.append(f"   ... e mais {len(requisitos) - 3} requisitos")

        relatorio.append("\n" + "=" * 60)
        relatorio.append("📄 Fim do relatório")
        relatorio.append("=" * 60)

        return "\n".join(relatorio)

    def salvar_requisitos_em_log(self, nome_arquivo: str = None) -> str:
        """
        Salva os requisitos em formato .log usando o registrador de funcionários.

        Args:
            nome_arquivo: Nome personalizado do arquivo (opcional)

        Returns:
            Caminho do arquivo salvo
        """
        try:
            # Registrar cada requisito usando o registrador_funcionarios
            for requisito in self.requisitos:
                registrador_funcionarios.registrar_requisito_funcionario(
                    id_ordem=self.id_ordem,
                    id_pedido=self.id_pedido,
                    id_atividade=requisito.id_atividade,
                    nome_atividade=requisito.nome_atividade,
                    tipos_profissionais={requisito.tipo_profissional},
                    inicio=requisito.inicio,
                    fim=requisito.fim,
                    quantidade=requisito.quantidade,
                    fips=requisito.fips
                )

            # Finalizar o log com a contagem total
            registrador_funcionarios.finalizar_log(
                id_ordem=self.id_ordem,
                id_pedido=self.id_pedido,
                total_requisitos=len(self.requisitos)
            )

            # Retornar o caminho do arquivo
            caminho_arquivo = registrador_funcionarios.obter_caminho_log(self.id_ordem, self.id_pedido)
            logger.info(f"📄 Log de funcionários salvo: {caminho_arquivo} ({len(self.requisitos)} requisitos)")
            return caminho_arquivo

        except Exception as e:
            logger.error(f"❌ Erro ao salvar requisitos em log: {e}")
            raise
    def salvar_requisitos_em_arquivo(self, nome_arquivo: str = None) -> str:
        """
        Salva os requisitos coletados em arquivo JSON.

        Args:
            nome_arquivo: Nome personalizado do arquivo (opcional)

        Returns:
            Caminho do arquivo salvo
        """
        try:
            # Criar pasta se não existir
            pasta_logs = "logs/tipos_funcionarios_requeridos"
            os.makedirs(pasta_logs, exist_ok=True)

            # Gerar nome do arquivo se não fornecido
            if not nome_arquivo:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                if self.id_ordem and self.id_pedido:
                    nome_arquivo = f"requisitos_ordem_{self.id_ordem}_pedido_{self.id_pedido}_{timestamp}.json"
                else:
                    nome_arquivo = f"requisitos_funcionarios_{timestamp}.json"

            caminho_arquivo = os.path.join(pasta_logs, nome_arquivo)

            # Preparar dados para salvar
            dados = {
                'metadados': {
                    'id_ordem': self.id_ordem,
                    'id_pedido': self.id_pedido,
                    'timestamp_geracao': datetime.now().isoformat(),
                    'total_requisitos': len(self.requisitos),
                    'tipos_unicos': len(self.obter_tipos_necessarios()),
                    'atividades_unicas': len({req.id_atividade for req in self.requisitos})
                },
                'estatisticas': self.obter_estatisticas(),
                'requisitos': [
                    {
                        'id_atividade': req.id_atividade,
                        'nome_atividade': req.nome_atividade,
                        'tipo_profissional': req.tipo_profissional.name,
                        'inicio': req.inicio.isoformat(),
                        'fim': req.fim.isoformat(),
                        'quantidade': req.quantidade,
                        'fips': req.fips
                    }
                    for req in self.requisitos
                ]
            }

            # Salvar arquivo
            with open(caminho_arquivo, 'w', encoding='utf-8') as f:
                json.dump(dados, f, indent=2, ensure_ascii=False)

            logger.info(
                f"💾 Requisitos salvos em arquivo: {caminho_arquivo} "
                f"({len(self.requisitos)} requisitos)"
            )

            return caminho_arquivo

        except Exception as e:
            logger.error(f"❌ Erro ao salvar requisitos em arquivo: {e}")
            raise

    def carregar_requisitos_de_arquivo(self, caminho_arquivo: str) -> bool:
        """
        Carrega requisitos de um arquivo JSON.

        Args:
            caminho_arquivo: Caminho para o arquivo JSON

        Returns:
            True se carregado com sucesso, False caso contrário
        """
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                dados = json.load(f)

            # Limpar requisitos atuais
            self.limpar_requisitos()

            # Carregar metadados
            metadados = dados.get('metadados', {})
            self.id_ordem = metadados.get('id_ordem')
            self.id_pedido = metadados.get('id_pedido')

            # Carregar requisitos
            requisitos_dados = dados.get('requisitos', [])
            for req_data in requisitos_dados:
                try:
                    tipo_profissional = TipoProfissional[req_data['tipo_profissional']]
                    inicio = datetime.fromisoformat(req_data['inicio'])
                    fim = datetime.fromisoformat(req_data['fim'])

                    requisito = RequisitoFuncionario(
                        id_atividade=req_data['id_atividade'],
                        nome_atividade=req_data['nome_atividade'],
                        tipo_profissional=tipo_profissional,
                        inicio=inicio,
                        fim=fim,
                        quantidade=req_data['quantidade'],
                        fips=req_data.get('fips', {})
                    )

                    self.requisitos.append(requisito)

                except Exception as e:
                    logger.warning(f"⚠️ Erro ao carregar requisito: {e}")

            logger.info(
                f"📂 Requisitos carregados de arquivo: {caminho_arquivo} "
                f"({len(self.requisitos)} requisitos)"
            )

            return True

        except Exception as e:
            logger.error(f"❌ Erro ao carregar requisitos de arquivo: {e}")
            return False

    def limpar_requisitos(self) -> None:
        """
        Limpa todos os requisitos registrados.
        """
        count = len(self.requisitos)
        self.requisitos.clear()
        logger.info(f"🧹 {count} requisitos limpos do gestor")

    def __len__(self) -> int:
        """Retorna número total de requisitos"""
        return len(self.requisitos)

    def __repr__(self):
        return (f"GestorTipoFuncionarios(ordem={self.id_ordem}, pedido={self.id_pedido}, "
                f"requisitos={len(self.requisitos)})")