# Importa as ferramentas do Flask
from flask import Flask, render_template, request 
# Importa a biblioteca para falar com APIs externas
import requests


# Cria a instância do seu site (o aplicativo)
app = Flask(__name__)

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
    chave_api = '118bc417716a14681a9e0e718b52b16a'
    # Monta o endereço da busca, injetando a chave e o nome do filme na URL
    url = f"https://api.themoviedb.org/3/search/movie?api_key={chave_api}&query={nome_do_filme}&language=pt-BR"
    # Faz a chamada real para a internet
    resposta = requests.get(url)
    # Converte o "textão" que a API manda em um dicionário Python
    dados = resposta.json()
    # Extrai apenas a lista de filmes da chave 'results'
    print(dados)
    lista_filmes = dados.get('results', [])
    # Devolve o HTML, mas agora preenchido com os filmes da pesquisa
    return render_template('index.html', filmes = lista_filmes, nome_usuario ='Caio')



# Define o que acontece ao acessar o endereço base do site
@app.route('/')
def index():
    chave_api = '118bc417716a14681a9e0e718b52b16a'
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
    chave_api = '118bc417716a14681a9e0e718b52b16a'
    url = f'https://api.themoviedb.org/3/movie/{id_filme}?api_key={chave_api}&language=pt-BR'
    resposta = requests.get(url)
    dados_filmes = resposta.json()
    return render_template('detalhes.html', filme=dados_filmes)

# Garante que o site só rode se este arquivo for executado diretamente
if __name__ == '__main__':
    # Inicia o servidor. O 'debug=True' reinicia o site sozinho se você mudar o código.
    app.run(debug=True)


