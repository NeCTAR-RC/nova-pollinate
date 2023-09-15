# Copyright 2023 Australian Research Data Commons
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from datetime import datetime
from datetime import timedelta

from hvac import Client
from hvac.api.auth_methods import Kubernetes

from oslo_config import cfg
from oslo_log import log as logging

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


K8S_TOKEN_PATH = '/var/run/secrets/kubernetes.io/serviceaccount/token'


class PollinateSecrets():

    def __init__(self):
        self.vault_client = None
        self.secrets_fetched = None
        self.secrets = None
        self.k8s_token = None

    def _get_vault_client(self):
        """Authenticate to vault and return a client"""
        if not self.vault_client:
            # Config provided token (development)
            if CONF.vault.token:
                LOG.debug('Logging in to Vault at: %s with local token',
                          CONF.vault.url)
                self.vault_client = Client(
                    url=CONF.vault.url, token=CONF.vault.token)
            # Kubernetes token (production)
            elif CONF.vault.role:
                LOG.debug('Logging in to Vault at: %s with K8s token',
                          CONF.vault.url)
                client = Client(url=CONF.vault.url)
                if not self.k8s_token:
                    with open(K8S_TOKEN_PATH, 'r') as f:
                        self.k8s_token = f.read()
                Kubernetes(client.adapter).login(
                    role=CONF.vault.role, jwt=self.k8s_token)
                self.vault_client = client
            else:
                raise Exception('No Vault method configured')
        return self.vault_client

    def get_secrets(self):
        if not self.secrets_fetched or \
                self.secrets_fetched < datetime.now() - timedelta(seconds=60):
            LOG.debug('Using cached secrets')
            client = self._get_vault_client()
            self.secrets = client.secrets.kv.read_secret_version(
                path=CONF.vault.path,
                raise_on_deleted_version=True)
            self.secrets_fetched = datetime.now()
        return self.secrets['data']['data']

    def get(self, name):
        LOG.debug('Searching for secret: %s', name)
        secrets = self.get_secrets()
        return secrets[name]  # Raise exception if not found
