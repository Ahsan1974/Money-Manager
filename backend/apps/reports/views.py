import json

from django.http import HttpResponse
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import Account
from apps.core.models import ImportSession


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def import_upload(request):
    from apps.reports.services import start_import

    uploaded = request.FILES.get("file")
    if not uploaded:
        return Response({"error": "Please choose a CSV or Excel file."}, status=400)
    session = start_import(request.user, uploaded)
    return Response(
        {
            "id": session.id,
            "columns": session.detected_columns,
            "mapping": session.mapping,
            "preview": session.preview,
            "status": session.status,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def import_preview(request, pk: int):
    from apps.reports.services import preview_import

    session = ImportSession.objects.filter(user=request.user, pk=pk).first()
    if not session:
        return Response({"error": "Import session not found."}, status=404)
    account_id = request.data.get("account")
    account = Account.objects.filter(user=request.user, pk=account_id).first()
    if not account:
        return Response({"error": "Choose an account for imported rows."}, status=400)
    mapping = request.data.get("mapping") or session.mapping
    preview = preview_import(session, mapping, account)
    return Response({"id": session.id, "preview": preview, "status": session.status})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def import_commit(request, pk: int):
    from apps.reports.services import commit_import

    session = ImportSession.objects.filter(user=request.user, pk=pk).first()
    if not session:
        return Response({"error": "Import session not found."}, status=404)
    account_id = request.data.get("account")
    account = Account.objects.filter(user=request.user, pk=account_id).first()
    if not account:
        return Response({"error": "Choose an account."}, status=400)
    skip = str(request.data.get("skip_duplicates", "true")).lower() != "false"
    result = commit_import(session, account, skip_duplicates=skip)
    return Response(result)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def export_view(request):
    from apps.reports.services import build_pdf_report, export_transactions_csv, export_transactions_xlsx

    fmt = request.query_params.get("format") or "csv"
    year = request.query_params.get("year")
    month = request.query_params.get("month")
    year_i = int(year) if year else None
    month_i = int(month) if month else None
    if fmt == "xlsx":
        return export_transactions_xlsx(request.user, year_i, month_i)
    if fmt == "pdf":
        today = timezone.localdate()
        return build_pdf_report(request.user, year_i or today.year, month_i)
    return export_transactions_csv(request.user, year_i, month_i)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def report_pdf(request):
    from apps.reports.services import build_pdf_report

    today = timezone.localdate()
    year = int(request.query_params.get("year") or today.year)
    month = request.query_params.get("month")
    month_i = int(month) if month else None
    return build_pdf_report(request.user, year, month_i)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def backup_view(request):
    from apps.reports.services import backup_payload

    payload = backup_payload(request.user)
    response = HttpResponse(json.dumps(payload, default=str, indent=2), content_type="application/json")
    response["Content-Disposition"] = "attachment; filename=monea-backup.json"
    return response


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def restore_view(request):
    from apps.reports.services import restore_backup

    if request.data.get("confirmation") != "RESTORE":
        return Response({"error": "Type RESTORE to confirm restoring a backup."}, status=400)
    payload = request.data.get("payload")
    if payload is None and request.FILES.get("file"):
        payload = json.loads(request.FILES["file"].read().decode("utf-8"))
    if not payload:
        return Response({"error": "Provide a backup file."}, status=400)
    try:
        restore_backup(request.user, payload)
    except ValueError as exc:
        return Response({"error": str(exc)}, status=400)
    return Response({"ok": True})
