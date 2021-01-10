from random import shuffle
import json

from flask import Flask, render_template, request
from flask_wtf import FlaskForm
from wtforms import StringField, HiddenField, RadioField, SelectField
from wtforms.validators import InputRequired, Length
from flask_sqlalchemy import SQLAlchemy
import flask_migrate

from days_of_week import week
from lesson_start_time import lesson_start_time


class UserForm(FlaskForm):
    name = StringField('Вас зовут', [InputRequired()])
    tel = StringField('Ваш телефон', [InputRequired(), Length(min=5, max=25)])
    client_weekday = HiddenField('День недели')
    client_time = HiddenField('Время записи')
    client_teacher = HiddenField('Преподаватель')
    goal = RadioField(
        'Какая цель занятий?', 
        choices=[
            ('travel', 'Для путешествий'), 
            ('study', 'Для школы'),
            ('work', 'Для работы'),
            ('relocate', 'Для переезда')
            ])
    time = RadioField(
        'Сколько времени есть?',
        choices=[
            ('1-2', '1-2 часа в&nbsp;неделю'),
            ('3-5', '3-5 часов в&nbsp;неделю'),
            ('5-7', '5-7 часов в&nbsp;неделю'),
            ('7-10', '7-10 часов в&nbsp;неделю')
            ])
    sorting = SelectField(
        'Порядок сортировки', 
        choices=[
            ('4', 'В случайном порядке'),
            ('3', 'Сначала лучшие по рейтингу'),
            ('1', 'Сначала дорогие'), 
            ('2', 'Сначала недорогие')
            ])


app = Flask(__name__)
db = SQLAlchemy(app)
app.secret_key = 'random_string'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
migrate = flask_migrate.Migrate(app, db)


class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.Integer, primary_key=True)
    data_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String, nullable=False)
    about = db.Column(db.String, nullable=False)
    rating = db.Column(db.Float, nullable=False)
    picture = db.Column(db.String, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    goals = db.Column(db.String, nullable=False)
    free = db.Column(db.JSON, nullable=False)
    booking = db.relationship("Booking")


class Booking(db.Model):
    __tablename__ = 'booking'
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey('teachers.id'))
    profile = db.relationship("Teacher")
    day = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)


class Request(db.Model):
    __tablename__ = 'requests'
    id = db.Column(db.Integer, primary_key=True)
    goal = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    tel = db.Column(db.Integer, nullable=False)


@app.route('/')
def index():
    teachers = db.session.query(Teacher).all()
    random_card = [i for i in range(0, len(teachers))]
    shuffle(random_card)
    output = render_template(
        'index.html', 
        random_card=random_card,
        teachers=teachers
        )
    return output


@app.route('/all/', methods=['GET', 'POST'])
def all_teachers():
    teachers = json_to_py_teachers()
    form = UserForm()
    sorting = form.sorting.data
    if request.method == 'GET' or sorting == '4':
        random_card = [i for i in range(0, len(teachers))]
        shuffle(random_card)
        output = render_template(
            'all.html', 
            teachers=teachers,
            sort_list=random_card,
            form=form
            )
        return output
    elif sorting == '1' or sorting == '2':
        sort_list = []
        price = []
        price_edit = []
        for i in teachers:
            price.append(i['price'])
        for i in price:
            if i not in price_edit:
                price_edit.append(i)
        if sorting == '1':
            price = sorted(price_edit, reverse=True)
            for i in price:
                for j in teachers:
                    if i == j['price']:
                        sort_list.append(j['id'])
            output = render_template(
                'all.html',
                teachers=teachers,
                sort_list=sort_list,
                form=form
            )
            return output
        elif sorting == '2':
            price = sorted(price_edit)
            for i in price:
                for j in teachers:
                    if i == j['price']:
                        sort_list.append(j['id'])
            output = render_template(
                'all.html',
                teachers=teachers,
                sort_list=sort_list,
                form=form
            )
            return output
    elif sorting == '3':
        rating = []
        rating_edit = []
        sort_list = []
        for i in teachers:
            rating.append(i['rating'])
        for i in rating:
            if i not in rating_edit:
                rating_edit.append(i)
        rating = sorted(rating_edit, reverse=True)
        for i in rating:
            for j in teachers:
                if i == j['rating']:
                    sort_list.append(j['id'])
        output = render_template(
            'all.html',
            teachers=teachers,
            sort_list=sort_list,
            form=form
        )
        return output
    else:
        return '<h2>Сначала задайте параметры сортировки</h2>'


