# ui/face_ui.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QPainter, QBrush, QColor, QPen
from PySide6.QtCore import Qt, QTimer
from ui.animations import Animator, FaceState
import math

class AvatarFace(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.anim = Animator()
        self.status_label = QLabel("Initializing...", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #88aaff; font-size: 13px; margin-top: 15px; font-weight: bold;")

        layout = QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(self.status_label)
        layout.setContentsMargins(0, 0, 0, 20)

        self.resize(400, 500)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_state)
        self.timer.start(16)  # ~60 FPS

    def set_state(self, state):
        """Accepts FaceState enum or string, normalizes safely"""
        if isinstance(state, str):
            try:
                state = FaceState(state)
            except ValueError:
                state = FaceState.IDLE
        self.anim.state = state
        
        state_map = {
            FaceState.IDLE: "Ready",
            FaceState.LISTENING: "Listening...",
            FaceState.THINKING: "Thinking...",
            FaceState.SPEAKING: "Speaking...",
            FaceState.ERROR: "Error"
        }
        self.status_label.setText(state_map.get(state, "Ready"))
        
        # Visual feedback for errors
        if state == FaceState.ERROR:
            self.status_label.setStyleSheet("color: #ff5555; font-size: 13px; margin-top: 15px; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: #88aaff; font-size: 13px; margin-top: 15px; font-weight: bold;")

    def set_volume(self, vol: float):
        if self.anim.state == FaceState.SPEAKING:
            self.anim.target_pulse = vol * 2.5

    def update_state(self):
        self.anim.update(0.016)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2 - 40

        # Dynamic color based on state
        if self.anim.state == FaceState.ERROR:
            base_color = QColor(220, 60, 60)
            accent_color = QColor(255, 100, 100)
        elif self.anim.state == FaceState.THINKING:
            base_color = QColor(255, 180, 50)
            accent_color = QColor(255, 220, 100)
        else:
            base_color = QColor(30, 100, 220)
            accent_color = QColor(100, 180, 255)

        # Outer glow
        painter.setBrush(QBrush(base_color))
        painter.setPen(Qt.NoPen)
        glow_size = 160 + 40 * self.anim.mouth_open
        painter.drawEllipse(int(cx - glow_size/2), int(cy - glow_size/2), int(glow_size), int(glow_size))

        # Face base
        painter.setBrush(QBrush(QColor(15, 20, 30)))
        painter.drawEllipse(cx - 65, cy - 65, 130, 130)

        # Mouth (syncs with audio volume)
        mouth_h = max(4, 12 + 35 * math.sin(self.anim.pulse))
        painter.setBrush(QBrush(accent_color))
        painter.drawEllipse(cx - 22, cy + 18, 44, mouth_h)

        # Thinking orbit
        if self.anim.state == FaceState.THINKING:
            pen = QPen(QColor(255, 220, 100), 3)
            painter.setPen(pen)
            for i in range(3):
                angle = self.anim.think_angle + i * (2 * 3.14159 / 3)
                px = cx + 95 * math.cos(angle)
                py = cy + 95 * math.sin(angle)
                painter.drawEllipse(int(px - 6), int(py - 6), 12, 12)