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

from dbmind.metadatabase.ddl import truncate_table
from ..result_db_session import get_session
from ..schema import HealingRecords


def insert_healing_record(
        instance,
        trigger_events,
        trigger_root_causes,
        action,
        called_method,
        success,
        detail,
        occurrence_at
):
    with get_session() as session:
        session.add(
            HealingRecords(
                instance=instance,
                trigger_events=trigger_events,
                trigger_root_causes=trigger_root_causes,
                action=action,
                called_method=called_method,
                success=success,
                detail=detail,
                occurrence_at=occurrence_at
            )
        )


def select_healing_records(instance=None, action=None, success=None, min_occurrence=None, offset=None, limit=None):
    with get_session() as session:
        result = session.query(HealingRecords)
        if action is not None:
            result = result.filter(HealingRecords.action == action)
        if success is not None:
            result = result.filter(HealingRecords.success == success)
        if instance is not None:
            if type(instance) in (tuple, list):
                result = result.filter(HealingRecords.instance.in_(instance))
            else:
                result = result.filter(HealingRecords.instance == instance)
        if min_occurrence is not None:
            result = result.filter(
                HealingRecords.occurrence_at >= min_occurrence
            )
        result = result.order_by(HealingRecords.occurrence_at)
        if offset is not None:
            result = result.offset(offset)
        if limit is not None:
            result = result.limit(limit)
        return result


def count_healing_records(instance=None, action=None, success=None, min_occurrence=None):
    return select_healing_records(instance, action, success, min_occurrence).count()


def delete_timeout_healing_records(oldest_occurrence_time):
    with get_session() as session:
        session.query(HealingRecords).filter(
            HealingRecords.occurrence_at <= oldest_occurrence_time
        ).delete()


def truncate_history_alarm():
    truncate_table(HealingRecords.__tablename__)
