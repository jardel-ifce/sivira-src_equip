import os
from enums.tipo_equipamento import TipoEquipamento
from enums.tipo_item import TipoItem
from enums.tipo_profissional import TipoProfissional
from typing import List, Optional
from services.mapa_gestor_equipamento import MAPA_GESTOR
from services.gestor_funcionarios.gestor_funcionarios import GestorFuncionarios
from utils.logger_factory import setup_logger
from utils.conversores_temporais import converter_para_timedelta
from utils.normalizador_de_nomes import normalizar_nome
from models.atividade_base import Atividade
from models.funcionarios.funcionario import Funcionario
from parser.carregador_json_atividades import buscar_dados_por_id_atividade
from factory import fabrica_equipamentos
from datetime import datetime, timedelta

logger = setup_logger('Atividade_Modular')


class AtividadeModular(Atividade):
    def __init__(self, id, id_atividade: int, tipo_item: TipoItem, quantidade_produto: int, *args, **kwargs):
        self.ordem_id = kwargs.get("ordem_id")
        id_produto_gerado = kwargs.get("id_produto")
        self.log_path = f"logs/funcionarios_{self.ordem_id}.log"

        dados_atividade = kwargs.get("dados")
        if not dados_atividade:
            dados_gerais, dados_atividade = buscar_dados_por_id_atividade(id_atividade, tipo_item)
            self.nome_atividade = dados_gerais.get("nome_atividade", f"Atividade {id_atividade}")
            self.nome_item = dados_gerais.get("nome_item", "item_desconhecido")
        else:
            self.nome_atividade = f"Atividade {id_atividade}"
            self.nome_item = "item_desconhecido"
        
        self.tipos_necessarios = set(
            TipoProfissional[nome] for nome in dados_atividade.get("tipos_profissionais_permitidos",[])
        )
        # ================================================
        # Lógica dos funcionários
        # ================================================
        self.funcionarios_elegiveis = kwargs.get("funcionarios_elegiveis", [])
        self.funcionarios_necessarios: List[Funcionario] = []
        self.qtd_profissionais_requeridos: int = int(dados_atividade.get("quantidade_funcionarios", 0))

        # Seleciona somente os necessários para a atividade
        self.funcionarios_necessarios = [
            f for f in self.funcionarios_elegiveis if f.tipo_profissional in self.tipos_necessarios
        ]
        for f in self.funcionarios_necessarios:
            print(f"✔️ {f.nome} - {f.tipo_profissional.name}")
        
        # Obtém fips dos profissionais permitidos
        self.fips_profissionais_permitidos: dict[str, int] = dados_atividade.get(
            "fips_profissionais_permitidos", {}
        )

        # Quantidade de profissionais requeridos para a atividade
        self.qtd_profissionais_requeridos: int = int(dados_atividade.get("quantidade_funcionarios", 0))


        self.tempo_maximo_de_espera = converter_para_timedelta(dados_atividade.get("tempo_maximo_de_espera"))

        nomes_equipamentos = dados_atividade.get("equipamentos_elegiveis", [])
        equipamentos_elegiveis = [getattr(fabrica_equipamentos, nome) for nome in nomes_equipamentos]
        self.tipo_item = tipo_item

        super().__init__(
            id=id,
            id_atividade=id_atividade,
            tipos_profissionais_permitidos=[],
            quantidade_funcionarios=0,
            equipamentos_elegiveis=equipamentos_elegiveis,
            id_produto_gerado=id_produto_gerado,
            quantidade_produto=quantidade_produto
        )

        self.fips_equipamentos = {
            getattr(fabrica_equipamentos, nome): fip
            for nome, fip in dados_atividade.get("fips_equipamentos", {}).items()
        }

        self.configuracoes_equipamentos = dados_atividade.get("configuracoes_equipamentos", {})

        self._quantidade_por_tipo_equipamento = {
            TipoEquipamento[nome]: qtd
            for nome, qtd in dados_atividade.get("tipo_equipamento", {}).items()
        }

        self.duracao = self._consultar_duracao_por_faixas(dados_atividade)

    def calcular_duracao(self):
        return super().calcular_duracao()

    def _consultar_duracao_por_faixas(self, dados_atividade) -> timedelta:
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

    def tentar_alocar_e_iniciar(self, inicio_jornada: datetime, fim_jornada: datetime) -> bool:
        horario_final = fim_jornada
        atividades_nao_alocadas = []  # Lista para registrar as atividades não alocadas

        while horario_final - self.duracao >= inicio_jornada:
            sucesso = True
            equipamentos_alocados = []  # Lista para registrar os equipamentos alocados com sucesso
            funcionarios_alocados = []  # Lista para registrar os funcionários alocados com sucesso
            ocupacoes_efetuadas = []  # Lista para registrar as ocupações
            horario_fim_etapa = horario_final

            for tipo_eqp, _ in reversed(list(self._quantidade_por_tipo_equipamento.items())):
                equipamentos = [eqp for eqp in self.equipamentos_elegiveis if eqp.tipo_equipamento == tipo_eqp]

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

                equipamento_exemplo = equipamentos[0]
                nome_normalizado = normalizar_nome(equipamento_exemplo.nome)
                config = self.configuracoes_equipamentos.get(nome_normalizado, {})

                # 🔧 Cálculo seguro de horário de início
                inicio_previsto = horario_fim_etapa - self.duracao

                try:
                    resultado = metodo_alocacao(
                        gestor=gestor,
                        inicio=inicio_previsto,
                        fim=horario_fim_etapa,
                        **config
                    )

                    if not resultado[0]:
                        sucesso = False
                        break

                    equipamentos_alocados.append(resultado)
                    horario_fim_etapa = resultado[2]  # Atualiza o horário de fim da etapa

                except Exception as e:
                    logger.error(f"❌ Erro ao alocar {tipo_eqp}: {e}")
                    sucesso = False
                    break

            if sucesso:
                inicio_atividade, fim_atividade = self._registrar_sucesso_equipamentos(equipamentos_alocados, horario_fim_etapa, horario_final)

                # Obtemos a alocação de funcionários
                flag, selecionados_funcionarios = GestorFuncionarios.priorizar_funcionarios(
                    ordem_id=self.ordem_id,
                    nome_atividade=self.nome_atividade,
                    inicio=inicio_atividade,
                    fim=fim_atividade,
                    qtd_profissionais_requeridos=self.qtd_profissionais_requeridos,
                    tipos_necessarios=self.tipos_necessarios,
                    fips_profissionais_permitidos=self.fips_profissionais_permitidos,
                    funcionarios_elegiveis=self.funcionarios_elegiveis
                )

                #flag, selecionados_funcionarios = self._priorizar_funcionarios(inicio_atividade, fim_atividade)
                if flag is False:
                    logger.warning(f"⚠️ Não foi possível alocar funcionários para a atividade {self.id_atividade}.")
                    # Rollback caso falha na alocação de qualquer equipamento
                    for equipamento in [e[1] for e in equipamentos_alocados]:
                        try:
                            if hasattr(equipamento, "liberar_por_atividade"):
                                equipamento.liberar_por_atividade(self.id_atividade, self.ordem_id)
                                logger.info(f"↩️ Rollback: desalocada atividade {self.id} em {equipamento.nome}")
                        except Exception as e:
                            logger.warning(f"⚠️ Falha ao desalocar atividade {self.id} de {equipamento.nome}: {e}")

                    # Rollback dos funcionários
                    for funcionario in self.funcionarios_elegiveis:
                        try:
                            if hasattr(funcionario, "liberar_por_atividade"):
                                funcionario.liberar_por_ordem(self.ordem_id)
                                logger.info(f"↩️ Rollback: funcionário {funcionario.nome} liberado da ordem {self.ordem_id}")
                        except Exception as e:
                            logger.warning(f"⚠️ Falha ao liberar funcionário {funcionario.nome} da ordem {self.ordem_id}: {e}")
                        try:
                            if os.path.exists(self.log_path):
                                os.remove(self.log_path)
                                logger.info(f"🗑️ Arquivo de log removido: {self.log_path}")
                        except Exception as e:
                            logger.warning(f"⚠️ Falha ao remover log da ordem: {e}")

                    raise ValueError(
                        f"❌ Não foi possível alocar funcionários para a atividade {self.id_atividade}. "
                        f"Verifique os requisitos de profissionais e disponibilidade."
                    )
                
                else:
                    for funcionario in selecionados_funcionarios:
                        funcionario.registrar_ocupacao(
                            ordem_id=self.ordem_id,
                            id_atividade_modular=self.id,
                            id_atividade_json=self.id_atividade,
                            inicio=inicio_atividade,
                            fim=fim_atividade
                        )
                        funcionarios_alocados.append(funcionario)  # Para controle de rollback
                    self._registrar_sucesso_funcionarios(funcionarios_alocados, inicio_atividade, fim_atividade)

                    return True, inicio_atividade, fim_atividade, self.tempo_maximo_de_espera

            # Rollback caso falha na alocação de qualquer equipamento
            for equipamento in [e[1] for e in equipamentos_alocados]:
                try:
                    if hasattr(equipamento, "liberar_por_atividade"):
                        equipamento.liberar_por_atividade(self.id, self.ordem_id)
                        logger.info(f"↩️ Rollback: desalocada atividade {self.id} em {equipamento.nome}")
                except Exception as e:
                    logger.warning(f"⚠️ Falha ao desalocar atividade {self.id} de {equipamento.nome}: {e}")

            horario_final -= timedelta(minutes=1)

        logger.error(f"❌ Não foi possível alocar a atividade {self.id_atividade} dentro da jornada.")
        raise ValueError(
            f"❌ Não foi possível alocar a atividade {self.id_atividade} dentro do intervalo de jornada "
            f"de {inicio_jornada.strftime('%H:%M')} até {fim_jornada.strftime('%H:%M')}. "
            f"Tente ajustar os horários ou a duração da atividade."
        )


    def _registrar_sucesso_funcionarios(self, funcionarios_alocados: List[Funcionario], inicio: datetime, fim: datetime):
        self.inicio_real = inicio
        self.fim_real = fim
        self.alocada = True

        logger.info("✅ Atividade alocada com sucesso!")
        for funcionario in funcionarios_alocados:
            logger.info(f"👨‍🍳 {funcionario.nome} alocado de {inicio.strftime('%H:%M')} até {fim.strftime('%H:%M')}")

        if self.ordem_id:
            os.makedirs("logs", exist_ok=True)
            caminho = f"logs/funcionarios_{self.ordem_id}.log"
            with open(caminho, "a", encoding="utf-8") as arq:
                for funcionario in funcionarios_alocados:
                    linha = (
                        f"{self.ordem_id} | "
                        f"{self.id_atividade} | {self.nome_item} | {self.nome_atividade} | "
                        f"{funcionario.nome} | {inicio.strftime('%H:%M')} | {fim.strftime('%H:%M')} \n"
                    )
                    arq.write(linha)

    def _registrar_sucesso_equipamentos(self, equipamentos_alocados, inicio: datetime, fim: datetime, **kwargs):
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

        if self.ordem_id:
            os.makedirs("logs", exist_ok=True)
            caminho = f"logs/ordem_{self.ordem_id}.log"
            with open(caminho, "a", encoding="utf-8") as arq:
                for _, equipamento, inicio, fim in equipamentos_alocados:
                    linha = (
                        f"{self.ordem_id} | "
                        f"{self.id_atividade} | {self.nome_item} | {self.nome_atividade} | "
                        f"{equipamento.nome} | {inicio.strftime('%H:%M')} | {fim.strftime('%H:%M')} \n"
                    )
                    arq.write(linha)
        inicios = [i for _, _, i, _ in equipamentos_alocados if i]
        fins = [f for _, _, _, f in equipamentos_alocados if f]
        
        # ✅ Retorna os extremos para alocação de funcionário
        return min(inicios), max(fins)

    def _resolver_metodo_alocacao(self, tipo_equipamento):
        return {
            TipoEquipamento.REFRIGERACAO_CONGELAMENTO: self._alocar_camara,
            TipoEquipamento.BANCADAS: self._alocar_bancada,
            TipoEquipamento.FOGOES: self._alocar_fogao,
            TipoEquipamento.BATEDEIRAS: self._alocar_batedeira,
            TipoEquipamento.BALANCAS: self._alocar_balanca,
            TipoEquipamento.FORNOS: self._alocar_forno,
            TipoEquipamento.MISTURADORAS: self._alocar_misturadora,
            TipoEquipamento.MISTURADORAS_COM_COCCAO: self._alocar_misturadora_com_coccao,
            TipoEquipamento.ARMARIOS_PARA_FERMENTACAO: self._alocar_armario_fermentacao,
            TipoEquipamento.MODELADORAS: self._alocar_modeladora,
            TipoEquipamento.DIVISORAS_BOLEADORAS: self._alocar_divisora_boleadora,
        }.get(tipo_equipamento, lambda *args, **kwargs: (_ for _ in ()).throw(
            ValueError(f"❌ Nenhum método de alocação definido para {tipo_equipamento}")
        ))

    def _alocar_camara(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_bancada(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self)
    def _alocar_fogao(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_batedeira(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_balanca(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_forno(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_misturadora(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_misturadora_com_coccao(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_armario_fermentacao(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_modeladora(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)
    def _alocar_divisora_boleadora(self, gestor, inicio, fim, **kwargs): return gestor.alocar(inicio, fim, self, self.quantidade_produto)

    def mostrar_agendas_dos_gestores(self):
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
