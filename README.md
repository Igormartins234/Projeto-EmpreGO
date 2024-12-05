# EmpreGO - Sistema de Gerenciamento de Vagas de Emprego

O **EmpreGO** é uma plataforma web desenvolvida para conectar empresas e candidatos, facilitando a busca e a aplicação para vagas de emprego. O sistema permite que empresas cadastradas publiquem vagas, gerenciem candidaturas e mantenham seus dados atualizados. Candidatos podem pesquisar vagas, se candidatar e enviar seus currículos.
A
---

## Índice
- [Funcionalidades](#funcionalidades)
- [Tecnologias Utilizadas](#tecnologias-utilizadas)
- [Instalação](#instalação)

---

## Funcionalidades

### Para Empresas:
- **Cadastro**: Empresas podem se cadastrar na plataforma, fornecendo informações como nome, CNPJ, telefone e email.
- **Login**: Acesso seguro através de credenciais de login.
- **Publicação de Vagas**: Criar novas vagas de emprego, incluindo detalhes como título, descrição, tipo de vaga, local, salário e formato de trabalho.
- **Gerenciamento de Vagas**: Editar vagas existentes, alterar o status (ativa/inativa) e excluir vagas.
- **Visualização de Candidaturas**: Acesso à lista de candidatos para cada vaga, com informações de contato e currículos.
- **Gerenciamento de Status da Empresa**: A empresa pode ter seu status alterado (ativa/inativa) pelo administrador.

### Para Candidatos:
- **Busca de Vagas**: Pesquisar vagas de emprego utilizando palavras-chave (título e descrição).
- **Visualização de Detalhes da Vaga**: Acesso a informações completas sobre vagas de interesse.
- **Candidatura**: Aplicar para vagas de emprego, enviando informações pessoais e currículo.

---

## Tecnologias Utilizadas

### Backend:
![PYTHON](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![FLASK](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=Flask&logoColor=white)
![MYSQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)

### Frontend:
![HTML](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![CSS](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)
![JAVACRIPT](https://img.shields.io/badge/JavaScript-323330?style=for-the-badge&logo=javascript&logoColor=F7DF1E)
![BOOTSTRAP](https://img.shields.io/badge/Bootstrap-563D7C?style=for-the-badge&logo=bootstrap&logoColor=white)

---

## Instalação

Clone o repositório: git clone [URL do repositório] Substitua [URL do repositório] pela URL correta do seu repositório.

Crie um banco de dados MySQL: Crie um banco de dados com o nome especificado em config.py. Importe o esquema do banco de dados (script SQL, se existir um) para o banco criado.

Instale as dependências: pip install -r requirements.txt

Configure o arquivo config.py: Preencha as credenciais do seu banco de dados MySQL (DATABASE, USER, PASSWORD, HOST). Crie este arquivo se ele não existir, baseado no exemplo config_example.py (se existir).

Execute a aplicação: python app.py
