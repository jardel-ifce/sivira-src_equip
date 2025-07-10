from datetime import datetime
from enum import Enum
from models.funcionarios.funcionario import Funcionario
from typing import List, Tuple
from utils.logs.logger_factory import setup_logger
logger = setup_logger("GestorFuncionarios")

class GestorFuncionarios:
    # ... demais métodos

    @staticmethod
    def priorizar_funcionarios(
        ordem_id: int,
        pedido_id: int,
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

        candidatos = [
            f for f in funcionarios_elegiveis if f.tipo_profissional in tipos_necessarios
        ]

        if not candidatos:
            logger.warning(f"⚠️ Nenhum funcionário compatível para {nome_atividade}")
            return False, []

        def chave_pedido(f: Funcionario):
            fip_json = fips_profissionais_permitidos.get(f.tipo_profissional.name, 0)
            engajado = f.ja_esta_no_pedido(pedido_id=pedido_id, ordem_id=ordem_id)
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
