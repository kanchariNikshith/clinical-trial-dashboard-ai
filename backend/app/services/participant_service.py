"""CSV validation and transactional participant import service."""

from __future__ import annotations

import csv
import io
from collections import Counter
from datetime import datetime
from typing import Any, Iterable

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.participant import Participant
from backend.app.models.trial import Trial
from backend.app.services.audit_service import ACTION_CSV_IMPORT, record_audit_event

ALLOWED_STATUSES = {"active", "completed", "withdrawn"}
REQUIRED_COLUMNS = ("participant_id", "status")
OPTIONAL_COLUMNS = (
    "visits_completed",
    "visits_planned",
    "enrollment_date",
    "last_visit_date",
    "next_visit_due_date",
)


def _normalize_header(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip().lower().replace(" ", "_")


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _get_row_value(row: list[str], header_map: dict[str, int], column_name: str) -> str:
    index = header_map.get(column_name)
    if index is None or index >= len(row):
        return ""
    return _clean(row[index])


def _parse_iso_date(value: str, field_name: str) -> datetime.date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:  # pragma: no cover - raised in validation branch
        raise ValueError(f"{field_name} must use ISO format YYYY-MM-DD.") from exc


def _validate_and_preview_csv(file: UploadFile, db: Session, trial_id: str) -> dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "Only CSV files are accepted for participant import.",
                "details": ["The uploaded file must use a .csv extension."],
            },
        )

    if hasattr(file.file, "seek"):
        file.file.seek(0)

    content = file.file.read() if hasattr(file, "file") and not isinstance(file.file, (str, bytes)) else b""
    if hasattr(file.file, "seek"):
        file.file.seek(0)

    if len(content) == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "The uploaded CSV file is empty.",
                "details": ["Please provide a CSV containing at least one participant row."],
            },
        )

    if len(content) > settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail={
                "code": "UPLOAD_LIMIT_EXCEEDED",
                "message": f"The uploaded CSV exceeds the {settings.MAX_UPLOAD_MB} MB size limit.",
                "details": [f"Maximum allowed upload size is {settings.MAX_UPLOAD_MB} MB."],
            },
        )

    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "The uploaded CSV is not valid UTF-8 text.",
                "details": ["Please save the file as UTF-8 encoded CSV."],
            },
        ) from exc

    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if len(rows) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "CSV file is missing a header row.",
                "details": ["The file must include a header row followed by participant records."],
            },
        )

    header = [str(cell).strip() for cell in rows[0]]
    normalized_header = {_normalize_header(value): value for value in header if value}
    header_index_map = {key: index for index, key in enumerate(header) if key}
    # Keep a normalized index map so malformed rows with fewer cells fail gracefully instead of crashing.
    normalized_index_map = {_normalize_header(key): index for index, key in enumerate(header) if key}
    if len(rows) - 1 >= settings.MAX_CSV_ROWS:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail={
                "code": "ROW_LIMIT_EXCEEDED",
                "message": f"The CSV exceeds the maximum of {settings.MAX_CSV_ROWS} participant rows.",
                "details": [f"Please split the file into multiple imports or reduce the row count under {settings.MAX_CSV_ROWS}."],
            },
        )

    missing = [column for column in REQUIRED_COLUMNS if _normalize_header(column) not in normalized_header]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "code": "VALIDATION_ERROR",
                "message": "CSV file is missing required columns.",
                "details": [f"Missing required column(s): {', '.join(missing)}."],
            },
        )

    existing_codes = {participant.participant_id.lower() for participant in db.query(Participant).filter(Participant.trial_id == trial_id).all()}
    file_participant_ids = [
        _get_row_value(row, normalized_index_map, "participant_id").lower()
        for row in rows[1:]
        if row and not all(_clean(cell) == "" for cell in row)
    ]
    duplicate_ids = {value for value, count in Counter(file_participant_ids).items() if count > 1}
    valid_rows: list[dict[str, Any]] = []
    errors: list[str] = []
    total_rows = 0

    for row_index, row in enumerate(rows[1:], start=2):
        if not row or all(_clean(cell) == "" for cell in row):
            continue

        total_rows += 1
        record: dict[str, Any] = {}
        row_errors: list[str] = []

        participant_id = _get_row_value(row, normalized_index_map, "participant_id")
        if not participant_id:
            row_errors.append("participant_id is required.")
        else:
            participant_key = participant_id.lower()
            if participant_key in duplicate_ids:
                row_errors.append(f"Duplicate participant_id '{participant_id}' within the uploaded CSV.")
            elif participant_key in existing_codes:
                row_errors.append(f"Duplicate participant_id '{participant_id}' already exists for this trial.")
            record["participant_id"] = participant_id

        status_value = _get_row_value(row, normalized_index_map, "status")
        if not status_value:
            row_errors.append("status is required.")
        else:
            normalized_status = status_value.lower()
            if normalized_status not in ALLOWED_STATUSES:
                row_errors.append(
                    f"status '{status_value}' is not supported. Allowed values are: active, completed, withdrawn."
                )
            else:
                record["status"] = normalized_status

        for field_name in OPTIONAL_COLUMNS:
            actual_name = normalized_header.get(field_name)
            if not actual_name:
                continue
            raw_value = _get_row_value(row, normalized_index_map, field_name)
            if not raw_value:
                continue

            if field_name in {"visits_completed", "visits_planned"}:
                try:
                    int_value = int(raw_value)
                except ValueError:
                    row_errors.append(f"{field_name} must be a whole number.")
                    continue
                if int_value < 0:
                    row_errors.append(f"{field_name} cannot be negative.")
                    continue
                record[field_name] = int_value
            elif field_name in {"enrollment_date", "last_visit_date", "next_visit_due_date"}:
                try:
                    parsed_date = _parse_iso_date(raw_value, field_name)
                except ValueError as exc:
                    row_errors.append(str(exc))
                    continue
                record[field_name] = parsed_date.isoformat()

        enrollment_date = record.get("enrollment_date")
        last_visit_date = record.get("last_visit_date")
        next_visit_due_date = record.get("next_visit_due_date")
        if enrollment_date and last_visit_date:
            if datetime.strptime(last_visit_date, "%Y-%m-%d").date() < datetime.strptime(enrollment_date, "%Y-%m-%d").date():
                row_errors.append("last_visit_date cannot be before enrollment_date.")
        if enrollment_date and next_visit_due_date:
            if datetime.strptime(next_visit_due_date, "%Y-%m-%d").date() < datetime.strptime(enrollment_date, "%Y-%m-%d").date():
                row_errors.append("next_visit_due_date cannot be before enrollment_date.")
        if "visits_completed" in record and "visits_planned" in record:
            if record["visits_completed"] > record["visits_planned"]:
                row_errors.append("visits_completed cannot exceed visits_planned.")

        if row_errors:
            errors.append(f"Row {row_index}: {'; '.join(row_errors)}")
            continue

        valid_rows.append(record)

    preview = [
        {
            "participant_id": row.get("participant_id", ""),
            "status": row.get("status", ""),
            "visits_completed": row.get("visits_completed"),
            "visits_planned": row.get("visits_planned"),
            "enrollment_date": row.get("enrollment_date"),
            "last_visit_date": row.get("last_visit_date"),
            "next_visit_due_date": row.get("next_visit_due_date"),
        }
        for row in valid_rows[:25]
    ]

    return {
        "total_rows": total_rows,
        "valid_rows": len(valid_rows),
        "invalid_rows": total_rows - len(valid_rows),
        "errors": errors,
        "preview": preview,
        "valid_records": valid_rows,
    }


