# -*- coding: utf-8 -*-
from datetime import date
from typing import Tuple
from erp_models import Projeto, Modulo, Unidade


class ProjetoValidator:
    """Valida dados de projetos ERP contra regras de negócio"""

    @staticmethod
    def validar_projeto(nome: str, data_aceite: date, data_conclusao: date,
                       valor_mensalidades: float = 0) -> Tuple[bool, str]:
        """
        Valida dados de um novo projeto.
        Retorna (válido, mensagem_erro)
        """

        # 1. Validação de nome
        if not nome or len(nome.strip()) == 0:
            return False, "Nome do projeto é obrigatório"

        if len(nome.strip()) < 3:
            return False, "Nome do projeto deve ter pelo menos 3 caracteres"

        # 2. Validação de datas
        # Data de conclusão é opcional, validar apenas se foi fornecida
        if data_conclusao is not None and data_aceite >= data_conclusao:
            return False, "Data de conclusão deve ser posterior à de aceite"

        # 3. Validação de valor
        if valor_mensalidades < 0:
            return False, "Valor de mensalidades não pode ser negativo"

        return True, ""

    @staticmethod
    def validar_modulo(nome: str, data_conclusao: date = None,
                       data_inicio: date = None) -> Tuple[bool, str]:
        """
        Valida dados de um módulo ERP.
        Retorna (válido, mensagem_erro)
        """

        # 1. Validação de nome
        if not nome or len(nome.strip()) == 0:
            return False, "Nome do módulo é obrigatório"

        # 2. Se tem datas, valida sequência
        if data_inicio is not None and data_conclusao is not None:
            if data_inicio >= data_conclusao:
                return False, "Data de conclusão deve ser posterior à de início"

        return True, ""

    @staticmethod
    def validar_unidade(nome: str, data_conclusao: date = None) -> Tuple[bool, str]:
        """
        Valida dados de uma unidade/loja.
        Retorna (válido, mensagem_erro)
        """

        # 1. Validação de nome
        if not nome or len(nome.strip()) == 0:
            return False, "Nome da unidade é obrigatório"

        if len(nome.strip()) < 2:
            return False, "Nome da unidade deve ter pelo menos 2 caracteres"

        return True, ""

    @staticmethod
    def validar_conclusao_projeto(projeto: Projeto) -> Tuple[bool, str]:
        """
        Valida se o projeto pode ser marcado como finalizado.
        Retorna (válido, mensagem_erro)
        """

        # Verifica se todos os módulos estão concluídos ou cancelados
        modulos_pendentes = [m for m in projeto.modulos if m.status not in ['Concluído', 'Cancelado']]
        if modulos_pendentes:
            return False, f"Ainda existem {len(modulos_pendentes)} módulos não concluídos"

        # Verifica se todas as unidades estão finalizadas ou canceladas
        unidades_pendentes = [u for u in projeto.unidades if u.status not in ['Finalizado', 'Cancelado']]
        if unidades_pendentes:
            return False, f"Ainda existem {len(unidades_pendentes)} unidades não finalizadas"

        return True, ""
