/***************************************************************************
    qgsauthenticationconfigselect.h
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

#ifndef QGSAUTHENTICATIONCONFIGSELECT_H
#define QGSAUTHENTICATIONCONFIGSELECT_H

#include <QWidget>

#include "ui_qgsauthenticationconfigselect.h"
#include "qgsauthenticationconfig.h"

class GUI_EXPORT QgsAuthConfigSelect : public QWidget, private Ui::QgsAuthConfigSelect
{
    Q_OBJECT

  public:
    explicit QgsAuthConfigSelect( QWidget *parent = 0, bool keypasssupported = true );
    ~QgsAuthConfigSelect();

    void setKeyPassSupported( bool supported );
    bool keyPassSupported() const { return mKeyPassSupported; }

    void setConfigId( const QString& authid );
    const QString configId() const { return mConfigId; }

  private slots:
    void loadConfig();
    void clearConfig();
    void validateConfig();
    void populateConfigSelector();

    void on_cmbConfigSelect_currentIndexChanged( int index );

    void on_btnConfigAdd_clicked();

    void on_btnConfigEdit_clicked();

    void on_btnConfigRemove_clicked();

  private:
    void loadAvailableConfigs();

    bool mKeyPassSupported;
    QString mConfigId;
    QHash<QString, QgsAuthConfigBase> mConfigs;
};

#endif // QGSAUTHENTICATIONCONFIGSELECT_H
