from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# MySQL 데이터베이스 연결 정보 설정
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://test:1234@localhost/test'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 데이터베이스 연동 설정 초기화
db = SQLAlchemy(app)

# 게시물 모델 정의
class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)
    
    comments = db.relationship('Comment', backref='post', cascade='all, delete-orphan')

    def __init__(self, title, content):
        self.title = title
        self.content = content

# 댓글 모델 정의
class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp(), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'), nullable=False)

    def __init__(self, text, post_id):
        self.text = text
        self.post_id = post_id

# 루트 경로: 게시판 목록 표시
@app.route('/')
def index():
    posts = Post.query.all()
    return render_template('index.html', posts=posts)

# 게시물 작성
@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        post = Post(title=title, content=content)
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
        post.title = request.form['title']
        post.content = request.form['content']
        db.session.commit()
        flash('게시물이 수정되었습니다.', 'success')
        return redirect('/')
    return render_template('edit.html', post=post)

# 게시물 삭제
@app.route('/delete/<int:id>', methods=['POST', 'GET'])
def delete(id):
    post = Post.query.get(id)
    
    if request.method == 'POST':
        db.session.delete(post)
        db.session.commit()
        flash('게시물이 삭제되었습니다.', 'success')
        return redirect('/')

    return render_template('delete.html', post=post)

# 게시물 보기
@app.route('/view/<int:id>')
def view(id):
    post = Post.query.get(id)
    comments = Comment.query.filter_by(post_id=id).all()
    return render_template('show_post.html', post=post, comments=comments)

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
        return redirect('/')  # 댓글을 작성한 후에는 홈 페이지로 리디렉션
    return redirect('/view/' + str(id))  # 댓글 작성에 실패한 경우 해당 게시물 페이지로 리디렉션

# 댓글 삭제
@app.route('/delete_comment/<int:id>', methods=['POST'])
def delete_comment(id):
    comment = Comment.query.get(id)
    if comment:
        db.session.delete(comment)
        db.session.commit()
        flash('댓글이 삭제되었습니다.', 'success')
    return redirect('/')

# 게시물 검색
@app.route('/search', methods=['POST'])
def search():
    keyword = request.form['keyword']
    # 게시물 검색 쿼리: 제목 또는 내용에 키워드가 포함된 게시물을 검색
    posts = Post.query.filter(
        (Post.title.like(f"%{keyword}%")) |
        (Post.content.like(f"%{keyword}%"))
    ).all()
    return render_template('search_results.html', posts=posts)

if __name__ == '__main__':
    app.run(debug=True, port=5001)  # 포트 번호를 5001로 설정
