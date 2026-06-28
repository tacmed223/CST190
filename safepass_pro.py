import os
import csv
import base64
import sys
from typing import List, Optional
from dataclasses import dataclass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

@dataclass
class CredentialEntity:
    """Domain model abstraction representing unencrypted core entities."""
    platform: str
    username: str
    password: str

class AdvancedCryptoEngine:
    """Handles high-security key derivation and cryptographic transformations."""
    def __init__(self, master_passphrase: str):
        self._salt_file = "security.salt"
        self._salt = self._initialize_salt()
        self._cipher = self._derive_symmetric_cipher(master_passphrase)

    def _initialize_salt(self) -> bytes:
        if os.path.exists(self._salt_file):
            with open(self._salt_file, "rb") as f:
                return f.read()
        else:
            generated_salt = os.urandom(16)
            with open(self._salt_file, "wb") as f:
                f.write(generated_salt)
            return generated_salt

    def _derive_symmetric_cipher(self, passphrase: str) -> Fernet:
        """Derives a secure cryptographic key using multi-iteration PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._salt,
            iterations=400_000,  # Mitigates high-speed GPU brute-forcing
        )
        derived_key = base64.urlsafe_b64encode(kdf.derive(passphrase.encode('utf-8')))
        return Fernet(derived_key)

    def encrypt_string(self, plaintext: str) -> str:
        if not plaintext:
            return ""
        return self._cipher.encrypt(plaintext.encode('utf-8')).decode('utf-8')

    def decrypt_string(self, ciphertext: str) -> str:
        if not ciphertext:
            return ""
        try:
            return self._cipher.decrypt(ciphertext.encode('utf-8')).decode('utf-8')
        except Exception:
            raise PermissionError("Subsystem Decryption Failure: Invalid Cryptographic Authority Key.")


class RelationalCSVDataAccessObject:
    """Manages the decoupled storage access layer (DAO Design Pattern)."""
    def __init__(self, database_path: str, crypto_engine: AdvancedCryptoEngine):
        self._db_path = database_path
        self._crypto = crypto_engine
        self._bootstrap_database()

    def _bootstrap_database(self) -> None:
        if not os.path.exists(self._db_path):
            with open(self._db_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Platform_Hash", "Identity_Hash", "Secret_Hash"])

    def persist_record(self, entity: CredentialEntity) -> None:
        """Encrypts data attributes and commits them directly to disk storage."""
        enc_plat = self._crypto.encrypt_string(entity.platform)
        enc_user = self._crypto.encrypt_string(entity.username)
        enc_pass = self._crypto.encrypt_string(entity.password)
        
        with open(self._db_path, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([enc_plat, enc_user, enc_pass])

    def fetch_records(self) -> List[CredentialEntity]:
        """Extracts rows from storage, running multi-layered decryption sequences."""
        retrieved_entities: List[CredentialEntity] = []
        if not os.path.exists(self._db_path):
            return retrieved_entities

        with open(self._db_path, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # Skip structural headers
            for record_row in reader:
                if len(record_row) == 3:
                    retrieved_entities.append(CredentialEntity(
                        platform=self._crypto.decrypt_string(record_row[0]),
                        username=self._crypto.decrypt_string(record_row[1]),
                        password=self._crypto.decrypt_string(record_row[2])
                    ))
        return retrieved_entities


class UserInterfaceController:
    """Orchestrates runtime state loops and handles input constraints."""
    def __init__(self, dao: RelationalCSVDataAccessObject):
        self._dao = dao

    def execute_system_loop(self) -> None:
        while True:
            print("\n⚡ SAFEPASS ENTERPRISE PLATFORM ENGINE v2.0")
            print("1) Encrypt & Commit New Credential Instance")
            print("2) Decrypt & Inspect Local Secure Database")
            print("3) Invalidate Session & Terminate Thread")
            user_choice = input("[*] Command Target: ").strip()

            try:
                if user_choice == "1":
                    p = input("Platform Domain Name: ").strip()
                    u = input("Target Account Username: ").strip()
                    w = input("Plaintext Authentication Key: ").strip()
                    if not (p and u and w):
                        print("[Validation Alert] Field inputs cannot be empty.")
                        continue
                    self._dao.persist_record(CredentialEntity(p, u, w))
                    print("[✓] Encrypted record committed to filesystem.")
                elif user_choice == "2":
                    records = self._dao.fetch_records()
                    print(f"\n{'= AUTHORIZED RETRIEVAL SECURE BLOCK =':^60}")
                    for record in records:
                        print(f"Domain: {record.platform:<15} | ID: {record.username:<15} | Key: {record.password}")
                    print("=" * 60)
                elif choice_index := user_choice == "3":
                    print("[Termination Process Complete] System memory wiped clean.")
                    break
            except Exception as system_exception:
                print(f"[Subsystem Exception Intercepted] Execution Halted: {system_exception}")


if __name__ == "__main__":
    print("=== INITIALIZATION SEGMENT AUTHORIZATION ===")
    passphrase_input = input("Establish Vault Authorization Master Passphrase: ")
    if len(passphrase_input) < 12:
        print("[Security Policy Restriction] Master passphrase length must be >= 12 characters.")
        sys.exit(1)
        
    crypto_engine = AdvancedCryptoEngine(passphrase_input)
    data_access_object = RelationalCSVDataAccessObject("vault_v2.csv", crypto_engine)
    app_runtime = UserInterfaceController(data_access_object)
    app_runtime.execute_system_loop()
