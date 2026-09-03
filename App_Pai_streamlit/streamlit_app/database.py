import sqlite3
import hashlib
import secrets
from pathlib import Path

# ==========================================================
# CONFIGURAÇÃO DA BASE DE DADOS
# ==========================================================

DB_DIR = Path("data")
DB_DIR.mkdir(exist_ok=True)

DB_FILE = DB_DIR / "database.db"


def get_connection():
    return sqlite3.connect(DB_FILE)


# ==========================================================
# CRIAÇÃO DA BASE DE DADOS
# ==========================================================

def init_db():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS pedidos(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            colaborador TEXT NOT NULL,

            data_inicio TEXT NOT NULL,

            data_fim TEXT NOT NULL,

            periodo TEXT NOT NULL,

            estado TEXT NOT NULL DEFAULT 'Pendente',

            aprovado_por TEXT,

            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS responsaveis(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            nome TEXT UNIQUE NOT NULL,

            salt TEXT NOT NULL,

            password_hash TEXT NOT NULL,

            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP

        )
    """)

    conn.commit()
    conn.close()


# ==========================================================
# AUTENTICAÇÃO DE RESPONSÁVEIS
# ==========================================================

def _hash_password(password, salt=None):
    """Gera um hash seguro (PBKDF2-SHA256) da password, com salt aleatório."""

    if salt is None:
        salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100_000
    ).hex()

    return salt, password_hash


def criar_responsavel(nome, password):
    """Cria um novo responsável com password. Devolve False se o nome já existir."""

    salt, password_hash = _hash_password(password)

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            INSERT INTO responsaveis(nome, salt, password_hash)
            VALUES(?,?,?)
        """, (nome, salt, password_hash))

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        return False

    finally:
        conn.close()


def verificar_login(nome, password):
    """Verifica se o nome + password correspondem a um responsável válido."""

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT salt, password_hash
        FROM responsaveis
        WHERE nome = ?
    """, (nome,))

    row = cur.fetchone()
    conn.close()

    if not row:
        return False

    salt, password_hash_guardada = row
    _, password_hash_calculada = _hash_password(password, salt)

    return secrets.compare_digest(password_hash_calculada, password_hash_guardada)


def listar_responsaveis():
    """Devolve a lista de nomes de responsáveis (para preencher o login)."""

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT nome FROM responsaveis ORDER BY nome")
    rows = [r[0] for r in cur.fetchall()]

    conn.close()

    return rows


def alterar_password(nome, nova_password):
    """Atualiza a password de um responsável existente."""

    salt, password_hash = _hash_password(nova_password)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE responsaveis
        SET salt=?, password_hash=?
        WHERE nome=?
    """, (salt, password_hash, nome))

    conn.commit()
    conn.close()


# ==========================================================
# INSERIR PEDIDO
# ==========================================================

def inserir_pedido(
    colaborador,
    data_inicio,
    data_fim,
    periodo
):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO pedidos(
            colaborador,
            data_inicio,
            data_fim,
            periodo
        )
        VALUES(?,?,?,?)
    """, (
        colaborador,
        data_inicio,
        data_fim,
        periodo
    ))

    conn.commit()
    conn.close()


# ==========================================================
# LISTAR PEDIDOS
# ==========================================================
def listar_pedidos():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            colaborador,
            data_inicio,
            data_fim,
            periodo,
            estado,
            IFNULL(aprovado_por,'')
        FROM pedidos
        ORDER BY id DESC
    """)

    rows = cur.fetchall()

    conn.close()

    return rows


# ==========================================================
# APROVAR PEDIDO
# ==========================================================

def aprovar_pedido(
    id_pedido,
    responsavel
):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE pedidos
        SET estado=?,
            aprovado_por=?
        WHERE id=?
    """, (
        "Aprovado",
        responsavel,
        id_pedido
    ))

    conn.commit()
    conn.close()


# ==========================================================
# RECUSAR PEDIDO
# ==========================================================

def recusar_pedido(
    id_pedido,
    responsavel
):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE pedidos
        SET estado=?,
            aprovado_por=?
        WHERE id=?
    """, (
        "Recusado",
        responsavel,
        id_pedido
    ))

    conn.commit()
    conn.close()


# ==========================================================
# ELIMINAR PEDIDO
# ==========================================================

def apagar_pedido(id_pedido):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM pedidos
        WHERE id = ?
    """, (id_pedido,))

    conn.commit()
    conn.close()
