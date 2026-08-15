"""Unit tests for Phase 10.1 Dataset Upload Handler."""

from __future__ import annotations

import io
import zipfile
import pytest

from backend.datasets.upload import DatasetUploadError, DatasetUploadHandler


def test_upload_single_csv():
    csv_content = b"id,val\n1,10.5\n2,20.0\n3,30.5\n"
    file_obj = io.BytesIO(csv_content)

    detail = DatasetUploadHandler.process_upload(
        file_obj=file_obj,
        filename="test_sales_data.csv",
        display_name="Test Sales",
    )

    assert detail.dataset_id.startswith("upload_test_sales_data_")
    assert detail.is_upload is True
    assert detail.table_count == 1
    assert detail.table_summaries[0].table_name == "test_sales_data"
    assert detail.table_summaries[0].row_count == 3


def test_upload_zip_with_multiple_tables():
    zip_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_bytes, "w") as zf:
        zf.writestr("customers_v1.csv", "c_id,segment\n101,SEG_A\n102,SEG_B\n")
        zf.writestr("orders_v1.csv", "o_id,c_id,amount\n1,101,50.0\n2,102,99.9\n")
    zip_bytes.seek(0)

    detail = DatasetUploadHandler.process_upload(
        file_obj=zip_bytes,
        filename="custom_ecommerce.zip",
    )

    assert detail.table_count == 2
    table_names = {t.table_name for t in detail.table_summaries}
    assert {"customers_v1", "orders_v1"}.issubset(table_names)


def test_reject_zip_slip_attack():
    zip_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_bytes, "w") as zf:
        zf.writestr("../../../etc/passwd.csv", "hacked,root\n")
    zip_bytes.seek(0)

    with pytest.raises(DatasetUploadError) as exc_info:
        DatasetUploadHandler.process_upload(
            file_obj=zip_bytes,
            filename="malicious.zip",
        )
    assert "ZIP_SLIP_ATTACK_REJECTED" in str(exc_info.value)


def test_reject_executable_files():
    zip_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_bytes, "w") as zf:
        zf.writestr("valid.csv", "a,b\n1,2\n")
        zf.writestr("malicious_script.sh", "#!/bin/bash\necho hack\n")
    zip_bytes.seek(0)

    with pytest.raises(DatasetUploadError) as exc_info:
        DatasetUploadHandler.process_upload(
            file_obj=zip_bytes,
            filename="executables.zip",
        )
    assert "EXECUTABLE_FILE_REJECTED" in str(exc_info.value)


def test_reject_table_name_collision():
    zip_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_bytes, "w") as zf:
        zf.writestr("transactions.csv", "id,amt\n1,10\n")
        zf.writestr("transactions.parquet", "id,amt\n1,10\n")
    zip_bytes.seek(0)

    with pytest.raises(DatasetUploadError) as exc_info:
        DatasetUploadHandler.process_upload(
            file_obj=zip_bytes,
            filename="collision.zip",
        )
    assert "TABLE_NAME_COLLISION" in str(exc_info.value)
