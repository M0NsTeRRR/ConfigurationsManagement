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

from json import dumps as json_dumps

import pika

from flask import current_app
from flask_babel import gettext

from website.db import update_task


class RabbitMQ(object):
    def __init__(self):
        self.host = current_app.config["RABBITMQ_HOST"]
        self.port = current_app.config["RABBITMQ_PORT"]
        self.queue = current_app.config["RABBITMQ_QUEUE"]
        self.login = current_app.config["RABBITMQ_LOGIN"]
        self.password = current_app.config["RABBITMQ_PASSWORD"]
        self.token = current_app.config["WORKER_TOKEN"]
        self.credentials = None
        self.connection = None
        self.channel = None

    def create_task(self, task, id):
        try:
            self.credentials = pika.credentials.PlainCredentials(self.login, self.password)
            self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host, port=self.port, credentials=self.credentials))
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue, durable=True)
            task['worker_token'] = self.token
            self.channel.basic_publish(
                exchange='',
                routing_key=self.queue,
                body=json_dumps(task),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                    content_type='application/json'
                )
            )
            update_task(id, state=1)
            self.connection.close()
        except Exception as e:
            update_task(id, error=1, message=gettext(u'Error when creating task.'))
            current_app.logger.error(f"{e}")
