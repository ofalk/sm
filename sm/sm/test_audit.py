from django.test import TestCase
from cluster.models import Model as Cluster
from clusterpackage.models import Model as ClusterPackage
from clusterpackagetype.models import Model as ClusterPackageType
from clustersoftware.models import Model as ClusterSoftware
from domain.models import Model as Domain
from location.models import Model as Location
from operatingsystem.models import Model as OS
from patchtime.models import Model as Patchtime
from server.models import Model as Server
from servermodel.models import Model as ServerModel
from status.models import Model as Status
from vendor.models import Model as Vendor

class AuditLoggingTest(TestCase):
    def test_models_have_history(self):
        models = [
            Cluster, ClusterPackage, ClusterPackageType, ClusterSoftware,
            Domain, Location, OS, Patchtime, Server, ServerModel,
            Status, Vendor
        ]
        for model in models:
            self.assertTrue(hasattr(model, 'history'), f"Model {model.__name__} is missing audit history!")
