/***************************************************************************
    qgsauthenticationmanager.h
    ---------------------
    begin                : October 5, 2014
    copyright            : (C) 2014 by Boundless Spatial, Inc. USA
    author               : Larry Shaffer
    email                : lshaffer at boundlessgeo dot com
 ***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

#ifndef QGSAUTHENTICATIONMANAGER_H
#define QGSAUTHENTICATIONMANAGER_H

#include <QObject>
#include <QNetworkReply>
#include <QNetworkRequest>
#include <QSqlDatabase>
#include <QSqlError>
#include <QSqlQuery>
#include <QStringList>

#include "qgsauthenticationconfig.h"

namespace QCA
{
  class Initializer;
}
class QgsAuthProvider;

class CORE_EXPORT QgsAuthManager : public QObject
{
    Q_OBJECT
    Q_ENUMS( MessageLevel )

  public:

    enum MessageLevel
    {
      INFO = 0,
      WARNING = 1,
      CRITICAL = 2
    };

    static QgsAuthManager *instance();

    QSqlDatabase authDbConnection() const;

    const QString authDbConfigTable() const { return smAuthConfigTable; }

    bool init( const QString& authdatabasedir = QString() );

    const QString authenticationDbPath() const { return mAuthDbPath; }

    bool setMasterPassword( bool verify = false );

    bool setMasterPassword( const QString& pass, bool verify = false );

    bool verifyMasterPassword();

    bool masterPasswordIsSet() const;

    bool masterPasswordHashInDb() const;

    void clearMasterPassword() { mMasterPass = QString(); }

    bool masterPasswordSame( const QString& pass ) const;

    bool resetMasterPassword( const QString& newpass, const QString& oldpass, bool keepbackup, QString *backuppath = 0 );

    const QString authManTag() const { return smAuthManTag; }


    void registerProviders();

    void updateConfigProviderTypes();

    QgsAuthProvider* configProvider( const QString& authid );

    QgsAuthType::ProviderType configProviderType( const QString& authid );

    const QString uniqueConfigId() const;

    bool configIdUnique( const QString &id ) const;

    QStringList configIds() const;

    QHash<QString, QgsAuthConfigBase> availableConfigs();


    bool storeAuthenticationConfig( QgsAuthConfigBase &config );

    bool updateAuthenticationConfig( const QgsAuthConfigBase& config );

    bool loadAuthenticationConfig( const QString& authid, QgsAuthConfigBase &config, bool full = false );

    bool removeAuthenticationConfig( const QString& authid );

    bool removeAllAuthenticationConfigs();

    bool eraseAuthenticationDatabase();


    bool updateNetworkRequest( QNetworkRequest &request, const QString& authid );

    bool updateNetworkReply( QNetworkReply *reply, const QString& authid );

  signals:
    void messageOut( const QString& message, const QString& tag = smAuthManTag, QgsAuthManager::MessageLevel level = INFO ) const;

    void masterPasswordVerified( bool verified ) const;

  public slots:
    void clearAllCachedConfigs();

    void clearCachedConfig( const QString& authid );

  private slots:
    void writeToConsole( const QString& message, const QString& tag = QString(), QgsAuthManager::MessageLevel level = INFO );

  protected:
    explicit QgsAuthManager( QObject *parent = 0 );
    ~QgsAuthManager();

  private:

    bool masterPasswordInput();

    bool masterPasswordRowsInDb( int *rows ) const;

    bool masterPasswordCheckAgainstDb() const;

    bool masterPasswordStoreInDb() const;

    bool masterPasswordClearDb();

    const QString masterPasswordCiv() const;

    bool verifyPasswordCanDecryptConfigs() const;

    bool reencryptAllAuthenticationConfigs( const QString& prevpass, const QString& prevciv );

    bool reencryptAuthenticationConfig( const QString& authid, const QString& prevpass, const QString& prevciv );

    bool authDbOpen() const;

    bool authDbQuery( QSqlQuery *query ) const;

    bool authDbStartTransaction() const;

    bool authDbCommit() const;

    bool authDbTransactionQuery( QSqlQuery *query ) const;

    const QString authDbPassTable() const { return smAuthPassTable; }

    static QgsAuthManager* smInstance;
    static const QString smAuthConfigTable;
    static const QString smAuthPassTable;
    static const QString smAuthManTag;

    QString mAuthDbPath;

    QCA::Initializer * mQcaInitializer;

    QHash<QString, QgsAuthType::ProviderType> mConfigProviders;
    QHash<QgsAuthType::ProviderType, QgsAuthProvider*> mProviders;
    bool mProvidersRegistered;

    QString mMasterPass;
};

#endif // QGSAUTHENTICATIONMANAGER_H
