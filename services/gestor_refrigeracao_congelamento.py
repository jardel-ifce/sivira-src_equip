from datetime import datetime
from models.atividade_base import Atividade
from utils.conversores_ocupacao import gramas_para_caixas, gramas_para_niveis_tela
from utils.logger_factory import setup_logger


logger = setup_logger('GestorRefrigeracaoCongelamento')


class GestorRefrigeracaoCongelamento:
    def __init__(self, equipamento):
        self.equipamento = equipamento

    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: Atividade,
        temperatura_desejada: int
    ) -> tuple[str, datetime, datetime]:
        """
        ❄️ Tenta alocar diretamente no intervalo fornecido.
        ✔️ Faz verificação de espaço e temperatura e ajusta a câmara se possível.
        """
        if not self.equipamento.verificar_compatibilidade_de_temperatura(
            inicio, fim, temperatura_desejada
        ):
            return "ERRO_TEMPERATURA", None, None

        if not self.equipamento.selecionar_faixa_temperatura(temperatura_desejada):
            return "ERRO_TEMPERATURA", None, None

        if atividade.tipo_ocupacao == "CAIXAS":
            quantidade_caixas = gramas_para_caixas(atividade.quantidade_produto)
            if not self.equipamento.verificar_espaco_caixas(quantidade_caixas, inicio, fim):
                return "ERRO_OCUPACAO", None, None

            sucesso = self.equipamento.ocupar_caixas(
                quantidade_caixas, inicio, fim, atividade.id
            )

        elif atividade.tipo_ocupacao == "NIVEIS_TELA":
            quantidade_niveis = gramas_para_niveis_tela(atividade.quantidade_produto)
            if not self.equipamento.verificar_espaco_niveis(quantidade_niveis, inicio, fim):
                return "ERRO_OCUPACAO", None, None

            sucesso = self.equipamento.ocupar_niveis(
                quantidade_niveis, inicio, fim, atividade.id
            )
        else:
            raise ValueError("❌ Tipo de ocupação inválido. Use 'CAIXAS' ou 'NIVEIS_TELA'.")

        if sucesso:
            return "SUCESSO", inicio, fim
        else:
            return "ERRO_OCUPACAO", None, None

    def liberar_por_atividade(self, atividade: Atividade):
        self.equipamento.liberar_por_atividade(atividade.id)

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        self.equipamento.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        self.equipamento.liberar_todas_ocupacoes()

    def liberar_intervalo(self, inicio: datetime, fim: datetime):
        self.equipamento.liberar_intervalo(inicio, fim)

    def mostrar_agenda(self):
        self.equipamento.mostrar_agenda()
