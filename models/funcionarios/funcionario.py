from datetime import datetime, timedelta, date, time
from typing import List, Optional
from utils.regras_folga import RegraFolga
from utils.data_utils import mapa_dia_semana
from enums.tipo_folga import TipoFolga
from enums.tipo_profissional import TipoProfissional
from utils.data_utils import formatar_hora_e_min


class Funcionario:
    """
    👷 Classe responsável por representar um funcionário da produção.

    Armazena dados contratuais, regras de folga, disponibilidade e histórico
    de ocupações para permitir o agendamento de atividades via backward scheduling.
    """

    def __init__(
        self,
        id: int,
        nome: str,
        tipo_profissional: TipoProfissional,
        regras_folga: List[RegraFolga],
        ch_semanal: int,
        horario_inicio: time,
        horario_final: time,
        horario_intervalo: tuple[time, timedelta],
        fip: float,
    ):
        # Identificação e perfil
        self.id = id
        self.nome = nome
        self.tipo_profissional = tipo_profissional
        self.fip = fip  # fator de importância (priorização por menor FIP)

        # Carga horária e jornada de trabalho
        self.ch = ch_semanal
        self.horario_inicio_turno = horario_inicio
        self.horario_final_turno = horario_final
        self.horario_intervalo = horario_intervalo  # (horário, duração)

        # Ocupações confirmadas: (id_atividade, inicio, fim)
        self.ocupacoes: List[tuple[int, datetime, datetime]] = []

        # Regras de folga (semanais e mensais)
        self.regras_folga = regras_folga
        self.folga_semanal = None
        self.folga_mensal = []

        for regra in regras_folga:
            if regra.tipo == TipoFolga.DIA_FIXO_SEMANA:
                self.folga_semanal = regra.dia_semana.value
            elif regra.tipo == TipoFolga.N_DIA_SEMANA_DO_MES:
                self.folga_mensal = [regra.dia_semana.value, regra.n_ocorrencia]

    def esta_de_folga(self, dia: datetime) -> bool:
        """
        Verifica se o funcionário estará de folga em uma determinada data.
        Considera tanto folga semanal fixa quanto ocorrência mensal (ex: 2ª sexta-feira do mês).
        """
        data = dia.date()
        dia_semana = data.weekday()

        # Folga semanal
        if self.folga_semanal is not None:
            if dia_semana == mapa_dia_semana[self.folga_semanal]:
                return True

        # Folga mensal
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

    def esta_disponivel(self, inicio: datetime, duracao_min: timedelta) -> bool:
        """
        Verifica se o funcionário está disponível para assumir uma atividade no intervalo indicado.
        Considera:
        - Folgas
        - Horário de trabalho
        - Intervalo de refeição
        - Choques com ocupações anteriores
        """
        fim = inicio + duracao_min

        if self.esta_de_folga(inicio) or self.esta_de_folga(fim):
            return False

        # Turno e intervalo
        inicio_turno = datetime.combine(inicio.date(), self.horario_inicio_turno)
        fim_turno = datetime.combine(inicio.date(), self.horario_final_turno)
        inicio_intv, duracao_intv = self.horario_intervalo
        inicio_intervalo = datetime.combine(inicio.date(), inicio_intv)
        fim_intervalo = inicio_intervalo + duracao_intv

        if inicio < inicio_turno or fim > fim_turno:
            return False

        if not (fim <= inicio_intervalo or inicio >= fim_intervalo):
            return False

        # Choque com ocupações
        for id_ativ, ocup_inicio, ocup_fim in self.ocupacoes:
            if not (fim <= ocup_inicio or inicio >= ocup_fim):
                return False

        return True

    def registrar_ocupacao(self, inicio: datetime, fim: datetime, id_atividade: int):
        """
        Registra uma ocupação para a atividade informada,
        desde que o horário seja válido e não conflite com outras ocupações.
        """
        if self.esta_disponivel(inicio, fim - inicio):
            self.ocupacoes.append((id_atividade, inicio, fim))
            print(f"⏱️ {self.nome} ocupado de {inicio.time()} até {fim.time()} — Atividade #{id_atividade}")
        else:
            print(f"⚠️ {self.nome} não está disponível para a atividade no horário solicitado.")

    def desalocar(self, id_atividade: int):
        """
        Remove a ocupação associada a uma atividade específica, se existente.

        🔁 Usado em operações de rollback quando a alocação geral falha.
        """
        ocup_antes = len(self.ocupacoes)
        self.ocupacoes = [oc for oc in self.ocupacoes if oc[0] != id_atividade]
        ocup_depois = len(self.ocupacoes)

        if ocup_antes > ocup_depois:
            print(f"↩️ {self.nome} desalocado da atividade #{id_atividade}")
        else:
            print(f"⚠️ Nenhuma ocupação encontrada para desalocar: atividade #{id_atividade}")

    def mostrar_ocupacoes(self):
        """
        Exibe todas as ocupações já registradas no funcionário.
        """
        if not self.ocupacoes:
            print(f"✅ {self.nome} não possui ocupações registradas.")
            return

        print(f"📅 Ocupações de {self.nome}:")
        for i, (id_atividade, inicio, fim) in enumerate(sorted(self.ocupacoes, key=lambda o: o[1]), start=1):
            data_str = inicio.strftime('%d/%m/%Y')
            hora_inicio = inicio.strftime('%H:%M')
            hora_fim = fim.strftime('%H:%M')
            duracao_min = int((fim - inicio).total_seconds() // 60)
            print(f"  {i}. {data_str} — das {hora_inicio} às {hora_fim} ({duracao_min} min) → id_atividade:{id_atividade}")

    def mostrar_folgas(self, inicio: datetime, fim: datetime):
        """
        Exibe as datas de folga do funcionário no intervalo especificado.
        """
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

    def __str__(self):
        return (
            f"Funcionario: id = {self.id} | nome = {self.nome} | tipo_profissional = {self.tipo_profissional}\n"
            f"carga_horaria = {self.ch} | fator_importancia = {self.fip}\n"
            f"horario_inicio_turno = {formatar_hora_e_min(self.horario_inicio_turno)}\n"
            f"horario_final_turno = {formatar_hora_e_min(self.horario_final_turno)}\n"
            f"intervalo de {self.horario_intervalo[1].seconds // 60} min às {formatar_hora_e_min(self.horario_intervalo[0])}"
        )
