from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
import os
import enum
import secrets

#Define possible categories of tasks
class MyEnum(enum.Enum):
    todo="To Do"
    progress="In Progress"
    done="Completed"

#Initialize the application and configure
app = Flask(__name__)
path=os.path.join(os.getcwd(), 'todo.db')
app.config['SECRET_KEY']=secrets.token_hex(16)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+path

#Initialize a database
db = SQLAlchemy(app)

#Define Schema for User
class User(db.Model):
    user_id=db.Column(db.Integer, primary_key=True)
    name=db.Column(db.String(50))
    username=db.Column(db.String(20))
    password=db.Column(db.String(30))

#Define Schema for Task
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    description=db.Column(db.Text)
    category = db.Column(db.Enum(MyEnum))
    user=db.Column(db.Integer, db.ForeignKey(User.user_id))

#Define the home route
@app.route("/")
def home():
    #If a user is already logged in, load user's tasks
    current_user=session.get('user_id')
    if current_user:
        todo=Todo.query.filter_by(user=current_user,category=MyEnum.todo).all()
        progress=Todo.query.filter_by(user=current_user,category=MyEnum.progress).all()
        done=Todo.query.filter_by(user=current_user,category=MyEnum.done).all() 
        name_u=User.query.filter_by(user_id=current_user).first().name
    
    #If there is no user, initialize as empty
    else:
        todo,progress, done=[], [],[]
        name_u=""

    #Return the webpage
    return render_template("base.html", todo=todo,progress=progress,done=done, session=session, name=name_u)

#Route to log in
@app.route("/login", methods=["POST"])
def login():
    #Get all information from the form
    username=request.form.get("username")
    password=request.form.get("password")

    #Initialize error variable
    error=None

    #Find user with the credentials 
    user=User.query.filter_by(username=username).first()

    #If there is no such user or incorrect password, add error
    if user is None:
        error='Incorrect username'
    elif not check_password_hash(user.password, password):
        error='Incorrect password'
    
    #If no error occured, update session data
    if error is None:
        session.clear()
        session['user_id']=user.user_id
    
    #Print error 
    print(error)

    #Go to the homepage
    return redirect(url_for("home"))

#Route for user registering
@app.route("/register", methods=["POST"])
def register():
    #Get all information
    username=request.form.get("username")
    name=request.form.get("name")
    password=generate_password_hash(request.form.get("password"))

    #Initialize error variable
    error=None
    
    #If any information is missing or a user already exists, write error
    if not username or not name or not password:
        error="One of the fields is missing"
    else:
        try:
            new_user=User(name=name, username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
        except:
            error="User already registered!"
    
    #Print error
    print(error)

    #Go to the homepage
    return redirect(url_for("home"))

#Route for log out
@app.route("/logout")
def logout():
    #Clear session information (with user_id)
    session.clear()

    #Go to the homepage
    return redirect(url_for("home"))

#Route to add new tasks
@app.route("/add", methods=["POST"])
def add():
    
    #Retrieve the data from the form
    title = request.form.get("title")
    description=request.form.get("description")
    category=request.form.get("category")
    user=session['user_id']
    
    #Create a new instance of the Task
    new_todo = Todo(title=title, description=description, category=category, user=user)

    #Add to the table
    db.session.add(new_todo)
    db.session.commit()

    #Go to the homepage
    return redirect(url_for("home"))

#Route for updating the task to the right (To Do --> Progress --> Done)
@app.route("/updater/<int:todo_id>")
def updater(todo_id):
    
    #Find the updated task
    todo = Todo.query.filter_by(id=todo_id).first()

    #Change the category
    if todo.category==MyEnum.todo:
        todo.category=MyEnum.progress
    elif todo.category==MyEnum.progress:
        todo.category=MyEnum.done
    elif todo.category==MyEnum.done:
        todo.category=MyEnum.todo

    #Commit changes
    db.session.commit()

    #Go back to the homepage
    return redirect(url_for("home"))

#Route for updating the task to the left (To Do <-- Progress <-- Done)
@app.route("/updatel/<int:todo_id>")
def updatel(todo_id):
    #Find the task
    todo = Todo.query.filter_by(id=todo_id).first()

    #Update the category
    if todo.category==MyEnum.todo:
        todo.category=MyEnum.done
    elif todo.category==MyEnum.progress:
        todo.category=MyEnum.todo
    elif todo.category==MyEnum.done:
        todo.category=MyEnum.progress

    #Commit changes
    db.session.commit()

    #Go back to the homepage
    return redirect(url_for("home"))

#Route for deleting tasks
@app.route("/delete/<int:todo_id>")
def delete(todo_id):
    #Find the task by id
    todo = Todo.query.filter_by(id=todo_id).first()

    #Delete and commit
    db.session.delete(todo)
    db.session.commit()

    #Go back to the homepage
    return redirect(url_for("home"))

#Before the app runs
@app.before_first_request
def create_table():
    #Create all tables in case they do not exist
    db.create_all()

    
if __name__ == "__main__":
    #Run app
    app.run(debug=True)