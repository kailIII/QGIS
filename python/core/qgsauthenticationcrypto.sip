class QgsAuthCrypto
{
%TypeHeaderCode
#include <qgsauthenticationcrypto.h>
%End

  public:
    static const QString encrypt( QString pass, QString text, QString cipher );

    static const QString decrypt( QString pass, QString text, QString cipher );

    static void passwordHash( const QString &pass , QString *salt, QString *hash );

    static bool verifyPasswordHash( const QString& pass,
                                    const QString& salt,
                                    const QString& hash,
                                    QString *hashderived = 0 );
};
