#include "qgsauthenticationprovider.h"

#include <QFile>
#ifndef QT_NO_OPENSSL
#include <QSslConfiguration>
#include <QSslError>
#endif

#include "qgsauthenticationconfig.h"
#include "qgsauthenticationmanager.h"
#include "qgslogger.h"

QgsAuthProvider::QgsAuthProvider( QgsAuthType::ProviderType providertype )
    : mType( providertype )
{
}

QgsAuthProvider::~QgsAuthProvider()
{
}

bool QgsAuthProvider::urlToResource( const QString &accessurl, QString *resource, bool withpath )
{
  QString res = QString();
  if ( !accessurl.isEmpty() )
  {
    QUrl url( accessurl );
    if ( url.isValid() )
    {
      res = QString( "%1://%2:%3%4" ).arg( url.scheme() ).arg( url.host() ).arg( url.port() ).arg( withpath ? url.path() : "" );
    }
  }
  *resource = res;
  return ( !res.isEmpty() );
}


//////////////////////////////////////////////////////
// QgsAuthProviderBasic
//////////////////////////////////////////////////////

QMap<QString, QgsAuthConfigBasic> QgsAuthProviderBasic::mAuthBasicCache = QMap<QString, QgsAuthConfigBasic>();

QgsAuthProviderBasic::QgsAuthProviderBasic()
    : QgsAuthProvider( QgsAuthType::Basic )
{
}

QgsAuthProviderBasic::~QgsAuthProviderBasic()
{
  mAuthBasicCache.clear();
}

void QgsAuthProviderBasic::updateNetworkRequest( QNetworkRequest& request, const QString& authid )
{
  QgsAuthConfigBasic config = getAuthBasicConfig( authid );
  if ( !config.isValid() )
  {
    QgsDebugMsg( QString( "Update request config FAILED for authid: %1: basic config invalid" ).arg( authid ) );
    return;
  }

  QString username = config.username();
  QString password = config.password();

  if ( !username.isEmpty() )
  {
    request.setRawHeader( "Authorization", "Basic " + QString( "%1:%2" ).arg( username ).arg( password ).toAscii().toBase64() );
  }
}

void QgsAuthProviderBasic::updateNetworkReply( QNetworkReply *reply, const QString& authid )
{
  Q_UNUSED( reply );
  Q_UNUSED( authid );
}

QgsAuthConfigBasic QgsAuthProviderBasic::getAuthBasicConfig( const QString& authid )
{
  QgsAuthConfigBasic config;

  // check if it is cached
  if ( mAuthBasicCache.contains( authid ) )
  {
    config = mAuthBasicCache.value( authid );
    QgsDebugMsg( QString( "Retrieved basic bundle for authid %1" ).arg( authid ) );
    return config;
  }

  // else build basic bundle
  if ( !QgsAuthManager::instance()->loadAuthenticationConfig( authid, config, true ) )
  {
    QgsDebugMsg( QString( "Basic bundle for authid %1: FAILED to retrieve config" ).arg( authid ) );
    return config;
  }

  // cache bundle
  putAuthBasicConfig( authid, config );

  return config;
}

void QgsAuthProviderBasic::putAuthBasicConfig( const QString& authid, QgsAuthConfigBasic config )
{
  QgsDebugMsg( QString( "Putting basic config for authid %1" ).arg( authid ) );
  mAuthBasicCache.insert( authid, config );
}

void QgsAuthProviderBasic::removeAuthBasicConfig( const QString& authid )
{
  if ( mAuthBasicCache.contains( authid ) )
  {
    mAuthBasicCache.remove( authid );
    QgsDebugMsg( QString( "Removed basic config for authid: %1" ).arg( authid ) );
  }
}

void QgsAuthProviderBasic::clearCachedConfig( const QString& authid )
{
  Q_UNUSED( authid );
}


#ifndef QT_NO_OPENSSL

//////////////////////////////////////////////////////
// QgsPkiBundle
//////////////////////////////////////////////////////

