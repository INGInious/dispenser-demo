# -*- coding: utf-8 -*-
#
# This file is part of INGInious. See the LICENSE and the COPYRIGHTS files for
# more information about the licensing of this file.

import os
import json

from collections import OrderedDict
from flask import send_from_directory

from inginious.common.base import id_checker
from inginious.frontend.pages.utils import INGIniousPage
from inginious.frontend.task_dispensers import TaskDispenser

__version__ = "0.1.dev0"

PATH_TO_PLUGIN = os.path.abspath(os.path.dirname(__file__))
PATH_TO_TEMPLATES = os.path.join(PATH_TO_PLUGIN, "templates")


class StaticMockPage(INGIniousPage):
    def GET(self, path):
        return send_from_directory(os.path.join(PATH_TO_PLUGIN, "static"), path)

    def POST(self, path):
        return self.GET(path)


class DemoDispenser(TaskDispenser):

    def __init__(self, task_list_func, dispenser_data):
        '''
        :param task_list_func: a function returning a dictionary with filesystem taskid as keys and task objects as values
        :param dispenser_data: the dispenser data as written in course.yaml
        '''
        self._task_list_func = task_list_func
        self._data = dispenser_data

    @classmethod
    def get_id(cls):
        '''
        :return: a unique id for the task dispenser
        '''
        return "demo_dispenser"

    @classmethod
    def get_name(cls, language):
        '''
        :param language: the user language
        :return: a human readable name for the task dispenser
        '''
        return "Demo task dispenser"

    def get_dispenser_data(self):
        return self._data

    def render_edit(self, template_helper, course, task_data):
        '''
        :param template_helper: the template_helper singleton
        :param course: the WebAppCourse object
        :param task_data: a helper dictionary containing the human-readable name and download urls
        :return: HTML code for the task list edition page
        '''
        return template_helper.render("admin/task_list_edit.html", template_folder=PATH_TO_TEMPLATES, course=course,
                                      dispenser_data=self._data, tasks=task_data)

    def render(self, template_helper, course, tasks_data, tag_list):
        '''
        :param template_helper: the template_helper singleton
        :param course:  the WebAppCourse object
        :param tasks_data: a helper dict containing achievements status for each task
        :param tag_list: the course tag list to help filtering the tasks (can be ignored)
        :return: HTML code for the student task list page
        '''
        return template_helper.render("student/task_list.html", template_folder=PATH_TO_TEMPLATES, course=course,
                                      tasks=self._task_list_func(), tasks_data=tasks_data, tag_filter_list=tag_list,
                                      dispenser_data=self._data)

    @classmethod
    def check_dispenser_data(cls, dispenser_data):
        '''
        Checks the dispenser data as formatted by the form from render_edit function
        :param dispenser_data: dispenser_data got from the web form (dispenser_structure_ js function)
        :return: A tuple (bool, List<str>). The first item is True if the dispenser_data got from the web form is valid
        The second takes a list of string containing error messages
        '''
        disp_task_list = json.loads(dispenser_data)
        valid = any(set([id_checker(taskid) for taskid in disp_task_list]))
        errors = [] if valid else ["Wrong task ids"]
        return disp_task_list if valid else None, errors

    def get_user_task_list(self, usernames):
        '''
        Returns the task list as seen by the specified users
        :param usernames: the list of users usernames who the user task list is needed for
        :return: a dictionary with username as key and the user task list as value
        '''
        tasks = self._task_list_func()
        task_list = [taskid for taskid in self._data if tasks[taskid].get_accessible_time().after_start()]
        return {username: task_list for username in usernames}

    def get_ordered_tasks(self):
        """ Returns a serialized version of the tasks structure as an OrderedDict"""
        tasks = self._task_list_func()
        return OrderedDict([(taskid, tasks[taskid]) for taskid in self._data if taskid in tasks])

    def get_task_order(self, taskid):
        """ Get the position of this task in the course """
        tasks = self._data
        if taskid in tasks:
            return tasks.index(taskid)
        else:
            return len(tasks)


def init(plugin_manager, course_factory, client, plugin_config):
    # TODO: Replace by shared static middleware and let webserver serve the files
    plugin_manager.add_page('/plugins/disp_demo/static/<path:path>', StaticMockPage.as_view("demodispenserstaticpage"))
    plugin_manager.add_hook("javascript_header", lambda: "/plugins/disp_demo/static/admin.js")
    plugin_manager.add_hook("javascript_header", lambda: "/plugins/disp_demo/static/student.js")
    course_factory.add_task_dispenser(DemoDispenser)
