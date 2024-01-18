import configparser
import mimetypes
import os
import sys
#import tempfile

from PIL import Image, ImageDraw, ImageFont
import pyzbar.pyzbar

from PyQt5 import QtCore, QtWidgets, QtGui
import design

VERSION = "2023.7.8.442"

class MainWindow(QtWidgets.QMainWindow, design.Ui_MainWindow):
    def __init__(self, app):
        super().__init__()
        self.setupUi(self)

        # Устанавливаем текущую версию
        self.label_version.setText(VERSION)

        # Ключ дебага устанавливается из командной строки
        self.debug = False
        if "--debug" in app.arguments():
            self.debug = True

        self.pushButton_addFiles.clicked.connect(self.openFiles)
        self.pushButton_clearList.clicked.connect(self.clearList)
        self.pushButton_generatePrint.clicked.connect(self.generateFile)
        self.listWidget_files.viewport().installEventFilter(self)

        self.spinBox_widthA4.valueChanged.connect(self.setWidthA4)
        self.spinBox_heightA4.valueChanged.connect(self.setHeightA4)
        self.spinBox_barcodeVSpacing.valueChanged.connect(self.setBarcodeVSpacing)
        self.spinBox_barcodeHSpacing.valueChanged.connect(self.setBarcodeHSpacing)
        self.groupBox_barcodeDecoding.clicked.connect(self.setAddText)
        self.spinBox_pixelFontHeight.valueChanged.connect(self.setPixelFontHeight)
        self.spinBox_marginText.valueChanged.connect(self.setMarginText)
        self.pushButton_saveSettings.clicked.connect(self.saveSettings)

        self.list_items = []
        self.statusbarTimeout = 2000

        # Устанавливаем значения из настроек
        self.setSettings()

    def setSettings(self):
        '''
        Установка настроек приложения
        '''
        self.settings = {}

        try:
            # Устанавливаем настройки из файла
            config = configparser.ConfigParser()
            config.read('config.ini', encoding="utf-8")

            # размер холста
            self.settings["sizeA4"] = [config.getint('size','width'), config.getint('size','height')]
            self.spinBox_widthA4.setValue(self.settings["sizeA4"][0])
            self.spinBox_heightA4.setValue(self.settings["sizeA4"][1])

            # вертикальное расстояние между штрихкодами
            self.settings["barcodeVSpacing"] = config.getint('barcodeSpacing','barcodeVSpacing')
            self.spinBox_barcodeVSpacing.setValue(self.settings["barcodeVSpacing"])
            # горизонтальное расстояние между штрихкодами
            self.settings["barcodeHSpacing"] = config.getint('barcodeSpacing','barcodeHSpacing')
            self.spinBox_barcodeHSpacing.setValue(self.settings["barcodeHSpacing"])

            # добавлять ли подпись под штрихкодом
            self.settings["addText"] = config.getboolean('barcodeDecoding','addText')
            self.groupBox_barcodeDecoding.setChecked(self.settings["addText"])
            # высота подписи под штрихкодом
            self.settings["pixelFontHeight"] = config.getint('barcodeDecoding','pixelFontHeight')
            self.spinBox_pixelFontHeight.setValue(self.settings["pixelFontHeight"])
            # отступ подписи от штрихкода
            self.settings["marginText"] = config.getint('barcodeDecoding','marginText')
            self.spinBox_marginText.setValue(self.settings["marginText"])
        except (configparser.NoSectionError, configparser.NoOptionError) as e:
            if self.debug:
                print(e)

            # В крайнем случае устанавливаем на значения по умолчанию
            self.setDefaultSettings()

    def setDefaultSettings(self):
        '''
        Установка настроек по умолчанию
        '''
        config = configparser.ConfigParser()

        config.add_section('size')
        # размер холста
        self.settings["sizeA4"] = [1568, 2218]
        config.set('size','width',f"{self.settings['sizeA4'][0]}")
        config.set('size','height',f"{self.settings['sizeA4'][1]}")
        self.spinBox_widthA4.setValue(self.settings["sizeA4"][0])
        self.spinBox_heightA4.setValue(self.settings["sizeA4"][1])

        config.add_section('barcodeSpacing')
        # вертикальное расстояние между штрихкодами
        self.settings["barcodeVSpacing"] = 25
        config.set('barcodeSpacing','barcodeVSpacing',f"{self.settings['barcodeVSpacing']}")
        self.spinBox_barcodeVSpacing.setValue(self.settings["barcodeVSpacing"])
        # горизонтальное расстояние между штрихкодами
        self.settings["barcodeHSpacing"] = 0
        config.set('barcodeSpacing','barcodeHSpacing',f"{self.settings['barcodeHSpacing']}")
        self.spinBox_barcodeHSpacing.setValue(self.settings["barcodeHSpacing"])

        config.add_section('barcodeDecoding')
        # добавлять ли подпись под штрихкодом
        self.settings["addText"] = True
        config.set('barcodeDecoding','addText',f"{self.settings['addText']}")
        self.groupBox_barcodeDecoding.setChecked(self.settings["addText"])
        # высота подписи под штрихкодом
        self.settings["pixelFontHeight"] = 25
        config.set('barcodeDecoding','pixelFontHeight',f"{self.settings['pixelFontHeight']}")
        self.spinBox_pixelFontHeight.setValue(self.settings["pixelFontHeight"])
        # отступ подписи от штрихкода
        self.settings["marginText"] = 5
        config.set('barcodeDecoding','marginText',f"{self.settings['marginText']}")
        self.spinBox_marginText.setValue(self.settings["marginText"])

        with open('config.ini','w', encoding="utf-8") as f:
            config.write(f)

    def saveSettings(self):
        '''
        Сохранение текущих настроек в файл
        '''
        config = configparser.ConfigParser()

        config.add_section('size')
        # размер холста
        config.set('size','width',f"{self.settings['sizeA4'][0]}")
        config.set('size','height',f"{self.settings['sizeA4'][1]}")

        config.add_section('barcodeSpacing')
        # вертикальное расстояние между штрихкодами
        config.set('barcodeSpacing','barcodeVSpacing',f"{self.settings['barcodeVSpacing']}")
        # горизонтальное расстояние между штрихкодами
        config.set('barcodeSpacing','barcodeHSpacing',f"{self.settings['barcodeHSpacing']}")

        config.add_section('barcodeDecoding')
        # добавлять ли подпись под штрихкодом
        config.set('barcodeDecoding','addText',f"{self.settings['addText']}")
        # высота подписи под штрихкодом
        config.set('barcodeDecoding','pixelFontHeight',f"{self.settings['pixelFontHeight']}")
        # отступ подписи от штрихкода
        config.set('barcodeDecoding','marginText',f"{self.settings['marginText']}")

        with open('config.ini','w', encoding="utf-8") as f:
            config.write(f)

    def setWidthA4(self):
        '''
        Установка настройки ширины холста
        '''
        if self.debug:
            print("WidthA4", self.spinBox_widthA4.value())
        self.settings["sizeA4"][0] = self.spinBox_widthA4.value()

    def setHeightA4(self):
        '''
        Установка настройки высоты холста
        '''
        if self.debug:
            print("HeightA4", self.spinBox_heightA4.value())
        self.settings["sizeA4"][1] = self.spinBox_heightA4.value()

    def setBarcodeVSpacing(self):
        '''
        Установка настройки вертикального расстояния между штрихкодами
        '''
        if self.debug:
            print("VSpacing", self.spinBox_barcodeVSpacing.value())
        self.settings["barcodeVSpacing"] = self.spinBox_barcodeVSpacing.value()

    def setBarcodeHSpacing(self):
        '''
        Установка настройки горизонтального расстояния между штрихкодами
        '''
        if self.debug:
            print("HSpacing", self.spinBox_barcodeHSpacing.value())
        self.settings["barcodeHSpacing"] = self.spinBox_barcodeHSpacing.value()

    def setAddText(self):
        '''
        Установка настройки добавления подписи под штрихкодом
        '''
        if self.debug:
            print("addText", self.groupBox_barcodeDecoding.isChecked())
        self.settings["addText"] = self.groupBox_barcodeDecoding.isChecked()

    def setPixelFontHeight(self):
        '''
        Установка настройки высоты подписи под штрихкодом
        '''
        if self.debug:
            print("PixelFontHeight", self.spinBox_pixelFontHeight.value())
        self.settings["pixelFontHeight"] = self.spinBox_pixelFontHeight.value()

    def setMarginText(self):
        '''
        Установка настройки отступа подписи от штрихкода
        '''
        if self.debug:
            print("MarginText", self.spinBox_marginText.value())
        self.settings["marginText"] = self.spinBox_marginText.value()

    def openFiles(self):
        '''
        Добавление файлов через диалоговое окно
        '''
        # Подготавливаем список допустимых расширений для фильтра
        imageExtensions = " ".join(f"*{ext}" for ext in self.imageExtensions())
        # Собственно получение списка файлов
        files = QtWidgets.QFileDialog.getOpenFileNames(self, filter=f"Изображения ({imageExtensions})")[0]
        # Добавление файлов в список
        for file in files:
            self.addFile(file)
        if files:
            self.statusbar.showMessage("Файлы добавлены", self.statusbarTimeout)

    def eventFilter(self, source, event):
        '''
        Переопределённый метод отлавливания событий
        '''
        # Перемещение файлов на область списка файлов
        if (
            source is self.listWidget_files.viewport() and
            (
                event.type() in (
                    QtCore.QEvent.DragEnter,
                    QtCore.QEvent.DragMove,
                    QtCore.QEvent.Drop,
                )
            ) and
            event.mimeData().hasUrls()
        ):
            files_count = 0
            if event.type() == QtCore.QEvent.Drop:
                # Добавление файлов в список
                for url in event.mimeData().urls():
                    if self.isImage(url):
                        self.addFile(url.toLocalFile())
                        files_count += 1
            if files_count:
                self.statusbar.showMessage("Файлы добавлены", self.statusbarTimeout)
            event.accept()
            return True
        # Открытие контекстного меню в списке файлов
        elif (source is self.listWidget_files.viewport() and
            (event.type() in (QtCore.QEvent.ContextMenu,))):
            menu = QtWidgets.QMenu()
            menu_copy = QtWidgets.QAction("Копировать")
            menu_del = QtWidgets.QAction("Удалить")
            menu.addAction(menu_copy)
            menu.addAction(menu_del)

            # Получаем элемент, к которому вызвали меню
            try:
                item = self.listWidget_files.itemAt(event.pos())
            except Exception as e:
                if self.debug:
                    print(f"No item selected {e}")
                return False

            # Элемент не выбран => меню не открываем
            if not item: return False

            # Получаем действие, вызванное из контекстного меню
            menu_click = menu.exec(event.globalPos())

            # Копируем путь выбранного файла в буфер обмена
            if menu_click == menu_copy:
                if self.debug:
                    print("Скопировано", item)
                path = item.text()
                QtWidgets.QApplication.clipboard().setText(path)
                self.statusbar.showMessage(f"Скопировано {path}", self.statusbarTimeout)

            # Убираем выбранный файл из списка
            elif menu_click == menu_del:
                if self.debug:
                    print("Удалено", item)
                self.removeFile(item)

            event.accept()
            return True
        return super().eventFilter(source, event)

    def generateFile(self):
        '''
        Генерация изображения со скомпонованными на нём штрихкодами
        '''
        if self.debug:
            print("generate")

        # Работаем только при наличии списка файлов
        if self.list_items:
            # Подготавливаем список допустимых расширений для фильтра
            imageExtensions = " ".join(f"*{ext}" for ext in self.imageExtensions())

            # Выбираем место сохранения файла
            defaultFileName = "barcode.png"
            filePath = QtWidgets.QFileDialog.getSaveFileName(self, directory=defaultFileName, filter=f"Изображения ({imageExtensions});;Все файлы (*)")[0]

            if filePath:
                # Создание нового белого холста в чёрно-белом режиме
                img = Image.new("1", self.settings["sizeA4"], color="#ffffff")
                # Рисуем из верхнего левого угла
                box = {"right": 0, "bottom": 0, "maxbottom": 0}
                index_item = 0

                # Создаём временный файл
                #tempFilePath = tempfile.mktemp('.png')

                # Проходим по списку файлов со штрихкодами
                for barcodePath in self.list_items:
                    # Координаты указаны - холст есть
                    if box:
                #barcodePath = self.list_items[0]
                #while box:
                        index_item += 1
                        self.statusbar.showMessage(f"({index_item}/{len(self.list_items)}) Добавление на лист {barcodePath}", self.statusbarTimeout)
                        # Добавляем штрихкод на холст и обновляем координаты для следующего штрихкода
                        img, box = self.addBarcode(img, barcodePath, box)

                # Сохраняем изображение в файл
                img.save(filePath)

            self.statusbar.showMessage("Файл для печати создан", self.statusbarTimeout)

        else:
            self.statusbar.showMessage("Сначала добавьте файлы", self.statusbarTimeout)

    def addBarcode(self, img, barcodePath, box):
        '''
        Добавление штрихкода на холст
        img: холст, на который производится добавление
        barcodePath: путь к файлу со штрихкодом
        box: координаты, по которым нужно вставить штрихкод

        Возвращается пара (модифицированный холст, следующие координаты)
        '''
        # Открываем файл со штрихкодом
        barcode = Image.open(barcodePath)

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
            # Декодируем штрихкод - получаем его содержимое в виде строки, которую используем как подпись
            decodedBarcode = self.decodeBarcode(barcode)
            defaultFontHeight = 7 # константная высота символа из ImageFont.load_default(). Над символом есть ещё 2 пикселя, помимо этого
            defaultFontWidth = 6 # константная ширина символа из ImageFont.load_default()
            # Создаём белый холст для подписи по размеру надписи, но не шире ширины штрихкода
            img_text = Image.new("1", (min(defaultFontWidth*len(decodedBarcode), barcode.width), defaultFontHeight), color="#ffffff")
            # Пишем на холсте подписи саму надпись
            draw = ImageDraw.Draw(img_text)
            font = ImageFont.load_default()
            draw.text((0, -2), decodedBarcode, font=font)

            # Пропорционально изменяем изображение подписи до нужного нам размера pixelFontHeight, но не шире ширины штрихкода
            img_text_width = min(img_text.width*self.settings["pixelFontHeight"]//defaultFontHeight, barcode.width)
            img_text_height = img_text.height*img_text_width//img_text.width
            img_text = img_text.resize((img_text_width, img_text_height,))

            # Обновляем границу смещения штрихкода вниз с учётом подписи
            newbox["maxbottom"] = max(newbox["maxbottom"],newbox["bottom"]+barcode.height+img_text.height)
            # Сдвигаем подпись так, чтобы на общем холсте она была отцентрирована относитеельно штрихкода и находилась под ним на marginText расстоянии
            centeredTextBox = (currentbox[0]+(barcode.width-img_text.width)//2, currentbox[1]+barcode.height+self.settings["marginText"])
            # Добавляем подпись на холст
            img.paste(img_text, centeredTextBox)

        return img, newbox

    def decodeBarcode(self, img):
        '''
        Чтение строки, содержащейся в штрихкоде
        img: объект изображения

        Возвращается прочитанная строка
        '''
        code = pyzbar.pyzbar.decode(img)
        if code:
            return code[0].data.decode("utf8")
        # Если прочитать ничего не удалось, возвращаем пустую строку
        return " "

    def imageExtensions(self):
        '''
        Функция получения всех расширений файлов, соответствующих изображениям
        '''
        images = []
        # Просто проходим по списку MIME и забираем те расширения, что соответствуют image
        for ext in mimetypes.types_map:
            if mimetypes.types_map[ext].split('/')[0] == "image":
                images.append(ext)
        return images

    def isImage(self, url):
        '''
        Проверка файла по расширению, является ли он изображением
        url: путь к файлу

        Возвращается булево знначение
        '''
        # Только локальные файлы
        if not url.isLocalFile():
            return False
        mimetype = mimetypes.guess_type(url.fileName(), strict=True)[0]
        if mimetype and mimetype.startswith('image/'):
            return True
        return False

    def addFile(self, path):
        '''
        Добавление файлов в список
        path: путь к добавляемому файлу
        '''
        if self.debug:
            print("adding file", path)
        # Нормируем путь
        normpath = os.path.normpath(path)
        # Файлы, уже присутствующие в списке, не дублируем
        if normpath not in self.list_items:
            # Добавляем в список
            self.list_items.append(normpath)
            # Добавляем в отображаемый список
            self.listWidget_files.addItem(normpath)
        self.statusbar.showMessage(f"Добавлен файл {normpath}", self.statusbarTimeout)

    def removeFile(self, item):
        '''
        Удаление файлов из списка
        item: элемент отображаемого списка, который удаляем
        '''
        # Находим индекс элемента, соответствующий отображаемому и внутреннему списку
        path = item.text()
        item_index = self.listWidget_files.indexFromItem(item).row()
        # Удаляем элемент из внутреннего списка
        del self.list_items[item_index]
        # Удаляем элемент из отображаемого списка
        self.listWidget_files.removeItemWidget(self.listWidget_files.takeItem(item_index))
        self.statusbar.showMessage(f"Убрано {path}", self.statusbarTimeout)

    def clearList(self):
        '''
        Полная очистка списка
        '''
        self.list_items = []
        self.listWidget_files.clear()
        self.statusbar.showMessage("Список очищен", self.statusbarTimeout)

def main():
    app = QtWidgets.QApplication(sys.argv)  # Новый экземпляр QApplication
    window = MainWindow(app)  # Создаём объект класса ExampleApp
    window.show()  # Показываем окно
    app.exec()  # и запускаем приложение

if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    main()  # то запускаем функцию main()
