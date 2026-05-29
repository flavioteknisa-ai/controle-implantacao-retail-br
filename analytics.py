from datetime import datetime
from typing import List, Dict, Tuple
from models import Colaborador, Ferias


class FeriasAnalytics:
    """Análises sobre férias: conflitos, saldos, disponibilidade"""

    def __init__(self, colaboradores: List[Colaborador], ferias_planejadas: List[Ferias], ferias_realizadas: List[Ferias]):
        self.colaboradores = {c.id: c for c in colaboradores}
        self.ferias_planejadas = ferias_planejadas
        self.ferias_realizadas = ferias_realizadas

    def detectar_conflitos(self) -> List[Dict]:
        """
        Detecta todos os conflitos de férias (2+ pessoas do mesmo time ausentes).
        Retorna lista de conflitos com detalhes
        """
        conflitos = []
        processados = set()

        for ferias in self.ferias_planejadas:
            if ferias.status == 'Cancelado':
                continue

            # Encontra quem mais sai no mesmo período
            colab = self.colaboradores.get(ferias.colaborador_id)
            if not colab:
                continue

            em_conflito = []
            for outras in self.ferias_planejadas:
                if outras.id == ferias.id or outras.status == 'Cancelado':
                    continue

                if ferias.sobrepoe_com(outras):
                    colab_outras = self.colaboradores.get(outras.colaborador_id)
                    if colab_outras and colab.time == colab_outras.time:
                        em_conflito.append(outras)

            if em_conflito:
                chave = tuple(sorted([ferias.id] + [f.id for f in em_conflito]))
                if chave not in processados:
                    processados.add(chave)
                    conflitos.append({
                        'ferias_principal': ferias,
                        'colaborador_principal': colab,
                        'conflitos_com': em_conflito,
                        'data_inicio': ferias.data_inicio,
                        'data_fim': ferias.data_fim,
                        'aprovado': ferias.conflito_aprovado
                    })

        return conflitos

    def obter_saldos_por_colaborador(self) -> Dict[int, Dict]:
        """
        Retorna saldo de férias por colaborador com status (crítico/alerta/ok)
        """
        saldos = {}

        for colab_id, colab in self.colaboradores.items():
            if not colab.ativo:
                continue

            saldo = colab.calcular_saldo_ferias(self.ferias_realizadas)

            # Determina status do saldo
            if saldo == 0:
                status = 'crítico'  # Saldo zerado
            elif saldo <= 10:
                status = 'alerta'   # Saldo baixo
            else:
                status = 'ok'       # Saldo ok

            saldos[colab_id] = {
                'colaborador': colab,
                'saldo': saldo,
                'status': status,
                'direito_total': colab.calcular_saldo_ferias(self.ferias_realizadas) + sum(f.dias for f in self.ferias_realizadas if f.colaborador_id == colab_id)
            }

        return saldos

    def colaboradores_disponiveis(self, data: datetime) -> List[Colaborador]:
        """Retorna colaboradores que NÃO estão de férias em uma data específica"""
        disponíveis = []

        for colab_id, colab in self.colaboradores.items():
            if not colab.ativo:
                continue

            em_ferias = False
            for ferias in self.ferias_planejadas:
                if ferias.colaborador_id == colab_id and ferias.status in ['Confirmado', 'Planejado']:
                    if ferias.data_inicio <= data <= ferias.data_fim:
                        em_ferias = True
                        break

            if not em_ferias:
                disponíveis.append(colab)

        return disponíveis

    def gerar_estado_mes(self, ano: int, mes: int) -> Dict[int, List[Colaborador]]:
        """
        Gera estado de férias para um mês específico.
        Retorna {dia_do_mes: [colaboradores_em_férias]}
        """
        from datetime import date
        from calendar import monthrange

        estado = {}
        dias_no_mes = monthrange(ano, mes)[1]

        for dia in range(1, dias_no_mes + 1):
            data_dia = datetime(ano, mes, dia)
            estado[dia] = self.colaboradores_disponiveis(data_dia)

        return estado

    def obter_proximas_ferias(self, dias_futuros: int = 90) -> List[Dict]:
        """
        Retorna próximas férias nos próximos N dias
        """
        from datetime import timedelta

        hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        data_limite = hoje + timedelta(days=dias_futuros)

        proximas = []
        for ferias in sorted(self.ferias_planejadas, key=lambda f: f.data_inicio):
            if ferias.status == 'Cancelado':
                continue

            if hoje <= ferias.data_inicio <= data_limite:
                colab = self.colaboradores.get(ferias.colaborador_id)
                proximas.append({
                    'ferias': ferias,
                    'colaborador': colab,
                    'dias_para_inicio': (ferias.data_inicio - hoje).days
                })

        return proximas

    def saldos_criticos(self) -> List[Dict]:
        """Retorna colaboradores com saldo crítico (0-10 dias)"""
        saldos = self.obter_saldos_por_colaborador()
        criticos = [s for s in saldos.values() if s['status'] in ['crítico', 'alerta']]
        return sorted(criticos, key=lambda x: x['saldo'])

    def percentual_equipe_em_ferias(self, data: datetime) -> float:
        """Calcula percentual da equipe ativa em férias em uma data"""
        total_ativa = sum(1 for c in self.colaboradores.values() if c.ativo)
        if total_ativa == 0:
            return 0

        em_ferias = 0
        for ferias in self.ferias_planejadas:
            if ferias.status in ['Confirmado', 'Planejado']:
                if ferias.data_inicio <= data <= ferias.data_fim:
                    em_ferias += 1

        return (em_ferias / total_ativa) * 100
