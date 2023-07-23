from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
from string import ascii_uppercase
import random

app = Flask(__name__)
app.config["SECRET_KEY"] = "ybnz272@32k#nkm3HFTGuyYWHJUW"
socketio = SocketIO(app)

rooms = {}
def generate_unique_code(length):
    while True:
        code = ""
        for i in range(length):
            code += random.choice(ascii_uppercase)
        if code not in rooms:
            break
    return code

#creating routes (home and room)
#home page route
@app.route("/", methods=["POST", "GET"])
def home():
    session.clear() 
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False) #return False if join doesn't exist
        create = request.form.get("create", False)

        #if name is not provided
        if not name:
            return render_template("home.html", error="Provide name !", code=code, name=name)
        
        #if joining without providing code
        if join != False and not code:
            return render_template("home.html", error="Provide room code !", code=code, name=name)
        
        room = code
        if create != False:
            room = generate_unique_code(5) #create new room with random unique code
            rooms[room] = {"members": 0, "messages": []} 
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist.", code=code, name=name)
        
        session["room"] = room #storing data in sessions (not permanent)
        session["name"] = name

        return redirect(url_for("room"))

    return render_template("home.html")

#chat room page route
@app.route("/room")
def room():
    room = session.get("room")
    #to prevent directly going to /room page without creating new room or entering existing room
    if room is None or session.get("name") is None or room not in rooms: 
        return redirect(url_for("home"))
    return render_template("room.html", code=room, messages=rooms[room]["messages"])

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return 
    
    content = {
        "name": session.get("name"),
        "message": data["data"]
    }
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name: #if niether name or room code is provided
        return
    if room not in rooms: #if invalid room code is entered
        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0: #if everyone left the room, we'll delete the room
            del rooms[room]
    
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left the room {room}")




if __name__ == "__main__":
    socketio.run(app, debug=True)   
    
#since we are using debug=True, we don't have to refresh everytime we make change to the code