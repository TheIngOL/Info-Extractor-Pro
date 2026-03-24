# --------------------------------------------------------
# Info Extractor Pro
# Created by: Tobias Herden
# Assistance: Logic and structure partially generated/refined using AI (Google Gemini)
# Date: 2026-03-24
# Qt Version: Dual-Compatible (Qt5 & Qt6)
# --------------------------------------------------------

import os
import re
import datetime
import time
from qgis.PyQt.QtCore import Qt, QCoreApplication
from qgis.PyQt.QtGui import QIcon, QPalette
from qgis.PyQt.QtWidgets import (QAction, QDialog, QVBoxLayout, QTextBrowser, 
                             QDialogButtonBox, QFileDialog, QApplication)
from qgis.core import QgsRaster, QgsFeatureRequest, QgsGeometry, QgsRectangle
from .point_tool import PointTool

class ResultDialog(QDialog):
    def __init__(self, title, html_content, coords_to_copy, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(800, 500)
        self.coords_to_copy = coords_to_copy

        layout = QVBoxLayout(self)
        self.browser = QTextBrowser()
        
        # --- Qt6-Fix: QPalette Roles ---
        palette = self.palette()
        try:
            bg_role = QPalette.ColorRole.Base
            text_role = QPalette.ColorRole.Text
        except AttributeError:
            bg_role = QPalette.Base
            text_role = QPalette.Text

        bg_color = palette.color(bg_role).name()
        text_color = palette.color(text_role).name()

        style = f"""
        <style>
            body {{ background-color: {bg_color}; color: {text_color}; font-family: sans-serif; font-size: 10pt; line-height: 1.4; }}
            h3 {{ color: #e67e22; margin-bottom: 5px; }}
            b {{ color: #e67e22; }}
            b.layer-title {{ color: #e67e22; font-size: 11pt; display: block; margin-top: 10px; }}
            hr {{ border: 0; border-top: 1px dotted #888; margin: 10px 0; }}
            ul {{ margin-top: 5px; }}
        </style>
        """
        self.browser.setHtml(style + html_content)
        layout.addWidget(self.browser)

        # QDialogButtonBox StandardButtons
        try:
            ok_button = QDialogButtonBox.StandardButton.Ok
        except AttributeError:
            ok_button = QDialogButtonBox.Ok

        self.button_box = QDialogButtonBox(ok_button)
        
        # QDialogButtonBox ButtonRole
        try:
            action_role = QDialogButtonBox.ButtonRole.ActionRole
        except AttributeError:
            action_role = QDialogButtonBox.ActionRole

        # Kopier-Button
        self.copy_button = self.button_box.addButton("Koordinaten kopieren", action_role)
        self.copy_button.clicked.connect(self.copy_to_clipboard)
        
        # Export-Button
        self.export_button = self.button_box.addButton("Daten exportieren (.txt)", action_role)
        self.export_button.clicked.connect(self.export_data)
        
        self.button_box.accepted.connect(self.accept)
        layout.addWidget(self.button_box)

    def copy_to_clipboard(self):
        QApplication.clipboard().setText(self.coords_to_copy)
        print(f"Kopiert: {self.coords_to_copy}")

    def export_data(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Ergebnis speichern", "abfrage_ergebnis.txt", "Text (*.txt)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.browser.toPlainText())
            except Exception as e:
                print(f"Export-Fehler: {e}")

class InfoExtractor:
    def __init__(self, iface):
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.action = None

    def initGui(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
        self.action = QAction(QIcon(icon_path), "WMS/WFS Abfrage", self.iface.mainWindow())
        self.action.triggered.connect(self.activate_tool)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("&Info Tools", self.action)

    def unload(self):
        if self.action:
            self.iface.removeToolBarIcon(self.action)
            self.iface.removePluginMenu("&Info Tools", self.action)

    def activate_tool(self):
        self.point_tool = PointTool(self.canvas, self.process_point)
        self.canvas.setMapTool(self.point_tool)

    def clean_html(self, html):
        if not html: return ""
        html = re.sub(r'color\s*:\s*[^;"]+;?', '', html, flags=re.IGNORECASE)
        html = re.sub(r'background-color\s*:\s*[^;"]+;?', '', html, flags=re.IGNORECASE)
        return html

    def process_point(self, point):
        # --- Qt6-Fix: Cursor Shape ---
        try:
            QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        except AttributeError:
            QApplication.setOverrideCursor(Qt.WaitCursor)

        self.iface.statusBarIface().showMessage("Abfrage läuft...")

        try:
            now = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            coords_str = f"Ost: {point.x():.3f}, Nord: {point.y():.3f}"
            kbs = self.canvas.mapSettings().destinationCrs().authid()
            
            results = [
                f"<h3>Abfrage-Protokoll</h3>",
                f"<b>Zeitpunkt:</b> {now}<br>",
                f"<b>Koordinaten:</b> {coords_str}<br>",
                f"<b>System:</b> {kbs}<br>"
            ]
            
            layers = self.canvas.layers()
            for layer in layers:
                QCoreApplication.processEvents()

                if layer.type() == layer.RasterLayer:
                    provider = layer.dataProvider()
                    if not (provider.capabilities() & provider.Identify):
                        continue
                    
                    pixel_size = self.canvas.mapUnitsPerPixel()
                    tolerance_units = pixel_size * 10  # 10 Pixel Puffer
                    
                    search_area = QgsRectangle(
                        point.x() - tolerance_units,
                        point.y() - tolerance_units,
                        point.x() + tolerance_units,
                        point.y() + tolerance_units
                    )

                    res = provider.identify(point, 
                                            QgsRaster.IdentifyFormatHtml, 
                                            search_area, 
                                            10, 10)
                    
                    if not res.isValid() or not res.results():
                        res = provider.identify(point, 
                                                QgsRaster.IdentifyFormatText, 
                                                search_area, 
                                                10, 10)
                    
                    if res.isValid() and res.results():
                        content = list(res.results().values())[0]
                        if content and len(str(content).strip()) > 15:
                            results.append(f"<hr><b class='layer-title'>Layer: {layer.name()}</b><br>{self.clean_html(str(content))}")
                            time.sleep(0.02)

                elif layer.type() == layer.VectorLayer:
                    tolerance = self.canvas.mapUnitsPerPixel() * 10
                    rect = QgsGeometry.fromPointXY(point).buffer(tolerance, 5).boundingBox()
                    request = QgsFeatureRequest().setFilterRect(rect).setFlags(QgsFeatureRequest.NoGeometry)
                    features = layer.getFeatures(request)
                    
                    layer_data = []
                    for feat in features:
                        attrs = feat.attributeMap()
                        items = "".join([f"<li><b>{k}:</b> {v}</li>" for k, v in attrs.items()])
                        layer_data.append(f"<ul>{items}</ul>")
                    
                    if layer_data:
                        results.append(f"<hr><b class='layer-title'>Layer: {layer.name()}</b>" + "".join(layer_data[:10]))

        finally:
            QApplication.restoreOverrideCursor()
            self.iface.statusBarIface().clearMessage()

        self.show_custom_dialog("Ergebnisse der Abfrage", "".join(results), coords_str)

    def show_custom_dialog(self, title, html_text, coords_str):
        dialog = ResultDialog(title, html_text, coords_str, self.iface.mainWindow())
        
        # Dual-Kompatibilität für exec() (Qt6) und exec_() (Qt5)
        if hasattr(dialog, 'exec'):
            dialog.exec()
        else:
            dialog.exec_()
