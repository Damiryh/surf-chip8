from flask import Flask, render_template, g, send_from_directory

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'secret_key'
    
    @app.route('/')
    def index():
        return render_template("index.html", user=g.user)

    @app.route('/chip8/<path:path>')
    def get_chip_file(path):
        return send_from_directory('static/chip8', path)

    @app.route('/about')
    def about():
        return render_template("about.html")
    
    from . import db
    db.init_app(app)

    from . import auth
    from . import snippets
    app.register_blueprint(auth.bp)
    app.register_blueprint(snippets.bp)
    return app
