# -*- coding: utf-8 -*-
"""
    __init__

    Teambox api

    :copyright: (c) 2011 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import urllib
import urllib2
import base64
import json
from itertools import ifilter

from .utils import RequestWithMethod, AutoReferencingList

__version__ = "0.2"




class BaseAPI(object):
    """
    Base implementation of the API
    """

    #: The version of teambox api to connect to
    api_version = "1"

    #: If the responses have to objectified with the supplementary data
    #: provided by teambox in certain ocassions
    objectify = True

    def __init__(self, base_url=None, username=None, password=None):
        """
        :param username: The username to use for Basic password auth
        :param password: The password for Basic auth
        :param base_url: URL of teambox installation. Defaults to the hosted
                         service at https://teambox.com
        """
        if base_url is None:
            base_url = "https://teambox.com"

        authorization = base64.b64encode('%s:%s' % (username, password))
        self.headers = {
            'Accept': 'application/json',
            'Authorization': "Basic %s" % authorization
            }
        self.base_url = base_url

    @classmethod
    def frominstance(cls, instance):
        """Creates an instance of the api from another instantiacted api
        """
        new_instance = cls()
        new_instance.headers = instance.headers
        new_instance.base_url = instance.base_url
        return new_instance 

    def objectify(self, response):
        """Objectifies data into lazy loading objects which lookup in
        the reference data attached to the object
        """
        if isinstance(response, dict) and ('objects' in response) \
                and ('references' in response):
            return AutoReferencingList.from_response(response)
        return response

    def make_request(self, resource, data=None, method=None):
        """
        Send a request

        .. tip::

            Use the method below which proxy this method as a restful 
            interface. See :meth:`post`, :meth:`get`, :meth:`delete` and 
            :meth:`put`

        :param resource: resource path without / in beginning
        :param objectify: A flag to indicate if the response must be 
                          objectified
        """
        url_opener = urllib2.build_opener(
            urllib2.HTTPCookieProcessor(),
            urllib2.HTTPSHandler(),
            )
        url = '/'.join([self.base_url, "api/%s" % self.api_version, resource])
        request = RequestWithMethod(url, data, self.headers, method=method)
        response = json.loads(url_opener.open(request).read())

        if not self.objectify:
            return response
        return self.objectify(response)

    def post(self, resource, data):
        """A proxy for :meth:`make_request` which sends a post to given uri
        """
        return self.make_request(resource, urllib.urlencode(data))

    def get(self, resource):
        """ proxy for :meth:`make_request` which sends a GET to given uri
        """
        return self.make_request(resource)

    def delete(self, resource):
        return self.make_reqeust(resource, method="DELETE")

    def put(self, resource, data):
        return self.make_request(resource, data, method="PUT")

    def filter(self, predicate, *args, **kwargs):
        """Filter the output based on attributes. 

        .. note ::

            This is not a standard API method but a wrapper over the index
            call

        :param predicate: A function which takes a specific record as an 
                          argument and returns True if it should be included 
                          in the result

        All other positional and keyword arguments are propogated to the
        index method. If an idnex method does not exist, then an Exception
        is raised.

        Examples ::

            >>> mem_api = Membership(username="username", password="password")
            >>> # This will return all  members
            >>> all_members = mem_api.index(1)
            >>> # Now to get admin members alone
            >>> admin_members = mem_api.filter(
            ...     lambda member: member['role'] == 30, 1)
            >>> # To see all admin_members
            >>> list(admin_members)

        .. tip::

            Even nested attributes could be used for filtering. Example:

            Let us filter members by locale, which is an attribute of user_id

        Advanced Example::

            >>> admin_members = mem_api.filter(
            ...     lambda member: member['user_id']['locale'] == 'en', 1)


        .. note::

            Note that filter always returns an iterable object. To view it as
            a list pass the iterbale as an argument to a list.
        """
        if not hasattr(self, 'index'):
            raise Exception("This API has no index method implemented")

        return ifilter(predicate, self.index(*args, **kwargs))


class Organization(BaseAPI):
    """Organizations group together :class:`Projects` and :class:`User`s
    (via :class:`Membership`).
    """
    def create(self, data):
        """Creates a new organization
        """
        return self.post("organizations", data)

    def index(self, external=None):
        """Returns the most recent organizations you own or belong to.

        By default external organizations* aren't included. They can be
        included by adding external=true as a GET parameter

        *External organization: An organization that owns a project the user
                                is in, but he's not on the organization.
        """
        path = "organizations"
        if external is not None:
            path = "%s?external=%s" % (path, (external and "true" or "false"))
        self.get(path)

    def show(self, organization):
        """Returns the data for a given organization
        """
        return self.get("organizations/%d" % organization)

    def update(self, organization, data):
        """Updates an organization
        """
        return self.put("organizations/%d" % organization, data)


class Membership(BaseAPI):
    """A membership links a User to an Organization.

    To add people to an organization, make an Invitation.
    """

    def destroy(self, organization, membership):
        """Destroys a member in the organization. 

        .. tip::

            You need to be an administrator in the organization for this 
            to work.
        """
        path = "organizations/%d/memberships/%d" % (organization, membership)
        return self.delete(path)

    def index(self, organization):
        """Returns the most recent people in the project.
        """
        path = "organizations/%d/memberships" % organization
        return self.get(path)

    def show(self, organization, membership):
        """Returns the data for a person in the project
        """
        path = "organizations/%d/memberships/%d" % (organization, membership)
        return self.get(path)

    def update(self, organization, membership, role):
        """Updates a membership in the project. 

        You need to be an administrator in the organization for this to work.

        Roles are as follows:

          * 10 External
          * 20 Participant
          * 30 Admin

        """
        path = "organizations/%d/memberships/%d" % (organization, membership)
        return self.put(path, {'role': role})


class Project(BaseAPI):
    """
    Projects contain most of the objects present in Teambox.
    """

    def create(self, data, organization=None):
        """

        Routes:

          * projects
          * organizations/:organization_id/projects
        """
        path = "organizations/%d/projects" % organization \
            if organization else "projects"
        return self.post(path, data)

    def index(self, organization=None):
        """Returns the most recent projects you own or belong to.

        .. tip::

            You can also filter by organization by passing in organization_id. 
        """
        path = "organizations/%d/projects" % organization \
            if organization else "projects"
        return self.get(path)

    def destroy(self, project, organization=None):
        """Destroys a project.

        .. note::

            You must be the owner in order to perform this action.
        """
        path = "organizations/%d/projects/%d" % (organization, project) \
            if organization else "projects/%d" % (project)
        return self.delete(path)

    def show(self, project, organization=None):
        """Returns the data for a given project
        """
        path = "organizations/%d/projects/%d" % (organization, project) \
            if organization else "projects/%d" % (project)
        return self.get(path)

    def update(self, project, data, organization=None):
        """Updates a project
        """
        path = "organizations/%d/projects/%d" % (organization, project) \
            if organization else "projects/%d" % (project)
        return self.put(path, data)


class Person(BaseAPI):
    """
    A person links a :class:`User` to a :class:`Project`.

    To add people to a project, make an Invitation.
    """

    def destroy(self, project, person):
        """Destroys a person in the project. You need to be an administrator
        in the project for this to work.
        """
        path = "projects/%d/people/%d" % (project, person)
        return self.delete(path)

    def index(self, project):
        """Returns the most recent people in the project.
        """
        path = "projects/%d/people" % (project,)
        return self.get(path)

    def show(self, project, person):
        """Returns the data for a person in the project
        """
        path = "projects/%d/people/%d" % (project, person)
        return self.get(path)

    def update(self,  project, person, role):
        """Updates a person in the project.

        .. note::

            You need to be an administrator in the project for this to work.

                Roles are as follows:

                  * 0 Observer
                  * 1 Commenter
                  * 2 Participant
                  * 3 Admin
        """
        path = "projects/%d/people/%d" % (project, person)
        return self.put(path, {'role': role})


#: A proxy object for :class:`Person` as teambox documentation list says 
#: `People` instead of `Person`
People = Person


class Activity(BaseAPI):
    """An activity is a record of what happened in a :class:`Project`.
    """

    def index(self, project=None, threads=None):
        """Returns the most recent activities in the project. 

        Related objects required to reconstruct a Teambox timeline are stored 
        in references.

        By default all the activities will be returned, but by providing 
        `threads=True` as a parameter, comments inside threads won't be 
        returned.

        This is ideal for apps that want to display a compact view of 
        activities (such as the collapsed view on the web version).
        """
        path = "projects/%d/activities" % project if project \
            else "activities"
        if threads is not None:
            path = "%s?threads=%s" % (path, (threads and "true" or "false"))
        return self.get(path)

    def show(self, activity, project=None):
        """Returns the data for an activity in the project.
        """
        path = "projects/%d/activities/%d" % (project, activity) \
            if project else "activities/%d" % activity
        return self.get(path)


class Comment(BaseAPI):
    """A comment is the core model for communication in Teambox.

    Comments can belong to a Project, a Conversation, or Task.
    """

    def create(self, data, conversation=None, task=None, project=None):
        """
        Creates a new comment. You can specify the target of the comment using
        one of the appropriate routes.

        For time tracking, simply pass in time taken using the hours parameter.
        Acceptable values are the same as on the web frontend -
        e.g. 12h, 1.4, 13m, 2:15.

        Routes:

          * projects/:project_id/conversations/:conversation_id/comments
          * projects/:project_id/tasks/:task_id/comments
          * conversations/:conversation_id/comments
          * tasks/:task_id/comments

        """
        if not any((conversation, task)):
            raise ValueError("Conversion ID or Task ID must be specified")

        if conversation:
            path = "conversations/%d/comments" % conversation
        elif task:
            path = "tasks/%d/comments" % task

        if project:
            # Just prefic the path with Project id
            path = "projects/%d/%s" % (project, path)

        return self.post(path, data)

    def destroy(self, comment):
        """Destroys a comment. You need to be either the owner of the comment,
        or an administrator of the target project for this to work.

        .. note::

            This does not completely implement the paths impemented by teambox
        """
        path = "comments/%d" % comment
        return self.delete(path)

    def index(self, task=None, conversation=None, project=None, 
            target_type=None):
        """
        Returns the most recent comments in a the target.

        Use the optional target_type parameter to filter tasks by their target 
        type, which can be either Conversation or Task. For example, to only
        view only comments belonging to conversations, you would query
        """
        if project and task:
            path = "projects/%d/tasks/%d/comments" % (project, task)
        elif project and conversation:
            path = "projects/%d/conversations/%d/comments" % (
                project, conversation
            )
        elif project:
            path = "projects/%d/comments" % project
        elif task:
            path = "tasks/%d/comments" % task
        elif conversation:
            path = "conversations/%d/comments" % conversation
        else:
            path = "comments"

        if target_type is not None:
            assert target_type in ("Conversation", "Task")
            path = "%s?target_type=%s" % (path, target_type)

        return self.get(path)

    def show(self, comment):
        """Returns the data for an comment.

        .. note::

            This does not completely implement the paths impemented by teambox
        """
        path = "comments/%d" % comment
        return self.get(path)

    def update(self, comment, data):
        """Updates the content of a comment. 

        .. warning::

            You can no longer update comments 15 minutes after they have been
            created.
        """
        path = "comments/%d" % comment
        return self.put(path, data)


class Invitation(BaseAPI):
    """An Invitation invites a User to a Project, via email.

    .. warning::

        NOT IMPLEMENTED YET

    """
    pass


class Conversation(BaseAPI):
    """Conversation is a group of comments.

    It can also act as a thread in the project overview.
    Comments belong to a Project.

    .. warning::

        NOT IMPLEMENTED YET

    """
    pass


class TaskList(BaseAPI):
    """A task list is a collection of Tasks in a Project.
    """

    def archive(self, project, task_list):
        """Archives the task list. 

        .. warning::

            All tasks belonging to the task list will be updated and resolved.
        """
        path = "projects/%d/task_lists/%d/archive" % (project, task_list)
        return self.put(path, None)

    def create(self, data, project=None):
        path = "task_lists"
        if project:
            path = "projects/%d/%s" % (project, path)

        return self.post(path, data)

    def destroy(self, task_list, project=None):
        """Destroys a task list.
        """
        path = "task_lists/%d" % task_list
        if project:
            path = "projects/%d/%s" % (project, path)
        return self.delete(path)

    def index(self, project=None, archived=None):
        """Returns the most recent task lists in a project.

        .. tip::

            To filter by archived or unarchived lists, pass in the optional
            archived parameter. To view everything, simply omit the archived
            parameter.
        """
        path = "task_lists"
        if project:
            path = "projects/%d/%s" % (project, path)

        if archived is not None:
            path = "%s?archived=%s" % (archived and "true" or "false")
        return self.get(path)

    def reorder(self, project, order):
        """Reorders the task lists in a project according to the order each 
        task list id is presented in task_list_ids.

        :param order: List of task_list ids in the order
        """
        path = "projects/%d/task_lists/reorder" % project
        return self.put(path, {'task_list_ids': ",".join(order)})

    def show(self, task_list, project=None):
        """Returns the data for a task list.
        """
        path = "task_lists/%d" % task_list
        if project:
            path = "projects/%d/%s" % (project, path)
        return self.get(path)

    def unarchive(self, project, task_list):
        """Unarchives the task list.
        """
        path = "projects/%d/task_lists/%d/unarchive" % (project, task_list)
        return self.put(path, None)

    def update(self, task_list, data, project=None):
        """Updates the name, start date and end date of a task list.
        """
        path = "task_lists/%d" % task_list
        if project:
            path = "projects/%d/%s" % (project, path)
        return self.put(path, data)
