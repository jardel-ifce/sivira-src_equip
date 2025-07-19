from datetime import datetime, timedelta
from typing import Optional, Tuple, List, TYPE_CHECKING
from models.equipamentos.divisora_de_massas import DivisoraDeMassas
if TYPE_CHECKING:
    from models.atividades.atividade_modular import AtividadeModular
from utils.logs.logger_factory import setup_logger
import unicodedata

logger = setup_logger('GestorDivisoras')


class GestorDivisorasBoleadoras:
    """
    🏭 Gestor especializado para controle de divisoras de massas com ou sem boleadora,
    utilizando backward scheduling com prioridade por FIP.
    """

    def __init__(self, divisoras: List[DivisoraDeMassas]):
        self.divisoras = divisoras

    # ==========================================================
    # 📊 Ordenação dos equipamentos por FIP (fator de importância)
    # ==========================================================
    def _ordenar_por_fip(self, atividade: "AtividadeModular") -> List[DivisoraDeMassas]:
        ordenadas = sorted(
            self.divisoras,
            key=lambda d: atividade.fips_equipamentos.get(d, 999)
        )
        # logger.info("📊 Ordem das divisoras por FIP (prioridade):")
        # for d in ordenadas:
        #     fip = atividade.fips_equipamentos.get(d, 999)
        #     logger.info(f"🔹 {d.nome} (FIP: {fip})")
        return ordenadas
    
    # ==========================================================
    # 🔍 Leitura dos parâmetros via JSON
    # ==========================================================  
    def _obter_capacidade_explicita_do_json(self, atividade: "AtividadeModular") -> Optional[float]:
        """
        🔍 Verifica se há um valor explícito de 'capacidade_gramas' no JSON da atividade
        para alguma chave que contenha 'divisora' no nome. Se houver, retorna esse valor.
        """
        try:
            config = atividade.configuracoes_equipamentos or {}
            for chave, conteudo in config.items():
                chave_normalizada = unicodedata.normalize("NFKD", chave).encode("ASCII", "ignore").decode("utf-8").lower()
                if "divisora" in chave_normalizada:
                    capacidade_gramas = conteudo.get("capacidade_gramas")
                    if capacidade_gramas is not None:
                        logger.info(
                            f"📦 JSON da atividade {atividade.id_atividade} define capacidade_gramas = {capacidade_gramas}g para o equipamento '{chave}'"
                        )
                        return capacidade_gramas
            logger.info(f"ℹ️ Nenhuma capacidade_gramas definida no JSON da atividade {atividade.id_atividade}.")
            return None
        except Exception as e:
            logger.error(f"❌ Erro ao buscar capacidade_gramas no JSON da atividade: {e}")
            return None
    

    def _obter_flag_boleadora(self, atividade: "AtividadeModular", divisora: DivisoraDeMassas) -> bool:
        try:
            nome_bruto = divisora.nome.lower().replace(" ", "_")
            nome_chave = unicodedata.normalize("NFKD", nome_bruto).encode("ASCII", "ignore").decode("utf-8")

            config = atividade.configuracoes_equipamentos.get(nome_chave)
            if config:
                return str(config.get("boleadora", "False")).lower() == "true"
        except Exception as e:
            logger.warning(f"⚠️ Erro ao obter flag boleadora para {divisora.nome}: {e}")
        return False
    
    # ==========================================================
    # 🎯 Alocação
    # ==========================================================
    def alocar(
        self,
        inicio: datetime,
        fim: datetime,
        atividade: "AtividadeModular",
        quantidade_gramas: float
    ) -> Tuple[bool, Optional[DivisoraDeMassas], Optional[datetime], Optional[datetime]]:

        duracao = atividade.duracao
        horario_final_tentativa = fim

        # logger.info(
        #     f"🎯 Tentando alocar atividade {atividade.id} (duração: {duracao}, quantidade: {quantidade_gramas}g) "
        #     f"entre {inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        # )

        divisoras_ordenadas = self._ordenar_por_fip(atividade)
        peso_json = self._obter_capacidade_explicita_do_json(atividade)
        if peso_json is not None:
            quantidade_final = peso_json
        else:
            quantidade_final = quantidade_gramas
            
        while horario_final_tentativa - duracao >= inicio:
            horario_inicio_tentativa = horario_final_tentativa - duracao

            for divisora in divisoras_ordenadas:
                if (
                    divisora.validar_capacidade(quantidade_final)
                    and divisora.esta_disponivel(horario_inicio_tentativa, horario_final_tentativa)
                ):
                    boleadora_flag = self._obter_flag_boleadora(atividade, divisora)

                    sucesso = divisora.ocupar(
                        ordem_id=atividade.ordem_id,
                        pedido_id=atividade.pedido_id,
                        atividade_id=atividade.id_atividade,
                        quantidade=quantidade_final,
                        inicio=horario_inicio_tentativa,
                        fim=horario_final_tentativa
                    )

                    if sucesso:
                        atividade.equipamento_alocado = divisora
                        atividade.equipamentos_selecionados = [divisora]
                        atividade.alocada = True
                        atividade.inicio_planejado = horario_inicio_tentativa
                        atividade.fim_planejado = horario_final_tentativa

                        logger.info(
                            f"✅ Atividade {atividade.id_atividade} alocada na {divisora.nome} | Quantidade {quantidade_final} "
                            f"de {horario_inicio_tentativa.strftime('%H:%M')} até {horario_final_tentativa.strftime('%H:%M')}"
                            f" com boleadora={boleadora_flag}."
                        )
                        return True, divisora, horario_inicio_tentativa, horario_final_tentativa

            horario_final_tentativa -= timedelta(minutes=1)

        logger.warning(
            f"❌ Atividade {atividade.id_atividade} não pôde ser alocada em nenhuma divisora dentro da janela entre "
            f"{inicio.strftime('%H:%M')} e {fim.strftime('%H:%M')}."
        )
        return False, None, None, None
    
    # ==========================================================
    # 🔓 Liberação
    # ==========================================================
    def liberar_por_atividade(self, atividade: "AtividadeModular") -> None:
        for divisora in self.divisoras:
            divisora.liberar_por_atividade(ordem_id=atividade.ordem_id, pedido_id=atividade.pedido_id, atividade_id=atividade.id_atividade)

    def liberar_por_pedido(self, atividade: "AtividadeModular") -> None:
        for divisora in self.divisoras:
            divisora.liberar_por_pedido(ordem_id=atividade.ordem_id, pedido_id=atividade.pedido_id)

    def liberar_por_ordem(self, atividade: "AtividadeModular") -> None:
        for divisora in self.divisoras:
            divisora.liberar_por_ordem(ordem_id=atividade.ordem_id)

    def liberar_ocupacoes_finalizadas(self, horario_atual: datetime) -> None:
        for divisora in self.divisoras:
            divisora.liberar_ocupacoes_finalizadas(horario_atual)

    # ==========================================================
    # 📅 Agenda
    # ==========================================================
    def mostrar_agenda(self):
        logger.info("==============================================")
        logger.info("📅 Agenda das Divisoras")
        logger.info("==============================================")
        for divisora in self.divisoras:
            divisora.mostrar_agenda()
