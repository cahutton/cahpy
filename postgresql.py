# -*- coding: utf_8 -*-
"""TODO."""

from collections import deque
from contextlib import contextmanager
# from operator import add
from re import compile as re_compile
# from time import sleep

from psycopg2 import connect, Error, OperationalError, ProgrammingError
from psycopg2.extensions import make_dsn
from psycopg2.extras import LoggingConnection, LoggingCursor
from psycopg2.sql import Identifier, Literal, SQL

from cahpy.log import ObjectWithLogger
from cahpy.system import ExitException


DEFAULT_ENCODING = 'utf_8'


class BetterLoggingConnection(LoggingConnection):
    """TODO."""

    def cursor(self, *args, **kwargs):
        """TODO."""
        return super().cursor(
            *args, cursor_factory=BetterLoggingCursor, **kwargs)

    def filter(self, message, cursor):
        """TODO."""
        if isinstance(message, bytes):
            message = message.decode(DEFAULT_ENCODING)

        return message

    def logAllLines(self, source, cursor, prefix='<\t'):
        """TODO."""
        for line in source.split('\n'):
            if line.strip():
                self.log(prefix + line, cursor)

    def logAllResponses(self, cursor):
        """TODO."""
        while self.notices:
            self.logAllLines(self.notices.popleft(), cursor)
        if cursor.statusmessage:
            self.logAllLines(cursor.statusmessage, cursor)


class BetterLoggingCursor(LoggingCursor):
    """TODO."""

    def callproc(self, procname, args=None):
        """TODO."""
        # self.connection.logAllLines(
        #     self.mogrify(procname, args).decode(DEFAULT_ENCODING), self,
        #     prefix='>\t')
        result = super().callproc(procname, args)
        self.connection.logAllResponses(self)

        return result

    def execute(self, query, args=None):
        """TODO."""
        # self.connection.logAllLines(
        #     self.mogrify(query, args).decode(DEFAULT_ENCODING), self,
        #     prefix='>\t')
        result = super().execute(query, args)
        self.connection.logAllResponses(self)

        return result


