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

import functools

from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from flask_babel import gettext

from website.db import (
    get_user,
    check_password
)

bp = Blueprint('auth', __name__, url_prefix='/auth')


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash(gettext(u'Unauthorized: You must be authenticated to access this page.'), 'fail')
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view


def already_login(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user:
            return redirect(url_for('tasks.index'))
        return view(**kwargs)
    return wrapped_view


@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_user(user_id=user_id)


@bp.route('/login', methods=('GET', 'POST'))
@already_login
def login():
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        error = None

        if not login:
            error = gettext(u'Login is required.')
        elif not password:
            error = gettext(u'Password is required.')
        elif not check_password(login, password):
            error = gettext(u'Incorrect login/password.')

        if error is None:
            session.clear()
            user = get_user(login)
            session["user_id"] = user["id"]
            flash(gettext(u'Welcome %(login)s.', login=user['login']), 'success')
            return redirect(url_for('tasks.index'))

        if error:
            flash(error, 'fail')

    return render_template('auth/login.html', isLogged=False)


@bp.route('/logout', methods=('GET',))
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
