from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from server.models import Model as Server
from cluster.models import Model as Cluster
from vendor.models import Model as Vendor
from operatingsystem.models import Model as OS
from django.db.models import Count
from django.core.exceptions import ObjectDoesNotExist
from django.apps import apps
from django.http import Http404

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Basic Stats
        context['server_count'] = Server.objects.count()
        context['cluster_count'] = Cluster.objects.count()
        context['vendor_count'] = Vendor.objects.count()
        context['os_count'] = OS.objects.count()
        
        # Data for Charts
        # OS Distribution
        os_dist = Server.objects.values('operatingsystem__vendor__name', 'operatingsystem__version') \
            .annotate(count=Count('id')) \
            .order_by('-count')[:5]
        
        context['os_labels'] = [f"{item['operatingsystem__vendor__name']} {item['operatingsystem__version']}" for item in os_dist]
        context['os_data'] = [item['count'] for item in os_dist]
        
        # Recent Activity
        context['recent_servers'] = Server.objects.all().order_by('-id')[:5]
        
        return context

class SearchView(LoginRequiredMixin, TemplateView):
    template_name = "search.html"

    def get_template_names(self):
        if self.request.GET.get('ajax'):
            return ["search_results_ajax.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('q', '')
        context['query'] = query
        
        if len(query) >= 2:
            context['servers'] = Server.objects.filter(hostname__icontains=query)[:10]
            context['vendors'] = Vendor.objects.filter(name__icontains=query)[:10]
            context['clusters'] = Cluster.objects.filter(name__icontains=query)[:10]
            
            # Simple check if anything was found
            context['has_results'] = any([
                context['servers'].exists(),
                context['vendors'].exists(),
                context['clusters'].exists()
            ])
        else:
            context['has_results'] = False
            context['query_too_short'] = True
            
        return context

class HistoryDiffView(LoginRequiredMixin, TemplateView):
    template_name = "history_diff.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        app_label = kwargs.get('app_label')
        model_name = kwargs.get('model_name')
        history_id = kwargs.get('history_id')

        try:
            model = apps.get_model(app_label, 'Model')
            record = model.history.get(history_id=history_id)
        except (LookupError, ObjectDoesNotExist):
            raise Http404("History record not found")

        context['record'] = record
        context['instance'] = record.instance
        context['app_label'] = app_label
        
        if record.prev_record:
            context['diff'] = record.diff_against(record.prev_record)
        else:
            context['diff'] = None
            
        return context

class TermsView(TemplateView):
    template_name = "legal/terms.html"

class PrivacyView(TemplateView):
    template_name = "legal/privacy.html"

class ImpressumView(TemplateView):
    template_name = "legal/impressum.html"
