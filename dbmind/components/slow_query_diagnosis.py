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
import argparse
import os
import sys
import time
import traceback
import logging
from getpass import getpass

from prettytable import PrettyTable

from dbmind import constants
from dbmind import global_vars
from dbmind.cmd.config_utils import DynamicConfig
from dbmind.cmd.config_utils import load_sys_configs
from dbmind.common.utils.checking import path_type, date_type
from dbmind.common.utils.cli import keep_inputting_until_correct, write_to_terminal
from dbmind.metadatabase.dao import slow_queries
from dbmind.service.utils import is_rpc_valid, is_tsdb_valid
from dbmind.common.utils.exporter import set_logger


def _initialize_rpc_service():
    from dbmind.common.rpc import RPCClient
    from dbmind.common.utils import read_simple_config_file
    from dbmind.constants import METRIC_MAP_CONFIG
    global_vars.metric_map = read_simple_config_file(
        METRIC_MAP_CONFIG
    )
    # Initialize RPC components.
    master_url = global_vars.configs.get('AGENT', 'master_url')
    ssl_certfile = global_vars.configs.get('AGENT', 'ssl_certfile')
    ssl_keyfile = global_vars.configs.get('AGENT', 'ssl_keyfile')
    ssl_keyfile_password = global_vars.configs.get('AGENT', 'ssl_keyfile_password')
    ssl_ca_file = global_vars.configs.get('AGENT', 'ssl_ca_file')
    agent_username = global_vars.configs.get('AGENT', 'username')
    agent_pwd = global_vars.configs.get('AGENT', 'password')
    global_vars.agent_rpc_client = RPCClient(
        master_url,
        username=agent_username,
        pwd=agent_pwd,
        ssl_cert=ssl_certfile,
        ssl_key=ssl_keyfile,
        ssl_key_password=ssl_keyfile_password,
        ca_file=ssl_ca_file
    )
    return is_rpc_valid()


def _initialize_tsdb_param():
    from dbmind.common.tsdb import TsdbClientFactory
    try:
        TsdbClientFactory.set_client_info(
            global_vars.configs.get('TSDB', 'name'),
            global_vars.configs.get('TSDB', 'host'),
            global_vars.configs.get('TSDB', 'port'),
            global_vars.configs.get('TSDB', 'username'),
            global_vars.configs.get('TSDB', 'password'),
            global_vars.configs.get('TSDB', 'ssl_certfile'),
            global_vars.configs.get('TSDB', 'ssl_keyfile'),
            global_vars.configs.get('TSDB', 'ssl_keyfile_password'),
            global_vars.configs.get('TSDB', 'ssl_ca_file')
        )
        return is_tsdb_valid()
    except Exception as e:
        logging.warning(e)
        return False


def _initialize_driver(driver, url):
    try:
        driver.initialize(url)
        return True
    except ConnectionError:
        logging.warning("Error occurred when initialized URL.")
        return False


def _is_database_exist(database, data_source='tsdb', driver=None):
    stmt = "select datname from pg_database where datname = '%s'" % database
    if data_source == 'tsdb':
        rows = global_vars.agent_rpc_client.call('query_in_database',
                                                 stmt,
                                                 database,
                                                 return_tuples=True)
    else:
        rows = driver.query(stmt, return_tuples=True)
    if rows:
        return True
    return False


def _is_schema_exist(schema, database=None, data_source='tsdb', driver=None):
    stmt = "select nspname from pg_namespace where nspname = '%s'" % schema
    if data_source == 'tsdb':
        rows = global_vars.agent_rpc_client.call('query_in_database',
                                                 stmt,
                                                 database,
                                                 return_tuples=True)
    else:
        rows = driver.query(stmt, return_tuples=True)
    if rows:
        return True
    return False


def _check_tsdb_configuration(database, schema):
    if not _initialize_rpc_service():
        write_to_terminal('RPC service not exists, exiting...', color='red')
        sys.exit()
    if not _initialize_tsdb_param():
        write_to_terminal('TSDB service not exists, exiting...', color='red')
        sys.exit()
    if database is None:
        write_to_terminal("Lack the information of 'database', exiting...", color='red')
        sys.exit()
    if not _is_database_exist(database, data_source='tsdb'):
        write_to_terminal("Database '%s' does not exist, exiting..." % database, color='red')
        sys.exit()
    if schema is not None and not _is_schema_exist(schema, database=database, data_source='tsdb'):
        write_to_terminal("Schema '%s' does not exist, exiting..." % schema, color='red')
        sys.exit()


