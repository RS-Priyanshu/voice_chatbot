from enum import Enum

class FaceState(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    ERROR = "error"

class Animator:
    def __init__(self):
        self.state = FaceState.IDLE
        self.mouth_open = 0.0
        self.pulse = 0.0
        self.target_pulse = 0.0
        self.think_angle = 0.0

    def update(self, dt: float):
        if self.state == FaceState.THINKING:
            self.think_angle = (self.think_angle + 2 * dt) % (2 * 3.14159)
        else:
            self.think_angle = 0

        if self.state in (FaceState.SPEAKING, FaceState.LISTENING):
            self.pulse += dt * 3
            self.target_pulse = max(0.8, self.target_pulse) if self.state == FaceState.SPEAKING else 0.5
        else:
            self.pulse = 0
            self.target_pulse = 0

        # Smooth interpolation
        self.mouth_open += (self.target_pulse - self.mouth_open) * 0.2
        self.target_pulse *= 0.95