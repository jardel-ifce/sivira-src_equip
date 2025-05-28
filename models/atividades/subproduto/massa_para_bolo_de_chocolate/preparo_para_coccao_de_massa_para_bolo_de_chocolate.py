from models.atividade_base import Atividade
from models.equips.bancada import Bancada
from models.equips.armario_esqueleto import ArmarioEsqueleto
from enums.tipo_equipamento import TipoEquipamento
from datetime import timedelta


class PreparoParaCoccaoDeMassaDeBoloDeChocolate(Atividade):
    """
    Atividade que representa o preparo para cocção da massa de bolo de chocolate.
    Utiliza bancadas (ocupação fracionada) e armário esqueleto (níveis de tela).
    """

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.BANCADAS: 1,
            TipoEquipamento.ARMARIOS_PARA_FERMENTACAO: 1,
        }

    def calcular_duracao(self):
        q = self.quantidade_produto
        if 3000 <= q <= 6000:
            self.duracao = timedelta(minutes=8)
        elif 6001 <= q <= 13000:
            self.duracao = timedelta(minutes=16)
        elif 13001 <= q <= 20000:
            self.duracao = timedelta(minutes=24)
        else:
            raise ValueError(
                f"❌ Quantidade {q} fora das faixas válidas para PREPARO PARA COCCAO DE MASSA DE BOLO DE CHOCOLATE."
            )

    def iniciar(self):
        if not self.alocada:
            raise Exception("❌ Atividade não alocada ainda.")

        bancada_alocada = None
        armario_alocado = None

        equipamentos_ordenados = sorted(
            self.equipamentos_selecionados,
            key=lambda e: self.fips_equipamentos.get(e, 999)
        )

        for equipamento in equipamentos_ordenados:
            if isinstance(equipamento, Bancada) and bancada_alocada is None:
                sucesso = equipamento.ocupar(equipamento.capacidade_total)
                if sucesso:
                    bancada_alocada = equipamento
                    print(
                        f"🪵 Bancada {equipamento.nome} ocupada na fração {equipamento.capacidade_total} "
                        f"para preparo da massa de bolo de chocolate."
                    )
                else:
                    print(
                        f"⚠️ Bancada {equipamento.nome} não disponível. Buscando próxima..."
                    )

            if isinstance(equipamento, ArmarioEsqueleto) and armario_alocado is None:
                sucesso = equipamento.ocupar(self.quantidade_produto)
                if sucesso:
                    armario_alocado = equipamento
                    print(
                        f"🥶 Armário {equipamento.nome} ocupado com {self.quantidade_produto}g "
                        f"(equivale a {(self.quantidade_produto + 999) // 1000} níveis de tela)."
                    )
                else:
                    print(
                        f"⚠️ Armário {equipamento.nome} não disponível. Buscando próxima..."
                    )

            if bancada_alocada and armario_alocado:
                print(
                    f"✅ Preparo para cocção de massa de bolo de chocolate iniciado com "
                    f"Bancada {bancada_alocada.nome} e Armário {armario_alocado.nome}."
                )
                return True

        raise Exception(
            "❌ Não foi possível alocar todos os equipamentos necessários "
            "(Bancada e Armário Esqueleto)."
        )
