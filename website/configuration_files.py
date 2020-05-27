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

from difflib import unified_diff
from base64 import b64decode, b64encode
from json import dumps as json_dumps

from flask import (
    Blueprint,
    render_template,
    url_for,
    redirect,
    session,
    flash,
    request,
    current_app
)

import requests

from flask_babel import gettext

from website.auth import login_required

from website.gitea.gitea import GiteaAPI
from website.gitea.giteaError import GiteaAPIError
from website.gitea.utils import gitea_required

from website.db import (
    get_user,
    get_gitea
)

bp = Blueprint('configuration_files', __name__, url_prefix='/configuration_files')


@bp.route('/', methods=('GET',))
@login_required
@gitea_required
def index():
    ref = request.args.get('ref', 'master')
    path = request.args.get('path', '')
    user = get_user(user_id=session.get('user_id'))
    gitea = get_gitea()
    repo_contents = None
    commits = None
    error = False
    folder = False

    try:
        commits = GiteaAPI(user['gitea_token']).repo_get_commits().json()
        if not path:
            req = GiteaAPI(user['gitea_token']).repo_get_contents_list({'ref': ref})
        else:
            req = GiteaAPI(user['gitea_token']).repo_get_contents(path, {'ref': ref})
    except (requests.exceptions.RequestException, GiteaAPIError) as e:
        flash(gettext(u'Error cannot get configuration files from Gitea.'), 'fail')
        error = True
        current_app.logger.error(f"{e}")
        return redirect(url_for('docs.index')) if ref == 'master' and path == '' else redirect(url_for('configuration_files.index'))
    else:
        repo_contents = req.json()
        folder = isinstance(repo_contents, list)
        if not folder:
            try:
                repo_contents['content'] = b64decode(repo_contents['content']).decode('utf-8')
            except UnicodeDecodeError:
                flash(gettext(u'Cannot read this type of file.'), 'fail')
                return redirect(url_for('configuration_files.index'))

    return render_template('configuration_files/index.html', folder=folder, gitea=gitea, repo_contents=repo_contents, commits=commits, ref=ref, error=error, isLogged=True)


@bp.route('/remove', methods=('GET', 'POST'))
@login_required
@gitea_required
def remove():
    path = request.args.get('path')
    user = get_user(user_id=session.get('user_id'))
    error = False

    if request.method == 'POST':
        try:
            req = GiteaAPI(user['gitea_token']).repo_get_contents(path, {'ref': 'master'})
            if isinstance(req.json(), list):
                raise GiteaAPIError('Cannot delete a folder, must be a file.')
            GiteaAPI(user['gitea_token']).repo_delete_contents(
                path,
                data=json_dumps({'sha': req.json()['sha']})
            )
        except (requests.exceptions.RequestException, GiteaAPIError) as e:
            flash(gettext(u'Error file does not exist.'), 'fail')
            error = True
            current_app.logger.error(f"{e}")
        else:
            flash(gettext(u'File deleted.'), 'success')
        return redirect(url_for('configuration_files.index'))
    else:
        try:
            req = GiteaAPI(user['gitea_token']).repo_get_contents(path, {'ref': 'master'})
            if isinstance(req.json(), list):
                raise GiteaAPIError('Cannot delete a folder, must be a file')
        except (requests.exceptions.RequestException, GiteaAPIError) as e:
            flash(gettext(u'Error file does not exist.'), 'fail')
            current_app.logger.error(f"{e}")
            return redirect(url_for('configuration_files.index'))
    return render_template('configuration_files/remove.html', path=path, error=error, isLogged=True)


@bp.route('/confirm_save', methods=('POST',))
@login_required
@gitea_required
def confirm_save():
    path = request.form.get('path')
    new_data = request.form.get('data')
    old_data = None
    diffs = None
    user = get_user(user_id=session.get('user_id'))

    try:
        req = GiteaAPI(user['gitea_token']).repo_get_contents(path, {'ref': 'master'})
        if isinstance(req.json(), list):
            raise GiteaAPIError('Cannot save a folder, must be a file.')
    except (requests.exceptions.RequestException, GiteaAPIError) as e:
        flash(gettext(u'Error file does not exist.'), 'fail')
        current_app.logger.error(f"{e}")
        return redirect(url_for('configuration_files.index'))
    else:
        old_data = b64decode(req.json()['content']).decode('utf-8')
        diffs = list(unified_diff(old_data.splitlines(keepends=True), new_data.splitlines(keepends=True)))
        if not diffs:
            flash(gettext(u'No data to update.'), 'fail')
            return redirect(url_for('configuration_files.index', path=path))
    return render_template('configuration_files/confirm_save.html', path=path, new_data=new_data, old_data=old_data, diffs=diffs, isLogged=True)


@bp.route('/save', methods=('POST',))
@login_required
def save():
    path = request.form.get('path', '')
    data = request.form.get('data')
    user = get_user(user_id=session.get('user_id'))

    if not data:
        flash(gettext(u'No data to update.'), 'fail')
        return redirect(url_for('configuration_files.index'))
    if path:
        try:
            req = GiteaAPI(user['gitea_token']).repo_get_contents(path)
            if isinstance(req.json(), list):
                raise GiteaAPIError('Cannot save a folder, must be a file.')
            GiteaAPI(user['gitea_token']).repo_put_contents(
                path,
                data=json_dumps({'content': str(b64encode(data.encode('utf-8')), 'utf-8'), 'sha': req.json()['sha']})
            )
            flash(gettext(u'File contents updated.'), 'success')
        except (requests.exceptions.RequestException, GiteaAPIError) as e:
            flash(gettext(u'Error file does not exist.'), 'fail')
            current_app.logger.error(f"{e}")
            return redirect(url_for('configuration_files.index'))
    else:
        path = ''
        flash(gettext(u'Error file path is undefined.'), 'fail')
    return redirect(url_for('configuration_files.index', path=path))
