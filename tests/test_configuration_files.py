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
import uuid

import pytest
from flask_babel import gettext

# read configuration file
with open(os.path.join(os.path.dirname(__file__), "config.json")) as f:
    config = json.load(f)
config['USER']['GITEA_TEST_TOKEN'] = os.environ.get('GITEA_TEST_TOKEN') or config['USER']['GITEA_TEST_TOKEN']


def test_index(client, auth):
    # test if user is not logged
    auth.auth_protected("/configuration_files/")

    auth.login()

    # test that viewing the page renders without template errors
    assert client.get("/configuration_files/").status_code == 200

    # test with a folder path
    response = client.get(f"/configuration_files/?path={config['GITEA']['TEST']['PATH_FOLDER']}")
    assert gettext('Error cannot get configuration files from Gitea.').encode('utf-8') not in response.data

    # test with a file path
    response = client.get(f"/configuration_files/?path={config['GITEA']['TEST']['PATH_FILE']}")
    assert gettext('Error cannot get configuration files from Gitea.').encode('utf-8') not in response.data

    # test with a ref
    response = client.get(f"/configuration_files/?ref={config['GITEA']['TEST']['REF']}")
    assert gettext('Error cannot get configuration files from Gitea.').encode('utf-8') not in response.data


@pytest.mark.parametrize(
    ("ref", "path", "message"),
    (
        ('aaaa', '', gettext('Error cannot get configuration files from Gitea.').encode('utf-8')),
        ('', 'aaaa', gettext('Error cannot get configuration files from Gitea.').encode('utf-8')),
    ),
)
def test_index_validate_input(client, auth, ref, path, message):
    auth.login()
    response = client.get(f"/configuration_files/?ref={ref}&path={path}", follow_redirects=True)
    assert message in response.data


def test_remove(auth, client):
    # test if user is not logged
    auth.auth_protected(f"/configuration_files/remove?path={config['GITEA']['TEST']['PATH_FILE']}")

    auth.login()

    # test that viewing the page renders without template errors
    assert client.get(f"/configuration_files/remove?path={config['GITEA']['TEST']['PATH_FILE']}").status_code == 200


@pytest.mark.parametrize(
    ("path", "message"),
    (
        (config['GITEA']['TEST']['PATH_FOLDER'], gettext('Error file does not exist.').encode('utf-8')),
        ('aaaa', gettext('Error file does not exist.').encode('utf-8')),
    ),
)
def test_remove_validate_input(client, auth, path, message):
    auth.login()
    response_get = client.get(f"/configuration_files/remove?path={path}", follow_redirects=True)
    assert message in response_get.data

    response_post = client.post(
        "/configuration_files/remove",
        method='post',
        data={'path': path},
        follow_redirects=True
    )

    assert message in response_post.data


def test_confirm_save(auth, client):
    # test if user is not logged
    auth.auth_protected("/configuration_files/confirm_save", method='post')

    auth.login()

    # test that viewing the page renders without template errors
    assert client.post(
        "/configuration_files/confirm_save",
        method='post',
        data={'path': config['GITEA']['TEST']['PATH_FILE'], 'data': 'unittest'}
    ).status_code == 200


@pytest.mark.parametrize(
    ("path", "data", "message"),
    (
        (config['GITEA']['TEST']['PATH_FOLDER'], 'unittest', gettext('Error file does not exist.').encode('utf-8')),
        ('aaaa', 'unittest', gettext('Error file does not exist.').encode('utf-8')),
    ),
)
def test_confirm_save_validate_input(client, auth, path, data, message):
    auth.login()
    response = client.post(
        "/configuration_files/confirm_save",
        data={'path': path, 'data': data},
        follow_redirects=True
    )
    assert message in response.data


def test_save(auth, client):
    # test if user is not logged
    auth.auth_protected("/configuration_files/save", method='post')

    auth.login()

    # test save
    response = client.post(
        "/configuration_files/save",
        method='post',
        data={
            'path': config['GITEA']['TEST']['PATH_FILE'],
            'data': f'unittest-{uuid.uuid4().hex}'
        },
        follow_redirects=True
    )
    assert gettext(u'File contents updated.').encode('utf-8') in response.data


@pytest.mark.parametrize(
    ("path", "data", "message"),
    (
        (None, '', gettext('No data to update.').encode('utf-8')),
        (config['GITEA']['TEST']['PATH_FOLDER'], 'unittest', gettext('Error file does not exist.').encode('utf-8')),
        ('aaaa', 'unittest', gettext('Error file does not exist.').encode('utf-8')),
    ),
)
def test_save_validate_input(client, auth, path, data, message):
    auth.login()
    response = client.post(
        "/configuration_files/save",
        data={'path': path, 'data': data},
        follow_redirects=True
    )
    assert message in response.data

