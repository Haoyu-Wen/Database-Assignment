from flask import Flask, session, g
import config
from exts import db
from models import UserModel
from flask_migrate import Migrate
from blueprints.account import bp as account_bp
from blueprints.homepage import bp as homepage_bp
# from blueprints import forms

app = Flask(__name__)
app.config.from_object(config)  # read configuration

db.init_app(app)
migrate = Migrate(app, db)

app.register_blueprint(account_bp)
app.register_blueprint(homepage_bp)


@app.before_request
def my_before_request():
    user_id = session.get("user_id")
    if user_id:
        user = UserModel.query.get(user_id)
        setattr(g, "user", user)
    else:
        setattr(g, "user", None)


@app.context_processor
def my_context_processor():
    return {'user': g.user}


@app.route('/hello')
def test():
    user = UserModel(username='Why', nickname="我是神", password="111111", phone="12345678901", identify=0)
    db.session.add(user)
    db.session.commit()
    return "hello"
    # return f"Hello {user.username} and {user.nickname}"


@app.errorhandler(404)
def page_not_found(error):
    # return render_template('page_not_found.html'), 404
    return "404 NOT FOUND"


if __name__ == '__main__':
    app.run(debug=True, port=5000)
