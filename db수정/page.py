from flask import Flask, render_template, request, redirect, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from os.path import join
import os

app = Flask(__name__)

app.secret_key = 'your_secret_key'

# MySQL 데이터베이스 연결 정보 설정
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:tiger@localhost/tiger'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 이미지 업로드 설정
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

# 데이터베이스 연동 설정 초기화
db = SQLAlchemy(app)

# 패스워드 해싱 함수 정의
def hash_password(password):
    return generate_password_hash(password)

def verify_password(password, password_hash):
    return check_password_hash(password_hash, password)

# 게시물 모델 정의
class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)
    author = db.Column(db.String(255), nullable=False)
    views = db.Column(db.Integer, default=0)
    image_path = db.Column(db.String(255), nullable=True)
    password_hash = db.Column(db.String(255), nullable=True)  # 비밀번호 해시 저장

    comments = db.relationship('Comment', backref='post', cascade='all, delete-orphan')

    def __init__(self, title, content, author, image_path, password_hash=None):
        self.title = title
        self.content = content
        self.author = author
        self.image_path = image_path
        if password_hash:
            # 비밀번호가 제공되면 해시값 저장
            self.password_hash = password_hash

# 댓글 모델 정의 (수정하지 않음)
class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# 루트 경로: 게시판 목록 표시
@app.route('/')
def index():
    posts = Post.query.all()
    return render_template('index.html', posts=posts)

@app.route('/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)



# 게시물 작성
@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        author = request.form['author']
        password = request.form['password']

        # 사용자가 제출한 패스워드를 해싱하여 password_hash 변수에 저장
        password_hash = hash_password(password)

        if not password:
            flash('비밀번호를 입력하세요.', 'error')
        else:
            if 'image' in request.files:
                image = request.files['image']
                if image and allowed_file(image.filename):
                    filename = secure_filename(image.filename)
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image.save(image_path)
                else:
                    image_path = None
            else:
                image_path = None

            # 게시물 작성 시 password_hash를 전달
            post = Post(title=title, content=content, author=author, image_path=image_path, password_hash=password_hash)
            db.session.add(post)
            db.session.commit()
            flash('게시물이 성공적으로 작성되었습니다.', 'success')
            return redirect('/')
    return render_template('create.html')


# 게시물 수정
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    post = Post.query.get(id)

    if request.method == 'POST':
        # Get the entered password from the form
        entered_password = request.form['password']

        if verify_password(entered_password, post.password_hash):
            # Password is correct, proceed with editing
            post.title = request.form['title']
            post.content = request.form['content']
            db.session.commit()
            flash('게시물이 수정되었습니다.', 'success')
            return redirect('/')
        else:
            # Password is incorrect, display an error message
            flash('비밀번호가 일치하지 않습니다. 다시 시도하세요.', 'error')

    return render_template('edit.html', post=post)




# 게시물 삭제
@app.route('/delete/<int:id>', methods=['POST', 'GET'])
def delete(id):
    post = Post.query.get(id)
    
    if request.method == 'POST':
        # 사용자가 입력한 패스워드
        entered_password = request.form['password']
        
        if verify_password(entered_password, post.password_hash):
            db.session.delete(post)
            db.session.commit()
            flash('게시물이 삭제되었습니다.', 'success')
            return redirect('/')
        else:
            flash('비밀번호가 일치하지 않습니다.', 'error')
            return redirect(f'/delete/{id}')
        
    return render_template('delete.html', post=post)

# 게시물 보기
@app.route('/view/<int:id>')
def view(id):
    post = Post.query.get(id)
    if post:
        post.views += 1
        db.session.commit()
        comments = Comment.query.filter_by(post_id=id).all()
        return render_template('show_post.html', post=post, comments=comments, image_filename=post.image_path)
    else:
        flash('게시물을 찾을 수 없습니다.', 'error')
        return redirect('/')

# 댓글 생성
@app.route('/add_comment/<int:id>', methods=['POST'])
def add_comment(id):
    post = Post.query.get(id)
    if request.method == 'POST':
        comment_text = request.form['comment_text']
        comment = Comment(text=comment_text, post_id=id)
        db.session.add(comment)
        db.session.commit()
        flash('댓글이 성공적으로 추가되었습니다.', 'success')
        return render_template('show_post.html', post=post, comments=Comment.query.filter_by(post_id=id).all())
    return render_template('show_post.html', post=post, comments=Comment.query.filter_by(post_id=id).all())

# 댓글 삭제
@app.route('/delete_comment/<int:id>', methods=['POST'])
def delete_comment(id):
    comment = Comment.query.get(id)
    if comment:
        db.session.delete(comment)
        db.session.commit()
        flash('댓글이 삭제되었습니다.', 'success')
    
    post_id = comment.post_id if comment else None
    post = Post.query.get(post_id)
    comments = Comment.query.filter_by(post_id=post_id).all()

    return render_template('show_post.html', post=post, comments=comments)


# 게시물 검색
@app.route('/search', methods=['POST'])
def search():
    keyword = request.form['keyword']
    # 제목, 내용, 작성자 모두를 검색어와 비교
    posts = Post.query.filter(
        (Post.title.like(f"%{keyword}%")) |
        (Post.content.like(f"%{keyword}%")) |
        (Post.author.like(f"%{keyword}%"))
    ).all()
    return render_template('search_results.html', posts=posts)

if __name__ == '__main__':
    app.run(port=5001,debug=True)
