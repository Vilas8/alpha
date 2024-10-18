from flask import Flask, render_template
from main import session, User

app = Flask(__name__)

@app.route('/admin')
def admin():
    users = session.query(User).all()
    return render_template('admin.html', users=users)

if __name__ == '__main__':
    app.run(debug=True)
# 8015231286:AAGusBB1eTTQA3B3q8ZgUlz8l0Ksvnp1k8E
