
# Generates VAPID keys and stores them in DB settings
from pywebpush import __version__  # ensure installed
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from server.db import SessionLocal
from server.models import Setting

def b64url(b: bytes) -> str:
    import base64
    return base64.urlsafe_b64encode(b).decode('utf-8').rstrip('=')

def main():
    private_key = ec.generate_private_key(ec.SECP256R1())
    priv_bytes = private_key.private_numbers().private_value.to_bytes(32, 'big')
    pub = private_key.public_key().public_numbers()
    x = pub.x.to_bytes(32, 'big')
    y = pub.y.to_bytes(32, 'big')
    # Public key is uncompressed 65-byte: 0x04 || X || Y, but webpush expects base64url-encoded P-256 public key in uncompressed form
    pub_key = b'\x04' + x + y
    public_b64 = b64url(pub_key)
    private_b64 = b64url(priv_bytes)
    with SessionLocal() as db:
        for k,v in (("vapid_public", public_b64), ("vapid_private", private_b64)):
            row = db.query(Setting).filter(Setting.key==k).first()
            if row: row.value = v
            else: db.add(Setting(key=k, value=v))
        db.commit()
    print("Saved VAPID keys to DB settings. Public:", public_b64)

if __name__ == "__main__":
    main()
