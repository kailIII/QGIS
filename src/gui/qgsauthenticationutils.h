#ifndef QGSAUTHENTICATIONUTILS_H
#define QGSAUTHENTICATIONUTILS_H

#include <QDialog>

#include "ui_qgsmasterpasswordresetdialog.h"

class QgsMessageBar;

class GUI_EXPORT QgsMasterPasswordResetDialog : public QDialog, private Ui::QgsMasterPasswordResetDialog
{
    Q_OBJECT

  public:
    explicit QgsMasterPasswordResetDialog( QWidget *parent = 0 );
    ~QgsMasterPasswordResetDialog();

    bool requestMasterPasswordReset( QString *password, bool *keepbackup );

  private slots:
    void on_leMasterPassCurrent_textChanged( const QString& pass );
    void on_leMasterPassNew_textChanged( const QString& pass );

    void on_chkPassShowCurrent_stateChanged( int state );
    void on_chkPassShowNew_stateChanged( int state );

  private:
    void validatePasswords();

    bool mPassCurOk;
    bool mPassNewOk;
};

///////////////////////////////////////////////

class GUI_EXPORT QgsAuthenticationUtils
{
  public:

    //! Sets the cached master password (and verifies it if its hash is in authentication database)
    static void setMasterPassword( QgsMessageBar *msgbar, int timeout = 0 );

    //! Clear the currently cached master password (not its hash in database)
    static void clearCachedMasterPassword( QgsMessageBar *msgbar, int timeout = 0 );

    //! Reset the cached master password, updating its hash in authentication database and reseting all existing configs to use it
    static void resetMasterPassword( QgsMessageBar *msgbar, int timeout = 0, QWidget *parent = 0 );

    //! Clear out all authentication configs
    static void clearAuthenticationConfigs(QgsMessageBar *msgbar, int timeout = 0, QWidget *parent = 0 );

    //! Completely clear out the authentication database (configs and master password)
    static void clearAuthenticationDatabase( QgsMessageBar *msgbar, int timeout = 0, QWidget *parent = 0  );

};

#endif // QGSAUTHENTICATIONUTILS_H
