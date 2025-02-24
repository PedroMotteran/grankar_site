from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'grankar'

# Conexão com o MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['carros_db']
carros_collection = db['carros']
clientes_collection = db['clientes']

# Configurações para upload de imagens
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Dados dos bancos
bancos = [
    {"nome": "Banco CNH Industrial", "taxa": 1.16},
    {"nome": "Banco Safra", "taxa": 1.59},
    {"nome": "Banco Bradesco", "taxa": 1.63},
    {"nome": "Banco do Brasil", "taxa": 1.50},
    {"nome": "Banco Itaú", "taxa": 1.55},
    {"nome": "Caixa Econômica", "taxa": 1.45},
    {"nome": "Banco Santander", "taxa": 1.60},
]

@app.route('/')
def index():
    carros = list(carros_collection.find())
    return render_template('index.html', carros=carros)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        senha = request.form['senha']
        if senha == "grankar":  # Senha fixa
            return redirect(url_for('admin', logged_in='true'))  # Redireciona com o parâmetro logged_in
        else:
            return "Senha incorreta. Tente novamente."
    return render_template('login.html')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    # Verificar se o usuário está logado (parâmetro logged_in na URL)
    if request.args.get('logged_in') != 'true':
        return redirect(url_for('login'))
    
    # Se o método for POST, processar o formulário
    if request.method == 'POST':
        if 'add_carro' in request.form:
            # Processar o upload de múltiplas imagens
            imagens = []
            if 'imagens' in request.files:
                files = request.files.getlist('imagens')  # Obter lista de arquivos
                for file in files:
                    if file and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(file_path)
                        imagens.append(filename)  # Salvar apenas o nome do arquivo

            # Criar o novo carro
            novo_carro = {
                "nome": request.form['nome'],
                "ano": request.form['ano'],
                "preco": float(request.form['preco']),
                "imagens": imagens,  # Lista de nomes das imagens
                "descricao": request.form['descricao']
            }
            carros_collection.insert_one(novo_carro)
        elif 'remover_carro' in request.form:
            carro_id = request.form['carro_id']
            carros_collection.delete_one({"_id": ObjectId(carro_id)})
    
    # Renderizar a página de administração
    carros = list(carros_collection.find())
    clientes = list(clientes_collection.find().sort('data_criacao', -1))
    return render_template('admin.html', carros=carros, clientes=clientes)

@app.route('/simular/<carro_id>', methods=['GET', 'POST'])
def simular(carro_id):
    carro = carros_collection.find_one({"_id": ObjectId(carro_id)})
    if request.method == 'POST':
        cliente = {
            "nome": request.form['nome'],
            "telefone": request.form['telefone'],
            "carro_nome": carro['nome']
        }
        clientes_collection.insert_one(cliente)
        return redirect(url_for('detalhes', carro_id=carro_id))
    return render_template('simular.html', carro=carro)

@app.route('/detalhes/<carro_id>')
def detalhes(carro_id):
    carro = carros_collection.find_one({"_id": ObjectId(carro_id)})
    return render_template('detalhes.html', carro=carro, bancos=bancos)

if __name__ == '__main__':
    app.run(debug=True)