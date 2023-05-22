from flask import Flask, render_template, g

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret_key'
    
    @app.route('/')
    def index():
        return render_template("index.html", user=g.user)

    from . import db
    db.init_app(app)

    from . import auth
    from . import snippets
    app.register_blueprint(auth.bp)
    app.register_blueprint(snippets.bp)
    return app