QgsPkiBundle::QgsPkiBundle( const QgsAuthConfigPkiPaths& config,
                            const QSslCertificate& cert,
                            const QSslKey& certkey,
                            const QSslCertificate& issuer )
    : mConfig( config )
    , mCert( cert )
    , mCertKey( certkey )
    , mIssuer( issuer )
{
}

QgsPkiBundle::~QgsPkiBundle()
{
}

bool QgsPkiBundle::isValid()
{
  return ( !mCert.isNull() && !mCertKey.isNull() );
}

//////////////////////////////////////////////////////
// Local Functions
//////////////////////////////////////////////////////

static QByteArray fileData_( const QString& path, bool astext = false )
{
  QByteArray data;
  QFile file( path );
  if ( file.exists() )
  {
    QFile::OpenMode openflags( QIODevice::ReadOnly );
    if ( astext )
      openflags |= QIODevice::Text;
    bool ret = file.open( openflags );
    if ( ret )
    {
      data = file.readAll();
    }
    file.close();
  }
  return data;
}

QSsl::KeyAlgorithm pemKeyAlgorithm_( const QByteArray& keydata )
{
  QString keytxt( keydata );
  return ( keytxt.contains( "BEGIN DSA P" ) ? QSsl::Dsa : QSsl::Rsa );
}

//////////////////////////////////////////////////////
// QgsAuthProviderPkiPaths
//////////////////////////////////////////////////////

QMap<QString, QgsPkiBundle *> QgsAuthProviderPkiPaths::mPkiBundleCache = QMap<QString, QgsPkiBundle *>();

QgsAuthProviderPkiPaths::QgsAuthProviderPkiPaths()
    : QgsAuthProvider( QgsAuthType::PkiPaths )
{

}

QgsAuthProviderPkiPaths::~QgsAuthProviderPkiPaths()
{
  qDeleteAll( mPkiBundleCache.values() );
  mPkiBundleCache.clear();
}

void QgsAuthProviderPkiPaths::updateNetworkRequest( QNetworkRequest &request, const QString &authid )
{
  // TODO: is this too restrictive, to intercept only HTTPS connections?
  if ( request.url().scheme().toLower() != QString( "https" ) )
  {
    QgsDebugMsg( QString( "Update request SSL config SKIPPED for authid %1: not HTTPS" ).arg( authid ) );
    return;
  }
  else
  {
    QgsDebugMsg( QString( "Update request SSL config: HTTPS connection for authid: %1" ).arg( authid ) );
  }

  QgsPkiBundle * pkibundle = getPkiBundle( authid );
  if ( !pkibundle || !pkibundle->isValid() )
  {
    QgsDebugMsg( QString( "Update request SSL config FAILED for authid: %1: PKI bundle invalid" ).arg( authid ) );
    return;
  }
  else
  {
    QgsDebugMsg( QString( "Update request SSL config: PKI bundle valid for authid: %1" ).arg( authid ) );
  }

  QSslConfiguration sslConfig = request.sslConfiguration();
  //QSslConfiguration sslConfig( QSslConfiguration::defaultConfiguration() );

  // TODO: test for supported protocols for OpenSSL version built against
  //sslConfig.setProtocol( QSsl::TlsV1SslV3 );

  QSslCertificate issuercert = pkibundle->issuerCert();
  if ( !issuercert.isNull() )
  {
    QList<QSslCertificate> sslCAs( sslConfig.caCertificates() );
    sslCAs << issuercert;
    sslConfig.setCaCertificates( sslCAs );
  }

  sslConfig.setLocalCertificate( pkibundle->clientCert() );
  sslConfig.setPrivateKey( pkibundle->clientCertKey() );

  request.setSslConfiguration( sslConfig );
}

