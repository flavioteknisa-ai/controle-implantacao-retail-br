# 📅 Sistema de Controle de Férias - Guia Rápido

## ⚡ Início Rápido

### 1. Iniciar a Aplicação

**Opção A: Clique Duplo no run.bat**
```
sistema_ferias\run.bat
```

**Opção B: Terminal (PowerShell)**
```powershell
cd sistema_ferias
python app.py
```

### 2. Acessar no Navegador
```
http://localhost:5000
```

---

## 📊 Importar Dados de Colaboradores

Se você tem uma planilha Excel com dados de colaboradores, use o script de importação:

### Opção 1: Modo Interativo

```powershell
cd sistema_ferias
python importar_dados.py
```

O script pedirá:
1. **Caminho do arquivo** (ex: `C:\dados\colaboradores.xlsx`)
2. **Nome da coluna com nomes** (ex: `Nome`, `Colaborador`)
3. **Nome da coluna com datas** (ex: `Data Admissão`, `Admissao`)
4. **Nome da coluna com times** (ex: `Departamento`, `Time`)

### Opção 2: Importação Programática

```python
from importar_dados import importar_colaboradores

importar_colaboradores(
    caminho_origem=r'C:\dados\colaboradores.xlsx',
    coluna_nome='Nome',
    coluna_data_admissao='Data Admissão',
    coluna_time='Departamento'
)
```

### Exemplo de Estrutura de Arquivo

Seu arquivo Excel deve ter algo assim:

| Nome | Data Admissão | Departamento |
|------|---------------|--------------|
| João Silva | 2022-06-15 | Tech |
| Maria Santos | 2023-01-20 | Sales |
| Pedro Costa | 2021-03-10 | RH |

---

## 🎯 Usar o Sistema

### 1. Adicionar Colaborador
1. Menu → **"+ Colaborador"**
2. Preencha: Nome, Data Admissão, Departamento
3. Clique "Salvar Colaborador"

### 2. Registrar Férias
1. Menu → **"+ Férias"**
2. Selecione o colaborador
3. Escolha as datas (início e fim)
4. Sistema valida:
   - ✓ Mínimo 12 meses de admissão
   - ✓ Saldo disponível
   - ✓ Sem sobreposição com outras férias
5. Se houver **conflito** (2+ pessoas ausentes):
   - Sistema exibe alerta
   - Clique **"✓ Aprovar Mesmo Assim"** se necessário

### 3. Ver Dashboard
- Visualiza próximas férias (90 dias)
- Mostra saldos atuais
- Exibe conflitos não-aprovados

---

## 💾 Dados Salvos em Excel

Todos os dados ficam em: `sistema_ferias/data/ferias_data.xlsx`

**Abas:**
- **Colaboradores**: ID, Nome, Data Admissão, Time, Ativo
- **Férias Planejadas**: Períodos futuros com status
- **Férias Realizadas**: Histórico de férias já usadas

---

## 🔧 Troubleshooting

### Erro: "Colaborador precisa de 12 meses"
- Férias só podem ser tiradas após 12 meses da admissão
- Solução: Escolha data posterior

### Erro: "Saldo insuficiente"
- Colaborador não tem saldo para esse período
- Solução: Registre menos dias ou escolha outra pessoa

### Erro: "Período já existe"
- Mesmo período foi registrado 2 vezes
- Solução: Cancele o período duplicado

### Página não carrega
- Verifique se a aplicação está rodando: `python app.py`
- Verifique porta: http://localhost:5000
- Se porta 5000 está ocupada, edite `app.py` linha final: `app.run(port=5001)`

---

## 📋 Fluxo de Validação

```
┌─────────────────────┐
│  Registrar Férias   │
└──────────┬──────────┘
           ↓
    ┌──────────────┐
    │ 12 meses?    │ ← Data admissão + 12 meses?
    └──────┬───────┘
           ↓ SIM
    ┌──────────────┐
    │ Saldo ok?    │ ← Tem dias disponíveis?
    └──────┬───────┘
           ↓ SIM
    ┌──────────────────┐
    │ Sobrepõe?        │ ← Conflita com outra pessoa?
    └──────┬───────────┘
           ↓ NÃO
    ┌──────────────────┐
    │ ✓ Registrado OK  │
    └──────────────────┘
    
    Se SIM em "Sobrepõe?":
    ┌──────────────────────┐
    │ ⚠ Alerta Conflito    │
    │ Aprovar mesmo assim? │
    └──────┬───────────────┘
           ↓ SIM
    ┌──────────────────────┐
    │ ✓ Registrado         │
    │   (com aprovação)    │
    └──────────────────────┘
```

---

## 📈 Cálculo de Saldo

```
Saldo = Dias de Direito - Dias Utilizados

Dias de Direito = (Anos desde admissão) × 30

Exemplo:
├─ Admissão: 2022-06-15
├─ Hoje: 2026-06-25
├─ Direito: 4 anos × 30 = 120 dias
├─ Utilizados em 2025: 50 dias
└─ Saldo: 120 - 50 = 70 dias
```

---

## 🎓 Exemplos de Uso

### Caso 1: Importar 10 Colaboradores
```powershell
python importar_dados.py
# Arquivo: C:\dados\team.xlsx
# Coluna Nome: Colaborador
# Coluna Data: Data Admissao
# Coluna Time: Area
```

### Caso 2: Registrar Férias de 20 Dias
1. Dashboard → "+ Férias"
2. Selecione João Silva
3. Data início: 01/06/2026
4. Data fim: 20/06/2026 (20 dias automaticamente)
5. Sistema valida e registra

### Caso 3: Aprovar Férias em Conflito
1. Sistema detecta: João e Maria no mesmo período
2. Clique "✓ Aprovar Mesmo Assim"
3. Alerta desaparece do dashboard
4. Férias registradas com flag de aprovação

---

## 📞 Suporte

Se tiver dúvidas sobre:
- **Instalação**: Verifique requirements.txt está instalado
- **Dados**: Confirme estrutura do Excel (nomes de colunas)
- **Bugs**: Verifique console para mensagens de erro

---

**Versão**: MVP 1.0  
**Última atualização**: 2026-05-25  
**Status**: ✓ Pronto para uso
