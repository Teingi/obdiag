#!/usr/bin/env python
# -*- coding: UTF-8 -*
# Copyright (c) 2022 OceanBase
# OceanBase Diagnostic Tool is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#          http://license.coscl.org.cn/MulanPSL2
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
"""
@time: 2024/08/21
@file: result_type.py
@desc:
"""
import json


class ObdiagResult:
    # ObdiagResult is the result of obdiag.
    # It contains the code and result of obdiag.

    # SERVER_ERROR_CODE(5xx) is the code of server error.
    SERVER_ERROR_CODE = 500
    # INPUT_ERROR_CODE(4xx) is the code of input error.
    INPUT_ERROR_CODE = 400
    # SUCCESS_CODE(200) is the code of success.
    SUCCESS_CODE = 200

    def __init__(self, code, data=None, error_data=None):
        self.command = None
        self.trace_id = None
        self.data = data
        self.error_data = error_data
        if code is None:
            raise TypeError("ObdiagResult code is None. Please contact the Oceanbase community. ")
        self.code = code
        if data is not None:
            if isinstance(data, dict):
                self.data = data
            else:
                raise TypeError("ObdiagResult data is not dict. Please contact the Oceanbase community. ")
        if error_data is not None:
            if isinstance(error_data, str):
                self.error_data = error_data
            else:
                raise TypeError("ObdiagResult error_data is not str. Please contact the Oceanbase community. ")

    def set_trace_id(self, trace_id):
        self.trace_id = "{0}".format(trace_id)

    def set_command(self, command):
        self.command = command

    def get_result(self):
        result = {"code": self.code, "data": self.data, "error_data": self.error_data, "trace_id": self.trace_id, "command": self.command}
        return json.dumps(result, ensure_ascii=False)

    def _json_to_markdown(self, obj, indent=0):
        """将JSON对象转换为Markdown格式"""
        if obj is None:
            return "`null`"
        elif isinstance(obj, (str, int, float, bool)):
            return f"`{obj}`"
        elif isinstance(obj, list):
            if not obj:
                return "`[]`"
            md_lines = []
            for i, item in enumerate(obj):
                md_lines.append(f"{'  ' * indent}- {self._json_to_markdown(item, indent + 1)}")
            return "\n".join(md_lines)
        elif isinstance(obj, dict):
            if not obj:
                return "`{}`"
            md_lines = []
            for key, value in obj.items():
                if isinstance(value, (dict, list)) and value:
                    md_lines.append(f"{'  ' * indent}- **{key}**:")
                    md_lines.append(self._json_to_markdown(value, indent + 1))
                else:
                    md_lines.append(f"{'  ' * indent}- **{key}**: {self._json_to_markdown(value, indent + 1)}")
            return "\n".join(md_lines)
        else:
            return f"`{str(obj)}`"

    def get_result_md(self):
        result = {"code": self.code, "data": self.data, "error_data": self.error_data, "trace_id": self.trace_id, "command": self.command}
        result_data = json.dumps(result, ensure_ascii=False)

        # 转换为Markdown格式
        md_content = "# Obdiag Result\n\n"
        md_content += self._json_to_markdown(result)

        return md_content

    def get_code(self):
        return self.code

    def is_success(self):
        return self.code == self.SUCCESS_CODE
