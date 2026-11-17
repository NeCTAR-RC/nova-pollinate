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

from hvac.api.auth_methods import Kubernetes
from hvac import Client
from hvac import exceptions as hvac_exc

from oslo_config import cfg
from oslo_log import log as logging

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


K8S_TOKEN_PATH = '/var/run/secrets/kubernetes.io/serviceaccount/token'
CACHE_TTL = timedelta(seconds=60)


class PollinateSecrets:
    def __init__(self):
        self._cache = {}  # path -> (fetched_at, data)
        self.k8s_token = None

    def _get_vault_client(self):
        """Authenticate to vault and return a client"""
        # Config provided token (development)
        if CONF.vault.token:
            LOG.debug(
                'Logging in to Vault at: %s with local token', CONF.vault.url
            )
            return Client(
                url=CONF.vault.url,
                token=CONF.vault.token,
                timeout=CONF.vault.timeout,
            )
        # Kubernetes token (production)
        elif CONF.vault.role:
            LOG.debug(
                'Logging in to Vault at: %s with K8s token', CONF.vault.url
            )
            client = Client(url=CONF.vault.url, timeout=CONF.vault.timeout)
            if not self.k8s_token:
                with open(K8S_TOKEN_PATH) as f:
                    self.k8s_token = f.read()
            Kubernetes(client.adapter).login(
                role=CONF.vault.role, jwt=self.k8s_token
            )
            return client
        else:
            raise Exception('No Vault method configured')

    def get_secrets(self, path=None):
        """Return the data at a Vault path (default [vault] path), cached."""
        path = path or CONF.vault.path
        cached = self._cache.get(path)
        if not cached or cached[0] < datetime.now() - CACHE_TTL:
            LOG.debug('Fetching secrets from Vault path %s', path)
            client = self._get_vault_client()
            data = client.secrets.kv.read_secret_version(
                path=path, raise_on_deleted_version=True
            )['data']['data']
            cached = self._cache[path] = (datetime.now(), data)
        return cached[1]

    def get(self, name, path=None):
        """Return one secret; raises KeyError if the path or key is missing."""
        LOG.debug('Searching for secret: %s', name)
        try:
            return self.get_secrets(path)[name]
        except hvac_exc.InvalidPath:
            raise KeyError(path)
