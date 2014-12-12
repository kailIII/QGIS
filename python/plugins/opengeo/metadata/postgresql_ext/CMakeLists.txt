FILE(GLOB INSTALLER_FILES *.sql)

PLUGIN_INSTALL(opengeo metadata/postgresql_ext ${INSTALLER_FILES})
