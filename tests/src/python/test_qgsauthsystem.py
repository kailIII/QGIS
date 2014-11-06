# -*- coding: utf-8 -*-
"""QGIS Unit tests for core QgsAuthManager class

From build dir: ctest -R PyQgsAuthManager -V

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""
__author__ = 'Larry Shaffer'
__date__ = '2014/11/05'
__copyright__ = 'Copyright 2014, Boundless Spatial, Inc.'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '$Format:%H$'

import os
import tempfile
import time

from qgis.core import (
    QgsAuthType,
    QgsAuthManager,
    QgsAuthProvider,
    QgsAuthProviderBasic,
    QgsAuthProviderPkiPaths,
    QgsAuthProviderPkiPkcs12,
    QgsAuthConfigBase,
    QgsAuthConfigBasic,
    QgsAuthConfigPkiPaths,
    QgsAuthConfigPkiPkcs12
)

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from utilities import (
    TestCase,
    getQgisTestApp,
    unittest,
    expectedFailure,
    unitTestDataPath,
)

QGISAPP, CANVAS, IFACE, PARENT = getQgisTestApp()


class TestQgsAuthManager(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.authm = QgsAuthManager.instance()
        cls.authdbdir = tempfile.mkdtemp()
        cls.authm.init(cls.authdbdir)
        msg = 'Auth db could not be created in temp dir'
        assert os.path.exists(cls.authm.authenticationDbPath()), msg

        db1 = QFileInfo(cls.authm.authenticationDbPath()).canonicalFilePath()
        db2 = QFileInfo(cls.authdbdir + '/qgis-auth.db').canonicalFilePath()
        msg = 'Auth db path does not match db path of manager'
        assert db1 == db2, msg

    def setUp(self):
        testid = self.id().split('.')
        testheader = '\n#####_____ {0}.{1} _____#####\n'. \
            format(testid[1], testid[2])
        qDebug(testheader)

        if (not self.authm.masterPasswordIsSet()
                or not self.authm.masterPasswordHashInDb()):
            self.set_master_password()

    def set_master_password(self):
        msg = 'Failed to store and verify master password in auth db'
        assert self.authm.setMasterPassword('pass', True), msg

    def test_01_master_password(self):
        msg = 'Master password is not set'
        self.assertTrue(self.authm.masterPasswordIsSet(), msg)

        msg = 'Master password hash is not in database'
        self.assertTrue(self.authm.masterPasswordHashInDb(), msg)

        msg = 'Master password not verified against hash in database'
        self.assertTrue(self.authm.verifyMasterPassword(), msg)

        msg = 'Master password comparison dissimilar'
        self.assertTrue(self.authm.masterPasswordSame('pass'), msg)

        msg = 'Master password not unset'
        self.authm.clearMasterPassword()
        self.assertFalse(self.authm.masterPasswordIsSet(), msg)

        msg = 'Master password not reset and validated'
        self.assertTrue(self.authm.setMasterPassword('pass', True), msg)

    def test_02_auth_configid(self):
        msg = 'Could not generate a config id'
        self.assertIsNotNone(self.authm.uniqueConfigId(), msg)

        uids = []
        for _ in xrange(50):
            # time.sleep(0.01)  # or else the salt is not random enough
            uids.append(self.authm.uniqueConfigId())
        msg = 'Generated 50 config ids are not unique:\n{0}\n{1}'.format(
            uids,
            list(set(uids))
        )
        self.assertEqual(len(uids), len(list(set(uids))), msg)

    def config_obj(self, kind, base=True):
        if kind == 'Basic':
            config = QgsAuthConfigBasic()
            if base:
                return config
            config.setName(kind)
            config.setRealm('Realm')
            config.setUri('http://example.com')
            config.setUsername('username')
            config.setPassword('password')
            return config

    def config_values_valid(self, kind, config):
        if kind == 'Basic':
            """:type config: QgsAuthConfigBasic"""
            return (
                config.name() == kind
                and config.realm() == 'Realm'
                and config.uri() == 'http://example.com'
                and config.username() == 'username'
                and config.password() == 'password'
            )

    def test_03_auth_configs(self):
        # these list items need to match the QgsAuthType provider type strings
        for kind in ['Basic']:
            config = self.config_obj(kind, base=False)
            msg = 'Could not validate {0} config'.format(kind)
            self.assertTrue(config.isValid(), msg)

            msg = 'Could not store {0} config'.format(kind)
            self.assertTrue(self.authm.storeAuthenticationConfig(config), msg)

            configid = config.id()
            msg = 'Could not retrieve {0} config id from store op'.format(kind)
            self.assertIsNotNone(configid, msg)

            msg = 'Could not retrieve {0} config id from db'.format(kind)
            self.assertTrue(configid in self.authm.configIds(), msg)

            msg = 'Could not retrieve provider type for {0} config'.format(kind)
            self.assertTrue(QgsAuthType.typeToString(
                self.authm.configProviderType(configid)) == kind, msg)

            config2 = self.config_obj(kind, base=True)
            msg = 'Could not load {0} config'.format(kind)
            self.assertTrue(
                self.authm.loadAuthenticationConfig(configid, config2, True),
                msg)

            msg = 'Could not validate loaded {0} config values'.format(kind)
            self.assertTrue(self.config_values_valid(kind, config2), msg)

            # values haven't been changed, but the db update still takes place
            msg = 'Could not update {0} config values'.format(kind)
            self.assertTrue(self.authm.updateAuthenticationConfig(config2), msg)

            config3 = self.config_obj(kind, base=True)
            msg = 'Could not load updated {0} config'.format(kind)
            self.assertTrue(
                self.authm.loadAuthenticationConfig(configid, config3, True),
                msg)

            msg = 'Could not validate updated {0} config values'.format(kind)
            self.assertTrue(self.config_values_valid(kind, config3), msg)

            msg = 'Could not remove {0} config (by id) from db'.format(kind)
            self.assertTrue(
                self.authm.removeAuthenticationConfig(configid), msg)

            msg = 'Did not remove {0} config id from db'.format(kind)
            self.assertFalse(configid in self.authm.configIds(), msg)

    def test_04_auth_db(self):
        msg = 'Could not erase auth db'
        self.assertTrue(self.authm.eraseAuthenticationDatabase(), msg)

        msg = 'Master password not erased from auth db'
        self.assertTrue(not self.authm.masterPasswordIsSet()
                        and not self.authm.masterPasswordHashInDb(), msg)

        self.set_master_password()

        kinds = ['Basic']
        for kind in kinds:
            config = self.config_obj(kind, base=False)
            msg = 'Could not store {0} config'.format(kind)
            self.assertTrue(self.authm.storeAuthenticationConfig(config), msg)

        msg = 'Could not store a sample of all configs in auth db'
        self.assertTrue((len(self.authm.configIds()) == len(kinds)), msg)


if __name__ == '__main__':
    unittest.main()
