import tkinter as tk
from tkinter import Menu, messagebox, simpledialog, filedialog
import random
import os
import sys
import glob
from PIL import Image, ImageTk, ImageSequence
from enum import Enum
import math

# --------------- 1. 配置中心 ---------------
import json   # 新增
class Config:
    ASSETS_DIR = "images"
    CONFIG_FILE = "config.json"

    # 默认值（如果 config.json 缺失或不全）
    DEFAULTS = {
        'animation_speed': 120,
        'movement_speed': 3,
        'action_interval_min': 3000,
        'action_interval_max': 8000,
        'drag_threshold': 5,
        'gravity': 2,
        'edge_snap_margin': 5,
        'snap_speed_threshold': 8,
        'mouse_idle_time_before_action': 30000,
        'mouse_follow_speed': 5,
        'begin_fall_velocity': 200,
        'fall_zoom_size': 150
    }

    def __init__(self):
        self.settings = self._load_settings()

    def _load_settings(self):
        """从 config.json 加载 settings 配置"""
        config_path = os.path.join(self.ASSETS_DIR, self.CONFIG_FILE)
        if not os.path.exists(config_path):
            print(f"⚠️ 配置文件未找到: {config_path}，使用默认值")
            return self.DEFAULTS.copy()

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            settings = data.get("settings", {})
            # 合并默认值，确保所有键都存在
            merged = self.DEFAULTS.copy()
            merged.update({k: v for k, v in settings.items() if k in self.DEFAULTS})
            return merged
        except Exception as e:
            print(f"⚠️ 读取配置失败: {e}，使用默认值")
            return self.DEFAULTS.copy()

    # --- 属性代理访问 ---
    @property
    def DEFAULT_ANIMATION_SPEED(self):
        return self.settings['animation_speed']

    @property
    def DEFAULT_MOVEMENT_SPEED(self):
        return self.settings['movement_speed']

    @property
    def ACTION_INTERVAL_MIN(self):
        return self.settings['action_interval_min']

    @property
    def ACTION_INTERVAL_MAX(self):
        return self.settings['action_interval_max']

    @property
    def DRAG_THRESHOLD(self):
        return self.settings['drag_threshold']

    @property
    def GRAVITY(self):
        return self.settings['gravity']

    @property
    def EDGE_SNAP_MARGIN(self):
        return self.settings['edge_snap_margin']

    @property
    def SNAP_SPEED_THRESHOLD(self):
        return self.settings['snap_speed_threshold']

    @property
    def MOUSE_IDLE_TIME_BEFORE_ACTION(self):
        return self.settings['mouse_idle_time_before_action']

    @property
    def MOUSE_FOLLOW_SPEED(self):
        return self.settings['mouse_follow_speed']

    @property
    def begin_fall_velocity(self):
        return self.settings['begin_fall_velocity']

    @property
    def fall_zoom_size(self):
        return self.settings['fall_zoom_size']

    @classmethod
    def load_characters(cls):
        """返回 dict: {角色名: {状态: gif绝对路径}}"""
        path = os.path.join(cls.ASSETS_DIR, cls.CONFIG_FILE)
        if not os.path.exists(path):
            return {}
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        chars = {}
        for char, state_map in raw.get("characters", {}).items():
            chars[char] = {st.lower(): os.path.join(cls.ASSETS_DIR, gif)
                           for st, gif in state_map.items()}
        return chars

# --- 2. 状态机 (State Machine) ---
class PetState(Enum):
    IDLE = "idle"
    MOVING = "moving"
    DRAGGING = "dragging"
    SLEEPING = "sleeping"
    FALLING = "falling" # 新增：掉落状态
    ANGRY = "angry"     # 新增
    BYEBYE = "byebye"   # 新增
    FOLLOWING_MOUSE = "following_mouse"

