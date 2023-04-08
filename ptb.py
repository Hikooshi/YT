from pytube import YouTube
import os, sys, time
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import requests
from ffmpeg_progress_yield import FfmpegProgress
from subprocess import CREATE_NO_WINDOW

class Main(QWidget):
    def __init__(self):
        super().__init__()
        vbox = QVBoxLayout(self)
        self.textEdit = QLineEdit()
        self.textEdit.setPlaceholderText("Введите адрес видео")
        self.bFind = QPushButton("Найти")
        self.bFind.clicked.connect(self.getVideo)
        hbox = QHBoxLayout()
        hbox.addWidget(self.textEdit)
        hbox.addWidget(self.bFind)
        vbox.addLayout(hbox)
        self.bDownload = QPushButton("Загрузить")
        self.bDownload.setDisabled(True)
        self.bDownload.clicked.connect(self.download)
        self.label = QLabel("Здесь будет предпросмотр")
        self.label.setFixedSize(213, 160)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFrameStyle(3)
        self.lAuthor = QLabel("Автор:")
        self.lAuthor.setFont(QFont("Times", 12, QFont.Bold))
        self.lAuthorText = QLabel()
        self.lName = QLabel("Название:")
        self.lName.setFont(QFont("Times", 12, QFont.Bold))
        self.lNameText = QLabel()
        vbox1 = QVBoxLayout()
        vbox1.addWidget(self.lAuthor)
        vbox1.addWidget(self.lAuthorText)
        vbox1.addWidget(self.lName)
        vbox1.addWidget(self.lNameText)
        hbox2 = QHBoxLayout()
        hbox2.setAlignment(Qt.AlignLeft)
        hbox2.addWidget(self.label)
        hbox2.addLayout(vbox1)
        vbox.addLayout(hbox2)
        self.pathText = QLineEdit()
        self.pathText.setPlaceholderText("Путь до результирующего файла")
        self.bPath = QPushButton("Указать")
        self.bPath.clicked.connect(self.getDirectory)
        self.progressBar = QProgressBar()
        self.progressBar.setRange(0, 100)
        self.rbOneFile = QRadioButton("Одним файлом")
        self.rbOneFile.setChecked(True)
        self.rbTwoFiles = QRadioButton("Видео и аудио двумя файлами")
        self.rbOnlyVideo = QRadioButton("Только видео")
        self.rbOnlyAudio = QRadioButton("Только аудио")
        self.bGroup = QButtonGroup()
        self.bGroup.addButton(self.rbOneFile, 0)
        self.bGroup.addButton(self.rbTwoFiles, 1)
        self.bGroup.addButton(self.rbOnlyVideo, 2)
        self.bGroup.addButton(self.rbOnlyAudio, 3)
        self.bGroup.buttonClicked[int].connect(self.setDownloadMtd)
        saveGroup = QGroupBox("Сохранение")
        vboxSG = QVBoxLayout(saveGroup)
        vboxSG.addWidget(self.rbOneFile)
        vboxSG.addWidget(self.rbTwoFiles)
        vboxSG.addWidget(self.rbOnlyVideo)
        vboxSG.addWidget(self.rbOnlyAudio)
        self.lVideo = QLabel("Разрешение видео:")
        self.vBox = QComboBox()
        self.lAudio = QLabel("Битрейт аудио:")
        self.aBox = QComboBox()
        qualityGroup = QGroupBox("Качество")
        vboxQG = QVBoxLayout(qualityGroup)
        vboxQG.addWidget(self.lVideo)
        vboxQG.addWidget(self.vBox)
        vboxQG.addWidget(self.lAudio)
        vboxQG.addWidget(self.aBox)
        hboxSnQ = QHBoxLayout()
        hboxSnQ.addWidget(saveGroup)
        hboxSnQ.addSpacing(64)
        hboxSnQ.addWidget(qualityGroup)
        vbox.addLayout(hboxSnQ)
        hbox4 = QHBoxLayout()
        hbox4.addWidget(self.pathText)
        hbox4.addWidget(self.bPath)
        hbox4.addWidget(self.bDownload)
        vbox.addLayout(hbox4)
        self.progressLabel = QLabel()
        vbox.addWidget(self.progressLabel)
        vbox.addWidget(self.progressBar)
        self.videos = []
        self.audios = []
        self.toDownload = (True, True, True)
        self.downloadMtd = ((True, True, True), (True, True, False), (True, False, False), (False, True, False))

    def getVideo(self):
        videoUrl = self.textEdit.text()
        try:
            self.yt = YouTube(videoUrl, on_progress_callback=self.downloadingProgress)
            self.setCursor(Qt.CursorShape.BusyCursor)
            tnlUrl = self.yt.thumbnail_url
            data = requests.get(tnlUrl).content
            pixmap = QPixmap()
            pixmap.loadFromData(data)
            pixmap = pixmap.scaledToHeight(160)
            self.label.setPixmap(pixmap)
            author = self.yt.author
            title = self.yt.title
            self.lAuthorText.setText(author)
            self.lNameText.setText(title)
            lst = self.yt.streams.filter(adaptive=True)
            for i in lst:
                if i.type == "video":
                    resolution = i.resolution + str(i.fps)
                    self.videos.append(int(i.itag))
                    self.vBox.addItem(resolution)
                elif i.type == "audio":
                    bitrate = i.abr
                    self.audios.append(int(i.itag))
                    self.aBox.addItem(bitrate)
            self.setCursor(Qt.CursorShape.ArrowCursor)
        except:
            message = QMessageBox()
            message.setText("Адрес введен неверно")
            message.exec()

    def getDirectory(self):
        fd = QFileDialog()
        fd.setFileMode(QFileDialog.ExistingFile)
        self.path, _ = fd.getSaveFileName(self, "Сохранить файл", "", "mp4, mp3 (*.mp4 *.mp3)")
        self.fInfo = QFileInfo(self.path)
        self.pathText.setText(self.fInfo.filePath())
        if self.pathText.text() != "":
            self.bDownload.setDisabled(False)
        else:
            self.bDownload.setDisabled(True)

    def download(self):
        vTag = self.videos[self.vBox.currentIndex()]
        aTag = self.audios[self.aBox.currentIndex()]
        name = self.fInfo.fileName()
        path = self.fInfo.path()
        vName = name.split(".")[0] + ".mp4"
        vNameTemp = name.split(".")[0] + "temp.mp4"
        aName = name.split(".")[0] + ".mp3"
        self.outputPath = path + "/" + vNameTemp
        self.progressLabel.setText("Скачивание файлов")
        if self.toDownload[0]:
            vStream = self.yt.streams.filter(adaptive=True).get_by_itag(vTag)
            self.dataSize = vStream.filesize
            self.vTempName = vStream.download(output_path=path, filename=vName)
            self.vTempName = self.vTempName.replace("\\", "/")
            self.progressBar.setValue(0)
            time.sleep(0.1)
        if self.toDownload[1]:
            aStream = self.yt.streams.filter(adaptive=True).get_by_itag(aTag)
            self.dataSize = aStream.filesize
            self.aTempName = aStream.download(output_path=path, filename=aName)
            self.aTempName = self.aTempName.replace("\\", "/")
            self.progressBar.setValue(0)
            time.sleep(0.1)
        if self.toDownload[2]:
            time.sleep(0.5)
            self.progressLabel.setText("Объединение видео и аудио в один файл")
            cmd = f"ffmpeg\\bin\\ffmpeg.exe -i {self.vTempName} -i {self.aTempName} -c:v copy {self.outputPath}"
            ff = FfmpegProgress(cmd.split())
            for progress in ff.run_command_with_progress({"creationflags": CREATE_NO_WINDOW}):
                self.progressBar.setValue(progress)
            os.remove(self.vTempName)
            os.remove(self.aTempName)
            os.rename(self.outputPath, path + "/" + vName)
        doneMessage = QMessageBox()
        doneMessage.setText("Сохранение выполено")
        doneMessage.exec()

    def downloadingProgress(self, chunk, fileHandle, remainingBytes):
        percent = ((self.dataSize - remainingBytes) / self.dataSize) * 100
        self.progressBar.setValue(int(percent))

    def setDownloadMtd(self, int):
        self.toDownload = self.downloadMtd[int]




if __name__ == "__main__":
    app = QApplication([])
    window = Main()
    window.setMinimumWidth(720)
    window.show()

    sys.exit(app.exec_())