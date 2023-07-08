from setuptools import setup
from setuptools import find_packages

setup(
  name = "barcode_merger",
  description = "Данное приложение позволяет объединить несколько файлов-изображений со штрихкодами в один лист, готовый для печати.",
  url = "https://github.com/Atronar/barcode_merger",
  version = "2023.7.8.442",
  author = "ATroN",
  author_email = "master.atron@gmail.com",
  python_requires='>=3.8',
  packages = find_packages(),
  install_requires = ["PyQt5","mimetypes","Pillow","pyzbar"],
  include_package_data = True,
  classifiers = [
    "Development Status :: 3 - Alpha",
    "Operating System :: OS Independent",
    "Topic :: Office/Business",
    "Programming Language :: Python :: 3",
    "Natural Language :: Russian",
    "License :: OSI Approved :: The Unlicense (Unlicense)"
  ]
)
