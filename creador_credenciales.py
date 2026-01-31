import sys
import os
import json 

# --- GESTIÓN DE RUTAS PARA EXE Y SCRIPT ---
if getattr(sys, 'frozen', False):
    # SI ESTAMOS EN MODO .EXE:
    # 1. La base de datos (JSON) se guarda AL LADO del ejecutable (para que persista)
    BASE_DIR = os.path.dirname(sys.executable)
    # 2. Los recursos (Logo) se buscan ADENTRO del paquete temporal (sys._MEIPASS)
    RESOURCE_DIR = sys._MEIPASS
else:
    # SI ESTAMOS EN MODO SCRIPT (Python normal):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_DIR = BASE_DIR

# Rutas definitivas
# Asegúrate que tu imagen se llame EXACTAMENTE así en tu carpeta
RUTA_LOGO_ESCUELA = os.path.join(RESOURCE_DIR, "logo_placeholder.png") 
ARCHIVO_DB = os.path.join(BASE_DIR, "base_datos_alumnos.json")

from PyQt6 import QtWidgets, QtGui, QtCore
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox, QFrame, QSplitter, QScrollArea
)
from PyQt6.QtGui import (
    QPainter, QPixmap, QColor, QFont, QPen, QBrush, QPainterPath, 
    QImage, QPalette, QDragEnterEvent, QDropEvent, QFontMetrics
)
from PyQt6.QtCore import Qt, pyqtSignal

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm

# --- CONFIGURACIÓN ---
CARD_W = 1000
CARD_H = 600
PRINT_W_MM = 84
PRINT_H_MM = 52

# --- FUENTES ---
def get_playful_font(size, weight=QFont.Weight.Normal):
    playful_families = ["Comic Sans MS", "Segoe Print", "Ink Free", "Kristen ITC"]
    for family in playful_families:
        font = QFont(family, size, weight)
        if font.exactMatch(): return font
    return QFont("Arial Rounded MT Bold", size, weight)

# --- DRAG & DROP ---
class DropLabel(QLabel):
    imageDropped = pyqtSignal(str)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setText("\nArrastra tu Foto Aquí\no Click para Buscar")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls(): event.accept()
        else: event.ignore()
    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls: self.imageDropped.emit(urls[0].toLocalFile())