def _check_driver_configuration(url, schema, driver):
    if not _initialize_driver(driver, url):
        write_to_terminal("Error occurred when initialized the URL, exiting...", color='red')
        sys.exit()
    if schema is not None and not _is_schema_exist(schema, data_source='driver', driver=driver):
        write_to_terminal("Schema '%s' does not exist, exiting..." % schema, color='red')
        sys.exit()


def show(query, start_time, end_time):
    field_names = (
        'slow_query_id', 'schema_name', 'db_name',
        'query', 'start_at', 'duration_time',
        'root_cause', 'suggestion'
    )
    output_table = PrettyTable()
    output_table.field_names = field_names

    result = slow_queries.select_slow_queries(field_names, query, start_time, end_time)
    nb_rows = 0
    for slow_query in result:
        row = [getattr(slow_query, field) for field in field_names]
        output_table.add_row(row)
        nb_rows += 1

    if nb_rows > 50:
        write_to_terminal('The number of rows is greater than 50. '
                          'It seems too long to see.')
        char = keep_inputting_until_correct('Do you want to dump to a file? [Y]es, [N]o.', ('Y', 'N'))
        if char == 'Y':
            dump_file_name = 'slow_queries_%s.txt' % int(time.time())
            with open(dump_file_name, 'w+') as fp:
                fp.write(str(output_table))
            write_to_terminal('Dumped file is %s.' % os.path.realpath(dump_file_name))
        elif char == 'N':
            print(output_table)
            print('(%d rows)' % nb_rows)
    else:
        print(output_table)
        print('(%d rows)' % nb_rows)


def clean(retention_days):
    if retention_days is None:
        slow_queries.truncate_slow_queries()
        slow_queries.truncate_killed_slow_queries()
    else:
        start_time = int((time.time() - float(retention_days) * 24 * 60 * 60) * 1000)
        slow_queries.delete_slow_queries(start_time)
        slow_queries.delete_killed_slow_queries(start_time)
    write_to_terminal('Success to delete redundant results.')


def diagnosis(query, database, schema=None, start_time=None, end_time=None, url=None, data_source='tsdb'):
    driver = None
    if data_source == 'tsdb':
        _check_tsdb_configuration(database, schema)
    if data_source == 'driver':
        from dbmind.components.opengauss_exporter.core.opengauss_driver import Driver
        driver = Driver()
        _check_driver_configuration(url, schema, driver)
    if schema is None:
        write_to_terminal("Lack the information of 'schema', use default value: 'public'.", color='yellow')
        schema = 'public'

    from dbmind.service.web import toolkit_slow_sql_rca
    field_names = ('root_cause', 'suggestion')
    output_table = PrettyTable()
    output_table.field_names = field_names
    output_table.align = "l"
    root_causes, suggestions = toolkit_slow_sql_rca(query=query,
                                                    dbname=database,
                                                    schema=schema,
                                                    start_time=start_time,
                                                    end_time=end_time,
                                                    url=url,
                                                    data_source=data_source,
                                                    driver=driver)
    for root_cause, suggestion in zip(root_causes[0], suggestions[0]):
        output_table.add_row([root_cause, suggestion])
    print(output_table)


def get_plan(query, database, schema=None, url=None, data_source='tsdb'):
    driver = None
    if data_source == 'tsdb':
        _check_tsdb_configuration(database, schema)
    if data_source == 'driver':
        from dbmind.components.opengauss_exporter.core.opengauss_driver import Driver
        driver = Driver()
        _check_driver_configuration(url, schema, driver)
    if schema is None:
        write_to_terminal("Lack the information of 'schema', use default value: 'public'.", color='yellow')
        schema = 'public'

    from dbmind.service.web import toolkit_get_query_plan
    output_table = PrettyTable()
    field_names = ('normalized', 'plan')
    output_table.field_names = field_names
    output_table.align = "l"
    query_plan, query_type = toolkit_get_query_plan(query=query,
                                                    database=database,
                                                    schema=schema,
                                                    url=url,
                                                    data_source=data_source,
                                                    driver=driver)
    if query_type == 'normalized':
        output_table.add_row([True, query_plan])
    else:
        output_table.add_row([False, query_plan])
    print(output_table)


