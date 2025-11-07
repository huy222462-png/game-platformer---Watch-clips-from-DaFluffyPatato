game-platformer---Watch-clips-from-DaFluffyPatato
Game 2D, watch clip from DaFluffyPatato. this progam just learn. So it dont use to buy and sell.[main e6062c7] README.md have information of this program 1 file changed, 2 insertions(+), 1 deletion(-) Làm thêm được giao diện đăng nhập vào file json. Làm thêm được skill như phi tiêu(shuriken), vũ khí tầm gần(kunai).
Chạy game bằng File game.py Các file dữ liệu hình ảnh từ asset animation đến background cũng như âm thânh đều nằm trong Folder Data
# Game Platformer 2D - Hướng dẫn đầy đủ

Game 2D platformer được phát triển dựa trên clip của DaFluffyPatato. Đây là dự án học tập, không dùng cho mục đích thương mại.

## 💻 Cài đặt cho máy mới (Setup từ đầu)

### Bước 1: Cài đặt Python
1. **Tải Python từ trang chính thức:**
   - Vào https://python.org/downloads/
   - Tải Python 3.7+ (khuyến nghị Python 3.10+)
   
2. **Cài đặt Python:**
   - ✅ **Quan trọng:** Tích vào "Add Python to PATH"
   - Chọn "Install Now"

3. **Kiểm tra cài đặt:**
```bash
python --version
# Hoặc
python3 --version
```

### Bước 2: Cài đặt VS Code (khuyến nghị)
1. **Tải VS Code:**
   - Vào https://code.visualstudio.com/
   - Tải và cài đặt

2. **Cài Extension cho Python:**
   - Mở VS Code
   - Vào Extensions (Ctrl+Shift+X)
   - Tìm và cài "Python" (của Microsoft)
   - Tìm và cài "Pylance" (IntelliSense cho Python)

### Bước 3: Clone/Tải project
```bash
# Nếu có git:
git clone https://github.com/huy222462-png/game-platformer---Watch-clips-from-DaFluffyPatato.git

# Hoặc tải ZIP từ GitHub và giải nén
```

### Bước 4: Cài đặt thư viện Python
Mở Terminal/Command Prompt trong thư mục project:

```bash
# Cài pygame-ce (phiên bản mới, khuyến nghị):
pip install pygame-ce

# Nếu lỗi, thử:
pip install pygame

# Nếu máy có cả Python 2 và 3:
pip3 install pygame-ce

# Trên một số hệ thống:
python -m pip install pygame-ce
```

### Bước 5: Kiểm tra hoạt động
```bash
# Di chuyển vào thư mục project
cd game-platformer---Watch-clips-from-DaFluffyPatato

# Chạy game
python game.py
```

### ⚠️ Xử lý lỗi thường gặp:

#### Lỗi "python is not recognized":
- Python chưa được thêm vào PATH
- Cài lại Python và tích "Add to PATH"
- Hoặc dùng `py game.py` thay vì `python game.py`

#### Lỗi "No module named 'pygame'":
```bash
# Kiểm tra pip:
pip --version

# Cài lại pygame:
pip uninstall pygame pygame-ce
pip install pygame-ce

# Hoặc dùng conda (nếu có Anaconda):
conda install pygame
```

#### Lỗi âm thanh/graphics trên Linux:
```bash
sudo apt-get install python3-pygame
# Hoặc
sudo apt-get install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev
```

### 🎯 Test cài đặt thành công:
Nếu game chạy được và bạn thấy:
- Màn hình đăng nhập
- Có thể chọn nhân vật
- Game load map 1 và di chuyển được
➜ **Cài đặt thành công!**

## 🎮 Cách chạy game

```bash
python game.py
```

**Yêu cầu hệ thống:**
- Python 3.7+
- pygame-ce (hoặc pygame)

**Cài đặt thư viện:**
```bash
pip install pygame-ce
# hoặc
pip install pygame
```

## 🎨 Hệ thống Animation