class Postgresql(ObjectWithLogger):
    """TODO."""

    ATTEMPTS = 10
    COPY_REGEX = re_compile(
        r'COPY ((?P<schemaName>.*)[.])?(?P<tableName>.*)'
        r' (?P<direction>TO|FROM) [\'](?P<source>.*)[\'] WITH (?P<options>.*)')
    ENCODING = 'UTF8'
    LOCALE = Identifier('en_US.UTF-8')
    LOGGER_NAME = 'Postgresql'
    SLEEP_TIME = 1  # s
    SYSTEM_DATABASES = [
        'postgres',
        'template0',
        'template1'
    ]
    SYSTEM_LANGUAGES = [
        'sql'
    ]
    SYSTEM_SCHEMATA = [
        'information_schema',
        'pg_catalog',
        'pg_toast',
        'public'
    ]
    SYSTEM_TABLESPACES = [
        'pg_default',
        'pg_global'
    ]
    SYSTEM_USERS = [
        'postgres',
        'pg_monitor',
        'pg_read_all_settings',
        'pg_read_all_stats',
        'pg_signal_backend',
        'pg_stat_scan_tables'
    ]
    TIMEOUT = 3  # s

    def __init__(self, dbname=None, user=None, password=None, host=None,
                 port=None):
        """TODO."""
        super().__init__()

        self.executed = False

        self.connect(dbname=dbname, user=user, password=password,
                     host=host, port=port)

    def __enter__(self):
        """TODO."""
        return self

    def __exit__(self, type, value, traceback):
        """TODO."""
        self.connection.close()
        self.logInfo('...connection closed.')

    def analyzeAll(self, verbose=True, **kwargs):
        """TODO."""
        '''
            ANALYZE VERBOSE;
        '''
        return self.execute(
            SQL('ANALYZE' + (' VERBOSE' if verbose else '')), True, **kwargs)

    def comment(self, objectType, name, comment, schemaName=None, **kwargs):
        """TODO."""
        if schemaName:
            name = Identifier(schemaName) + SQL('.') + Identifier(name)
        else:
            name = Identifier(name)

        return self.execute(
            SQL('COMMENT ON ' + objectType + ' ') + name + SQL(' IS ')
            + Literal(comment), **kwargs)

    def commentOnDatabase(self, name, comment, **kwargs):
        """TODO."""
        '''
            COMMENT ON DATABASE :"name"
                IS :'comment';
        '''
        return self.comment('DATABASE', name, comment, **kwargs)

    def commentOnRole(self, name, comment, **kwargs):
        """TODO."""
        '''
            COMMENT ON ROLE :"name"
                IS :'comment';
        '''
        return self.comment('ROLE', name, comment, **kwargs)

    def commentOnSchema(self, name, comment, **kwargs):
        """TODO."""
        '''
            COMMENT ON SCHEMA :"name"
                IS :'comment';
        '''
        return self.comment('SCHEMA', name, comment, **kwargs)

    def commentOnTable(self, name, comment, schemaName=None, **kwargs):
        """TODO."""
        '''
            COMMENT ON TABLE :"name"
                IS :'comment';
        '''
        return self.comment('TABLE', name, comment, schemaName, **kwargs)

    def commentOnTablespace(self, name, comment, **kwargs):
        """TODO."""
        '''
            COMMENT ON TABLESPACE :"name"
                IS :'comment';
        '''
        return self.comment('TABLESPACE', name, comment, **kwargs)

    def connect(self, dbname=None, user=None, password=None, host=None,
                port=None, attempts=ATTEMPTS):
        """TODO."""
        connection_kwargs = {
            'connect_timeout': self.TIMEOUT,
            'dbname': dbname,
            'host': host,
            'password': password,
            'port': port,
            'user': user
        }

        connectionString = make_dsn(**connection_kwargs)

        try:
            self.logInfo(
                'Connecting to '
                + self.getConnectionString(**connection_kwargs) + ' ('
                + connectionString + ')...')
            with connect(connectionString,
                         BetterLoggingConnection) as connection:
                if hasattr(self, 'connection'):
                    self.connection.close()
                self.connection = connection
                self.logInfo('...connected; configuring connection...')
                connection.initialize(self.logger)
                connection.notices = deque(connection.notices)
                connection.set_client_encoding(self.ENCODING)
                self.logInfo('...connection configured...')

                return self
        except OperationalError as error:
            self.logDebug(str(error))
            self.logDebug(str(error.pgcode))
            self.logError('...' + str(error.pgerror).strip() + '...')
            self.logError('...couldn\'t connect.')
            self.logDebug(connection_kwargs)

            raise ExitException()

    def create(self, objectType, names, schemaName=None, arguments=None,
               before=None, after=None, ifNotExists=False, **kwargs):
        """TODO."""
        if isinstance(names, str):
            names = [names]

        command = SQL('CREATE ' + objectType
                      + (' IF NOT EXISTS ' if ifNotExists else ' ')) \
            + SQL(', ').join([
                Identifier(schemaName) + SQL('.') + Identifier(name)
                if schemaName else Identifier(name)
                for name in names
            ])
        if before:
            command = before + SQL(' ') + command
        if arguments:
            command += SQL(' (') + SQL(', ').join(arguments) + SQL(')')
        if after:
            command += SQL(' ') + after

        return self.execute(command, **kwargs)

    def createDatabase(self, name, owner=None, template=None, encoding=None,
                       lcCollate=None, lcCtype=None, tablespace=None,
                       allowConnections=None, connectionLimit=None,
                       isTemplate=None, comment=None, überuser=None,
                       dropIfExists=None, **kwargs):
        """TODO."""
        '''
            CREATE DATABASE :"name"
                WITH
                    OWNER :"owner"
                    TEMPLATE :"template"
                    ENCODING :'encoding'
                    LC_COLLATE :"lcCollate"
                    LC_CTYPE :"lcCtype"
                    TABLESPACE :"tablespace"
                    ALLOW_CONNECTIONS TRUE
                    CONNECTION_LIMIT -1
                    IS_TEMPLATE TRUE;
        '''
        DEFAULT = SQL('DEFAULT')

        options = []
        if owner is not None:
            options.append(SQL('OWNER ') + (
                Identifier(owner) if owner else DEFAULT))
        if template is not None:
            options.append(SQL('TEMPLATE ') + (
                Identifier(template) if template else DEFAULT))
        if encoding is not None:
            options.append(SQL('ENCODING ') + Literal(
                encoding if encoding else self.ENCODING))
        if lcCollate is not None:
            options.append(SQL('LC_COLLATE ') + (
                Identifier(lcCollate) if lcCollate else self.LOCALE))
        if lcCtype is not None:
            options.append(SQL('LC_CTYPE ') + (
                Identifier(lcCtype) if lcCtype else self.LOCALE))
        if tablespace is not None:
            options.append(SQL('TABLESPACE ') + (
                Identifier(tablespace) if tablespace else DEFAULT))
        if allowConnections is not None:
            options.append(SQL('ALLOW_CONNECTIONS ' + (
                'TRUE' if allowConnections else 'FALSE')))
        if connectionLimit is not None:
            options.append(SQL('CONNECTION_LIMIT ' + (
                '-1' if connectionLimit is False else str(connectionLimit))))
        if isTemplate is not None:
            options.append(SQL('IS_TEMPLATE '
                               + ('TRUE' if isTemplate else 'FALSE')))
        options = SQL(' ').join(options)

        attempts = 1
        while attempts:
            try:
                create = self.create(
                    'DATABASE', name,
                    after=SQL('WITH ') + options if options else None,
                    transactionless=True, **kwargs)
            except ProgrammingError as error:
                self.logWarning(dropIfExists)
                if error.pgcode != '42P04' or not dropIfExists:
                    raise
                drop = self.dropDatabase(name, **kwargs)
                attempts += 1
            else:
                drop = None
            finally:
                attempts -= 1

        commands = [create]
        if drop:
            commands.prepend(drop)

        with self.startTransaction():
            if comment:
                commands.append(self.commentOnDatabase(name, comment,
                                                       **kwargs))
            if überuser:
                commands.append(
                    self.grantAllPrivilegesOnDatabase(name, überuser, True,
                                                      **kwargs))

        return commands

    def createExtension(self, name, schema=None, cascade=False, überuser=None,
                        **kwargs):
        """TODO."""
        '''
            CREATE EXTENSION IF NOT EXISTS :"name"
                WITH
                    SCHEMA :"schema"
                    CASCADE;
        '''
        if isinstance(name, str):
            name = [name]

        after = []
        if schema:
            after.append(SQL(' SCHEMA ') + Identifier(schema))
        if cascade:
            after.append(SQL(' CASCADE'))

        # FIXME
        # if after:
        #     after = SQL('WITH') + reduce(add, after)

        commands = []
        with self.startTransaction():
            for extension in name:
                commands.append(
                    self.create('EXTENSION', extension, after=after, **kwargs))
                if überuser:
                    if extension.endswith('_fdw'):
                        commands.append(
                            self.grantAllPrivilegesOnForeignDataWrapper(
                                extension, überuser, True, **kwargs))
                    elif extension.startswith('pl'):
                        commands.append(self.grantAllPrivilegesOnLanguage(
                            extension, überuser, True, **kwargs))

                    if extension == 'file_fdw':
                        commands.append(
                            self.createServer('filesystem', extension))

        return commands

    def createRole(self, name, superuser=False, createdb=False,
                   createrole=False, inherit=False, login=False,
                   replication=False, bypassrls=False, connectionLimit=None,
                   encryptedPassword=None, inRole=None, comment=None,
                   überuser=False, **kwargs):
        """TODO."""
        '''
            CREATE ROLE :"name"
                WITH
                    SUPERUSER
                    CREATEDB
                    CREATEROLE
                    INHERIT
                    LOGIN
                    REPLICATION
                    BYPASSRLS
                    CONNECTION LIMIT -1
                    ENCRYPTED PASSWORD :'encryptedPassword'
                    IN ROLE
                        "postgres",
                        "pg_monitor",
                        "pg_read_all_settings",
                        "pg_read_all_stats",
                        "pg_signal_backend",
                        "pg_stat_scan_tables";
        '''
        after = SQL('WITH')
        if superuser or überuser:
            after += SQL(' SUPERUSER')
        if createdb or überuser:
            after += SQL(' CREATEDB')
        if createrole or überuser:
            after += SQL(' CREATEROLE')
        if inherit or überuser:
            after += SQL(' INHERIT')
        if login or überuser:
            after += SQL(' LOGIN')
        if replication or überuser:
            after += SQL(' REPLICATION')
        if bypassrls or überuser:
            after += SQL(' BYPASSRLS')
        if connectionLimit is None and überuser:
            connectionLimit = -1
        if connectionLimit is not None:
            after += SQL(' CONNECTION LIMIT ' + str(connectionLimit))
        if encryptedPassword:
            after += SQL(' ENCRYPTED PASSWORD ') + Literal(encryptedPassword)
        if inRole:
            # TODO
            after += ()

        with self.startTransaction():
            commands = [self.create('ROLE', name, after=after, **kwargs)]
            if comment:
                commands.append(self.commentOnRole(name, comment, **kwargs))
            if überuser:
                commands += [
                    self.grantRole(self.SYSTEM_USERS, name, True, **kwargs),
                    self.grantAllPrivilegesOnTablespace(
                        self.SYSTEM_TABLESPACES, name, True, **kwargs),
                    self.grantAllPrivilegesOnDatabase(self.SYSTEM_DATABASES,
                                                      name, True, **kwargs),
                    self.grantAllPrivilegesOnLanguage(self.SYSTEM_LANGUAGES,
                                                      name, True, **kwargs),
                    self.grantAllPrivilegesOnSchema(self.SYSTEM_SCHEMATA, name,
                                                    True, überuser, **kwargs)
                ]

        return commands

    def createSchema(self, name, authorization=None, comment=None,
                     überuser=None, **kwargs):
        """TODO."""
        '''
            CREATE SCHEMA IF NOT EXISTS :"name"
                AUTHORIZATION :"authorization";
        '''
        with self.startTransaction():
            commands = [self.create(
                'SCHEMA', name,
                after=(SQL('AUTHORIZATION ') + Identifier(authorization))
                if authorization else None, **kwargs)]
            if comment:
                commands.append(self.commentOnSchema(name, comment, **kwargs))
            if überuser:
                commands += [
                    self.grantAllPrivilegesOnSchema(name, überuser, **kwargs),
                    self.grantAllPrivilegesOnAllFunctionsInSchema(
                        name, überuser, **kwargs),
                    self.grantAllPrivilegesOnAllSequencesInSchema(
                        name, überuser, **kwargs),
                    self.grantAllPrivilegesOnAllTablesInSchema(
                        name, überuser, **kwargs)
                ]

        return commands

    def createServer(self, serverName, foreignDataWrapper, comment=None,
                     **kwargs):
        """TODO."""
        '''
            CREATE SERVER :"name"
                FOREIGN DATA WRAPPER
        '''
        # TODO

    def createTable(self, name, columns=None, constraints=None,
                    schemaName=None, temporary=False, fillfactor='\'100\'',
                    comment=None, **kwargs):
        """TODO."""
        columns = [
            Identifier(column['name']) + SQL(' ' + column['type'])
            + SQL(' NOT NULL' if column['notNull'] else '')
            + SQL(' ').join('' for constraint in column.get('constraints', []))
            for column in columns
        ]
        constraints = []  # for constraint in constraints

        options = {}
        if fillfactor:
            options['fillfactor'] = fillfactor

        commands = [self.create(('TEMPORARY ' if temporary else '') + 'TABLE',
                                name, schemaName, columns + constraints,
                                after=SQL('WITH (') + SQL(', ').join(
                                    SQL(option + ' = ' + value)
                                    for option, value in options.items()
                                ) + SQL(')'), **kwargs)]
        # if geographyColumns:
        #     # TODO
        #     commands.append('SELECT AddGeometryColumn(' + Literal(schemaName)
        #                     + ', ' + Literal(name)
        #                     + ', \'geometry\', \'0\', \'MULTIPOLYGON\', 2);')
        if comment:
            commands.append(
                self.commentOnTable(name, comment, schemaName, **kwargs))

        return commands

    def createTablespace(self, name, location, owner=None, comment=None,
                         überuser=None, **kwargs):
        """TODO."""
        '''
            CREATE TABLESPACE :"name"
                OWNER :"owner"
                LOCATION :'location';
        '''
        after = SQL('LOCATION ') + Literal(location)
        if owner or überuser:
            after = SQL('OWNER ') + Identifier(owner or überuser) + SQL(' ') \
                + after

        with self.getCursor():
            commands = [self.create('TABLESPACE', name, after=after,
                                    transactionless=True, **kwargs)]
            if comment:
                commands.append(self.commentOnTablespace(name, comment,
                                                         **kwargs))
            if überuser:
                commands.append(
                    self.grantAllPrivilegesOnTablespace(name, überuser,
                                                        **kwargs))

        return commands

    def drop(self, objectType, names, schemaName=None, ifExists=True,
             **kwargs):
        """TODO."""
        if isinstance(names, str):
            names = [names]
        return self.execute(
            SQL('DROP ' + objectType + (' IF EXISTS ' if ifExists else ' '))
            + SQL(', ').join([
                Identifier(schemaName) + SQL('.') + Identifier(name)
                if schemaName else Identifier(name)
                for name in names
            ]), **kwargs)

    def dropDatabase(self, name, **kwargs):
        """TODO."""
        return self.drop('DATABASE', name, **kwargs)

    def dropSchema(self, name, **kwargs):
        """TODO."""
        return self.drop('SCHEMA', name, **kwargs)

    def dropTable(self, name, schemaName=None, **kwargs):
        """TODO."""
        return self.drop('TABLE', name, schemaName=schemaName, **kwargs)

    def execute(self, command, transactionless=None, getString=None):
        """TODO."""
        if transactionless:
            with self.getCursor() as cursor:
                if getString:
                    return command.as_string(cursor)
                else:
                    return cursor.execute(command)
        elif getString:
            return command.as_string(self.cursor)
        else:
            self.executed = True

            return self.cursor.execute(command)

    def getConnectionString(self, dbname=None, host=None, user=None,
                            password=None, port=None, **kwargs):
        """TODO."""
        '''
            postgresql://[[user[:password]@][netloc][:port][,...]][/dbname]
                [?param1=value1[&...]]
        '''
        connectionString = 'postgresql://'
        if user:
            connectionString += user
            if password:
                connectionString += ':' + password
            connectionString += '@'
        if host:
            connectionString += host
        if port:
            connectionString += ':' + port
        if dbname:
            connectionString += '/' + dbname
        if kwargs:
            connectionString += '?' + '&'.join([
                param + '=' + str(value) for param, value in kwargs.items()
            ])

        return connectionString

    @contextmanager
    def getCursor(self, withTransaction=False):
        """TODO."""
        self.connection.set_session(autocommit=not withTransaction)

        with self.connection.cursor() as cursor:
            try:
                self.cursor = cursor

                # try:
                yield cursor
                # except ProgrammingError as error:
                #     pass
                #     # handle dropIfExists
            except Error as error:
                self.logDebug(
                    (type(error), type(error).__name__, str(error.pgcode)))
                self.connection.logAllLines(error.pgerror.strip(), self.cursor)
                self.logInfo('...rolling back transaction...')
                self.connection.rollback()

                raise ExitException()
            else:
                if withTransaction and self.executed:
                    self.logInfo('...committing transaction...')
                    self.connection.commit()
                    self.logInfo('...transaction committed...')

    def grant(self, objectType, names, user, allPrivileges=None,
              withGrantOption=None, withAdminOption=None):
        """TODO."""
        if isinstance(names, str):
            names = [names]

        privileges = None
        if allPrivileges:
            privileges = SQL('ALL PRIVILEGES')

        grant = SQL(', ').join(Identifier(name) for name in names)
        if privileges:
            if objectType:
                privileges += SQL(' ON ' + objectType)
            grant = privileges + SQL(' ') + grant

        command = SQL('GRANT ') + grant + SQL(' TO ') + Identifier(user)
        if withGrantOption:
            command += SQL(' WITH GRANT OPTION')
        elif withAdminOption:
            command += SQL(' WITH ADMIN OPTION')

        return self.execute(command)

    def grantAllPrivilegesOnAllFunctionsInSchema(self, name, user,
                                                 withGrantOption=None):
        """TODO."""
        '''
            GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA :"name"
                TO :"user"
                WITH GRANT OPTION;
        '''
        return self.grantOnAllFunctionsInSchema(name, user, True,
                                                withGrantOption)

    def grantAllPrivilegesOnAllSequencesInSchema(self, name, user,
                                                 withGrantOption=None):
        """TODO."""
        '''
            GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA :"name"
                TO :"user"
                WITH GRANT OPTION;
        '''
        return self.grantOnAllSequencesInSchema(name, user, True,
                                                withGrantOption)

    def grantAllPrivilegesOnAllTablesInSchema(self, name, user,
                                              withGrantOption=None):
        """TODO."""
        '''
            GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA :"name"
                TO :"user"
                WITH GRANT OPTION;
        '''
        return self.grantOnAllTablesInSchema(name, user, True, withGrantOption)

    def grantAllPrivilegesOnDatabase(self, name, user, withGrantOption=None):
        """TODO."""
        '''
            GRANT ALL PRIVILEGES ON DATABASE :"name"
                TO :"user"
                WITH GRANT OPTION;
        '''
        return self.grantOnDatabase(name, user, True, withGrantOption)

    def grantAllPrivilegesOnForeignDataWrapper(self, name, user,
                                               withGrantOption=None):
        """TODO."""
        '''
            GRANT ALL PRIVILEGES ON FOREIGN DATA WRAPPER :"name"
                TO :"user"
                WITH GRANT OPTION;
        '''
        return self.grantOnForeignDataWrapper(name, user, True,
                                              withGrantOption)

    def grantAllPrivilegesOnLanguage(self, name, user, withGrantOption=None):
        """TODO."""
        '''
            GRANT ALL PRIVILEGES ON LANGUAGE :"name"
                TO :"user"
                WITH GRANT OPTION;
        '''
        return self.grantOnLanguage(name, user, True, withGrantOption)

    def grantAllPrivilegesOnSchema(self, name, user, withGrantOption=None,
                                   überuser=None):
        """TODO."""
        '''
            GRANT ALL PRIVILEGES ON SCHEMA :"name"
                TO :"überuser"
                WITH GRANT OPTION;
        '''
        commands = [self.grantOnSchema(name, user, True, withGrantOption)]
        if überuser:
            commands += [
                self.grantAllPrivilegesOnAllFunctionsInSchema(
                    name, user, True),
                self.grantAllPrivilegesOnAllSequencesInSchema(
                    name, user, True),
                self.grantAllPrivilegesOnAllTablesInSchema(name, user, True)
            ]

        return commands

    def grantAllPrivilegesOnTablespace(self, name, user, withGrantOption=None):
        """TODO."""
        '''
            GRANT ALL PRIVILEGES ON TABLESPACE :"name"
                TO :"user"
                WITH GRANT OPTION;
        '''
        return self.grantOnTablespace(name, user, True, withGrantOption)

    def grantOnAllFunctionsInSchema(self, name, user, allPrivileges=None,
                                    withGrantOption=None):
        """TODO."""
        return self.grant('ALL FUNCTIONS IN SCHEMA', name, user, allPrivileges,
                          withGrantOption)

    def grantOnAllSequencesInSchema(self, name, user, allPrivileges=None,
                                    withGrantOption=None):
        """TODO."""
        return self.grant('ALL SEQUENCES IN SCHEMA', name, user, allPrivileges,
                          withGrantOption)

    def grantOnAllTablesInSchema(self, name, user, allPrivileges=None,
                                 withGrantOption=None):
        """TODO."""
        return self.grant('ALL TABLES IN SCHEMA', name, user, allPrivileges,
                          withGrantOption)

    def grantOnDatabase(self, name, user, allPrivileges=None,
                        withGrantOption=None):
        """TODO."""
        return self.grant('DATABASE', name, user, allPrivileges,
                          withGrantOption)

    def grantOnForeignDataWrapper(self, name, user, allPrivileges=None,
                                  withGrantOption=None):
        """TODO."""
        return self.grant('FOREIGN DATA WRAPPER', name, user, allPrivileges,
                          withGrantOption)

    def grantOnLanguage(self, name, user, allPrivileges=None,
                        withGrantOption=None):
        """TODO."""
        return self.grant('LANGUAGE', name, user, allPrivileges,
                          withGrantOption)

    def grantOnSchema(self, name, user, allPrivileges=None,
                      withGrantOption=None):
        """TODO."""
        return self.grant('SCHEMA', name, user, allPrivileges, withGrantOption)

    def grantOnTablespace(self, name, user, allPrivileges=None,
                          withGrantOption=None):
        """TODO."""
        return self.grant('TABLESPACE', name, user, allPrivileges,
                          withGrantOption)

    def grantRole(self, name, user, withAdminOption=None):
        """TODO."""
        '''
            GRANT :"name"
                TO :"user"
                WITH ADMIN OPTION;
        '''
        return self.grant(None, name, user, withAdminOption=withAdminOption)

    def insert(self, tableName, rowsType, values, schemaName=None,
               columnNames=None, **kwargs):
        """TODO."""
        columnNames = [
            Identifier(columnName) for columnName in columnNames
        ]

        command = SQL('INSERT INTO') \
            + (SQL(' ') + Identifier(schemaName) + SQL('.')
               if schemaName else SQL(' ')) + Identifier(tableName) \
            + (SQL(' (') + SQL(', ').join(columnNames) + SQL(') ')
               if columnNames else SQL(' ')) + SQL(rowsType + ' (%s)')

        return self.execute(command, values, **kwargs)

    def insertValues(self, tableName, values, schemaName=None,
                     columnNames=None, **kwargs):
        """TODO."""
        return self.insert(tableName, 'VALUES', values, schemaName,
                           columnNames, **kwargs)

    def run(self, filePath):
        """TODO."""
        with open(str(filePath), 'r') as inputFile:
            commands = inputFile.read().split(';')

        results = []
        with self.getCursor() as cursor:
            for command in commands:
                command = command.strip().strip('\r')
                while command.startswith('\\') or command.startswith('--'):
                    try:
                        command = command.split('\n', maxsplit=1)[1]
                    except IndexError:
                        command = ''

                if command:
                    if command.startswith('COPY'):
                        commandParts = self.COPY_REGEX.match(command)
                        isCopyTo = commandParts.group('direction') == 'TO'
                        source = commandParts.group('source')
                        with open(source, 'w' if isCopyTo else 'r') as file:
                            command = command.replace(
                                '\'' + source + '\'',
                                'STDOUT' if isCopyTo else 'STDIN')
                            self.logDebug(command)
                            cursor.copy_expert(command, file)
                    else:
                        results.append(cursor.execute(command))

        return results

    def startTransaction(self):
        """TODO."""
        return self.getCursor(True)

    def vacuumAll(self, verbose=True, full=True, getString=None):
        """TODO."""
        '''
            VACUUM (FULL, FREEZE, VERBOSE);
        '''
        if full:
            options = ['FULL', 'FREEZE']
        else:
            options = ['FREEZE', 'DISABLE_PAGE_SKIPPING']

        if verbose:
            options += ['VERBOSE']

        command = SQL('VACUUM' + (' (' + ', '.join(options) + ')'
                                  if options else ''))

        return self.execute(command, True)

    def vacuumAnalyzeAll(self, verbose=True, full=True):
        """TODO."""
        self.vacuumAll(verbose, full)
        self.analyzeAll(verbose)