# --- 3. 核心类：桌面宠物 ---
class DesktopPet:

    def __init__(self, master):
        self.master = master
        self.config = Config()  # 现在会自动加载 settings
        self._setup_window()
        self.characters = Config.load_characters()   # 所有角色
        if not self.characters:
            messagebox.showerror("配置错误", "config.json 中没有定义任何角色！")
            sys.exit(1)
        self.character_names = list(self.characters.keys())
        self.current_char_idx = 0                    # 默认第一个角色
        self.state_map = self.characters[self.character_names[0]]
        # 原 self.state 改名
        self.behavior_state = PetState.IDLE
        # 新增拖动开关
        self.dragging_flag = False
        self.drag_start_pos = None   # 记录起点
        self.drag_moved = False      # 是否已“正式”拖动
        self.drag_start_pos = None
        self.animation_frames = []
        self.current_frame_index = 0
        self.current_gif_path = None
        self.action_manager = ActionManager(self)
        # 初始化鼠标位置（初始值不重要，后面会刷新）
        self.last_mouse_pos = (0, 0)
        self.mouse_idle_timer = None
        self.is_following_mouse = False
        self.click_counter = 0          # 连点次数
        self.click_reset_job = None     # 用于 1 秒内未点击就清零
        self._setup_ui()
        self._bind_events()
        self._ensure_assets_dir()
        self.load_animation()          # 这句原来就有
        self.change_gif_by_state()     # 新增：第一次套壳
        self._start_animation_loop()
        self._start_update_loop()
        self.action_manager.schedule_next_action()

        # >>> 新增：拖动计时器 <<<
        self.drag_timer_job = None
        self.long_drag_detected = False  # 是否已判定为长时间拖动

    @property
    def state(self):
        """兼容老代码：外部仍可用 self.state 读取行为状态"""
        return self.behavior_state

    @state.setter
    def state(self, value):
        self.behavior_state = value

    def _setup_window(self):
        self.master.overrideredirect(True)
        self.master.attributes("-topmost", True)
        
        try:
            self.master.wm_attributes("-transparentcolor", "white")
        except tk.TclError:
            self.master.attributes("-transparent", True)
            bg_color = 'systemTransparent' if sys.platform == "darwin" else 'white'
            self.master.config(bg=bg_color)
        
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()
        self.master.geometry(f"100x100+{screen_width//2-50}+{screen_height//2-50}")

    # --------------- DesktopPet 新增方法 ---------------
    def change_gif_by_state(self):
        """按当前状态切换 GIF，找不到就保持原样"""
        gif_path = self.state_map.get(self.state.value)
        if gif_path and os.path.exists(gif_path):
            self.load_animation(gif_path)
        # 找不到就什么都不做，继续用上一张

    def set_state(self, new_state: PetState):
        """安全地切换状态并换图"""
        if self.state == new_state:
            return
        self.state = new_state
        #print("[dbg]:",new_state)
        self.change_gif_by_state()

    # 新增：切角色
    def switch_to_character(self, char_name: str):
        """外部/菜单直接调用：先告别，再切到指定角色"""
        if self.state == PetState.BYEBYE:          # 防重复
            return
        print(f"{self.current_char_idx}:ByeBye")
        # 保存目标
        self._pending_char = char_name
        # 1. 立即进入 BYEBYE
        self.set_state(PetState.BYEBYE)
        # 2. 2 秒后真正执行
        self.master.after(2000, self._do_switch_character)

    def _do_switch_character(self):
        # 取出目标角色
        target = getattr(self, '_pending_char', None)
        if target not in self.character_names:
            self.set_state(PetState.IDLE)          # 异常兜底
            return
        # 真正切换
        self.current_char_idx = self.character_names.index(target)
        self.state_map = self.characters[target]
        print(f"切换角色 -> {target}")
        self.set_state(PetState.IDLE)

    def _setup_ui(self):
        bg_color = 'systemTransparent' if sys.platform == "darwin" and 'systemTransparent' in self.master.config('bg') else 'white'
        self.pet_label = tk.Label(self.master, bg=bg_color)
        self.pet_label.pack()

    def _bind_events(self):
        self.pet_label.bind("<Button-1>", self._on_drag_start)
        self.pet_label.bind("<ButtonRelease-1>", self._on_drag_release)
        self.pet_label.bind("<B1-Motion>", self._on_drag_motion)
        self.pet_label.bind("<Button-3>", self._show_context_menu)
        # ↓↓↓ 新增：单独监听左键按下（触发连点计数）
        self.pet_label.bind("<Button-1>", self._on_left_click, add="+")
        # ✅ 使用 bind_all 确保全屏捕获鼠标移动
        self.master.bind_all("<Motion>", self._on_mouse_move)

    def _on_mouse_move(self, event):
        # ✅ 使用 pointerx/pointery 获取屏幕绝对坐标
        current_mouse_x = self.master.winfo_pointerx()
        current_mouse_y = self.master.winfo_pointery()
        screen_h = self.master.winfo_screenheight()

        if current_mouse_y > screen_h:
            current_mouse_y = screen_h

        if (current_mouse_x, current_mouse_y) != self.last_mouse_pos:
            self.last_mouse_pos = (current_mouse_x, current_mouse_y)
            self._reset_mouse_idle_timer()
            if self.is_following_mouse:
                print("Mouse moved, stopping follow.")
                self.is_following_mouse = False
                if self.state == PetState.FOLLOWING_MOUSE:
                    self.set_state(PetState.IDLE)
                self.action_manager.schedule_next_action()

    def _reset_mouse_idle_timer(self):
        if self.mouse_idle_timer:
            self.master.after_cancel(self.mouse_idle_timer)
        self.mouse_idle_timer = self.master.after(self.config.MOUSE_IDLE_TIME_BEFORE_ACTION, self._on_mouse_idle)

    def _on_mouse_idle(self):
        print("Follow")
        if self.state not in [PetState.DRAGGING, PetState.FALLING]:
            # ✅ 强制刷新为当前真实鼠标位置
            current_mouse_x = self.master.winfo_pointerx()
            current_mouse_y = self.master.winfo_pointery()
            self.last_mouse_pos = (current_mouse_x, current_mouse_y)
            
            self.is_following_mouse = True
            self.action_manager.follow_mouse()

    # 新增方法：连点计数 + 进入愤怒
    def _on_left_click(self, event):
        # 新增：愤怒状态下完全忽略点击
        if self.state == PetState.ANGRY:
            return
        # 如果正在愤怒，不计数
        if self.state == PetState.BYEBYE:
            return
        self.click_counter += 1
        # 1 秒内无新点击就清零
        if self.click_reset_job:
            self.master.after_cancel(self.click_reset_job)
        self.click_reset_job = self.master.after(1000, self._reset_click_counter)
        # 达到 3 次 → 愤怒
        if self.click_counter >= 3:
            self._enter_angry()

    def _reset_click_counter(self):
        self.click_counter = 0

    def _enter_angry(self):
        self.click_counter = 0
        self.action_manager.cancel_next_action()          # 取消之前排队的动作
        self.set_state(PetState.ANGRY)                     # 换图（走已有逻辑）
        # 3 秒后自动退出
        self.master.after(2000, lambda: self.set_state(PetState.IDLE))

    def _ensure_assets_dir(self):
        if not os.path.exists(self.config.ASSETS_DIR):
            os.makedirs(self.config.ASSETS_DIR)
            messagebox.showinfo("提示", f"已创建'{self.config.ASSETS_DIR}'文件夹，请将GIF文件放入其中。")

    def _start_update_loop(self):
        self.action_manager.update()
        self.master.after(30, self._start_update_loop)

    def _start_animation_loop(self):
        if self.animation_frames:
            self.current_frame_index = (self.current_frame_index + 1) % len(self.animation_frames)
            current_frame_image = self.animation_frames[self.current_frame_index]
            self.pet_label.config(image=current_frame_image)
        self.master.after(self.config.DEFAULT_ANIMATION_SPEED, self._start_animation_loop)

    def load_animation(self, gif_path=None):
        if gif_path is None:
            gif_files = glob.glob(os.path.join(self.config.ASSETS_DIR, '*.gif'))
            if not gif_files:
                self._create_default_pet_image()
                return
            gif_path = random.choice(gif_files)
        try:
            self.animation_frames = []
            pil_image = Image.open(gif_path)
            frame_one = pil_image.copy().convert('RGBA')
            w, h = frame_one.size
            self.master.geometry(f"{w}x{h}")
            for frame in ImageSequence.Iterator(pil_image):
                frame_image = ImageTk.PhotoImage(frame.copy().convert('RGBA'))
                self.animation_frames.append(frame_image)
            self.current_gif_path = gif_path
            self.current_frame_index = 0
            if self.animation_frames:
                self.pet_label.config(image=self.animation_frames[0])
        except Exception as e:
            messagebox.showerror("加载错误", f"无法加载GIF文件 '{os.path.basename(gif_path)}'.\n错误: {e}")
            self._create_default_pet_image()

    def _create_default_pet_image(self):
        w, h = 64, 64
        self.master.geometry(f"{w}x{h}")
        bg_color = 'systemTransparent' if sys.platform == "darwin" and 'systemTransparent' in self.master.config('bg') else 'white'
        img = tk.PhotoImage(width=w, height=h)
        if bg_color == 'white':
            img.put(bg_color, to=(0, 0, w, h))
        for x in range(w):
            for y in range(h):
                if (x-w/2)**2 + (y-h/2)**2 <= (w/2-2)**2:
                    img.put("#ffcc00", (x, y))
        self.animation_frames = [img]
        self.pet_label.config(image=self.animation_frames[0])

    def _on_drag_start(self, event):
        # 记录拖动开始时鼠标的全局位置与窗口左上角的偏移
        self.drag_start_pos = (event.x_root, event.y_root)
        self.window_start_pos = (self.master.winfo_x(), self.master.winfo_y())
        self.dragging_flag = False
        self.drag_moved = False
        self.last_mouse_pos = (event.x_root, event.y_root)  # 用于速度计算
        self.release_velocity = 0  # 初始释放速度为0
        self._reset_mouse_idle_timer() # 重置计时器

        # >>> 新增：启动 3 秒计时器 <<<
        self.long_drag_detected = False
        self.drag_timer_job = self.master.after(1000, self._on_long_drag)

    def _on_drag_motion(self, event):
        if self.drag_start_pos is None:
            return
        # 当前鼠标全局位置
        x_root, y_root = event.x_root, event.y_root

        # 首次超过阈值 → 正式进入拖动模式
        dx_total = x_root - self.drag_start_pos[0]
        dy_total = y_root - self.drag_start_pos[1]
        dist = math.hypot(dx_total, dy_total)

        if not self.dragging_flag and dist >= self.config.DRAG_THRESHOLD:
            self.dragging_flag = True
            self.drag_moved = True
            self.action_manager.cancel_next_action()

        if self.dragging_flag:
            # 计算新窗口位置（基于初始窗口位置 + 鼠标移动差）
            new_x = self.window_start_pos[0] + (x_root - self.drag_start_pos[0])
            new_y = self.window_start_pos[1] + (y_root - self.drag_start_pos[1])
            self.master.geometry(f'+{int(new_x)}+{int(new_y)}')

            # 更新最后位置用于速度估算
            self.last_mouse_pos = (x_root, y_root)

    def _on_drag_release(self, event):
        if not self.dragging_flag and not self.drag_moved:
            # 纯点击，不做任何事
            self.drag_start_pos = None
            self.window_start_pos = None
            return

        # 标记结束拖动
        self.dragging_flag = False
        self.drag_moved = False

        # 只有向下速度快或靠近底部边缘才触发掉落
        current_x = self.master.winfo_x()
        current_y = self.master.winfo_y()
        pet_h = self.master.winfo_height()
        pet_w = self.master.winfo_width()
        screen_h = self.master.winfo_screenheight()
        screen_w = self.master.winfo_screenwidth()

        near_bottom = ((current_y + pet_h) > screen_h - self.config.fall_zoom_size) \
                    or ((current_x + pet_w) > screen_w - self.config.fall_zoom_size) \
                    or (current_y < self.config.fall_zoom_size) \
                    or (current_x < self.config.fall_zoom_size)    # 距离边300像素内
        
        # >>> 判断是否为长时间拖动，决定是否愤怒 <<<
        if self.long_drag_detected:
            self._enter_angry_on_release()
        else:
            # 否则按原逻辑判断是否掉落
            if near_bottom:
                self.set_state(PetState.FALLING)
                # 初始下落速度设为释放时的垂直速度（归一化）
                self.action_manager.fall_velocity = self.config.begin_fall_velocity
            else:
                if self.state != PetState.ANGRY and self.state != PetState.BYEBYE:
                    self.set_state(PetState.IDLE)
                    self.action_manager.schedule_next_action()

        self.drag_start_pos = None
        self.window_start_pos = None
        self._reset_mouse_idle_timer() # 重置计时器

    def _on_long_drag(self):
        """拖动持续超过3秒，标记为长拖"""
        self.long_drag_detected = True
        # 可选：播放提示音或轻微抖动，这里只做标记

    def _enter_angry_on_release(self):
        """因长时间拖动而进入愤怒状态"""
        self.action_manager.cancel_next_action()
        self.set_state(PetState.ANGRY)
        print("宠物生气了！被拖太久！")
        # 2秒后恢复
        self.master.after(2000, lambda: self.set_state(PetState.IDLE))

    def _show_context_menu(self, event):
        menu = Menu(self.master, tearoff=0)
        # 新增子菜单：选择角色
        char_menu = Menu(menu, tearoff=0)
        for name in self.character_names:
            # 命令里用 lambda 默认参数锁定当前名字
            char_menu.add_command(label=name,
                                command=lambda n=name: self.switch_to_character(n))
        menu.add_cascade(label="选择角色", menu=char_menu)

        menu.add_separator()
        menu.add_command(label="退出", command=self.master.quit)
        menu.post(event.x_root, event.y_root)

