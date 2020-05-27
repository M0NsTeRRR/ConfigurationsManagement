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

import pytest
from flask_babel import gettext

from website.db import get_user, get_gitea

# read configuration file
with open(os.path.join(os.path.dirname(__file__), "config.json")) as f:
    config = json.load(f)
config['USER']['GITEA_TEST_TOKEN'] = os.environ.get('GITEA_TEST_TOKEN') or config['USER']['GITEA_TEST_TOKEN']


def test_index(client, auth):
    # test if user is not logged
    auth.auth_protected("/settings/")

    auth.login()

    # test that viewing the page renders without template errors
    assert client.get("/settings/").status_code == 200


@pytest.mark.parametrize(
    ("gitea_token", "message"),
    (
        ('', gettext('Token is required.').encode('utf-8')),
    ),
)
def test_gitea_connect_validate_input(client, auth, gitea_token, message):
    auth.login()
    client.post("/settings/gitea/disconnect", follow_redirects=True)
    response = client.post("/settings/gitea/connect", data={"gitea_token": gitea_token}, follow_redirects=True)
    assert message in response.data


@pytest.mark.parametrize(
    ("gitea_url", "gitea_owner", "gitea_repository", "message"),
    (
        ('', '', '', gettext('Gitea url is required.').encode('utf-8')),
        ('a', '', '', gettext('Owner of the repository is required.').encode('utf-8')),
        ('a', 'a', '', gettext('Name of the repository is required.').encode('utf-8')),
    ),
)
def test_gitea_repository_validate_input(client, auth, gitea_url, gitea_owner, gitea_repository, message):
    auth.login()
    response = client.post(
        "/settings/gitea/repository",
        data={"gitea_url": gitea_url, "gitea_owner": gitea_owner, "gitea_repository": gitea_repository},
        follow_redirects=True
    )
    assert message in response.data


def test_gitea_connect(client, auth, app):
    # test if user is not logged
    auth.auth_protected("/settings/gitea/connect", data={"gitea_token": config["USER"]["GITEA_TEST_TOKEN"]}, method='post')

    auth.login()

    # test that you can't link your account if he is already linked
    response = client.post("/settings/gitea/connect", data={"gitea_token": "aaaaaa"}, follow_redirects=True)
    assert gettext('Your account is already linked with Gitea.').encode('utf-8') in response.data

    # unlink account from gitea
    client.post("/settings/gitea/disconnect", follow_redirects=True)

    # test that account was not linked with fake token
    response = client.post("/settings/gitea/connect", data={"gitea_token": "aaaaaa"}, follow_redirects=True)
    assert gettext('Error account not linked.').encode('utf-8') in response.data

    # test that successful account linked
    response = client.post("/settings/gitea/connect", data={"gitea_token": config["USER"]["GITEA_TEST_TOKEN"]}, follow_redirects=True)
    assert gettext('Your account is now linked with Gitea.').encode('utf-8') in response.data
    with app.app_context():
        assert get_user(login="test")['gitea_token'] == config["USER"]["GITEA_TEST_TOKEN"]


def test_gitea_repository(client, auth, app):
    # test if user is not logged
    auth.auth_protected(
        "/settings/gitea/repository",
        data={"gitea_url": "fff", "gitea_owner": "fff", "gitea_repository": "fff"},
        method='post'
    )

    auth.login()
    # test that successful gitea configuration were edit
    response = client.post(
        "/settings/gitea/repository",
        data={"gitea_url": "fff", "gitea_owner": "fff", "gitea_repository": "fff"},
        follow_redirects=True
    )
    assert gettext('Repository configuration saved.').encode('utf-8') in response.data
    with app.app_context():
        gitea = get_gitea()
        assert gitea['url'] == "fff"
        assert gitea['owner'] == "fff"
        assert gitea['repository'] == "fff"


def test_gitea_disconnect(client, auth, app):
    # test if user is not logged
    auth.auth_protected("/settings/gitea/disconnect", method='post')

    auth.login()

    # test that successful gitea account unlinked
    response = client.post("/settings/gitea/disconnect", follow_redirects=True)
    assert gettext('Your account is no longer linked with Gitea.').encode('utf-8') in response.data
    with app.app_context():
        assert get_user(login="test")['gitea_token'] is None

    # test that you can't unlink gitea account when it isn't linked
    response = client.post("/settings/gitea/disconnect", follow_redirects=True)
    assert gettext('Your account is not linked with Gitea.').encode('utf-8') in response.data


def test_create_api_key(client, auth, app):
    # test if user is not logged
    auth.auth_protected("/settings/api_key/generate", method='post')

    auth.login()

    # test that successful api key generated
    with app.app_context():
        api_key = get_user(login="test")['api_key']
    response = client.post("/settings/api_key/generate", follow_redirects=True)
    assert gettext('New API key generated.').encode('utf-8') in response.data
    with app.app_context():
        assert api_key != get_user(login="test")['api_key']


def test_delete_api_key(client, auth, app):
    # test if user is not logged
    auth.auth_protected("/settings/api_key/delete", method='post')

    auth.login()

    # test that successful api key deleted
    response = client.post("/settings/api_key/delete", follow_redirects=True)
    assert gettext('API key deleted.').encode('utf-8') in response.data
    with app.app_context():
        assert get_user(login="test")['api_key'] is None

    # test that you can't delete API key when you haven't one
    response = client.post("/settings/api_key/delete", follow_redirects=True)
    assert gettext('No API key to delete.').encode('utf-8') in response.data