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

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for
)

import click

from flask_babel import gettext

from flask.cli import with_appcontext

from website.db import (
    insert_user,
    update_password,
    delete_user,
    get_user,
    get_users
)

from website.auth import login_required

bp = Blueprint('admin', __name__, url_prefix='/admin')


@bp.route('/', methods=('GET',))
@login_required
def index():
    return render_template('admin/index.html', users=get_users(), isLogged=True)


@bp.route('/register', methods=('GET', 'POST'))
@login_required
def register():
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        confirmed_password = request.form.get('confirmed_password')
        error = None

        if not login:
            error = gettext(u'Login is required.')
        elif not password:
            error = gettext(u'Password is required.')
        elif not password == confirmed_password:
            error = gettext(u'Password not confirmed.')
        elif get_user(login=login) is not None:
            error = gettext(u'User is already registered.')

        if error is None:
            insert_user(login, password)
            flash(gettext(u'Account %(login)s created.', login=login), 'success')
            return redirect(url_for('admin.register'))

        if error:
            flash(error, 'fail')

    return render_template('admin/register.html', isLogged=True)


@bp.route('/edit_password/<string:login>', methods=('GET', 'POST'))
@login_required
def edit_password(login):
    user = get_user(login=login)
    if user is None:
        flash(gettext(u'User doesn\'t exist.'), 'fail')
        return redirect(url_for('admin.index'))
    else:
        if request.method == 'POST':
            password = request.form.get('password')
            confirmed_password = request.form.get('confirmed_password')
            error = None

            if not password:
                error = gettext(u'Password is required.')
            elif not password == confirmed_password:
                error = gettext(u'Password not confirmed.')

            if error is None:
                update_password(user['id'], password)
                flash(gettext(u'User %(login)s password changed.', login=user['login']), 'success')
                return redirect(url_for('admin.index'))

            if error:
                flash(error, 'fail')
        return render_template('admin/edit_password.html', user=user, isLogged=True)


@bp.route('/delete/<string:login>', methods=('GET', 'POST'))
@login_required
def remove(login):
    user = get_user(login=login)
    if user is None:
        flash(gettext(u'User doesn\'t exist.'), 'fail')
        return redirect(url_for('admin.index'))
    else:
        if request.method == 'POST':
            delete_user(user['id'])
            flash(gettext(u'User %(login)s deleted.', login=user['login']), 'success')
            return redirect(url_for('admin.index'))
        return render_template('admin/remove.html', user=user, isLogged=True)


def create_user(login, password):
    insert_user(login, password)


@click.command('create-user')
@click.argument("login")
@click.argument("password")
@with_appcontext
def create_user_command(login, password):
    """Create an user."""
    if login is None or len(login) == 0:
        raise click.BadParameter('Argument "LOGIN" can\'t be empty')
    if password is None or len(password) == 0:
        raise click.BadParameter('Argument "PASSWORD" can\'t be empty')
    create_user(login, password)
    click.echo('User {login} created.'.format(login=login))


def init_app(app):
    app.cli.add_command(create_user_command)
