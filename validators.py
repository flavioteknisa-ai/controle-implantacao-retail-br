from datetime import datetime
from typing import List, Tuple
from dateutil.relativedelta import relativedelta
from models import Colaborador, Ferias


class FeriasValidator:
    """Valida período de férias contra regras rigorosas"""

    @staticmethod
    def validar_ferias(ferias: Ferias, colaborador: Colaborador, todas_ferias: List[Ferias],
                      ferias_realizadas: List[Ferias], saldo_disponivel: int) -> Tuple[bool, str]:
        """
        Valida se um período de férias é válido.
        Retorna (válido, mensagem_erro)
        """

        # 1. Validação de datas básicas
        if ferias.data_fim <= ferias.data_inicio:
            return False, "Data final deve ser posterior à data inicial"

        # 2. Validação de admissão (12 meses mínimo)
        delta = relativedelta(ferias.data_inicio, colaborador.data_admissao)
        if delta.years == 0 and delta.months < 12:
            meses_faltantes = 12 - delta.months
            return False, f"Colaborador precisa de mais {meses_faltantes} mês(es) de admissão. Data liberação: {(colaborador.data_admissao + relativedelta(months=12)).strftime('%d/%m/%Y')}"

        # 3. Validação de saldo
        if ferias.dias > saldo_disponivel:
            return False, f"Saldo insuficiente. Disponível: {saldo_disponível} dias, solicitado: {ferias.dias} dias"

        # 4. Validação de sobreposição COMPLETA (mesmo período 2x)
        for outras in todas_ferias:
            if outras.id == ferias.id or outras.status == 'Cancelado':
                continue

            # Se é EXATAMENTE o mesmo período
            if outras.data_inicio == ferias.data_inicio and outras.data_fim == ferias.data_fim:
                return False, f"Período {ferias.data_inicio.strftime('%d/%m/%Y')} a {ferias.data_fim.strftime('%d/%m/%Y')} já foi registrado"

            # Se sobrepõe parcialmente (mesmo que 1 dia)
            if ferias.sobrepoe_com(outras) and outras.colaborador_id == ferias.colaborador_id:
                dias_overlap = ferias.get_dias_sobrepostos(outras)
                return False, f"Período sobrepõe com férias existentes ({dias_overlap} dia(s)) em {outras.data_inicio.strftime('%d/%m/%Y')} a {outras.data_fim.strftime('%d/%m/%Y')}"

        return True, ""

    @staticmethod
    def validar_novo_colaborador(nome: str, data_admissao: datetime) -> Tuple[bool, str]:
        """Valida dados de novo colaborador"""

        if not nome or len(nome.strip()) == 0:
            return False, "Nome é obrigatório"

        if data_admissao > datetime.now():
            return False, "Data de admissão não pode ser no futuro"

        return True, ""

    @staticmethod
    def detectar_conflitos_time(ferias: Ferias, todas_ferias: List[Ferias], colaboradores: dict) -> List[Tuple[Ferias, int]]:
        """
        Detecta conflitos de férias no mesmo time (2+ pessoas ausentes).
        Retorna lista de (férias em conflito, dias sobrepostos)
        """
        conflitos = []
        colab_ferias = colaboradores.get(ferias.colaborador_id)

        if not colab_ferias:
            return conflitos

        for outras in todas_ferias:
            if outras.id == ferias.id or outras.status == 'Cancelado':
                continue

            # Se sobrepõe
            if ferias.sobrepoe_com(outras):
                colab_outras = colaboradores.get(outras.colaborador_id)

                # Se mesmo time
                if colab_outras and colab_ferias.time == colab_outras.time:
                    dias_overlap = ferias.get_dias_sobrepostos(outras)
                    conflitos.append((outras, dias_overlap))

        return conflitos
