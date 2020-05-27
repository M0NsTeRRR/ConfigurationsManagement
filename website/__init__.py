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

import os
import string
import secrets
from sys import exit as sys_exit

from pytz import all_timezones

from flask import (
    Flask,
    request,
    redirect,
    url_for,
    send_from_directory
)

from flask_cors import CORS

from flask_babel import Babel, gettext, format_datetime

from flasgger import Swagger, LazyString, LazyJSONEncoder

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from . import (
    db,
    auth,
    configuration_files,
    tasks,
    settings,
    admin,
    api,
    errors,
    csrf
)

from .api import api_auth_required

from .csrf import csrf_protect


def create_app(test_config=None):
    # generate a random token used by workers
    alphabet = string.ascii_letters + string.digits + string.punctuation
    token = ''.join(secrets.choice(alphabet) for _ in range(secrets.randbelow(30) + 50))

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        WORKER_TOKEN=token,
        DATABASE=os.path.join(app.instance_path, 'db.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)

        # load environment variables
        app.config['DEBUG'] = bool(os.environ.get('DEBUG') or app.config.get('DEBUG', False))
        app.config['TESTING'] = bool(os.environ.get('TESTING') or app.config.get('TESTING', False))
        if os.environ.get('SECRET_KEY'):
            app.config['SECRET_KEY'] = bytes(os.environ.get('SECRET_KEY'), encoding='utf8')
        app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME') or app.config.get('SERVER_NAME', None)
        app.config['TIMEZONE'] = os.environ.get('TIMEZONE') or app.config.get('TIMEZONE', 'Europe/Paris')

        app.config['RABBITMQ_HOST'] = os.environ.get('RABBITMQ_HOST') or app.config.get('RABBITMQ_HOST', 'localhost')
        app.config['RABBITMQ_PORT'] = int(os.environ.get('RABBITMQ_PORT') or app.config.get('RABBITMQ_PORT', 5672))
        app.config['RABBITMQ_QUEUE'] = os.environ.get('RABBITMQ_QUEUE') or app.config.get('RABBITMQ_QUEUE', 'tasks')

        app.config['API_ENABLE'] = bool(os.environ.get('API_ENABLE') or app.config.get('API_ENABLE', False))
        if os.environ.get('API_CORS_ALLOW_ORIGINS'):
            app.config['API_CORS_ALLOW_ORIGINS'] = os.environ.get('API_CORS_ALLOW_ORIGINS')
            if ',' in app.config['API_CORS_ALLOW_ORIGINS']:
                app.config['API_CORS_ALLOW_ORIGINS'] = app.config['API_CORS_ALLOW_ORIGINS'].split(',')

        app.config['SENTRY_DSN'] = bool(os.environ.get('SENTRY_DSN') or app.config.get('SENTRY_DSN', ''))
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    if not app.config['TIMEZONE'] in all_timezones:
        app.logger.error(gettext(u'ERROR: TIMEZONE is not filled properly'))
        sys_exit(1)
    if not app.config['SECRET_KEY']:
        app.logger.error(gettext(u'ERROR: SECRET_KEY is not filled properly'))
        sys_exit(1)

    CORS(app, resources={r"/api/*": {"origins": app.config.get("API_CORS_ALLOW_ORIGINS", "http://localhost")}})

    # init sentry
    sentry_dsn = app.config.get("SENTRY_DSN", "")
    if sentry_dsn:
        sentry_sdk.init(
            sentry_dsn,
            integrations=[FlaskIntegration()]
        )

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    babel = Babel(app, default_timezone=app.config['TIMEZONE'])

    @babel.localeselector
    def get_locale():
        return request.accept_languages.best_match(['fr', 'en'], 'en')

    @app.template_filter('datetime')
    def jinja_format_datetime(dt, format='short'):
        if dt is None:
            return ""
        return format_datetime(dt, format=format)

    csrf_protect.init_app(app)

    db.init_app(app)
    admin.init_app(app)

    app.register_blueprint(auth.bp)
    app.register_blueprint(configuration_files.bp)
    app.register_blueprint(tasks.bp)
    app.register_blueprint(settings.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(errors.bp)
    app.register_blueprint(csrf.bp)

    if app.config['API_ENABLE']:
        app.json_encoder = LazyJSONEncoder
        app.config['SWAGGER'] = {
            'title': 'ConfigurationsManagement API',
            'uiversion': 3
        }
        template = dict(
            info={
                'title': LazyString(lambda: 'ConfigurationsManagement API'),
                'version': LazyString(lambda: '1.0.0'),
                'description': LazyString(lambda: ''),
                'termsOfService': LazyString(lambda: ''),
                'license': {
                    'name': 'CeCILL v2.1'
                }
            },
            basePath='/',
            securityDefinitions={
                'APIKeyHeader': {
                    'type': 'apiKey',
                    'in': 'header',
                    'name': 'X-API-Key'
                }
            },
            security=[
                {'APIKeyHeader': []},
            ]
        )
        swagger_config = {
            "headers": [],
            "specs": [
                {
                    "endpoint": 'docs',
                    "route": '/api/docs.json',
                    "rule_filter": lambda rule: True,  # all in
                    "model_filter": lambda tag: True,  # all in
                }
            ],
            "static_url_path": "/flasgger_static",
            "swagger_ui": True,
            "specs_route": "/api/docs"
        }
        Swagger(app, template=template, config=swagger_config, decorators=[api_auth_required])

        app.register_blueprint(api.bp)
        csrf_protect.exempt(api.bp)

    @app.route("/ping")
    def hello():
        return "OK", 200

    @app.route('/')
    def index():
        return redirect(url_for('tasks.index'), code=302)

    @app.route('/favicon.ico')
    def favicon():
        return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

    return app
