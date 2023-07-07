from PyQt5 import QtCore, QtWidgets, QtGui
import design
import sys
import mimetypes
import os
from PIL import Image, ImageDraw, ImageFont
import tempfile
import pyzbar.pyzbar

version = "20230707.2330"

class MainWindow(QtWidgets.QMainWindow, design.Ui_MainWindow):
   def __init__(self, app):
      super().__init__()
      self.setupUi(self)

      self.label_version.setText(version)

      self.tab_settings.setEnabled(False)

      self.debug = False
      if "--debug" in app.arguments():
         self.debug = True

      self.pushButton_addFiles.clicked.connect(self.openFiles)
      self.pushButton_clearList.clicked.connect(self.clearList)
      self.pushButton_generatePrint.clicked.connect(self.generateFile)
      self.listWidget_files.viewport().installEventFilter(self)

      self.list_items = []
      self.statusbarTimeout = 2000

      self.setSettings()

   def setSettings(self):
      self.settings = {}
      self.setDefaultSettings()

   def setDefaultSettings(self):
      self.settings["sizeA4"] = (1568, 2218) # размер холста
      self.settings["barcodeVSpacing"] = 25 # вертикальное расстояние между штрихкодами
      self.settings["barcodeHSpacing"] = 0 # горизонтальное расстояние между штрихкодами

      self.settings["addText"] = True # добавлять ли подпись под штрихкодом
      self.settings["pixelFontHeight"] = 25 # высота подписи под штрихкодом
      self.settings["marginText"] = 5 # отступ подписи от штрихкода

   def openFiles(self):
      imageExtensions = " ".join(f"*{ext}" for ext in self.imageExtensions())
      files = QtWidgets.QFileDialog.getOpenFileNames(self, filter=f"Изображения ({imageExtensions})")[0]
      for file in files:
         self.addFile(file)
      if files:
         self.statusbar.showMessage("Файлы добавлены", self.statusbarTimeout)

   def eventFilter(self, source, event):
      if (source is self.listWidget_files.viewport() and
         (event.type() in (QtCore.QEvent.DragEnter,
                           QtCore.QEvent.DragMove,
                           QtCore.QEvent.Drop,)) and
          event.mimeData().hasUrls()):
         files_count = 0
         if event.type() == QtCore.QEvent.Drop:
            for url in event.mimeData().urls():
               if self.isImage(url):
                  self.addFile(url.toLocalFile())
                  files_count += 1
         if files_count:
            self.statusbar.showMessage("Файлы добавлены", self.statusbarTimeout)
         event.accept()
         return True
      elif (source is self.listWidget_files.viewport() and
         (event.type() in (QtCore.QEvent.ContextMenu,))):
         menu = QtWidgets.QMenu()
         menu_copy = QtWidgets.QAction("Копировать")
         menu_del = QtWidgets.QAction("Удалить")
         menu.addAction(menu_copy)
         menu.addAction(menu_del)
         
         try:
             item = self.listWidget_files.itemAt(event.pos())
         except Exception as e:
             print(f"No item selected {e}")
             return False

         if not item: return False

         menu_click = menu.exec(event.globalPos())
 
         if menu_click == menu_copy:
            if self.debug:
               print("Скопировано", item)
            path = item.text()
            QtWidgets.QApplication.clipboard().setText(path)
            self.statusbar.showMessage(f"Скопировано {path}", self.statusbarTimeout)

         elif menu_click == menu_del:
            if self.debug:
               print("Удалено", item)
            self.removeFile(item)

         event.accept()
         return True
      return super().eventFilter(source, event)

   def generateFile(self):
      if self.debug:
         print("generate")

      if self.list_items:
         img = Image.new("1", self.settings["sizeA4"], color="#ffffff")
         box = {"right": 0, "bottom": 0, "maxbottom": 0}
         index_item = 0

         tempFilePath = tempfile.mktemp('.png')

         for barcodePath in self.list_items:
            # Координаты указаны - холст есть
            if box:
         #barcodePath = self.list_items[0]
         #while box:
               index_item += 1
               self.statusbar.showMessage(f"({index_item}/{len(self.list_items)}) Добавление на лист {barcodePath}", self.statusbarTimeout)
               img, box = self.addBarcode(img, barcodePath, box)
      
         img.save(tempFilePath)
   
         self.statusbar.showMessage(f"Файл для печати создан", self.statusbarTimeout)

      else:
         self.statusbar.showMessage(f"Сначала добавьте файлы", self.statusbarTimeout)

   def addBarcode(self, img, barcodePath, box):
      barcode = Image.open(barcodePath)

      #barcode = barcode.convert("1")
      #barcode = barcode.resize((barcode.width//4, barcode.height//4,))
      if box["right"]+barcode.width > img.width:
         # Штрихкод выйдет за правую рамку холста, если разместить его правее, поэтому сдвигаем вниз и к левому краю
         box = {
            "right": 0,
            "bottom": max(box["maxbottom"],box["bottom"]+barcode.height) + self.settings["barcodeVSpacing"],
            "maxbottom": max(box["maxbottom"],box["bottom"]+barcode.height) + self.settings["barcodeVSpacing"]
         }
      if box["bottom"]+barcode.height+self.settings["pixelFontHeight"] > img.height:
         # Штрихкод выйдет за нижнюю рамку холста, если разместить его ниже, поэтому сообщаем, что newbox отсутствует
         newbox = None
         return img, newbox
      # Координаты следующего штрихкода - правее
      newbox = {
            "right": box["right"]+barcode.width + self.settings["barcodeHSpacing"],
            "bottom": box["bottom"],
            "maxbottom": max(box["maxbottom"],box["bottom"]+barcode.height)
      }
      # Вставляем сам штрихкод на холст
      currentbox = (box["right"], box["bottom"])
      img.paste(barcode, currentbox)

      # Создание подписи под штрихкодом
      if self.settings["addText"]:
         decodedBarcode = self.decodeBarcode(barcode)
         defaultFontHeight = 7 # константная высота символа из ImageFont.load_default(). Над символом есть ещё 2 пикселя, помимо этого
         defaultFontWidth = 6 # константная ширина символа из ImageFont.load_default()
         img_text = Image.new("1", (min(defaultFontWidth*len(decodedBarcode), barcode.width), defaultFontHeight), color="#ffffff")
         draw = ImageDraw.Draw(img_text)
         font = ImageFont.load_default()
         draw.text((0, -2), decodedBarcode, font=font)
         img_text = img_text.resize((img_text.width*self.settings["pixelFontHeight"]//defaultFontHeight, img_text.height*self.settings["pixelFontHeight"]//defaultFontHeight,))

         newbox["maxbottom"] = max(newbox["maxbottom"],newbox["bottom"]+barcode.height+img_text.height)
         centeredTextBox = (currentbox[0]+(barcode.width-img_text.width)//2, currentbox[1]+barcode.height+self.settings["marginText"])
         img.paste(img_text, centeredTextBox)

      return img, newbox

   def decodeBarcode(self, img):
      code = pyzbar.pyzbar.decode(img)
      if code:
         return code[0].data.decode("utf8")
      return " "

   def imageExtensions(self):
      images = []
      for ext in mimetypes.types_map:
         if mimetypes.types_map[ext].split('/')[0] == "image":
            images.append(ext)
      return images

   def isImage(self, url):
      if not url.isLocalFile():
         return False
      mimetype = mimetypes.guess_type(url.fileName(), strict=True)[0]
      if mimetype and mimetype.startswith('image/'):
         return True
      return False

   def addFile(self, path):
      if self.debug:
         print("adding file", path)
      normpath = os.path.normpath(path)
      if normpath not in self.list_items:
         self.list_items.append(normpath)
         self.listWidget_files.addItem(normpath)
      self.statusbar.showMessage(f"Добавлен файл {normpath}", self.statusbarTimeout)

   def removeFile(self, item):
      path = item.text()
      item_index = self.listWidget_files.indexFromItem(item).row()
      del(self.list_items[item_index])
      self.listWidget_files.removeItemWidget(self.listWidget_files.takeItem(item_index))
      self.statusbar.showMessage(f"Убрано {path}", self.statusbarTimeout)

   def clearList(self):
      self.list_items = []
      self.listWidget_files.clear()
      self.statusbar.showMessage(f"Список очищен", self.statusbarTimeout)

def main():
   app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
   window = MainWindow(app)  # Создаём объект класса ExampleApp
   window.show()  # Показываем окно
   app.exec()  # и запускаем приложение

def main2():
   barcode = Image.open(r"C:\Users\maste\Desktop\21505249_barcode.png")
   code = pyzbar.pyzbar.decode(barcode)
   print(code[0].data.decode("utf8"))

if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
   main()  # то запускаем функцию main()