### Cấu trúc thư mục Animation
```
data/images/entities/
├── player/
│   ├── idle/          # Animation nhàn rỗi
│   ├── run/           # Animation chạy
│   ├── jump/          # Animation nhảy
│   ├── slide/         # Animation trượt
│   └── wall_slide/    # Animation trượt tường
├── enemy/
│   ├── idle/          # Animation enemy đứng yên
│   └── run/           # Animation enemy di chuyển
└── boss/
    ├── idle/          # Animation boss đứng yên
    ├── walk/          # Animation boss đi bộ
    ├── attack1/       # Animation tấn công cận chiến
    ├── attack2/       # Animation tấn công tầm xa
    └── hurt/          # Animation bị thương
```

### Cách thêm Animation mới

1. **Tạo thư mục animation:**
```
data/images/entities/[tên_nhân_vật]/[tên_animation]/
```

2. **Đặt file ảnh theo thứ tự:**
- 0.png, 1.png, 2.png, ... (bắt đầu từ 0)
- Tất cả ảnh cùng kích thước
- Format PNG với nền trong suốt

3. **Thêm vào code:**
```python
# Trong game.py, phần load assets
try:
    self.assets['tên_nhân_vật/tên_animation'] = load_images('entities/tên_nhân_vật/tên_animation')
except:
    # Fallback nếu không tìm thấy
    pass
```

4. **Sử dụng trong class Entity:**
```python
def set_action(self, action):
    if action != self.action:
        self.action = action
        if action in self.game.assets:
            self.animation = self.game.assets[action].copy()
```

### Các thông số Animation quan trọng

- **img_duration**: Thời gian hiển thị mỗi frame (mặc định: 6)
- **loop**: Animation có lặp lại không (True/False)
- **done**: Animation đã hoàn thành chưa

## 🔊 Hệ thống Âm thanh

### Cấu trúc thư mục Âm thanh
```
data/sfx/
├── jump.wav           # Âm thanh nhảy
├── dash.wav           # Âm thanh lướt
├── hit.wav            # Âm thanh tấn công
├── shoot.wav          # Âm thanh bắn
└── ambience.wav       # Âm thanh nền
```

### Cách thêm Âm thanh mới

1. **Đặt file âm thanh:**
- Format: WAV (khuyến nghị) hoặc OGG
- Đặt trong thư mục `data/sfx/`
- Tên file ngắn gọn, dễ hiểu

2. **Load âm thanh trong code:**
```python
# Trong game.py, phần __init__
try:
    self.sfx = {
        'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
        'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
        'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
    }
except:
    self.sfx = {}  # Fallback nếu không có âm thanh
```

3. **Phát âm thanh:**
```python
# Phát âm thanh một lần
if 'jump' in self.game.sfx:
    self.game.sfx['jump'].play()

# Phát âm thanh với âm lượng
if 'hit' in self.game.sfx:
    sound = self.game.sfx['hit']
    sound.set_volume(0.5)  # 50% âm lượng
    sound.play()
```

## 💥 Hệ thống Va chạm (Collision)

### Collision Detection cơ bản

Game sử dụng hệ thống collision dựa trên **tile-based** và **rectangle collision**.

### 1. Tile Collision (Va chạm với địa hình)

```python
def collision_test(rect, tiles):
    """Kiểm tra va chạm giữa rectangle và danh sách tiles"""
    hit_list = []
    for tile in tiles:
        if rect.colliderect(tile):
            hit_list.append(tile)
    return hit_list

def move(rect, movement, tiles):
    """Di chuyển với xử lý collision"""
    # Di chuyển theo trục X trước
    rect.x += movement[0]
    hit_list = collision_test(rect, tiles)
    for tile in hit_list:
        if movement[0] > 0:  # Di chuyển sang phải
            rect.right = tile.left
        elif movement[0] < 0:  # Di chuyển sang trái
            rect.left = tile.right
    
    # Di chuyển theo trục Y sau
    rect.y += movement[1]
    hit_list = collision_test(rect, tiles)
    for tile in hit_list:
        if movement[1] > 0:  # Rơi xuống
            rect.bottom = tile.top
        elif movement[1] < 0:  # Nhảy lên
            rect.top = tile.bottom
    
    return rect, hit_list
```

### 2. Entity Collision (Va chạm giữa các đối tượng)

#### Player vs Enemy:
```python
# Trong update loop
player_rect = self.player.rect()
for enemy in self.enemies:
    enemy_rect = enemy.rect()
    if player_rect.colliderect(enemy_rect):
        # Xử lý va chạm player-enemy
        self.player.take_damage()
```

