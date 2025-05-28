from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from models.equips.forno import Forno
from utils.conversores_ocupacao import gramas_para_niveis_tela
from utils.logger_factory import setup_logger


# 🔥 Logger específico para o gestor de fornos
logger = setup_logger('GestorFornos')


class GestorFornos:
    """
    🔥 Gestor especializado no controle de fornos.
    Utiliza backward scheduling, levando em conta:
    - Ocupação por níveis de tela
    - Controle de temperatura
    - Controle de vaporização (se aplicável)
    - Controle de velocidade (se aplicável)
    """

    def __init__(self, fornos: List[Forno]):
        self.fornos = fornos

    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade,
        temperatura_desejada: int,
        vaporizacao_desejada: Optional[int] = None,
        velocidade_desejada: Optional[int] = None,
        atividade_exige_vaporizacao: bool = False,
        atividade_exige_velocidade: bool = False,
    ) -> Tuple[bool, Optional[Forno], Optional[datetime], Optional[datetime]]:
        """
        🔥 Faz a alocação backward:
        Busca o horário mais tardio possível dentro da janela,
        respeitando ocupação e parâmetros operacionais.

        Retorna:
        (Sucesso, forno, inicio_real, fim_real)
        """

        duracao = atividade.duracao
        quantidade_gramas = atividade.quantidade_produto
        ocupacao_id = atividade.id

        # 🔢 Converte quantidade de produto em quantidade de níveis de tela
        quantidade_niveis = gramas_para_niveis_tela(quantidade_gramas)

        # 🔥 Ordenar fornos pela prioridade (FIP) definida na atividade
        equipamentos_ordenados = sorted(
            self.fornos,
            key=lambda f: atividade.fips_equipamentos.get(f, 999)
        )

        horario_final_tentativa = fim

        while horario_final_tentativa - duracao >= inicio:
            horario_inicial_tentativa = horario_final_tentativa - duracao

            for forno in equipamentos_ordenados:
                # ✔️ Verifica espaço
                tem_espaco = forno.verificar_espaco_niveis(
                    quantidade=quantidade_niveis,
                    inicio=horario_inicial_tentativa,
                    fim=horario_final_tentativa
                )

                # ✔️ Verifica temperatura
                temp_ok = forno.verificar_compatibilidade_temperatura(
                    inicio=horario_inicial_tentativa,
                    fim=horario_final_tentativa,
                    temperatura=temperatura_desejada
                )

                # ✔️ Verifica vaporização
                vap_ok = forno.verificar_compatibilidade_vaporizacao(
                    inicio=horario_inicial_tentativa,
                    fim=horario_final_tentativa,
                    vaporizacao=vaporizacao_desejada
                )

                # ✔️ Verifica velocidade
                vel_ok = forno.verificar_compatibilidade_velocidade(
                    inicio=horario_inicial_tentativa,
                    fim=horario_final_tentativa,
                    velocidade=velocidade_desejada
                )

                if all([tem_espaco, temp_ok, vap_ok, vel_ok]):
                    # ✔️ Configura parâmetros operacionais
                    forno.selecionar_temperatura(temperatura_desejada)
                    forno.selecionar_vaporizacao(vaporizacao_desejada, atividade_exige_vaporizacao)
                    forno.selecionar_velocidade(velocidade_desejada, atividade_exige_velocidade)

                    # ✔️ Ocupa os níveis
                    forno.ocupar_niveis(
                        ocupacao_id=ocupacao_id,
                        quantidade=quantidade_niveis,
                        inicio=horario_inicial_tentativa,
                        fim=horario_final_tentativa,
                        atividade_id=atividade.id
                    )

                    logger.info(
                        f"✅ Forno {forno.nome} alocado para Atividade {atividade.id} "
                        f"de {horario_inicial_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')} | "
                        f"Temp: {temperatura_desejada}°C | "
                        f"Vapor: {vaporizacao_desejada if vaporizacao_desejada is not None else 'N/A'} | "
                        f"Velocidade: {velocidade_desejada if velocidade_desejada is not None else 'N/A'}"
                    )

                    return True, forno, horario_inicial_tentativa, horario_final_tentativa

            # 🔄 Tenta o bloco anterior
            horario_final_tentativa -= timedelta(minutes=5)

        logger.warning(
            f"❌ Nenhum forno disponível para alocar a atividade {atividade.id} "
            f"dentro da janela {inicio.strftime('%H:%M')} - {fim.strftime('%H:%M')}."
        )
        return False, None, None, None

    # ==========================================================
    # 🔓 Liberações
    # ==========================================================
    def liberar_por_atividade(self, atividade_id: int):
        for forno in self.fornos:
            forno.liberar_por_atividade(atividade_id)

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime):
        for forno in self.fornos:
            forno.liberar_ocupacoes_finalizadas(horario_atual)

    def liberar_todas_ocupacoes(self):
        for forno in self.fornos:
            forno.liberar_todas_ocupacoes()

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("\n==============================")
        logger.info("📅 Agenda dos Fornos")
        logger.info("==============================")
        for forno in self.fornos:
            forno.mostrar_agenda()
