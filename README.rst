Nectar dynamic vendordata API
=============================

This Python package provides a dynamic vendordata plugin for the OpenStack
nova metadata service for the Nectar Research Cloud.

Build
=====

In this directory, run::

  python setup.py build


Installation
============

In this directory, run::

  python setup.py install


Configuration
=============

nova needs to be configured to enable the vendordata REST service,
for example: **/etc/nova/nova.conf**::

  [api]
  vendordata_providers = DynamicJSON
  vendordata_dynamic_targets = 'nectar@http://127.0.0.1:8912/v1/'
  vendordata_dynamic_connect_timeout = 5
  vendordata_dynamic_read_timeout = 30

Vendordata enables keystone authentication by default, as seen in
**/etc/vendordata/api-paste.ini**. So credentials need to be set for
nova to be able to communicate with vendordata. This we can set in the
``[vendordata_dynamic_auth]`` section of **/etc/nova/nova.conf**::

  [vendordata_dynamic_auth]
  # Options within this group control the authentication of the vendordata
  # subsystem of the metadata API server (and config drive) with external
  # systems.
  auth_type = v3password
  auth_url = < keystone auth url >
  username = < service user >
  password = < service user password  >
  project_name = < service project >
  user_domain_name = < service user domain >
  project_domain_name = < service project domain >

It is possible to just use the nova credentials here; or create a user just for
this. So choose depending on your requirements.

Metadata REST Service Configuration
===================================

The REST service is configured in **/etc/vendordata/vendordata.conf** in the
DEFAULT section. It provides the following options:

- vendordata_listen_port: The TCP port to listen on. Defaults to 8912.
- api_paste_config: The paste configuration file to use.
- debug: Enable additional debugging output. Default is False.
- auth_strategy: The authentication strategy to use

One must also configure the authtoken middleware in **/etc/vendordata/vendordata.conf** as
specified in the `Keystone middleware documentation`_.

.. _`Keystone middleware documentation`: https://docs.openstack.org/developer/keystonemiddleware/middlewarearchitecture.html#configuration


Logging
=======

The REST vendordata service logs by default to
/var/log/vendordata/vendordata.log

A logrotate script for this is::

  /var/log/vendordata/*log {
      weekly
      rotate 14
      size 10M
      missingok
      compress
  }


Copyright and License
=====================

Copyright Australian Research Data Commons, 2018

   Licensed under the Apache License, Version 2.0 (the "License"); you may
   not use this file except in compliance with the License. You may obtain
   a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
   License for the specific language governing permissions and limitations
   under the License.
