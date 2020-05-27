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
import functools
from json.decoder import JSONDecodeError

from flask import (
    Blueprint,
    request,
    url_for,
    g,
    session
)

from flask_restful import (
    Api,
    Resource,
    reqparse
)

from flask_babel import gettext

from website.rabbitmq.rabbitmq import RabbitMQ

from website.gitea.gitea import GiteaAPI
from website.gitea.giteaError import GiteaAPIError

from website.db import (
    get_user,
    get_gitea,
    create_task,
    get_task
)

bp = Blueprint('api', __name__, url_prefix='/api')

api = Api()
api.init_app(bp)


def api_auth_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        api_key = request.headers.get("X-Api-Key")
        user = get_user(api_key=api_key)
        if g.user is None and (user is None or user['api_key'] is None):
            return {"message": gettext(u'ERROR: Unauthorized')}, 401
        return view(**kwargs)
    return wrapped_view


def api_gitea_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        api_key = request.headers.get("X-Api-Key")
        if api_key is None:
            user = get_user(user_id=session.get('user_id'))
        else:
            user = get_user(api_key=api_key)
        if user is None or user['gitea_token'] is None:
            return {"message": gettext(u'ERROR: Gitea Token not configured')}, 503
        try:
            GiteaAPI(user['gitea_token']).repo_get_commits({'sha': 'master'}).json()
        except (JSONDecodeError, GiteaAPIError):
            return {"message": gettext(u'ERROR: Can\'t connect to Gitea server')}, 503
        return view(**kwargs)
    return wrapped_view


tasks_parser = reqparse.RequestParser()
tasks_parser.add_argument('hostname', dest='hostname', type=str, location='json', required=True)
tasks_parser.add_argument('module', dest='module', type=str, location='json', required=True)
tasks_parser.add_argument('action', dest='action', type=str, location='json', required=True)
tasks_parser.add_argument('path', dest='path', type=str, location='json', required=True)


@api.resource('/task/<int:id>')
class GetTask(Resource):
    method_decorators = [api_auth_required]

    def get(self, id):
        """
        Retrieve one task
        ---
        tags:
          - Tasks
        parameters:
          - name: id
            in: path
            description: The id of the task to retrieve
            type: integer
            required: true
        responses:
          200:
            description: Task found
            examples:
                task_1: {
                    'id': 1,
                    'hostname': '192.168.0.1',
                    'module': 'pfsense',
                    'action': 'save',
                    'path': '/pfsense/backup12.zip',
                    'state': '4',
                    'message': '',
                    'start_date': '2020-05-10 22:24:12.104606',
                    'end_date': '2020-05-10 22:24:12.104606',
                    'error': 0
                }
                task_2: {
                    'id': 1,
                    'hostname':
                    'pfsense.test.fr',
                    'module': 'pfsense',
                    'action': 'restore',
                    'path': '/pfsense/backup12.zip',
                    'state': '3',
                    'message': 'Cannot access to server',
                    'start_date': '2020-05-10 22:24:12.104606',
                    'end_date': '2020-05-10 22:24:12.104606',
                    'error': 1
                }
          404:
            description: Task not found
        """
        task = get_task(id)
        if task is None:
            return {"message": gettext(u'ERROR: Not found')}, 404
        else:
            return {
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
            }, 200


@api.resource('/tasks')
class PostTask(Resource):
    method_decorators = {'post': [api_gitea_required, api_auth_required]}

    def post(self):
        """
        Create one task
        ---
        tags:
          - Tasks
        parameters:
          - name: task
            in: body
            description: The task to create
            required: true
            schema:
                required:
                  - hostname
                  - module
                  - action
                  - path
                properties:
                  hostname:
                    type: string
                    example: 192.168.0.1
                  module:
                    type: string
                    example: pfsense
                  action:
                    type: string
                    enum: [save, restore]
                    example: save
                  path:
                    type: string
                    example: /pfsense/backup12.zip
        responses:
          201:
            description: Task created
            examples:
                task_1: { 'id': 1 }
                task_2: { 'id': 2 }
          400:
            description: Task not created
        """
        args = tasks_parser.parse_args()
        if not args.hostname or not args.module or args.action not in ['save', 'restore'] or not args.path:
            return {"message": gettext(u'ERROR: Bad Request')}, 400
        else:
            api_key = request.headers.get("X-Api-Key")
            if api_key is None:
                user = get_user(user_id=session.get('user_id'))
            else:
                user = get_user(api_key=api_key)

            if args.path[0] == '/':
                args.path = args.path[1:]

            gitea = get_gitea()

            id = create_task(args.hostname, args.module, args.action, args.path, datetime.now(timezone.utc))

            rabbit = RabbitMQ()
            rabbit.create_task({
                'id': id,
                'gitea': {
                    'token': user['gitea_token'],
                    'url': gitea['url'],
                    'owner': gitea['owner'],
                    'repository': gitea['repository'],
                },
                'hostname': args.hostname,
                'module': args.module,
                'action': args.action,
                'path': args.path,
            }, id)

            return {'id': id}, 201
