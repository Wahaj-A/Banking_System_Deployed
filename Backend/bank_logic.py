"""
BANK LOGIC MODULE
-----------------
Database-backed banking logic.

Database selection:
- Local development: SQLite (banking.db)
- Vercel/production: Neon PostgreSQL using DATABASE_URL

The public classes and methods are kept compatible with the existing
FastAPI application:
    Auth
    Account
    Transaction
    Bank
"""

import hashlib
import os
import random
import sqlite3
from datetime import datetime, timezone

from Backend.logger import logger


# ---------------------------------------------------------------------------
# DATABASE CONFIGURATION
# ---------------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    DATABASE_TYPE = "postgres"
else:
    DATABASE_TYPE = "sqlite"

    DB_FILE = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "banking.db",
    )


# ---------------------------------------------------------------------------
# CONNECTION
# ---------------------------------------------------------------------------

def get_connection():
    """
    Return a database connection.

    If DATABASE_URL is configured, connect to Neon PostgreSQL.
    Otherwise, use the local SQLite database.
    """

    if DATABASE_TYPE == "postgres":
        try:
            import psycopg
            from psycopg.rows import dict_row

            conn = psycopg.connect(
                DATABASE_URL,
                row_factory=dict_row,
                connect_timeout=10,
            )

            return conn

        except Exception:
            logger.exception("DATABASE PostgreSQL connection failed")
            raise

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def _execute(conn, query, params=()):
    """
    Execute SQL using the correct placeholder style.

    SQLite uses:
        ?

    PostgreSQL uses:
        %s
    """

    if DATABASE_TYPE == "postgres":
        query = query.replace("?", "%s")

    return conn.execute(query, params)


# ---------------------------------------------------------------------------
# DATABASE INITIALIZATION
# ---------------------------------------------------------------------------

def init_db():
    """
    Create the required tables if they do not already exist.
    """

    conn = get_connection()

    try:
        if DATABASE_TYPE == "postgres":

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    account_id BIGSERIAL PRIMARY KEY,
                    account_number TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    balance DOUBLE PRECISION NOT NULL DEFAULT 0,
                    email TEXT
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id BIGSERIAL PRIMARY KEY,
                    account_id BIGINT NOT NULL,
                    type TEXT NOT NULL,
                    amount DOUBLE PRECISION NOT NULL,
                    balance_after DOUBLE PRECISION NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    FOREIGN KEY (account_id)
                        REFERENCES accounts(account_id)
                        ON DELETE CASCADE
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGSERIAL PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL
                )
                """
            )

        else:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    account_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_number TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    balance REAL NOT NULL DEFAULT 0,
                    email TEXT
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    type TEXT NOT NULL,
                    amount REAL NOT NULL,
                    balance_after REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (account_id)
                        REFERENCES accounts(account_id)
                )
                """
            )

            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

        conn.commit()

        logger.info(
            "DATABASE initialized successfully using %s",
            DATABASE_TYPE,
        )

    except Exception:
        conn.rollback()
        logger.exception("DATABASE initialization failed")
        raise

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# AUTHENTICATION
# ---------------------------------------------------------------------------

