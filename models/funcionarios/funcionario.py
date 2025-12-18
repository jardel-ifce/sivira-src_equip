from datetime import datetime, timedelta, date, time
from typing import List, Optional, Tuple
from utils.funcionarios.regras_folga import RegraFolga
from utils.time.data_utils import mapa_dia_semana, formatar_hora_e_min
from utils.logs.logger_factory import setup_logger
from enums.funcionarios.tipo_folga import TipoFolga
from enums.funcionarios.tipo_profissional import TipoProfissional
from enums.producao.tipo_setor import TipoSetor

logger = setup_logger('Funcionario')

class Funcionario:
    """
    👷 Representa um funcionário da produção com controle de jornada, folgas e ocupações.
    ✔️ Gerencia folgas semanais e mensais.
    ✔️ Verifica disponibilidade para alocação em atividades.
    ✔️ Registra ocupações por atividade, ordem e pedido.
    """

    def __init__(
        self,
        id: int,
        nome: str,
        setor: List[TipoSetor],
        tipo_profissional: List[TipoProfissional],
        regras_folga: List[RegraFolga],
        ch_semanal: int,
        horario_inicio: time,
        horario_final: time,
        horario_intervalo: tuple[time, timedelta],
        fip: float,
        
    ):
        self.id = id
        self.nome = nome
        self.setor = setor
        self.tipo_profissional = tipo_profissional
        self.fip = fip
        self.ch = ch_semanal
        self.horario_inicio_turno = horario_inicio
        self.horario_final_turno = horario_final
        self.horario_intervalo = horario_intervalo  # (horário, duração)



        # (id_ordem, id_pedido, id_atividade, nome_atividade, inicio, fim)
        self.ocupacoes: List[tuple[int, int, int, str, datetime, datetime]] = []

        self.regras_folga = regras_folga
        self.folga_semanal = None
        self.folga_mensal = []

        # (id_ordem, id_pedido, id_atividade, atividade_nome, inicio, fim)
        self.historico_alocacoes: List[Tuple[int, int, int, str, datetime, datetime]] = []

        for regra in regras_folga:
            if regra.tipo == TipoFolga.DIA_FIXO_SEMANA:
                self.folga_semanal = regra.dia_semana.value
            elif regra.tipo == TipoFolga.N_DIA_SEMANA_DO_MES:
                self.folga_mensal = [regra.dia_semana.value, regra.n_ocorrencia]

    # ==========================================================
    # ✅ Validações
    # ==========================================================
    def esta_de_folga(self, dia: datetime) -> bool:
        data = dia.date()
        dia_semana = data.weekday()

        if self.folga_semanal is not None:
            if dia_semana == mapa_dia_semana[self.folga_semanal]:
                return True

        if self.folga_mensal:
            dia_folga, n_ocorrencia = self.folga_mensal
            dia_semana_alvo = mapa_dia_semana[dia_folga]

            contador = 0
            data_cursor = date(data.year, data.month, 1)
            while data_cursor.month == data.month:
                if data_cursor.weekday() == dia_semana_alvo:
                    contador += 1
                    if contador == n_ocorrencia and data_cursor == data:
                        return True
                data_cursor += timedelta(days=1)

        return False
    
    def ja_esta_no_pedido(self, id_pedido: int, id_ordem: int) -> bool:
        for ocupacao in self.ocupacoes:
            oid, pid, *_ = ocupacao
            if pid == id_pedido and oid == id_ordem:
                return True
        return False

    # ==========================================================
    # 🔍 Validações Detalhadas (Retornam Tuple[bool, str])
    # ==========================================================

    def validar_folga(self, inicio: datetime, fim: datetime) -> Tuple[bool, str]:
        """
        Valida se o funcionário NÃO está de folga no período.

        Returns:
            (True, "Disponível") se NÃO está de folga
            (False, "Motivo") se ESTÁ de folga
        """
        if self.esta_de_folga(inicio):
            return False, f"Funcionário de folga em {inicio.strftime('%d/%m/%Y')}"

        if self.esta_de_folga(fim):
            return False, f"Funcionário de folga em {fim.strftime('%d/%m/%Y')}"

        return True, "Disponível (não está de folga)"

    def _eh_turno_noturno(self) -> bool:
        """Verifica se o turno cruza a meia-noite (ex: 22:00-07:00)."""
        return self.horario_final_turno < self.horario_inicio_turno

    def validar_horario_turno(self, inicio: datetime, fim: datetime) -> Tuple[bool, str]:
        """
        Valida se o período está dentro do horário de turno do funcionário.
        Suporta turnos noturnos que cruzam a meia-noite (ex: 22:00-07:00).

        Returns:
            (True, "Disponível") se está dentro do turno
            (False, "Motivo") se está fora do turno
        """
        hora_inicio = inicio.time()
        hora_fim = fim.time()

        if self._eh_turno_noturno():
            # Turno noturno (ex: 22:00-07:00)
            # Válido se: hora >= 22:00 OU hora <= 07:00
            inicio_valido = (hora_inicio >= self.horario_inicio_turno or
                           hora_inicio <= self.horario_final_turno)
            fim_valido = (hora_fim >= self.horario_inicio_turno or
                         hora_fim <= self.horario_final_turno)

            if not inicio_valido:
                return False, (
                    f"Fora do turno {self.horario_inicio_turno.strftime('%H:%M')}-"
                    f"{self.horario_final_turno.strftime('%H:%M')}"
                )
            if not fim_valido:
                return False, (
                    f"Fora do turno {self.horario_inicio_turno.strftime('%H:%M')}-"
                    f"{self.horario_final_turno.strftime('%H:%M')}"
                )
        else:
            # Turno diurno normal (ex: 08:00-18:00)
            if hora_inicio < self.horario_inicio_turno:
                return False, (
                    f"Fora do turno {self.horario_inicio_turno.strftime('%H:%M')}-"
                    f"{self.horario_final_turno.strftime('%H:%M')}"
                )
            if hora_fim > self.horario_final_turno:
                return False, (
                    f"Fora do turno {self.horario_inicio_turno.strftime('%H:%M')}-"
                    f"{self.horario_final_turno.strftime('%H:%M')}"
                )

        return True, "Disponível (dentro do turno)"

    def validar_intervalo(self, inicio: datetime, fim: datetime) -> Tuple[bool, str]:
        """
        Valida se o período NÃO sobrepõe com o intervalo de almoço.

        Returns:
            (True, "Disponível") se NÃO sobrepõe
            (False, "Motivo") se sobrepõe
        """
        inicio_intv, duracao_intv = self.horario_intervalo
        inicio_intervalo = datetime.combine(inicio.date(), inicio_intv)
        fim_intervalo = inicio_intervalo + duracao_intv

        # Verifica se NÃO há sobreposição
        if not (fim <= inicio_intervalo or inicio >= fim_intervalo):
            return False, (
                f"Sobrepõe intervalo "
                f"({inicio_intervalo.strftime('%H:%M')} - {fim_intervalo.strftime('%H:%M')})"
            )

        return True, "Disponível (não sobrepõe intervalo)"

    def validar_conflitos_ocupacao(self, inicio: datetime, fim: datetime) -> Tuple[bool, str]:
        """
        Valida se NÃO há conflitos com outras ocupações já registradas.

        Returns:
            (True, "Disponível") se NÃO há conflitos
            (False, "Motivo") se há conflitos
        """
        for i, (_, _, _, _, ocup_inicio, ocup_fim) in enumerate(self.ocupacoes):
            if not (fim <= ocup_inicio or inicio >= ocup_fim):
                return False, (
                    f"Conflito com ocupação de {ocup_inicio.strftime('%H:%M')} "
                    f"a {ocup_fim.strftime('%H:%M')}"
                )

        return True, "Disponível (sem conflitos)"

    def validar_disponibilidade_completa(self, inicio: datetime, fim: datetime) -> Tuple[bool, str]:
        """
        Valida TODAS as restrições de disponibilidade do funcionário.
        Executa validações em ordem e retorna no primeiro erro encontrado.

        Returns:
            (True, "Disponível") se passou em todas as validações
            (False, "Motivo") com o primeiro motivo de falha encontrado
        """
        # 1. Validar folga
        valido, motivo = self.validar_folga(inicio, fim)
        if not valido:
            return False, motivo

        # 2. Validar horário de turno
        valido, motivo = self.validar_horario_turno(inicio, fim)
        if not valido:
            return False, motivo

        # 3. Validar intervalo
        valido, motivo = self.validar_intervalo(inicio, fim)
        if not valido:
            return False, motivo

        # 4. Validar conflitos de ocupação
        valido, motivo = self.validar_conflitos_ocupacao(inicio, fim)
        if not valido:
            return False, motivo

        return True, "Disponível (passou em todas as validações)"

    # ==========================================================
    # 🔄 Métodos Legados (mantidos para compatibilidade)
    # ==========================================================

    def verificar_disponibilidade_no_intervalo(self, inicio: datetime, fim: datetime) -> Tuple[bool, str]:
        for i, (_, _, _, _, ocup_inicio, ocup_fim) in enumerate(self.ocupacoes):
            if not (fim <= ocup_inicio or inicio >= ocup_fim):
                logger.debug(
                    f"🚫 Conflito detectado na ocupação {i}: "
                    f"({ocup_inicio.strftime('%H:%M')} - {ocup_fim.strftime('%H:%M')}) "
                    f"vs tentativa ({inicio.strftime('%H:%M')} - {fim.strftime('%H:%M')})"
                )
                return False, (
                    f"Conflito com ocupação de {ocup_inicio.strftime('%H:%M')} "
                    f"a {ocup_fim.strftime('%H:%M')}."
                )
        return True, "Disponível."

    def esta_disponivel(self, inicio: datetime, duracao_min: timedelta) -> bool:
        fim = inicio + duracao_min

        if self.esta_de_folga(inicio) or self.esta_de_folga(fim):
            return False

        # Validar turno (com suporte a turnos noturnos)
        hora_inicio = inicio.time()
        hora_fim = fim.time()

        if self._eh_turno_noturno():
            # Turno noturno (ex: 22:00-07:00)
            inicio_valido = (hora_inicio >= self.horario_inicio_turno or
                           hora_inicio <= self.horario_final_turno)
            fim_valido = (hora_fim >= self.horario_inicio_turno or
                         hora_fim <= self.horario_final_turno)
            if not (inicio_valido and fim_valido):
                return False
        else:
            # Turno diurno normal
            if hora_inicio < self.horario_inicio_turno or hora_fim > self.horario_final_turno:
                return False

        # Validar intervalo
        inicio_intv, duracao_intv = self.horario_intervalo
        inicio_intervalo = datetime.combine(inicio.date(), inicio_intv)
        fim_intervalo = inicio_intervalo + duracao_intv

        if not (fim <= inicio_intervalo or inicio >= fim_intervalo):
            return False

        for _, _, _, _, ocup_inicio, ocup_fim in self.ocupacoes:
            if not (fim <= ocup_inicio or inicio >= ocup_fim):
                return False

        return True

    def registrar_ocupacao(
        self,
        id_ordem: int,
        id_pedido: int,
        id_atividade_json: int,
        nome_atividade: str,
        inicio: datetime,
        fim: datetime
    ):
        disponivel, motivo = self.verificar_disponibilidade_no_intervalo(inicio, fim)
        if disponivel:
            self.ocupacoes.append((id_ordem, id_pedido, id_atividade_json, nome_atividade, inicio, fim))
            logger.info(
                f"✅ {self.nome} | Ocupação registrada: {nome_atividade} de {inicio.strftime('%H:%M')} "
                f"até {fim.strftime('%H:%M')}."
            )

        else:
            logger.warning(
                f"🚫 {self.nome} | Ocupação não registrada: {nome_atividade} de {inicio.strftime('%H:%M')} "
                f"até {fim.strftime('%H:%M')}. Motivo: {motivo}"
            )

    # ==========================================================
    # 🔒 Liberação
    # ==========================================================
    def liberar_por_atividade(self, id_ordem: int, id_pedido: int, id_atividade: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            o for o in self.ocupacoes
            if not (o[0] == id_ordem and o[1] == id_pedido and o[2] == id_atividade)
        ]
        depois = len(self.ocupacoes)
        if antes != depois:
            logger.info(f"🔓 Ocupação do {self.nome} liberada para a atividade {id_atividade} do pedido {id_pedido} da ordem {id_ordem}.")
        # else:
        #     logger.warning(f"⚠️ Nenhuma ocupação encontrada para liberar o {self.nome} da atividade {id_atividade} do pedido {id_pedido} da ordem {id_ordem}.")

    def liberar_por_pedido(self, id_ordem: int, id_pedido: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            o for o in self.ocupacoes
            if not (o[0] == id_ordem and o[1] == id_pedido)
        ]
        depois = len(self.ocupacoes)
        if antes != depois:
            logger.info(f"🔓 Ocupação do {self.nome} liberada para o pedido {id_pedido} da ordem {id_ordem}.")
        #else:
            #logger.warning(f"⚠️ Nenhuma ocupação encontrada para liberar o {self.nome} do pedido {id_pedido} da ordem {id_ordem}.")
       
    
    def liberar_por_ordem(self, id_ordem: int):
        antes = len(self.ocupacoes)
        self.ocupacoes = [
            o for o in self.ocupacoes
            if o[0] != id_ordem
        ]
        depois = len(self.ocupacoes)
        if antes != depois:
            logger.info(f"🔓 Ocupação do {self.nome} liberada da ordem {id_ordem}.")
        #else:
            #logger.warning(f"⚠️ Nenhuma ocupação encontrada do {self.nome} para liberar da ordem {id_ordem}.")

    # ==========================================================
    # 📅 Agenda 
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info(f"📅 Agenda do Funcionário: {self.nome}")
        logger.info("==============================================")
        
        for ocupacao in self.ocupacoes:
            id_ordem, id_pedido, atividade_json_id, nome_atividade, inicio, fim = ocupacao
            logger.info(
                f"🗓️ Ocupação: Ordem {id_ordem}, Pedido {id_pedido}, {nome_atividade} "
                f"de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}"
            )

    def mostrar_folgas(self, inicio: datetime, fim: datetime):
        print(f"🛌 Folgas de {self.nome} entre {inicio.strftime('%d/%m/%Y')} e {fim.strftime('%d/%m/%Y')}:")
        data_atual = inicio
        folgas = []

        while data_atual <= fim:
            if self.esta_de_folga(data_atual):
                folgas.append(data_atual.strftime('%A, %d/%m/%Y'))
            data_atual += timedelta(days=1)

        if folgas:
            for dia in folgas:
                print(f"  • {dia}")
        else:
            print("  Nenhuma folga registrada nesse período.")

    # ==========================================================
    # 📊 Contabilização de Horas
    # ==========================================================
    def calcular_horas_por_dia(self, data_inicio: date = None, data_fim: date = None) -> dict:
        """
        Calcula as horas trabalhadas por dia em um período específico.

        Args:
            data_inicio: Data início do período (opcional - se não fornecida, usa todas as ocupações)
            data_fim: Data fim do período (opcional - se não fornecida, usa todas as ocupações)

        Returns:
            dict: {data: {'horas': float, 'atividades': [{'nome': str, 'horas': float}]}}
        """
        horas_por_dia = {}

        for ocupacao in self.ocupacoes:
            id_ordem, id_pedido, atividade_json_id, nome_atividade, inicio, fim = ocupacao

            data_ocupacao = inicio.date()

            # Filtrar por período se especificado
            if data_inicio and data_ocupacao < data_inicio:
                continue
            if data_fim and data_ocupacao > data_fim:
                continue

            # Calcular duração em horas
            duracao = fim - inicio
            horas = duracao.total_seconds() / 3600

            # Inicializar dia se não existir
            if data_ocupacao not in horas_por_dia:
                horas_por_dia[data_ocupacao] = {
                    'horas': 0.0,
                    'atividades': []
                }

            # Adicionar horas e atividade
            horas_por_dia[data_ocupacao]['horas'] += horas
            horas_por_dia[data_ocupacao]['atividades'].append({
                'id_atividade': atividade_json_id,
                'nome': nome_atividade,
                'horas': round(horas, 2),
                'inicio': inicio.strftime('%H:%M'),
                'fim': fim.strftime('%H:%M'),
                'ordem': id_ordem,
                'pedido': id_pedido
            })

        # Arredondar total de horas por dia
        for data in horas_por_dia:
            horas_por_dia[data]['horas'] = round(horas_por_dia[data]['horas'], 2)

        return horas_por_dia

    def obter_total_horas_periodo(self, data_inicio: date = None, data_fim: date = None) -> float:
        """
        Obtém o total de horas trabalhadas em um período.

        Args:
            data_inicio: Data início do período (opcional)
            data_fim: Data fim do período (opcional)

        Returns:
            float: Total de horas trabalhadas no período
        """
        horas_por_dia = self.calcular_horas_por_dia(data_inicio, data_fim)
        return sum(dia['horas'] for dia in horas_por_dia.values())

    def obter_media_horas_diarias(self, data_inicio: date = None, data_fim: date = None) -> float:
        """
        Calcula a média de horas trabalhadas por dia no período.

        Args:
            data_inicio: Data início do período (opcional)
            data_fim: Data fim do período (opcional)

        Returns:
            float: Média de horas por dia trabalhado
        """
        horas_por_dia = self.calcular_horas_por_dia(data_inicio, data_fim)
        if not horas_por_dia:
            return 0.0

        total_horas = sum(dia['horas'] for dia in horas_por_dia.values())
        dias_trabalhados = len(horas_por_dia)

        return round(total_horas / dias_trabalhados, 2) if dias_trabalhados > 0 else 0.0

    def gerar_relatorio_horas(self, data_inicio: date = None, data_fim: date = None) -> str:
        """
        Gera um relatório detalhado das horas trabalhadas por dia.

        Args:
            data_inicio: Data início do período (opcional)
            data_fim: Data fim do período (opcional)

        Returns:
            str: Relatório formatado em texto
        """
        horas_por_dia = self.calcular_horas_por_dia(data_inicio, data_fim)

        if not horas_por_dia:
            return f"📊 {self.nome}: Nenhuma ocupação registrada no período especificado."

        relatorio = []
        relatorio.append("=" * 60)
        relatorio.append(f"📊 RELATÓRIO DE HORAS - {self.nome}")
        relatorio.append("=" * 60)

        # Período
        if data_inicio or data_fim:
            periodo_inicio = data_inicio.strftime('%d/%m/%Y') if data_inicio else "início"
            periodo_fim = data_fim.strftime('%d/%m/%Y') if data_fim else "fim"
            relatorio.append(f"📅 Período: {periodo_inicio} até {periodo_fim}")

        # Totais
        total_horas = self.obter_total_horas_periodo(data_inicio, data_fim)
        media_diaria = self.obter_media_horas_diarias(data_inicio, data_fim)
        dias_trabalhados = len(horas_por_dia)

        relatorio.append(f"⏰ Total de horas: {total_horas}h")
        relatorio.append(f"📈 Média diária: {media_diaria}h")
        relatorio.append(f"📆 Dias trabalhados: {dias_trabalhados}")
        relatorio.append("")

        # Detalhes por dia
        relatorio.append("📋 DETALHAMENTO POR DIA:")
        for data in sorted(horas_por_dia.keys()):
            dia_info = horas_por_dia[data]
            relatorio.append(f"\n📅 {data.strftime('%A, %d/%m/%Y')} - {dia_info['horas']}h:")

            for atividade in dia_info['atividades']:
                relatorio.append(
                    f"   • {atividade['nome']} ({atividade['inicio']}-{atividade['fim']}) "
                    f"- {atividade['horas']}h | O:{atividade['ordem']} P:{atividade['pedido']}"
                )

        relatorio.append("\n" + "=" * 60)

        return "\n".join(relatorio)