@app.route('/goals/<goal>/')
def all_goals(goal):
    content = db.session.query(Teacher).all()
    goal_req = None
    for i in content:
        if goal in i.goals.split(','):
            goal_req = goal
            break
    if goal_req is None:
        return '<h2>Задайте правильную категорию</h2>'
    teachers_edited = []
    rating = []
    rating_edit = []
    for i in content:
        goals = i.goals.split(',')
        if goal in goals:
            teachers_edited.append(i)
    for i in teachers_edited:
        rating.append(i.rating)
    for i in rating:
        if i not in rating_edit:
            rating_edit.append(i)
    rating = sorted(rating_edit, reverse=True)
    teachers = []
    for i in rating:
        for j in teachers_edited:
            if i == j.rating:
                teachers.append(j)
    goals = json_to_py_goals()
    output = render_template(
        'goal.html',
        goals=goals,
        goal=goal_req,
        teachers=teachers
    )
    return output


@app.route('/profiles/<profile_id>/')
def all_profiles(profile_id):
    teacher = db.session.query(Teacher).all()
    content = None
    for i in teacher:
        if i.data_id == int(profile_id):
            content = i
            break
    if content is None:
        return render_template('404.html'), 404
    goals = json_to_py_goals()
    output = render_template(
        'profile.html', 
        content=content,
        goals=goals
        )
    return output


@app.route('/request/')
def reception_of_request():
    form = UserForm()
    output = render_template(
        'request.html',
        form=form
        )
    return output


@app.route('/request_done/', methods=["GET", "POST"])
def requests_done():
    if request.method == 'POST':
        goals = json_to_py_goals()
        form = UserForm()
        goal = form.goal.data
        time = form.time.data
        name = form.name.data
        tel = form.tel.data
        if time == '1-2':
            hours = ' часа в неделю'
        else:
            hours = ' часов в неделю'
        data = {
            'goal': goal,
            'time': time,
            'name': name,
            'tel': tel
        }
        request_json(data)
        output = render_template(
            'request_done.html',
            goal=goal,
            goals=goals,
            time=time,
            tel=tel,
            name=name,
            hours=hours
        )
        return output
    return '<h2>Для начала нужно ввести данные</h2>'


@app.route('/booking/<profile_id>/<day>/<time>/')
def all_booking(profile_id, day, time):
    content = json_to_py_teachers()
    check = 0
    for i in content:
        if int(profile_id) == i['id']:
            check += 1
    if check > 0:
        if day in week:
            if time in lesson_start_time:
                for i in content:
                    if i['id'] == int(profile_id):
                        if i['free'][day][(time + ':00')]:
                            goals = json_to_py_goals()
                            form = UserForm()
                            output = render_template(
                                'booking.html', 
                                content=content_formation(content, profile_id),
                                goals=goals,
                                day=day,
                                time=time,
                                week=week,
                                form=form
                                )
                            return output
                        else:
                            return f'''<h2>На это время занятие уже забронировано. <br />
                            Выберете <a href='/profiles/{ profile_id }/'>другое</a> время<h2>'''
            else:
                return f'''<h2>Не получится вас записать на середину занятия <br /> 
                Сделайте выбор на <a href='/profiles/{ profile_id }/'>актуальное</a> время</h2>'''
        else:
            return '<h2>Не правильный день недели</h2>'
    else:
        return '<h2>Такого преподавателя нет</h2>'


@app.route('/booking_done/', methods=["GET", "POST"])
def booking_done():
    if request.method == 'POST':
        form = UserForm()
        name = form.name.data
        tel = form.tel.data
        day = form.client_weekday.data
        time = form.client_time.data + ':00'
        teacher = form.client_teacher.data
        data = {
            'teacher': teacher,
            'day': day,
            'time': time,
            'name': name,
            'tel': tel
            }
        booking_json(data)
        output = render_template(
            'booking_done.html',
            name=name,
            tel=tel,
            time=time,
            day=day,
            week=week
        )
        return output
    return '<h2>Нужно ввести данные для регистрации на пробное занятие</h2>'


def json_to_py_teachers():
    with open('data_teachers.json', 'r', encoding='utf-8') as f:
        content = json.load(f)
        return content


def json_to_py_goals():
    with open('data_goals.json', 'r', encoding='utf-8') as f:
        content = json.load(f)
        return content


def booking_json(content):
    with open("booking.json", "w", encoding='utf-8') as f:
        json.dump(content, f)


def request_json(content):
    with open("request.json", "w", encoding='utf-8') as f:
        json.dump(content, f)


'''def content_formation(content, profile_id):
    content = content
    profile_id = profile_id
    for i in content:
        if i['id'] == int(profile_id):
            return i'''


@app.errorhandler(404)
def render_not_found(error):
    return """<p style="font-size: 150px">404</p>
    <h1>Ничего не нашлось! Вот неудача, отправляйтесь на <a href='/'>главную</a>!</h1>"""


if __name__ == '__main__':
    app.run()
