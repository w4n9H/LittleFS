# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@author: mango
@contact: w4n9@sina.com
@create: 16/7/7
hail hydra!
"""

__author__ = "mango"
__version__ = "0.1"


import os
import json
import tornado.web
import tornado.gen
from tornado.web import HTTPError
from post_streamer import PostDataStreamer
from base import BaseHandler

import logging
logger = logging.getLogger('littlefs.' + __name__)


# noinspection PyAbstractClass,PyAttributeOutsideInit
@tornado.web.stream_request_body
class UploadHandler(BaseHandler):
    def initialize(self):
        self.set_header('Content-type', 'application/json')
        self.upload_dir = self.settings.get('fs_dir')
        if not os.path.exists(self.upload_dir):
            os.mkdir(self.upload_dir)
        self.file_tmp_path = None
        self.res_status = dict()
        self.file_info = dict()

    @tornado.gen.coroutine
    def prepare(self):
        """
        第二步执行,读取请求头
        :return:
        """
        try:
            total = int(self.request.headers.get("Content-Length", "0"))
        except:
            total = 0
        self.ps = PostDataStreamer(total, self.upload_dir)

    @tornado.gen.coroutine
    def data_received(self, chunk):
        """
        第三步执行,写文件
        :param chunk: 文件内容
        :return:
        """
        self.ps.receive(chunk)

    @tornado.gen.coroutine
    @tornado.web.asynchronous
    def post(self, *args, **kwargs):
        """
        第四步执行,获取文件信息,上传写数据库,销毁文件
        :param args:
        :param kwargs:
        :return:
        """
        file_name = self.get_argument('filename', default=None, strip=True)
        try:
            self.ps.finish_receive()
            # 获取文件信息
            for idx, part in enumerate(self.ps.parts):
                self.file_info['file_size'] = part.get('size', 0)
                self.file_tmp_path = part.get("tmpfile").name
                for header in part["headers"]:
                    params = header.get("params", None)
                    if params:
                        if file_name:
                            self.file_info['file_name'] = file_name
                        else:
                            self.file_info['file_name'] = params.get("filename", "")
            os.rename(self.file_tmp_path,
                      os.path.join(self.settings.get('static_path'), self.file_info.get('file_name')))
            self.res_status['status'], self.res_status['result'] = 0, self.file_info['file_name']
        except Exception as error:
            logging.error(str(error))
            self.res_status['status'], self.res_status['result'] = 1, str(error)
        finally:
            self.file_info.clear()
            # self.ps.release_parts()    # 删除处理
            self.write(json.dumps(self.res_status))
            self.finish()


# noinspection PyAbstractClass
class DownloadHandler(BaseHandler):
    def initialize(self):
        self.set_header('Content-Type', 'application/octet-stream')

    @tornado.gen.coroutine
    @tornado.web.asynchronous
    def get(self, file_name):
        try:
            self.set_header('Content-Disposition', 'attachment; filename=%s' % file_name)
            file_path = os.path.join(self.settings.get('static_path'), file_name)
            if not file_name or not os.path.exists(file_path):
                raise HTTPError(404)
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(self.settings.get('buf_size'))
                    if data:
                        self.write(data)
                    else:
                        self.finish()
                        return
        except Exception as error:
            logging.error(str(error))
            raise HTTPError(404)
        finally:
            self.finish()