# --- DIBUJO ---
class CardPainter:
    @staticmethod
    def fit_font_to_width(text, font, max_width):
        fm = QFontMetrics(font)
        text_w = fm.horizontalAdvance(text)
        current_font = QFont(font)
        ps = current_font.pointSize()
        while text_w > max_width and ps > 15:
            ps -= 2
            current_font.setPointSize(ps)
            fm = QFontMetrics(current_font)
            text_w = fm.horizontalAdvance(text)
        return current_font, fm.height()

    @staticmethod
    def draw_colorful_leer(painter, x_center, y_baseline):
        colors = [QColor("#FF0000"), QColor("#00AA00"), QColor("#0000FF"), QColor("#FF8C00")]
        word = "LEER"
        font_leer = get_playful_font(42, QFont.Weight.Bold)
        painter.setFont(font_leer)
        fm_leer = QFontMetrics(font_leer)
        current_x = x_center 
        for i, char in enumerate(word):
            color = colors[i % len(colors)]
            path = QPainterPath()
            path.addText(current_x, y_baseline, font_leer, char)
            painter.setPen(QPen(Qt.GlobalColor.white, 8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            painter.setBrush(Qt.BrushStyle.NoBrush); painter.drawPath(path)
            painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(color); painter.drawPath(path)
            current_x += fm_leer.horizontalAdvance(char) + 3

        font_resto = get_playful_font(24, QFont.Weight.Bold)
        painter.setFont(font_resto)
        fm_resto = QFontMetrics(font_resto)
        text_resto = "es divertido"
        w_resto = fm_resto.horizontalAdvance(text_resto)
        center_x_leer = x_center + 70 
        x_resto = center_x_leer - (w_resto / 2)
        y_resto = y_baseline + 35 
        painter.setPen(QColor("#00539C")); painter.drawText(int(x_resto), int(y_resto), text_resto)

    @staticmethod
    def draw_card(data):
        C_AZUL_CLARO = QColor("#4FB0C6"); C_AZUL_OSCURO = QColor("#00539C"); C_NARANJA = QColor("#FF8C00") 
        pixmap = QPixmap(CARD_W, CARD_H); pixmap.fill(Qt.GlobalColor.white)
        painter = QPainter(pixmap); painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fondo
        path_h = QPainterPath(); path_h.moveTo(0, 0); path_h.lineTo(CARD_W, 0); path_h.lineTo(CARD_W, 130)
        path_h.cubicTo(CARD_W*0.7, 190, CARD_W*0.3, 70, 0, 160); path_h.closeSubpath()
        grad = QtGui.QLinearGradient(0, 0, 0, 180); grad.setColorAt(0, C_AZUL_CLARO.lighter(120)); grad.setColorAt(1, C_AZUL_CLARO)
        painter.setPen(Qt.PenStyle.NoPen); painter.setBrush(QBrush(grad)); painter.drawPath(path_h)

        path_f = QPainterPath(); path_f.moveTo(0, CARD_H); path_f.lineTo(CARD_W, CARD_H); path_f.lineTo(CARD_W, CARD_H-110)
        path_f.cubicTo(CARD_W*0.6, CARD_H-180, CARD_W*0.4, CARD_H-50, 0, CARD_H-130); path_f.closeSubpath()
        painter.setBrush(QBrush(C_AZUL_CLARO.lighter(130))); painter.drawPath(path_f)

        # Logo
        if os.path.exists(RUTA_LOGO_ESCUELA):
            logo = QPixmap(RUTA_LOGO_ESCUELA).scaled(140, 140, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            painter.drawPixmap(30, 20, logo)
        else:
            painter.setPen(QPen(Qt.GlobalColor.gray, 2, Qt.PenStyle.DashLine)); painter.setBrush(Qt.BrushStyle.NoBrush); painter.drawRect(30, 20, 140, 140)

        # Titulo
        font_tit = get_playful_font(60, QFont.Weight.Bold)
        painter.setFont(font_tit); painter.setPen(C_AZUL_OSCURO)
        painter.drawText(CARD_W - 405, 115, "Biblioteca"); painter.setPen(Qt.GlobalColor.white); painter.drawText(CARD_W - 410, 110, "Biblioteca")

        # Foto
        px, py, pw, ph = 50, 190, 280, 350
        painter.setPen(QPen(C_AZUL_OSCURO, 7)); painter.setBrush(Qt.BrushStyle.NoBrush); painter.drawRect(px, py, pw, ph)
        if data.get("photo_path") and os.path.exists(data["photo_path"]):
            img = QImage(data["photo_path"])
            scaled = img.scaled(pw-7, ph-7, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation)
            painter.drawImage(px+4, py+4, scaled)

        # Datos
        tx = 370; ty = 240
        painter.setFont(get_playful_font(26)); painter.setPen(C_AZUL_CLARO.darker(115)); painter.drawText(tx, ty, "Nombre del Alumno:")
        ty += 70
        base_font_name = get_playful_font(55, QFont.Weight.Bold)
        final_font, _ = CardPainter.fit_font_to_width(data["name"], base_font_name, CARD_W - tx - 40)
        painter.setFont(final_font); painter.setPen(C_AZUL_OSCURO); painter.drawText(tx, ty, data["name"])
        painter.setPen(QPen(C_AZUL_OSCURO, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)); painter.drawLine(tx, ty + 15, CARD_W - 40, ty + 15)
        ty += 100
        painter.setFont(get_playful_font(26)); painter.setPen(C_AZUL_CLARO.darker(115)); painter.drawText(tx, ty, "Grado:"); painter.drawText(tx+320, ty, "Grupo:")
        painter.setFont(get_playful_font(45, QFont.Weight.Bold)); painter.setPen(C_AZUL_OSCURO); painter.drawText(tx+130, ty+5, data["grade"]); painter.drawText(tx+450, ty+5, data["group"])
        painter.setPen(QPen(C_AZUL_OSCURO, 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)); painter.drawLine(tx+120, ty+20, tx+280, ty+20); painter.drawLine(tx+440, ty+20, tx+580, ty+20)

        # Footer
        CardPainter.draw_colorful_leer(painter, 380, CARD_H - 90)

        if data.get("folio"):
            font_folio = get_playful_font(30, QFont.Weight.Bold)
            painter.setFont(font_folio); painter.setPen(C_NARANJA)
            folio_text = f"FOLIO: {data['folio']}"
            fm = QFontMetrics(font_folio); w_text = fm.horizontalAdvance(folio_text)
            painter.drawText(CARD_W - 40 - w_text, CARD_H - 40, folio_text)

        painter.end()
        return pixmap

# --- VENTANA ---
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema Credenciales - v9.0 Final")
        self.students = []; self.photo_path = None; self.is_dark_mode = False 
        app = QApplication.instance(); app.setStyle("Fusion")
        self.setup_ui(); self.apply_theme_light(); self.load_data_from_db(); self.showMaximized()

    def setup_ui(self):
        central = QWidget(); self.setCentralWidget(central); main_layout = QVBoxLayout(central)
        top_bar = QHBoxLayout(); top_bar.addStretch()
        self.btn_theme = QPushButton("🌙 Modo Obscuro"); self.btn_theme.setFixedSize(140, 40)
        self.btn_theme.clicked.connect(self.toggle_theme); top_bar.addWidget(self.btn_theme); main_layout.addLayout(top_bar)
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.left_c = QWidget(); left_layout = QVBoxLayout(self.left_c); left_layout.setSpacing(15)
        lbl_tit = QLabel("Nueva Credencial"); lbl_tit.setObjectName("Titulo"); left_layout.addWidget(lbl_tit)

        self.input_nombre = self.mk_input(left_layout, "Nombre Completo:")
        self.input_grado = self.mk_input(left_layout, "Grado:")
        self.input_grupo = self.mk_input(left_layout, "Grupo:")
        self.input_folio = self.mk_input(left_layout, "Folio (Opcional):")

        left_layout.addWidget(QLabel("Fotografía:"))
        self.drop_area = DropLabel(); self.drop_area.setFixedSize(220, 260)
        self.drop_area.imageDropped.connect(self.load_photo_from_path); self.drop_area.mousePressEvent = self.manual_photo_select
        h_d = QHBoxLayout(); h_d.addStretch(); h_d.addWidget(self.drop_area); h_d.addStretch(); left_layout.addLayout(h_d)

        btn_add = QPushButton("AGREGAR ALUMNO", objectName="BtnAdd"); btn_add.setMinimumHeight(45)
        btn_add.clicked.connect(self.add_student); left_layout.addWidget(btn_add); left_layout.addStretch()
        scroll.setWidget(self.left_c); splitter.addWidget(scroll)

        self.right_c = QWidget(); right_layout = QVBoxLayout(self.right_c)
        lbl_list = QLabel("Lista de Impresión"); lbl_list.setObjectName("Titulo"); right_layout.addWidget(lbl_list)
        self.table = QTableWidget(0, 5); self.table.setHorizontalHeaderLabels(["Sel", "Nombre", "Grado", "Grupo", "Folio"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch); self.table.setColumnWidth(0, 40); right_layout.addWidget(self.table)
        
        h_btns = QHBoxLayout()
        btn_all = QPushButton("Todas"); btn_all.clicked.connect(lambda: self.select_all(True))
        btn_none = QPushButton("Ninguna"); btn_none.clicked.connect(lambda: self.select_all(False))
        btn_del = QPushButton("Borrar"); btn_del.clicked.connect(self.delete_row); btn_del.setObjectName("BtnDel")
        h_btns.addWidget(btn_all); h_btns.addWidget(btn_none); h_btns.addWidget(btn_del); right_layout.addLayout(h_btns)
        btn_pdf = QPushButton("GENERAR PDF", objectName="BtnPDF"); btn_pdf.setMinimumHeight(55)
        btn_pdf.clicked.connect(self.generate_pdf); right_layout.addWidget(btn_pdf)
        splitter.addWidget(self.right_c); splitter.setSizes([400, 800]); main_layout.addWidget(splitter)

    def load_data_from_db(self):
        if os.path.exists(ARCHIVO_DB):
            try:
                with open(ARCHIVO_DB, "r", encoding="utf-8") as f:
                    self.students = json.load(f)
                    for st in self.students: self.add_row_to_table(st)
            except: pass
    def save_data_to_db(self):
        try:
            with open(ARCHIVO_DB, "w", encoding="utf-8") as f: json.dump(self.students, f, indent=4, ensure_ascii=False)
        except: pass

    def toggle_theme(self):
        if self.is_dark_mode: self.apply_theme_light(); self.btn_theme.setText("🌙 Modo Obscuro")
        else: self.apply_theme_dark(); self.btn_theme.setText("☀️ Modo Claro")
        self.is_dark_mode = not self.is_dark_mode
    def apply_theme_light(self):
        palette = QPalette(); palette.setColor(QPalette.ColorRole.Window, Qt.GlobalColor.white); palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.Base, Qt.GlobalColor.white); palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.black)
        palette.setColor(QPalette.ColorRole.Button, QColor("#f0f0f0")); palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.black)
        QApplication.instance().setPalette(palette)
        font = get_playful_font(12).family()
        self.setStyleSheet(f"""
            QWidget {{ font-family: '{font}', 'Segoe UI'; }} QLabel#Titulo {{ color: #00539C; font-size: 20px; font-weight: bold; }}
            QLabel {{ color: #2c3e50; font-size: 14px; font-weight: bold; }} QLineEdit {{ background: white; color: black; border: 2px solid #ccc; padding: 6px; border-radius: 8px; }}
            QTableWidget {{ background: white; color: black; border: 2px solid #ccc; }} QHeaderView::section {{ background: #00539C; color: white; }}
            QPushButton {{ background: #ecf0f1; border: 2px solid #bdc3c7; border-radius: 10px; padding: 8px; color: black; font-weight: bold; }}
            QPushButton#BtnAdd {{ background: #00539C; color: white; border: none; }} QPushButton#BtnPDF {{ background: #27ae60; color: white; border: none; }}
            QPushButton#BtnDel {{ background: #e74c3c; color: white; border: none; }} QScrollArea {{ background: white; border: none; }}
        """)
        self.drop_area.setStyleSheet("QLabel { border: 3px dashed #bdc3c7; background: #f9f9f9; color: #7f8c8d; border-radius: 15px; font-size: 14px; }")
    def apply_theme_dark(self):
        palette = QPalette(); c_bg = QColor("#1e272e"); c_fg = QColor("#d2dae2")
        palette.setColor(QPalette.ColorRole.Window, c_bg); palette.setColor(QPalette.ColorRole.WindowText, c_fg)
        palette.setColor(QPalette.ColorRole.Base, QColor("#2f3640")); palette.setColor(QPalette.ColorRole.Text, c_fg)
        palette.setColor(QPalette.ColorRole.Button, QColor("#485460")); palette.setColor(QPalette.ColorRole.ButtonText, c_fg)
        QApplication.instance().setPalette(palette)
        font = get_playful_font(12).family()
        self.setStyleSheet(f"""
            QWidget {{ font-family: '{font}', 'Segoe UI'; }} QLabel#Titulo {{ color: #4FB0C6; font-size: 20px; font-weight: bold; }}
            QLabel {{ color: #d2dae2; font-size: 14px; font-weight: bold; }} QLineEdit {{ background: #2f3640; color: white; border: 2px solid #485460; padding: 6px; border-radius: 8px; }}
            QTableWidget {{ background: #2f3640; color: white; border: 2px solid #485460; }} QHeaderView::section {{ background: #00539C; color: white; }}
            QPushButton {{ background: #485460; border: 2px solid #1e272e; border-radius: 10px; padding: 8px; color: white; font-weight: bold; }}
            QPushButton#BtnAdd {{ background: #00539C; color: white; border: none; }} QPushButton#BtnPDF {{ background: #27ae60; color: white; border: none; }}
            QPushButton#BtnDel {{ background: #c0392b; color: white; border: none; }} QScrollArea {{ background: #1e272e; border: none; }}
        """)
        self.drop_area.setStyleSheet("QLabel { border: 3px dashed #485460; background: #2f3640; color: #d2dae2; border-radius: 15px; font-size: 14px; }")

    def mk_input(self, l, t): l.addWidget(QLabel(t)); i = QLineEdit(); l.addWidget(i); return i
    def manual_photo_select(self, event):
        f, _ = QFileDialog.getOpenFileName(self, "Foto", "", "Img (*.jpg *.png *.jpeg)")
        if f: self.load_photo_from_path(f)
    def load_photo_from_path(self, path):
        self.photo_path = path; pix = QPixmap(path)
        self.drop_area.setPixmap(pix.scaled(self.drop_area.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)); self.drop_area.setText("")
    def add_row_to_table(self, s):
        r = self.table.rowCount(); self.table.insertRow(r)
        chk = QTableWidgetItem(); chk.setCheckState(Qt.CheckState.Checked); chk.setData(Qt.ItemDataRole.UserRole, s["id"])
        self.table.setItem(r,0,chk); self.table.setItem(r,1,QTableWidgetItem(s["name"])); self.table.setItem(r,2,QTableWidgetItem(s["grade"])); self.table.setItem(r,3,QTableWidgetItem(s["group"])); self.table.setItem(r,4,QTableWidgetItem(s["folio"]))
    
    def add_student(self):
        n = self.input_nombre.text().strip().title()
        gra = self.input_grado.text().strip().upper()
        gru = self.input_grupo.text().strip().upper()
        
        # VALIDACIÓN MEJORADA: Todo obligatorio excepto folio
        if not n or not gra or not gru or not self.photo_path:
            QMessageBox.warning(self, "Faltan Datos", "Por favor llena: Nombre, Grado, Grupo y selecciona una Foto.")
            return

        st = {
            "id": len(self.students) + 1000, "name": n,
            "grade": gra, "group": gru, # SE CONVIERTEN A MAYUSCULA (a -> A)
            "folio": self.input_folio.text().upper(), "photo_path": self.photo_path
        }
        self.students.append(st); self.add_row_to_table(st); self.save_data_to_db()
        self.input_nombre.clear(); self.input_grado.clear(); self.input_grupo.clear(); self.input_folio.clear()
        self.drop_area.clear(); self.drop_area.setText("\nArrastra tu Foto Aquí\no Click"); self.photo_path = None; self.input_nombre.setFocus()

    def select_all(self, s): st = Qt.CheckState.Checked if s else Qt.CheckState.Unchecked; [self.table.item(i,0).setCheckState(st) for i in range(self.table.rowCount())]
    def delete_row(self):
        rows = [i for i in range(self.table.rowCount()) if self.table.item(i,0).checkState() == Qt.CheckState.Checked]
        ids = [self.table.item(i,0).data(Qt.ItemDataRole.UserRole) for i in rows]
        for i in sorted(rows, reverse=True): self.table.removeRow(i)
        self.students = [s for s in self.students if s["id"] not in ids]
        self.save_data_to_db()

    def generate_pdf(self):
        sel = [next((x for x in self.students if x["id"] == self.table.item(i,0).data(Qt.ItemDataRole.UserRole)), None) for i in range(self.table.rowCount()) if self.table.item(i,0).checkState() == Qt.CheckState.Checked]
        if not sel: return QMessageBox.warning(self, "Ojo", "Selecciona alumnos")
        
        # AQUI ESTA EL CAMBIO: Nombre sugerido por defecto
        p, _ = QFileDialog.getSaveFileName(self, "Guardar PDF", "Credenciales_Biblioteca.pdf", "PDF (*.pdf)")
        if not p: return

        c = canvas.Canvas(p, pagesize=letter); mh, mw = 15*mm, 15*mm; x, y = mw, letter[1]-mh-(PRINT_H_MM*mm); col = 0; tmps = []
        for i, s in enumerate(sel):
            pix = CardPainter.draw_card(s); tp = f"t_{i}.png"; pix.save(tp, "PNG", 100); tmps.append(tp)
            if y < mh: c.showPage(); y = letter[1]-mh-(PRINT_H_MM*mm); col = 0
            cx = x + (col*(PRINT_W_MM*mm+5*mm)); c.drawImage(tp, cx, y, width=PRINT_W_MM*mm, height=PRINT_H_MM*mm); c.setStrokeColorRGB(0.9,0.9,0.9); c.rect(cx, y, PRINT_W_MM*mm, PRINT_H_MM*mm)
            col += 1; 
            if col >= 2: col = 0; y -= (PRINT_H_MM*mm + 2*mm)
        c.save(); [os.remove(t) for t in tmps]; QMessageBox.information(self, "Listo", f"PDF:\n{p}")

if __name__ == "__main__":
    app = QApplication(sys.argv); window = MainWindow(); sys.exit(app.exec())