from django.shortcuts import get_object_or_404, redirect
from django.db.models import Q
from django.http import Http404
from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin
from django.conf import settings

from mezzanine.pages.views import page as page_view

from widgy.contrib.form_builder.views import HandleFormMixin
from widgy.contrib.widgy_mezzanine import get_widgypage_model
from widgy.models import Node
from widgy.views.base import AuthorizedMixin
from widgy.utils import fancy_import

WidgyPage = get_widgypage_model()


def get_page_from_node(node):
    root_node = node.get_root()
    try:
        # try to find a page that uses this root node
        return get_object_or_404(
            WidgyPage.objects.distinct(),
            Q(root_node__commits__root_node=root_node) | Q(root_node__working_copy=root_node)
        )
    except Http404:
        # otherwise, use a fake page
        return WidgyPage(
            titles='restoring page',
            content_model='widgypage',
        )


class HandleFormView(HandleFormMixin, View):
    def get(self, request, *args, **kwargs):
        # This will raise a KeyError when `from` is for some reason
        # missing. What should it actually do?
        return redirect(request.GET['from'])

    def form_invalid(self, form):
        try:
            root_node = get_object_or_404(Node, pk=self.kwargs['root_node_pk'])
        except KeyError:
            root_node = self.form_node.get_root()
        page = get_page_from_node(root_node)

        return page_view(self.request, page.slug, extra_context=self.get_context_data(
            form=form,
            page=page,
            root_node_override=root_node,
        ))

handle_form = HandleFormView.as_view()


class PreviewView(AuthorizedMixin, SingleObjectMixin, View):
    model = Node
    pk_url_kwarg = 'node_pk'

    def get(self, request, node_pk, node=None):
        node = node or self.get_object()

        page = get_page_from_node(node)

        context = {
            'page': page,
            'root_node_override': node,
            '_current_page': page,
        }

        return page_view(request, page.slug, extra_context=context)

preview = PreviewView.as_view(
    site=fancy_import(settings.WIDGY_MEZZANINE_SITE),
)
