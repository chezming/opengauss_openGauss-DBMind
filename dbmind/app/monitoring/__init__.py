# Copyright (c) 2020 Huawei Technologies Co.,Ltd.
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

import logging

from dbmind import global_vars
from dbmind.common.utils import is_integer_string, cast_to_int_or_float
from dbmind.metadatabase.schema import config_dynamic_params


def get_default_dynamic_param(category, name):
    params = config_dynamic_params.DynamicParams.__default__.get(category)
    for _name, _value, _annotation in params:
        if _name == name:
            logging.warning(
                'Cannot get the %s parameter %s. '
                'DBMind used a default value %s as an alternative. '
                'Please check and update the dynamic configuration.',
                category, name, _value)
            return _value
    else:
        raise KeyError('The %s-%s is not even in the default dynamic configs. '
                       'Please check the category and name.', category, name)


def get_dynamic_param(category, name):
    try:
        value = global_vars.dynamic_configs.get(category, name)
    except AttributeError:
        value = None

    if value is None:
        value = get_default_dynamic_param(category, name)

    return value


def get_detection_param(name: str):
    value = get_dynamic_param('detection_params', name)
    if isinstance(value, (int, float)):
        return value
    elif isinstance(value, str):
        try:
            if is_integer_string(value):
                return int(value)
            return float(value)
        except (ValueError, TypeError):
            if value != "None":
                return value
    else:
        return None


def get_slow_sql_param(name: str):
    return cast_to_int_or_float(get_dynamic_param('slow_sql_threshold', name))


def get_detection_threshold(name: str) -> [float, int]:
    return cast_to_int_or_float(get_dynamic_param('detection_threshold', name))
