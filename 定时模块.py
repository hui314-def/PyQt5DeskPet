from PyQt5.QtCore import QTimer
import time
from 音频模块 import Sound

class Timer:
    def __init__(self, main_window=None):
        self.main_window = main_window
        self.sleeping = False # 是否处于睡觉状态
        self.last_activity_time = time.time()  # 记录开始的活动时间，用于检测是否不在线
        self.usage_start_time = time.time()  # 记录开始使用电脑的时间，用于检测是否长时间使用

        self.sound = Sound() # 实例化音频类
        self.idle_voice_timer = QTimer() # 定时语音设置
        self.idle_voice_timer.timeout.connect(lambda: self.sound.rand_say('长时间未操作'))
        self.idle_voice_timer.start(600000) # 每隔10分钟钟播放不在线语音

        self.sleep_timer = QTimer()  # 睡觉检测定时器
        self.sleep_timer.timeout.connect(self.check_idle_and_sleep)
        self.sleep_timer.start(600000)  # 每10分钟检查一次是否进入睡觉状态
        
        self.usage_timer = QTimer()  # 使用时间检测定时器
        self.usage_timer.timeout.connect(self.check_usage_time)
        self.usage_timer.start(1200000)  # 每20分钟检查一次使用时间

        self.movement = QTimer()
        self.movement.timeout.connect(self.main_window.move_window)

        self.following = QTimer()
        self.following.timeout.connect(self.main_window.follow)

        self.click_timer = QTimer()  # 连续点击检测定时器
        self.click_timer.timeout.connect(self.check_click_time)
        
        self.clock_timer = QTimer() # 闹钟定时器
        self.clock_times = 60000 # 默认时长为1min
        self.clock_timer.timeout.connect(self.clock)

    def check_click_time(self):
        '''关闭连续点击定时器'''
        if self.main_window.click_times > 0:
            self.main_window.click_times = 0
            self.click_timer.stop()

    def reset_idle_voice_timer(self, interval=600000):
        '''重设语音播放时间'''
        if not self.sleeping:
            self.idle_voice_timer.stop()
            self.idle_voice_timer.start(interval)

    def check_idle_and_sleep(self):
        '''检查是否长时间未活动（20分钟）'''
        if time.time() - self.last_activity_time > 1200 and not self.sleeping:
            self.main_window.go_to_sleep()

    def check_usage_time(self):
        '''检查使用电脑时间'''
        if self.sleeping: # 睡觉状态下不检查
            return
        usage_hours = (time.time() - self.usage_start_time) / 3600 # 计算使用时间（小时）
        if usage_hours >= 1:# 如果使用时间超过1小时
            self.sound.rand_say('长时间使用提醒')
            self.usage_start_time = time.time() # 重置使用时间

    def set_clock(self, clock_times=1):
        '''参数单位为min'''
        self.clock_times = clock_times * 60000
        self.clock_timer.start(self.clock_times)

    def clock(self):
        '''闹钟提醒'''
        self.clock_timer.stop()
        self.main_window.bubble('叮咚！叮咚！主人设置的闹钟响起来了哦！⏰')
        self.sound.say('闹钟提醒.mp3')
