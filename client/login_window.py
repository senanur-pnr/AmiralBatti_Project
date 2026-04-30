from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Amiral Battı - Giriş")
        self.layout = QVBoxLayout()

        # Kullanıcı Adı
        self.layout.addWidget(QLabel("Kullanıcı Adı:"))
        self.username_input = QLineEdit()
        self.layout.addWidget(self.username_input)

        # Sunucu IP (AWS için zorunlu)
        self.layout.addWidget(QLabel("Sunucu IP (AWS):"))
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("Örn: 13.232.x.x")
        self.layout.addWidget(self.ip_input)

        self.login_button = QPushButton("Oyuna Bağlan")
        self.login_button.clicked.connect(self.handle_login)
        self.layout.addWidget(self.login_button)

        self.setLayout(self.layout)

    def handle_login(self):
        username = self.username_input.text()
        ip = self.ip_input.text()
        
        if username and ip:
            # Burada Network sınıfını başlatıp ana oyuna geçeceğiz[cite: 2]
            print(f"Bağlanılıyor: {username} @ {ip}")
        else:
            QMessageBox.warning(self, "Hata", "Lütfen tüm alanları doldurun!")