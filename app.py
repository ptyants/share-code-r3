from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Thay thế bằng một secret key bất kỳ
#app.config['UPLOADED_VIDEOS_URL'] = '/static/uploads/'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///main.db' 



db = SQLAlchemy(app)

def create_tables():
    with app.app_context():
        db.create_all()
        
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    correct_lession = db.Column(db.Integer)
    learning = db.Column(db.Integer) #chỉ có 1
    number_completed = db.Column(db.Integer)
    
# [số tầng 0,1, số giai đoạn 0,1,2, số bài đã học, , tổng số bài]
   
#giai đoạn 
stages = [
    #[nơi, giai đoạn, tên giai đoạn, số sự kiện trong giai đoạn đó (phải có thật trong file)]
    [0,0,"pháp phổ đại chiến",1],
    [1,0,"vua trịnh lê",3],
    [1,1,"đại việt",4],
    [1,2,"pháp thuộc",0]
]  


def create_lession(Place,stage,event):
    name_file = "data/{0}/{1}/{0} {1} {2}.txt".format(Place,stage,event)
    #text_lession = []
    with open(name_file, encoding='utf-8')  as tep:
        lession_name = tep.readline().strip()
        time_learn = int(tep.readline().strip())
        name_pic_1 = tep.readline().strip()
        name_pic_2 = tep.readline().strip()
        #for line in tep.readlines():
            #text_lession.append(line.strip('/n'))
        text_lession = tep.readlines()
    return [lession_name ,time_learn ,text_lession ,name_pic_1 ,name_pic_2]



def processing_lession(username, time_today):
    list_lession_today=[]
    user = User.query.filter_by(username=username).first()
    learning_json = user.learning
    learning = json.loads(learning_json)
    #learning = user.learning
    number_corrected_lession = int(user.number_completed)
    done_lession = False
    stage_info = None
    for stage in stages:
        if stage[0] == int(learning[0]) and stage[1] == int(learning[1]):
            stage_info = stage
            break
    if number_corrected_lession == stage_info[3]:
        number_lession_ll_done = number_corrected_lession
        done_lession = True
        
    else:
        sum_time_learn = 0
        while number_corrected_lession < stage_info[3]:
            
            lessions = create_lession(learning[0],learning[1],number_corrected_lession)
            sum_time_learn += lessions[1]
            if sum_time_learn <= time_today:
                list_lession_today.append(lessions)
            else:
                break
            number_corrected_lession += 1
        number_lession_ll_done = number_corrected_lession
    return [list_lession_today ,number_lession_ll_done ,done_lession]
     
    

print(create_lession(1,0,0))

