# Importa as ferramentas do Flask
from flask import Flask, render_template, request, redirect, url_for 
# Importa a biblioteca para falar com APIs externas
import requests
from flask_sqlalchemy import SQLAlchemy
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

# Cria a instância do seu site (o aplicativo)
app = Flask(__name__)
# Configura o caminho do banco de dados (SQLite criará um arquivo chamado 'cinepy.db')
# Desativa um recurso de rastreamento que consome memória extra e não usaremos agora
# Cria a instância do banco de dados conectada ao seu app
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cinepy.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Favorito(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_filme = db.Column(db.Integer, unique=True, nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    poster = db.Column(db.String(200))

    def __repr__(self):
        return f'<Favorito {self.titulo}>'



GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

'''
Flask: O motor principal do site.

render_template: A função que lê arquivos HTML e permite enviar dados do Python para eles.

request: Serve para capturar dados que o usuário envia (como o nome do filme no formulário).

import requests: É quem faz a "viagem" até o servidor do TMDB para buscar os filmes.
'''


# Define que essa página só aceita envios de formulário (POST)
@app.route('/buscar', methods=['POST'])
def buscar():
    # Captura o texto que o usuário digitou no <input name="filme">
    nome_do_filme = request.form.get('filme')
    chave_api = TMDB_API_KEY
    # Monta o endereço da busca, injetando a chave e o nome do filme na URL
    url = f"https://api.themoviedb.org/3/search/movie?api_key={chave_api}&query={nome_do_filme}&language=pt-BR"
    # Faz a chamada real para a internet
    resposta = requests.get(url)
    # Converte o "textão" que a API manda em um dicionário Python
    dados = resposta.json()
    # Extrai apenas a lista de filmes da chave 'results'
    filmes = dados.get('results', [])
    if not filmes:
        return render_template('index.html', filmes=[], erro="Ops, Não encontramos nenhum filme com esse nome.")
    # Devolve o HTML, mas agora preenchido com os filmes da pesquisa
    return render_template('index.html', filmes=filmes, nome_usuario ='Caio')



# Define o que acontece ao acessar o endereço base do site
@app.route('/')
def index():
    chave_api = TMDB_API_KEY
    # URL diferente: aqui busco os filmes "popular" (em alta)
    url = f'https://api.themoviedb.org/3/movie/popular?api_key={chave_api}&language=pt-BR'
    resposta = requests.get(url)
    dados = resposta.json()
    print(dados)
    lista_popular = dados.get('results', [])
    # Renderiza o mesmo index.html, mas com os filmes populares logo de cara
    return render_template('index.html', filmes=lista_popular, nome_usuario='Caio')



@app.route('/filme/<int:id_filme>')
def detalhes(id_filme):
    chave_api = TMDB_API_KEY
    url = f'https://api.themoviedb.org/3/movie/{id_filme}?api_key={chave_api}&language=pt-BR'
    resposta = requests.get(url)
    dados_filmes = resposta.json()
    titulo = dados_filmes.get('title')
    prompt = f'Me conte uma curiosidade muita curta e interessante sobre os bastidores do filme {titulo}. Responda em português-BR e seja direto.'
    try:
        
        resposta_ia = client.models.generate_content(
            model="gemini-flash-latest", 
            contents=prompt
        )
        # IMPORTANTE: Use .text para extrair a string
        resposta_texto = resposta_ia.text 
    except Exception as e:
        print(f"ERRO REAL NO TERMINAL: {e}")
        resposta_texto = "A IA teve um soluço técnico. Verifique o terminal!"
    return render_template('detalhes.html', filme=dados_filmes, insight=resposta_texto)



@app.route('/favoritar/<int:id_filme>')
def favorito(id_filme):
    chave_api = TMDB_API_KEY
    url = f'https://api.themoviedb.org/3/movie/{id_filme}?api_key={chave_api}&language=pt-BR'
    resposta = requests.get(url)
    dados = resposta.json()
    novo_fav = Favorito(id_filme=id_filme, titulo=dados.get('title'), poster=dados.get('poster_path'))
    db.session.add(novo_fav)
    db.session.commit()
    return redirect(url_for('detalhes', id_filme=id_filme))



@app.route('/deletar/<int:id_filme>')
def deletar(id_filme):
    # 1. Procura o filme no banco pelo ID do TMDB
    filme_para_remover = Favorito.query.filter_by(id_filme=id_filme).first()
    # 2. Se ele existir, a gente deleta
    if filme_para_remover:
        db.session.delete(filme_para_remover)
        db.session.commit()
    # 3. Redireciona de volta para a página de favoritos
    return redirect(url_for('favoritos'))



@app.route('/favoritos')
def favoritos():
    meus_filmes = Favorito.query.all()
    return render_template('favoritos.html', filmes_favoritos=meus_filmes, nome_usuario='Caio')



@app.route('/genero/<int:id_genero>')
def ver_genero(id_genero):
    chave_api = TMDB_API_KEY
    url = f'https://api.themoviedb.org/3/discover/movie?api_key={chave_api}&with_genres={id_genero}&language=pt-BR'
    resposta = requests.get(url)
    dados_filmes = resposta.json()
    filmes_genero = dados_filmes.get('results', [])
    return render_template('index.html', filmes=filmes_genero, nome_usuario='Caio')



@app.route('/pergunta/<int:id_filme>', methods=['POST'])
def perguntar(id_filme):
    pergunta = request.form.get('pergunta_usuario') 
    # Buscamos o filme de novo para dar contexto à IA
    chave_api = TMDB_API_KEY
    url = f'https://api.themoviedb.org/3/movie/{id_filme}?api_key={chave_api}&language=pt-BR'
    dados_filmes = requests.get(url).json()
    titulo = dados_filmes.get('title')
    # Criamos um "Super Prompt" que une o filme + a dúvida do usuário
    contexto = f"Você é um especialista em cinema. O usuário está vendo o filme {titulo}. Responda à pergunta dele: {pergunta}"
    try:
        resposta_ia = client.models.generate_content(
            model="gemini-flash-latest", 
            contents=contexto # ou prompt
        )
        # IMPORTANTE: Use .text para extrair a string
        resposta_texto = resposta_ia.text 
    except Exception as e:
        print(f"ERRO REAL NO TERMINAL: {e}")
        resposta_texto = "A IA teve um soluço técnico. Verifique o terminal!"
    # Voltamos para a página de detalhes, mas agora levando a resposta do chat
    return render_template('detalhes.html', filme=dados_filmes, insight=resposta_texto)



# Garante que o site só rode se este arquivo for executado diretamente
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Inicia o servidor. O 'debug=True' reinicia o site sozinho se você mudar o código.
    app.run(debug=True)


