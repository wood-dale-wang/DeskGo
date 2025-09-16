# DeskGO

一个基于 Python `tkinter` 的桌面互动程序。人物可以在屏幕上自由活动、跟随鼠标、响应点击与拖动，并支持多角色切换。通过配置文件可轻松更换角色和动画。

---

## 🌟 功能特性

- **自由活动**：人物会在屏幕上随机移动或空闲。
- **鼠标交互**：
  - **点击**：连续快速点击 3 次，人物会进入“生气”状态。
  - **拖动**：
    - 短时间拖动：可自由移动人物。
    - 长时间拖动（超过 1 秒）：释放后人物会“生气”。
    - 拖到屏幕边缘附近（150 像素内）：触发“吸附”效果，自动吸附到边缘。
- **鼠标跟随**：鼠标长时间静止（30 秒），人物会自动跟随鼠标移动。
- **多角色支持**：通过 `config.json` 配置多个角色，右键菜单可随时切换。
- **状态管理**：支持 `idle`、`moving`、`dragging`、`falling`、`angry`、`byebye`、`following_mouse` 等多种行为状态。
- **GIF 动画播放**：支持透明背景的 GIF 动画，自动适配尺寸。

---

## 📦 项目结构

```
desktop_pet/
├── main.py              # 主程序
├── config.json          # 角色配置文件
├── images/              # GIF 动画资源目录
│   ├── cat_idle.gif
│   ├── cat_moving.gif
│   ├── dog_idle.gif
│   └── ...
└── README.md
```

---

## ⚙️ 配置说明

### 1. `config.json` 配置文件

用于定义多个角色及其对应的状态动画。格式如下：

```json
{
  "小猫": {
    "idle": "cat_idle.gif",
    "moving": "cat_moving.gif",
    "angry": "cat_angry.gif",
    "byebye": "cat_byebye.gif",
    "falling": "cat_falling.gif"
  },
  "小狗": {
    "idle": "dog_idle.gif",
    "moving": "dog_moving.gif",
    "angry": "dog_angry.gif"
  }
}
```

> ✅ 注意：
> - 状态名（如 `idle`）**必须小写**。
> - GIF 文件需放在 `images/` 目录下。
> - 若某个状态未定义，程序会沿用上一个动画。

---

### 2. 全局配置（`Config` 类）

| 配置项 | 默认值 | 说明 |
|-------|--------|------|
| `DEFAULT_ANIMATION_SPEED` | 120 | GIF 播放间隔（毫秒） |
| `DEFAULT_MOVEMENT_SPEED` | 3 | 移动速度（像素/帧） |
| `ACTION_INTERVAL_MIN/MAX` | 3000/8000 | 随机行为间隔（毫秒） |
| `DRAG_THRESHOLD` | 5 | 拖动判定阈值（像素） |
| `GRAVITY` | 2 | 掉落时的加速度 |
| `EDGE_SNAP_MARGIN` | 5 | 贴边判定距离（像素） |
| `MOUSE_IDLE_TIME_BEFORE_ACTION` | 30000 | 鼠标静止多久后开始跟随（毫秒） |
| `MOUSE_FOLLOW_SPEED` | 5 | 跟随鼠标的速度 |
| `begin_fall_velocity` | 200 | 初始掉落速度（归一化） |
| `fall_zoom_size` | 150 | 触发掉落的边缘距离（像素） |

> ⚠️ 可根据需要修改 `Config` 类中的常量。

---

## 🖱️ 交互方式

| 操作 | 效果 |
|------|------|
| 左键点击（3 次） | 人物进入“生气”状态（2 秒后恢复） |
| 左键拖动（短） | 移动人物，释放后可能掉落或恢复空闲 |
| 左键拖动（长 >1s） | 释放后人物“生气” |
| 鼠标静止（>30s） | 人物开始跟随鼠标 |
| 右键点击 | 弹出菜单：选择角色 / 退出 |

---

## 🛠️ 运行方法

### 1. 环境依赖

- Python 3.6+
- 安装依赖：
  ```bash
  pip install pillow
  ```

### 2. 文件准备

- 创建 `images/` 目录。
- 将所有 `.gif` 动画文件放入 `images/`。
- 创建 `config.json` 并配置角色。

### 3. 启动程序

```bash
python main.py
```

> ✅ 首次运行若无资源，会生成一个黄色圆形默认人物。

---

## 🔧 开发说明

- **状态机设计**：使用 `PetState` 枚举统一管理行为状态。
- **解耦设计**：`ActionManager` 负责行为逻辑，`DesktopPet` 负责 UI 与事件。
- **事件绑定**：
  - 使用 `bind_all` 确保鼠标移动事件全局捕获。
  - 使用 `winfo_pointerx/y()` 获取真实屏幕坐标。
- **性能优化**：
  - 动画循环独立于行为更新。
  - 拖动与点击事件互不干扰。

---

## 🐛 常见问题

| 问题 | 解决方案 |
|------|----------|
| 人物不透明 / 白底 | 确保系统支持透明色，或检查 `.gif` 是否为 RGBA 透明格式 |
| 动画不播放 | 检查路径、文件名拼写，确保 GIF 为合法动画格式 |
| 鼠标跟随不灵敏 | 调整 `MOUSE_FOLLOW_SPEED` 或检查 `winfo_pointerx()` 是否正常 |
| 切换角色无反应 | 检查 `config.json` 是否加载成功，路径是否正确 |

---

## 📎 示例：默认 `config.json`

```json
{
  "猫咪": {
    "idle": "cat_idle.gif",
    "moving": "cat_walk.gif",
    "angry": "cat_angry.gif",
    "byebye": "cat_byebye.gif",
    "falling": "cat_fall.gif"
  },
  "机器人": {
    "idle": "robot_idle.gif",
    "moving": "robot_walk.gif",
    "angry": "robot_angry.gif"
  }
}
```

---

## 📜 许可证

MIT License

---

> 💡 提示：你可以为人物添加音效、更多动画状态，或接入系统事件（如锁屏、音量变化）来增强互动性！