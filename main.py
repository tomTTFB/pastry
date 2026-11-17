from flask import Flask, render_template, request, redirect, url_for, abort
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy

from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound
from markupsafe import Markup

import os
from datetime import datetime
import secrets

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Paste(db.Model):
    id = db.Column(db.String(10), primary_key=True)
    content = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(30), nullable=False, default="text")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now())
    expires_at = db.Column(db.DateTime, nullable=True)
    burn_after_read = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"Name : {self.first_name}, Age: {self.age}"

def highlight_paste(content, language):
    try:
        lexer = get_lexer_by_name(language)
    except ClassNotFound:
        lexer = TextLexer()
    formatter = HtmlFormatter(linenos=True)
    return Markup(highlight(content, lexer, formatter))


@app.route('/')
def hello_world():
    return render_template("index.html")

@app.route('/new', methods=['POST'])
def add_paste():
    print(request.form)

    content = request.form.get('content', '')
    language = request.form.get('language', '')
    burn_after_read = 'burn_after_read' in request.form

    if not content.strip():
        return("Paste can't be empty", 400)

    paste = Paste(
        id=secrets.token_urlsafe(6),
        content=content,
        language=language,
        burn_after_read=burn_after_read
    )
    db.session.add(paste)
    db.session.commit()

    highlighted = highlight_paste(paste.content, paste.language)

    return render_template("newpaste.html", id=paste.id, content=paste.content, created_at=paste.created_at, language=paste.language, highlighted=highlighted)

@app.route('/view_paste/<id>')
def view_paste(id):
    paste = db.session.get(Paste, id)
    if paste is None:
        abort(404)

    highlighted = highlight_paste(paste.content, paste.language)

    burn = paste.burn_after_read

    if burn is True:
        db.session.delete(paste)
        db.session.commit()

    return render_template("paste.html", content=paste.content, created_at=paste.created_at, language=paste.language, highlighted=highlighted, burned=burn)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)