# --- 4. 行为管理器 (Decoupled Action Manager) ---
class ActionManager:
    def __init__(self, pet:DesktopPet):
        self.pet:DesktopPet = pet
        self.master = pet.master
        self.target_pos = None
        self.scheduled_action = None
        self.fall_velocity = 0 # 用于计算掉落速度

    def follow_mouse(self):
        self.cancel_next_action()
        self.pet.set_state(PetState.FOLLOWING_MOUSE)
        print("Pet is now following mouse.")
        self._set_mouse_target_pos()

    def _set_mouse_target_pos(self):
        """计算宠物应该移动到的鼠标中心位置（终极加固版）"""
        # ✅ 直接获取实时鼠标位置，不依赖 last_mouse_pos
        mouse_x = self.pet.master.winfo_pointerx()
        mouse_y = self.pet.master.winfo_pointery()
        
        self.master.update_idletasks()

        pet_w = self.master.winfo_width()
        pet_h = self.master.winfo_height()
        screen_w = self.master.winfo_screenwidth()
        screen_h = self.master.winfo_screenheight()

        # 保护默认尺寸
        if pet_w <= 1:
            pet_w = 64
        if pet_h <= 1:
            pet_h = 64


        # 限制坐标在屏幕范围内
        mouse_x = max(0, min(mouse_x, screen_w))
        mouse_y = max(0, min(mouse_y, screen_h))

        target_x = mouse_x - pet_w // 2
        target_y = mouse_y - pet_h // 2

        # 限制目标位置在屏幕内
        target_x = max(0, target_x)
        target_y = max(0, target_y)
        target_x = min(target_x, screen_w - pet_w)
        target_y = min(target_y, screen_h - pet_h)

        self.target_pos = (target_x, target_y)

    def _move_to_mouse_target(self):
        """使宠物移动到鼠标目标位置"""
        # ✅ 每次都重新计算目标位置（实时跟随）
        self._set_mouse_target_pos()
        if not self.target_pos:
            return

        current_x = self.master.winfo_x()
        current_y = self.master.winfo_y()

        dx = self.target_pos[0] - current_x
        dy = self.target_pos[1] - current_y
        distance = math.hypot(dx, dy)

        if distance < self.pet.config.MOUSE_FOLLOW_SPEED:
            self.master.geometry(f"+{self.target_pos[0]}+{self.target_pos[1]}")
            self.pet.set_state(PetState.IDLE)
            print("✅ 宠物已到达鼠标位置，停止跟随。")
        else:
            angle = math.atan2(dy, dx)
            move_x = self.pet.config.MOUSE_FOLLOW_SPEED * math.cos(angle)
            move_y = self.pet.config.MOUSE_FOLLOW_SPEED * math.sin(angle)
            new_x = round(current_x + move_x)
            new_y = round(current_y + move_y)
            self.master.geometry(f"+{new_x}+{new_y}")

    def schedule_next_action(self):
        if self.pet.is_following_mouse:
            return
        self.cancel_next_action()
        interval = random.randint(self.pet.config.ACTION_INTERVAL_MIN, self.pet.config.ACTION_INTERVAL_MAX)
        self.scheduled_action = self.master.after(interval, self.perform_random_action)

    def cancel_next_action(self):
        if self.scheduled_action:
            self.master.after_cancel(self.scheduled_action)
            self.scheduled_action = None

    def perform_random_action(self):
        # 只要正在拖动，就不执行任何随机行为
        if self.pet.dragging_flag:
            self.schedule_next_action()
            return
        # 愤怒状态下不做任何随机事
        if self.pet.state == PetState.ANGRY or self.pet.state == PetState.BYEBYE:
            self.schedule_next_action()
            return
        if self.pet.dragging_flag and self.pet.drag_moved or self.pet.state == PetState.FALLING or self.pet.is_following_mouse:
            self.schedule_next_action()
            return
        # 确保在安全的状态下执行随机行为
        if self.pet.state not in [PetState.DRAGGING, PetState.FALLING]:
            actions = {self.idle: 0.6, self.wander: 0.4}
            chosen_action = random.choices(list(actions.keys()), weights=list(actions.values()), k=1)[0]
            chosen_action()
        
        self.schedule_next_action()

    def update(self):
        """在主循环中被调用，用于更新需要持续进行的行为"""
        if self.pet.state == PetState.MOVING:
            self._move_towards_target()
        elif self.pet.state == PetState.FALLING:
            self._apply_gravity()
        elif self.pet.state == PetState.FOLLOWING_MOUSE:
            self._move_to_mouse_target()

    def idle(self):
        print("Action: Idle")
        self.pet.set_state(PetState.IDLE)
        self.target_pos = None

    def wander(self):
        print("Action: Wander")
        self.pet.set_state(PetState.MOVING)
        screen_w, screen_h = self.master.winfo_screenwidth(), self.master.winfo_screenheight()
        pet_w, pet_h = self.master.winfo_width(), self.master.winfo_height()
        self.target_pos = (random.randint(0, screen_w - pet_w), random.randint(0, screen_h - pet_h))

    def _move_towards_target(self):
        if not self.target_pos:
            self.pet.set_state(PetState.IDLE)
            return
        current_pos = (self.master.winfo_x(), self.master.winfo_y())
        dx, dy = self.target_pos[0] - current_pos[0], self.target_pos[1] - current_pos[1]
        distance = math.hypot(dx, dy)
        if distance < self.pet.config.DEFAULT_MOVEMENT_SPEED:
            self.master.geometry(f"+{self.target_pos[0]}+{self.target_pos[1]}")
            self.idle()
        else:
            angle = math.atan2(dy, dx)
            move_x = self.pet.config.DEFAULT_MOVEMENT_SPEED * math.cos(angle)
            move_y = self.pet.config.DEFAULT_MOVEMENT_SPEED * math.sin(angle)
            new_pos = (round(current_pos[0] + move_x), round(current_pos[1] + move_y))
            self.master.geometry(f"+{new_pos[0]}+{new_pos[1]}")
            
    def _apply_gravity(self):
        """重力→吸附到最近屏幕边缘"""
        screen_w = self.master.winfo_screenwidth()
        screen_h = self.master.winfo_screenheight()
        pet_w = self.master.winfo_width()
        pet_h = self.master.winfo_height()
        x, y = self.master.winfo_x(), self.master.winfo_y()

        # 1. 计算到四条边的距离
        dist_left = x
        dist_right = screen_w - (x + pet_w)
        dist_top = y
        dist_bottom = screen_h - (y + pet_h)
        min_dist, edge = min(
            (dist_left, 'left'),
            (dist_right, 'right'),
            (dist_top, 'top'),
            (dist_bottom, 'bottom')
        )

        # 2. 目标吸附坐标
        if edge == 'left':
            target_x, target_y = 0, y
        elif edge == 'right':
            target_x, target_y = screen_w - pet_w, y
        elif edge == 'top':
            target_x, target_y = x, 0
        else:  # bottom
            target_x, target_y = x, screen_h - pet_h

        # 3. 水平/垂直方向速度（统一用 fall_velocity 变量）
        dx = target_x - x
        dy = target_y - y
        distance = math.hypot(dx, dy)

        if distance < self.pet.config.EDGE_SNAP_MARGIN:
            # 已贴边→结束
            self.master.geometry(f"+{target_x}+{target_y}")
            self.pet.set_state(PetState.IDLE)
            self.schedule_next_action()
            self.fall_velocity = 0
            return

        # 4. 加速度朝向边缘
        self.fall_velocity += self.pet.config.GRAVITY
        # 在 apply_gravity 中增加最大速度限制
        MAX_FALL_SPEED = 20
        self.fall_velocity = min(self.fall_velocity, MAX_FALL_SPEED)
        move = min(self.fall_velocity, distance)  # 不要冲过边缘
        ratio = move / distance
        new_x = round(x + dx * ratio)
        new_y = round(y + dy * ratio)

        self.master.geometry(f"+{new_x}+{new_y}")


# --- 5. 程序入口 ---
def main():
    root = tk.Tk()
    app = DesktopPet(root)
    root.mainloop()

if __name__ == "__main__":
    main()