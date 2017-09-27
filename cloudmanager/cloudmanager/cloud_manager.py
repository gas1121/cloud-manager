import logging
import datetime
import json
import asyncio
from threading import Thread

import arrow
from docker.errors import DockerException

from .terraform_helper import TerraformHelper
from .salt_helper import SaltHelper
from .exceptions import (MasterCountChangeError, TerraformOperationError,
                         ClusterSetupError)

log = logging.getLogger(__name__)


class CloudManager(object):
    """
    Cloud server manager with a internal loop to check and prepare servers
    every several minutes.
    It manage cloud vps resource with following rules:
        1. Store all request vps count and use max of them as vps number,
        2. All request expire after 24 hours, and if no request left,
           destroy all created vps
        3. Every request come with a unique key to identify
        4. When scale is greater than 0, different master count is not allowed
    """
    def __init__(self):
        self.scale_dict = {}
        self.expire_hour = 24
        self.next_id = 0
        self.curr_server_count = (0, 0)
        self.sleep_interval = 5*60

        # thread for internal loop
        self.loop = asyncio.get_event_loop()
        self.loop.call_soon_threadsafe(asyncio.async, self.check_exit_event())
        self.loop.call_soon_threadsafe(asyncio.async, self.check_event())
        self.t = Thread(target=self.main_loop, args=())

    def start(self):
        self.t.start()

    def main_loop(self):
        self.loop.run_forever()
        self.loop.close()

    async def check_exit_event(self):
        """
        Check if exit regularly
        """
        while True:
            await asyncio.sleep(3)

    async def check_event(self):
        """
        Manager's cheduled task
        """
        while True:
            try:
                self.check_cloud()
            except TerraformOperationError:
                log.info('terraform operation failed, wait for next try')
            await asyncio.sleep(self.sleep_interval)

    def stop(self):
        self.loop.stop()
        for task in asyncio.Task.all_tasks():
            task.cancel()

    def new_key(self):
        """Generate new unique key
        """
        new_key = self.next_id
        self.next_id += 1
        return new_key

    def scale_cloud(self, key, master_count, servant_count):
        """
        Add scale data to queue
        """
        if not self._is_master_count_equal(master_count):
            raise MasterCountChangeError
        total_count = master_count + servant_count
        self.scale_dict[key] = (total_count, master_count, servant_count,
                                arrow.now().format('YYYYMMDD HHmmss'))
        log.debug('request data added to queue')

    def check_cloud(self):
        """
        Scale cloud properly
        """
        log.debug('begin a cloud check job')
        # clean expired data
        self._clean_expired_data()
        # get current max scale number
        _, master_count, servant_count, _ = self._get_max_scale_number()
        # is scale number is same with current one, skip following steps
        if (master_count, servant_count) == self.curr_server_count:
            return
        # use terraform to scale cloud
        try:
            tf_helper = TerraformHelper()
            output = tf_helper.do_terraform_scale_job(
                master_count, servant_count)
        except DockerException:
            # raise as terraform job failed
            raise TerraformOperationError
        # read data from terraform result
        data = json.loads(output)
        salt_helper = SaltHelper()
        # prepare salt for work
        salt_helper.prepare_salt_data(data)
        # use salt to do initialization job if needed
        salt_helper.do_salt_init_job()
        # check if request is handled properly
        if not salt_helper.is_cluster_set_up(master_count, servant_count):
            raise ClusterSetupError
        # if all job done, record current master and servant count
        self.curr_server_count = master_count, servant_count

    def _is_master_count_equal(self, master_count):
        for key in self.scale_dict:
            if self.scale_dict[key][1] != master_count:
                return False
        return True

    def _clean_expired_data(self):
        """
        clean data that is over expire_hour
        """
        curr_time = arrow.now()
        filtered_dict = {}
        for key in self.scale_dict:
            item_time = arrow.get(
                self.scale_dict[key][-1], 'YYYYMMDD HHmmss')
            if curr_time - item_time > datetime.timedelta(
                    hours=self.expire_hour):
                continue
            filtered_dict[key] = self.scale_dict[key]
        self.scale_dict = filtered_dict

    def _get_max_scale_number(self):
        if not self.scale_dict:
            return 0, 0, 0, arrow.now().format('YYYYMMDD HHmmss')
        return max(list(self.scale_dict.values()))
