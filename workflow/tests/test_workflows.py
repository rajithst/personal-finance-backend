import io
from unittest.mock import MagicMock

import pandas as pd
import pytest

from common.enums import WorkflowContextType
from workflow.import_workflow import ImportCsvWorkflow
from workflow.storage_backend.local_storage import LocalStorage
from workflow.upload_workflow import UploadWorkflow


class DummyProcessor:
    def get_read_config(self):
        return {}

    def get_expected_columns(self):
        return ['col_a', 'col_b']

    def process_data(self, df, account):
        df['processed'] = True
        return df

    def validate_dataframe(self, df):
        return df


class TestLocalStorage:
    def test_upload_and_read_file(self, tmp_path):
        storage = LocalStorage(str(tmp_path))

        content = b"header1,header2\nval1,val2\n"
        stream = io.BytesIO(content)
        uploaded = storage.upload_file(stream, "test_file.csv")
        assert uploaded is True

        # Read file as stream
        with storage.read_file("test_file.csv") as f:
            lines = [line.strip() for line in f]
            assert lines == ["header1,header2", "val1,val2"]

        # Read file as dataframe
        df = storage.read_csv("test_file.csv")
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["header1", "header2"]
        assert len(df) == 1

        # List files
        files = storage.list_files("")
        assert "test_file.csv" in files

        # Delete file
        deleted = storage.delete_file("test_file.csv")
        assert deleted is True
        assert storage.delete_file("test_file.csv") is False

    def test_read_all_files(self, tmp_path):
        storage = LocalStorage(str(tmp_path))
        storage.upload_file(io.BytesIO(b"a,b\n1,2\n"), "sub/file1.csv")
        storage.upload_file(io.BytesIO(b"a,b\n3,4\n"), "sub/file2.csv")

        dfs = storage.read_all_files("sub")
        assert len(dfs) == 2
        combined = pd.concat(dfs, ignore_index=True)
        assert len(combined) == 2


class TestImportCsvWorkflow:
    def test_import_with_skiprows_detection(self, tmp_path):
        storage = LocalStorage(str(tmp_path))
        # CSV with junk preamble before header
        csv_content = (
            "Title: Statement Report\n"
            "Generated: 2026-01-01\n"
            "col_a,col_b\n"
            "foo,bar\n"
            "baz,qux\n"
        )
        storage.upload_file(io.BytesIO(csv_content.encode('utf-8')), "test_statement.csv")

        mock_provider = MagicMock()
        mock_provider.get_provider.return_value = storage

        account = MagicMock()
        account.id = 1

        workflow = ImportCsvWorkflow(
            account=account,
            account_processor=DummyProcessor(),
            storage_provider=mock_provider,
            is_development=True,
        )

        result_df = workflow.import_data_from_files(
            workflow_type="unused_target",
            file_names=["test_statement.csv"],
        )

        assert len(result_df) == 2
        assert "col_a" in result_df.columns
        assert "col_b" in result_df.columns
        assert result_df["processed"].all() == True

    def test_invalid_workflow_type_raises(self):
        account = MagicMock()
        workflow = ImportCsvWorkflow(
            account=account,
            account_processor=DummyProcessor(),
            is_development=True,
        )
        with pytest.raises(ValueError, match="Invalid workflow type"):
            workflow.import_data_from_files(workflow_type=12345)


class TestUploadWorkflow:
    def test_upload_files(self, tmp_path, mocker):
        mocker.patch("workflow.upload_workflow.get_current_user", return_value=MagicMock(id=99))
        storage = LocalStorage(str(tmp_path))
        mock_provider = MagicMock()
        mock_provider.get_provider.return_value = storage

        account = MagicMock()
        account.id = 10

        upload_file_mock = MagicMock()
        upload_file_mock.name = "my_statement.csv"
        upload_file_mock.read.return_value = b"sample,data\n1,2\n"

        workflow = UploadWorkflow(
            account=account,
            storage_provider=mock_provider,
            is_development=True,
        )

        uploaded = workflow.upload_files(WorkflowContextType.TRANSACTION_FILES, [upload_file_mock])
        assert len(uploaded) == 1
        assert "user_99" in uploaded[0]
        assert "acc_10" in uploaded[0]
        assert "my_statement.csv" in uploaded[0]
