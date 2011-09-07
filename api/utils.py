# -*- coding: utf-8 -*-
"""
    utils

    Utility functions

    :copyright: (c) 2011 by Openlabs Technologies & Consulting (P) Limited
    :license: BSD, see LICENSE for more details.
"""
import urllib2
from collections import namedtuple
from itertools import groupby


class RequestWithMethod(urllib2.Request):
    """
    Implementation of urllib2.Request which also takes a method
    """

    def __init__(self, *args, **kwargs):
        self._method = kwargs.pop('method', None)
        urllib2.Request.__init__(self, *args, **kwargs)

    def get_method(self):
        return (self._method if self._method \
            else urllib2.Request.get_method(self)
        )

data_structure = {
    u'Organization': [
        u'permalink', u'name', u'language', u'created_at', 
        u'domain', u'updated_at', u'time_zone', u'logo_url', 
        u'type', u'id', u'description'
    ], 
    u'User': [
        u'username', u'utc_offset', u'last_name', u'locale', 
        u'created_at', u'updated_at', u'time_zone', u'avatar_url', 
        u'first_name', u'type', u'id', u'biography'
    ],
    u'Comment': [
        u'body', u'hours', u'previous_due_on', u'user_id', 
        u'previous_assigned_id', u'created_at', u'assigned_id', u'target_id', 
        u'body_html', u'updated_at', u'previous_status', u'status', u'due_on', 
        u'project_id', u'type', u'id', u'target_type'
    ],
    u'Project': [
        u'permalink', u'name', u'created_at', u'archived', u'updated_at', 
        u'organization_id', u'owner_user_id', u'type', u'id'
    ],
    u'Task': [
        u'status', u'watchers', u'user_id', u'name', u'created_at', 
        u'assigned_id', u'first_comment_id', u'updated_at', 
        u'recent_comment_ids', u'comments_count', u'due_on', u'position', 
        u'task_list_id', u'project_id', u'type', u'id'
    ],
    u'Person': [u'type', u'source_user_id', u'role', u'id', u'user_id'],

}


class LazyReferenceDescriptor(object):
    """A descriptor implementation for referencing the items from reference map
    """
    def __init__(self, field_name, target_id, reference_map):
        self.target_obj = field_name.rsplit('_id', 1)[0]
        self.target_id = target_id
        self.reference_map = reference_map

    def __getitem__(self, key):
        return self.reference_map[self.target_obj][self.target_id][key]

    def __getattr__(self, name):
        return getattr(
            self.reference_map[self.target_obj][self.target_id], name
            )

    def __repr__(self):
        return u'<%s obj (%d)>' % (self.target_obj, self.target_id)

#: A proxy witha  smaller name
LRD = LazyReferenceDescriptor


class ReferenceObj(dict):
    """An object which automatically translates
    """

    @classmethod
    def from_teambox_obj(cls, data_dict, reference_map):
        items = []
        return cls((
            (k, (LRD(k, v, reference_map) if k.endswith('_id') else v)) \
                for k, v in data_dict.iteritems()
        ))


class AutoReferencingList(list):
    """The response from temabox consists of objects and references which
    complement each other. This list will be an iterator over the objects
    but each object will hold a lazy reference to the related items in the 
    references
    """

    @classmethod
    def from_response(cls, response):
        """Creates and returns a list which has attached reference data for
        each object.
        """
        # Step 1: rebuild references as a reference_map
        # {
        #   type: {
        #       id_1: data,
        #       id_2: data,
        #   }
        # }
        sort_key = lambda reference: reference['type']
        references = sorted(response['references'], key=sort_key)
        reference_map = dict()
        for ref_type, ref_list in groupby(references, key=sort_key):
            reference_map[ref_type.lower()] = dict(
                    ((i['id'], i) for i in ref_list)
            )

        return cls((
            ReferenceObj.from_teambox_obj(obj, reference_map) \
                for obj in response['objects']
        ))
