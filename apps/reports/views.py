from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest
from django.shortcuts import render

from apps.expenses.forms import ExpenseFilterForm

from . import exporters
from .services import default_date_range, filtered_expenses, report_summary

EXPORTERS = {
    "csv": exporters.export_csv,
    "xlsx": exporters.export_xlsx,
    "pdf": exporters.export_pdf,
}


def _resolve_filters(request):
    form = ExpenseFilterForm(request.GET or None, user=request.user)
    start_date, end_date = default_date_range()
    category = None
    if form.is_valid():
        start_date = form.cleaned_data.get("start_date") or start_date
        end_date = form.cleaned_data.get("end_date") or end_date
        category = form.cleaned_data.get("category")
    return form, start_date, end_date, category


@login_required
def report_view(request):
    form, start_date, end_date, category = _resolve_filters(request)
    queryset = filtered_expenses(request.user, start_date, end_date, category)
    summary = report_summary(queryset)

    context = {
        "filter_form": form,
        "summary": summary,
        "expenses": queryset[:50],
        "start_date": start_date,
        "end_date": end_date,
    }
    return render(request, "reports/report.html", context)


@login_required
def export_view(request, file_format):
    exporter = EXPORTERS.get(file_format)
    if exporter is None:
        return HttpResponseBadRequest("Unsupported export format.")

    _, start_date, end_date, category = _resolve_filters(request)
    queryset = filtered_expenses(request.user, start_date, end_date, category)
    filename = f"nexpense-report-{start_date}-to-{end_date}"

    if file_format == "pdf":
        return exporter(queryset, filename=filename, user=request.user, date_range=f"{start_date} to {end_date}")
    return exporter(queryset, filename=filename)
