from ckan.lib.base import c
from ckan.lib.helpers import json
from ckan import model
from ckan.controllers.package import PackageController
from ckan.authz import Authorizer

from ckan.logic.schema import package_form_schema
from ckan.lib.navl.validators import (ignore_missing,
                                      not_empty,
                                      empty,
                                      ignore,
                                      keep_extras,
                                     )
from ckan.lib.navl.dictization_functions import Missing, Invalid
from ckan.lib.field_types import DateType, DateConvertError

from countries import COUNTRIES

class PackageIatiController(PackageController):

    package_form = 'package/form_iati.html'

    def _setup_template_variables(self, context, data_dict=None):

        super(PackageIatiController,self)._setup_template_variables(context,data_dict)

        c.groups_authz = self.get_groups()
        c.groups_available = self.get_groups(available_only=True)

        c.countries = [(v, k) for k, v in COUNTRIES]

    def _form_to_db_schema(self):
        schema = package_form_schema()
        schema.update({
            'department': [unicode,convert_to_extras,ignore_missing],
            'country': [convert_to_extras, ignore_missing],
            'donors': [unicode, convert_from_comma_list, convert_to_extras, ignore_missing],
            'donors_type': [unicode, convert_from_comma_list, convert_to_extras, ignore_missing],
            'donors_country': [unicode, convert_from_comma_list, convert_to_extras, ignore_missing],
            'record_updated': [date_to_db, convert_to_extras,ignore_missing],
            'data_updated': [date_to_db, convert_to_extras,ignore_missing],
            'activity_period-from': [date_to_db, convert_to_extras,ignore_missing],
            'activity_period-to': [date_to_db, convert_to_extras,ignore_missing],
            'activity_count': [integer,convert_to_extras,ignore_missing],
            'archive_file': [checkbox_value, convert_to_extras,ignore_missing],
            'verified': [checkbox_value, convert_to_extras,ignore_missing],
        })

        return schema

    def _db_to_form_schema(self):
        schema = package_form_schema()
        schema.update({
            'department': [convert_from_extras,ignore_missing],
            'country': [convert_from_extras, ignore_missing],
            'donors': [convert_from_extras, convert_to_comma_list, ignore_missing],
            'donors_type': [convert_from_extras, convert_to_comma_list, ignore_missing],
            'donors_country': [convert_from_extras, convert_to_comma_list, ignore_missing],
            'record_updated': [convert_from_extras,ignore_missing, date_to_form],
            'data_updated': [convert_from_extras,ignore_missing, date_to_form],
            'activity_period-from': [convert_from_extras,ignore_missing, date_to_form],
            'activity_period-to': [convert_from_extras,ignore_missing, date_to_form],
            'activity_count': [convert_from_extras,ignore_missing],
            'archive_file': [convert_from_extras,ignore_missing],
            'verified': [convert_from_extras,ignore_missing],
        })

        return schema

    def _check_data_dict(self, data_dict):
        return

    # End hooks

    def get_groups(self,available_only=False):

        query = Authorizer().authorized_query(c.user, model.Group, model.Action.EDIT)
        groups = set(query.all())

        if available_only:
            package = c.pkg
            if package:
                groups = groups - set(package.groups)

        return [{'id':group.id,'name':group.name, 'title':group.title} for group in groups if group.state==model.State.ACTIVE]


def convert_to_extras(key, data, errors, context):

    extras = data.get(('extras',), [])
    if not extras:
        data[('extras',)] = extras

    extras.append({'key': key[-1], 'value': data[key]})

def convert_from_extras(key, data, errors, context):

    for data_key, data_value in data.iteritems():
        if (data_key[0] == 'extras'
            and data_key[-1] == 'key'
            and data_value == key[-1]):
            data[key] = data[('extras', data_key[1], 'value')]

def date_to_db(value, context):
    try:
        value = DateType.form_to_db(value)
    except DateConvertError, e:
        raise Invalid(str(e))
    return value

def date_to_form(value, context):
    try:
        value = DateType.db_to_form(value)
    except DateConvertError, e:
        raise Invalid(str(e))
    return value

def convert_to_comma_list(value, context):

    return ', '.join(json.loads(value))

def convert_from_comma_list(value, context):

    return [x.strip() for x in value.split(',') if len(x)]

def checkbox_value(value,context):

    return 'yes' if not isinstance(value, Missing) else 'no'

def integer(value,context):
    try:
        value = int(value)
    except ValueError,e:
        raise Invalid(str(e))
    return value

