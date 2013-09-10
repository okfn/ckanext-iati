# Bad import: should be in toolkit
from pylons import config

import ckan.model as model # get_licenses should be in core
import ckan.lib.helpers as helpers

import ckanext.iati.lists as lists


def get_countries():
    return lists.COUNTRIES

def get_publisher_source_types():
    return lists.PUBLISHER_SOURCE_TYPES

def get_organization_types():
    return lists.ORGANIZATION_TYPES

def get_country_title(code):
    return _get_list_item_title(lists.COUNTRIES, code)

def get_file_type_title(code):
    return _get_list_item_title(lists.FILE_TYPES, code)

def get_publisher_source_type_title(code):
    return _get_list_item_title(lists.PUBLISHER_SOURCE_TYPES, code)

def get_organization_type_title(code):
    return _get_list_item_title(lists.ORGANIZATION_TYPES, code)

def get_issue_title(code):
    return code.replace('-', ' ').title()

def get_licenses():
    return [('', '')] + model.Package.get_license_options()

def is_route_active(menu_item):
    _menu_items = config.get('routes.named_routes')
    if menu_item not in _menu_items:
        return False
    return helpers._link_active(_menu_items[menu_item])

def return_select_options(name, data):
    return_options = []
    return_selected = False

    if name == 'publisher_type':
        options = get_publisher_source_types()
        return_selected = data.get('type')
        for value, label in options:
            return_options.append({ 'text': label, 'value': value })
    elif name == 'license_id':
        options = get_licenses()
        return_selected = data.get('license_id', 'notspecified')
        for label, value in options:
            if label:
                return_options.append({ 'text': label, 'value': value })
    elif name == 'publisher_organization_type':
        options = get_organization_types()
        return_selected = data.get('publisher_organization_type')
        for value, label in options:
            return_options.append({ 'text': label, 'value': value })
    elif name == 'state':
        return_options = [
            { 'text': 'Active', 'value': 'active' },
            { 'text': 'Pending', 'value': 'pending' },
            { 'text': 'Deleted', 'value': 'deleted' },
        ]
        return_selected = data.get('state', 'none')

    return (return_options, return_selected)

def _get_list_item_title(_list, code):
    return dict(_list).get(code, code)

