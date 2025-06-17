from datetime import datetime, timedelta, date, time
from typing import List, Optional, Tuple
from utils.regras_folga import RegraFolga
from utils.data_utils import mapa_dia_semana, formatar_hora_e_min
from enums.tipo_folga import TipoFolga
from enums.tipo_profissional import TipoProfissional


class Funcionario:
    """
    👷 Representa um funcionário da produção com controle de jornada, folgas e ocupações.
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
        self.id = id
        self.nome = nome
        self.tipo_profissional = tipo_profissional
        self.fip = fip
        self.ch = ch_semanal
        self.horario_inicio_turno = horario_inicio
        self.horario_final_turno = horario_final
        self.horario_intervalo = horario_intervalo  # (horário, duração)



        # (ordem_id, id_atividade_modular, id_atividade_json, inicio, fim)
        self.ocupacoes: List[tuple[int, int, int, datetime, datetime]] = []

        self.regras_folga = regras_folga
        self.folga_semanal = None
        self.folga_mensal = []
        # (ordem_id, atividade_id, atividade_nome, inicio, fim)
        self.historico_alocacoes: List[Tuple[int, int, str, datetime, datetime]] = []

        for regra in regras_folga:
            if regra.tipo == TipoFolga.DIA_FIXO_SEMANA:
                self.folga_semanal = regra.dia_semana.value
            elif regra.tipo == TipoFolga.N_DIA_SEMANA_DO_MES:
                self.folga_mensal = [regra.dia_semana.value, regra.n_ocorrencia]

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

    def esta_disponivel(self, inicio: datetime, duracao_min: timedelta) -> bool:
        fim = inicio + duracao_min

        if self.esta_de_folga(inicio) or self.esta_de_folga(fim):
            return False

        inicio_turno = datetime.combine(inicio.date(), self.horario_inicio_turno)
        fim_turno = datetime.combine(inicio.date(), self.horario_final_turno)
        inicio_intv, duracao_intv = self.horario_intervalo
        inicio_intervalo = datetime.combine(inicio.date(), inicio_intv)
        fim_intervalo = inicio_intervalo + duracao_intv

        if inicio < inicio_turno or fim > fim_turno:
            return False
        if not (fim <= inicio_intervalo or inicio >= fim_intervalo):
            return False

        for _, _, _, ocup_inicio, ocup_fim in self.ocupacoes:
            if not (fim <= ocup_inicio or inicio >= ocup_fim):
                return False

        return True

    def registrar_ocupacao(
        self,
        ordem_id: int,
        id_atividade_modular: int,
        id_atividade_json: int,
        inicio: datetime,
        fim: datetime
    ):
        disponivel, motivo = self.verificar_disponibilidade(inicio, fim)
        if disponivel:
            self.ocupacoes.append((ordem_id, id_atividade_modular, id_atividade_json, inicio, fim))
            print(
                f"⏱️ {self.nome} ocupado de {inicio.time()} até {fim.time()} "
                f"— Ordem #{ordem_id} | Atividade #{id_atividade_modular}/{id_atividade_json}"
            )
        else:
            print(
                f"⚠️ {self.nome} não está disponível para a atividade no horário solicitado. "
                f"Motivo: {motivo}"
            )


    def desalocar(self, id_atividade: int, ordem_id: Optional[int] = None):
        """
        🔁 Remove a ocupação associada à atividade e, se fornecido, à ordem específica.
        """
        ocup_antes = len(self.ocupacoes)

        if ordem_id is not None:
            self.ocupacoes = [
                oc for oc in self.ocupacoes
                if not (oc[0] == ordem_id and oc[1] == id_atividade)
            ]
        else:
            self.ocupacoes = [oc for oc in self.ocupacoes if oc[1] != id_atividade]

        ocup_depois = len(self.ocupacoes)
        if ocup_antes > ocup_depois:
            print(f"↩️ {self.nome} desalocado da atividade #{id_atividade} (ordem {ordem_id if ordem_id else 'todas'})")
        else:
            print(f"⚠️ Nenhuma ocupação encontrada para desalocar: atividade #{id_atividade} (ordem {ordem_id if ordem_id else 'todas'})")

    def mostrar_ocupacoes(self):
        if not self.ocupacoes:
            print(f"✅ {self.nome} não possui ocupações registradas.")
            return

        print(f"📅 Ocupações de {self.nome}:")
        for i, (ordem_id, id_atividade, id_json, inicio, fim) in enumerate(sorted(self.ocupacoes, key=lambda o: o[3]), start=1):
            data_str = inicio.strftime('%d/%m/%Y')
            hora_inicio = inicio.strftime('%H:%M')
            hora_fim = fim.strftime('%H:%M')
            duracao_min = int((fim - inicio).total_seconds() // 60)
            print(f"  {i}. {data_str} — das {hora_inicio} às {hora_fim} ({duracao_min} min) → ordem:{ordem_id} | atividade:{id_atividade}/{id_json}")

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

    def __str__(self):
        return (
            f"Funcionario: id = {self.id} | nome = {self.nome} | tipo_profissional = {self.tipo_profissional}\n"
            f"carga_horaria = {self.ch} | fator_importancia = {self.fip}\n"
            f"horario_inicio_turno = {formatar_hora_e_min(self.horario_inicio_turno)}\n"
            f"horario_final_turno = {formatar_hora_e_min(self.horario_final_turno)}\n"
            f"intervalo de {self.horario_intervalo[1].seconds // 60} min às {formatar_hora_e_min(self.horario_intervalo[0])}"
        )
    def esta_de_folga(self, data: datetime) -> bool:
        """
        Verifica se o funcionário está de folga em uma determinada data.
        """
        for folga in self.folgas:
            if folga[0] <= data <= folga[1]:
                return True
        return False
        
    # ========================================================
    # ALOCACOES SEM CRITERIOS DE FOLGA OU VERIFICACAO DE HORÁRIOS
    # ========================================================

    def registrar_alocacao(self, ordem_id: int, atividade_id: int, nome_atividade: str, inicio: datetime, fim: datetime):
        """
        Registra uma alocação da atividade associada à ordem com seus horários.
        """
        self.historico_alocacoes.append((ordem_id, atividade_id, nome_atividade, inicio, fim))

    def ja_esta_na_ordem(self, ordem_id: int) -> bool:
        """
        Verifica se o funcionário já foi alocado em alguma atividade da ordem fornecida.
        """
        return any(oid == ordem_id for oid, _, _, _, _ in self.historico_alocacoes)


    def exibir_historico(self):
        """
        Apenas para debug ou visualização.
        """
        for oid, aid, ini, fim in self.historico_alocacoes:
            print(f"📦 Ordem {oid} | Atividade {aid} | {ini.strftime('%H:%M')} - {fim.strftime('%H:%M')} - ")

    def verificar_disponibilidade(self, inicio: datetime, fim: datetime) -> Tuple[bool, str]:
        """
        🔍 Verifica se o funcionário está disponível entre `inicio` e `fim`,
        analisando apenas conflitos com outras ocupações.
        """
        for _, _, _, ocup_inicio, ocup_fim in self.ocupacoes:
            if not (fim <= ocup_inicio or inicio >= ocup_fim):
                return False, (
                    f"Conflito com ocupação de {ocup_inicio.strftime('%H:%M')} "
                    f"a {ocup_fim.strftime('%H:%M')}."
                )

        return True, "Disponível."

