from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
import os
from dotenv import load_dotenv
from database import obter_conexao
from google import genai
from google.genai import types
import json

# Carrega as variáveis do .env
load_dotenv()

# Inicializa a instância do Flask primeiro para que os filtros possam utilizá-la
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Filtro customizado para converter string JSON para dicionário no HTML
@app.template_filter('from_json')
def from_json_filter(value):
    if isinstance(value, str):
        return json.loads(value)
    # Se já for um dicionário (MySQL Connector às vezes faz isso com campos JSON)
    return value

# Inicializa o Bcrypt para criptografia de senhas
bcrypt = Bcrypt(app)

# Inicializa o cliente do Gemini (ele busca a chave GEMINI_API_KEY automaticamente do .env)
client = genai.Client()

# Definição do prompt de sistema para análise de carreira
PROMPT_SISTEMA = """
Você é um Arquiteto de Software e Tech Recruiter Sênior. Sua função é analisar o código-fonte fornecido por um estudante e mapear o perfil técnico dele, gerando um guia de carreiras personalizado.

Você deve analisar:
1. A complexidade do código, boas práticas e padrões de arquitetura.
2. Tecnologias, linguagens e paradigmas utilizados.

Você DEVE retornar a resposta ESTRITAMENTE no formato JSON, sem crases de marcação markdown (como ```json) e sem textos adicionais fora do objeto. O formato deve seguir exatamente esta estrutura:
{
    "pontos_fortes": ["Ponto 1", "Ponto 2"],
    "tecnologias_detectadas": ["Tech 1", "Tech 2"],
    "carreira_sugerida": "Nome da Carreira (Ex: Desenvolvedor Backend Python)",
    "justificativa": "Texto explicando o porquê dessa sugestão baseado no código analisado.",
    "proximos_steps": ["O que estudar a seguir 1", "O que estudar a seguir 2"]
}
"""

# ROTA INICIAL (Redireciona para o login ou dashboard)
@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# ROTA DE CADASTRO
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        if not nome or not email or not senha:
            flash("Por favor, preencha todos os campos!", "danger")
            return redirect(url_for('cadastro'))
        
        # Gera o hash seguro da senha
        senha_hash = bcrypt.generate_password_hash(senha).decode('utf-8')
        
        conexao = obter_conexao()
        if conexao:
            cursor = conexao.cursor()
            try:
                comando = "INSERT INTO usuarios (nome, email, senha_hash) VALUES (%s, %s, %s)"
                cursor.execute(comando, (nome, email, senha_hash))
                conexao.commit()
                flash("Conta criada com sucesso! Faça seu login.", "success")
                return redirect(url_for('login'))
            except Exception as erro:
                flash("Este e-mail já está cadastrado.", "danger")
                print(f"Erro no cadastro: {erro}")
            finally:
                cursor.close()
                conexao.close()
                
    return render_template('cadastro.html')

# ROTA DE LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        
        conexao = obter_conexao()
        if conexao:
            cursor = conexao.cursor(dictionary=True)
            comando = "SELECT * FROM usuarios WHERE email = %s"
            cursor.execute(comando, (email,))
            usuario = cursor.fetchone()
            
            cursor.close()
            conexao.close()
            
            # Compara a senha digitada com o hash salvo no banco
            if usuario and bcrypt.check_password_hash(usuario['senha_hash'], senha):
                session['usuario_id'] = usuario['id']
                session['usuario_nome'] = usuario['nome']
                return redirect(url_for('dashboard'))
            else:
                flash("E-mail ou senha incorretos.", "danger")
                
    return render_template('login.html')

# ROTA DO DASHBOARD ATUALIZADA (Busca os projetos do aluno logado)
@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        flash("Faça login para acessar esta página.", "warning")
        return redirect(url_for('login'))
        
    usuario_id = session['usuario_id']
    projetos_usuario = []
    
    conexao = obter_conexao()
    if conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            # Seleciona os projetos salvos pelo usuário para listar na lateral
            comando = "SELECT id, titulo, linguagem_principal, criado_em FROM projetos WHERE usuario_id = %s ORDER BY criado_em DESC"
            cursor.execute(comando, (usuario_id,))
            projetos_usuario = cursor.fetchall()
        except Exception as erro:
            print(f"Erro ao buscar projetos: {erro}")
        finally:
            cursor.close()
            conexao.close()
        
    return render_template('dashboard.html', nome=session['usuario_nome'], projetos=projetos_usuario)

