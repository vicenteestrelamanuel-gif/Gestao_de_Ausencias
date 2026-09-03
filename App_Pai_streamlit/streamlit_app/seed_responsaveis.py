"""
Corre este script UMA VEZ para criar os responsáveis iniciais com password.
Depois de correr, cada responsável deve mudar a sua password
(ver database.alterar_password).

Uso local:
    python seed_responsaveis.py
"""

from database import init_db, criar_responsavel

# Define aqui os responsáveis e uma password temporária para cada um.
# IMPORTANTE: muda estas passwords depois do primeiro login!
RESPONSAVEIS_INICIAIS = {
    "Bruno Carrulo": "muda-me-123",
    "Bruno Santos": "muda-me-123",
    "Bruno Ribeiro": "muda-me-123",
}


if __name__ == "__main__":
    init_db()

    for nome, password in RESPONSAVEIS_INICIAIS.items():
        criado = criar_responsavel(nome, password)

        if criado:
            print(f"✅ Responsável criado: {nome}")
        else:
            print(f"⚠️  Já existia: {nome}")

    print("\nConcluído. Podes agora apagar as passwords deste ficheiro por segurança.")
