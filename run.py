from app import create_app, socketio
from flask import redirect, url_for
app = create_app()

@app.route('/')
def home():
    return redirect(url_for('auth.login_page'))
if __name__ == '__main__':
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)
