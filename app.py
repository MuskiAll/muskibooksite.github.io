from flask import Flask, render_template, request, redirect, session
from pushbullet import Pushbullet

app = Flask(__name__)
app.secret_key = 'muskibooks-secretkey'  # Defina uma chave secreta para uso na sessão

books = []
purchased_books = set()

users = []

pb = Pushbullet('o.426seWO5AGJMjxIeSqdMzbdXERr0aY86')

# Rota de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Verifique as credenciais do usuário
        if any(user['username'] == username and user['password'] == password for user in users):
            session['logged_in'] = True
            return redirect('/admin')
        else:
            return render_template('login.html', message='Credenciais inválidas')

    return render_template('login.html')

# Rota para deslogar
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# Rota raiz
@app.route('/')
def index():
    return render_template('index.html', books=books)

# Rota de administração
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        return redirect('/login')

    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        price = request.form['price']
        description = request.form['description']

        book = {
            'id': len(books) + 1,
            'title': title,
            'author': author,
            'price': price,
            'description': description,
            'payment_received': {}
        }

        for user in users:
            book['payment_received'][user['username']] = False

        books.append(book)
        return redirect('/')
    else:
        return render_template('admin.html', books=books, users=users)

# Rota de registro de usuários
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Verifique se o usuário já existe
        if any(user['username'] == username for user in users):
            return render_template('register.html', message='Nome de usuário já existe')

        # Crie um novo usuário
        user = {
            'username': username,
            'password': password
        }

        users.append(user)
        return redirect('/login')
    else:
        return render_template('register.html')

# Rota para leitura de livros
@app.route('/books/<int:book_id>/read')
def read_book(book_id):
    if not session.get('logged_in'):
        return redirect('/login')

    book = next((book for book in books if book['id'] == book_id), None)
    if not book:
        return redirect('/')

    if not book['payment_received'].get(session.get('username'), False):
        return redirect('/purchase/' + str(book_id))

    return render_template('read_book.html', book=book)

# Rota de compra de livro
@app.route('/purchase/<int:book_id>')
def purchase(book_id):
    if not session.get('logged_in'):
        return redirect('/login')

    book = next((book for book in books if book['id'] == book_id), None)
    if not book:
        return redirect('/')
    
    
    
    if book['payment_received'].get(session.get('username'), False):
        return redirect('/books/' + str(book_id) + '/read')

    return render_template('purchase.html', book=book)

# Rota para confirmar o pagamento
@app.route('/payment_confirmation', methods=['POST'])
def payment_confirmation():
    if not session.get('logged_in'):
        return redirect('/login')

    book_id = int(request.form['book_id'])
    book = next((book for book in books if book['id'] == book_id), None)
    if not book:
        return redirect('/')

    username = session.get('username')
    if not book['payment_received'].get(username, False):
        book['payment_received'][username] = True

        if all(received for received in book['payment_received'].values()):
            purchased_books.add(book_id)

    return redirect('/books/' + str(book_id) + '/read')

# Função para enviar notificação via Pushbullet
def push_notification(username, book_title):
    push_title = 'Pagamento Recebido'
    push_message = f'O usuário {username} fez o pagamento e pode acessar o livro "{book_title}"? Verifique se o pagamento foi recebido e acesse o site mrbarbecue7127.github.io/admin para permitir ou negar.'

    pb.push_note(push_title, push_message)

if __name__ == '__main__':
    app.run(debug=True)
