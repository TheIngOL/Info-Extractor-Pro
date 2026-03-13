# --------------------------------------------------------
# Info Extractor Pro
# Created by: Tobias Herden
# Assistance: Logic and structure partially generated/refined using AI (Google Gemini)
# Date: 2026-03-13
# Qt Version: Dual-Compatible (Qt5 & Qt6)
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
        
        
        pathcurser = os.path.join(os.path.dirname(__file__), 'crosshair.png')
        pixmap = QPixmap(pathcurser)
        pixmap = pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio)
        self.setCursor(QCursor(pixmap))

    def canvasReleaseEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        self.callback(point)
