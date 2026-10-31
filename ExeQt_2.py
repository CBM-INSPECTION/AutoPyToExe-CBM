# -*- coding: utf-8 -*-
"""
Created on Tue Oct 27 16:30:12 2026

@author: Sadjad
"""


# -*- coding: utf-8 -*-
import sys
import os
import subprocess
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QLineEdit, 
                             QRadioButton, QButtonGroup, QFileDialog, 
                             QTextEdit, QCheckBox, QGroupBox, QMessageBox, QProgressBar, QSplashScreen)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QColor


# --- کلاس Thread برای اجرای PyInstaller بدون فریز شدن UI ---
class ConvertThread(QThread):
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool)

    def __init__(self, command, working_dir):
        super().__init__()
        self.command = command
        self.working_dir = working_dir

    def run(self):
        try:
            env = os.environ.copy()
            conda_path = r"C:\Users\User\anaconda3\envs\Youre_enviroment"
            env["CONDA_PREFIX"] = conda_path
            env["CONDA_DEFAULT_ENV"] = "Youre_enviroment"
            env["PATH"] = f"{conda_path};{conda_path}\\Library\\mingw-w64\\bin;{conda_path}\\Library\\usr\\bin;{conda_path}\\Library\\bin;{conda_path}\\Scripts;" + env.get("PATH", "")

            process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                shell=True,
                cwd=self.working_dir,
                env=env
            )
            
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.output_signal.emit(output.strip())
            
            if process.returncode == 0:
                self.finished_signal.emit(True)
            else:
                self.finished_signal.emit(False)
                
        except Exception as e:
            self.output_signal.emit(f"Error: {str(e)}")
            self.finished_signal.emit(False)


