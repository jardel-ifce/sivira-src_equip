#!/usr/bin/env python3
"""
Teste do novo formato de data nos logs de funcionários
"""

from datetime import datetime, time
from utils.logs.registrador_funcionarios import RegistradorFuncionarios
from enums.funcionarios.tipo_profissional import TipoProfissional

def testar_novo_formato():
    """Testa o novo formato com datas nos logs."""
    print("🧪 Testando novo formato de logs com datas")

    registrador = RegistradorFuncionarios()

    # Simular requisito com data/hora específica
    inicio = datetime(2025, 9, 30, 8, 0)  # 30/09/2025 08:00
    fim = datetime(2025, 9, 30, 10, 30)   # 30/09/2025 10:30

    registrador.registrar_requisito_funcionario(
        id_ordem=999,
        id_pedido=888,
        id_atividade=12345,
        nome_atividade="teste_formato_data_atividade",
        tipos_profissionais={TipoProfissional.CONFEITEIRO, TipoProfissional.AUXILIAR_DE_CONFEITEIRO},
        inicio=inicio,
        fim=fim,
        quantidade=2,
        fips={"CONFEITEIRO": 3, "AUXILIAR_DE_CONFEITEIRO": 1}
    )

    print("✅ Log de teste criado!")
    print("📁 Verifique: logs/tipos_funcionarios_requeridos/ordem: 999 | pedido: 888.log")

if __name__ == "__main__":
    testar_novo_formato()