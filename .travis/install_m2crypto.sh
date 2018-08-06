#!/bin/sh -xe

# This is based on a suggestion in a github comment:
# https://github.com/travis-ci/travis-ci/issues/721#issuecomment-17197098

# openssl 1.0 does not have sslv2, which is not disabled in m2crypto
# therefore this workaround is required

PATCH="
--- SWIG/_ssl.i   2015-11-03 15:54:40.942000000 -0500
+++ SWIG/_ssl.i   2015-11-03 15:55:17.810000000 -0500
@@ -48,8 +48,10 @@
 %rename(ssl_get_alert_desc_v) SSL_alert_desc_string_long;
 extern const char *SSL_alert_desc_string_long(int);
 
+#ifndef OPENSSL_NO_SSL2
 %rename(sslv2_method) SSLv2_method;
 extern SSL_METHOD *SSLv2_method(void);
+#endif
 %rename(sslv3_method) SSLv3_method;
 extern SSL_METHOD *SSLv3_method(void);
 %rename(sslv23_method) SSLv23_method;"

sudo ln -s /usr/include/x86_64-linux-gnu/openssl/opensslconf.h /usr/include/openssl/opensslconf.h

pip install --download="." m2crypto==0.21.1
tar -xf M2Crypto-*.tar.gz
rm M2Crypto-*.tar.gz
cd M2Crypto-*
echo "$PATCH" | patch -p0
python setup.py install
cd ..
# We need to clean up so that flake8 doesn't get upset.
rm -rf M2Crypto-*
