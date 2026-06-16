# Distributed under the Apache License, Version 2.0.
# See accompanying NOTICE file for details.

import base64
import hashlib
import json
import logging
import requests
import urllib.parse

from iracingdataapi.client import irDataClient
from pathlib import Path

from core.garage61 import Garage61Client
from core.objects import Main
from core.credentials import data_credentials, google_credentials


_logger = logging.getLogger('log')


def _request_password_limited_token(username: str, password: str, client_id: str, client_secret: str):

    def _encode(string: str) -> str:
        """
        URL (percent) encode the provided string
        """
        return urllib.parse.quote(string, safe='/', encoding=None, errors=None)

    def _mask_secret(secret: str, identifier: str) -> str:
        """
        Mask a secret (client_secret or password) using iRacing's masking algorithm.

        Args:
            secret: The secret to mask
            identifier: client_id for client_secret, username for password

        Returns:
            Base64 encoded SHA-256 hash of secret + normalized_identifier
        """
        # Normalize the identifier (trim and lowercase)
        normalized_id = identifier.strip().lower()

        # Concatenate secret with normalized identifier
        combined = f"{secret}{normalized_id}"

        hasher = hashlib.sha256()
        hasher.update(combined.encode('utf-8'))

        return base64.b64encode(hasher.digest()).decode('utf-8')

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = (f"grant_type=password_limited&"
               f"client_id={client_id}&"
               f"client_secret={_encode(_mask_secret(client_secret, client_id))}&"
               f"username={_encode(username)}&"
               f"password={_encode(_mask_secret(password, username))}&"
               f"scope=iracing.auth")

    r = requests.post(url="https://oauth.iracing.com/oauth2/token",
                      data=payload,
                      headers=headers,
                      timeout=5.0)

    content_type = r.headers.get("Content-Type")

    if "application/json" in content_type:
        return r.json()["access_token"]
    else:
        raise SystemError("Unsupported Content-Type")


class ClientMain(Main):
    __slots__ = ["_idc", "_g61", "_credentials", "_google_credentials"]

    def __init__(self, log_filename: str):
        self._idc = None
        self._g61 = None
        self._credentials = None
        self._google_credentials = None
        super().__init__(log_filename)

    def add_args(self, parser):
        super().add_args(parser)
        parser.add_argument(
            "-cr", "--credentials",
            default=Path("./credentials.json"),
            type=Path,
            help="Credentials file for connecting to iRacing and Garage61."
        )
        parser.add_argument(
            "-gcr", "--google_credentials",
            default=Path("./google.svc.credentials.json"),
            type=Path,
            help="Credentials file for connecting to google sheets."
        )

    def process_args(self, args):
        super().process_args(args)
        if args.credentials.exists():
            with open(args.credentials, 'r') as file:
                self._credentials = json.load(file)
        else:
            self._credentials = data_credentials()
        if self._credentials is None or len(self._credentials) == 0:
            raise IOError(f"Unable to find data credentials")

        if args.google_credentials.exists():
            with open(args.google_credentials, 'r') as file:
                self._google_credentials = json.load(file)
        else:
            self._google_credentials = google_credentials()
        if self._google_credentials is None or len(self._google_credentials) == 0:
            _logger.warning(f"!!!No google credentials found, will not be able to push to a google sheet!!!")

    @property
    def idc(self):
        if not self._idc:
            access_token = _request_password_limited_token(username=self._credentials["username"],
                                                           password=self._credentials["password"],
                                                           client_id=self._credentials["client_id"],
                                                           client_secret=self._credentials["client_secret"])
            self._idc = irDataClient(access_token=access_token)
        return self._idc

    @property
    def g61(self):
        if not self._g61:
            self._g61 = Garage61Client(token=self._credentials["garage61_token"])
        return self._g61

    @property
    def google_credentials(self) -> dict: return self._google_credentials
