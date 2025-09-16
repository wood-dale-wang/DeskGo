# DeskGo - 轻量级桌面角色互动应用

**DeskGo** 是一个轻量、可扩展的桌面角色互动项目，使用 Python + Tkinter 构建。它允许你在桌面上放置可爱的动态角色，支持拖拽、跟随鼠标、自动行为、多角色切换等功能，并可通过 JSON 配置灵活自定义行为参数与角色资源。

> 🐾 让你的桌面不再孤单！

---

## ✨ 功能特性

- **动态 GIF 角色支持**：加载并播放透明背景的 GIF 动画。
- **智能行为系统**：
  - 闲置时随机走动或发呆
  - 被长时间拖动会“生气”抗议
  - 连点三次触发愤怒状态
  - 鼠标静止一段时间后自动跟随
- **物理模拟效果**：
  - 拖到屏幕边缘自动“掉落”吸附
  - 带速度感应的释放判定
- **多角色自由切换**：
  - 支持通过右键菜单实时更换人物角色
  - 每个角色可配置不同状态动画（idle, moving, angry 等）
- **高度可配置化**：
  - 所有速度、时间间隔、灵敏度等均可在 `config.json` 中调整
  - 无需修改代码即可添加新角色和动画

---

## 📦 项目结构

```bash
DeskGo/
├── images/                     # 资源目录（默认存放 GIF 文件）
│   └── config.json             # 角色与设置配置文件
├── deskgo.py                   # 主程序入口
└── README.md                   # 本文件
```

---

## ⚙️ 配置说明

### 1. `config.json` 示例

```json
{
  "settings": {
    "animation_speed": 120,
    "movement_speed": 3,
    "action_interval_min": 3000,
    "action_interval_max": 8000,
    "drag_threshold": 5,
    "gravity": 2,
    "edge_snap_margin": 5,
    "snap_speed_threshold": 8,
    "mouse_idle_time_before_action": 30000,
    "mouse_follow_speed": 5,
    "begin_fall_velocity": 200,
    "fall_zoom_size": 150
  },
  "characters": {
    "anon": {
            "idle": "anon/anon1.gif",
            "moving": "anon/anon1.gif",
            "falling": "anon/anon1.gif",
            "sleeping": "anon/anon1.gif",
            "angry": "anon/anon2.gif",
            "byebye": "anon/anon3.gif"
        },
        "mutsumi": {
            "idle": "mutsumi/mutsumi1.gif",
            "moving": "mutsumi/mutsumi1.gif",
            "falling": "mutsumi/mutsumi1.gif",
            "sleeping": "mutsumi/mutsumi1.gif",
            "angry": "mutsumi/mutsumi2.gif",
            "byebye": "mutsumi/mutsumi3.gif"
        }
  }
}
```

> 💡 所有路径均相对于 `images/` 目录。

---

## 🧰 使用方法

### 1. 环境依赖

确保已安装 Python 3.6+ 及以下库：

```bash
pip install pillow
```

> Tkinter 通常随 Python 自带。

### 2. 准备资源

1. 在 `images/` 目录下放入你的透明背景 GIF 动画。
2. 编写 `images/config.json`，定义角色及其对应的状态动画。

### 3. 启动程序

```bash
python deskgo.py
```

### 4. 操作方式

| 操作 | 效果 |
|------|------|
| 左键点击 | 触发交互（连点3次 → 生气） |
| 左键拖动 | 移动人物；持续超过1秒 → 生气 |
| 拖至屏幕边缘释放 | 人物“掉落”并吸附到边框 |
| 鼠标静止30秒 | 人物开始跟随鼠标 |
| 右键点击 | 打开菜单：切换角色 / 退出 |

---

## 🔧 开发者说明

### 核心模块设计

- `Config`：配置管理器，自动加载 `config.json` 并提供默认值兜底。
- `PetState (Enum)`：有限状态机控制人物行为逻辑。
- `DesktopPet`：主窗口与事件处理。
- `ActionManager`：解耦的行为调度器，负责移动、跟随、掉落等动作更新。
- 状态驱动动画：通过 `set_state()` 自动匹配对应 GIF。

### 扩展建议

- 添加声音反馈（如愤怒叫声）
- 支持更多状态（如睡觉、吃东西）
- 引入 AI 对话接口（如接入 LLM）
- 实现保存/读取用户偏好设置

---

## 📄 许可协议

MIT License

---

## 🙌 致谢

感谢所有开源社区贡献者！  
特别鸣谢：Pillow 团队、Tkinter 维护者。

---

📌 **提示**：首次运行若无 `images/` 目录，程序将自动创建并生成一个默认黄色圆形占位人物。
