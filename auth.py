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
    # store extra fields for lockout / attempt tracking
    data["users"].append({
        "username": username,
        "password": password,
        "failed_attempts": 0,
        "locked": False
    })
    save_users(data)
    return True, "Đăng ký thành công!"

def login(username, password):
    data = load_users()
    # find user by username
    for user in data["users"]:
        if user.get("username") == username:
            # ensure fields exist (backwards compatibility)
            if "failed_attempts" not in user:
                user["failed_attempts"] = 0
            if "locked" not in user:
                user["locked"] = False

            if user.get("locked"):
                return False, "Tài khoản đã bị khóa do nhập sai nhiều lần."

            if user.get("password") == password:
                # successful login -> reset attempts
                user["failed_attempts"] = 0
                user["locked"] = False
                save_users(data)
                return True, "Đăng nhập thành công!"
            else:
                # wrong password -> increment attempts
                user["failed_attempts"] = user.get("failed_attempts", 0) + 1
                if user["failed_attempts"] >= 5:
                    user["locked"] = True
                    save_users(data)
                    return False, "Tài khoản đã bị khóa sau 5 lần nhập sai."
                else:
                    save_users(data)
                    remaining = 5 - user["failed_attempts"]
                    return False, f"Sai tên đăng nhập hoặc mật khẩu! Còn {remaining} lần thử."

    # username not found -> generic message (don't reveal existence)
    return False, "Sai tên đăng nhập hoặc mật khẩu!"
