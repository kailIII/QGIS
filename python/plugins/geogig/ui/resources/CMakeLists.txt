FILE(GLOB INSTALLER_FILES *.qrc *.gif *.png)

PLUGIN_INSTALL(geogig ui/resources ${INSTALLER_FILES})
