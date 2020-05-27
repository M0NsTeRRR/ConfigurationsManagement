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

from datetime import datetime, timezone
from math import ceil as math_ceil

from flask import (
    Blueprint,
    render_template,
    current_app,
    redirect,
    url_for,
    request,
    session,
    flash
)

from flask_babel import gettext

from website.csrf import csrf_protect

from website.auth import login_required

from website.rabbitmq.rabbitmq import RabbitMQ

from website.gitea.utils import gitea_required

from website.db import (
    get_user,
    get_gitea,
    create_task,
    update_task,
    get_task,
    get_tasks,
    get_nb_tasks
)

bp = Blueprint('tasks', __name__, url_prefix='/tasks')


@bp.route('/', methods=('GET', 'POST'))
@login_required
@gitea_required
def index():
    if request.method == 'POST':
        hostname = request.form.get('hostname')
        module = request.form.get('module')
        action = request.form.get('action')
        path = request.form.get('path')
        error = None

        if not hostname:
            error = gettext(u'Hostname is required.')
        elif not module:
            error = gettext(u'Module is required.')
        elif action not in ['save', 'restore']:
            error = gettext(u'Action is required.')
        elif not path:
            error = gettext(u'Path is required.')

        if error:
            flash(error, 'fail')
            return redirect(url_for('tasks.index'))

        if path[0] == '/':
            path = path[1:]

        user = get_user(user_id=session.get('user_id'))
        gitea = get_gitea()

        id = create_task(hostname, module, action, path, datetime.now(timezone.utc))

        rabbit = RabbitMQ()
        rabbit.create_task({
            'id': id,
            'gitea': {
                'token': user['gitea_token'],
                'url': gitea['url'],
                'owner': gitea['owner'],
                'repository': gitea['repository'],
            },
            'hostname': hostname,
            'module': module,
            'action': action,
            'path': path,
        }, id)
        return redirect(url_for('tasks.task', id=id))
    else:
        return render_template('tasks/index.html', isLogged=True)


@bp.route('/tasks', methods=('GET',))
@login_required
def tasks():
    page = request.args.get('page', '1')
    try:
        page = int(page)
    except ValueError:
        return redirect(url_for('tasks.tasks', page=1))
    if page < 1:
        return redirect(url_for('tasks.tasks', page=1))
    nb = 20
    offset = (page - 1) * nb
    tasks = get_tasks(nb, offset)
    if page != 1 and not tasks:
        return redirect(url_for('tasks.tasks', page=1))
    nb_pages = math_ceil(get_nb_tasks() / nb)
    return render_template('tasks/tasks.html', page=page, nbPages=nb_pages, tasks=tasks, isLogged=True)


@bp.route('/task/<int:id>', methods=('GET',))
@login_required
def task(id):
    task = get_task(id)
    json = request.args.get('json')

    if task is None:
        if json is None:
            flash(gettext(u'Task doesn\'t exist.'), 'fail')
            return redirect(url_for('tasks.index'))
        else:
            return {"message": "ERROR: Not found"}, 404
    task_json = {
       'id': task['id'],
       'hostname': task['hostname'],
       'module': task['module'],
       'action': task['action'],
       'path': task['path'],
       'state': task['state'],
       'message': task['message'],
       'start_date': task['start_date'].strftime("%Y-%m-%d %H:%M:%S.%f"),
       'end_date': task['end_date'].strftime("%Y-%m-%d %H:%M:%S.%f") if task['end_date'] else task['end_date'],
       'error': task['error']
    }
    if json is not None:
        return task_json, 200
    else:
        return render_template('tasks/task.html', task=task, task_json=task_json, isLogged=True)


@csrf_protect.exempt
@bp.route('/task/<int:id>', methods=('PUT',))
def task_worker(id):
    task = get_task(id)
    token = request.form.get('worker_token')

    if current_app.config["WORKER_TOKEN"] != token:
        return {"message": gettext(u'ERROR: Unauthorized')}, 401
    if task is None:
        return {"message": gettext(u'ERROR: Not found')}, 404

    state = request.form.get('state')
    error = request.form.get('error')
    message = request.form.get('message')
    end_date = request.form.get('end_date')

    try:
        if state:
            state = int(state)
        if error:
            error = int(error)
    except ValueError:
        return {"message": gettext(u'ERROR: Bad Request')}, 400

    update_task(id, state=state, error=error, message=message, end_date=end_date)

    if state is not None and state == 3 and error is None:
        update_task(id, state=4)
    return {"message": "SUCCESS: Updated"}, 204
