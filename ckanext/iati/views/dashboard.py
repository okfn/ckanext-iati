from flask import Blueprint
from ckan.lib.base import request, response, render, abort
from ckan.common import _, c, g
from ckan.views.user import _extra_template_variables
import ckan.plugins as p
import ckan.lib.helpers as h
from ckan import logic
import ckan.model as model
from ckan.views import group as core_group_view
from ckanext.iati import helpers as iati_h
import logging

log = logging.getLogger(__name__)
ValidationError = logic.ValidationError
NotAuthorized = logic.NotAuthorized

custom_dashboard = Blueprint(u'custom_dashboard', __name__)


def datasets():
    """
    User Dashboard > My Datasets pagination.
    """
    context = {u'for_view': True, u'user': g.user, u'auth_user_obj': g.userobj}
    data_dict = {u'user_obj': g.userobj, u'include_datasets': True}
    extra_vars = _extra_template_variables(context, data_dict)

    items_per_page = 10  # , readme

    # check ckan version and call appropriate get_page number
    if p.toolkit.check_ckan_version(min_version='2.5.0',
                                    max_version='2.5.3'):
        page = self._get_page_number(request.params) or 1
    else:
        page = h.get_page_number(request.params) or 1

    c.page = h.Page(
        collection=extra_vars['user_dict']['datasets'],
        page=page,
        url=h.pager_url,
        item_count=len(extra_vars['user_dict']['datasets']),
        items_per_page=items_per_page,
    )
    c.page.items = extra_vars['user_dict']['datasets']

    return render(u'user/dashboard_datasets.html', extra_vars)


def recent_publishers():
    is_organization = True
    group_type = u'organization'

    context = {u'model': model, u'for_view': True, u'user': g.user, u'auth_user_obj': g.userobj}
    data_dict = {u'user_obj': g.userobj}

    # Only for sysadmin
    try:
        logic.check_access('sysadmin', context, {})
    except logic.NotAuthorized:
        abort(403, _('Need to be system administrator to administer'))

    extra_vars = {}
    core_group_view.set_org(is_organization)
    page = h.get_page_number(request.params) or 1
    items_per_page = 10

    context = {
        u'model': model,
        u'session': model.Session,
        u'user': c.user,
        u'for_view': True,
        u'with_private': False
    }

    q = request.params.get(u'q', u'')
    sort_by = c.sort_by_selected = request.params.get(u'sort', u'publisher_first_publish_date desc')
    c.q = q

    extra_vars["q"] = q
    extra_vars["sort_by_selected"] = sort_by

    # pass user info to context as needed to view private datasets of
    # orgs correctly
    if c.userobj:
        context['user_id'] = c.userobj.id
        context['user_is_admin'] = c.userobj.sysadmin

    try:
        data_dict_global_results = {
            u'all_fields': False,
            u'q': q,
            u'sort': sort_by,
            u'type': group_type or u'group',
        }
        global_results = core_group_view._action(u'group_list')(context,
                                                                data_dict_global_results)
    except ValidationError as e:
        if e.error_dict and e.error_dict.get(u'message'):
            msg = e.error_dict['message']
        else:
            msg = str(e)
        h.flash_error(msg)
        extra_vars["page"] = h.Page([], 0)
        extra_vars["group_type"] = group_type
        extra_vars.update(_extra_template_variables(context, data_dict))
        return render(
            _get_group_template(u'index_template', group_type), extra_vars)

    data_dict_page_results = {
        u'all_fields': True,
        u'q': q,
        u'sort': sort_by,
        u'type': group_type or u'group',
        u'limit': items_per_page,
        u'offset': items_per_page * (page - 1),
        u'include_extras': True
    }
    page_results = core_group_view._action(u'group_list')(context, data_dict_page_results)

    extra_vars["page"] = h.Page(
        collection=global_results,
        page=page,
        url=h.pager_url,
        items_per_page=items_per_page, )

    extra_vars["page"].items = page_results
    extra_vars["group_type"] = group_type
    c.page = extra_vars["page"]
    extra_vars.update(_extra_template_variables(context, data_dict))
    return render('user/dashboard_recent_publishers.html', extra_vars)


def recent_publishers_download(self):
    """
    Download recent publisher list. Only csv download is allowed
    :return:
    """
    context = {'model': model,
               'user': c.user, 'auth_user_obj': c.userobj}
    try:
        logic.check_access('sysadmin', context, {})
    except NotAuthorized:
        abort(403, _('Not authorized to download file'))

    pub_list = PublishersListDownload('csv', request_recent_publisher=True)

    return pub_list.download()


def my_pending_organizations():
    log.debug('dashboard pending orgainzations')
    # Anonymous user should not be allowed to visit the link
    context = {u'model': model, u'for_view': True, u'user': g.user, u'auth_user_obj': g.userobj}
    data_dict = {u'user_obj': g.userobj}
    try:
        if not c.user:
            raise NotAuthorized
        pending_organizations = iati_h.organization_list_pending()
        extra_vars = _extra_template_variables(context, data_dict)
        extra_vars['pending_organizations'] = pending_organizations
        return render('user/dashboard_pending_organizations.html', extra_vars)
    except NotAuthorized:
        p.toolkit.abort(401, _('Unauthorized to visit pending publisher page %s') % '')


def my_organizations():
    log.debug('dashboard my orgainzations')
    context = {u'model': model, u'for_view': True, u'user': g.user, u'auth_user_obj': g.userobj}
    data_dict = {u'user_obj': g.userobj}
    try:
        if not c.user:
            raise NotAuthorized
        organizations = iati_h.organizations_available_with_extra_fields()
        extra_vars = _extra_template_variables(context, data_dict)
        extra_vars['organizations'] = organizations
        return render('user/my_organizations.html', extra_vars)
    except NotAuthorized:
        p.toolkit.abort(401, _('Unauthorized to visit my publisher page  %s') % '')


custom_dashboard.add_url_rule(u'/dashboard/recent-publishers', view_func=recent_publishers)
custom_dashboard.add_url_rule(u'/dashboard/recent-publishers/download', view_func=recent_publishers_download)
custom_dashboard.add_url_rule(u'/dashboard/datasets', view_func=datasets)
custom_dashboard.add_url_rule(u'/dashboard/mypublishers-pending', view_func=my_pending_organizations)
custom_dashboard.add_url_rule(u'/dashboard/mypublishers', view_func=my_organizations)