class Auth:
    """
    Handles user signup and login.

    Passwords are never stored directly.
    Each password is combined with a random salt and hashed using PBKDF2.
    """

    def __init__(self):
        init_db()

    def _hash_password(self, password, salt):
        return hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt),
            100_000,
        ).hex()

    def signup(self, email, password):
        email = email.strip().lower()

        if not email or not password:
            raise ValueError("Email and password are required.")

        if len(password) < 4:
            raise ValueError("Password must be at least 4 characters.")

        conn = get_connection()

        try:
            existing = _execute(
                conn,
                "SELECT 1 FROM users WHERE email = ?",
                (email,),
            ).fetchone()

            if existing:
                raise ValueError("That email is already registered.")

            salt = os.urandom(16).hex()
            password_hash = self._hash_password(password, salt)

            if DATABASE_TYPE == "postgres":
                conn.execute(
                    """
                    INSERT INTO users
                    (email, password_hash, salt, created_at)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        email,
                        password_hash,
                        salt,
                        datetime.now(timezone.utc),
                    ),
                )
            else:
                _execute(
                    conn,
                    """
                    INSERT INTO users
                    (email, password_hash, salt, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        email,
                        password_hash,
                        salt,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                )

            conn.commit()

            logger.info("AUTH signup completed")

        except ValueError:
            conn.rollback()
            raise

        except Exception:
            conn.rollback()
            logger.exception("AUTH signup failed")
            raise

        finally:
            conn.close()

    def login(self, email, password):
        email = email.strip().lower()

        conn = get_connection()

        try:
            row = _execute(
                conn,
                "SELECT * FROM users WHERE email = ?",
                (email,),
            ).fetchone()

        finally:
            conn.close()

        if row is None:
            logger.warning("AUTH invalid email")
            raise ValueError("Invalid email or password.")

        candidate_hash = self._hash_password(
            password,
            row["salt"],
        )

        if candidate_hash != row["password_hash"]:
            logger.warning("AUTH invalid credentials")
            raise ValueError("Invalid email or password.")

        logger.info("AUTH credentials verified")

        return row["email"]


# ---------------------------------------------------------------------------
# ACCOUNT
# ---------------------------------------------------------------------------

class Account:

    def __init__(self, row):
        self.account_id = row["account_id"]
        self.account_number = row["account_number"]
        self.name = row["name"]
        self.balance = row["balance"]
        self.email = row["email"]

    def __str__(self):
        return (
            f"ID {self.account_id} | "
            f"Account #{self.account_number}: "
            f"{self.name} — balance: {self.balance}"
        )


# ---------------------------------------------------------------------------
# TRANSACTION
# ---------------------------------------------------------------------------

class Transaction:

    def __init__(self, row):
        self.tx_type = row["type"]
        self.amount = row["amount"]
        self.balance_after = row["balance_after"]
        self.timestamp = row["timestamp"]

    def __str__(self):
        return (
            f"[{self.timestamp}] "
            f"{self.tx_type.upper():<10} "
            f"{self.amount:<10} "
            f"(balance after: {self.balance_after})"
        )


# ---------------------------------------------------------------------------
# BANK
# ---------------------------------------------------------------------------

class Bank:

    def __init__(self, name="My Bank"):
        self.name = name
        init_db()

    # -----------------------------------------------------------------------
    # ACCOUNT NUMBER
    # -----------------------------------------------------------------------

    def _generate_account_number(self, conn):

        while True:

            candidate = str(
                random.randint(100000, 999999)
            )

            exists = _execute(
                conn,
                "SELECT 1 FROM accounts WHERE account_number = ?",
                (candidate,),
            ).fetchone()

            if not exists:
                return candidate

    # -----------------------------------------------------------------------
    # CREATE ACCOUNT
    # -----------------------------------------------------------------------

    def create_account(
        self,
        name,
        starting_balance=0,
        email="",
    ):

        if not name or not str(name).strip():
            raise ValueError("Account name is required.")

        if starting_balance < 0:
            raise ValueError("Starting balance cannot be negative.")

        conn = get_connection()

        try:

            account_number = self._generate_account_number(conn)

            if DATABASE_TYPE == "postgres":

                row = conn.execute(
                    """
                    INSERT INTO accounts
                    (account_number, name, balance, email)
                    VALUES (%s, %s, %s, %s)
                    RETURNING account_id
                    """,
                    (
                        account_number,
                        str(name).strip(),
                        starting_balance,
                        email.strip().lower() if email else "",
                    ),
                ).fetchone()

                account_id = row["account_id"]

            else:

                cursor = _execute(
                    conn,
                    """
                    INSERT INTO accounts
                    (account_number, name, balance, email)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        account_number,
                        str(name).strip(),
                        starting_balance,
                        email.strip().lower() if email else "",
                    ),
                )

                account_id = cursor.lastrowid

            conn.commit()

            if starting_balance > 0:
                self._log_transaction(
                    account_id,
                    "Deposit",
                    starting_balance,
                    starting_balance,
                )

            logger.info("BANK account created")

            return self.find_account(account_number)

        except Exception:
            conn.rollback()
            logger.exception("BANK account creation failed")
            raise

        finally:
            conn.close()

    # -----------------------------------------------------------------------
    # FIND ACCOUNT
    # -----------------------------------------------------------------------

    def find_account(self, account_identifier):

        conn = get_connection()

        try:

            row = _execute(
                conn,
                """
                SELECT *
                FROM accounts
                WHERE account_number = ?
                   OR CAST(account_id AS TEXT) = ?
                LIMIT 1
                """,
                (
                    str(account_identifier),
                    str(account_identifier),
                ),
            ).fetchone()

            return Account(row) if row else None

        finally:
            conn.close()

    # -----------------------------------------------------------------------
    # INTERNAL TRANSACTION LOGGER
    # -----------------------------------------------------------------------

    def _log_transaction(
        self,
        account_id,
        tx_type,
        amount,
        balance_after,
    ):

        conn = get_connection()

        try:

            if DATABASE_TYPE == "postgres":

                conn.execute(
                    """
                    INSERT INTO transactions
                    (account_id, type, amount, balance_after, timestamp)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        account_id,
                        tx_type,
                        amount,
                        balance_after,
                        datetime.now(timezone.utc),
                    ),
                )

            else:

                _execute(
                    conn,
                    """
                    INSERT INTO transactions
                    (account_id, type, amount, balance_after, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        account_id,
                        tx_type,
                        amount,
                        balance_after,
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    ),
                )

            conn.commit()

        except Exception:
            conn.rollback()
            logger.exception("BANK transaction logging failed")
            raise

        finally:
            conn.close()

    # -----------------------------------------------------------------------
    # DEPOSIT
    # -----------------------------------------------------------------------

    def deposit(self, account_identifier, amount: float):

        if amount <= 0:
            raise ValueError("Deposit amount must be greater than zero.")

        acc = self.find_account(account_identifier)

        if not acc:
            raise ValueError("Account not found.")

        conn = get_connection()

        try:

            new_balance = float(acc.balance) + float(amount)

            _execute(
                conn,
                """
                UPDATE accounts
                SET balance = balance + ?
                WHERE account_id = ?
                """,
                (
                    amount,
                    acc.account_id,
                ),
            )

            if DATABASE_TYPE == "postgres":

                conn.execute(
                    """
                    INSERT INTO transactions
                    (account_id, type, amount, balance_after, timestamp)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        acc.account_id,
                        "Deposit",
                        amount,
                        new_balance,
                        datetime.now(timezone.utc),
                    ),
                )

            else:

                _execute(
                    conn,
                    """
                    INSERT INTO transactions
                    (account_id, type, amount, balance_after, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        acc.account_id,
                        "Deposit",
                        amount,
                        new_balance,
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    ),
                )

            conn.commit()

            logger.info("BANK deposit completed")

            return self.find_account(account_identifier)

        except Exception:
            conn.rollback()
            logger.exception("BANK deposit failed")
            raise

        finally:
            conn.close()

    # -----------------------------------------------------------------------
    # WITHDRAW
    # -----------------------------------------------------------------------

    def withdraw(self, account_identifier, amount: float):

        if amount <= 0:
            raise ValueError("Withdrawal amount must be greater than zero.")

        acc = self.find_account(account_identifier)

        if not acc:
            raise ValueError("Account not found.")

        if float(acc.balance) < float(amount):
            raise ValueError("Insufficient funds.")

        conn = get_connection()

        try:

            new_balance = float(acc.balance) - float(amount)

            _execute(
                conn,
                """
                UPDATE accounts
                SET balance = balance - ?
                WHERE account_id = ?
                """,
                (
                    amount,
                    acc.account_id,
                ),
            )

            if DATABASE_TYPE == "postgres":

                conn.execute(
                    """
                    INSERT INTO transactions
                    (account_id, type, amount, balance_after, timestamp)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        acc.account_id,
                        "Withdraw",
                        amount,
                        new_balance,
                        datetime.now(timezone.utc),
                    ),
                )

            else:

                _execute(
                    conn,
                    """
                    INSERT INTO transactions
                    (account_id, type, amount, balance_after, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        acc.account_id,
                        "Withdraw",
                        amount,
                        new_balance,
                        datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    ),
                )

            conn.commit()

            logger.info("BANK withdrawal completed")

            return self.find_account(account_identifier)

        except Exception:
            conn.rollback()
            logger.exception("BANK withdrawal failed")
            raise

        finally:
            conn.close()

    # -----------------------------------------------------------------------
    # TRANSFER
    # -----------------------------------------------------------------------

    def transfer(
        self,
        from_account_identifier,
        to_account_identifier,
        amount: float,
    ):

        if amount <= 0:
            raise ValueError("Transfer amount must be greater than zero.")

        sender = self.find_account(from_account_identifier)
        receiver = self.find_account(to_account_identifier)

        if not sender:
            raise ValueError("Sender account not found.")

        if not receiver:
            raise ValueError("Receiver account not found.")

        if sender.account_id == receiver.account_id:
            raise ValueError("Cannot transfer to the same account.")

        if float(sender.balance) < float(amount):
            raise ValueError("Insufficient funds in sender account.")

        conn = get_connection()

        try:

            sender_new_balance = (
                float(sender.balance) - float(amount)
            )

            receiver_new_balance = (
                float(receiver.balance) + float(amount)
            )

            _execute(
                conn,
                """
                UPDATE accounts
                SET balance = balance - ?
                WHERE account_id = ?
                """,
                (
                    amount,
                    sender.account_id,
                ),
            )

            _execute(
                conn,
                """
                UPDATE accounts
                SET balance = balance + ?
                WHERE account_id = ?
                """,
                (
                    amount,
                    receiver.account_id,
                ),
            )

            if DATABASE_TYPE == "postgres":

                now = datetime.now(timezone.utc)

                conn.execute(
                    """
                    INSERT INTO transactions
                    (account_id, type, amount, balance_after, timestamp)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        sender.account_id,
                        "Transfer Out",
                        amount,
                        sender_new_balance,
                        now,
                    ),
                )

                conn.execute(
                    """
                    INSERT INTO transactions
                    (account_id, type, amount, balance_after, timestamp)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        receiver.account_id,
                        "Transfer In",
                        amount,
                        receiver_new_balance,
                        now,
                    ),
                )

            else:

                now = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )

                _execute(
                    conn,
                    """
                    INSERT INTO transactions
                    (account_id, type, amount, balance_after, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        sender.account_id,
                        "Transfer Out",
                        amount,
                        sender_new_balance,
                        now,
                    ),
                )

                _execute(
                    conn,
                    """
                    INSERT INTO transactions
                    (account_id, type, amount, balance_after, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        receiver.account_id,
                        "Transfer In",
                        amount,
                        receiver_new_balance,
                        now,
                    ),
                )

            conn.commit()

            logger.info("BANK transfer completed")

            return (
                self.find_account(from_account_identifier),
                self.find_account(to_account_identifier),
            )

        except Exception:
            conn.rollback()
            logger.exception("BANK transfer failed")
            raise

        finally:
            conn.close()

    # -----------------------------------------------------------------------
    # LIST ACCOUNTS
    # -----------------------------------------------------------------------

    def list_accounts(self):

        conn = get_connection()

        try:

            rows = conn.execute(
                "SELECT * FROM accounts ORDER BY account_id"
            ).fetchall()

            return [Account(row) for row in rows]

        finally:
            conn.close()

    # -----------------------------------------------------------------------
    # TRANSACTION HISTORY
    # -----------------------------------------------------------------------

    def get_transaction_history(self, account_identifier):

        acc = self.find_account(account_identifier)

        if not acc:
            return []

        conn = get_connection()

        try:

            rows = _execute(
                conn,
                """
                SELECT *
                FROM transactions
                WHERE account_id = ?
                ORDER BY transaction_id DESC
                """,
                (acc.account_id,),
            ).fetchall()

            return [dict(row) for row in rows]

        finally:
            conn.close()

