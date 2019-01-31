# Copyright 2016 Red Hat, Inc.
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

import json

from keystoneauth1 import exceptions as keystone_exception
from keystoneauth1 import loading as ks_loading
from keystoneclient.v3 import client as ks_client_v3
from oslo_config import cfg

CFG_GROUP = "service_credentials"

_SESSION = None
_AUTH = None


def get_session():
    """Get a service credentials auth session."""

    global _SESSION  # pylint: disable=global-statement
    global _AUTH  # pylint: disable=global-statement

    if not _AUTH:
        _AUTH = ks_loading.load_auth_from_conf_options(cfg.CONF, CFG_GROUP)
    if not _SESSION:
        _SESSION = ks_loading.load_session_from_conf_options(
            cfg.CONF, CFG_GROUP, auth=_AUTH, session=_SESSION
        )
    return _SESSION


def get_client(trust_id=None):
    """Return a client for keystone v3 endpoint, optionally using a trust."""
    session = get_session()
    return ks_client_v3.Client(session=session, trust_id=trust_id)


def get_service_catalog(client):
    return client.session.auth.get_access(client.session).service_catalog


def get_auth_token(client):
    return client.session.auth.get_access(client.session).auth_token


def register_keystoneauth_opts(conf):
    ks_loading.register_auth_conf_options(conf, CFG_GROUP)
    ks_loading.register_session_conf_options(
        conf, CFG_GROUP,
        deprecated_opts={'cacert': [
            cfg.DeprecatedOpt('os-cacert', group=CFG_GROUP),
            cfg.DeprecatedOpt('os-cacert', group="DEFAULT")]
        })


def get_project(project_id):
    """Given a keystone project-id return the the project."""
    ks = get_client()
    try:
        return ks.projects.get(project_id)
    except keystone_exception.NotFound:
        return None


def get_user(user_id):
    """Given a keystone user-id return the name of the user."""
    # Handle case where no credentials are configured
    try:
        ks = get_client()
    except cfg.NoSuchOptError:
        return None

    try:
        return ks.users.get(user_id)
    except keystone_exception.NotFound:
        return None


def get_credentials(project_id):
    try:
        ks = get_client()
    except cfg.NoSuchOptError:
        return None

    try:
        creds = ks.credentials.list(type='cloudstor')
        data = next(c.blob for c in creds if c.project_id == project_id)
        return json.loads(data)
    except StopIteration:
        return None
