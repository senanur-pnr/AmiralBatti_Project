import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Amiral Battı - Giriş")
        self.layout = QVBoxLayout()

        self.layout.addWidget(QLabel("Kullanıcı Adı:"))
        self.username_input = QLineEdit()
        self.layout.addWidget(self.username_input)

        self.layout.addWidget(QLabel("Sunucu IP (AWS):"))
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Örn: 127.0.0.1")
        self.layout.addWidget(self.ip_input)

        self.login_button = QPushButton("Oyuna Bağlan")
        self.login_button.clicked.connect(self.handle_login)
        self.layout.addWidget(self.login_button)

        self.setLayout(self.layout)

    def handle_login(self):
        username = self.username_input.text()
        ip = self.ip_input.text()
        
        if username and ip:
            try:
                from network import Network
                from setup_window import SetupWindow
                
                self.network = Network(ip)
                if self.network.id:
                    self.setup_win = SetupWindow(self.network, username)
                    self.setup_win.show()
                    self.close()
                else:
                    QMessageBox.critical(self, "Hata", "Sunucuya bağlanılamadı!")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Bağlantı kurulamadı: {e}")
        else:
            QMessageBox.warning(self, "Hata", "Lütfen tüm alanları doldurun!")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())