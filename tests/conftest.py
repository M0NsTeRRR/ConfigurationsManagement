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
import json
import tempfile

import pytest

from flask import request

from flask_wtf.csrf import CSRFProtect

from flask_babel import Babel

from website import create_app
from website.db import (
    get_db,
    init_db,
    update_token,
    update_gitea
)

# read configuration file
with open(os.path.join(os.path.dirname(__file__), "config.json")) as f:
    config = json.load(f)
config['USER']['GITEA_TEST_TOKEN'] = os.environ.get('GITEA_TEST_TOKEN') or config['USER']['GITEA_TEST_TOKEN']

# read in SQL for populating test data
with open(os.path.join(os.path.dirname(__file__), "data.sql"), "rb") as f:
    _data_sql = f.read().decode("utf8")


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # create a temporary file to isolate the database for each test
    db_fd, db_path = tempfile.mkstemp()
    # create the app with common test config
    app = create_app({
        "DEBUG": False,
        "TESTING": True,
        "SECRET_KEY": "dev",
        "TIMEZONE": "Europe/Paris",
        "WORKER_TOKEN": "dev",
        "RABBITMQ_HOST": "localhost",
        "RABBITMQ_PORT": 5672,
        "RABBITMQ_QUEUE": "tasks",
        "RABBITMQ_LOGIN": "test",
        "RABBITMQ_PASSWORD": "test",
        "API_ENABLE": True,
        "API_KEY": "dev",
        "API_CORS_ALLOW_ORIGINS": "*",
        "DATABASE": db_path,
        "WTF_CSRF_ENABLED": False
    })

    # create the database and load test data
    with app.app_context():
        init_db()
        get_db().executescript(_data_sql)
        update_token(1, config['USER']['GITEA_TEST_TOKEN'])
        update_gitea(
            config['GITEA']['TEST_URL'],
            config['GITEA']['TEST_OWNER'],
            config['GITEA']['TEST_REPOSITORY']
        )

    babel = Babel(app)

    @babel.localeselector
    def get_locale():
        return request.accept_languages.best_match(['fr', 'en'], 'en')

    CSRFProtect(app)

    yield app

    # close and remove the temporary database
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login(self, login="test", password="test"):
        return self._client.post(
            "/auth/login", data={"login": login, "password": password}
        )

    def auth_protected(self, url, data=None, method='get'):
        self.logout()
        if method == 'get':
            req = self._client.get(f'{url}', data=data)
        else:
            req = self._client.post(f'{url}', data=data)

        assert "http://localhost/auth/login" == req.headers["Location"]

    def logout(self):
        return self._client.get("/auth/logout")


@pytest.fixture
def auth(client):
    return AuthActions(client)
