class QgsAuthProvider
{
%TypeHeaderCode
#include <qgsauthenticationprovider.h>
%End

  public:

    explicit QgsAuthProvider( QgsAuthType::ProviderType providertype = QgsAuthType::None );

    virtual ~QgsAuthProvider();

    QgsAuthType::ProviderType providerType() const;

    static bool urlToResource( const QString& accessurl, QString *resource, bool withpath = false );

    virtual void updateNetworkRequest( QNetworkRequest &request /In,Out/, const QString& authid ) = 0;

    virtual void updateNetworkReply( QNetworkReply *reply, const QString& authid ) = 0;

    virtual void clearCachedConfig( const QString& authid ) = 0;

  protected:
    static const QString authProviderTag();
};


class QgsAuthProviderBasic : QgsAuthProvider
{
%TypeHeaderCode
#include <qgsauthenticationprovider.h>
%End

  public:
    QgsAuthProviderBasic();

    ~QgsAuthProviderBasic();

    // QgsAuthProvider interface
    void updateNetworkRequest( QNetworkRequest &request /In,Out/, const QString &authid );
    void updateNetworkReply( QNetworkReply *reply, const QString &authid );
    void clearCachedConfig( const QString& authid );
};


class QgsPkiBundle
{
%TypeHeaderCode
#include <qgsauthenticationprovider.h>
%End

  public:
    QgsPkiBundle( const QgsAuthConfigPkiPaths& config,
                  const QSslCertificate& cert,
                  const QSslKey& certkey,
                  const QSslCertificate& issuer = QSslCertificate() );
    ~QgsPkiBundle();

    bool isValid();

    const QgsAuthConfigPkiPaths config() const;
    void setConfig( const QgsAuthConfigPkiPaths& config );

    const QSslCertificate clientCert() const;
    void setClientCert( const QSslCertificate& cert );

    const QSslKey clientCertKey() const;
    void setClientCertKey( const QSslKey& certkey );

    const QSslCertificate issuerCert() const;
    void setIssuerCert( const QSslCertificate& issuer );

};


class  QgsAuthProviderPkiPaths : QgsAuthProvider
{
%TypeHeaderCode
#include <qgsauthenticationprovider.h>
%End

  public:
    QgsAuthProviderPkiPaths();

    virtual ~QgsAuthProviderPkiPaths();

    // QgsAuthProvider interface
    void updateNetworkRequest( QNetworkRequest &request /In,Out/, const QString &authid );

    void updateNetworkReply( QNetworkReply *reply, const QString &authid );
    void clearCachedConfig( const QString& authid );

    static const QByteArray certAsPem( const QString &certpath );

    static const QByteArray keyAsPem( const QString &keypath,
                                      const QString &keypass = QString(),
                                      QString *algtype = 0 );

    static const QByteArray issuerAsPem( const QString &issuerpath );

};