def _build_csv_error(message: str, details: Iterable[str]) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail={
            "code": "VALIDATION_ERROR",
            "message": message,
            "details": list(details),
        },
    )


async def preview_participants(file: UploadFile, db: Session, trial_id: str) -> dict[str, Any]:
    return _validate_and_preview_csv(file, db, trial_id)


async def import_participants(file: UploadFile, db: Session, trial_id: str, confirmed: bool) -> dict[str, Any]:
    if not confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "CONFIRMATION_REQUIRED",
                "message": "CSV import requires explicit user confirmation before any participant records are written.",
                "details": ["Set confirm=true to proceed with the batch import."],
            },
        )

    preview_result = _validate_and_preview_csv(file, db, trial_id)
    if preview_result["invalid_rows"] > 0:
        raise _build_csv_error(
            "The uploaded CSV contains validation errors. Review the preview and fix the rows before importing.",
            preview_result["errors"],
        )

    if not preview_result["valid_records"]:
        raise _build_csv_error(
            "No valid participant rows were found in the CSV.",
            ["At least one row must pass validation before import can proceed."],
        )

    trial = db.query(Trial).filter(Trial.id == trial_id).first()
    if not trial:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"code": "TRIAL_NOT_FOUND", "message": "Trial not found.", "details": []})

    participants_to_insert = []
    for record in preview_result["valid_records"]:
        participant = Participant(
            trial_id=trial_id,
            participant_id=record["participant_id"],
            status=record["status"],
            visits_completed=record.get("visits_completed"),
            visits_planned=record.get("visits_planned"),
            enrollment_date=(datetime.strptime(record["enrollment_date"], "%Y-%m-%d").date() if record.get("enrollment_date") else None),
            last_visit_date=(datetime.strptime(record["last_visit_date"], "%Y-%m-%d").date() if record.get("last_visit_date") else None),
            next_visit_due_date=(datetime.strptime(record["next_visit_due_date"], "%Y-%m-%d").date() if record.get("next_visit_due_date") else None),
        )
        participants_to_insert.append(participant)

    try:
        db.add_all(participants_to_insert)
        db.commit()
    except Exception as exc:  # pragma: no cover - transactional safety path
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "IMPORT_FAILED",
                "message": "The CSV import failed and no participant records were saved.",
                "details": ["The database transaction was rolled back. Please review the CSV and try again."],
            },
        ) from exc

    record_audit_event(
        db=db,
        action=ACTION_CSV_IMPORT,
        entity_type="trial",
        entity_id=trial_id,
        actor_user_id=trial.owner_user_id,
        outcome="success",
        metadata={
            "trial_id": trial_id,
            "file_name": file.filename,
            "total_rows": preview_result["total_rows"],
            "valid_rows": preview_result["valid_rows"],
            "invalid_rows": preview_result["invalid_rows"],
            "status_counts": {
                "active": sum(1 for row in preview_result["valid_records"] if row["status"] == "active"),
                "completed": sum(1 for row in preview_result["valid_records"] if row["status"] == "completed"),
                "withdrawn": sum(1 for row in preview_result["valid_records"] if row["status"] == "withdrawn"),
            },
        },
    )

    return {
        "trial_id": trial_id,
        "imported_count": len(preview_result["valid_records"]),
        "total_rows": preview_result["total_rows"],
        "valid_rows": preview_result["valid_rows"],
        "invalid_rows": preview_result["invalid_rows"],
        "errors": [],
        "preview": preview_result["preview"],
    }
