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


class QgsPkiPathsBundle
{
%TypeHeaderCode
#include <qgsauthenticationprovider.h>
%End

  public:
    QgsPkiPathsBundle( const QgsAuthConfigPkiPaths& config,
                       const QSslCertificate& cert,
                       const QSslKey& certkey,
                       const QSslCertificate& issuer = QSslCertificate() );
    ~QgsPkiPathsBundle();

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

    ~QgsAuthProviderPkiPaths();

    // QgsAuthProvider interface
    void updateNetworkRequest( QNetworkRequest &request /In,Out/, const QString &authid );

    void updateNetworkReply( QNetworkReply *reply, const QString &authid );
    void clearCachedConfig( const QString& authid );

};
