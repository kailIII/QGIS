class QgsAuthConfigSelect : QWidget
{
%TypeHeaderCode
#include <qgsauthenticationconfigselect.h>
%End

  public:
    explicit QgsAuthConfigSelect( QWidget *parent = 0 );
    ~QgsAuthConfigSelect();

    void setConfigId( const QString& authid );
    const QString configId() const;
};