def main(argv):
    parser = argparse.ArgumentParser(description='Slow Query Diagnosis: Analyse the root cause of slow query')
    parser.add_argument('action', choices=('show', 'clean', 'diagnosis', 'get_plan'),
                        help='choose a functionality to perform')
    parser.add_argument('-c', '--conf', metavar='DIRECTORY', required=True, type=path_type,
                        help='Set the directory of configuration files')
    parser.add_argument('--database', metavar='DATABASE',
                        help='Set the name of database')
    parser.add_argument('--schema', metavar='SCHEMA',
                        help='Set the schema of database')
    parser.add_argument('--query', metavar='SLOW_QUERY',
                        help='Set a slow query you want to retrieve')
    parser.add_argument('--start-time', metavar='TIMESTAMP_IN_MICROSECONDS', type=date_type,
                        help='Set the start time of a slow SQL diagnosis result to be retrieved')
    parser.add_argument('--end-time', metavar='TIMESTAMP_IN_MICROSECONDS', type=date_type,
                        help='Set the end time of a slow SQL diagnosis result to be retrieved')
    parser.add_argument('--url', metavar='DSN of database',
                        help="set database dsn('postgres://user@host:port/dbname' or "
                             "'user=user dbname=dbname host=host port=port') "
                             "when tsdb is not available. Note: don't contain password in DSN. Using in diagnosis.")
    parser.add_argument('--data-source', choices=('tsdb', 'driver'), metavar='data source of SLOW-SQL-RCA',
                        help='set database dsn when tsdb is not available. Using in diagnosis.')
    parser.add_argument('--retention-days', metavar='DAYS', type=float,
                        help='clear historical diagnosis results and set '
                             'the maximum number of days to retain data')

    args = parser.parse_args(argv)
    if not os.path.exists(args.conf):
        parser.exit(1, 'Not found the directory %s.\n' % args.conf)

    if args.action == 'show':
        if None in (args.query, args.start_time, args.end_time):
            write_to_terminal('There may be a lot of results because you did not use all filter conditions.',
                              color='red')
            inputted_char = keep_inputting_until_correct('Press [A] to agree, press [Q] to quit:', ('A', 'Q'))
            if inputted_char == 'Q':
                parser.exit(0, "Quitting due to user's instruction.\n")
    elif args.action == 'clean':
        if args.retention_days is None:
            write_to_terminal('You did not specify retention days, so we will delete all historical results.',
                              color='red')
            inputted_char = keep_inputting_until_correct('Press [A] to agree, press [Q] to quit:', ('A', 'Q'))
            if inputted_char == 'Q':
                parser.exit(0, "Quitting due to user's instruction.\n")
    elif args.action in ('diagnosis', 'get_plan'):
        if args.query is None or not len(args.query.strip()):
            write_to_terminal('You did noy specify query, so we cant not diagnosis root cause.')
            parser.exit(1, "Quiting due to lack of query.\n")
        if args.data_source == 'driver':
            from psycopg2.extensions import parse_dsn
            if args.url is None:
                parser.exit(1, "Quiting due to lack of URL.\n")
            try:
                parsed_dsn = parse_dsn(args.url)
                if 'password' in parsed_dsn:
                    parser.exit(1, "Quiting due to security considerations.\n")
                password = getpass('Please input the password in URL:')
                parsed_dsn['password'] = password
                args.url = ' '.join(['{}={}'.format(k, v) for (k, v) in parsed_dsn.items()])
            except Exception:
                parser.exit(1, "Quiting due to wrong URL format.\n")

    # Set the global_vars so that DAO can login the meta-database.
    os.chdir(args.conf)
    global_vars.configs = load_sys_configs(constants.CONFILE_NAME)
    set_logger(os.path.join('logs', constants.SLOW_SQL_RCA_LOG_NAME), "info")
    try:
        if args.action == 'show':
            show(args.query, args.start_time, args.end_time)
        elif args.action == 'clean':
            clean(args.retention_days)
        elif args.action == 'diagnosis':
            global_vars.dynamic_configs = DynamicConfig
            diagnosis(args.query, args.database, args.schema,
                      start_time=args.start_time, end_time=args.end_time, url=args.url, data_source=args.data_source)
        elif args.action == 'get_plan':
            get_plan(args.query, args.database, args.schema, url=args.url, data_source=args.data_source)
    except Exception as e:
        write_to_terminal('An error occurred probably due to database operations, '
                          'please check database configurations. For details:\n' +
                          str(e), color='red', level='error')
        traceback.print_tb(e.__traceback__)
        return 2
    return args


if __name__ == '__main__':
    main(sys.argv[1:])
