# 🧠 Hostly AI — Monitoramento Inteligente de Maturidade de Código e Mapeamento de Carreira

> **Projeto Acadêmico** desenvolvido para a disciplina de *Engenharia de Prompt e Aplicações em IA* no curso de Análise e Desenvolvimento de Sistemas (ADS) — Universidade Cruzeiro do Sul (2026).

---

## 🚀 Visão Geral do Projeto

O **Hostly AI** é um ecossistema SaaS full-stack corporativo concebido para solucionar uma das maiores lacunas do ensino tecnológico: a conversão de scripts laboratoriais acadêmicos em portfólios estratégicos de mercado. 

Através de uma integração nativa com o modelo de linguagem de última geração **Google Gemini (gemini-2.5-flash)**, a aplicação atua de forma consultiva, simulando as decisões técnicas de um **Arquiteto de Software** e as métricas de triagem de um **Tech Recruiter Sênior**. O estudante realiza o upload ou cola o código-fonte de seus projetos autorais na interface, e o pipeline de IA executa uma varredura semântica profunda para classificar a stack, avaliar boas práticas de Clean Code e sugerir roadmaps de estudo personalizados.

---

## 🛠️ Tecnologias e Arquitetura de Sistemas

O projeto foi construído utilizando um conjunto de tecnologias modernas e robustas para garantir performance, segurança e responsividade:

* **Camada de Apresentação (Frontend):** HTML5, Tailwind CSS (com diretrizes de *Premium Dark Mode* e componentes translúcidos baseados em *Glassmorphism UI*) e Jinja2 para renderização dinâmica de dados.
* **Camada de Regras de Negócio (Backend):** Python 3.12 com o microframework Flask gerenciando rotas RESTful, middlewares de proteção e controle de sessões.
* **Persistência Relacional (Database):** Banco de dados relacional MySQL/SQLite gerenciado com relacionamentos estruturados e integridade referencial por deleção em cascata (`ON DELETE CASCADE`).
* **Pipeline de Inteligência Artificial (Generative AI):** Google GenAI Client SDK integrado nativamente ao modelo **gemini-2.5-flash** alimentado por variáveis de ambiente isoladas.
* **Segurança da Informação:** Criptografia assimétrica via biblioteca `Flask-Bcrypt` para hashing seguro de credenciais antes da persistência física no banco de dados.

---

## 🧠 Engenharia de Prompt Aplicada

Para assegurar total estabilidade ao back-end em Flask e eliminar riscos de quebras na renderização de tela ou alucinações clássicas de LLMs, o time **GenAI** desenvolveu uma abordagem baseada em técnicas consolidadas de engenharia de prompt estruturada:

1.  **Role-Prompting:** O modelo é instruído no início de sua memória de contexto a assumir o papel e a persona estrita de um *Arquiteto de Software e Tech Recruiter Sênior*, garantindo que o tom do feedback seja corporativo e altamente técnico.
2.  **Output Format Constraints (JSON Mode):** Passagem do parâmetro explícito `response_mime_type="application/json"` no SDK do Gemini, forçando o retorno de um objeto JSON gramaticalmente perfeito. Isso elimina as crases delimitadoras de markdown (```json ... ```) e textos adicionais de introdução ou conclusão que quebrariam a desserialização do backend.
3.  **Zero-Shot Chain of Thought (CoT):** Instruções sequenciais sem exemplos prévios que forçam a IA a processar logicamente os pacotes importados, a complexidade ciclomática e a qualidade estrutural do código antes de emitir o parecer final nos campos do JSON.
4.  **Context Window Isolation:** O prompt de usuário utiliza delimitadores estritos (`-----`) para isolar o código enviado pelo aluno, impedindo falhas de injeção de prompt (*Prompt Injection*) contra o núcleo do sistema.

---

## 📋 Pré-requisitos para Execução Local

Antes de iniciar a aplicação na sua máquina, certifique-se de ter instalado:
* Python 3.10 ou superior
* MySQL Server (ou suporte local para SQLite configurado no arquivo `database.py`)
* Uma chave de API do Google AI Studio (`GEMINI_API_KEY`)

---

## 🔧 Instalação e Execução

Siga os passos abaixo no terminal do seu ambiente de desenvolvimento para rodar o projeto localmente:

### 1. Clonar o Repositório
```bash
git clone [https://github.com/DenilsonFerreiraDev/hostly_ai.git](https://github.com/DenilsonFerreiraDev/hostly_ai.git)
cd hostly_ai
python -m venv venv
# No Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# No Linux/Mac:
source venv/bin/activate
pip install -r requirements.txt
4. Configurar as Variáveis de Ambiente (.env)
Crie um arquivo chamado .env na raiz do projeto e preencha com as suas chaves e dados de conexão:
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=sua_senha_do_mysql
DB_NAME=hostly_ai
FLASK_SECRET_KEY=uma_chave_criptografica_aleatoria_aqui
GEMINI_API_KEY=Sua_Chave_Privada_Do_Google_AI_Studio
python database.py
python app.py
