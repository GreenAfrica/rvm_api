from .camera import open_camera
from .detector import Detector

# Global singletons for app lifetime
_cap = open_camera()
detector = Detector(_cap)
