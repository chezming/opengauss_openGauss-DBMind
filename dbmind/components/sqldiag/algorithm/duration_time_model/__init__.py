# Copyright (c) 2022 Huawei Technologies Co.,Ltd.
#
# openGauss is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#
#          http://license.coscl.org.cn/MulanPSL2
#
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
import abc


class AbstractModel:
    def __init__(self, params):
        self.params = params

    @abc.abstractmethod
    def fit(self, data):
        pass

    @abc.abstractmethod
    def transform(self, data):
        pass

    @abc.abstractmethod
    def load(self, filepath):
        pass

    @abc.abstractmethod
    def save(self, filepath):
        pass
