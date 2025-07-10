import os
from datetime import datetime, timedelta
from enums.equipamentos.tipo_equipamento import TipoEquipamento
from enums.producao.tipo_item import TipoItem
from enums.funcionarios.tipo_profissional import TipoProfissional
from factory import fabrica_equipamentos
from models.funcionarios.funcionario import Funcionario
from parser.carregador_json_atividades import buscar_dados_por_id_atividade
from services.gestor_funcionarios.gestor_funcionarios import GestorFuncionarios
from services.mapas.mapa_gestor_equipamento import MAPA_GESTOR
from services.rollback.rollback import rollback_equipamentos, rollback_funcionarios
from typing import List, Tuple, Optional
from utils.producao.calculadora_duracao import consultar_duracao_por_faixas
from utils.time.conversores_temporais import converter_para_timedelta
from utils.logs.logger_factory import setup_logger
from utils.commons.normalizador_de_nomes import normalizar_nome
from utils.logs.gerenciador_logs import registrar_log_equipamentos, registrar_log_funcionarios, remover_log_funcionarios, remover_log_equipamentos
import itertools
import traceback

logger = setup_logger('Atividade_Modular')

TIPOS_SEM_QUANTIDADE = {TipoEquipamento.BANCADAS}

class AtividadeModular:
    def __init__(self, id, id_atividade: int, tipo_item: TipoItem, quantidade_produto: int, *args, **kwargs):
        # 🆔 Identificadores principais
        self.id = id
        self.id_atividade = id_atividade
        self.pedido_id = kwargs.get("pedido_id")
        self.ordem_id = kwargs.get("ordem_id")
        self.id_produto_gerado = kwargs.get("id_produto")
        self.tipo_item = tipo_item
        self.quantidade_produto = quantidade_produto
        self.alocada = False

        # 📄 Carregamento dos dados da atividade (direto ou via parser)
        dados_atividade = kwargs.get("dados")
        if not dados_atividade:
            dados_gerais, dados_atividade = buscar_dados_por_id_atividade(id_atividade, tipo_item)
            self.nome_atividade = dados_gerais.get("nome_atividade", f"Atividade {id_atividade}")
            self.nome_item = dados_gerais.get("nome_item", "item_desconhecido")
        else:
            self.nome_atividade = f"Atividade {id_atividade}"
            self.nome_item = "item_desconhecido"

        self.dados_atividade = dados_atividade  # manter para uso em outros métodos

        # 👥 Profissionais
        self.tipos_necessarios = {
            TipoProfissional[nome] for nome in dados_atividade.get("tipos_profissionais_permitidos", [])
        }
        self.funcionarios_elegiveis = kwargs.get("funcionarios_elegiveis", [])
        self.funcionarios_necessarios: List[Funcionario] = [
            f for f in self.funcionarios_elegiveis if f.tipo_profissional in self.tipos_necessarios
        ]
        self.qtd_profissionais_requeridos: int = int(dados_atividade.get("quantidade_funcionarios", 0))
        self.fips_profissionais_permitidos: dict[str, int] = dados_atividade.get("fips_profissionais_permitidos", {})
        self.funcionarios_alocados: List[Funcionario] = []

        # for f in self.funcionarios_necessarios:
        #     print(f"✔️ {f.nome} - {f.tipo_profissional.name}")

        # ⏳ Tempo de espera entre atividades
        self.tempo_maximo_de_espera = converter_para_timedelta(
            dados_atividade.get("tempo_maximo_de_espera")
        )

        # 🛠️ Equipamentos
        nomes_equipamentos = dados_atividade.get("equipamentos_elegiveis", [])
        self.equipamentos_elegiveis = [
            getattr(fabrica_equipamentos, nome) for nome in nomes_equipamentos
        ]
        self.equipamentos_selecionados: List = []

        self.fips_equipamentos = {
            getattr(fabrica_equipamentos, nome): fip
            for nome, fip in dados_atividade.get("fips_equipamentos", {}).items()
        }

        self._quantidade_por_tipo_equipamento = {
            TipoEquipamento[nome]: qtd
            for nome, qtd in dados_atividade.get("tipo_equipamento", {}).items()
        }

        self.configuracoes_equipamentos = dados_atividade.get("configuracoes_equipamentos", {})

        # ⏳ Tempo da atividade
        self.duracao: timedelta = consultar_duracao_por_faixas(dados_atividade, self.quantidade_produto)



    def _criar_gestores_por_tipo(self) -> dict[TipoEquipamento, object]:
        gestores_por_tipo = {}

        for tipo_equipamento, _ in self._quantidade_por_tipo_equipamento.items():
            if tipo_equipamento not in MAPA_GESTOR:
                raise ValueError(f"❌ Gestor não definido para o tipo de equipamento: {tipo_equipamento.name}")

            gestor_cls = MAPA_GESTOR[tipo_equipamento]

            equipamentos_filtrados = [
                equipamento for equipamento in self.equipamentos_elegiveis
                if equipamento.tipo_equipamento == tipo_equipamento
            ]

            if not equipamentos_filtrados:
                raise ValueError(f"⚠️ Nenhum equipamento do tipo {tipo_equipamento.name} associado à atividade.")

            gestores_por_tipo[tipo_equipamento] = gestor_cls(equipamentos_filtrados)

        return gestores_por_tipo

    
    def _registrar_sucesso_equipamentos(self, equipamentos_alocados, inicio: datetime, fim: datetime, **kwargs):
        self.equipamentos_selecionados = [dados[1] for dados in equipamentos_alocados]
        print(f"🛠️ Equipamentos alocados: {[eqp.nome for eqp in self.equipamentos_selecionados]}")
        self.equipamento_alocado = self.equipamentos_selecionados
        self.inicio_real = inicio
        self.fim_real = fim
        self.alocada = True

        # DEBUG: verificar dados antes do log
        # logger.warning(f"📋 Registrando log de equipamentos: ordem={self.ordem_id}, pedido={self.pedido_id}, atividade={self.id_atividade}")
        # for i, (ocupacao_id, equipamento, inicio_eqp, fim_eqp) in enumerate(equipamentos_alocados):
        #     logger.warning(
        #         f"🔧 [{i}] Equipamento: {equipamento.nome}, Início: {inicio_eqp}, Fim: {fim_eqp}, Ocupação ID: {ocupacao_id}"
        #     )

        # Registro no log
        registrar_log_equipamentos(
            ordem_id=self.ordem_id,
            pedido_id=self.pedido_id,
            id_atividade=self.id_atividade,
            nome_item=self.nome_item,
            nome_atividade=self.nome_atividade,
            equipamentos_alocados=equipamentos_alocados
        )

        inicios = [inicio_eqp for _, _, inicio_eqp, _ in equipamentos_alocados if inicio_eqp]
        fins = [fim_eqp for _, _, _, fim_eqp in equipamentos_alocados if fim_eqp]

        min_inicio = min(inicios)
        max_fim = max(fins)

        return min_inicio, max_fim


    def _resolver_metodo_alocacao(self, tipo_equipamento):
        def metodo_generico(gestor, inicio, fim, **kwargs):
            try:
                if tipo_equipamento in TIPOS_SEM_QUANTIDADE:
                    return gestor.alocar(inicio, fim, self)
                return gestor.alocar(inicio, fim, self, self.quantidade_produto)
            except TypeError as e:
                raise RuntimeError(f"🚨 Erro de chamada em gestor {gestor.__class__.__name__} para {tipo_equipamento.name}: {e}")


        if tipo_equipamento not in [
            TipoEquipamento.REFRIGERACAO_CONGELAMENTO,
            TipoEquipamento.BANCADAS,
            TipoEquipamento.FOGOES,
            TipoEquipamento.BATEDEIRAS,
            TipoEquipamento.BALANCAS,
            TipoEquipamento.FORNOS,
            TipoEquipamento.MISTURADORAS,
            TipoEquipamento.MISTURADORAS_COM_COCCAO,
            TipoEquipamento.ARMARIOS_PARA_FERMENTACAO,
            TipoEquipamento.MODELADORAS,
            TipoEquipamento.DIVISORAS_BOLEADORAS,
        ]:
            raise ValueError(f"❌ Nenhum método de alocação definido para {tipo_equipamento}")

        return metodo_generico

    def mostrar_agendas_dos_gestores(self):
        try:
            gestores = self._criar_gestores_por_tipo()
        except Exception as e:
            # logger.warning(f"⚠️ Não foi possível criar os gestores para mostrar agenda: {e}")
            return
        for tipo, gestor in gestores.items():
            if hasattr(gestor, "mostrar_agenda"):
                gestor.mostrar_agenda()
            # else:
            #     logger.warning(f"⚠️ Gestor de {tipo.name} não possui método 'mostrar_agenda'.")



    def tentar_alocar_e_iniciar_equipamentos(
        self,
        inicio_jornada: datetime,
        fim_jornada: datetime
    ) -> Tuple[bool, Optional[datetime], Optional[datetime], Optional[timedelta], List[Tuple]]:
        horario_final = fim_jornada
        equipamentos_alocados = []

        while horario_final - self.duracao >= inicio_jornada:
            sucesso = True
            equipamentos_alocados = []
            horario_fim_etapa = horario_final

            for tipo_eqp, _ in reversed(list(self._quantidade_por_tipo_equipamento.items())):
                equipamentos = [eqp for eqp in self.equipamentos_elegiveis if eqp.tipo_equipamento == tipo_eqp]

                if not equipamentos:
                    logger.warning(f"⚠️ Nenhum equipamento disponível do tipo {tipo_eqp}.")
                    sucesso = False
                    break

                classe_gestor = MAPA_GESTOR.get(tipo_eqp)
                if not classe_gestor:
                    logger.warning(f"⚠️ Nenhum gestor configurado para tipo {tipo_eqp}.")
                    sucesso = False
                    break

                gestor = classe_gestor(equipamentos)
                metodo_alocacao = self._resolver_metodo_alocacao(tipo_eqp)

                equipamento_exemplo = equipamentos[0]
                nome_normalizado = normalizar_nome(equipamento_exemplo.nome)
                config = self.configuracoes_equipamentos.get(nome_normalizado, {})

                try:
                    inicio_previsto = horario_fim_etapa - self.duracao
                    resultado = metodo_alocacao(
                        gestor=gestor,
                        inicio=inicio_previsto,
                        fim=horario_fim_etapa,
                        **config
                    )
                    print(f"🔍 [DEBUG] Resultado retornado por gestor.alocar: {resultado} | Tipo: {type(resultado)} | Len: {len(resultado) if hasattr(resultado, '__len__') else '??'}")

                    if not resultado[0] or resultado[1] is None:
                        sucesso = False
                        break

                    equipamentos_alocados.append(resultado)
                    horario_fim_etapa = resultado[2]

                except Exception as e:
                    
                    logger.error(f"❌ Erro ao alocar {tipo_eqp}: {e}")
                    traceback.print_exc()
                    
                    sucesso = False
                    break
                 # Se possível, imprima o resultado bruto antes do unpack
                try:
                    continue
                    # logger.debug(f"📦 Resultado bruto retornado por gestor.alocar({tipo_eqp}): {resultado}")
                    # print(f"📦 Resultado bruto retornado por gestor.alocar({tipo_eqp}): {resultado} | Tipo: {type(resultado)} | Len: {len(resultado) if hasattr(resultado, '__len__') else 'n/a'}")
                except Exception as inner:
                    logger.warning(f"⚠️ Não foi possível imprimir resultado retornado: {inner}")

            if sucesso:
                equipamentos_ordenados = sorted(equipamentos_alocados, key=lambda x: x[2])
                for i in range(1, len(equipamentos_ordenados)):
                    fim_anterior = equipamentos_ordenados[i - 1][3]
                    inicio_atual = equipamentos_ordenados[i][2]

                    if fim_anterior != inicio_atual:
                        logger.warning(
                            f"🔁 Equipamentos da atividade {self.id_atividade} não estão sequenciados corretamente. "
                            f"'{equipamentos_ordenados[i - 1][1].nome}' terminou às {fim_anterior.strftime('%H:%M:%S')} "
                            f"e '{equipamentos_ordenados[i][1].nome}' iniciou às {inicio_atual.strftime('%H:%M:%S')}."
                        )
                        sucesso = False
                        break

            if sucesso:
                inicio_atividade = equipamentos_ordenados[0][2]
                fim_atividade = equipamentos_ordenados[-1][3]
                self.inicio_real = inicio_atividade
                self.fim_real = fim_atividade
                self._registrar_sucesso_equipamentos(
                    equipamentos_alocados,
                     inicio_atividade, fim_atividade
                )

                flag, funcionarios_alocados = GestorFuncionarios.priorizar_funcionarios(
                    ordem_id=self.ordem_id,
                    pedido_id=self.pedido_id,
                    inicio=inicio_atividade,
                    fim=fim_atividade,
                    qtd_profissionais_requeridos=self.qtd_profissionais_requeridos,
                    tipos_necessarios=self.tipos_necessarios,
                    fips_profissionais_permitidos=self.fips_profissionais_permitidos,
                    funcionarios_elegiveis=self.funcionarios_elegiveis,
                    nome_atividade=self.nome_atividade
                )

                if flag:
                    for funcionario in funcionarios_alocados:
                        funcionario.registrar_ocupacao(
                            ordem_id=self.ordem_id,
                            pedido_id=self.pedido_id,
                            id_atividade_json=self.id_atividade,
                            inicio=inicio_atividade,
                            fim=fim_atividade
                        )
                    registrar_log_funcionarios(
                        ordem_id=self.ordem_id,
                        pedido_id=self.pedido_id,
                        id_atividade=self.id_atividade,
                        nome_item=self.nome_item,
                        nome_atividade=self.nome_atividade,
                        funcionarios_alocados=funcionarios_alocados,
                        inicio=inicio_atividade,
                        fim=fim_atividade
                    )
                else:
                    # bloco em testes, talvez não seja necessárioo rollback, vou deixar para a classe PedidoDeProducao
                    #rollback_equipamentos(equipamentos_alocados, self.ordem_id, self.pedido_id)
                    #rollback_funcionarios(self.funcionarios_elegiveis, self.ordem_id, self.pedido_id)
                    raise RuntimeError(
                        f"❌ Não foi possível alocar os funcionários necessários para a atividade {self.id_atividade}."
                    )
                   
                    

                return True, inicio_atividade, fim_atividade, self.tempo_maximo_de_espera, equipamentos_alocados
            else:
                rollback_equipamentos(equipamentos_alocados, self.ordem_id, self.pedido_id, self.id_atividade)
                #rollback_funcionarios(self.funcionarios_elegiveis, self.ordem_id, self.pedido_id, self.id_atividade)
               # remover_log_funcionarios(self.ordem_id, self.pedido_id, self.id_atividade)
                remover_log_equipamentos(self.ordem_id, self.pedido_id)
            horario_final -= timedelta(minutes=300)

        logger.error(f"🛑 Limite da jornada atingido. Impossível alocar a atividade {self.id_atividade}.")
        return False, None, None, self.tempo_maximo_de_espera, equipamentos_alocados