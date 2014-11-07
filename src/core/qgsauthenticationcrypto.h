/***************************************************************************
    qgsauthenticationcrypto.h
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

#ifndef QGSAUTHENTICATIONCRYPTO_H
#define QGSAUTHENTICATIONCRYPTO_H

#include <QString>

class CORE_EXPORT QgsAuthCrypto
{

  public:
    static const QString encrypt( QString pass, QString cipheriv, QString text );

    static const QString decrypt( QString pass, QString cipheriv, QString text );

    static void passwordKeyHash( const QString &pass,
                                 QString *salt,
                                 QString *hash,
                                 QString *cipheriv = 0 );

    static bool verifyPasswordKeyHash( const QString& pass,
                                       const QString& salt,
                                       const QString& hash,
                                       QString *hashderived = 0 );

  private:
    static QString encryptdecrypt( QString passstr,
                                   QString cipheriv,
                                   QString textstr,
                                   bool encrypt );
};

#endif  // QGSAUTHENTICATIONCRYPTO_H
