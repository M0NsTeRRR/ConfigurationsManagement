# ----------------------------------------------------------------------------
# Copyright © Ortega Ludovic, 2020
#
# Contributeur(s):
#     * Ortega Ludovic - mastership@hotmail.fr
#
# Ce logiciel, ConfigurationsManagement est un outil qui permet de
# sauvegarder/restorer des serveurs/services.
#
# Ce logiciel est régi par la licence CeCILL soumise au droit français et
# respectant les principes de diffusion des logiciels libres. Vous pouvez
# utiliser, modifier et/ou redistribuer ce programme sous les conditions
# de la licence CeCILL telle que diffusée par le CEA, le CNRS et l'INRIA
# sur le site "http://www.cecill.info".
#
# En contrepartie de l'accessibilité au code source et des droits de copie,
# de modification et de redistribution accordés par cette licence, il n'est
# offert aux utilisateurs qu'une garantie limitée.  Pour les mêmes raisons,
# seule une responsabilité restreinte pèse sur l'auteur du programme,  le
# titulaire des droits patrimoniaux et les concédants successifs.
#
# A cet égard  l'attention de l'utilisateur est attirée sur les risques
# associés au chargement,  à l'utilisation,  à la modification et/ou au
# développement et à la reproduction du logiciel par l'utilisateur étant
# donné sa spécificité de logiciel libre, qui peut le rendre complexe à
# manipuler et qui le réserve donc à des développeurs et des professionnels
# avertis possédant  des  connaissances  informatiques approfondies.  Les
# utilisateurs sont donc invités à charger  et  tester  l'adéquation  du
# logiciel à leurs besoins dans des conditions permettant d'assurer la
# sécurité de leurs systèmes et ou de leurs données et, plus généralement,
# à l'utiliser et l'exploiter dans les mêmes conditions de sécurité.
#
# Le fait que vous puissiez accéder à cet en-tête signifie que vous avez
# pris connaissance de la licence CeCILL, et que vous en avez accepté les
# termes.
# ----------------------------------------------------------------------------

import sqlite3

import click
from flask import current_app, g
from flask.cli import with_appcontext

from werkzeug.security import check_password_hash, generate_password_hash


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def insert_user(login, password):
    db = get_db()
    db.execute(
        'INSERT INTO user (login, password, gitea_token) VALUES (?, ?, ?)',
        (login, generate_password_hash(password), None)
    )
    db.commit()


def update_password(id, password):
    db = get_db()
    db.execute(
        'UPDATE user SET password = ? WHERE id = ?',
        (generate_password_hash(password), id)
    )
    db.commit()


def update_token(id, gitea_token):
    db = get_db()
    db.execute(
        'UPDATE user SET gitea_token = ? WHERE id = ?',
        (gitea_token, id)
    )
    db.commit()


def update_api_key(id, api_key):
    db = get_db()
    db.execute(
        'UPDATE user SET api_key = ? WHERE id = ?',
        (api_key, id)
    )
    db.commit()


def delete_user(id):
    db = get_db()
    db.execute(
        'DELETE FROM user WHERE id = ?',
        (id,)
    )
    db.commit()


def get_user(login=None, user_id=None, api_key=None):
    db = get_db()
    if login:
        query = 'SELECT * FROM user WHERE login = ?'
        params = (login,)
    elif user_id:
        query = 'SELECT * FROM user WHERE id = ?'
        params = (user_id,)
    else:
        query = 'SELECT * FROM user WHERE api_key = ?'
        params = (api_key,)
    return db.execute(
        query, params
    ).fetchone()


def get_users():
    db = get_db()
    return db.execute('SELECT * FROM user').fetchall()


def check_password(login, password):
    user = get_user(login=login)
    return user is not None and check_password_hash(user['password'], password)


def update_gitea(url, owner, repository):
    db = get_db()
    db.execute(
        'UPDATE gitea SET url = ?, owner = ?, repository = ? WHERE id = 1',
        (url, owner, repository)
    )
    db.commit()


def get_gitea():
    db = get_db()
    return db.execute(
        'SELECT * FROM gitea WHERE id = 1',
        ()
    ).fetchone()


def create_task(hostname, module, action, path, start_date):
    db = get_db()
    id = db.execute(
        'INSERT INTO task (hostname, module, action, path, start_date) VALUES (?, ?, ?, ?, ?)',
        (hostname, module, action, path, start_date)
    ).lastrowid
    db.commit()

    return id


def update_task(id='', state='', error='', message='', end_date=''):
    db = get_db()
    query = 'UPDATE task SET'
    values = tuple()

    if state:
        query = f'{query} state = ?,'
        values = values + (state,)
    if error:
        query = f'{query} error = ?,'
        values = values + (error,)
    if message:
        query = f'{query} message = ?,'
        values = values + (message,)
    if end_date:
        query = f'{query} end_date = ?,'
        values = values + (end_date,)

    query = f'{query[:-1]} WHERE id = ?'
    values = values + (id,)

    db.execute(
        query,
        values
    )
    db.commit()


def get_task(id):
    db = get_db()
    return db.execute(
        'SELECT * FROM task WHERE id = ?',
        (id,)
    ).fetchone()


def get_tasks(nb, offset):
    db = get_db()
    return db.execute(
        'SELECT * FROM task LIMIT ? OFFSET ?',
        (nb, offset)
    ).fetchall()


def get_nb_tasks():
    db = get_db()
    return db.execute(
        'SELECT COUNT(*) FROM task',
        ()
    ).fetchone()[0]


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
