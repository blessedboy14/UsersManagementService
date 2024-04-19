import passlib
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


passw = "asdasdcxz"


hashed = pwd_context.hash(passw)
print(pwd_context.verify(passw, hashed))
print(hashed)