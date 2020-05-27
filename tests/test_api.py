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

# read configuration file
with open(os.path.join(os.path.dirname(__file__), "config.json")) as f:
    config = json.load(f)
config['USER']['GITEA_TEST_TOKEN'] = os.environ.get('GITEA_TEST_TOKEN') or config['USER']['GITEA_TEST_TOKEN']


def test_api_gitea_required(client, auth):
    auth.login()
    # test with wrong gitea url
    client.post(
        "/settings/gitea/repository",
        data={"gitea_url": "fff", "gitea_owner": "fff", "gitea_repository": "fff"},
        follow_redirects=True
    )
    assert client.post(
        "/api/tasks",
        json={'hostname': '192.168.0.1', 'module': 'pfsense', 'action': 'save', 'path': '/pfsense/backup12.zip'},
        headers={'X-Api-Key': 'API_KEY'}
    ).status_code == 503

    # reset gitea repository config
    client.post(
        "/settings/gitea/repository",
        data={"gitea_url": config["GITEA"]["TEST_URL"], "gitea_owner": config["GITEA"]["TEST_OWNER"], "gitea_repository": config["GITEA"]["TEST_REPOSITORY"]},
        follow_redirects=True
    )

    # test with gitea token not configured
    client.post("/settings/gitea/disconnect")
    assert client.post(
        "/api/tasks",
        json={'hostname': '192.168.0.1', 'module': 'pfsense', 'action': 'save', 'path': '/pfsense/backup12.zip'},
        headers={'X-Api-Key': 'API_KEY'}
    ).status_code == 503


def test_docs(client, auth):
    # test if user is not logged
    assert client.get("/api/docs").status_code == 401
    assert client.get("/api/docs.json").status_code == 401

    # test with API key
    assert client.get("/api/docs", headers={'X-Api-Key': 'API_KEY'}).status_code == 200
    assert client.get("/api/docs.json", headers={'X-Api-Key': 'API_KEY'}).status_code == 200

    # test if user is logged
    auth.login()
    assert client.get("/api/docs").status_code == 200
    assert client.get("/api/docs.json").status_code == 200


@pytest.mark.parametrize(
    ("id", "message"),
    (
        ('a', gettext('ERROR: Not found').encode('utf-8')),
        (80, gettext('ERROR: Not found').encode('utf-8')),
    ),
)
def test_get_task_input(client, auth, id, message):
    response = client.get(f"/api/task/{id}", headers={'X-Api-Key': 'API_KEY'})
    assert message in response.data


@pytest.mark.parametrize(
    ("id", "hostname", "module", "action", "path", "state", "error", "message", "start_date", "end_date"),
    (
        (1, 'pfsense.test', 'pfsense', 'save', '/pfsense/backup12.zip', 3, 1, 'Error', '2020-05-10 22:24:12.104606', '2020-05-10 22:24:12.104606'),
        (2, '192.168.0.1', 'pfsense', 'restore', '/pfsense/backup12.zip', 4, 0, None, '2020-05-10 22:24:12.104606', '2020-05-10 22:24:12.104606'),
        (3, '192.168.0.1', 'pfsense', 'save', '/pfsense/backup12.zip', 4, 0, None, '2020-05-10 22:24:12.104606', '2020-05-10 22:24:12.104606'),
        (4, '192.168.0.1', 'pfsense', 'save', '/pfsense/backup12.zip', 3, 0, None, '2020-05-10 22:24:12.104606', None),
        (5, '192.168.0.1', 'pfsense', 'save', '/pfsense/backup12.zip', 2, 0, None, '2020-05-10 22:24:12.104606', None),
        (6, '192.168.0.1', 'pfsense', 'save', '/pfsense/backup12.zip', 1, 0, None, '2020-05-10 22:24:12.104606', None)
    ),
)
def test_get_task(client, auth, id, hostname, module, action, path, state, error, message, start_date, end_date):
    # test if user is not logged
    assert client.get(f"/api/task/{id}").status_code == 401

    # test with API key
    response = client.get(f"/api/task/{id}", headers={'X-Api-Key': 'API_KEY'})
    assert response.status_code == 200
    assert json.loads(json.dumps({
        "id": id,
        "hostname": hostname,
        "module": module,
        "action": action,
        "path": path,
        "state": state,
        "message": message,
        "start_date": start_date,
        "end_date": end_date,
        "error": error
    })) == json.loads(response.data)

    # test if user is logged
    auth.login()
    response = client.get(f"/api/task/{id}")
    assert response.status_code == 200
    assert json.loads(json.dumps({
        "id": id,
        "hostname": hostname,
        "module": module,
        "action": action,
        "path": path,
        "state": state,
        "message": message,
        "start_date": start_date,
        "end_date": end_date,
        "error": error
    })) == json.loads(response.data)


@pytest.mark.parametrize(
    ("hostname", "module", "action", "path"),
    (
        ('', '', '', ''),
        ('a', '', '', ''),
        ('a', 'a', '', ''),
        ('a', 'a', 'a', ''),
        ('a', 'a', 'save', ''),
        ('a', 'a', 'a', 'a'),
    ),
)
def test_post_task_input(client, auth, hostname, module, action, path):
    response = client.post(
        "/api/tasks",
        json={'hostname': hostname, 'module': module, 'action': action, 'path': path},
        headers={'X-Api-Key': 'API_KEY'}
    )
    assert response.status_code == 400
    assert json.dumps({"message": gettext(u'ERROR: Bad Request')}) in response.data.decode('utf8')


def test_post_task(client, auth):
    # test if user is not logged
    assert client.post("/api/tasks").status_code == 401

    # test with API key
    request = client.post(
        "/api/tasks",
        json={'hostname': '192.168.0.1', 'module': 'pfsense', 'action': 'save', 'path': '/pfsense/backup12.zip'},
        headers={'X-Api-Key': 'API_KEY'}
    )
    assert request.status_code == 201
    assert json.dumps({'id': 7}) in request.data.decode('utf8')

    # test if user is logged
    auth.login()
    request = client.post(
        "/api/tasks",
        json={'hostname': '192.168.0.1', 'module': 'pfsense', 'action': 'save', 'path': '/pfsense/backup12.zip'}
    )
    assert request.status_code == 201
    assert json.dumps({'id': 8}) in request.data.decode('utf8')
