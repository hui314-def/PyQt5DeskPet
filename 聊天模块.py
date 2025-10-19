import requests, json, os, emoji
import datetime as dt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QIcon
from 音频模块 import Sound
from 设置模块 import SettingsDialog

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
        self.abspath = os.path.dirname(os.path.abspath(__file__))
        self.ui_init()
        self.sound = Sound()
        self.history = {}
        self.history['time'] = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S") # 打开程序的时间
        self.is_save = False
        self.use_tts = False
        with open(os.path.join(self.abspath, '预设参数', '模型参数.json'), 'r', encoding='utf-8') as f:
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
        # self.init_chatworker.start() # 打开对话框时预加载模型减少初次等待时间
        self.dialog = SettingsDialog(self) # 参数设置对话框实例化

    def ui_init(self):
        self.setWindowTitle('聊天输入框')
        self.setFixedSize(600, 80) # 禁用窗口大小更改
        self.setWindowIcon(QIcon(os.path.join(self.abspath, "images", "图标", "icon.png")))
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
        self.data["messages"] = [self.data["messages"].pop(0)] # 重置历史对话
        # 保存最新参数配置文件
        with open(os.path.join(self.abspath, '预设参数', '模型参数.json'),'w', encoding='utf-8') as f:
            json.dump(self.model, f, indent=4, ensure_ascii=False)
        # 接受关闭事件
        a0.accept()
        # 通知主程序释放资源
        if self.main:
            self.main.on_chat_window_closed()
