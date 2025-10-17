import os, random, subprocess, edge_tts, asyncio
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, QThread, pyqtSignal

class TTSWorker(QThread):
    finished = pyqtSignal(str) # 传递生成的音频文件路径

    def __init__(self, text, num, parent=None):
        super().__init__(parent)
        self.text = text
        self.num = num

    def run(self):
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sound', '历史音频合成', f"chat_{self.num}.mp3")
        asyncio.run(self.amain(self.text, file_path))
        self.finished.emit(file_path)

    async def amain(self, text, file_path):
        communicate = edge_tts.Communicate(text, "zh-CN-XiaoyiNeural")
        await communicate.save(file_path)

class Sound:
    def __init__(self):
        self.abspath = os.path.dirname(os.path.abspath(__file__))
        self.player = QMediaPlayer() # 音乐实例化
        self.num = 0
        self.tts_worker = None
        self.is_off = False # 关闭音频
        self.max_audio_files = 30  # 最大保存的音频文件数

    def rand_say(self,dir):
        '''文件夹内随机语音播放'''
        if self.is_off:
            return
        path = os.path.join(self.abspath, "sound", dir) # 调用语音文件夹
        try:
            choices = os.listdir(path)
            n = random.randint(0, len(choices) - 1)
            file_path = os.path.join(path, choices[n])
            url = QUrl.fromLocalFile(file_path)
            self.player.setMedia(QMediaContent(url))
            self.player.play()
        except:
            print('文件不存在！语音播放失败')

    def say(self,filename):
        '''sound文件夹内指定语音播放'''
        if self.is_off:
            return
        file_path = os.path.join(self.abspath, "sound", filename)
        try:
            url = QUrl.fromLocalFile(file_path)
            self.player.setMedia(QMediaContent(url))
            self.player.play()
        except:
            print('文件不存在！语音播放失败')

    def rand_music(self):
        '''播放随机音乐'''
        music_dir = os.path.join(self.abspath, "sound", "音乐")
        try:
            choices = os.listdir(music_dir)
            n = random.randint(0, len(choices) - 1)
            file_path = os.path.join(music_dir, choices[n])
            subprocess.Popen(['start', '', file_path], shell=True)
        except:
            print('文件不存在！音乐播放失败')

    def text_to_sound(self,text):
        '''启动文本转语音线程'''
        if self.is_off:
            return
        self.tts_worker = TTSWorker(text, self.num)
        self.tts_worker.finished.connect(self.on_tts_finished)
        self.tts_worker.start()

    def on_tts_finished(self, file_path):
        '''转化完成后播放'''
        try:
            url = QUrl.fromLocalFile(file_path)
            self.player.setMedia(QMediaContent(url))
            self.player.play()
            self.num += 1
        except Exception as e:
            print(f"播放失败: {e}")
