from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import send_file
from flask import Response
from flask import request
from flask import session
from flask import url_for
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from .db import get_db_session
from .model import *
import functools
from .auth import login_required
import json

bp = Blueprint('snippets', __name__, url_prefix='/snippets')

@bp.route('/')
def snippets_list():
    dbs = get_db_session()

    expression = request.args.get('expression')
    search_by = request.args.get('search-by')

    try:
        if (not expression) or (not search_by):
            snippets = dbs.scalars(select(Snippet)).all()
        elif search_by == 'name':
            snippets = dbs.query(Snippet)\
                .where(Snippet.name.op('regexp')(expression))\
                .all()
        elif search_by == 'author':
            snippets = dbs.query(Snippet)\
                .join(User)\
                .where(User.name.op('regexp')(expression))\
                .all()
        elif search_by == 'source':
            snippets = dbs.query(Snippet)\
                .where(Snippet.source.op('regexp')(expresson))\
                .all()
    except OperationalError:
        flash("Ошибка в строке поиска")
        return redirect(url_for('index'))

    return render_template('snippets/list.html', snippets=snippets)


def send_response(message, status, **kwargs):
    content = { "message": message }
    for key, value in kwargs.items():
        content[key] = value
    return Response(json.dumps(content), status=status, mimetype='application/json')


@bp.route('/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def snippet(id):
    dbs = get_db_session()

    if request.method == 'GET':
        snippet = dbs.query(Snippet).get(id)
        if not snippet:
            flash("Сниппет не найден")
            return redirect(url_for("index"))
        if not g.user or snippet.author != g.user:
            return render_template('snippets/view.html', snippet=snippet)
        return render_template('snippets/edit.html', snippet=snippet)

    elif request.method == 'PUT':
        snippet = dbs.query(Snippet).get(id)
        
        if not snippet:
            return send_response('Сниппет не найден', 404)
        
        name = request.json.get('name')
        source = request.json.get('source')

        if not name or not source:
            return send_response('Не заполнено имя либо код', 400)
        
        snippet.name = name
        snippet.source = source
        
        try:
            dbs.add(snippet)
            dbs.commit()
        except IntegrityError as err:
            dbs.rollback()
            return send_response('Не удалось сохранить сниппет', 500)
        
        return send_response('Сниппет сохранен успешно', 200)

    elif request.method == 'DELETE':
        snippet = dbs.query(Snippet).get(id)
        try:
            if snippet: dbs.delete(snippet)
            dbs.commit()
            return send_response('Сниппет успешно удален!', 200)
        except IntegrityError:
            dbs.rollback()
            return send_response('Невозможно удалить сниппет', 500)



@bp.route('/<int:id>/assemble')
def assemble_snippet(id):
    dbs = get_db_session()
    snippet = dbs.query(Snippet).get(id)
    if not snippet: return send_response('Сниппет не найден', 404)
    
    from .chip8asm.assembler import assemble
    success, data, message = assemble(snippet)
    
    if success == False: return send_response(message, 500)
    if request.args.get('binary') != "1": return send_response(message, 200)
    
    return send_file(data, download_name='program.ch8', mimetype='application/octet-stream')


@bp.route('/<int:id>/run')
def run_snippet(id):
    dbs = get_db_session()
    snippet = dbs.query(Snippet).get(id)
    if not snippet: return send_response('Сниппет не найден', 404)
    return render_template('snippets/run.html', snippet=snippet)


    
@bp.route('/new', methods=['GET', 'POST'])
def create_new_snippet():
    dbs = get_db_session()
    
    if request.method == 'POST':
        name = request.json.get('name')
        source = request.json.get('source')

        if not name or not source:
            return send_response('Не заполнено название или код', 400)
        
        snippet = Snippet(name=name, source=source, author = g.user)
        
        try:
            dbs.add(snippet)
            dbs.commit()
        except IntegrityError as err:
            return send_response("Сниппет с данным названием уже существует", 400)
        
        return send_response("Новый сниппет успешно создан", 201, new_id=snippet.id)
        
    else:
        return render_template('snippets/edit.html', snippet=None)
