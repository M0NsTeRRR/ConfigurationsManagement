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

import string
import secrets

from json.decoder import JSONDecodeError

from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    session,
    current_app,
)

import requests

from flask_babel import gettext

from website.gitea.gitea import GiteaAPI
from website.gitea.giteaError import GiteaAPIError
from website.gitea.utils import gitea_required

from website.auth import login_required

from website.db import (
    get_user,
    update_token,
    update_gitea,
    update_api_key,
    get_gitea
)

bp = Blueprint('settings', __name__, url_prefix='/settings')


@bp.route('/', methods=('GET', 'POST'))
@login_required
def index():
    user = get_user(user_id=session.get('user_id'))
    gitea_user = None
    error = False
    if user['gitea_token']:
        try:
            gitea_user = GiteaAPI(user['gitea_token']).user_get_current().json()
        except (requests.exceptions.RequestException, GiteaAPIError, JSONDecodeError) as e:
            error = True
            flash(gettext(u'Error something went wrong.'), 'fail')
            current_app.logger.error(f"{e}")
    return render_template('settings/index.html', gitea_user=gitea_user, gitea=get_gitea(), api_key=user['api_key'], error=error, isLogged=True)


@bp.route('/gitea/connect', methods=('POST',))
@login_required
def gitea_connect():
    user = get_user(user_id=session.get('user_id'))
    gitea_token = request.form.get('gitea_token')
    error = None

    if user['gitea_token'] is not None:
        error = gettext(u'Your account is already linked with Gitea.')
    elif not gitea_token:
        error = gettext(u'Token is required.')

    if error is None:
        # test if API works
        try:
            GiteaAPI(gitea_token).user_get_current()
        except (requests.exceptions.RequestException, GiteaAPIError) as e:
            error = gettext(u'Error account not linked.')
            current_app.logger.error(f"{e}")
        else:
            update_token(session.get('user_id'), gitea_token)
            flash(gettext(u'Your account is now linked with Gitea.'), 'success')

    if error:
        flash(error, 'fail')

    return redirect(url_for('settings.index'))


@bp.route('/gitea/disconnect', methods=('POST',))
@login_required
def gitea_disconnect():
    user = get_user(user_id=session.get('user_id'))
    error = None

    if user['gitea_token'] is None:
        error = gettext(u'Your account is not linked with Gitea.')

    if error is None:
        update_token(user['id'], None)
        flash(gettext(u'Your account is no longer linked with Gitea.'), 'success')

    if error:
        flash(error, 'fail')

    return redirect(url_for('settings.index'))


@bp.route('/gitea/repository', methods=('POST',))
@login_required
def gitea_repository():
    gitea_url = request.form.get('gitea_url')
    gitea_owner = request.form.get('gitea_owner')
    gitea_repository = request.form.get('gitea_repository')
    error = None

    if not gitea_url:
        error = gettext(u'Gitea url is required.')
    elif not gitea_owner:
        error = gettext(u'Owner of the repository is required.')
    elif not gitea_repository:
        error = gettext(u'Name of the repository is required.')

    if error is None:
        update_gitea(gitea_url, gitea_owner, gitea_repository)
        flash(gettext(u'Repository configuration saved.'), 'success')

    if error:
        flash(error, 'fail')

    return redirect(url_for('settings.index'))


@bp.route('/api_key/generate', methods=('POST',))
@login_required
@gitea_required
def create_api_key():
    alphabet = string.ascii_letters + string.digits + string.punctuation.replace('"', '').replace("'", '')
    api_key = ''.join(secrets.choice(alphabet) for _ in range(secrets.randbelow(30) + 50))
    update_api_key(session.get('user_id'), api_key)
    flash(gettext(u'New API key generated.'), 'success')
    return redirect(url_for('settings.index'))


@bp.route('/api_key/delete', methods=('POST',))
@login_required
@gitea_required
def delete_api_key():
    user = get_user(user_id=session.get('user_id'))
    if user['api_key'] is None:
        flash(gettext(u'No API key to delete.'), 'fail')
    else:
        update_api_key(session.get('user_id'), None)
        flash(gettext(u'API key deleted.'), 'success')
    return redirect(url_for('settings.index'))
