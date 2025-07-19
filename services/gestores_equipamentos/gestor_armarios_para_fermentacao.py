from datetime import datetime, timedelta
from typing import List, Optional, Tuple, Union, TYPE_CHECKING
from models.equipamentos.armario_esqueleto import ArmarioEsqueleto
from models.equipamentos.armario_fermentador import ArmarioFermentador
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular
from utils.producao.conversores_ocupacao import gramas_para_niveis_tela, unidades_para_niveis_tela
from utils.logs.logger_factory import setup_logger
from enums.producao.tipo_item import TipoItem

# 🗄️ Logger exclusivo do gestor de Armários para Fermentação
logger = setup_logger('GestorArmariosParaFermentacao')

Armarios = Union[ArmarioEsqueleto, ArmarioFermentador]

class GestorArmariosParaFermentacao:
    """
    🗄️ Gestor especializado no controle de Armários para Fermentação (tipo Esqueleto e Fermentador).
    Utiliza backward scheduling e FIP.
    """
    def __init__(self, armarios: List[Armarios]):
        self.armarios = armarios
    
    # ==========================================================
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
    # ==========================================================
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[Armarios]:
        ordenadas = sorted(
            self.armarios,
            key=lambda m: atividade.fips_equipamentos.get(m, 999)
        )
        # logger.info("📊 Ordem dos armários esqueleto por FIP (prioridade):")
        # for m in ordenadas:
        #     fip = atividade.fips_equipamentos.get(m, 999)
        #     logger.info(f"🔹 {m.nome} (FIP: {fip})")
        return ordenadas
    
    # ==========================================================
    # 🎯 Alocação
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade: int
    ) -> Tuple[bool, Optional[ArmarioEsqueleto], Optional[datetime], Optional[datetime]]:
        """
        🗄️ Faz a alocação utilizando backward scheduling por FIP.
        Converte a quantidade para níveis de tela automaticamente.
        Retorna (True, equipamento, inicio_real, fim_real) se sucesso.
        Caso contrário: (False, None, None, None)
        """
        duracao = atividade.duracao
        armarios_ordenados = self._ordenar_por_fip(atividade)
        horario_final_tentativa = fim

    
        if atividade.tipo_item is TipoItem.SUBPRODUTO:
            niveis_necessarios = gramas_para_niveis_tela(quantidade)
        elif atividade.tipo_item is TipoItem.PRODUTO:
            niveis_necessarios = unidades_para_niveis_tela(quantidade)

        print(f"🔍 Níveis necessários para {quantidade}: {niveis_necessarios}")
        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            for armario in armarios_ordenados:
                if not armario.verificar_espaco_niveis(niveis_necessarios, horario_inicio_tentativa, horario_final_tentativa):
                    continue

                sucesso = armario.ocupar_niveis(
                    ordem_id=atividade.ordem_id,
                    pedido_id=atividade.pedido_id,
                    atividade_id=atividade.id_atividade,
                    quantidade=niveis_necessarios,
                    inicio=horario_inicio_tentativa,
                    fim=horario_final_tentativa
                )

                if sucesso:
                    atividade.equipamento_alocado = armario
                    atividade.equipamentos_selecionados = [armario]
                    atividade.alocada = True

                    logger.info(
                        f"✅ Atividade {atividade.id_atividade} alocada no {armario.nome}"
                        f"{horario_inicio_tentativa.strftime('%H:%M')} → {horario_final_tentativa.strftime('%H:%M')} | "
                        f"{niveis_necessarios} níveis"
                    )
               
                    return True, armario, horario_inicio_tentativa, horario_final_tentativa

            horario_final_tentativa -= timedelta(minutes=1)

        logger.error(
            f"❌ Atividade {atividade.id_atividade} não alocada entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}"
        )
        return False, None, None, None

    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade: "AtividadeModular") -> None:
        for armario in self.armarios:
            armario.liberar_por_atividade(ordem_id=atividade.ordem_id, pedido_id=atividade.pedido_id, atividade_id=atividade.id_atividade)

    def liberar_por_pedido(self, atividade: "AtividadeModular") -> None:
        for armario in self.armarios:
            armario.liberar_por_pedido(ordem_id=atividade.ordem_id, pedido_id=atividade.pedido_id)

    def liberar_por_ordem(self, atividade: "AtividadeModular") -> None:
        for armario in self.armarios:
            armario.liberar_por_ordem(atividade.ordem_id)

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime) -> None:
        for armario in self.armarios:
            armario.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self) -> None:
        for armario in self.armarios:
            armario.liberar_todas_ocupacoes()

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self) -> None:
        logger.info("==============================================")
        logger.info("📅 Agenda dos Armários para Fermentação")
        logger.info("==============================================")
        for armario in self.armarios:
            armario.mostrar_agenda()
