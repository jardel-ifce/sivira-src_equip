from enums.tipo_equipamento import TipoEquipamento
from models.atividade_base import Atividade
from models.equips.bancada import Bancada
from models.equips.armario_esqueleto import ArmarioEsqueleto
from datetime import timedelta


class PreparoParaArmazenamentoDeMassaParaBrownie(Atividade):
    """
    Atividade que representa o preparo para armazenamento de massas para brownie.
    Utiliza bancadas e armários esqueleto.
    """

    @property
    def quantidade_por_tipo_equipamento(self):
        return {
            TipoEquipamento.BANCADAS: 1,
            TipoEquipamento.ARMARIOS_PARA_FERMENTACAO: 1,
        }

    def calcular_duracao(self):
        """
        Define a duração da atividade com base na quantidade de massa.
        Tempo fixo de 20 minutos.
        """
        q = self.quantidade_produto
        if 3000 <= q <= 17000:
            self.duracao = timedelta(minutes=20)
        elif 17001 <= q <= 34000:
            self.duracao = timedelta(minutes=20)
        elif 34001 <= q <= 50000:
            self.duracao = timedelta(minutes=20)
        else:
            raise ValueError(
                f"❌ Quantidade {q} fora das faixas para PREPARO PARA ARMAZENAMENTO DE MASSAS PARA BROWNIE."
            )

    def iniciar(self):
        """
        Executa os métodos específicos dos equipamentos selecionados,
        priorizando conforme o FIP dos equipamentos.
        """
        if not self.alocada:
            raise Exception("❌ Atividade não alocada ainda.")

        bancada_alocada = None
        armario_alocado = None

        # Ordenar os equipamentos por FIP
        equipamentos_ordenados = sorted(
            self.equipamentos_selecionados,
            key=lambda e: self.fips_equipamentos.get(e, 999)
        )

        for equipamento in equipamentos_ordenados:
            # Ocupação da bancada
            if isinstance(equipamento, Bancada) and bancada_alocada is None:
                sucesso = equipamento.ocupar((1, 4))  # Exemplo: ocupa 1/4 da bancada
                if sucesso:
                    bancada_alocada = equipamento
                    print(
                        f"🧰 Bancada {equipamento.nome} ocupada para preparo de armazenamento."
                    )
                else:
                    print(
                        f"⚠️ Bancada {equipamento.nome} não disponível. Buscando próxima..."
                    )

            # Ocupação do Armário Esqueleto (seguindo a lógica de 1000g = 1 nível)
            if isinstance(equipamento, ArmarioEsqueleto) and armario_alocado is None:
                sucesso = equipamento.ocupar(self.quantidade_produto)
                if sucesso:
                    armario_alocado = equipamento
                    print(
                        f"📦 Armário Esqueleto {equipamento.nome} ocupado com "
                        f"{self.quantidade_produto}g (equivale a "
                        f"{(self.quantidade_produto + 999) // 1000} níveis de tela)."
                    )
                else:
                    print(
                        f"⚠️ Armário Esqueleto {equipamento.nome} não disponível. Buscando próximo..."
                    )

            # Se ambos foram alocados, encerra o loop
            if bancada_alocada and armario_alocado:
                print(
                    f"✅ Preparo para armazenamento de massas para brownie iniciado com "
                    f"Bancada {bancada_alocada.nome} e Armário {armario_alocado.nome}."
                )
                return True

        # Se falhar a alocação de qualquer um dos dois
        raise Exception(
            "❌ Não foi possível alocar todos os equipamentos necessários "
            "(Bancada e Armário Esqueleto)."
        )
