from flask import Flask , render_template , url_for , request , redirect , flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime , date
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField ,DateField , SelectField
from wtforms.validators import InputRequired, Length , ValidationError , Email
from flask_login import UserMixin , login_user , LoginManager , login_required , logout_user , current_user
from flask_bcrypt import Bcrypt
from flask_wtf.file import FileField , FileAllowed
import os , random
import requests , json
from werkzeug.utils import secure_filename
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

ADZUNA_APP_ID = "640b04ec"
ADZUNA_APP_KEY = "ed5241af76c80eea71618cdfd4997577"

def get_jobs_from_api(query):

    url = "https://api.adzuna.com/v1/api/jobs/in/search/1"
    params = {
        "app_id":ADZUNA_APP_ID,
        "app_key":ADZUNA_APP_KEY,
        "what":query,
        "where" : "India" ,
        "results_per_page" : 20
    }
    response = requests.get(url , params=params)
    if response.status_code == 200:
        data = response.json()
        return data.get("results" , [])
    return []
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(user, int(user_id))

class user(db.Model , UserMixin):
    id = db.Column(db.Integer , primary_key=True)
    username = db.Column(db.String(20) , nullable=False , unique=True)
    password = db.Column(db.String(200) , nullable=False)
    email = db.Column(db.String(200) , nullable = False , unique=True)
    profile_pic = db.Column(db.String(200) , nullable=True, default=None)
class learning_path(db.Model):
    id = db.Column(db.Integer , primary_key = True)
    role = db.Column(db.String(100) , nullable = True)
    description = db.Column(db.Text)
class LearningTopic(db.Model):
    id = db.Column(db.Integer , primary_key = True)
    path_id = db.Column(db.Integer , db.ForeignKey('learning_path.id') , nullable = False)
    title = db.Column(db.String(150) , nullable = False)
    description = db.Column(db.Text)
    details= db.Column(db.Text)
    stage = db.Column(db.Integer , nullable = False)
class MockTest(db.Model):
    id = db.Column(db.Integer , primary_key = True)
    title = db.Column(db.String(100), nullable = False)
    category = db.Column(db.String(50) , nullable = False)
    difficulty = db.Column(db.String(20) , nullable = False)
    duration = db.Column(db.Integer , nullable = False)
    total_questions = db.Column(db.Integer , nullable = False)

    questions = db.relationship(
        'Questions',
        backref = 'test',
        lazy = True ,# this controls when the questions are loaded from the databases.
        cascade = 'all , delete-orphan'
    )
