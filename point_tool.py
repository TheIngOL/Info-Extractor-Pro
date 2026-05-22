# --------------------------------------------------------
# Info Extractor Pro
# Created by: Tobias Herden
# Assistance: Logic and structure partially generated/refined using AI (Google Gemini)
# Date: 2026-05-22
# --------------------------------------------------------

import os
from qgis.gui import QgsMapToolEmitPoint
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QCursor, QPixmap, QPainter, QColor
from qgis.core import QgsSettings

class PointTool(QgsMapToolEmitPoint):
    def __init__(self, canvas, callback):
        super().__init__(canvas)
        self.canvas = canvas
        self.callback = callback


        pathcursor = os.path.join(os.path.dirname(__file__), 'crosshair.png')
        pixmap = QPixmap(pathcursor)
        pixmap = pixmap.scaled(24, 24, Qt.AspectRatioMode.KeepAspectRatio)
        
        # --- Farbanpassung aus den QGIS-Settings laden ---
        settings = QgsSettings()
        # Hole den Hex-Code (Standard ist Rot: #FF0000)
        color_hex = settings.value("InfoExtractorPro/cursor_color", "#FF0000") 
        color = QColor(color_hex)
        
        try:
            comp_mode = QPainter.CompositionMode.CompositionMode_SourceIn
        except AttributeError:
            comp_mode = QPainter.CompositionMode_SourceIn # Fallback für ältere PyQt5 Versionen
            
        # Bild dynamisch einfärben
        painter = QPainter(pixmap)
        painter.setCompositionMode(comp_mode) 
        painter.fillRect(pixmap.rect(), color)
        painter.end()
        # -------------------------------------------------
        
        self.setCursor(QCursor(pixmap))

    def canvasReleaseEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        self.callback(point)
