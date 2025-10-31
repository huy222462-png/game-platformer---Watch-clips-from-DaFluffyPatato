import json
import os

USER_FILE = "users.json"

def load_users():
    if not os.path.exists(USER_FILE):
        with open(USER_FILE, "w") as f:
            json.dump({"users": []}, f)
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USER_FILE, "w") as f:
        json.dump(data, f, indent=4)

def register(username, password):
    data = load_users()
    for user in data["users"]:
        if user["username"] == username:
            return False, "Tên người dùng đã tồn tại!"
    data["users"].append({"username": username, "password": password})
    save_users(data)
    return True, "Đăng ký thành công!"

def login(username, password):
    data = load_users()
    for user in data["users"]:
        if user["username"] == username and user["password"] == password:
            return True, "Đăng nhập thành công!"
    return False, "Sai tên đăng nhập hoặc mật khẩu!"
