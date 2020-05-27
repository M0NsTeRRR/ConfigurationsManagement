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
import pytest
import json
from flask_babel import gettext


@pytest.mark.parametrize(
    ("hostname", "module", "action", "path", "message"),
    (
        ('', '', '', '', gettext(u'Hostname is required.').encode('utf-8')),
        ('a', '', '', '', gettext(u'Module is required.').encode('utf-8')),
        ('a', 'a', '', '', gettext(u'Action is required.').encode('utf-8')),
        ('a', 'a', 'a', '', gettext(u'Action is required.').encode('utf-8')),
        ('a', 'a', 'save', '', gettext(u'Path is required.').encode('utf-8')),
    ),
)
def test_index_input(client, auth, hostname, module, action, path, message):
    auth.login()

    response = client.post(
        "/tasks/",
        data={'hostname': hostname, 'module': module, 'action': action, 'path': path},
        follow_redirects=True
    )
    assert message in response.data


def test_index(client, auth):
    # test if user is not logged
    auth.auth_protected("/tasks/")

    auth.login()

    # test that viewing the page renders without template errors
    assert client.get("/tasks/").status_code == 200

    # test that POST request create a task
    response = client.post(
        "/tasks/",
        data={'hostname': 'pfsense.test', 'module': 'pfsense', 'action': 'save', 'path': '/pfsense/backup12.zip'},
    )
    assert "http://localhost/tasks/task/7" == response.headers["Location"]


def test_tasks(client, auth):
    # test if user is not logged
    auth.auth_protected("/tasks/tasks")

    auth.login()

    # test that viewing the page renders without template errors
    assert client.get("/tasks/tasks").status_code == 200

    # test with a page index different from a number
    assert client.get("/tasks/tasks?page=aaaaa").headers["Location"] == "http://localhost/tasks/tasks?page=1"

    # test with a page index under 1
    assert client.get("/tasks/tasks?page=0").headers["Location"] == "http://localhost/tasks/tasks?page=1"

    # test with a page that doesn't exist
    assert client.get("/tasks/tasks?page=200").headers["Location"] == "http://localhost/tasks/tasks?page=1"


def test_task_404(client, auth):
    auth.login()

    assert client.get("/tasks/task/50").headers["Location"] == "http://localhost/tasks/"

    response = client.get("/tasks/task/50?json")
    assert response.status_code == 404


@pytest.mark.parametrize(
    ("id", "worker_token", "state", "error", "message", "end_date", "error_message", "status_code"),
    (
        (12, "dev", 1, 0, 'fff', datetime.now(timezone.utc), "ERROR: Not found", 404),
        (1, "dev", 'aaa', 0, 'fff', datetime.now(timezone.utc), "ERROR: Bad Request", 400),
        (1, "dev", 1, 'aaa', 'fff', datetime.now(timezone.utc), "ERROR: Bad Request", 400),
    ),
)
def test_put_task_input(client, auth, id, worker_token, state, error, message, end_date, error_message, status_code):
    response = client.put(
        f"/tasks/task/{id}",
        data={'worker_token': worker_token, 'state': state, 'error': error, 'message': message, 'end_date': end_date}
    )
    assert status_code == response.status_code
    assert error_message in response.data.decode('utf8')


def test_put_task(client, auth):
    # test without token
    assert client.put("/tasks/task/1").status_code == 401

    # test update
    assert client.put(
        "/tasks/task/1",
        data={'worker_token': 'dev', 'state': 1, 'error': 0, 'message': 'fff', 'end_date': datetime.now(timezone.utc)}
    ).status_code == 204


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
    auth.auth_protected(f"/tasks/task/{id}")

    auth.login()

    # test that viewing the page renders without template errors
    assert client.get(f"/tasks/task/{id}").status_code == 200

    # test that viewing the page renders without template errors
    response = client.get(f"/tasks/task/{id}?json")
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
