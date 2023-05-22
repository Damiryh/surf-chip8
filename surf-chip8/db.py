from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from flask import current_app, g
from .model import *
import click

engine = create_engine("sqlite:///database.db", echo=True)

def get_db_session():
    if 'db_session' not in g:
        g.db_session = Session(engine)
    return g.db_session

def close_db_session(e=None):
    db_session = g.pop('db_session', None)
    if db_session is not None:
        db_session.close()

def init_db():
    Base.metadata.create_all(engine)

@click.command('init-db')
def init_db_command():
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db_session)
    app.cli.add_command(init_db_command)
