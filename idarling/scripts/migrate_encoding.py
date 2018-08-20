# quick and dirty database migration for msgpack

from __future__ import print_function

import os
import msgpack


import idarling
from idarling.shared.database import Database


def encode_values(obj):
    if isinstance(obj, list):
        return [encode_values(elt) for elt in obj]

    if isinstance(obj, dict):
        return {k: encode_values(v) for k, v in obj.items()}

    if isinstance(obj, str):
        return str.encode('utf8')

    return obj


def find_database():
    db_path = os.path.join(
        os.path.dirname(idarling.__file__),
        'files',
        'database.db')
    if os.path.exists(db_path):
        return os.path.abspath(db_path)


def migrate_events(c):
    # Migrate JSON to msgpack
    c.execute("CREATE TABLE events_new (%s)" % ", ".join([
        'repo text not null',
        'branch text not null',
        'tick integer not null',
        'dict blob not null',
        'foreign key(repo) references repos(name)',
        'foreign key(repo, branch) references branches(repo, name)',
        'primary key(repo, branch, tick)',
    ]))

    c.execute("SELECT * from events")
    events = c.fetchall()
    insert_sql = "insert into events_new values (?, ?, ?, ?)"
    for row in events:
        loaded = msgpack.unpackb(row['dict'], raw=False)
        encoded = encode_values(loaded)
        packed = msgpack.packb(encoded, use_bin_type=True)
        c.execute(insert_sql, (row['repo'], row['branch'],
                               row['tick'], packed))

    c.execute("DROP TABLE events")
    c.execute("ALTER TABLE events_new RENAME TO events")
    c.execute("PRAGMA foreign_key_check")


def migrate(path):
    db = Database(path)
    cnx = db._conn

    c = cnx.cursor()
    c.execute("PRAGMA foreign_keys=OFF")
    c.execute("BEGIN")

    migrate_events(c)

    c.execute("COMMIT")
    c.execute("PRAGMA foreign_keys=ON")


def main():
    path = find_database()
    if path is None:
        print("Database not found")
        return

    print("Starting migration...")
    migrate(path)


if __name__ == "__main__":
    main()
