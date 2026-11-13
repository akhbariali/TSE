"""Authentication boundary checks for public pages and both market APIs."""
import http.client
from http.server import ThreadingHTTPServer
from pathlib import Path
import sys
import threading
import time
import unittest
from unittest.mock import patch
from urllib.parse import urlencode

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app
from app_auth import SingleUserAuth, password_record


class LoginTests(unittest.TestCase):
    def setUp(self):
        self.auth=SingleUserAuth(password_record('owner','test-password-123456'))
        self.auth_patch=patch.object(app,'AUTH',self.auth);self.auth_patch.start()
        self.server=ThreadingHTTPServer(('127.0.0.1',0),app.Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join();self.auth_patch.stop()

    def request(self,path,method='GET',body=None,headers=None):
        client=http.client.HTTPConnection(*self.server.server_address)
        client.request(method,path,body,headers or {})
        response=client.getresponse();result=(response.status,dict(response.getheaders()),response.read())
        client.close();return result

    def login(self,password='test-password-123456',headers=None):
        return self.request('/login','POST',urlencode({'username':'owner','password':password}),
                            {'Content-Type':'application/x-www-form-urlencoded',**(headers or {})})

    def test_pages_apis_files_and_mutations_require_login(self):
        self.assertEqual(self.request('/')[0],303)
        for path in ['/api/status','/api/ifb/status','/api/files/unknown','/api/ifb/files/unknown','/api/export/flows','/static/app.js']:
            self.assertIn(self.request(path)[0],(303,401))
        for path in ['/api/sync','/api/ifb/sync']:
            self.assertEqual(self.request(path,'POST',headers={'X-TSE-Request':'sync'})[0],401)
        self.assertEqual(self.request('/login')[0],200)
        self.assertEqual(self.request('/healthz')[0],200)

    def test_login_cookie_logout_and_revocation(self):
        status,headers,_=self.login();self.assertEqual(status,303)
        cookie=headers['Set-Cookie'];self.assertIn('HttpOnly',cookie);self.assertIn('SameSite=Strict',cookie)
        request_headers={'Cookie':cookie.split(';')[0]}
        self.assertEqual(self.request('/',headers=request_headers)[0],200)
        self.assertEqual(self.request('/logout','POST',headers=request_headers)[0],303)
        self.assertEqual(self.request('/',headers=request_headers)[0],303)

    def test_https_cookie_and_cross_origin_rejection(self):
        status,headers,_=self.login(headers={'X-Forwarded-Proto':'https'})
        self.assertEqual(status,303);self.assertIn('; Secure',headers['Set-Cookie'])
        self.assertEqual(self.login(headers={'Origin':'https://other.example'})[0],403)
        self.assertEqual(self.request('/logout','POST',headers={'Sec-Fetch-Site':'cross-site'})[0],403)

    def test_wrong_credentials_rate_limit_and_expiry(self):
        self.assertEqual(self.login('wrong')[0],401)
        self.auth.attempts['127.0.0.1']=[time.time()]*10
        self.assertEqual(self.login()[0],429)
        self.auth.attempts.clear()
        token,_=self.auth.login('owner','test-password-123456','local')
        self.assertTrue(self.auth.authenticated(token))
        with patch('app_auth.time.time',return_value=time.time()+13*3600):
            self.assertFalse(self.auth.authenticated(token))

    def test_unconfigured_auth_fails_closed(self):
        with patch.object(app,'AUTH',None):
            self.assertEqual(self.request('/api/status')[0],503)


if __name__=='__main__':unittest.main()
