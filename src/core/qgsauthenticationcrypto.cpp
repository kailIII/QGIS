// This 'encryption' function was culled from the Qrypto project
// Copyright (C) 2008-2010 Amine Roukh <amineroukh@gmail.com>
//
// This program is free software; you can redistribute it and/or
// modify it under the terms of the GNU General Public License
// as published by the Free Software Foundation; either version 3
// of the License, or (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program; If not, write to the Free Software
// Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


#include "qgsauthenticationcrypto.h"

#include <string.h>

// for Mac, define CRYPTOPP_DISABLE_ASM for build, if
// libcryptopp.dylib was built that way as well, e.g. Homebrew's

#include "cryptopp/aes.h"
#include "cryptopp/osrng.h"
#include "cryptopp/pwdbased.h"

#include "cryptopp/modes.h" // xxx_Mode< >
#include "cryptopp/filters.h" // StringSource and StreamTransformation
#include "cryptopp/hex.h"
#include "cryptopp/sha.h"

#include <QObject>

using namespace CryptoPP;
using namespace std;

const QString QgsAuthCrypto::encrypt( QString pass, QString text, QString cipher )
{
  return encryption( pass, text, cipher, true );
}

const QString QgsAuthCrypto::decrypt( QString pass, QString text, QString cipher )
{
  return encryption( pass, text, cipher, false ) ;
}

void QgsAuthCrypto::passwordHash( const QString &pass, QString *salt, QString *hash )
{
  string password = pass.toStdString();
  unsigned int iterations = 10000;

  AutoSeededRandomPool rng;

  SecByteBlock pwsalt( SHA256::DIGESTSIZE );
  rng.GenerateBlock( pwsalt, pwsalt.size() );

  SecByteBlock derivedkey( SHA256::DIGESTSIZE );

  PKCS5_PBKDF2_HMAC<SHA256> pbkdf;

  pbkdf.DeriveKey(
    derivedkey, derivedkey.size(),
    0x00,
    ( byte * ) password.data(), password.size(),
    pwsalt, pwsalt.size(),
    iterations
  );
  string salthex;
  StringSource ps(
    pwsalt, pwsalt.size(), true,
    new HexEncoder( new StringSink( salthex ) )
  );
  string derivedhex;
  StringSource dh(
    derivedkey, derivedkey.size(), true,
    new HexEncoder( new StringSink( derivedhex ) )
  );

  // LEAVE THIS DEBUG OUTPUT COMMENTED OUT, except during testing of source edits
  //qDebug( "salt hex: %s", salthex.c_str() );
  *salt = encrypt( pass, QString::fromStdString( salthex ), "AES" );
  //qDebug( "salt hex encrypted (out): %s", salt->toStdString().c_str() );
  *hash = QString::fromStdString( derivedhex );
}

bool QgsAuthCrypto::verifyPasswordHash( const QString &pass,
                                        const QString &salt,
                                        const QString& hash,
                                        QString *hashderived )
{
  string password = pass.toStdString();
  // debug output to see if res was "Unknown Error"
  //qDebug( "salt hex encrypted (in): %s", salt.toStdString().c_str() );
  string salthex = decrypt( pass, salt, "AES" ).toStdString();
  // LEAVE THIS DEBUG OUTPUT COMMENTED OUT, except during testing of source edits
  //qDebug( "salt hex decrypted: %s", salthex.c_str() );
  string hashhex = hash.toStdString();
  unsigned int iterations = 10000;

  SecByteBlock pwsalt( SHA256::DIGESTSIZE );

  HexDecoder decoder;
  decoder.Put(( byte * ) salthex.data(), salthex.size() );
  decoder.MessageEnd();
  decoder.Get( pwsalt.BytePtr(), pwsalt.size() );

  SecByteBlock derivedkey( SHA256::DIGESTSIZE );

  PKCS5_PBKDF2_HMAC<SHA256> pbkdf;

  pbkdf.DeriveKey(
    derivedkey, derivedkey.size(),
    0x00,
    ( byte * ) password.data(), password.size(),
    pwsalt, pwsalt.size(),
    iterations
  );

  string derivedhex;
  StringSource dh(
    derivedkey, derivedkey.size(), true,
    new HexEncoder( new StringSink( derivedhex ) )
  );

  if ( hashderived )
  {
    *hashderived = QString::fromStdString( derivedhex );
  }

  return derivedhex == hashhex;
}

QString QgsAuthCrypto::encryption( QString passstr, QString textstr, QString ciphername, bool encrypt )
{
  string pass = passstr.toStdString();
  string text = textstr.toStdString();
  string cipher = ciphername.toStdString();
  string ciphertext;
  string recoveredtext;

  if ( cipher == "AES" )
  {
    byte key[ AES::DEFAULT_KEYLENGTH ], iv[ AES::BLOCKSIZE ];
    StringSource ks(
      reinterpret_cast<const char*>( pass.c_str() ), true,
      new HashFilter( *( new SHA256 ), new ArraySink( key, AES::DEFAULT_KEYLENGTH ) )
    );
    memset( iv, 0x00, AES::BLOCKSIZE );

    if ( encrypt )
    {
      CBC_Mode<AES>::Encryption encryptor( key, sizeof( key ), iv );
      StringSource es(
        text, true,
        new StreamTransformationFilter( encryptor, new HexEncoder( new StringSink( ciphertext ) ) )
      );
    }
    else
    {
      try
      {
        CBC_Mode<AES>::Decryption decryptor( key, sizeof( key ), iv );
        StringSource ds(
          text, true,
          new HexDecoder( new StreamTransformationFilter( decryptor, new StringSink( recoveredtext ) ) )
        );
      }
      catch ( Exception& e )
      {
        return QString( e.what() );
      }
      catch ( ... )
      {
        return QString( "Unknown Error" );
      }
    }
  }


  if ( encrypt )
    return QString::fromStdString( ciphertext );

  return QString::fromStdString( recoveredtext );
}
