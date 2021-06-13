from flask import Flask, jsonify, render_template, flash, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_required, login_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_cors import CORS, cross_origin
import os, json
from PIL import Image
import detector
from detector import shrek
from datetime import datetime

UPLOAD_FOLDER = '../data/imagefiles'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] =  'sqlite:///penis.db'
 #app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:shashank@34.122.172.85/data'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(64))
    email = db.Column(db.String(64), index = True, unique = True)
    password_hash = db.Column(db.String(256))
    points = db.Column(db.Integer)
    markers = db.relationship('Marker', backref='user', lazy=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))

    def __repr__(self):
        return email

class Marker(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    lat = db.Column(db.Float)
    lon = db.Column(db.Float)
    img = db.Column(db.Integer)
    description = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),
        nullable=False)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String(64))
    date = db.Column(db.DateTime)
    creator_id = db.Column(db.Integer)
    markers = db.Column(db.String(128))
    users = db.relationship('User', backref='group', lazy=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
        
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        desc = request.form['description']
        coords = (request.form['coords']).split('|')
        print(file, desc, coords)
        lat = coords[0]
        lon = coords[1]
        
        if file.filename == '':
            flash('No selected file')
            return redirect(url_for('index'))
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            img = Image.open(file)
            with open('../data/annotations.json', 'r+') as f:
                data = json.load(f)
                data['images'][0]['width'] = img.size[0]
                data['images'][0]['height'] = img.size[1]
                data['images'][0]['file_name'] = '../detector/static/imagefiles/' + filename
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()

            img.save('static/imagefiles/' + filename)
            headphone, name = shrek()

    
            user = User.query.get(current_user.id)
            user.points = user.points + 1
            marker = Marker(lat=lat, lon=lon, img='static/imagefiles/' + name, description=desc, user_id=user.id)
            db.session.add(marker)
            db.session.commit()

            return redirect(url_for('index'))

    return render_template('upload.html')

@app.route('/home', methods=['GET'])
def index():
    return render_template('home.html', markers=Marker.query.all())

@app.route('/organize', methods=['GET', 'POST'])
def organize():
    if request.method == 'POST':
        marker_id = request.form['marker_id']
        name = request.form['name']
        print(request.form['date'])
        date = datetime.strptime(request.form['date'], '%Y-%m-%d')
        creator_id = current_user.id
        user = User.query.get(creator_id)
        user.points = user.points + 2
        group = Group(creator_id=creator_id, markers=marker_id, date=date, name=name)
        db.session.add(group)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('organize.html', markers=Marker.query.all())

@app.route('/notifications', methods=['GET'])
def notifications():
    return render_template('notifications.html', markers=Marker.query.all(), groups=Group.query.all())

@app.route('/create', methods=['POST'])
@login_required
def create_group():
    pass

@app.route('/join', methods=['GET', 'POST'])
@login_required
def join_group():
    group_id = request.form['marker_id']
    user_id = current_user.id
    user = User.query.get(user_id)
    user.points = user.points + 4
    group = Group.filter_by(group_id=group_id).first()
    if group.user_ids != '':
        group.user_ids = group.user_ids + ','
    group.user_ids = group.user_ids + str('user_id')
    db.session.commit()

@app.route('/profile', methods=['GET'])
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
    
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):  
            login_user(user)
            return redirect(url_for('index'))
        else:
            error = "invalid credentials"

    return render_template(('login.html'), error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        password2 = request.form['password2']
        
        if email == '' or password == '':
            return render_template('register.html', error="Cannot be empty")
        
        if User.query.filter_by(email=email).count() > 0:
            error = "User already exists"
        else:
            try:
                db.session.add(User(name=name, email=email, password_hash=generate_password_hash(password), points=0))
                db.session.commit()
                return redirect(url_for('login'))
            except:
                db.session.rollback()

    return render_template('register.html', error=error)


if __name__ == '__main__':
    context = ('server.crt', 'server.key')
    app.run(port=5000, ssl_context='adhoc', host='0.0.0.0')