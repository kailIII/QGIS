#ifndef QGSAUTHENTICATIONCONFIGEDITOR_H
#define QGSAUTHENTICATIONCONFIGEDITOR_H

#include <QSqlTableModel>
#include <QWidget>

#include "ui_qgsauthenticationconfigeditor.h"
#include "qgsauthenticationmanager.h"

class QgsMessageBar;

class GUI_EXPORT QgsAuthConfigEditor : public QWidget, private Ui::QgsAuthConfigEditor
{
    Q_OBJECT

  public:
    explicit QgsAuthConfigEditor( QWidget *parent = 0 );
    ~QgsAuthConfigEditor();

    void toggleTitleVisibility( bool visible );

  private slots:
    //! Sets the cached master password (and verifies it if its hash is in authentication database)
    void setMasterPassword();

    //! Clear the currently cached master password (not its hash in database)
    void clearCachedMasterPassword();

    //! Reset the cached master password, updating its hash in authentication database and reseting all existing configs to use it
    void resetMasterPassword();

    //! Clear all cached authentication configs for session
    void clearCachedAuthenticationConfigs();

    //! Remove all authentication configs
    void removeAuthenticationConfigs();

    //! Completely clear out the authentication database (configs and master password)
    void eraseAuthenticationDatabase();

    void authMessageOut( const QString& message, const QString& authtag, QgsAuthManager::MessageLevel level );

    void selectionChanged( const QItemSelection& selected, const QItemSelection& deselected );

    void checkSelection();

    void on_btnAddConfig_clicked();

    void on_btnEditConfig_clicked();

    void on_btnRemoveConfig_clicked();

  private:
    QgsMessageBar * messageBar();
    int messageTimeout();
    QString selectedConfigId();

    QSqlTableModel *mConfigModel;

    QMenu *mAuthUtilitiesMenu;
    QAction *mActionSetMasterPassword;
    QAction *mActionClearCachedMasterPassword;
    QAction *mActionResetMasterPassword;
    QAction *mActionClearCachedAuthConfigs;
    QAction *mActionRemoveAuthConfigs;
    QAction *mActionEraseAuthDatabase;
};

#endif // QGSAUTHENTICATIONCONFIGEDITOR_H
