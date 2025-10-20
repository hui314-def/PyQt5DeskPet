import os
from PyQt5.QtGui import QPixmap, QTransform
from PyQt5.QtCore import Qt, QTimer

class Animation:
    def __init__(self, main_window, interval):
        self.main_window = main_window
        self.w = self.main_window.width() - 100 # 防止窗口装不下图片
        self.h = self.main_window.height() - 100
        image_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "图片")
        # 加载动画图片组
        self.animations = {
            'walk':    [os.path.join(image_folder, '走路', f'{n}.png')  for n in range(1, len(os.listdir(os.path.join(image_folder, '走路')))+1)],
            'action1': [os.path.join(image_folder, '动作1', f'{n}.png') for n in range(1, len(os.listdir(os.path.join(image_folder, '动作1')))+1)],
            'action2': [os.path.join(image_folder, '动作2', f'{n}.png') for n in range(1, len(os.listdir(os.path.join(image_folder, '动作2')))+1)],
            'action3': [os.path.join(image_folder, '动作3', f'{n}.png') for n in range(1, len(os.listdir(os.path.join(image_folder, '动作3')))+1)],
            'action4': [os.path.join(image_folder, '动作4', f'{n}.png') for n in range(1, len(os.listdir(os.path.join(image_folder, '动作4')))+1)],
            'action5': [os.path.join(image_folder, '动作5', f'{n}.png') for n in range(1, len(os.listdir(os.path.join(image_folder, '动作5')))+1)],
            'drag':    [os.path.join(image_folder, '拖动', f'{n}.png')  for n in range(1, len(os.listdir(os.path.join(image_folder, '拖动')))+1)],
            'follow':  [os.path.join(image_folder, '爬动', f'{n}.png')  for n in range(1, len(os.listdir(os.path.join(image_folder, '爬动')))+1)],
        }
        # 加载静态图片
        self.pictures = {
            'hide':    os.path.join(image_folder, '躲藏.png'),
            'goodbye': os.path.join(image_folder, '再见.png'),
            'sleep':   os.path.join(image_folder, '睡觉.png'),
        }
        # 动画索引映射
        self.animation_indexs = {
            'walk': 0, 'action1': 0, 'action2': 0, 'action3': 0, 'action4': 0, 'action5': 0, 'drag': 0, 'follow': 0,
        }
        self.animation_timers = {} # 动画到定时器的映射
        self.interval = interval # 初始动画图片间隔时长(ms)
        self.init_timers() # 初始化定时器
        self.animation_timers['action1'].start(self.interval) # 初始展示动作1动画
    
    def init_timers(self):
        '''初始化所有动画定时器'''
        for anim_name in self.animations.keys(): # 以字典键名为属性赋值
            timer = QTimer(self.main_window)
            timer.timeout.connect(lambda a=anim_name: self.show_timer_img(a))
            setattr(self, anim_name, timer) # 给对象属性赋值，类似于 self.anim_name = timer
            self.animation_timers[anim_name] = timer
    
    def show_timer_img(self, animation_name):
        '''统一的动画显示方法'''
        if animation_name not in self.animation_indexs:
            return
        # 获取当前动画的图片列表和索引
        image_list = self.animations[animation_name]
        current_index = self.animation_indexs[animation_name]

        pixmap = QPixmap(image_list[current_index]).scaled(self.w, self.h, Qt.KeepAspectRatio) # 加载并缩放图片
        if animation_name == 'walk' and self.main_window.walk_change: # 行走动画需要根据方向翻转
            transform = QTransform().scale(-1, 1)
            pixmap = pixmap.transformed(transform)
        if animation_name == 'follow' and self.main_window.follow_change: # 爬行动画需要根据方向翻转
            transform = QTransform().scale(-1, 1)
            pixmap = pixmap.transformed(transform)
        self.animation_indexs[animation_name] = (current_index + 1) % len(image_list) # 循环更新索引
        self.main_window.label.setPixmap(pixmap)
    
    def show_img(self, animation_name, change=False):
        '''显示静态图片'''
        if animation_name not in self.pictures:
            return
        image_path = self.pictures[animation_name]
        pixmap = QPixmap(image_path).scaled(self.w, self.h, Qt.KeepAspectRatio)
        
        if animation_name == 'hide' and change: # 躲藏图片可能需要翻转
            transform = QTransform().scale(-1, 1)
            pixmap = pixmap.transformed(transform)
        self.main_window.label.setPixmap(pixmap)
    
    def stop_all_animation(self):
        '''停止所有动画'''
        if self.main_window.timer.movement.isActive(): # 停止移动定时器
            self.main_window.timer.movement.stop()
        if self.main_window.timer.following.isActive(): # 停止跟随定时器
            self.main_window.timer.following.stop()
        for timer in self.animation_timers.values(): # 停止所有动画定时器
            if timer.isActive():
                timer.stop()
