from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from server.models import Model as Server
from cluster.models import Model as Cluster
from vendor.models import Model as Vendor
from operatingsystem.models import Model as OS
from django.db.models import Count

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
        
        # Recent Activity (Placeholder for now, could be improved with Audit Logging later)
        context['recent_servers'] = Server.objects.all().order_by('-id')[:5]
        
        return context

class SearchView(LoginRequiredMixin, TemplateView):
    template_name = "search.html"

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
