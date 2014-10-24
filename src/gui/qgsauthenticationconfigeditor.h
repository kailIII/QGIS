#ifndef QGSAUTHENTICATIONCONFIGEDITOR_H
#define QGSAUTHENTICATIONCONFIGEDITOR_H

#include <QSqlTableModel>
#include <QWidget>

#include "ui_qgsauthenticationconfigeditor.h"
#include "qgsauthenticationmanager.h"

class GUI_EXPORT QgsAuthConfigEditor : public QWidget, private Ui::QgsAuthConfigEditor
{
    Q_OBJECT

  public:
    explicit QgsAuthConfigEditor( QWidget *parent = 0 );
    ~QgsAuthConfigEditor();

    void toggleTitleVisibility( bool visible );

  private slots:
    void authMessageOut( const QString& message, const QString& authtag, QgsAuthManager::MessageLevel level );

    void selectionChanged( const QItemSelection& selected, const QItemSelection& deselected );

    void checkSelection();

    void on_btnAddConfig_clicked();

    void on_btnEditConfig_clicked();

    void on_btnRemoveConfig_clicked();

  private:
    QString selectedConfigId();

    QSqlTableModel *mConfigModel;
};

#endif // QGSAUTHENTICATIONCONFIGEDITOR_H
