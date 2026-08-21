import tkinter
import cv2
from PIL import Image, ImageTk


class VideoApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Test Gui")
        self.window.geimetry("640x640")


        
        self.cap = cv2.VideoCapture("")