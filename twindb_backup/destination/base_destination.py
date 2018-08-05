# -*- coding: utf-8 -*-
"""
Module defines Base destination class and destination exception(s).
"""
from abc import abstractmethod

from subprocess import Popen, PIPE

from twindb_backup import LOG
from twindb_backup.destination.exceptions import DestinationError
from twindb_backup.status.exceptions import CorruptedStatus
from twindb_backup.status.mysql_status import MySQLStatus


class BaseDestination(object):
    """Base destination class"""

    def __init__(self, remote_path, status_path=None):
        if not remote_path:
            raise DestinationError(
                'remote path must be defined and cannot be %r' % remote_path
            )
        self.remote_path = remote_path.rstrip('/')
        if status_path:
            self.status_path = status_path
        else:
            self.status_path = '%s/status' % remote_path

    @abstractmethod
    def save(self, handler, name):
        """
        Save the given stream.

        :param handler: Incoming stream.
        :type handler: file
        :param name: Save stream as this name.
        :type name: str
        :raise: DestinationError if any error
        """

    @staticmethod
    def _save(cmd, handler):

        with handler as input_handler:
            LOG.debug('Running %s', ' '.join(cmd))
            try:
                proc = Popen(cmd, stdin=input_handler,
                             stdout=PIPE,
                             stderr=PIPE)
                cout_ssh, cerr_ssh = proc.communicate()

                ret = proc.returncode
                if ret:
                    if cout_ssh:
                        LOG.info(cout_ssh)
                    if cerr_ssh:
                        LOG.error(cerr_ssh)
                    raise DestinationError('%s exited with error code %d'
                                           % (' '.join(cmd), ret))
                LOG.debug('Exited with code %d', ret)
            except OSError as err:
                raise DestinationError('Failed to run %s: %s'
                                       % (' '.join(cmd), err))

    @abstractmethod
    def get_files(self, prefix, copy_type=None, interval=None):
        """
        Get files by copy type and interval

        :param prefix:
        :param copy_type:
        :param interval:
        :return:
        """

    @abstractmethod
    def delete(self, obj):
        """
        Delete object from the destination

        :param obj:
        :return:
        """

    def status(self, status=None):
        """
        Read or save backup status. Status is an instance of Status class.
        If status is None the function will read status from
        the remote storage.
        Otherwise it will store the status remotely.

        :param status: instance of Status class
        :type status: Status
        :return: instance of Status class
        :rtype: Status
        """
        if status:
            for _ in xrange(3):
                self.write_file(status.serialize(),
                                self.status_path)
                try:
                    return MySQLStatus(
                        content=self.read_file(
                            self.status_path
                        )
                    )
                except CorruptedStatus:
                    pass
            raise DestinationError("Can't write status")
        else:
            try:
                content = self.read_file(self.status_path)
                return MySQLStatus(content)
            except DestinationError:
                return MySQLStatus()

    @abstractmethod
    def write_file(self, content, path):
        """
        Function that actually write content to file

        :param content: Content of file
        :type content: str
        :param path: Path to file
        :type path: str
        """

    @abstractmethod
    def read_file(self, path):
        """
        Function that actually read content from file

        :param path: Path to file
        :type path: str
        :return: File content
        :rtype: str
        :raise DestinationError: If file not found
        """

    @abstractmethod
    def is_file_exist(self, path):
        """Check if file exists by path"""

    def get_run_type_from_full_path(self, path):
        """
        For a given backup copy path find what run_type it was.
        For example,
        s3://bucket/ip-10-0-52-101/daily/files/_etc-2018-04-05_00_07_13.tar.gz
        is a daily backup and
        /path/to/twindb-server-backups/master1/hourly/
        mysql/mysql-2018-04-08_03_51_18.xbstream.gz
        is an hourly backup.

        :param path: Full path of the backup copy
        :return: Run type this backup was taken on:

            - hourly
            - daily
            - weekly
            - monthly
            - yearly
        :rtype: str
        """
        return self.basename(path).split('/')[1]

    def basename(self, filename):
        """
        Basename of backup copy

        :param filename:
        :return:
        """
        return filename.replace(self.remote_path + '/', '', 1)

    def get_latest_backup(self):
        """Get latest backup path"""
        cur_status = self.status()
        latest = cur_status.get_latest_backup()
        if latest is None:
            return None
        url = "{remote_path}/{filename}".format(
            remote_path=self.remote_path,
            filename=latest
        )
        return url
