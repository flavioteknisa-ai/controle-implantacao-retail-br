# -*- coding: utf-8 -*-
from datetime import date, timedelta
from typing import List, Dict, Tuple
from erp_models import Projeto, Modulo, Unidade


class ProjetoAnalytics:
    """Análises sobre projetos ERP: status, atrasos, progresso, receita"""

    def __init__(self, projetos: List[Projeto]):
        self.projetos = projetos

    def projetos_por_status(self) -> Dict[str, int]:
        """
        Retorna contagem de projetos por status.
        Retorna {'Em andamento': int, 'Finalizado': int, 'Cancelado': int}
        """
        contagem = {
            'Em andamento': 0,
            'Finalizado': 0,
            'Cancelado': 0
        }

        for projeto in self.projetos:
            if projeto.status in contagem:
                contagem[projeto.status] += 1

        return contagem

    def projetos_atrasados(self) -> List[Projeto]:
        """Retorna lista de projetos com atraso"""
        return [p for p in self.projetos if p.esta_atrasado()]

    def projetos_proximos_vencimento(self, dias: int = 30) -> List[Dict]:
        """
        Retorna projetos com vencimento nos próximos N dias.
        Retorna lista de {'projeto': Projeto, 'dias_restantes': int}
        """
        proximos = []

        for projeto in self.projetos:
            if projeto.status == 'Finalizado':
                continue

            dias_restantes = projeto.dias_restantes()
            if 0 < dias_restantes <= dias:
                proximos.append({
                    'projeto': projeto,
                    'dias_restantes': dias_restantes
                })

        # Ordena por dias_restantes (mais urgentes primeiro)
        return sorted(proximos, key=lambda x: x['dias_restantes'])

    def valor_total_em_andamento(self) -> float:
        """Retorna valor total mensal de projetos em andamento"""
        return sum(p.valor_total_mes() for p in self.projetos if p.status == 'Em andamento')

    def valor_total_finalizado(self) -> float:
        """Retorna valor total que foi finalizado (histórico)"""
        return sum(p.valor_total_mes() for p in self.projetos if p.status == 'Finalizado')

    def percentual_conclusao_geral(self) -> float:
        """Calcula percentual médio de conclusão de todos os projetos"""
        if not self.projetos:
            return 0

        em_andamento = [p for p in self.projetos if p.status == 'Em andamento']
        if not em_andamento:
            return 0

        total = sum(p.percentual_geral() for p in em_andamento)
        return total / len(em_andamento)

    def projetos_criticos(self) -> List[Dict]:
        """
        Retorna projetos em situação crítica (atrasados + progresso baixo).
        Retorna lista de {'projeto': Projeto, 'motivo': str}
        """
        criticos = []

        for projeto in self.projetos:
            if projeto.status == 'Finalizado':
                continue

            motivos = []

            # Critério 1: Atraso
            if projeto.esta_atrasado():
                dias_atraso = abs(projeto.dias_restantes())
                motivos.append(f"Atraso de {dias_atraso} dias")

            # Critério 2: Progresso baixo (<30%) com tempo passando
            if projeto.percentual_geral() < 30 and projeto.dias_restantes() < 60:
                motivos.append(f"Progresso baixo ({projeto.percentual_geral():.1f}%) com prazo próximo")

            # Critério 3: Módulos atrasados
            modulos_atrasados = projeto.modulos_atrasados()
            if modulos_atrasados:
                motivos.append(f"{len(modulos_atrasados)} módulo(s) atrasado(s)")

            # Critério 4: Unidades atrasadas
            unidades_atrasadas = projeto.unidades_atrasadas()
            if unidades_atrasadas:
                motivos.append(f"{len(unidades_atrasadas)} unidade(s) atrasada(s)")

            if motivos:
                criticos.append({
                    'projeto': projeto,
                    'motivos': motivos,
                    'severidade': len(motivos)  # Quanto mais motivos, mais crítico
                })

        # Ordena por severidade
        return sorted(criticos, key=lambda x: x['severidade'], reverse=True)

    def resumo_geral(self) -> Dict:
        """
        Gera resumo geral dos projetos.
        Retorna dicionário com estatísticas principais
        """
        status_contagem = self.projetos_por_status()
        atrasados = self.projetos_atrasados()
        criticos = self.projetos_criticos()

        return {
            'total_projetos': len(self.projetos),
            'em_andamento': status_contagem['Em andamento'],
            'finalizados': status_contagem['Finalizado'],
            'cancelados': status_contagem['Cancelado'],
            'atrasados': len(atrasados),
            'criticos': len(criticos),
            'percentual_conclusao_geral': self.percentual_conclusao_geral(),
            'valor_mensal_ativo': self.valor_total_em_andamento(),
            'proximamente_vencer': len(self.projetos_proximos_vencimento(30))
        }

    def modulos_em_risco(self) -> List[Dict]:
        """
        Retorna módulos que estão em risco (atraso próximo ou progresso baixo).
        Retorna lista de {'modulo': Modulo, 'projeto': Projeto, 'dias_restantes': int}
        """
        em_risco = []

        for projeto in self.projetos:
            if projeto.status == 'Finalizado':
                continue

            for modulo in projeto.modulos:
                if modulo.status == 'Concluído':
                    continue

                dias_restantes = modulo.dias_restantes()

                # Critérios de risco
                esta_em_risco = False

                # Risco 1: Vai vencer em menos de 30 dias
                if 0 < dias_restantes <= 30:
                    esta_em_risco = True

                # Risco 2: Já está atrasado
                if dias_restantes < 0:
                    esta_em_risco = True

                # Risco 3: Pouco progresso faltando tempo
                if modulo.percentual_conclusao < 50 and dias_restantes < 45:
                    esta_em_risco = True

                if esta_em_risco:
                    em_risco.append({
                        'modulo': modulo,
                        'projeto': projeto,
                        'dias_restantes': dias_restantes,
                        'risco': 'crítico' if dias_restantes < 0 else 'alto' if dias_restantes <= 15 else 'médio'
                    })

        return sorted(em_risco, key=lambda x: x['dias_restantes'])

    def unidades_em_risco(self) -> List[Dict]:
        """
        Retorna unidades que estão em risco (não iniciadas perto do vencimento).
        Retorna lista de {'unidade': Unidade, 'projeto': Projeto}
        """
        em_risco = []

        for projeto in self.projetos:
            if projeto.status == 'Finalizado':
                continue

            for unidade in projeto.unidades:
                if unidade.status == 'Finalizado':
                    continue

                # Risco: Unidade não iniciada e projeto está perto de vencer
                if unidade.status == 'Não iniciado' and projeto.dias_restantes() < 60:
                    em_risco.append({
                        'unidade': unidade,
                        'projeto': projeto
                    })

        return em_risco

    def distribuicao_por_responsavel(self) -> Dict[str, List[Projeto]]:
        """
        Agrupa projetos por responsável.
        Retorna {'Nome Responsável': [lista de projetos]}
        """
        distribuicao = {}

        for projeto in self.projetos:
            responsavel = projeto.responsavel or 'Não atribuído'

            if responsavel not in distribuicao:
                distribuicao[responsavel] = []

            distribuicao[responsavel].append(projeto)

        return distribuicao

    def evolucao_por_mes(self, meses: int = 12) -> List[Dict]:
        """
        Simula evolução de projetos mês a mês (baseado em datas de conclusão).
        Retorna lista de {'mes': str, 'projetos_vencidos': int, 'projetos_restantes': int}
        """
        hoje = date.today()
        evolucao = []

        for i in range(meses):
            data_mes = hoje + timedelta(days=30 * i)
            ano_mes = data_mes.strftime('%m/%Y')

            vencidos = sum(1 for p in self.projetos
                          if p.status != 'Finalizado' and p.data_conclusao <= data_mes)
            restantes = sum(1 for p in self.projetos
                           if p.status != 'Finalizado' and p.data_conclusao > data_mes)

            evolucao.append({
                'mes': ano_mes,
                'projetos_vencidos': vencidos,
                'projetos_restantes': restantes
            })

        return evolucao