class Questions(db.Model):
    id = db.Column(db.Integer , primary_key = True)
    question = db.Column(
        db.String(500),
        nullable = False 
    )
    option_a = db.Column(db.String(200) , nullable = False)
    option_b = db.Column(db.String(200) , nullable = False)
    option_c = db.Column(db.String(200) , nullable = False)
    option_d = db.Column(db.String(200) , nullable = False)

    answer = db.Column(
        db.String(1),
        nullable = False
    )

    test_id =db.Column(
        db.Integer ,
        db.ForeignKey('mock_test.id'),
        nullable = False
    )
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired() , Length(min= 2 , max=30)], render_kw={"placeholder": "Username"})
    email = StringField('Eamil' , validators =[InputRequired() , Length(min = 2 , max = 100)] , render_kw = {"placeholder" : "email"})
    password = PasswordField('Password', validators=[InputRequired() , Length(min= 2 , max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField("Register")
    def validate_email(self , email):
        existing_email = user.query.filter_by(
            email=email.data).first()
        if existing_email:
            raise ValidationError(
                "email already exist."
            )
    def validate_username(self , username):
        existing_username = user.query.filter_by(
            username=username.data).first()
        if existing_username:
            raise ValidationError(
                "user name already exist."
            )
class LoginForm(FlaskForm):
    email = StringField('email', validators=[InputRequired() , Length(min= 2 , max=100)], render_kw={"placeholder": "email"})
    password = PasswordField('Password', validators=[InputRequired() , Length(min= 2 , max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Login") 

class Todo(db.Model):
    id = db.Column(db.Integer , primary_key=True)
    content = db.Column(db.String(200) , nullable=False)
    date_created = db.Column(db.DateTime , default=datetime.utcnow)
    due_date = db.Column(db.Date , nullable=True)
    priority = db.Column(db.String(20) , default="Meduim")
    complete = db.Column(db.Boolean , default = False)
    user_id = db.Column(db.Integer , db.ForeignKey('user.id'),nullable = False)

    def __repr__(self):
        return '<Task %r>' %self.id
class profileForm(FlaskForm):
    username = StringField('username' , validators = [InputRequired() , Length(min= 2 , max=30)])
    email = StringField('email' , validators = [InputRequired() , Length(min = 2 , max= 100)])
    profile_pic = FileField("profile picture" , validators =[FileAllowed(["jpg", "jpeg", "png"])])
    submit = SubmitField("Update Profile")
class TaskForm(FlaskForm):
    content = StringField("Task" , validators =[InputRequired() , Length(min=2 , max=100)] , render_kw = {"placeholder":"Enter task"})
    due_date = DateField("Due Date" , format = "%Y-%m-%d" , render_kw={"type":"date"})
    priority = SelectField("priority" , choices = [("High" , "🔴 High"),("Medium", "🟡 Medium"),
                                                    ("Low", "🟢 Low")] , default = "Meduim")

    submit = SubmitField("Add Task")
@app.route('/')
def home():
    return render_template("home.html")
@app.route('/register' , methods = ['POST' , 'GET'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form=RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = user(username = form.username.data , email = form.email.data , password = hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html' , form=form)
@app.route('/login' , methods = ['POST' , 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if  form.validate_on_submit():
        user_new = user.query.filter_by(email = form.email.data).first()
        print(user_new)
        if user_new:
            if bcrypt.check_password_hash(user_new.password , form.password.data):
                login_user(user_new)
                return redirect(url_for('home'))
    return render_template('login.html' , form=form)
@app.route('/logout' , methods = ['POST'])
def logout():
    logout_user()
    return redirect(url_for('login'))
def import_mock_tests():
    with open("data/mock_tests.json" , "r") as file:
        data = json.load(file)
    for test_data in data:
        test = MockTest(
            title = test_data['title'],
            category = test_data['category'],
            difficulty = test_data['difficulty'],
            duration = test_data['duration'],
            total_questions = test_data['total_questions']
        )
        db.session.add(test)
        db.session.flush()
        for question_data in test_data['questions']:
            question = Questions(
                question = question_data['question'],
                option_a = question_data['option_a'],
                option_b = question_data['option_b'],
                option_c = question_data['option_c'],
                option_d = question_data['option_d'],
                answer = question_data['answer'],
                test_id = test.id
            )
            db.session.add(question)
    db.session.commit()
@app.route('/import-mock-tests')
def import_mock_tests_route():
    import_mock_tests()
    return "mock tests imported successfully"
@app.route('/mock-tests')
@login_required
def mock_tests():
    search = request.args.get('search' ,'')
    if search:
        categories = db.session.query(
                    MockTest.category
                ).filter(MockTest.category.ilike(f'%{search}%')).distinct().all()
    else:
        categories = db.session.query(
            MockTest.category
        ).distinct().all()
    print(categories)
    return render_template(
        'mock.html',
        categories = categories
    )
@app.route('/category-tests/<category>')
def category_tests(category):
    tests = MockTest.query.filter_by(category = category).all()
    return render_template(
        'category.html',
        tests = tests,
        category = category,
    )
@app.route('/start-mock-test/<test_id>',methods = ['GET' , 'POST'])
def start_mock_test(test_id):
    test = MockTest.query.get_or_404(test_id)
    questions = Questions.query.filter_by(
        test_id = test.id
    ).all()
    questions = random.sample(questions , 20)
    if request.method == 'POST':
        score = 0
        for question in questions:
            selected_answer = request.form.get(
                f'question_{question.id}'
            )
            if selected_answer == question.answer:
                score += 1
        return render_template(
            'result.html',
            test = test,
            score = score,
            total = len(questions)
        )
    return render_template(
        'take_test.html',
        test=test,
        questions = questions
    )
@app.route('/profile' , methods = ['POST' , 'GET'])
@login_required
def profile():
    form = profileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        if request.form.get('remove_profile'):
            current_user.profile_pic = None
        elif form.profile_pic.data:
            picture = form.profile_pic.data
            filename = secure_filename(picture.filename)
            picture.save (
                os.path.join(app.config["UPLOAD_FOLDER"] , filename)
            )
            current_user.profile_pic = filename
        db.session.commit()
        return redirect(url_for('profile'))
    form.username.data = current_user.username
    form.email.data = current_user.email
    return render_template('profile.html' , form=form , user = current_user)

@app.route('/task' , methods=['POST' , 'GET'])
def add():
    form = TaskForm()

    if form.validate_on_submit():
        new_task = Todo(
        content = form.content.data,
        user_id = current_user.id,
        due_date = form.due_date.data,
        priority = form.priority.data
        
        )
        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect('/task')
        except Exception as e:
            return str(e)
    tasks = Todo.query.order_by(Todo.date_created).all()
    return render_template('planner.html' , tasks = tasks , form = form)
@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = Todo.query.get_or_404(id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/task')
    except:
            return "There was an issue deleting your task"  
@app.route('/update/<int:id>' , methods=['POST' , 'GET'])  

def update(id):
    task = Todo.query.get_or_404(id)
    if  request.method == 'POST':
        task.content = request.form['content']
        try:
            db.session.commit()
            return redirect('/task')
        except:
            return "There was an issue updating your task"  
       
    else:
        return render_template('update.html' , task = task)
@app.route('/planner' , methods = ['POST' , 'GET'])
@login_required
def planner():
    form = TaskForm()
    tasks = Todo.query.filter_by( user_id = current_user.id).order_by(Todo.date_created).all()
    return render_template('planner.html', tasks=tasks , form = form)
@app.route('/complete/<int:id>')
@login_required
def complete(id):
    task = Todo.query.get_or_404(id)
    task.complete = True
    db.session.commit()
    return redirect(url_for('planner'))
@app.route("/jobs")
@login_required
def jobs():
    query = request.args.get("q" , "")
    jobs = []
    jobs = get_jobs_from_api(query)
    return render_template("job.html" , jobs = jobs , query = query)
@app.route("/add-learning-data")
@login_required
def add_learning_data():
    url = "https://raw.githubusercontent.com/Setharasipalli/careerdeck-data/main/learning_paths.json"
    response = requests.get(url)
    if response.status_code != 200:
        return "Failed to fetch learning paths"
    data = response.json()
    for path_data in data:
        path = learning_path(
            role = path_data["role"],
            description = path_data["description"]
        )
        db.session.add(path)
        db.session.flush()
        for stage_data in path_data["stages"]:
            for topic in stage_data["topics"]:
                new_topic = LearningTopic(
                path_id = path.id ,
                title = topic['title'] ,
                description = topic['description'],
                details = "\n".join(topic['details']),
                stage = stage_data['stage']
                )
                db.session.add(new_topic)  
    db.session.commit()
    return redirect(url_for('learning_paths'))
@app.route('/learning-paths')
@login_required
def learning_paths():
    search = request.args.get('search' , '')
    if search:
        paths = learning_path.query.filter(learning_path.role.ilike(f'%{search}%')).all()
    else:
        paths = learning_path.query.all()

    return render_template(
        'learning_paths.html',
        paths=paths,
        search = search
    )
@app.route('/learning-path/<int:path_id>')
@login_required
def learning_path_detail(path_id):
    path = learning_path.query.get_or_404(path_id)
    topics = LearningTopic.query.filter_by(
        path_id = path.id
    ).order_by(
        LearningTopic.stage ,
        LearningTopic.id
    ).all()
    return render_template(
        "roadmap.html" ,
        path = path,
        topics = topics
    )
@app.route('/GetStarted')
def get_started():
    return render_template('GetStarted.html')

if __name__ == "__main__":
    import os
    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