# ROTA DE LOGOUT
@app.route('/logout')
def logout():
    session.clear()
    flash("Você saiu do sistema.", "info")
    return redirect(url_for('login'))

# --- ROTA: SALVAR PROJETO E MANDAR PARA O BANCO (COM INTEGRAÇÃO GEMINI) ---
@app.route('/salvar-projeto', methods=['POST'])
def salvar_projeto():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
        
    titulo = request.form.get('titulo')
    linguagem = request.form.get('linguagem')
    codigo = request.form.get('codigo')
    usuario_id = session['usuario_id']
    
    if not titulo or not codigo:
        flash("Preencha o título e o conteúdo do código!", "danger")
        return redirect(url_for('dashboard'))
        
    conexao = obter_conexao()
    if conexao:
        cursor = conexao.cursor()
        try:
            # 1. Salva o projeto do estudante no MySQL
            comando = """
                INSERT INTO projetos (usuario_id, titulo, conteudo_codigo, linguagem_principal) 
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(comando, (usuario_id, titulo, codigo, linguagem))
            conexao.commit()
            
            # Pega o ID do projeto que acabou de ser inserido
            projeto_id = cursor.lastrowid
            
            # 2. CHAMADA DA IA DO GEMINI
            # Usamos o modelo gemini-2.5-flash que é ideal, rápido e eficiente para tarefas de texto/código
            resposta_ia = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=f"Analise o seguinte código do estudante. Título do projeto: {titulo}. Código:\n\n{codigo}",
                config=types.GenerateContentConfig(
                    system_instruction=PROMPT_SISTEMA,
                    response_mime_type="application/json" # Força o modelo a responder em JSON estruturado
                )
            )
            
            # O texto da resposta já vem formatado como uma string JSON válida
            resultado_json = resposta_ia.text
            
            # 3. Salva a análise da IA na tabela analises_carreira
            comando_analise = """
                INSERT INTO analises_carreira (projeto_id, resultado_ia)
                VALUES (%s, %s)
            """
            cursor.execute(comando_analise, (projeto_id, resultado_json))
            conexao.commit()
            
            flash("Projeto hospedado e analisado pela IA com sucesso!", "success")
            return redirect(url_for('dashboard'))
            
        except Exception as erro:
            print(f"Erro ao salvar projeto ou integrar com IA: {erro}")
            flash("Erro interno ao processar o projeto ou chamar a IA.", "danger")
        finally:
            cursor.close()
            conexao.close()
            
    return redirect(url_for('dashboard'))

# --- ROTA: VISUALIZAR UM PROJETO ESPECÍFICO ---
@app.route('/projeto/<int:id>')
def visualizar_projeto(id):
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
        
    conexao = obter_conexao()
    projeto = None
    analise = None
    
    if conexao:
        cursor = conexao.cursor(dictionary=True)
        try:
            # Garante que o aluno só veja o projeto se ele for o dono (segurança extra)
            comando_projeto = "SELECT * FROM projetos WHERE id = %s AND usuario_id = %s"
            cursor.execute(comando_projeto, (id, session['usuario_id']))
            projeto = cursor.fetchone()
            
            if projeto:
                # Tenta buscar a análise da IA salva para esse projeto
                comando_analise = "SELECT resultado_ia FROM analises_carreira WHERE projeto_id = %s"
                cursor.execute(comando_analise, (id,))
                analise = cursor.fetchone()
        except Exception as erro:
            print(f"Erro ao detalhar projeto: {erro}")
        finally:
            cursor.close()
            conexao.close()
            
    if not projeto:
        flash("Projeto não encontrado ou acesso não autorizado.", "danger")
        return redirect(url_for('dashboard'))
        
    return render_template('projeto.html', nome=session['usuario_nome'], projeto=projeto, analise=analise)

if __name__ == '__main__':
    app.run(debug=True)