# Routes
@app.route('/')
def home():
    return render_template('viewpage.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error_message = None
    if request.method == 'POST':
        # Xử lý thông tin đăng nhập
        username_or_email = request.form['username_or_email']
        password = request.form['password']        
        user = User.query.filter_by(username=username_or_email).first()

        if user and check_password_hash(user.password, password):
            # Do something after successful login
            flash('Login successful', 'success')
            return redirect(url_for('user_view', username=user.username))
        else:
            error_message = "Tên đăng nhập hoặc mật khẩu không đúng!"
            
    return render_template('login.html', error_message=error_message)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if the username is already in use
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Tên đăng nhập hoặc email đã tồn tại!"
        new_teacher = Teachers(username=username, email=email, password=User().hash_password(password))
        with app.app_context():
            db.session.add(new_teacher)
            db.session.commit()

        return redirect(url_for('home'))

    return render_template('register.html')

@app.route('/choose_stage/<username>', methods=['GET', 'POST']) #khi chưa chọn bài học
def choose_stage(username):
    user = User.query.filter_by(username=username).first()
    message = session.pop('message', None)
    #user = db.session.query(User).get(username)
    if user is None:
        # Handle the case where the user doesn't exist
        return "User not found", 404
    
    if request.method == 'POST':
        selected_stage  = request.form.get('selected_stage')
        
        if selected_stage:
            stage_parts = selected_stage.split(',')
            history_option = [int(part) for part in stage_parts]  # Chuyển các phần tử thành số nguyên
        else:
            return "Invalid stage selected"
        
        stage_info = None
        for stage in stages:
            if stage[0] == int(history_option[0]) and stage[1] == int(history_option[1]):
                stage_info = stage
                break
            
        if stage_info is None:
            return render_template('choose_stage.html', stages=stages, username=username, message="Không tìm thấy thông tin giai đoạn tương ứng.")
        
        elif stage_info[3] == 0:
            return render_template('choose_stage.html', stages=stages, username=username, message="Khóa học đang được xây dựng, xin quý khách vui lòng chọn khóa học khác.")
        
        else:
            user.learning = json.dumps(history_option)
            user.number_completed = 0
            db.session.commit()   
            
            #When retrieving the learning information, deserialize it back to a list:
            #learning_json = user.learning  # Retrieve the JSON string from the database
            #learning_list = json.loads(learning_json)  # Deserialize the JSON string to a list
            
            return redirect(url_for('user_view', username=username))  
      
    return render_template('choose_stage.html', stages=stages, username=username, message=message)

@app.route('/<username>', methods=['GET', 'POST'])
def user_view(username):
    message = session.pop('message', None)  # Lấy thông điệp ra khỏi session nếu có
    user = User.query.filter_by(username=username).first()
    
    if user is None:
        # Handle the case where the user doesn't exist
        return "User not found", 404

    learning = user.learning

    if not learning:
        return redirect(url_for('choose_stage', username=username))

    if request.method == 'POST':
        time_today = int(request.form['time_today'])
        return redirect(url_for('learn_tab', username=username, time_today=time_today))

    return render_template('user_view.html', username=username, message=message)



@app.route('/learn_tab/<username>/<int:time_today>', methods=['GET', 'POST'])
def learn_tab(username, time_today):
    data = processing_lession(username, time_today)
    total_lession_today = len(data[0])
    lesson_index = 0
    user = User.query.filter_by(username=username).first()
    learning_json = user.learning
    learning = json.loads(learning_json)
    stage_info = None
    print("debug - ",data)
    if data[2] == False:
        for stage in stages:
            if stage[0] == int(learning[0]) and stage[1] == int(learning[1]):
                stage_info = stage
                break
    else:
        return redirect(url_for('make_test', username=username))
    
    if request.method == 'POST':
        lesson_index = int(request.form['lessonIndex']) 
        
        if 'correctButton' in request.form:
            user.number_completed += 1
            db.session.commit()
            if user.number_completed == stage_info[3]:
                return redirect(url_for('make_test', username=username))
            lesson_index = (lesson_index + 1) % total_lession_today 
           
            
            
    return render_template('learn_tab.html', stage_info=stage_info, username=username, time_today=time_today, total_lession_today=total_lession_today, i=lesson_index, data=data)



@app.route('/make_test/<username>', methods=['GET', 'POST'])
def make_test(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        return "User not found", 404
    learning_json = user.learning
    learning = json.loads(learning_json)
    print("debug learning - ",learning)
    place, event = learning
    name_test = f"{place} {event}.html"
    place_file = f"data/{place}/{event}"
    #return render_template("make_test.html", username=username)
    #return render_template(name_test, username=username)  
    if request.method == 'POST':
        correct_answers = 0
        for num in range(1,6):
            quest = f"quiz_{num}"
            answers = request.form[quest]
            print("answers - ",answers)
            correct_answers += int(answers)
            
        total_questions = 5
        
        score = (correct_answers / total_questions) * 100
        print("score", score)
        if score>=80:
            user = User.query.filter_by(username=username).first()
            #user.correct_lesson.append(json.dumps(learning))
            user.learning = None
            user.number_completed = None
            db.session.commit()
            session['message'] = f"Điểm của bạn là {score} đã đủ chỉ tiêu"
            return redirect(url_for('choose_stage', username=username))
            
        else:
            user = User.query.filter_by(username=username).first()
            user.number_completed = 0
            db.session.commit()
            session['message'] = f"Điểm của bạn là {score} phải học lại"
            return redirect(url_for('user_view', username=username))
    try:
        with open(f"{place_file}/{name_test}", "r", encoding="utf-8") as file:
            data_quizz = file.read()
    except FileNotFoundError:
        data_quizz = ""
    return render_template('make_test.html', username=username, data_quizz=data_quizz)


if __name__ == '__main__':
    create_tables()
    app.run(debug=True, port=5000)