import sys, time, subprocess, GPUtil, os, psutil, gc, tracemalloc, json, random
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QMenu, QSystemTrayIcon
from PyQt5.QtCore import Qt, QEvent, QTimer
from PyQt5.QtGui import QCursor, QPixmap, QIcon
from PyQt5.QtWidgets import QLabel
# 自定义包导入
from 动画模块 import Animation
from 音频模块 import Sound
from 定时模块 import Timer
from 聊天模块 import ModelApi
from 设置模块 import Personal_Settings

def memory_usage():
    """返回当前进程内存使用量(MB)"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

class MyQtDeskPet(QWidget):
    '''程序主体入口'''
    def __init__(self):
        '''参数和对象初始化'''
        super().__init__() # 父类窗口初始化
        self.abspath = os.path.dirname(os.path.abspath(__file__)) # 获取程序运行的绝对路径名
        self.hiding = False # 躲藏状态标志
        self.walk_change = False # 走路图像翻转
        self.follow_change = False # 爬动图像翻转
        self.is_move = False # 是否移动
        with open(os.path.join(self.abspath, '预设参数', '桌宠参数.json'), 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        with open(os.path.join(self.abspath, '预设参数', self.data['style']+'.qss'),'r',encoding='utf-8') as f:
            self.theme = f.read()
        self.dv = self.data['dv'] # 初始化移动速度
        self.click_times = 0 # 点击次数
        self.ui_init() # 界面初始化
        self.animation = Animation(self, self.data['interval']) # 实例化动画类
        self.sound = Sound() # 实例化音频类
        self.sound.say('随机声音/你好.mp3') # 初始语音播放
        self.timer = Timer(self) # 实例化定时器类
        self.dialog = Personal_Settings(self) # 实例化设置类
        
    def ui_init(self):
        '''界面初始化'''
        self.label = QLabel(self) # 初始化图片容器
        self.label.setAlignment(Qt.AlignCenter)
        self.setFixedSize(self.data['size']*100, int(self.data['size']*400/3)) # 设置初始大小（比例为3：4）
        self.setAttribute(Qt.WA_TranslucentBackground) # 窗口透明指令（需要和隐藏标题栏一起使用，否则窗口背景为黑色）
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint) # 标题栏隐藏和窗口置顶指令
        self.setWindowFlags(self.windowFlags() | Qt.Tool) # 隐藏任务栏图标
        self.setAcceptDrops(True) # 允许拖放文件
        layout = QVBoxLayout() # 布局器
        layout.addWidget(self.label)
        self.setLayout(layout)
        tray_icon = QSystemTrayIcon(QIcon(os.path.join(self.abspath, "图片", "图标", "icon.png")), self) # 托盘图标设置
        self.tray = QMenu() # 托盘菜单
        self.tray.setStyleSheet(self.theme) # 设置托盘菜单栏样式
        show_action = self.tray.addAction("显示桌宠")
        middle_action = self.tray.addAction("居中显示") # 防止桌宠被移动到窗口边界找不到
        set_action = self.tray.addAction("个性化设置")
        quit_action = self.tray.addAction("退出程序")
        show_action.triggered.connect(self.show) # 连接信号和槽
        set_action.triggered.connect(self.open_setting)
        quit_action.triggered.connect(self.exit)
        middle_action.triggered.connect(self.middle)
        tray_icon.setContextMenu(self.tray) # 设置托盘图标的上下文菜单
        tray_icon.show() # 显示托盘图标

    def middle(self):
        '''在屏幕正中间显示桌宠'''
        screen = QApplication.desktop().availableGeometry(self)
        self.move(int(screen.right()/2-self.width()/2), int(screen.bottom()/2-self.height()/2))

    def enterEvent(self,a0):
        '''自定义鼠标光标'''
        pixmap = QPixmap(os.path.join(self.abspath, "图片", "hand.png")).scaled(64, 48) # 加载图像文件
        self.setCursor(QCursor(pixmap))
  
    def move_window(self):
        '''桌宠水平移动'''
        screen = QApplication.desktop().availableGeometry(self)
        new_x = self.x() + self.dv
        # 保证窗口到屏幕边沿反弹
        if new_x < -120:
            new_x = -120
            self.dv = -self.dv
            self.walk_change = False
        elif new_x > screen.right()-120:
            new_x = screen.right()-120
            self.dv = -self.dv
            self.walk_change = True
        self.move(new_x, self.y())

    def follow(self):
        '''桌宠跟随鼠标移动'''
        mouse_pos = QCursor.pos()
        pet_rect = self.frameGeometry()
        center_x = pet_rect.x() + pet_rect.width() // 2
        center_y = pet_rect.y() + pet_rect.height() // 2

        dx = mouse_pos.x() - center_x
        dy = mouse_pos.y() - center_y

        distance = (dx ** 2 + dy ** 2) ** 0.5
        if distance < self.dv/2:
            self.sound.rand_say('跟随鼠标')
            self.animation.stop_all_animation()
            self.animation.action4.start(self.animation.interval)
            return  # 已经很接近鼠标，不再移动
        speed = abs(self.dv)
        move_x = int(center_x + speed * dx / distance)
        move_y = int(center_y + speed * dy / distance)
        if dx > 0:
            self.follow_change = True
        else:
            self.follow_change = False
        new_x = move_x - pet_rect.width() // 2
        new_y = move_y - pet_rect.height() // 2
        self.move(new_x, new_y)

    def bubble(self, content):
        '''创建文字显示气泡'''
        reminder_bubble = QLabel(content, None) # 父参数设为None，使其成为独立窗口
        reminder_bubble.setWindowFlags(
            Qt.FramelessWindowHint |  # 无边框
            Qt.Tool |  # 不在任务栏显示
            Qt.WindowStaysOnTopHint  # 置顶
        )
        # 根据窗口宽度动态调整气泡宽度和字体大小
        bubble_width = max(150, min(0.6 * self.width(), 500))
        font_size = max(15, min(int(self.width() / 30), 40))
        reminder_bubble.setFixedWidth(int(bubble_width))
        # 根据当前主题切换气泡配色（可根据需要在 data 中添加更多主题或自定义颜色）
        theme_map = {
            '橙色': ('rgba(255,250,230,200)', 'rgba(255,240,200,200)', '#FFA500'),
            '绿色': ('rgba(230,255,240,200)', 'rgba(200,255,220,200)', '#28A745'),
            '蓝色': ('rgba(232,244,255,200)', 'rgba(220,235,255,200)', '#007BFF'),
        }
        bg_start, bg_end, border_color = theme_map[self.data['style']]
        reminder_bubble.setStyleSheet(f"""
        QLabel {{
            background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1,
                stop:0 {bg_start}, stop:1 {bg_end});
            border: 2px solid {border_color};
            border-radius: 15px;
            padding: 15px;
            font-size: {font_size}px;
            font-weight: bold;
            color: #333;
        }}
        """)
        reminder_bubble.setWordWrap(True)
        reminder_bubble.adjustSize()
        # 获取桌宠的位置并计算气泡位置
        pet_rect = self.frameGeometry()
        bubble_x = pet_rect.x() + (pet_rect.width() - reminder_bubble.width()) // 2
        bubble_y = pet_rect.y() - 50
        # 确保气泡不会超出屏幕上方
        screen_geo = QApplication.desktop().availableGeometry()
        if bubble_y < screen_geo.top():
            bubble_y = pet_rect.bottom() - 50 # 如果上方空间不足，显示在桌宠下方
        
        reminder_bubble.move(bubble_x, bubble_y)
        reminder_bubble.show()
        reminder_bubble.raise_() # 确保气泡在最前面
        # 实现淡出功能
        def fade_out():
            if reminder_bubble.underMouse():
                # 鼠标在气泡上，延迟消失
                QTimer.singleShot(500, fade_out)
            else:
                animation = reminder_bubble.graphicsEffect() if hasattr(reminder_bubble, 'graphicsEffect') else None
                # 使用窗口透明度实现淡出
                step = 0.1
                def do_fade(opacity=1.0):
                    if reminder_bubble.underMouse():
                        reminder_bubble.setWindowOpacity(1.0)
                        QTimer.singleShot(500, fade_out)
                        return
                    opacity -= step
                    if opacity <= 0:
                        reminder_bubble.deleteLater()
                    else:
                        reminder_bubble.setWindowOpacity(opacity)
                        QTimer.singleShot(100, lambda: do_fade(opacity))
                do_fade()
        QTimer.singleShot(len(content)*300, fade_out)

    def contextMenuEvent(self, a0):
        '''菜单界面设置'''
        dir = os.path.join(self.abspath, "图片", "图标") # 菜单图标文件夹
        if self.timer.sleeping: # 睡觉状态下只显示唤醒、隐藏和退出选项
            menu = QMenu(self)
            menu.setStyleSheet(self.theme) # 设置菜单栏样式
            action_wake = menu.addAction("唤醒")
            action_wake.setIcon(QIcon(os.path.join(dir, "灯泡.png")))
            action_hide = menu.addAction("隐藏")
            action_hide.setIcon(QIcon(os.path.join(dir, "眼睛.png")))
            action_exit = menu.addAction("退出")
            action_exit.setIcon(QIcon(os.path.join(dir, "退出.png")))
            action = menu.exec_(a0.globalPos())
            if action == action_wake:
                self.wake_up()
            if action == action_exit:
                self.exit()
            if action == action_hide:
                self.hide()
        else:
            menu = QMenu(self)
            menu.setStyleSheet(self.theme) # 设置菜单栏样式
            action_menu = menu.addMenu("动作")
            action_menu.setIcon(QIcon(os.path.join(dir, "猫爪.png")))
            action1 = action_menu.addAction("动作 1")
            action2 = action_menu.addAction("动作 2")
            action3 = action_menu.addAction("动作 3")
            action4 = action_menu.addAction("动作 4")
            action5 = action_menu.addAction("动作 5")
            action_follow = action_menu.addAction("跟随鼠标")
            action_move = action_menu.addAction("移动")
            action_move.setIcon(QIcon(os.path.join(dir, "走动.png")))
            action_stop = action_menu.addAction("暂停")
            action_sleep = action_menu.addAction("睡觉")
            action_sleep.setIcon(QIcon(os.path.join(dir, "zzz.png")))

            sound_menu = menu.addMenu("声音")
            sound_menu.setIcon(QIcon(os.path.join(dir, "声音.png")))
            action_rand_sound = sound_menu.addAction("随机语音")
            action_rand_sound.setIcon(QIcon(os.path.join(dir, "语音.png")))
            action_music = sound_menu.addAction("随机音乐")
            action_music.setIcon(QIcon(os.path.join(dir, "音符.png")))

            menu.addSeparator() # 添加分隔线
            action_chat = menu.addAction("启动聊天模式")
            action_chat.setIcon(QIcon(os.path.join(dir, "聊天框.png")))
            action_save = menu.addAction("文件保存位置")
            action_save.setIcon(QIcon(os.path.join(dir, "文件夹.png")))
            action_hide = menu.addAction("隐藏")
            action_hide.setIcon(QIcon(os.path.join(dir, "眼睛.png")))
            action_set = menu.addAction("个性化设置")
            action_set.setIcon(QIcon(os.path.join(dir, "设置.png")))
            action_source = menu.addAction("电脑资源利用率")
            action_source.setIcon(QIcon(os.path.join(dir, "资源.png")))

            menu.addSeparator()
            action_about = menu.addAction("关于桌宠")
            action_about.setIcon(QIcon(os.path.join(dir, "问号.png")))
            action_exit = menu.addAction("退出")
            action_exit.setIcon(QIcon(os.path.join(dir, "退出.png")))
            action_view = menu.addAction("内存使用量")

            action = menu.exec_(a0.globalPos())
            #菜单事件绑定
            if action == action_exit:
                self.animation.stop_all_animation()
                self.animation.show_img('goodbye')
                self.sound.say('再见.mp3')
                QTimer.singleShot(3400, self.exit) # 等待语音播放完成后退出
            if action == action1: # 动作1
                self.animation.stop_all_animation()
                self.animation.action1.start(self.animation.interval)
            if action == action_move: # 移动
                self.animation.stop_all_animation()
                self.animation.walk.start(self.animation.interval)
                self.timer.movement.start(self.animation.interval)
            if action == action_stop: # 暂停所有动作
                self.animation.stop_all_animation()
            if action == action_sleep: # 睡觉
                self.animation.stop_all_animation()
                self.sound.rand_say('睡觉')
                self.go_to_sleep()
            if action == action_rand_sound:
                self.sound.rand_say('随机声音')
            if action == action2: # 动作2
                self.animation.stop_all_animation()
                self.animation.action2.start(self.animation.interval)
            if action == action3: # 动作3
                self.animation.stop_all_animation()
                self.sound.rand_say('动作3')
                self.animation.action3.start(self.animation.interval)
            if action == action4: # 动作4
                self.animation.stop_all_animation()
                self.sound.rand_say('动作4')
                self.animation.action4.start(self.animation.interval)
            if action == action5: # 动作5
                self.animation.stop_all_animation()
                self.sound.rand_say('动作5')
                self.animation.action5.start(self.animation.interval)
            if action == action_chat:
                self.chat()
            if action == action_save:
                os.startfile(os.path.join(self.abspath, "文件保存位置"))
            if action == action_music:
                self.sound.rand_music()
            if action == action_about:
                self.sound.say('开发者.mp3')
                subprocess.Popen(["notepad", os.path.join(self.abspath, "README.md")])
            if action == action_hide:
                self.sound.say('隐藏.mp3')
                self.hide()
            if action == action_set:
                self.open_setting()
            if action == action_source:
                self.get_source_info()
            if action == action_follow:
                self.animation.stop_all_animation()
                self.animation.follow.start(self.animation.interval)
                self.timer.following.start(self.animation.interval)
            if action == action_view:
                print(f'程序内存占用量为：{memory_usage():.2f}MB')

    def mouseMoveEvent(self, a0):
        '''重写鼠标移动事件，移动窗口'''
        if self.timer.sleeping:# 睡觉状态不响应移动
            return
        if a0.buttons() == Qt.LeftButton:# 鼠标左键移动过程中需要调用e.buttons()方法获取当前鼠标状态
            if abs(a0.x() - self.dx) > 5 or abs(a0.y() - self.dy) > 5: # 判断是否为轻微移动，设置一个阈值（如5像素），避免误判为拖动
                self.is_move = True
            else:
                return
            self.move(a0.globalX() - self.dx,a0.globalY() - self.dy)
            if self.dragging == True: # 一次移动导致事件重复触发时用于只执行一次该代码
                if random.randint(0,2) == 1:
                    self.sound.rand_say('拖动')
                self.animation.stop_all_animation()
                self.animation.drag.start(self.animation.interval)
                self.dragging = False
        
    def mousePressEvent(self, a0):
        '''鼠标点击窗口的事件 '''
        if self.timer.sleeping and a0.button() == Qt.LeftButton: # 睡觉状态不响应左键点击
            return 
        if a0.button() == Qt.LeftButton:
            self.dx = a0.x(); self.dy = a0.y() # 获取鼠标距离窗口位置，以便移动窗口            
            self.press_time = time.time() # 记录鼠标按下的时间
            self.dragging = True

    def mouseReleaseEvent(self, a0):
        '''鼠标释放事件'''
        if self.timer.sleeping: # 睡觉状态下禁用按键
            return 
        if a0.button() == Qt.LeftButton:  # 检查是否是左键释放
            elapsed = time.time()-self.press_time
            if elapsed < 0.2 and not self.is_move:  # 判断点击时间差是否小于0.2秒并且不是移动事件（点击事件）
                if a0.y() < self.height()/5*2: # 判断点击位置是否在窗口上方
                    if self.click_times >= 4: # 如果点击次数达到4次
                        self.sound.rand_say('点击次数过多')
                        self.click_times += 1
                    else:
                        self.sound.rand_say('点击其一')
                        self.click_times += 1 # 增加点击次数
                else: # 点击到下方位置
                    if self.click_times >= 4: # 如果点击次数达到4次
                        self.sound.rand_say('点击次数过多')
                        self.click_times += 1
                    else:
                        self.sound.rand_say('点击其二')
                        self.click_times += 1 # 增加点击次数
                self.timer.click_timer.start(10000) # 重置定时器
                return # 是点击事件，直接返回，不执行之后移动的指令
            elif not self.is_move: # 长按事件
                # 待开发……
                return # 是长按事件，直接返回，不执行之后移动的指令
            self.animation.stop_all_animation()
            self.animation.action1.start(self.animation.interval) # 恢复初始动作
            self.is_move = False
            if self.x() < int(-self.width()/5): # 如果拖动到左侧边界就切换图片
                self.animation.stop_all_animation()
                self.move(int(-self.width()/4), self.y())
                self.animation.show_img('hide')
                self.hiding = True
            elif self.x() > QApplication.desktop().availableGeometry(self).right()-self.width()+int(self.width()/5): # 右侧边界
                self.animation.stop_all_animation()
                self.move(QApplication.desktop().availableGeometry(self).right()-self.width()+int(self.width()/4), self.y())
                self.animation.show_img('hide', change=True) # 镜像翻转图片
                self.hiding = True
            elif self.y() < int(-self.height()/5): # 如果拖动到上边界就切换图片
                self.animation.stop_all_animation()
                self.move(self.x(), int(-self.height()/2.7))
                self.animation.show_img('hide2')
                self.hiding = True
            elif self.hiding == True: # 如果之前是躲藏状态，松开鼠标就恢复
                self.animation.action2.start(self.animation.interval)
                self.hiding = False
            
    def event(self, a0):
        '''监听所有用户操作事件，重置定时器'''
        if a0.type() in [QEvent.MouseButtonPress, QEvent.MouseMove, QEvent.KeyPress]:  # 鼠标/键盘/窗口相关事件
            self.timer.reset_idle_voice_timer()#产生事件时重设语音播放时间
            self.timer.last_activity_time = time.time()  # 更新活动时间
        return super().event(a0)
    
    def go_to_sleep(self):
        '''进入睡觉状态'''
        if self.timer.sleeping:
            return
        self.animation.stop_all_animation()
        self.animation.show_img('sleep') # 显示睡觉图片
        self.timer.sleeping = True
        self.setWindowFlag(Qt.WindowStaysOnTopHint, False) # 取消窗口置顶
        self.show() # 需要重新显示窗口使标志更改生效
        self.timer.idle_voice_timer.stop() # 停止语音定时器
        self.sound.rand_say('睡觉') # 播放睡觉语音
        # 释放部分内存占用
        gc.collect() # 主动进行垃圾回收
        try:
            if tracemalloc.is_tracing():
                tracemalloc.stop()
        except ImportError:
            pass

    def wake_up(self):
        '''唤醒桌宠'''
        self.timer.sleeping = False
        self.animation.stop_all_animation()
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True) # 恢复窗口置顶
        self.show() # 需要重新显示窗口使标志更改生效
        self.animation.action1.start(self.animation.interval) # 显示初始动作图片
        self.timer.idle_voice_timer.start(600000) # 重新启动语音定时器
        self.timer.last_activity_time = time.time() # 重置活动时间
        self.sound.rand_say('唤醒') # 播放唤醒语音

    def chat(self):
        '''打开聊天框'''
        self.sound.rand_say('打开聊天')
        if hasattr(self, 'api'):
            self.api.show()
            if self.api.isMinimized(): # 如果窗口最小化，则恢复正常
                self.api.showNormal()
            self.api.raise_() # 将窗口提到前台
            self.api.activateWindow() # 激活窗口
        else:
            self.api = ModelApi(self)
            self.api.show()

    def dragEnterEvent(self, a0):
        '''重写拖入文件事件'''
        if a0.mimeData().hasUrls() or a0.mimeData().hasText(): # 检查拖入的是否为文件/URL
            a0.acceptProposedAction() # 接受拖放操作
        else:
            a0.ignore() # 忽略非文件拖放
    
    def dropEvent(self, a0):
        '''放下文件进行上传'''
        if a0.mimeData().hasUrls(): # 获取文件地址并复制文件
            files = [url.toLocalFile() for url in a0.mimeData().urls()] # 获取所有文件路径
            for file_path in files:
                target_dir = os.path.join(self.abspath, "文件保存位置")
                os.makedirs(target_dir, exist_ok=True)
                filename = os.path.basename(file_path)
                target_path = os.path.join(target_dir, filename)
                try:
                    with open(file_path, "rb") as src, open(target_path, "wb") as dst:
                        dst.write(src.read()) # 执行上传操作
                    self.sound.rand_say('文件上传')
                except:
                    pass

        elif a0.mimeData().hasText(): # 获取文本内容并保存为文件
            text = a0.mimeData().text()
            target_dir = os.path.join(self.abspath, "文件保存位置")
            os.makedirs(target_dir, exist_ok=True)
            filename = f"text_{int(time.time())}.txt"
            target_path = os.path.join(target_dir, filename)
            try:
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(text) # 保存文本内容
                self.sound.rand_say('文件上传')
            except:
                pass

    def open_setting(self):
        '''打开个性化设置'''
        self.dialog.show()

    def get_source_info(self):
        '''获取电脑资源利用率'''
        cpu_usage = psutil.cpu_percent(interval=1)
        mem_usage = psutil.virtual_memory().percent
        gpus = GPUtil.getGPUs()
        gpu_usage = gpus[0].load * 100 if gpus else 0
        gpu_temper = gpus[0].temperature if gpus[0].temperature else 'NaN'
        net1 = psutil.net_io_counters()
        net2 = psutil.net_io_counters()
        upload_speed = (net2.bytes_sent - net1.bytes_sent) / 1024
        download_speed = (net2.bytes_recv - net1.bytes_recv) / 1024
        self.bubble(f'CPU利用率: {cpu_usage}%\n内存占用: {mem_usage}%\nGPU: {gpu_usage:.1f}%  温度：{gpu_temper}℃\n上行: {upload_speed:.1f}KB/s\n下行: {download_speed:.1f}KB/s')
        if type(gpu_temper) is float and gpu_temper > 90:
            self.sound.say('高温.mp3')
        elif cpu_usage > 70:
            self.sound.say('cpu利用率高.mp3')
        elif mem_usage > 80:
            self.sound.say('内存占用过高.mp3')
        elif gpu_usage > 80:
            self.sound.say('显卡利用率高.mp3')
        else:
            self.sound.say('合理.mp3')

    def exit(self):
        '''退出程序'''
        with open(os.path.join(self.abspath, '预设参数', '桌宠参数.json'),'w',encoding='utf-8') as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)
        QApplication.quit()

    def on_chat_window_closed(self):
        '''当聊天窗口关闭时释放资源'''
        if hasattr(self, 'api'):
            # 停止可能正在运行的线程
            if hasattr(self.api, 'worker') and self.api.worker and self.api.worker.isRunning():
                self.api.worker.terminate()
                self.api.worker.wait(1000) # 等待1秒
            try: # 断开所有信号连接
                if hasattr(self.api, 'worker'):
                    self.api.worker.finished.disconnect()
                    self.api.worker.error.disconnect()
            except:
                pass
            # 删除聊天窗口实例
            self.api.deleteLater()
            del self.api
            gc.collect() # 强制垃圾回收


if __name__ == "__main__": # 启动桌宠！
    app = QApplication(sys.argv)
    pet = MyQtDeskPet()
    pet.show()
    sys.exit(app.exec_())
