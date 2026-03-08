import jwt
secret = "test"
token = jwt.encode({"sub": "user"}, secret, algorithm="HS256")
try:
    jwt.decode(token, secret, algorithms=["HS256"])
    print("HS256 success")
except Exception as e:
    print(f"Error: {e}")

token2 = jwt.encode({"sub": "user"}, secret, algorithm="HS512")
try:
    jwt.decode(token2, secret, algorithms=["HS256"])
except Exception as e:
    print(f"Error 2: {e}")
