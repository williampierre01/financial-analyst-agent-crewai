"""Explicit operator actions, never called on application startup."""
import argparse
import sys

from backend.security.database import Database
from backend.security.auth import FirebaseIdentity


def main():
    parser = argparse.ArgumentParser(description="Configuração de acesso ao Analista")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("migrate")
    invite = sub.add_parser("invite")
    invite.add_argument("email")
    invite.add_argument("--role", choices=("user", "admin"), default="user")
    allow = sub.add_parser("allow")
    allow.add_argument("uid", help="UID copiado do Firebase, não o e-mail")
    allow.add_argument("--role", choices=("user", "admin"), default="user")
    disable = sub.add_parser("disable")
    disable.add_argument("uid")
    args = parser.parse_args()
    try:
        db = Database()
        if args.action == "migrate":
            db.migrate()
        elif args.action == "invite":
            identity = FirebaseIdentity()
            # No temporary password and no automatic message. The user chooses
            # their password through Firebase's recovery email in the UI.
            account = identity.auth.create_user(email=args.email, email_verified=False, app=identity.app)
            db.allow_user(account.uid, args.role)
            print("Conta criada. Oriente a pessoa a usar Primeiro acesso no aplicativo.")
        elif args.action == "allow":
            identity = FirebaseIdentity()
            account = identity.current(args.uid)
            if account.disabled:
                raise ValueError("Disabled account")
            db.allow_user(args.uid, args.role)
        else:
            db.disable_user(args.uid)
            identity = FirebaseIdentity()
            identity.auth.revoke_refresh_tokens(args.uid, app=identity.app)
        print("Operação concluída.")
    except Exception:
        print("Operação não concluída. Confira configuração e permissões. Em invite, confira se a conta foi criada no Firebase antes de repetir; use allow pelo UID se necessário. Em disable, confirme o estado da conta.", file=sys.stderr)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
