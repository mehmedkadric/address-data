from django.urls import path
from main.views import AddressEntryView, DeleteQueryView, AnalysisView

urlpatterns = [
    path('', AddressEntryView.as_view(), name='address_entry'),
    path('delete/<int:pk>/', DeleteQueryView.as_view(), name='delete_query'),
    path('analysis/', AnalysisView.as_view(), name='analysis'),
]