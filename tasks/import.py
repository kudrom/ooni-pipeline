#!/usr/bin/env python
from pymongo import MongoClient
from os.path import join, basename 
from os import renames, walk
import re
import yaml

db_host, db_port = '127.0.0.1', 27017
sanitized_dir = '/data/sanitized'
public_dir = '/data/public'
client = MongoClient(db_host, db_port)
db = client.ooni

def list_report_files(directory):
    for dirpath, dirname, filenames in walk(directory):
        for filename in filenames:
            if filename.endswith(".yamloo"):
                yield join(dirpath, filename)

class ReportInserter(object):
    def __init__(self, report_file):
        try:
            # Insert the report into the database
            self.fh = open(report_file)
            self._report = yaml.safe_load_all(self.fh)
            self.header = self._report.next()
            cc = self.header['probe_cc']
            assert re.match("[a-zA-Z]{2}",cc)

            public_file = join(public_dir, cc, basename(report_file))
            self.header['report_file'] = public_file
            self.rid = db.reports.insert(self.header)

            # Insert each measurement into the database
            for entry in self:
                entry['report_id'] = self.rid
                db.measurements.insert(entry)
            
            # Move the report into the public directory
            renames(report_file, public_file)
        except Exception, e:
            print e

    def __iter__(self):
        return self

    def next(self):
        try:
            entry = self._report.next()
        except StopIteration:
            self.fh.close()
            raise StopIteration
        if not entry:
            entry = self.next()
        return entry

for report_file in list_report_files(sanitized_dir):
    ReportInserter(report_file)