void QgsAuthProviderPkiPaths::updateNetworkReply( QNetworkReply *reply, const QString &authid )
{
  if ( reply->request().url().scheme().toLower() != QString( "https" ) )
  {
    QgsDebugMsg( QString( "Update reply SSL errors SKIPPED for authid %1: not HTTPS" ).arg( authid ) );
    return;
  }
  else
  {
    QgsDebugMsg( QString( "Update reply SSL errors: HTTPS connection for authid: %1" ).arg( authid ) );
  }

  QgsPkiBundle * pkibundle = getPkiBundle( authid );
  if ( !pkibundle || !pkibundle->isValid() )
  {
    QgsDebugMsg( QString( "Update reply SSL errors FAILED: PKI bundle invalid for authid: %1" ).arg( authid ) );
    return;
  }
  else
  {
    QgsDebugMsg( QString( "Update reply SSL errors: PKI bundle is valid for authid: %1" ).arg( authid ) );
  }
  if ( !pkibundle->config().issuerSelfSigned() )
  {
    // TODO: maybe sniff cert to see if it is self-signed, regardless of what user defines
    QgsDebugMsg( QString( "Update reply SSL errors SKIPPED for authid %1: issuer not self-signed" ).arg( authid ) );
    return;
  }

  QList<QSslError> expectedSslErrors;
  QSslError error = QSslError();
  QString issuer = "";
  QSslCertificate issuercert = pkibundle->issuerCert();

  if ( !issuercert.isNull() )
  {
    issuer = "defined issuer";
    error = QSslError( QSslError::SelfSignedCertificate, issuercert );
  }
  else
  {
    // issuer not defined, but may already be in available CAs
    issuer = "ALL in chain";
    error = QSslError( QSslError::SelfSignedCertificate );
  }
  if ( error.error() != QSslError::NoError )
  {
    QgsDebugMsg( QString( "Adding self-signed cert expected ssl error for %1 for authid: %2" ).arg( issuer ).arg( authid ) );
    expectedSslErrors.append( error );
    reply->ignoreSslErrors( expectedSslErrors );
  }
}

void QgsAuthProviderPkiPaths::clearCachedConfig( const QString& authid )
{
  QgsPkiBundle * pkibundle = 0;
  // check if it is cached
  if ( mPkiBundleCache.contains( authid ) )
  {
    pkibundle = mPkiBundleCache.take( authid );
    delete pkibundle;
    pkibundle = 0;
  }
}

const QByteArray QgsAuthProviderPkiPaths::certAsPem( const QString &certpath )
{
  bool pem = certpath.endsWith( ".pem", Qt::CaseInsensitive );
  if ( pem )
  {
    return fileData_( certpath, pem );
  }
  QSslCertificate clientcert( fileData_( certpath ), QSsl::Der );
  return ( !clientcert.isNull() ? clientcert.toPem() : QByteArray() );
}

const QByteArray QgsAuthProviderPkiPaths::keyAsPem( const QString &keypath,
    const QString &keypass,
    QString *algtype,
    bool reencrypt )
{
  bool pem = keypath.endsWith( ".pem", Qt::CaseInsensitive );
  QByteArray keydata( fileData_( keypath, pem ) );

  QSslKey clientkey;
  clientkey = QSslKey( keydata,
                       QSsl::Rsa,
                       pem ? QSsl::Pem : QSsl::Der,
                       QSsl::PrivateKey,
                       !keypass.isEmpty() ? keypass.toUtf8() : QByteArray() );
  if ( clientkey.isNull() )
  {
    // try DSA algorithm, since Qt can't seem to determine it otherwise
    clientkey = QSslKey( keydata,
                         QSsl::Dsa,
                         pem ? QSsl::Pem : QSsl::Der,
                         QSsl::PrivateKey,
                         !keypass.isEmpty() ? keypass.toUtf8() : QByteArray() );
    if ( clientkey.isNull() )
    {
      return QByteArray();
    }
    if ( algtype )
      *algtype = "dsa";
  }
  else
  {
    if ( algtype )
      *algtype = "rsa";
  }

  // reapply passphrase if protection is requested and passphrase exists
  return ( clientkey.toPem( reencrypt && !keypass.isEmpty() ? keypass.toUtf8() : QByteArray() ) );
}

