from datetime import datetime, timedelta, date, time
from typing import List, Optional, Tuple
from utils.funcionarios.regras_folga import RegraFolga
from utils.time.data_utils import mapa_dia_semana, formatar_hora_e_min
from utils.logs.logger_factory import setup_logger
from enums.funcionarios.tipo_folga import TipoFolga
from enums.funcionarios.tipo_profissional import TipoProfissional

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



        # (id_ordem, id_pedido, id_atividade, inicio, fim)
        self.ocupacoes: List[tuple[int, int, int, datetime, datetime]] = []

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
    
    def verificar_disponibilidade_no_intervalo(self, inicio: datetime, fim: datetime) -> Tuple[bool, str]:
        for i, (_, _, _, ocup_inicio, ocup_fim) in enumerate(self.ocupacoes):
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
        id_ordem: int,
        id_pedido: int,
        id_atividade_json: int,
        inicio: datetime,
        fim: datetime
    ):
        disponivel, motivo = self.verificar_disponibilidade_no_intervalo(inicio, fim)
        if disponivel:
            self.ocupacoes.append((id_ordem, id_pedido, id_atividade_json, inicio, fim))
            logger.info(
                f"✅ {self.nome} | Ocupação registrada: {id_atividade_json} de {inicio.strftime('%H:%M')} "
                f"até {fim.strftime('%H:%M')}."
            )
            
        else:
            logger.warning(
                f"🚫 {self.nome} | Ocupação não registrada: {id_atividade_json} de {inicio.strftime('%H:%M')} "
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
            id_ordem, id_pedido, atividade_json_id, inicio, fim = ocupacao
            logger.info(
                f"🗓️ Ocupação: Ordem {id_ordem}, Pedido {id_pedido}, Atividade {atividade_json_id} "
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