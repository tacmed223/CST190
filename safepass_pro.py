import os
import csv
import base64
from typing import List, Dict, Optional
from dataclasses import dataclass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

@dataclass
class CredentialRecord:
    """Domain model representing a decrypted credential structure."""
    platform: str
    username: str
    password: str

class CryptoEngine:
    """Handles advanced cryptographic key derivation and data transformation."""
    def __init__(self, master_password: str):
        self._salt_file = "entropy.salt"
        self._salt = self._load_or_create_salt()
        self._cipher = self._derive_cipher(master_password)

    def _load_or_create_salt(self) -> bytes:
        if os.path.exists(self._salt_file):
            with open(self._salt_file, "rb") as f:
                return f.read()
        else:
            salt = os.urandom(16)
            with open(self._salt_file, "wb") as f:
                f.write(salt)
            return salt

    def _derive_cipher(self, master_password: str) -> Fernet:
        """Derives a secure cryptographic key using PBKDF2HMAC to prevent raw key exposure."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._salt,
            iterations=400_000, # Enterprise-grade compute cost against brute-force
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode('utf-8')))
        return Fernet(key)

    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            return ""
        return self._cipher.encrypt(plaintext.encode('utf-8')).decode('utf-8')

    def decrypt(self, ciphertext: str) -> str:
        if not ciphertext:
            return ""
        try:
            return self._cipher.decrypt(ciphertext.encode('utf-8')).decode('utf-8')
        except Exception:
            raise PermissionError("Decryption failed. Invalid master authorization key.")


class SecureRepository:
    """Data Access Object (DAO) managing secure flat-file persistence layers."""
    def __init__(self, db_filepath: str, crypto_engine: CryptoEngine):
        self._db_file = db_filepath
        self._crypto = crypto_engine
        self._init_db()

    def _init_db(self) -> None:
        if not os.path.exists(self._db_file):
            with open(self._db_file, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Platform", "Username", "Password"])

    def save(self, record: CredentialRecord) -> None:
        """Encrypts domain entities and appends safely to persistent storage."""
        enc_plat = self._crypto.encrypt(record.platform)
        enc_user = self._crypto.encrypt(record.username)
        enc_pass = self._crypto.encrypt(record.password)
        
        with open(self._db_file, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([enc_plat, enc_user, enc_pass])

    def find_all(self) -> List[CredentialRecord]:
        """Reads, decrypts, and maps storage rows back into application domain structures."""
        records: List[CredentialRecord] = []
        if not os.path.exists(self._db_file):
            return records

        with open(self._db_file, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader) # Consume structural headers
            for row in reader:
                if len(row) == 3:
                    records.append(CredentialRecord(
                        platform=self._crypto.decrypt(row[0]),
                        username=self._crypto.decrypt(row[1]),
                        password=self._crypto.decrypt(row[2])
                    ))
        return records


class VaultController:
    """User Interface Coordinator processing application system loops."""
    def __init__(self, repository: SecureRepository):
        self._repo = repository

    def run(self) -> None:
        while True:
            print("\n🔒 SAFEPASS ADVANCED ENTERPRISE ENGINE v2.0")
            print("1. Create and Encrypt New Record")
            print("2. Decrypt and Read Local Vault")
            print("3. Terminate Secure Session")
            choice = input("[*] Action Selection: ").strip()

            try:
                if choice == "1":
                    plat = input("Platform: ").strip()
                    user = input("Username: ").strip()
                    pw = input("Password: ").strip()
                    if not (plat and user and pw):
                        print("[Validation Error] Input fields cannot be empty.")
                        continue
                    self._repo.save(CredentialRecord(plat, user, pw))
                    print("[✓] Entity successfully encrypted and committed.")
                elif choice == "2":
                    records = self._repo.find_all()
                    print(f"\n{'--- DECRYPTED ENTITIES VAULT ---':^60}")
                    for r in records:
                        print(f"Platform: {r.platform:<12} | User: {r.username:<15} | Pass: {r.password}")
                    print("-" * 60)
                elif choice == "3":
                    print("[Shutdown] Session cache cleared. Vault locked safely.")
                    break
            except Exception as ex:
                print(f"[Runtime Exception] Secure sequence aborted: {ex}")


if __name__ == "__main__":
    print("=== INITIALIZATION SUBSYSTEM AUTHORIZATION ===")
    master_key = input("Establish Master Passphrase to Derive Vault Cipher: ")
    if len(master_key) < 8:
        print("[Security Refusal] Master passphrases must contain at least 8 characters.")
    else:
        engine = CryptoEngine(master_key)
        repo = SecureRepository("vault_v2.csv", engine)
        app = VaultController(repo)
        app.run()
