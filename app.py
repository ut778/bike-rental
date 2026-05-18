from flask import Flask, render_template
from routes.auth import auth_bp
from routes.user import user_bp
from routes.admin import admin_bp

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_in_production'

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(user_bp)
app.register_blueprint(admin_bp)

@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)
