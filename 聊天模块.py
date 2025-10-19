import requests, json, os, emoji
import datetime as dt
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QLineEdit, QPushButton, QMessageBox, 
                            QDialog, QDialogButtonBox, QFormLayout, QComboBox, QCheckBox)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QSlider, QLabel, QInputDialog
from 音频模块 import Sound

class ChatWorker(QThread): # 聊天工作线程
    finished = pyqtSignal(str) # 用于传递回复的文本
    error = pyqtSignal(str) # 用于传递错误信息

    def __init__(self, data):
        super().__init__()
        self.data = data
        self.url = 'http://127.0.0.1:11434/api/chat' # 请求的api地址

    def run(self):
        '''利用requests库向模型发送post请求'''
        try:
            resp = requests.post(self.url, json=self.data)
            resp.raise_for_status()
            result = json.loads(resp.text)
            answer = result['message']['content']
            if answer.startswith('<think>'):
                answer = answer.split('</think>')[1].strip()
            self.finished.emit(answer)
        # 处理各个错误
        except requests.exceptions.HTTPError as http_err:
            self.error.emit(f"HTTP错误发生:{http_err}")
        except requests.exceptions.ConnectionError as conn_err:
            self.error.emit(f"连接错误发生:{conn_err}")
        except requests.exceptions.Timeout as timeout_err:
            self.error.emit(f"请求超时:{timeout_err}")
        except requests.exceptions.RequestException as req_err:
            self.error.emit(f"请求错误发生:{req_err}")
        except KeyError as key_err:
            self.error.emit(f"解析响应时发生键错误:{key_err}")
        except Exception as err:
            self.error.emit(f"其他错误发生:{err}")

class ModelApi(QWidget):
    '''大模型api调用'''
    def __init__(self, main=None):
        super().__init__()
        self.setAttribute(Qt.WA_QuitOnClose, False)
        self.main = main
        self.ui_init()
        self.sound = Sound()
        self.history = {}
        self.history['time'] = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S") # 打开程序的时间
        self.is_save = False
        self.use_tts = False
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '预设参数', '模型参数.json'), 'r', encoding='utf-8') as f:
            self.model = json.load(f)
        self.data = {
            "model":self.model['use_model'], # 调用的模型
            "messages":[{
                "role":"system",
                "content":'你是一只可爱的猫娘小桌宠，拥有橘色的毛发，绿色的眼睛，现在的你生活在主人的电脑中，你需要以猫娘的语言风格回复，字数限制在50字以内'
            }], # 系统提示词
            "stream":False, # 非流式回答
            "temperature": self.model['temperature'], # 温度
            "top_p": self.model['top_p'],
            "options": {"keep_alive": "10m"} # 控制模型在请求后保留在内存中的时间
        } # 发送请求的数据体
        self.worker = None # 初始ChatWorker对象
        # self.init_chatworker = ChatWorker(self.data)
        # self.init_chatworker.start() # 打开对话框时预加载模型
        self.dialog = SettingsDialog(self) # 参数设置对话框实例化

    def ui_init(self):
        self.setWindowTitle('聊天输入框')
        self.setFixedSize(600, 80) # 禁用窗口大小更改
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "images", "图标", "icon.png")))
        layout = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("请输入文本...")
        layout.addWidget(self.input)
        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self.run)
        layout.addWidget(self.send_button)
        self.set = QPushButton('设置',self)
        self.set.clicked.connect(self.open_setting)
        layout.addWidget(self.set)
        self.setLayout(layout)
        # 设置橙色主题样式
        self.setStyleSheet(self.main.theme)

    def keyPressEvent(self, a0):
        '''按回车键发送文本'''
        if a0.key() == Qt.Key_Return:
            self.send_button.click()

    def open_setting(self):
        '''打开模型参数设置框'''
        self.dialog.show()

    def run(self):
        '''启动工作线程'''
        user_input = self.input.text().strip()
        self.input.setText('')
        if not user_input:
            return
        # 禁用发送按钮防止重复点击
        self.send_button.setEnabled(False)
        self.data['messages'].append({"role":"user","content":user_input})
        # 创建并启动工作线程
        self.worker = ChatWorker(self.data)
        self.worker.finished.connect(self.on_chat_finished)
        self.worker.error.connect(self.on_chat_error)
        self.worker.start()

    def on_chat_finished(self, answer):
        '''在主线程中更新UI'''
        answer = answer.strip() # 删去首尾多余的换行符和空格
        self.main.bubble(answer) # 冒泡显示文本
        self.data['messages'].append({"role":"assistant","content":answer}) # 保存对话信息
        if self.use_tts: # 是否使用tts语音合成
            answer = emoji.replace_emoji(answer, replace='') # 删除表情包的转音
            self.sound.text_to_sound(answer)
        self.send_button.setEnabled(True) # 重新启用发送按钮

    def on_chat_error(self, error_msg):
        '''报错弹窗'''
        QMessageBox.critical(self, '错误', f"发生错误:{error_msg}")
        self.send_button.setEnabled(True) # 重新启用发送按钮

    def save(self):
        '''保存对话文件'''
        os.makedirs('历史对话',exist_ok=True)
        self.data['messages'].pop(0)
        self.history['message'] = self.data['messages']
        self.history['model'] = self.data['model']
        time_2 = dt.datetime.now().strftime("%Y-%m-%d-%H-%M-%S") # 保存程序的时间
        with open('历史对话/'+time_2+'.json','w',encoding='utf-8') as f: # 保存文件为json
            json.dump(self.history, f, indent=4, ensure_ascii=False)
        QMessageBox.information(self, '提示', f'成功保存到历史对话文件夹，文件名为{time_2}.json')

    def closeEvent(self, a0):
        if self.is_save:
            self.save()
        if self.main:
            self.main.t = None  # 重置标志位
        # a0.ignore() # 忽略关闭事件，防止应用程序退出
        # self.hide() # 隐藏窗口而不是关闭
        self.data["messages"] = [self.data["messages"].pop(0)] # 重置历史对话
        # 保存最新参数配置文件
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '预设参数', '模型参数.json'),'w', encoding='utf-8') as f:
            json.dump(self.model, f, indent=4, ensure_ascii=False)
        # 接受关闭事件
        a0.accept()
        # 通知主程序释放资源
        if self.main:
            self.main.on_chat_window_closed()
        
        
class SettingsDialog(QDialog):
    '''参数设置对话框'''
    def __init__(self, main=None):
        super().__init__(main)
        self.main = main
        self.setWindowTitle("参数设置")
        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | Qt.Tool)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QFormLayout()
        self.model_combo = QComboBox()# 模型选择
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
        