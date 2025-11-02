import os
from PyQt5.QtWidgets import (QFormLayout, QSpinBox, QPushButton, QComboBox, QDialog, 
                             QDialogButtonBox, QCheckBox, QHBoxLayout, QSlider, QLabel, QInputDialog)
from PyQt5.QtCore import Qt

class Personal_Settings(QDialog):
    '''个性化设置'''
    def __init__(self, main=None):
        super().__init__()
        self.main = main
        self.setWindowTitle("个性化设置")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)
        # 窗口大小设置
        self.size_spin = QSpinBox()
        self.size_spin.setRange(2, 10)
        self.size_spin.setValue(int(self.main.width()/100))
        layout.addRow("窗口大小：", self.size_spin)
        # 窗口主题切换
        self.combo_box = QComboBox()
        l = []
        for i in os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '预设参数')):
            if i.endswith('.qss'):
                l.append(i.split('.')[0])
        self.combo_box.addItems(l)
        self.combo_box.setCurrentText(self.main.data['style'])
        layout.addRow("主题颜色切换：", self.combo_box)
        # 图片切换速度设置
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(50, 1000)
        self.interval_spin.setSingleStep(50)
        self.interval_spin.setValue(self.main.animation.interval)
        layout.addRow("图片切换间隔(ms)：", self.interval_spin)
        # 移动速度大小设置
        self.speed_spin = QSpinBox()
        self.speed_spin.setRange(2, 50)
        self.speed_spin.setSingleStep(2)
        self.speed_spin.setValue(self.main.dv)
        layout.addRow("移动速度：", self.speed_spin)
        # 闹钟提醒开关
        self.alarm_checkbox = QCheckBox()
        self.alarm_checkbox.setText('是否启用闹钟')
        layout.addRow(self.alarm_checkbox)
        # 语音提醒时间设置
        self.voice_time_spin = QSpinBox()
        self.voice_time_spin.setRange(1, 999)
        self.voice_time_spin.setSingleStep(1)
        self.voice_time_spin.setValue(int(self.main.timer.clock_timer.interval()/1000/60) if self.main.timer.clock_timer.isActive() else 1)
        layout.addRow("闹钟提醒间隔(min)：", self.voice_time_spin)
        # 声音开关
        self.sound_checkbox = QCheckBox()
        self.sound_checkbox.setText('是否关闭声音')
        layout.addRow(self.sound_checkbox)
        # 保存按钮
        btn_save = QPushButton("保存设置")
        btn_save.clicked.connect(self.save_settings)
        layout.addRow(btn_save)

    def save_settings(self):
        '''应用设置到主窗口'''
        if self.main.data['size'] != self.size_spin.value(): # 设置窗口大小
            self.main.setFixedSize(self.size_spin.value()*100, int(self.size_spin.value()*4/3*100))
            self.main.animation.w = self.main.width()-100
            self.main.animation.h = self.main.height()-100
            self.main.data['size'] = self.size_spin.value()
        if self.main.data['style'] != self.combo_box.currentText(): # 设置窗口主题切换
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '预设参数', self.combo_box.currentText()+'.qss'),'r',encoding='utf-8') as f:
                self.main.theme = f.read()
            self.main.data['style'] = self.combo_box.currentText()
        if self.main.data['interval'] != self.interval_spin.value(): # 设置图片切换速度
            self.main.animation.interval = self.interval_spin.value()
            self.main.data['interval'] = self.main.animation.interval
        if self.main.data['dv'] != self.speed_spin.value(): # 设置移动速度
            self.main.dv = self.speed_spin.value()
            self.main.data['dv'] = self.main.dv
        if self.alarm_checkbox.isChecked(): # 设置语音提醒时间
            self.main.timer.set_clock(self.voice_time_spin.value())
        if self.main.sound.is_off != self.sound_checkbox.isChecked():
            self.main.sound.is_off = self.sound_checkbox.isChecked()
        self.accept()


class Model_Settings(QDialog):
    '''模型参数设置对话框'''
    def __init__(self, main=None):
        super().__init__(main)
        self.main = main
        self.setWindowTitle("参数设置")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | Qt.Tool)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QFormLayout()
        self.model_combo = QComboBox() # 模型选择
        self.model_combo.addItems(self.main.model['model_list'])# 默认模型选项
        self.model_combo.setCurrentText(self.main.data["model"])
        layout.addRow("模型:", self.model_combo)
        self.edit_models_btn = QPushButton("编辑模型选项")
        def edit_models():
            text, ok = QInputDialog.getText(self, "编辑模型选项", "用逗号分隔模型名：", text=",".join([self.model_combo.itemText(i) for i in range(self.model_combo.count())]))
            if ok:
                self.model_combo.clear()
                models = [m.strip() for m in text.split(",") if m.strip()]
                self.model_combo.addItems(models)
        self.edit_models_btn.clicked.connect(edit_models)
        layout.addRow(self.edit_models_btn)
        # 温度设置滑块
        self.temp_slider = QSlider(Qt.Horizontal)
        self.temp_slider.setRange(0, 200) # 0.0 ~ 2.0 映射为 0~200
        self.temp_slider.setValue(int(self.main.data["temperature"] * 100))
        self.temp_label = QLabel(f"{self.main.data['temperature']:.2f}")
        def update_temp_label(val):
            self.temp_label.setText(f"{val/100:.2f}")
        self.temp_slider.valueChanged.connect(update_temp_label)
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(self.temp_slider)
        temp_layout.addWidget(self.temp_label)
        layout.addRow("温度 (0-2):", temp_layout)
        # Top-p 设置滑块
        self.top_p_slider = QSlider(Qt.Horizontal)
        self.top_p_slider.setRange(0, 100) # 0.0 ~ 1.0 映射为 0~100
        self.top_p_slider.setValue(int(self.main.data["top_p"] * 100))
        self.top_p_label = QLabel(f"{self.main.data['top_p']:.2f}")
        def update_top_p_label(val):
            self.top_p_label.setText(f"{val/100:.2f}")
        self.top_p_slider.valueChanged.connect(update_top_p_label)
        top_p_layout = QHBoxLayout()
        top_p_layout.addWidget(self.top_p_slider)
        top_p_layout.addWidget(self.top_p_label)
        layout.addRow("Top-p (0-1):", top_p_layout)
        # 是否保存按钮
        self.save_button = QCheckBox('是否保存对话',self)
        layout.addRow(self.save_button)
        # 是否使用edge_tts合成
        self.tts_button = QCheckBox('是否使用语音合成（需要联网）',self)
        self.tts_button.setChecked(self.main.use_tts)
        layout.addRow(self.tts_button)
        # 确定和取消按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        self.setLayout(layout)

    def accept(self):
        '''保存设置'''
        self.main.data["model"] = self.model_combo.currentText()
        self.main.data["temperature"] = self.temp_slider.value()/100
        self.main.data["top_p"] = self.top_p_slider.value()/100
        self.main.model["use_model"] = self.model_combo.currentText()
        self.main.model["temperature"] = self.temp_slider.value()/100
        self.main.model["top_p"] = self.top_p_slider.value()/100
        if self.save_button.isChecked():
            self.main.is_save = True
        else:
            self.main.is_save = False
        if self.tts_button.isChecked():
            self.main.use_tts = True
        else:
            self.main.use_tts = False
        super().accept()
     