#### Projectile vs Entity:
```python
# Kiểm tra va chạm đạn
for projectile in self.projectiles[:]:
    proj_rect = projectile.rect()
    
    # Va chạm với enemy
    for enemy in self.enemies[:]:
        if proj_rect.colliderect(enemy.rect()):
            self.enemies.remove(enemy)
            self.projectiles.remove(projectile)
            break
```

### 3. Collision với Boss

Boss có hệ thống collision đặc biệt:

```python
class Boss:
    def rect(self):
        """Trả về collision box của boss (căn giữa)"""
        return pygame.Rect(
            self.pos[0] - self.size[0]//2, 
            self.pos[1] - self.size[1]//2, 
            self.size[0], 
            self.size[1]
        )
    
    def take_damage(self):
        """Xử lý khi boss bị tấn công"""
        if self.hit_cooldown <= 0:
            self.hp -= 1
            self.hit_cooldown = 60  # 1 giây cooldown
            if self.hp <= 0:
                return True  # Boss chết
        return False
```

### 4. Collision Types (Các loại va chạm)

#### Solid Collision (Va chạm rắn):
- Player không thể đi qua tiles
- Dừng chuyển động hoàn toàn

#### Trigger Collision (Va chạm kích hoạt):
- Pickup items (nhặt đồ)
- Spawn points
- Không chặn chuyển động

#### Damage Collision (Va chạm gây sát thương):
- Enemy tấn công player
- Player tấn công boss
- Projectile hit targets

### 5. Optimization Tips

#### Spatial Partitioning:
```python
# Chỉ kiểm tra collision với tiles gần player
nearby_tiles = []
for tile in self.tilemap.tiles_around(self.player.pos):
    nearby_tiles.append(tile['rect'])
```

#### Early Exit:
```python
# Thoát sớm nếu không có collision
if not rect.colliderect(bounding_box):
    return []  # Không cần kiểm tra chi tiết
```

## 🎯 Tính năng Game

### Hệ thống đăng nhập:
- Lưu thông tin người chơi trong file JSON
- Chọn nhân vật từ giao diện

### Hệ thống vũ khí:
- **Shuriken**: Vũ khí tầm xa, có thể ném
- **Kunai**: Vũ khí cận chiến, tấn công nhanh
- **Sword**: Vũ khí chính của player

### Hệ thống Boss:
- Boss có 15 HP
- Hai loại tấn công: cận chiến (<80px) và tầm xa (80-300px)
- Phải tiêu diệt hết enemy trước khi có thể đánh boss
- Hiển thị "WIN!" khi thắng boss

## 📁 Cấu trúc Project

```
game-platformer/
├── game.py              # File chính để chạy game
├── auth.py              # Hệ thống đăng nhập
├── users.json           # Dữ liệu người dùng
├── scripts/             # Các module game
│   ├── entities.py      # Player, Enemy, Boss classes
│   ├── utils.py         # Animation, Helper functions
│   ├── tilemap.py       # Hệ thống map
│   ├── particle.py      # Hiệu ứng particle
│   ├── spark.py         # Hiệu ứng tia lửa
│   ├── clouds.py        # Hiệu ứng mây
│   └── ui.py           # Giao diện người dùng
├── data/               # Assets game
│   ├── images/         # Hình ảnh
│   ├── maps/           # File map JSON
│   └── sfx/            # File âm thanh
└── README.md          # File hướng dẫn này
```

## 🚀 Mở rộng Game

### Thêm nhân vật mới:
1. Tạo thư mục animation trong `data/images/entities/`
2. Thêm class mới kế thừa từ Player
3. Load assets trong game.py

### Thêm map mới:
1. Tạo file JSON trong `data/maps/`
2. Sử dụng cấu trúc tilemap và spawners
3. Thêm vào danh sách maps trong game

### Thêm enemies mới:
1. Tạo class kế thừa từ Entity
2. Implement AI logic riêng
3. Thêm vào spawner system

---

**Lưu ý:** Đây là dự án học tập dựa trên hướng dẫn của DaFluffyPatato. Không sử dụng cho mục đích thương mại.