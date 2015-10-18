"""
Create an ERD from a live PostgreSQL database in SVG format.

Requires a PostgreSQL connect string as argument on the command line.
"""

import sys
sys.path.append('..')
sys.path.append('../..')  # path to pg_jts

from pg_jts import pg_jts
import jts_erd

import json


def main(db_conn_str):
    """
    Generate an entity-relationship diagram for the given database.

    *db_conn_str* must be a valid PostgreSQL connect string.
    """
    relation_regexps = [
        '(^| )[Rr]ef to ',
        '(^| )[Rr]eference( to|s) ',
    ]
    exclude_tables_regexps = [
        '^tmp_.*$',
        '^temp_.*$',
        '^loc_.*$',
        '^tmp1_.*$',
        '^unused_.*$',
        '^studytmp_.*$',
    ]
    if db_conn_str:
        json_database_schema, notifications = pg_jts.get_database(
            db_conn_str,
            relation_regexps=relation_regexps,
            exclude_tables_regexps=exclude_tables_regexps
        )
        j = json.loads(json_database_schema)
    else:
        j = default_database
        notifications = []
    from pprint import pprint as print_
    print_(j, width=200)
    jts_erd.save_svg(
        j,
        '/tmp/jts_erd_tmp.svg',
        display_columns=True,
        display_indexes=True,
        omit_isolated_tables=True,
        rankdir='RL',
    )
    for n in notifications:
        print(n[0], n[1])


default_database = {'database_description': 'test',
 'database_name': 'testdb',
 'datapackages': [{'datapackage': 'public',
                   'resources': [{'description': 'communication channel',
                                  'fields': [{'constraints': {'required': False}, 'default_value': 'channel_id_seq()', 'name': 'id', 'type': 'int4'},
                                             {'constraints': {'required': True}, 'name': 'channel_type', 'type': 'chan'},
                                             {'constraints': {'required': True}, 'description': 'Channel attributes (specific to channel_type)', 'name': 'channel_attrs', 'type': 'jsonb'}],
                                  'foreignKeys': [],
                                  'indexes': [{'creation': 'CREATE UNIQUE INDEX channel_pkey ON channel USING btree (id)',
                                               'definition': 'btree (id)',
                                               'fields': ['id'],
                                               'name': 'channel_pkey',
                                               'primary': True,
                                               'unique': True}],
                                  'name': 'channel',
                                  'primaryKey': ['id']},
                                 {'fields': [{'constraints': {'required': False}, 'default_value': 'person_id_seq()', 'name': 'id', 'type': 'int4'},
                                             {'constraints': {'required': False}, 'name': 'name', 'type': 'varchar(100)'},
                                             {'constraints': {'required': True}, 'description': 'references channel(id) 1--1..N', 'name': 'channel_id', 'type': 'int4'}],
                                  'foreignKeys': [{'enforced': True,
                                                   'fields': ['channel_id'],
                                                   'reference': {'datapackage': 'public', 'fields': ['id'], 'name': 'person_channel_id_fkey', 'resource': 'channel'}}],
                                  'indexes': [{'creation': 'CREATE UNIQUE INDEX person_pkey ON person USING btree (id)',
                                               'definition': 'btree (id)',
                                               'fields': ['id'],
                                               'name': 'person_pkey',
                                               'primary': True,
                                               'unique': True},
                                              {'creation': 'CREATE INDEX person__name ON person USING btree (name)',
                                               'definition': 'btree (name)',
                                               'fields': ['name'],
                                               'name': 'person__name',
                                               'primary': False,
                                               'unique': False}],
                                  'name': 'person',
                                  'primaryKey': ['id']},
                                 {'fields': [{'constraints': {'required': False}, 'default_value': 'software_release_id_seq()', 'name': 'id', 'type': 'int4'},
                                             {'constraints': {'required': False}, 'name': 'software_name', 'type': 'varchar(100)'},
                                             {'constraints': {'required': True}, 'name': 'release_name', 'type': 'varchar(100)'},
                                             {'constraints': {'required': False}, 'name': 'major', 'type': 'int4'},
                                             {'constraints': {'required': False}, 'name': 'minor', 'type': 'int4'},
                                             {'constraints': {'required': False}, 'name': 'patch', 'type': 'int4'},
                                             {'constraints': {'required': True}, 'name': 'revision', 'type': 'varchar(50)'}],
                                  'foreignKeys': [],
                                  'indexes': [{'creation': 'CREATE UNIQUE INDEX software_release__version ON software_release USING btree (software_name, major, minor, patch)',
                                               'definition': 'btree (software_name, major, minor, patch)',
                                               'fields': ['software_name', 'major', 'minor', 'patch'],
                                               'name': 'software_release__version',
                                               'primary': False,
                                               'unique': True},
                                              {'creation': 'CREATE INDEX software_release__versions2 ON software_release USING btree (major, minor)',
                                               'definition': 'btree (major, minor)',
                                               'fields': ['major', 'minor'],
                                               'name': 'software_release__versions2',
                                               'primary': False,
                                               'unique': False},
                                              {'creation': 'CREATE INDEX software_release__versions3 ON software_release USING btree (major, minor, patch)',
                                               'definition': 'btree (major, minor, patch)',
                                               'fields': ['major', 'minor', 'patch'],
                                               'name': 'software_release__versions3',
                                               'primary': False,
                                               'unique': False},
                                              {'creation': 'CREATE UNIQUE INDEX software_release_pkey ON software_release USING btree (id)',
                                               'definition': 'btree (id)',
                                               'fields': ['id'],
                                               'name': 'software_release_pkey',
                                               'primary': True,
                                               'unique': True}],
                                  'name': 'software_release',
                                  'primaryKey': ['id'],
                                  'unique': [{'fields': ['software_name', 'major', 'minor', 'patch'], 'name': 'software_release__version'}]},
                                 {'description': 'changes of features for software releases; (major, minor) references software_release (major, minor) 1..N--1',
                                  'fields': [{'constraints': {'required': False}, 'default_value': 'feature_change_id_seq()', 'name': 'id', 'type': 'int4'},
                                             {'constraints': {'required': False}, 'name': 'description', 'type': 'text'},
                                             {'constraints': {'required': False}, 'name': 'major', 'type': 'int4'},
                                             {'constraints': {'required': False}, 'name': 'minor', 'type': 'int4'}],
                                  'foreignKeys': [],
                                  'indexes': [{'creation': 'CREATE UNIQUE INDEX feature_change_pkey ON feature_change USING btree (id)',
                                               'definition': 'btree (id)',
                                               'fields': ['id'],
                                               'name': 'feature_change_pkey',
                                               'primary': True,
                                               'unique': True}],
                                  'name': 'feature_change',
                                  'primaryKey': ['id']}]}],
 'generation_begin_time': '2015-10-18 13:30:20.086386+02',
 'generation_end_time': '2015-10-18 13:30:20.086386+02',
 'source': 'PostgreSQL',
 'source_version': '9.4.4'}


if __name__ == '__main__':
    import sys
    if len(sys.argv) <= 1:
        print('NOTE: you gave no PostgreSQL connection string as arg1')
        print('      Example: "dbname=SOMEDATABASE user=SOMEUSER password=SOMEPASSWORD port=5432 host=127.0.0.1"')
        print('      Therefore we use a default database schema example.')
        db_conn_str = None
    else:
        db_conn_str = sys.argv[1]
    main(db_conn_str)
    print('Please find the output in /tmp/jts_erd_tmp.svg and view it in your browser.')
