from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from models.equips.camara_refrigerada import CamaraRefrigerada
from models.atividade_base import Atividade
from utils.conversores_ocupacao import gramas_para_caixas, gramas_para_niveis_tela
from utils.gerador_ocupacao import GeradorDeOcupacaoID
from utils.logger_factory import setup_logger

# ❄️ Logger específico
logger = setup_logger('GestorRefrigeracaoCongelamento')


class GestorRefrigeracaoCongelamento:
    """
    ❄️ Gestor especializado no controle de câmaras de refrigeração/congelamento.
    Retorno padrão: (sucesso: bool, equipamento, inicio, fim)
    """

    def __init__(self, equipamentos: List[CamaraRefrigerada]):
        self.equipamentos = equipamentos
        self.gerador_ocupacao_id = GeradorDeOcupacaoID()

    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: Atividade,
        temperatura_desejada: int
    ) -> Tuple[bool, Optional[CamaraRefrigerada], Optional[datetime], Optional[datetime]]:
        """
        ❄️ Faz a alocação utilizando backward scheduling.
        Retorna (True, equipamento, inicio_real, fim_real) se sucesso.
        Caso contrário: (False, None, None, None)
        """

        duracao = atividade.duracao
        quantidade_gramas = atividade.quantidade_produto

        if atividade.tipo_ocupacao == "CAIXAS":
            quantidade_ocupacao = gramas_para_caixas(quantidade_gramas)
            metodo_verificacao = "verificar_espaco_caixas"
            metodo_ocupar = "ocupar_caixas"
        elif atividade.tipo_ocupacao == "NIVEIS_TELA":
            quantidade_ocupacao = gramas_para_niveis_tela(quantidade_gramas)
            metodo_verificacao = "verificar_espaco_niveis"
            metodo_ocupar = "ocupar_niveis"
        else:
            raise ValueError("❌ Tipo de ocupação inválido. Use 'CAIXAS' ou 'NIVEIS_TELA'.")

        equipamentos_ordenados = sorted(
            self.equipamentos,
            key=lambda eq: atividade.fips_equipamentos.get(eq, 999)
        )

        horario_final_tentativa = fim

        logger.info(
            f"🎯 Iniciando tentativa de alocação da atividade {atividade.id} "
            f"({quantidade_gramas}g | {duracao}) entre "
            f"{inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')} | Temp: {temperatura_desejada}°C"
        )

        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            for equipamento in equipamentos_ordenados:
                if not equipamento.verificar_compatibilidade_de_temperatura(
                    horario_inicio_tentativa, horario_final_tentativa, temperatura_desejada
                ):
                    continue

                if equipamento.selecionar_faixa_temperatura(temperatura_desejada) == "ERRO_TEMPERATURA":
                    continue

                if not getattr(equipamento, metodo_verificacao)(
                    quantidade_ocupacao, horario_inicio_tentativa, horario_final_tentativa
                ):
                    continue

                ocupacao_id = self.gerador_ocupacao_id.gerar_id()
                sucesso = getattr(equipamento, metodo_ocupar)(
                    ocupacao_id=ocupacao_id,
                    atividade_id=atividade.id,
                    quantidade=quantidade_ocupacao,
                    inicio=horario_inicio_tentativa,
                    fim=horario_final_tentativa
                )

                if sucesso:
                    atividade.equipamento_alocado = equipamento
                    atividade.equipamentos_selecionados = [equipamento]
                    atividade.alocada = True

                    logger.info(
                        f"✅ Atividade {atividade.id} alocada na {equipamento.nome} "
                        f"| {horario_inicio_tentativa.strftime('%H:%M')} → {horario_final_tentativa.strftime('%H:%M')} "
                        f"| Temp: {temperatura_desejada}°C"
                    )
                    return True, equipamento, horario_inicio_tentativa, horario_final_tentativa

            horario_final_tentativa -= timedelta(minutes=1)

        logger.warning(
            f"❌ Nenhuma câmara pôde ser alocada para atividade {atividade.id} "
            f"entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )
        return False, None, None, None

    # ==========================================================
    # 🔓 Liberações
    # ==========================================================
    def liberar_por_atividade(self, atividade_id: int):
        for equipamento in self.equipamentos:
            equipamento.liberar_por_atividade(atividade_id)

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        for equipamento in self.equipamentos:
            equipamento.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        for equipamento in self.equipamentos:
            equipamento.liberar_todas_ocupacoes()

    def liberar_intervalo(self, inicio: datetime, fim: datetime):
        for equipamento in self.equipamentos:
            equipamento.liberar_intervalo(inicio, fim)

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda das Câmaras de Refrigeração/Congelamento")
        logger.info("==============================================")
        for equipamento in self.equipamentos:
            equipamento.mostrar_agenda()
