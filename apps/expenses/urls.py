from django.urls import path

from . import views

app_name = "expenses"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("expenses/", views.ExpenseListView.as_view(), name="list"),
    path("expenses/new/", views.ExpenseCreateView.as_view(), name="create"),
    path("expenses/<int:pk>/edit/", views.ExpenseUpdateView.as_view(), name="update"),
    path("expenses/<int:pk>/delete/", views.ExpenseDeleteView.as_view(), name="delete"),
    path("categories/", views.CategoryListView.as_view(), name="category_list"),
    path("categories/new/", views.CategoryCreateView.as_view(), name="category_create"),
    path("categories/<int:pk>/delete/", views.CategoryDeleteView.as_view(), name="category_delete"),
]
