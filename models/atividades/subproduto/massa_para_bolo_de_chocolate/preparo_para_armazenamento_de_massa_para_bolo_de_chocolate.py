from models.atividade_base import Atividade
from models.equips.bancada import Bancada
from models.equips.armario_esqueleto import ArmarioEsqueleto
from enums.tipo_equipamento import TipoEquipamento
from datetime import timedelta


class PreparoParaArmazenamentoDeMassaDeBoloDeChocolate(Atividade):
    """
    Atividade que representa o preparo para armazenamento de massa de bolo de chocolate.
    Utiliza bancada (ocupação fracionada) e armário esqueleto (níveis de tela).
    """

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.BANCADAS: 1,
            TipoEquipamento.ARMARIOS_PARA_FERMENTACAO: 1,
        }

    def calcular_duracao(self):
        """
        Define a duração da atividade.
        Tempo fixo de 20 minutos (exemplo — ajuste conforme necessário).
        """
        self.duracao = timedelta(minutes=20)  # 🔧 Ajuste conforme regra real

    def iniciar(self):
        """
        Realiza a ocupação dos equipamentos: bancada e armário esqueleto.
        """
        if not self.alocada:
            raise Exception("❌ Atividade não alocada ainda.")

        bancada_alocada = None
        armario_alocado = None

        equipamentos_ordenados = sorted(
            self.equipamentos_selecionados,
            key=lambda e: self.fips_equipamentos.get(e, 999)
        )

        # Quantidade de níveis necessários no armário (1000g = 1 nível)
        niveis_necessarios = (self.quantidade_produto + 999) // 1000

        for equipamento in equipamentos_ordenados:
            # 👉 Ocupação da Bancada
            if isinstance(equipamento, Bancada) and bancada_alocada is None:
                sucesso = equipamento.ocupar(equipamento.capacidade_total)
                if sucesso:
                    bancada_alocada = equipamento
                    print(
                        f"🪵 Bancada {equipamento.nome} ocupada na fração {equipamento.capacidade_total} "
                        f"para preparo da massa para armazenamento."
                    )
                else:
                    print(
                        f"⚠️ Bancada {equipamento.nome} não disponível. Buscando próxima..."
                    )

            # 👉 Ocupação do Armário Esqueleto
            if isinstance(equipamento, ArmarioEsqueleto) and armario_alocado is None:
                if niveis_necessarios < equipamento.nivel_tela_min:
                    raise Exception(
                        f"❌ A quantidade ({self.quantidade_produto}g) exige pelo menos "
                        f"{equipamento.nivel_tela_min} nível(s) no armário {equipamento.nome}."
                    )
                if niveis_necessarios > equipamento.nivel_tela_max:
                    raise Exception(
                        f"❌ A quantidade ({self.quantidade_produto}g) excede o limite máximo de "
                        f"{equipamento.nivel_tela_max} níveis no armário {equipamento.nome}."
                    )

                sucesso = equipamento.ocupar(self.quantidade_produto)
                if sucesso:
                    armario_alocado = equipamento
                    print(
                        f"🥶 Armário {equipamento.nome} ocupado com {niveis_necessarios} níveis "
                        f"para armazenamento de {self.quantidade_produto}g de massa."
                    )
                else:
                    print(
                        f"⚠️ Armário {equipamento.nome} não disponível. Buscando próximo..."
                    )

            if bancada_alocada and armario_alocado:
                print(
                    f"✅ Preparo para armazenamento da massa de bolo de chocolate iniciado com "
                    f"Bancada {bancada_alocada.nome} e Armário {armario_alocado.nome}."
                )
                return True

        raise Exception(
            "❌ Não foi possível alocar todos os equipamentos necessários "
            "(Bancada e Armário Esqueleto)."
        )