class PyToExeConverter(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto Py to Exe - CBM Version")
        self.setGeometry(600, 170, 700, 850)
        
        icon_file = "CBM Cyber Circuit Emblem.ico"
        if os.path.exists(icon_file):
            self.setWindowIcon(QIcon(icon_file))

        self.setStyleSheet("""
            QMainWindow { background-color: #2b2b2b; color: white; }
            QLabel { color: white; font-size: 14px; }
            QLineEdit { background-color: #3c3f41; color: white; border: 1px solid #555; padding: 5px; border-radius: 3px; }
            QPushButton { background-color: #007acc; color: white; border: none; padding: 8px 15px; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #005999; }
            QPushButton:disabled { background-color: #555; color: #aaa; }
            QRadioButton { color: white; font-size: 14px; }
            QCheckBox { color: white; font-size: 14px; }
            QGroupBox { border: 1px solid #555; border-radius: 5px; margin-top: 15px; color: white; }
            QGroupBox::title { subcontrol-origin: margin; subcontrol-position: top left; padding: 0 5px; }
            QTextEdit { background-color: #1e1e1e; color: #ffcc00; font-family: Consolas; font-size: 12px; border: 1px solid #555; }
            QProgressBar { border: 1px solid #555; border-radius: 5px; text-align: center; color: white; }
            QProgressBar::chunk { background-color: #007acc; }
        """)

        self.script_path = ""
        self.icon_path = ""
        self.conversion_successful = False

        self.init_ui()
        self.update_command()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # 1. Script Location
        script_layout = QHBoxLayout()
        script_layout.addWidget(QLabel("Script Location:"))
        self.script_input = QLineEdit()
        self.script_input.setPlaceholderText("Path to .py file")
        self.script_input.setReadOnly(True)
        script_layout.addWidget(self.script_input)
        
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_script)
        script_layout.addWidget(browse_btn)
        layout.addLayout(script_layout)

        # 2. Onefile / Onedirectory
        mode_group = QGroupBox("Onefile (-onedir / -onefile)")
        mode_layout = QHBoxLayout()
        self.radio_onefile = QRadioButton("One File")
        self.radio_onedir = QRadioButton("One Directory")
        self.radio_onefile.setChecked(True)
        
        mode_btn_group = QButtonGroup(self)
        mode_btn_group.addButton(self.radio_onefile)
        mode_btn_group.addButton(self.radio_onedir)
        mode_btn_group.buttonClicked.connect(self.update_command)
        
        mode_layout.addWidget(self.radio_onefile)
        mode_layout.addWidget(self.radio_onedir)
        mode_layout.addStretch()
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # 3. Console Window
        console_group = QGroupBox("Console Window (-console / -windowed)")
        console_layout = QHBoxLayout()
        self.radio_console = QRadioButton("Console Based")
        self.radio_windowed = QRadioButton("Window Based (hide the console)")
        self.radio_windowed.setChecked(True)
        
        console_btn_group = QButtonGroup(self)
        console_btn_group.addButton(self.radio_console)
        console_btn_group.addButton(self.radio_windowed)
        console_btn_group.buttonClicked.connect(self.update_command)
        
        console_layout.addWidget(self.radio_console)
        console_layout.addWidget(self.radio_windowed)
        console_layout.addStretch()
        console_group.setLayout(console_layout)
        layout.addWidget(console_group)

        # 4. Icon Selection
        icon_layout = QHBoxLayout()
        self.icon_checkbox = QCheckBox("Icon (-icon)")
        self.icon_checkbox.stateChanged.connect(self.toggle_icon)
        icon_layout.addWidget(self.icon_checkbox)

        self.icon_input = QLineEdit()
        self.icon_input.setPlaceholderText("Path to .ico file")
        self.icon_input.setReadOnly(True)
        self.icon_input.setEnabled(False)
        icon_layout.addWidget(self.icon_input)

        icon_btn = QPushButton("Browse Icon")
        icon_btn.setEnabled(False)
        icon_btn.clicked.connect(self.browse_icon)
        self.icon_btn = icon_btn
        icon_layout.addWidget(icon_btn)
        layout.addLayout(icon_layout)

        # 5. Editable Command Display (قابل ویرایش)
        layout.addWidget(QLabel("Final Command (Editable):"))
        self.command_display = QLineEdit()
        self.command_display.setStyleSheet("background-color: #1e1e1e; color: #ffcc00; font-family: Consolas; font-size: 13px; padding: 5px;")
        # اینجا دیگر ReadOnly نیست تا کاربر بتواند تغییر دهد
        layout.addWidget(self.command_display)

        # دکمه ریست دستور به حالت پیش‌فرض
        self.reset_cmd_btn = QPushButton("↺ Reset Command to Default")
        self.reset_cmd_btn.setStyleSheet("background-color: #555; font-size: 12px; padding: 5px;")
        self.reset_cmd_btn.clicked.connect(self.update_command)
        layout.addWidget(self.reset_cmd_btn)

        # 6. Convert Button
        self.convert_btn = QPushButton("CONVERT .PY TO .EXE")
        self.convert_btn.setStyleSheet("background-color: #005999; font-size: 16px; padding: 12px;")
        self.convert_btn.clicked.connect(self.start_conversion)
        layout.addWidget(self.convert_btn)

        # 7. Open Output Folder Button
        self.open_folder_btn = QPushButton("📂 Open Output Folder (dist)")
        self.open_folder_btn.setStyleSheet("background-color: #4a4a4a; font-size: 14px; padding: 10px;")
        self.open_folder_btn.clicked.connect(self.open_output_folder)
        self.open_folder_btn.setEnabled(False)
        layout.addWidget(self.open_folder_btn)

        # 8. Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # 9. Output Log
        layout.addWidget(QLabel("Output Log:"))
        self.output_log = QTextEdit()
        self.output_log.setReadOnly(True)
        layout.addWidget(self.output_log)

    def browse_script(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Python Script", "", "Python Files (*.py)")
        if file:
            self.script_path = file
            self.script_input.setText(file)
            self.update_command()

    def toggle_icon(self):
        state = self.icon_checkbox.isChecked()
        self.icon_input.setEnabled(state)
        self.icon_btn.setEnabled(state)
        if not state:
            self.icon_input.clear()
            self.icon_path = ""
        self.update_command()

    def browse_icon(self):
        file, _ = QFileDialog.getOpenFileName(self, "Select Icon", "", "Icon Files (*.ico)")
        if file:
            self.icon_path = file
            self.icon_input.setText(file)
            self.update_command()

    def update_command(self):
        # دستور پایه با استفاده از پایتون محیط مجازی
        cmd = r'"C:\Users\User\anaconda3\envs\Youre_enviroment\python.exe" -m PyInstaller --noconfirm'
        
        if self.radio_onefile.isChecked():
            cmd += " --onefile"
        else:
            cmd += " --onedir"

        if self.radio_windowed.isChecked():
            cmd += " --windowed"
        else:
            cmd += " --console"

        if self.icon_checkbox.isChecked() and self.icon_path:
            cmd += f' --icon="{self.icon_path}"'
            
            # --- این خط را اضافه کنید ---
        cmd += " --exclude-module PySide6"
        # -----------------------------

        if self.script_path:
            cmd += f' "{self.script_path}"'
        else:
            cmd += ' ""'

        # فقط اگر کاربر روی Reset کلیک کرده یا تغییرات دستی نداشته باشد، به روزرسانی می‌شود
        self.command_display.setText(cmd)

    def start_conversion(self):
        if not self.script_path:
            msg = QMessageBox(self)
            msg.setStyleSheet("QLabel { color: black; } QPushButton { color: black; background-color: #ddd; }")
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Error")
            msg.setText("Please select a Python script first!")
            msg.exec_()
            return

        # خواندن دستور از فیلد قابل ویرایش
        command = self.command_display.text().strip()
        if not command:
            msg = QMessageBox(self)
            msg.setStyleSheet("QLabel { color: black; } QPushButton { color: black; background-color: #ddd; }")
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Error")
            msg.setText("Command is empty! Please write a command.")
            msg.exec_()
            return

        working_dir = os.path.dirname(self.script_path)
        
        self.output_log.clear()
        self.output_log.append(f"Executing: {command}\n")
        self.output_log.append(f"Working Directory: {working_dir}\n")
        
        self.convert_btn.setEnabled(False)
        self.open_folder_btn.setEnabled(False)
        self.conversion_successful = False
        self.progress_bar.setRange(0, 0)

        self.thread = ConvertThread(command, working_dir)
        self.thread.output_signal.connect(self.append_output)
        self.thread.finished_signal.connect(self.conversion_finished)
        self.thread.start()

    def append_output(self, text):
        self.output_log.append(text)
        self.output_log.verticalScrollBar().setValue(self.output_log.verticalScrollBar().maximum())

    def conversion_finished(self, success):
        self.progress_bar.setRange(0, 1)
        self.convert_btn.setEnabled(True)
        msg_style = "QLabel { color: black; } QPushButton { color: black; background-color: #ddd; }"
        
        if success:
            self.progress_bar.setValue(1)
            self.conversion_successful = True
            self.open_folder_btn.setEnabled(True)
            self.output_log.append("\n✅ Conversion Completed Successfully!")
            
            msg = QMessageBox(self)
            msg.setStyleSheet(msg_style)
            msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Success")
            msg.setText("Executable created successfully in 'dist' folder.")
            msg.exec_()
        else:
            self.progress_bar.setValue(0)
            self.output_log.append("\n❌ Conversion Failed. Check the log above.")
            
            msg = QMessageBox(self)
            msg.setStyleSheet(msg_style)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Error")
            msg.setText("Conversion failed. Please check the output log.")
            msg.exec_()

    def open_output_folder(self):
        if self.script_path:
            dist_path = os.path.join(os.path.dirname(self.script_path), "dist")
        else:
            dist_path = os.path.join(os.getcwd(), "dist")
            
        if os.path.exists(dist_path):
            if sys.platform == "win32":
                os.startfile(dist_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", dist_path])
            else:
                subprocess.Popen(["xdg-open", dist_path])
        else:
            msg = QMessageBox(self)
            msg.setStyleSheet("QLabel { color: black; } QPushButton { color: black; background-color: #ddd; }")
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Not Found")
            msg.setText(f"Output folder 'dist' not found at:\n{dist_path}")
            msg.exec_()


class SplashScreen(QSplashScreen):
    def __init__(self, image_path="Splash_2.png"):
        pixmap = QPixmap(image_path)
        
        if pixmap.isNull():
            pixmap = QPixmap(300, 150)
            pixmap.fill(QColor("#2b2b2b"))
            painter = QPainter(pixmap)
            painter.setPen(QColor("white"))
            painter.setFont(QFont("Arial", 24, QFont.Bold))
            painter.drawText(pixmap.rect(), Qt.AlignCenter, "Auto Py to Exe")
            painter.end()
        
        super().__init__(pixmap)
        
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.FramelessWindowHint)
        
        self.base_pixmap = pixmap.copy()
        
        self.progress = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(30)
        
        self.redraw()
    
    def redraw(self):
        pixmap = self.base_pixmap.copy()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = pixmap.width()
        height = pixmap.height()
        
        bar_y = height - 40
        text_y = bar_y - 15
        
        # --- رسم متن بالای نوار ---
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Arial", 14, QFont.Bold))
        painter.drawText(0, 0, width, text_y, Qt.AlignHCenter | Qt.AlignBottom, "Auto Py to Exe")
        
        painter.setPen(QColor("#aaaaaa"))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(0, 0, width, text_y + 20, Qt.AlignHCenter | Qt.AlignTop, "Version 1.0")
        
        # --- رسم نوار پیشرفت ---
        bar_rect = pixmap.rect().adjusted(50, -40, -50, -25)
        bar_rect.setTop(height - 40)
        bar_rect.setBottom(height - 25)
        bar_rect.setLeft(50)
        bar_rect.setRight(width - 50)
        
        painter.setBrush(QColor("#1e1e1e"))
        painter.setPen(QColor("#555555"))
        painter.drawRoundedRect(bar_rect, 5, 5)
        
        if self.progress > 0:
            progress_rect = bar_rect.adjusted(2, 2, -2, -2)
            progress_rect.setWidth(int(progress_rect.width() * self.progress / 100))
            painter.setBrush(QColor("#007acc"))
            painter.setPen(Qt.NoPen)
            painter.drawRoundedRect(progress_rect, 3, 3)
        
        # --- رسم متن Loading در زیر نوار ---
        painter.setPen(QColor("#ffcc00"))
        painter.setFont(QFont("Arial", 9, QFont.StyleItalic))
        painter.drawText(0, bar_rect.bottom() + 5, width, 20, Qt.AlignHCenter | Qt.AlignTop, "Loading...")
        
        painter.end()
        self.setPixmap(pixmap)
    
    def update_progress(self):
        self.progress += 2
        if self.progress > 100:
            self.progress = 100
        
        self.redraw()
        
        if self.progress >= 100:
            self.timer.stop()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    splash = SplashScreen("Splash_2.png")
    splash.show()
    app.processEvents()
    
    window = PyToExeConverter()
    
    def close_splash():
        splash.finish(window)
        window.show()
    
    QTimer.singleShot(3000, close_splash)
    
    sys.exit(app.exec_())
