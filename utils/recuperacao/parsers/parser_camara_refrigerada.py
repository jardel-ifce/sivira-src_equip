"""
Parser para Câmara Refrigerada
==============================

Extrai ocupações de câmaras refrigeradas do log detalhado.

Formato esperado no log:
```
🔹 Nível 1, Tela 1:
   🗂️ Ordem 1 | Pedido 2 | Atividade 10723 | Item 1072 | 10.00 unidades | 05:36 → 06:36 | Temp: 4°C
📦 Caixa 1:
   🗂️ Ordem 1 | Pedido 2 | Atividade 20045 | Item 2004 | 500.00 unidades | 04:08 → 04:13 | Temp: -18°C
```
"""

from typing import List, Optional
from datetime import datetime
from .parser_base import ParserBase
from utils.recuperacao.modelos.ocupacao_dto import OcupacaoDTO


class ParserCamaraRefrigerada(ParserBase):
    """Parser especializado para Câmaras Refrigeradas"""

    def parse(self, log_content: str, nome_equipamento: str) -> List[OcupacaoDTO]:
        self.limpar_erros()
        ocupacoes = []

        linhas = log_content.split('\n')
        nivel_atual = None
        caixa_atual = None
        data_base = datetime.now()

        for linha in linhas:
            linha = linha.strip()

            # Detectar nível
            if '🔹 Nível' in linha:
                nivel_atual = self.extrair_numero_nivel(linha)
                caixa_atual = None
                continue

            # Detectar caixa
            if '📦 Caixa' in linha:
                caixa_atual = self.extrair_numero_caixa(linha)
                nivel_atual = None
                continue

            # Detectar ocupação
            if '🗂️' in linha:
                ocupacao = self._extrair_ocupacao_camara(
                    linha,
                    nivel_atual,
                    caixa_atual,
                    nome_equipamento,
                    data_base
                )
                if ocupacao:
                    ocupacoes.append(ocupacao)

        return ocupacoes

    def _extrair_ocupacao_camara(
        self,
        linha: str,
        nivel: Optional[int],
        caixa: Optional[int],
        nome_equipamento: str,
        data_base: datetime
    ) -> Optional[OcupacaoDTO]:
        try:
            ids = self.extrair_ids_ocupacao(linha)
            if not ids:
                return None
            id_ordem, id_pedido, id_atividade, id_item = ids

            horarios = self.extrair_horarios(linha)
            if not horarios:
                return None
            inicio_str, fim_str = horarios

            inicio = self.converter_horario_para_datetime(inicio_str, data_base=data_base)
            fim = self.converter_horario_para_datetime(fim_str, data_base=data_base)
            fim = self.ajustar_data_se_atravessar_meia_noite(inicio, fim)

            temperatura = self.extrair_temperatura(linha)
            quantidade = self.extrair_quantidade_unidades(linha)

            return OcupacaoDTO(
                id_ordem=id_ordem,
                id_pedido=id_pedido,
                id_atividade=id_atividade,
                id_item=id_item,
                inicio=inicio,
                fim=fim,
                nome_equipamento=nome_equipamento,
                tipo_equipamento="CamaraRefrigerada",
                detalhes={
                    "nivel_numero": nivel,
                    "caixa_numero": caixa,
                    "temperatura": temperatura,
                    "quantidade": quantidade
                }
            )

        except Exception as e:
            self.adicionar_erro(f"Erro ao extrair ocupação de câmara: {e}")
            return None