# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: mango
@contact: w4n9@sina.com
@create: 16/6/30
hail hydra!
"""

__author__ = "mango"
__version__ = "0.1"


from handlers.foo import FooHandler
from handlers.handler import UploadHandler, DownloadHandler

url_patterns = [
    (r"/foo", FooHandler),
    (r"/upload", UploadHandler),
    (r"/download/(.*)", DownloadHandler)
]
