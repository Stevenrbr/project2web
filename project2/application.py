import os
from collections import deque
from flask import Flask, render_template, session, request, redirect
from flask_socketio import SocketIO, send, emit, join_room, leave_room

from helpers import login_required

app = Flask(__name__)
app.config["SECRET_KEY"] = "my secret key"
socketio = SocketIO(app)

channelsCreated = []

usersLogged = []

channelsMessages = dict()

@app.route("/")
@login_required
def index():


    return render_template("index.html", channels=channelsCreated)

@app.route("/signin", methods=['GET','POST'])
def signin():
    session.clear()
    if request.method == "POST":

        username = request.form.get("username")
        if username == 'secreto':
            username = ' '
        elif username == ' ':
            return render_template("error.html", message="Necesita nombre de usuario")
        print(username)

        if username in usersLogged:
            return render_template("error.html", message="El usuario ya existe elija otro nombre")
        usersLogged.append(username)
        session['username'] = username
        session.permanent = True

        return redirect("/")
    else:
        return render_template("signin.html")

@app.route("/logout", methods=['GET'])
def logout():

    try:
        usersLogged.remove(session['username'])
    except ValueError:
        pass

    session.clear()

    return redirect("/")

@app.route("/create", methods=['GET','POST'])
def create():

    if request.method == "POST":
        newChannel = request.form.get("channel")

        if newChannel in channelsCreated:
            return render_template("error.html", message="that channel already exists!")

        channelsCreated.append(newChannel)

        channelsMessages[newChannel] = deque()

        return redirect("/channels/" + newChannel)

    else:

        return render_template("index.html", channels = channelsCreated)

@app.route("/channels/<channel>", methods=['GET','POST'])
@login_required
def enter_channel(channel):

    session['current_channel'] = channel

    if request.method == "POST":

        return redirect("/")
    else:
        return render_template("channel.html", channels= channelsCreated, messages=channelsMessages[channel])

@socketio.on("joined", namespace='/')
def joined():

    room = session.get('current_channel')

    join_room(room)

    emit('status', {
        'userJoined': session.get('username'),
        'channel': room,
        'msg': session.get('username') + ' Se ha unido al chat'},
        room=room)

@socketio.on("left", namespace='/')
def left():
    room = session.get('current_channel')

    leave_room(room)

    emit('status', {
        'msg': session.get('username') + ' ha dejado el chat'},
        room=room)

@socketio.on('send message')
def send_msg(msg, timestamp):

    room = session.get('current_channel')


    if len(channelsMessages[room]) > 100:
        channelsMessages[room].popleft()

    channelsMessages[room].append([timestamp, session.get('username'), msg])

    emit('announce message', {
        'user': session.get('username'),
        'timestamp': timestamp,
        'msg': msg},
        room=room)
