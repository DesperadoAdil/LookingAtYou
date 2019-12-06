# -*- coding: utf-8 -*-
import sys
import cv2
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import time
import win32api
import win32con

SLEEP_TIME = 250 # 4 minutes
KEY = ord('A') # press A every 4 minutes
CV_CAP_PROP_FRAME_WIDTH = 3
CV_CAP_PROP_FRAME_HEIGHT = 4
MODEL_FILE_PATH = "haarcascade_frontalface_default.xml"
START_ANGLE = 30
SPAN_ANGLE = 120
ANGLE_MULTIPLE = 16
ARC_POS_X = 0
ARC_POS_Y = 240
OUTTER_CIRCLE_D = 600
INNER_CIRCLE_D = 200

class KeyPressThread(QThread):

	def __init__(self):
		super(KeyPressThread, self).__init__()
		self.running = False

	def run(self):
		self.running = True
		while self.running:
			win32api.keybd_event(KEY, 0, 0, 0)
			win32api.keybd_event(KEY, 0, win32con.KEYEVENTF_KEYUP, 0)
			time.sleep(SLEEP_TIME)

	def stop(self):
		self.running = False


class AutoRunThread(QThread):

	def __init__(self, ui):
		super(AutoRunThread, self).__init__()
		self.ui = ui
		self.running = False
		self.cap = cv2.VideoCapture(0)
		self.cap_width = self.cap.get(CV_CAP_PROP_FRAME_WIDTH)
		self.cap_height = self.cap.get(CV_CAP_PROP_FRAME_HEIGHT)
		self.faceCascade = cv2.CascadeClassifier(MODEL_FILE_PATH)

	def run(self):
		self.running = True
		while self.running:
			_, frame = self.cap.read()
			gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			faces = self.faceCascade.detectMultiScale(
				gray,
				scaleFactor=1.1,
				minNeighbors=5,
				minSize=(30, 30)
			)
			face = len(faces)
			self.ui.face = face
			print ("Found {0} faces!".format(face))
			if face > 1:
				faces = sorted(faces, key=lambda x:x[0], reverse=True)
			for (x, y, w, h) in faces:
				rec_x = (1 - (x+w) / self.cap_width) * self.ui.width
				rec_y = (y / self.cap_height) * self.ui.height
				rec_w = (w / self.cap_width) * self.ui.width
				rec_h = (h / self.cap_height) * self.ui.height
				self.ui.center_x = int(rec_x + rec_w/2)
				self.ui.center_y = int(rec_y + rec_h/2)
				break
			self.ui.update()

	def stop(self):
		self.running = False
		self.cap.release()


class LookingAtYou(QWidget):
	stopDetect = pyqtSignal()

	def __init__(self):
		super().__init__()
		self.desktop = QApplication.desktop()
		self.face = 0
		self.center_x = 0
		self.center_y = 0

		self.screenRect = self.desktop.screenGeometry()
		self.height = self.screenRect.height()
		self.width = self.screenRect.width()
		self.center = (int(self.width/2), int(self.height/2))
		print (self.center)

		self.setWindowTitle("I'm Looking At You")
		palette = QPalette()
		palette.setColor(self.backgroundRole(), QColor(0, 0, 0))
		self.setPalette(palette)
		self.setAutoFillBackground(True)

		self.autorunthread = AutoRunThread(self)
		self.stopDetect.connect(self.autorunthread.stop)
		self.autorunthread.start()

		self.keypressthread = KeyPressThread()
		self.stopDetect.connect(self.keypressthread.stop)
		self.keypressthread.start()

		self.showFullScreen()

	def keyPressEvent(self, event):
		key = event.key()
		if key == Qt.Key_Q:
			self.stopDetect.emit()
			self.close()
		else:
			pass

	def paintEvent(self, QPaintEvent):
		painter = QPainter(self)
		white = QColor(255, 255, 255)
		black = QColor(0, 0, 0)
		gray = QColor(155, 155, 155)

		painter.begin(self)
		painter.setPen(white)
		startAngle = START_ANGLE * ANGLE_MULTIPLE
		spanAngle = SPAN_ANGLE * ANGLE_MULTIPLE
		painter.drawArc(ARC_POS_X, ARC_POS_Y, self.width, self.height, startAngle, spanAngle)
		startAngle = (START_ANGLE + 180) * ANGLE_MULTIPLE
		spanAngle = SPAN_ANGLE * ANGLE_MULTIPLE
		painter.drawArc(ARC_POS_X, -ARC_POS_Y, self.width, self.height, startAngle, spanAngle)

		if self.face >= 1:
			painter.setPen(gray)
			painter.setBrush(gray)
			painter.drawEllipse((self.width-OUTTER_CIRCLE_D)/2, (self.height-OUTTER_CIRCLE_D)/2, OUTTER_CIRCLE_D, OUTTER_CIRCLE_D)
			painter.setPen(black)
			painter.setBrush(black)
			x = (self.center_x * 2 / self.width) - 1
			y = (self.center_y * 2 / self.height) - 1
			xx = x * ((1 - y*y/2) ** 0.5)
			yy = y * ((1 - x*x/2) ** 0.5)
			# print ("x: %.3f y: %.3f" % (x, y))
			print ("xx: %.3f yy: %.3f" % (xx, yy))
			painter.drawEllipse(self.center[0]+int((xx-0.5)*INNER_CIRCLE_D), self.center[1]+int((yy-0.5)*INNER_CIRCLE_D), INNER_CIRCLE_D, INNER_CIRCLE_D)
		else:
			pass
		painter.end()


if __name__ == '__main__':
	app = QApplication(sys.argv)
	w = LookingAtYou()
	sys.exit(app.exec_())