const QByteArray QgsAuthProviderPkiPaths::issuerAsPem( const QString &issuerpath )
{
  bool pem = issuerpath.endsWith( ".pem", Qt::CaseInsensitive );
  if ( pem )
  {
    return fileData_( issuerpath, pem );
  }
  QSslCertificate issuercert( fileData_( issuerpath ), QSsl::Der );
  return ( !issuercert.isNull() ? issuercert.toPem() : QByteArray() );
}

QgsPkiBundle *QgsAuthProviderPkiPaths::getPkiBundle( const QString& authid )
{
  QgsPkiBundle * bundle = 0;

  // check if it is cached
  if ( mPkiBundleCache.contains( authid ) )
  {
    bundle = mPkiBundleCache.value( authid );
    if ( bundle )
    {
      QgsDebugMsg( QString( "Retrieved PKI bundle for authid %1" ).arg( authid ) );
      return bundle;
    }
  }

  // else build PKI bundle
  QgsAuthConfigPkiPaths config;

  if ( !QgsAuthManager::instance()->loadAuthenticationConfig( authid, config, true ) )
  {
    QgsDebugMsg( QString( "PKI bundle for authid %1: FAILED to retrieve config" ).arg( authid ) );
    return bundle;
  }

  // init client cert
  // Note: if this is not valid, no sense continuing
  QSslCertificate clientcert( QgsAuthProviderPkiPaths::certAsPem( config.certId() ) );
  if ( !clientcert.isValid() )
  {
    QgsDebugMsg( QString( "PKI bundle for authid %1: insert FAILED, client cert is not valid" ).arg( authid ) );
    return bundle;
  }

  // init key
  QString algtype;
  QByteArray keydata( QgsAuthProviderPkiPaths::keyAsPem( config.keyId(), config.keyPassphrase(), &algtype ) );

  if ( keydata.isNull() )
  {
    QgsDebugMsg( QString( "PKI bundle for authid %1: insert FAILED, no key data read" ).arg( authid ) );
    return bundle;
  }

  QSslKey clientkey( keydata,
                     ( algtype == "rsa" ) ? QSsl::Rsa : QSsl::Dsa,
                     QSsl::Pem,
                     QSsl::PrivateKey,
                     !config.keyPassphrase().isEmpty() ? config.keyPassphrase().toUtf8() : QByteArray() );

  if ( clientkey.isNull() )
  {
    QgsDebugMsg( QString( "PKI bundle for authid %1: insert FAILED, PEM cert key could not be created" ).arg( authid ).toAscii().constData() );
    return bundle;
  }

  // init issuer cert
  QSslCertificate issuercert;
  if ( !config.issuerId().isEmpty() )
  {
    QByteArray issuerdata( QgsAuthProviderPkiPaths::issuerAsPem( config.issuerId() ) );
    if ( !issuerdata.isNull() )
    {
      issuercert = QSslCertificate( issuerdata );
      if ( !issuercert.isValid() )
      {
        QgsDebugMsg( QString( "PKI bundle  for authid %1: insert FAILED, issuer cert is not valid" ).arg( authid ) );
        return bundle;
      }
    }
  }

  bundle = new QgsPkiBundle( config, clientcert, clientkey, issuercert );

  // cache bundle
  putPkiBundle( authid, bundle );

  return bundle;
}

void QgsAuthProviderPkiPaths::putPkiBundle( const QString &authid, QgsPkiBundle *pkibundle )
{
  QgsDebugMsg( QString( "Putting PKI bundle for authid %1" ).arg( authid ) );
  mPkiBundleCache.insert( authid, pkibundle );
}

void QgsAuthProviderPkiPaths::removePkiBundle( const QString& authid )
{
  if ( mPkiBundleCache.contains( authid ) )
  {
    QgsPkiBundle * pkibundle = mPkiBundleCache.take( authid );
    delete pkibundle;
    pkibundle = 0;
    QgsDebugMsg( QString( "Removed PKI bundle for authid: %1" ).arg( authid ) );
  }
}

#endif
