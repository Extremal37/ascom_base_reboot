"""HTTP client for Ostec/Ascom IP-DECT web interface."""

import ssl
from urllib.parse import urljoin, urlparse

import requests
from requests.adapters import HTTPAdapter
from requests.auth import HTTPDigestAuth

DEFAULT_VERIFY_PATH = "/GW-DECT/MASTER/mod_cmd.xml?xsl=dectmaster.xsl"
ADMIN_REDIRECT_PATH = "/GW-DECT/mod_cmd.xml?redirect=/admin.xml?xsl=admin.xsl"
REBOOT_PATH = "/CMD0/mod_cmd.xml?cmd=reset&xsl=reset.xsl&reset=OK"


class LegacyTLSAdapter(HTTPAdapter):
    """Allow TLS 1.0–1.2 and legacy ciphers used by IP-DECT bases."""

    def init_poolmanager(self, *args, **kwargs):
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        except AttributeError:
            # Python 3.6 / OpenSSL without PROTOCOL_TLS_CLIENT
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS)

        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        if hasattr(ssl, "TLSVersion"):
            ctx.minimum_version = ssl.TLSVersion.TLSv1
            ctx.maximum_version = ssl.TLSVersion.TLSv1_2
        else:
            ctx.options |= getattr(ssl, "OP_NO_SSLv2", 0)
            ctx.options |= getattr(ssl, "OP_NO_SSLv3", 0)

        try:
            ctx.set_ciphers("DEFAULT:@SECLEVEL=0")
        except ssl.SSLError:
            ctx.set_ciphers("DEFAULT")

        kwargs["ssl_context"] = ctx
        return super(LegacyTLSAdapter, self).init_poolmanager(*args, **kwargs)


class DectClient(object):
    def __init__(self, base_url, username, password, timeout=30.0):
        if "://" in base_url:
            parsed = urlparse(base_url)
        else:
            parsed = urlparse("https://{0}".format(base_url))
        if not parsed.scheme:
            parsed = parsed._replace(scheme="https")
        self.base_url = parsed.geturl().rstrip("/")
        self.username = username
        self.password = password
        self.timeout = timeout

        self.session = requests.Session()
        self.session.verify = False
        self.session.auth = HTTPDigestAuth(username, password)
        self.session.mount("https://", LegacyTLSAdapter())

    def _url(self, path):
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return urljoin(self.base_url + "/", path.lstrip("/"))

    def _get(self, path):
        return self.session.get(self._url(path), timeout=self.timeout)

    @staticmethod
    def _unauthorized(response):
        if response.status_code == 401:
            return True
        text = response.text.lower()
        return "401 unauthorized" in text or "not authorized" in text

    @staticmethod
    def _request_failed(response):
        if DectClient._unauthorized(response):
            return True
        return response.status_code >= 400

    def login(self):
        """Verify credentials against a protected GW-DECT endpoint."""
        response = self._get(DEFAULT_VERIFY_PATH)
        if self._unauthorized(response):
            raise RuntimeError(
                "login failed: invalid credentials (status {0})".format(
                    response.status_code
                )
            )
        if response.status_code >= 400:
            raise RuntimeError(
                "login failed: unexpected status {0}".format(response.status_code)
            )
        if not response.content:
            raise RuntimeError("login failed: empty response")

    def login_via_admin_redirect(self):
        """Same flow as the web UI: redirect to admin.xml after login."""
        return self._get(ADMIN_REDIRECT_PATH)

    def get_master_config(self):
        response = self._get(DEFAULT_VERIFY_PATH)
        if self._request_failed(response):
            raise RuntimeError(
                "not authorized (status {0})".format(response.status_code)
            )
        return response.content

    def reboot(self):
        """Reboot the base station via CMD0/mod_cmd.xml reset command."""
        self.login()
        response = self._get(REBOOT_PATH)
        if self._request_failed(response):
            raise RuntimeError(
                "reboot failed: unexpected status {0}".format(response.status_code)
            )
        if 'reset="true"' not in response.text and "reset='true'" not in response.text:
            snippet = response.text[:300].replace("\n", " ")
            raise RuntimeError("reboot failed: unexpected response: {0}".format(snippet))
