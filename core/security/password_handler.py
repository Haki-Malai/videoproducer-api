from passlib.context import CryptContext


class PasswordHandler:
    pwd_context = CryptContext(
        schemes=["bcrypt"],
        deprecated="auto",
    )

    def generate_password_hash(self, password: str) -> str:
        return self.pwd_context.hash(password)

    def check_password_hash(self, hashed_password: str, plain_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)


password_handler: PasswordHandler = PasswordHandler()
