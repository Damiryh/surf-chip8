from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import Response
from flask import request
from flask import session
from flask import url_for
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from .db import get_db_session
from .model import *
import functools
from .auth import login_required
import json

bp = Blueprint('snippets', __name__, url_prefix='/snippets')

@bp.route('/')
def snippets_list():
    dbs = get_db_session()
    snippets = dbs.scalars(select(Snippet)).all()
    return render_template('snippets/list.html', snippets=snippets)


def send_response(message, status):
    return Response('{ "message": "' + message + '" }', status=status, mimetype='application/json')


@bp.route('/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def snippet(id):
    dbs = get_db_session()

    if request.method == 'GET': # view single snippet
        snippet = dbs.query(Snippet).get(id)
        if not snippet:
            flash("Snippet not found")
            return redirect(url_for("index"))
        if not g.user or snippet.author != g.user:
            return render_template('snippets/view.html', snippet=snippet)
        return render_template('snippets/edit.html', snippet=snippet)

    elif request.method == 'PUT': # update snippet
        snippet = dbs.query(Snippet).get(id)
        if not snippet:
            return send_response('Snippet not found', 404)
        
        snippet.name = request.json['name']
        snippet.source = request.json['source']

        try:
            dbs.add(snippet)
            dbs.commit()
        except IntegrityError:
            dbs.rollback()
            return send_response('Cannot update snippet', 500)
        
        return send_response('Snippet updated successfully', 200)

    elif request.method == 'DELETE': # delete snippet
        snippet = dbs.query(Snippet).get(id)
        try:
            if snippet: dbs.delete(snippet)
            dbs.commit()
            return send_response('Snippet deleted successfully', 200)
        except IntegrityError:
            dbs.rollback()
            return send_response('Cannot delete snippet', 500)


@bp.route('/new', methods=['GET', 'POST'])
def create_new_snippet():
    dbs = get_db_session()
    
    
    if request.method == 'POST':
        snippet = Snippet(
            name = request.json['name'],
            source = request.json['source'],
            author = g.user)
        
        try:
            dbs.add(snippet)
            dbs.commit()
        except IntegrityError as err:
            return send_response("Snippet already exists", 400)
            
        return send_response("New snippet created successfully", 201)
        
    else:
        return render_template('snippets/edit.html', snippet=None)


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def snippet_edit(id):
    dbs = get_db_session()
    snippet = dbs.query(Snippet).get(id)

    if not snippet:
        flash("Page not found.")
        return redirect(url_for("index"))
    
    if snippet.author != g.user:
            flash("You are not author of this snippet.")
            return redirect(url_for('snippets.snippet_view', id=id))
    
    if request.method == 'POST':
        name = request.form['name']
        source = request.form['source']
        snippet.name = name
        snippet.source = source
        dbs.add(snippet)
        
        try:
            dbs.commit()
        except:
            dbs.rollback()

    return render_template('snippets/edit.html', snippet=snippet)

@bp.route('/<int:id>/play')
def snippet_play(id):
    dbs = get_db_session()
    snippet = dbs.query(Snippet).get(id)

    if not snippet:
        flash("Page not found.")
        return redirect(url_for("index"))
    
    return redirect(url_for("snippets.snippet_view", id=id))
