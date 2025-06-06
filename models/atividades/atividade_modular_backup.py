
import json
import os
from typing import Optional, Dict, Any
from datetime import timedelta, datetime
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_coccao import TipoCoccao
from enums.tipo_profissional import TipoProfissional
from services.mapa_gestor_equipamento import MAPA_GESTOR
from utils.logger_factory import setup_logger
from models.atividade_base import Atividade
from parser.leitor_json_subprodutos import buscar_dados_por_id_atividade
from factory import fabrica_equipamentos

logger = setup_logger('Atividade_Generica_Composta')


class AtividadeModular(Atividade):
    def __init__(self, id, id_atividade: int, quantidade_produto: int, *args, **kwargs):
        dados_gerais, dados_atividade = buscar_dados_por_id_atividade(id_atividade)
        nomes_equipamentos = dados_atividade.get("equipamentos_elegiveis", [])
        equipamentos_elegiveis = [getattr(fabrica_equipamentos, nome) for nome in nomes_equipamentos]

        super().__init__(
            id=id,
            id_atividade=id_atividade,
            tipos_profissionais_permitidos=[
                TipoProfissional[nome] for nome in dados_atividade.get("tipos_profissionais_permitidos", [])
            ],
            quantidade_funcionarios=dados_atividade.get("quantidade_funcionarios", 1),
            equipamentos_elegiveis=equipamentos_elegiveis,
            id_produto_gerado=dados_gerais["id_produto"],
            quantidade_produto=quantidade_produto
        )

        # Atributos diretos
        self.nome_produto = dados_gerais.get("nome_produto")
        self.fracoes_necessarias = dados_atividade.get("fracoes_necessarias")

        # Parâmetros técnicos opcionais
        self.faixa_temperatura_desejada_armazenamento = dados_atividade.get("faixa_temperatura_armazenamento")
        self.faixa_temperatura_desejada_coccao = dados_atividade.get("faixa_temperatura_desejada_coccao")
        self.vaporizacao_seg_desejada = dados_atividade.get("vaporizacao_seg_desejada")
        self.velocidade_mps_desejada = dados_atividade.get("velocidade_mps_desejada")
        self.tipo_coccao = dados_atividade.get("tipo_coccao")
        self.tipo_chama = dados_atividade.get("pressao_chama")
        self.pressao_chama = dados_atividade.get("pressao_chama")
        self.configuracoes_equipamentos = dados_atividade.get("configuracoes_equipamentos")

        # FIPs por equipamento
        self.fips_equipamentos = {
            getattr(fabrica_equipamentos, nome): fip
            for nome, fip in dados_atividade.get("fips_equipamentos", {}).items()
        }

        # Quantidade exigida por tipo de equipamento
        self._quantidade_por_tipo_equipamento = {
            TipoEquipamento[nome]: qtd
            for nome, qtd in dados_atividade.get("tipo_equipamento", {}).items()
        }

        # Cálculo de duração
        self.duracao = self._consultar_duracao_por_faixas(dados_atividade)

    def _consultar_duracao_por_faixas(self, dados_atividade: Dict[str, Any]) -> timedelta:
        faixas = dados_atividade.get("faixas", [])
        qtd = self.quantidade_produto

        for faixa in faixas:
            min_qtd = faixa.get("quantidade_min")
            max_qtd = faixa.get("quantidade_max")

            if min_qtd is None or max_qtd is None:
                raise ValueError(f"❌ Faixa de quantidade inválida ou incompleta: {faixa}")

            if min_qtd <= qtd <= max_qtd:
                h, m, s = map(int, faixa["duracao"].split(":"))
                return timedelta(hours=h, minutes=m, seconds=s)

        raise ValueError(f"❌ Nenhuma faixa compatível com a quantidade {qtd}g.")

    def _criar_gestores_por_tipo(self) -> dict[TipoEquipamento, object]:
        """
        🔧 Cria instâncias dos gestores adequados com base nos tipos de equipamento utilizados pela atividade.
        """
        gestores_por_tipo = {}

        for tipo_equipamento, _ in self._quantidade_por_tipo_equipamento.items():
            if tipo_equipamento not in MAPA_GESTOR:
                raise ValueError(f"❌ Gestor não definido para o tipo de equipamento: {tipo_equipamento.name}")

            gestor_cls = MAPA_GESTOR[tipo_equipamento]

            # Filtra os equipamentos da atividade que correspondem a este tipo
            equipamentos_filtrados = [
                equipamento for equipamento in self.equipamentos_elegiveis
                if equipamento.tipo_equipamento == tipo_equipamento
            ]

            if not equipamentos_filtrados:
                raise ValueError(f"⚠️ Nenhum equipamento do tipo {tipo_equipamento.name} associado à atividade.")

            gestores_por_tipo[tipo_equipamento] = gestor_cls(equipamentos_filtrados)

        return gestores_por_tipo

    def calcular_duracao(self):
        return super().calcular_duracao()

    def iniciar(self):
        return super().iniciar()

    def tentar_alocar_e_iniciar(
        self,
        inicio_jornada: datetime,
        fim_jornada: datetime
    ) -> bool:
        self.calcular_duracao()
        horario_final = fim_jornada

        while horario_final - self.duracao >= inicio_jornada:
            horario_inicio = horario_final - self.duracao

            sucesso = True
            equipamentos_alocados = []       # Lista com (sucesso, equipamento, ini, fim)
            ocupacoes_efetuadas = []         # Lista com (equipamento, ocupacao_id) para rollback

            for tipo_eqp, quantidade in self._quantidade_por_tipo_equipamento.items():
                equipamentos = [
                    eqp for eqp in self.equipamentos_elegiveis if eqp.tipo_equipamento == tipo_eqp
                ]

                if not equipamentos:
                    logger.warning(f"⚠️ Nenhum equipamento do tipo {tipo_eqp} disponível.")
                    sucesso = False
                    break

                classe_gestor = MAPA_GESTOR.get(tipo_eqp)
                if not classe_gestor:
                    logger.warning(f"⚠️ Nenhum gestor configurado para tipo {tipo_eqp}")
                    sucesso = False
                    break

                gestor = classe_gestor(equipamentos)
                metodo_alocacao = self._resolver_metodo_alocacao(tipo_eqp)

                try:
                    resultado = metodo_alocacao(
                        gestor=gestor,
                        inicio=horario_inicio,
                        fim=horario_final,
                    )

                    if not resultado[0]:
                        sucesso = False
                        break

                    # 🔹 Sucesso! Guardamos o equipamento e os dados de ocupação para registro e eventual rollback
                    equipamentos_alocados.append(resultado)
                    if hasattr(resultado[1], "ultimos_ids_ocupacao"):
                        for ocupacao_id in resultado[1].ultimos_ids_ocupacao:
                            ocupacoes_efetuadas.append((resultado[1], ocupacao_id))

                except Exception as e:
                    logger.error(f"❌ Erro ao alocar {tipo_eqp}: {e}")
                    sucesso = False
                    break

            if sucesso:
                self._registrar_sucesso(equipamentos_alocados, horario_inicio, horario_final)
                return True

            # ⏪ Rollback: desfaz todas as ocupações já feitas nesta tentativa
            for equipamento in [e[1] for e in equipamentos_alocados]:
                try:
                    if hasattr(equipamento, "liberar_por_atividade"):
                        equipamento.liberar_por_atividade(self.id)
                        logger.info(f"↩️ Rollback: desalocada atividade {self.id} em {equipamento.nome}")
                except Exception as e:
                    logger.warning(f"⚠️ Falha ao desalocar atividade {self.id} de {equipamento.nome}: {e}")


            # ⏪ Retrocede no tempo para nova tentativa
            horario_final -= timedelta(minutes=1)

        logger.warning(f"⚠️ Falha na alocação da atividade {self.id_atividade}")
        return False


    def _registrar_sucesso(self, equipamentos_alocados, inicio: datetime, fim: datetime):
        """
        ✅ Registra os equipamentos alocados e define horários reais da atividade.
        """
        self.equipamentos_selecionados = [dados[1] for dados in equipamentos_alocados]
        self.equipamento_alocado = self.equipamentos_selecionados
        self.inicio_real = inicio
        self.fim_real = fim
        self.alocada = True

        logger.info("✅ Atividade alocada com sucesso!")
        for sucesso, equipamento, i, f in equipamentos_alocados:
            if i and f:
                logger.info(f"🔧 {equipamento.nome} alocado de {i.strftime('%H:%M')} até {f.strftime('%H:%M')}")
            else:
                logger.info(f"🔧 {equipamento.nome} alocado (sem janela de tempo)")


    def _resolver_metodo_alocacao(self, tipo_equipamento):
        if tipo_equipamento == TipoEquipamento.REFRIGERACAO_CONGELAMENTO:
            return self._alocar_camara
        elif tipo_equipamento == TipoEquipamento.BANCADAS:
            return self._alocar_bancada
        elif tipo_equipamento == TipoEquipamento.FOGOES:
            return self._alocar_fogao
        elif tipo_equipamento == TipoEquipamento.BATEDEIRAS:
            return self._alocar_batedeira
        elif tipo_equipamento == TipoEquipamento.BALANCAS:
            return self._alocar_balanca
        elif tipo_equipamento == TipoEquipamento.FORNOS:
            return self._alocar_forno
        elif tipo_equipamento == TipoEquipamento.MISTURADORAS:
            return self._alocar_misturadora
        elif tipo_equipamento == TipoEquipamento.MISTURADORAS_COM_COCCAO:
            return self._alocar_misturadora_com_coccao
        elif tipo_equipamento == TipoEquipamento.ARMARIOS_PARA_FERMENTACAO:
            return self._alocar_armario_fermentacao
        else:
            raise ValueError(f"❌ Nenhum método de alocação definido para {tipo_equipamento}")


    def _alocar_camara(self, gestor, inicio, fim, **kwargs):
        return gestor.alocar(inicio, fim, self, self.quantidade_produto)

    def _alocar_bancada(self, gestor, inicio, fim, **kwargs):
        return gestor.alocar(inicio, fim, self)

    def _alocar_fogao(self, gestor, inicio, fim, **kwargs):
        return gestor.alocar(inicio, fim, self, self.quantidade_produto)

    def _alocar_batedeira(self, gestor, inicio, fim, **kwargs):
        return gestor.alocar(inicio, fim, self, self.quantidade_produto)

    def _alocar_balanca(self, gestor, inicio, fim, **kwargs):
        return gestor.alocar(inicio, fim, self, self.quantidade_produto)

    def _alocar_forno(self, gestor, inicio, fim, temperatura=180, vapor=False, velocidade=None, **kwargs):
        return gestor.alocar(inicio, fim, self, temperatura, vapor, velocidade)

    def _alocar_misturadora(self, gestor, inicio, fim, **kwargs):
        return gestor.alocar(inicio, fim, self, self.quantidade_produto)

    def _alocar_misturadora_com_coccao(self, gestor, inicio, fim, chama=None, pressao=None, velocidade=None, **kwargs):
        return gestor.alocar(inicio, fim, self, chama, pressao, velocidade)

    def _alocar_armario_fermentacao(self, gestor, inicio, fim, **kwargs):
        return gestor.alocar(inicio, fim, self)

    
    # ==========================================================
    # 📅 Exibe a agenda dos gestores associados à atividade
    # ==========================================================
    def mostrar_agendas_dos_gestores(self):
        """
        📅 Mostra a agenda de todos os gestores utilizados na atividade.
        """
        try:
            gestores = self._criar_gestores_por_tipo()
        except Exception as e:
            logger.warning(f"⚠️ Não foi possível criar os gestores para mostrar agenda: {e}")
            return
        for tipo, gestor in gestores.items():
            if hasattr(gestor, "mostrar_agenda"):
                gestor.mostrar_agenda()
            else:
                logger.warning(f"⚠️ Gestor de {tipo.name} não possui método 'mostrar_agenda'.")
