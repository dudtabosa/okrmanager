# OKR Manager

Sistema de gerenciamento de OKRs (Objectives and Key Results) desenvolvido em Django.

## 📋 Sobre o Projeto

O OKR Manager é uma aplicação web para gerenciamento de Objetivos e Resultados-Chave (OKRs) que permite:

- Acompanhamento de objetivos por times
- Monitoramento de progresso trimestral e anual
- Dashboard com visão geral do desempenho
- Gestão de KRs (Key Results) com metas trimestrais e anuais
- Registro histórico de progressos

## 🚀 Funcionalidades

- **Dashboard Anual**: Visualização do progresso geral e por trimestre
- **Gestão de Times**: Organização de OKRs por equipes
- **Controle de Objetivos**: Cadastro e acompanhamento de objetivos
- **Gestão de KRs**: Registro e atualização de resultados-chave
- **Histórico de Progressos**: Acompanhamento da evolução dos KRs
- **Interface Administrativa**: Painel admin para gestão completa dos dados

## 🛠️ Tecnologias Utilizadas

- Python
- Django
- SQLite
- HTML/CSS
- JavaScript
- Bootstrap

## ⚙️ Configuração do Ambiente

1. Clone o repositório:
```bash
git clone https://github.com/dudtabosa/okrmanager.git
cd okrmanager
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\\Scripts\\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Execute as migrações:
```bash
python manage.py migrate
```

5. Crie um superusuário:
```bash
python manage.py createsuperuser
```

6. Inicie o servidor:
```bash
python manage.py runserver
```

## 📊 Estrutura do Projeto

- `myapp/`: Aplicação principal
  - `templates/`: Templates HTML
  - `static/`: Arquivos estáticos (CSS, JS)
  - `views/`: Views da aplicação
- `okrs/`: App de gestão de OKRs
  - `models.py`: Modelos de dados
  - `admin.py`: Configuração do admin
  - `views.py`: Views específicas de OKRs

## 👥 Modelos de Dados

- **Diretoria**: Gestão de diretorias/departamentos
- **Time**: Equipes vinculadas às diretorias
- **Objetivo**: Objetivos vinculados aos times
- **KeyResult**: Resultados-chave vinculados aos objetivos
- **KeyResultProgresso**: Registro de progresso dos KRs

## 📈 Métricas e Cálculos

- Progresso anual por KR
- Progresso geral por OKR
- Média trimestral de progresso
- Progresso geral da organização

## 🔐 Acesso ao Sistema

- URL Admin: `/admin/`
- Dashboard: `/myapp/`
- Meus Objetivos: `/myapp/all-goals/`
- OKRs OPAH: `/myapp/opah-okrs/`

## 📝 Licença

Este projeto está sob a licença MIT.

## 👤 Autor

Carlos Eduardo Silva Tabosa
