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

import requests
from urllib.parse import quote_plus, urlunparse, urlparse

from website.db import get_gitea
from website.gitea.giteaError import GiteaAPIError


class GiteaAPI(object):
    api_endpoint = '/api/v1'
    user_endpoint = 'user'
    repo_endpoint = 'repos'

    def __init__(self, token=""):
        gitea = get_gitea()
        self.url = gitea['url']
        self.owner = gitea['owner']
        self.repository = gitea['repository']
        self.token = token

    def user_get_current(self):
        return self.__get(
            f'/{GiteaAPI.user_endpoint}'
        )

    def repo_get_contents_list(self, params=None):
        return self.__get(
            f'/{GiteaAPI.repo_endpoint}/{self.owner}/{self.repository}/contents',
            params=params
        )

    def repo_get_contents(self, filepath, params=None):
        return self.__get(
            f'/{GiteaAPI.repo_endpoint}/{self.owner}/{self.repository}/contents/{quote_plus(str(filepath))}',
            params=params
        )

    def repo_get_commits(self, params=None):
        return self.__get(
            f'/{GiteaAPI.repo_endpoint}/{self.owner}/{self.repository}/commits',
            params=params
        )

    def repo_post_contents(self, filepath, params=None):
        return self.__post(
            f'/{GiteaAPI.repo_endpoint}/{self.owner}/{self.repository}/contents/{quote_plus(str(filepath))}',
            params=params
        )

    def repo_put_contents(self, filepath, data=None):
        return self.__put(
            f'/{GiteaAPI.repo_endpoint}/{self.owner}/{self.repository}/contents/{quote_plus(str(filepath))}',
            data=data,
            headers={'Content-type': 'application/json'}
        )

    def repo_delete_contents(self, filepath, data=None):
        return self.__delete(
            f'/{GiteaAPI.repo_endpoint}/{self.owner}/{self.repository}/contents/{quote_plus(str(filepath))}',
            data=data,
            headers={'Content-type': 'application/json'}
        )

    def __get(self, path, params=None, headers=None):
        try:
            req = requests.get(self.__url(path), params=params, headers=self.__headers(headers))
            self.__class__._unauthorized(req)
            return req
        except requests.exceptions.RequestException as e:
            raise GiteaAPIError(e)

    def __put(self, path, data=None, headers=None):
        try:
            req = requests.put(self.__url(path), headers=self.__headers(headers), data=data)
            self.__class__._unauthorized(req)
            return req
        except requests.exceptions.RequestException as e:
            raise GiteaAPIError(e)

    def __post(self, path, params=None, headers=None):
        try:
            req = requests.post(self.__url(path), params=params, headers=self.__headers(headers))
            self.__class__._unauthorized(req)
            return req
        except requests.exceptions.RequestException as e:
            raise GiteaAPIError(e)

    def __delete(self, path, data=None, headers=None):
        try:
            req = requests.delete(self.__url(path), headers=self.__headers(headers), data=data)
            self.__class__._unauthorized(req)
            return req
        except requests.exceptions.RequestException as e:
            raise GiteaAPIError(e)

    def __url(self, path):
        base_url = urlparse(self.url)
        url = urlunparse((
            base_url.scheme,
            base_url.netloc + GiteaAPI.api_endpoint,
            path,
            '',
            '',
            ''
        ))
        return url

    def __headers(self, headers):
        if headers:
            headers['Authorization'] = f'token {self.token}'
        else:
            headers = {'Authorization': f'token {self.token}'}
        return headers

    @staticmethod
    def _unauthorized(req):
        if req.status_code == 401:
            raise GiteaAPIError('Unauthorized')
        elif req.status_code == 404:
            raise GiteaAPIError('Not found')
        elif req.status_code == 500:
            raise GiteaAPIError('Gitea server error')
