# --------------------------------------------------------
# Info Extractor Pro
# Created by: Tobias Herden
# Assistance: Logic and structure partially generated/refined using AI (Google Gemini)
# Date: 2026-03-24
# --------------------------------------------------------

from qgis.gui import QgsMapToolEmitPoint
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QCursor
import os
from qgis.PyQt.QtGui import QPixmap

class PointTool(QgsMapToolEmitPoint):
    def __init__(self, canvas, callback):
        super().__init__(canvas)
        self.canvas = canvas
        self.callback = callback
         
        pathcursor = os.path.join(os.path.dirname(__file__), 'crosshair.png')
        pixmap = QPixmap(pathcursor)
        pixmap = pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio)
        self.setCursor(QCursor(pixmap))

    def canvasReleaseEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        self.callback(point)
