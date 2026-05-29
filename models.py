from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import List, Tuple, Dict, Optional


class Colaborador:
    """Representa um colaborador da equipe"""

    def __init__(self, id: int, nome: str, data_admissao: datetime, time: str, ativo: bool = True, cidade: str = ''):
        self.id = id
        self.nome = nome
        self.data_admissao = data_admissao if isinstance(data_admissao, datetime) else datetime.strptime(str(data_admissao), "%Y-%m-%d")
        self.time = time
        self.ativo = ativo
        self.cidade = cidade or ''

    def calcular_saldo_ferias(self, ferias_realizadas: List['Ferias'], data_referencia: Optional[datetime] = None) -> int:
        """
        Calcula o saldo de férias disponível.
        Fórmula: (meses desde admissão / 12 * 30) - dias_já_tirados
        """
        if data_referencia is None:
            data_referencia = datetime.now()

        # Calcula quantos anos completos desde admissão
        delta = relativedelta(data_referencia, self.data_admissao)
        anos_completos = delta.years + (delta.months / 12)

        # Direito total: 30 dias por ano
        direito_total = int(anos_completos * 30)

        # Dias já utilizados (apenas férias realizadas)
        dias_utilizados = sum(f.dias for f in ferias_realizadas if f.status == 'Realizado' and f.colaborador_id == self.id)

        saldo = direito_total - dias_utilizados
        return max(0, saldo)

    def pode_tirar_ferias(self, data_inicio: datetime, data_fim: datetime, ferias_realizadas: List['Ferias'], ferias_planejadas: List['Ferias']) -> Tuple[bool, str]:
        """
        Verifica se o colaborador pode tirar férias nestas datas
        """
        # Verifica se tem pelo menos 12 meses de admissão
        delta = relativedelta(data_inicio, self.data_admissao)
        if delta.years == 0 and (delta.months < 12):
            return False, f"Colaborador precisa ter 12 meses de admissão. Admissão: {self.data_admissao.strftime('%d/%m/%Y')}"

        return True, ""

    def __repr__(self):
        return f"Colaborador(id={self.id}, nome='{self.nome}', time='{self.time}')"


class Ferias:
    """Representa um período de férias de um colaborador"""

    def __init__(self, id: int, colaborador_id: int, data_inicio: datetime, data_fim: datetime,
                 status: str = 'Planejado', conflito_detectado: bool = False, conflito_aprovado: bool = False):
        self.id = id
        self.colaborador_id = colaborador_id
        self.data_inicio = data_inicio if isinstance(data_inicio, datetime) else datetime.strptime(str(data_inicio), "%Y-%m-%d")
        self.data_fim = data_fim if isinstance(data_fim, datetime) else datetime.strptime(str(data_fim), "%Y-%m-%d")
        self.status = status  # 'Planejado', 'Confirmado', 'Realizado', 'Cancelado'
        self.conflito_detectado = conflito_detectado
        self.conflito_aprovado = conflito_aprovado
        self._calcular_dias()

    def _calcular_dias(self):
        """Calcula número de dias de férias (inclui o primeiro e último dia)"""
        delta = self.data_fim - self.data_inicio
        self.dias = delta.days + 1

    def sobrepoe_com(self, outra_ferias: 'Ferias') -> bool:
        """
        Verifica se este período sobrepõe com outro
        Sobreposição ocorre se: data_inicio <= outra.data_fim E data_fim >= outra.data_inicio
        """
        return self.data_inicio <= outra_ferias.data_fim and self.data_fim >= outra_ferias.data_inicio

    def get_dias_sobrepostos(self, outra_ferias: 'Ferias') -> int:
        """Retorna número de dias sobrepostos com outra férias"""
        if not self.sobrepoe_com(outra_ferias):
            return 0

        inicio_overlap = max(self.data_inicio, outra_ferias.data_inicio)
        fim_overlap = min(self.data_fim, outra_ferias.data_fim)

        delta = fim_overlap - inicio_overlap
        return delta.days + 1

    def __repr__(self):
        return f"Ferias(id={self.id}, colaborador_id={self.colaborador_id}, {self.data_inicio.strftime('%d/%m')} a {self.data_fim.strftime('%d/%m')}, {self.dias} dias)"


class ConflictManager:
    """Gerencia conflitos de férias (múltiplas pessoas ausentes)"""

    def __init__(self):
        self.conflitos_aprovados = {}  # {ferias_id: [conflitos_ids]}

    def detectar_conflitos(self, ferias: Ferias, todas_ferias: List[Ferias], colaboradores: Dict[int, Colaborador]) -> List[Tuple[Ferias, List[Ferias]]]:
        """
        Detecta todos os períodos que conflitam com a férias fornecida
        Retorna lista de (ferias em conflito, lista de colaboradores em conflito)
        """
        conflitos = []

        for outra in todas_ferias:
            # Ignora a própria férias e férias canceladas
            if outra.id == ferias.id or outra.status == 'Cancelado':
                continue

            # Se sobrepõe
            if ferias.sobrepoe_com(outra):
                # Verifica se são do mesmo time
                colab_ferias = colaboradores.get(ferias.colaborador_id)
                colab_outra = colaboradores.get(outra.colaborador_id)

                if colab_ferias and colab_outra and colab_ferias.time == colab_outra.time:
                    conflitos.append((outra, [outra]))

        return conflitos

    def aprovar_conflito(self, ferias_id: int):
        """Marca um período de férias como aprovado para conflito"""
        if ferias_id not in self.conflitos_aprovados:
            self.conflitos_aprovados[ferias_id] = True

    def revogar_aprovacao(self, ferias_id: int):
        """Remove aprovação de conflito"""
        if ferias_id in self.conflitos_aprovados:
            del self.conflitos_aprovados[ferias_id]

    def esta_aprovado(self, ferias_id: int) -> bool:
        """Verifica se um período teve conflito aprovado"""
        return self.conflitos_aprovados.get(ferias_id, False)
