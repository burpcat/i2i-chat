from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_socketio import SocketIO, join_room
from pymongo.errors import DuplicateKeyError

from db import get_user, save_user

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # for the login required decorator, redirects to the route where to login

socketio = SocketIO(app)  # Creating a SocketIO instance for the flask app

app.secret_key = 'some random secret key'


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/chat')
@login_required
def chat():
    username = request.args.get('username')  # used to fetch the data from the REST request
    room_id = request.args.get('room_id')

    if username and room_id:
        return render_template('chat.html', username=username, room_id=room_id)
    else:
        return redirect(url_for('home'))  # we can directly use redirect('/'), but url_for is more organised


@socketio.on('join_room')
def handle_join_room_event(data):
    app.logger.info(f"{data['username']} has joined the room {data['room_id']}")
    join_room(data['room_id'])
    socketio.emit('join_room_announcement', data)


@socketio.on('send_message')
def handle_send_message_event(data):
    app.logger.info(f"{data['username']} has sent {data['message']} to the room {data['room_id']}")
    socketio.emit('receive_message', data, room=data['room_id'])


# used by flask to store data in sessions
@login_manager.user_loader
def load_user(username):
    return get_user(username)


@app.route('/login', methods=['GET', 'POST'])
def login():

    if current_user.is_authenticated:
        return redirect(url_for('home'))

    message = ''

    if request.method == 'POST':
        username = request.form.get('username')
        password_input = request.form.get('password')
        user = get_user(username)
        if user and user.check_password(password_input):
            login_user(user)
            return redirect(url_for('home'))
        else:
            message = 'failed to login'

    return render_template('login.html', message=message)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    message = ''

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            save_user(username, email, password)
        except DuplicateKeyError:
            message = "User Exists"

        return redirect(url_for('home'))

    return render_template('signup.html', message=message)


if __name__ == '__main__':
    socketio.run(app, debug=True)
