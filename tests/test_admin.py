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

import pytest
from flask_babel import gettext

from website.admin import create_user_command


def test_index(client, auth):
    # test if user is not logged
    auth.auth_protected("/admin/")

    auth.login()

    # test that viewing the page renders without template errors
    assert client.get("/admin/").status_code == 200


@pytest.mark.parametrize(
    ("login", "password", "confirmed_password", "message"),
    (
        ('', '', '', gettext('Login is required.').encode('utf-8')),
        ('a', '', '', gettext('Password is required.').encode('utf-8')),
        ('a', 'a', '', gettext('Password not confirmed.').encode('utf-8')),
        ('a', 'a', 'b', gettext('Password not confirmed.').encode('utf-8')),
        ('test', 'test', 'test', gettext('User is already registered.').encode('utf-8')),
    ),
)
def test_register_validate_input(client, auth, login, password, confirmed_password, message):
    auth.login()

    response = client.post(
        "/admin/register", data={"login": login, "password": password, "confirmed_password": confirmed_password}
    )
    assert message in response.data


def test_register(client, auth, app):
    # test if user is not logged
    auth.auth_protected("/admin/register")

    auth.login()

    # test that viewing the page renders without template errors
    assert client.get("/admin/register").status_code == 200

    # test that successful registration redirects to the registration page
    response = client.post("/admin/register", data={"login": "a", "password": "a", "confirmed_password": "a"})
    assert "http://localhost/admin/register" == response.headers["Location"]

    # test that the user can log in
    auth.login(login="a", password="a")

    assert client.get("/admin/").status_code == 200


@pytest.mark.parametrize(
    ("password", "confirmed_password", "message"),
    (
        ('', '', gettext('Password is required.').encode('utf-8')),
        ('a', '', gettext('Password not confirmed.').encode('utf-8')),
        ('a', 'b', gettext('Password not confirmed.').encode('utf-8')),
    ),
)
def test_edit_password_validate_input(client, auth, password, confirmed_password, message):
    auth.login()

    response = client.post(
        "/admin/edit_password/test", data={"password": password, "confirmed_password": confirmed_password}
    )
    assert message in response.data


def test_edit_password(client, auth):
    # test if user is not logged
    auth.auth_protected("/admin/edit_password/test")

    auth.login()

    # test that viewing the page renders without template errors
    assert client.get("/admin/edit_password/test").status_code == 200

    # test that non-existent user redirects to the administration page
    response = client.post("/admin/edit_password/fefefe", data={"password": "a", "confirmed_password": "a"})
    assert "http://localhost/admin/" == response.headers["Location"]

    # test that successful edit password redirects to the administration page
    response = client.post("/admin/edit_password/test", data={"password": "a", "confirmed_password": "a"})
    assert "http://localhost/admin/" == response.headers["Location"]

    # test that the user can log in with this new password
    auth.logout()
    auth.login(login="test", password="a")

    assert client.get("/admin/").status_code == 200


def test_remove(client, auth):
    # test if user is not logged
    auth.auth_protected("/admin/delete/test")

    auth.login()

    # test that viewing the page renders without template errors
    assert client.get("/admin/delete/test").status_code == 200

    # test that non-existent user redirects to the administration page
    response = client.post("/admin/delete/fefefe")
    assert "http://localhost/admin/" == response.headers["Location"]

    # test that successful edit password redirects to the administration page
    response = client.post("/admin/delete/test")
    assert "http://localhost/admin/" == response.headers["Location"]

    # test that the user can't log in
    auth.logout()

    response = auth.login()
    assert gettext('Incorrect login/password.').encode('utf-8') in response.data


def test_create_user_command(runner):
    # no login and no password
    assert "Missing argument 'LOGIN'" in runner.invoke(create_user_command, []).output
    # no password
    assert "Missing argument 'PASSWORD'" in runner.invoke(create_user_command, ['a']).output
    # empty password
    assert 'Argument "PASSWORD" can\'t be empty' in runner.invoke(create_user_command, ['a', '']).output
    # empty login
    assert 'Argument "LOGIN" can\'t be empty' in runner.invoke(create_user_command, ['', 'a']).output

    assert 'created' in runner.invoke(create_user_command, ['a', 'a']).output
