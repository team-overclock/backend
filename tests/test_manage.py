"""관리용 라우터 및 주요 실행 함수 단위 테스트 모듈."""

import os
from unittest.mock import MagicMock, patch, ANY
import pytest
from fastapi import status


# ==============================================================================
# 1. API 엔드포인트 테스트 (API Router Tests)
# ==============================================================================

def test_create_tables_endpoint_success(client):
    """POST /manage/tables 테이블 생성 성공 테스트"""
    with patch("app.manage.tables.router.create") as mock_create:
        response = client.post("/manage/tables")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {"success": True}
        mock_create.assert_called_once()


def test_create_tables_endpoint_failure(client):
    """POST /manage/tables 테이블 생성 실패 테스트 (try-except 내장 처리로 201 반환)"""
    with patch("app.manage.tables.router.create", side_effect=Exception("Database Error")) as mock_create:
        response = client.post("/manage/tables")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json() == {"success": False}
        mock_create.assert_called_once()


def test_drop_tables_endpoint_success(client):
    """DELETE /manage/tables 테이블 삭제 성공 테스트"""
    with patch("app.manage.tables.router.drop") as mock_drop:
        response = client.delete("/manage/tables")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"success": True}
        mock_drop.assert_called_once()


def test_drop_tables_endpoint_failure(client):
    """DELETE /manage/tables 테이블 삭제 실패 테스트"""
    with patch("app.manage.tables.router.drop", side_effect=Exception("Database Error")) as mock_drop:
        response = client.delete("/manage/tables")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"success": False}
        mock_drop.assert_called_once()


def test_download_data_endpoint(client):
    """POST /manage/data/sources 소스 다운로드 백그라운드 요청 테스트"""
    with patch("app.manage.data.router.download") as mock_download:
        response = client.post("/manage/data/sources")
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json() == {"requested": True}
        mock_download.assert_called_once_with(silent=False)


def test_download_data_status_endpoint(client):
    """GET /manage/data/sources/status 다운로드 상태 및 버전 조회 테스트"""
    with patch("app.manage.data.router.get_current_version", return_value="v1.0.0") as mock_curr, \
         patch("app.manage.data.router.get_downloading_version", return_value="v1.1.0") as mock_down:
        
        response = client.get("/manage/data/sources/status")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "curr_version": "v1.0.0",
            "downloading_version": "v1.1.0"
        }
        mock_curr.assert_called_once()
        mock_down.assert_called_once()


def test_insert_data_endpoint(client):
    """PATCH /manage/data 데이터 삽입 백그라운드 요청 테스트"""
    with patch("app.manage.data.router.insert") as mock_insert:
        response = client.patch("/manage/data")
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json() == {"requested": True}
        mock_insert.assert_called_once_with(silent=False)


def test_check_data_status_endpoint(client, mock_db):
    """GET /manage/data/status 데이터 삽입 유무 및 테이블 행 존재 상태 확인 테스트"""
    mock_result = MagicMock()
    mock_result.tuples.return_value.first.return_value = (True, False, True)
    mock_db.execute.return_value = mock_result

    response = client.get("/manage/data/status")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "has_region": True,
        "has_property": False,
        "has_infrastructure": True,
    }


def test_generate_seeds_endpoint(client):
    """POST /manage/seeds 시드 데이터 생성 백그라운드 요청 테스트"""
    with patch("app.manage.seeds.router.insert_seeds") as mock_insert_seeds:
        response = client.post("/manage/seeds", json={"recommendations": 25, "users": 10})
        assert response.status_code == status.HTTP_202_ACCEPTED
        assert response.json() == {"requested": True}
        mock_insert_seeds.assert_called_once_with(
            num_recommendations=25,
            num_users=10,
            silent=True
        )


def test_delete_seeds_endpoint_success(client):
    """DELETE /manage/seeds 시드 데이터 삭제 성공 테스트"""
    with patch("app.manage.seeds.router.drop_seeds") as mock_drop_seeds:
        response = client.delete("/manage/seeds")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"success": True}
        mock_drop_seeds.assert_called_once()


def test_delete_seeds_endpoint_failure(client):
    """DELETE /manage/seeds 시드 데이터 삭제 실패 테스트"""
    with patch("app.manage.seeds.router.drop_seeds", side_effect=Exception("Database Error")) as mock_drop_seeds:
        response = client.delete("/manage/seeds")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"success": False}
        mock_drop_seeds.assert_called_once()


def test_check_seed_status_endpoint(client, mock_db):
    """GET /manage/seeds/status 시드 데이터 생성 상태 개수 조회 테스트"""
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [100, 250]
    mock_db.execute.return_value = mock_result

    response = client.get("/manage/seeds/status")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "total_users": 100,
        "total_recommendations": 250
    }


# ==============================================================================
# 2. 메인 실행 함수(Main Run Functions) 테스트
# ==============================================================================

def test_run_create_tables():
    """tables/create.py run() 함수 호출 테스트"""
    from app.manage.tables.create import run as run_create
    with patch("app.manage.tables.create.Base.metadata.create_all") as mock_create_all:
        run_create()
        mock_create_all.assert_called_once()


def test_run_create_tables_error():
    """tables/create.py run() 함수 예외 발생 테스트"""
    from app.manage.tables.create import run as run_create
    with patch("app.manage.tables.create.Base.metadata.create_all", side_effect=Exception("Metadata Error")):
        with pytest.raises(Exception) as exc_info:
            run_create()
        assert "Metadata Error" in str(exc_info.value)


def test_run_drop_tables():
    """tables/drop.py run() 함수 호출 테스트"""
    from app.manage.tables.drop import run as run_drop
    with patch("app.manage.tables.drop.Base.metadata.drop_all") as mock_drop_all:
        run_drop()
        mock_drop_all.assert_called_once()


def test_run_drop_tables_error():
    """tables/drop.py run() 함수 예외 발생 테스트"""
    from app.manage.tables.drop import run as run_drop
    with patch("app.manage.tables.drop.Base.metadata.drop_all", side_effect=Exception("Metadata Error")):
        with pytest.raises(Exception) as exc_info:
            run_drop()
        assert "Metadata Error" in str(exc_info.value)


def test_run_download_no_update():
    """data/download.py run() - 현재 버전과 최신 버전이 동일하여 다운로드하지 않는 경우"""
    from app.manage.data.download import run as run_download
    
    urls_mock = {"version": "http://ver", "google drive": "http://drive"}
    
    with patch("app.manage.data.download.read_url_file", return_value=urls_mock) as mock_read_urls, \
         patch("app.manage.data.download.read_file") as mock_read_file, \
         patch("app.manage.data.download.download_file") as mock_download_file, \
         patch("app.manage.data.download.download_folder") as mock_download_folder, \
         patch("app.manage.data.download.write_file") as mock_write_file, \
         patch("app.manage.data.download.move_folder") as mock_move_folder, \
         patch("app.manage.data.download.os.remove") as mock_remove:
         
        # read_file 첫 호출(curr_version): "v1.0", 두 번째 호출(new_version): "v1.0"
        mock_read_file.side_effect = ["v1.0", "v1.0"]
        
        result = run_download(silent=True)
        
        assert result is False
        mock_read_urls.assert_called_once()
        mock_download_file.assert_called_once_with(url="http://ver", output=ANY, silent=True)
        # 버전이 동일하므로 다운로드 폴더 및 파일 쓰기가 호출되면 안 됨
        mock_download_folder.assert_not_called()
        mock_write_file.assert_not_called()


def test_run_download_success():
    """data/download.py run() - 새 버전이 출시되어 정상 다운로드 및 데이터 갱신 완료되는 경우"""
    from app.manage.data.download import run as run_download
    
    urls_mock = {"version": "http://ver", "google drive": "http://drive"}
    
    with patch("app.manage.data.download.read_url_file", return_value=urls_mock) as mock_read_urls, \
         patch("app.manage.data.download.read_file") as mock_read_file, \
         patch("app.manage.data.download.download_file") as mock_download_file, \
         patch("app.manage.data.download.download_folder") as mock_download_folder, \
         patch("app.manage.data.download.write_file") as mock_write_file, \
         patch("app.manage.data.download.move_folder") as mock_move_folder, \
         patch("app.manage.data.download.os.remove") as mock_remove:
         
        # read_file 첫 호출(curr_version): "v1.0", 두 번째 호출(new_version): "v2.0"
        mock_read_file.side_effect = ["v1.0", "v2.0"]
        
        result = run_download(silent=True)
        
        assert result is True
        mock_read_urls.assert_called_once()
        mock_download_file.assert_called_once_with(url="http://ver", output=ANY, silent=True)
        mock_write_file.assert_called_once_with(ANY, "v2.0")
        mock_download_folder.assert_called_once_with(url="http://drive", output=ANY, silent=True)
        assert mock_move_folder.call_count == 2
        assert mock_remove.call_count == 2


def test_run_insert_data_success():
    """data/insert.py run() - 데이터 파일 정상 로드 및 DB 삽입 트랜잭션 정상 완료 테스트"""
    from app.manage.data.insert import run as run_insert
    
    mock_session = MagicMock()
    
    with patch("app.manage.data.insert.Base.metadata.create_all") as mock_create_all, \
         patch("app.manage.data.insert.SessionLocal", return_value=mock_session) as mock_session_local, \
         patch("app.manage.data.insert.Path.is_dir", return_value=True) as mock_is_dir, \
         patch("app.manage.data.insert.get_files", return_value=["file1.csv"]) as mock_get_files, \
         patch("app.manage.data.insert._run") as mock_internal_run:
         
        run_insert(silent=True)
        
        mock_create_all.assert_called_once()
        mock_session_local.assert_called_once()
        mock_internal_run.assert_called_once_with(mock_session, ["file1.csv"], silent=True)
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()


def test_run_insert_data_failure():
    """data/insert.py run() - 삽입 도중 에러가 발생하여 롤백 및 세션 종료가 처리되는 테스트"""
    from app.manage.data.insert import run as run_insert
    
    mock_session = MagicMock()
    
    with patch("app.manage.data.insert.Base.metadata.create_all") as mock_create_all, \
         patch("app.manage.data.insert.SessionLocal", return_value=mock_session) as mock_session_local, \
         patch("app.manage.data.insert.Path.is_dir", return_value=True) as mock_is_dir, \
         patch("app.manage.data.insert.get_files", return_value=["file1.csv"]) as mock_get_files, \
         patch("app.manage.data.insert._run", side_effect=Exception("IO Error")) as mock_internal_run:
         
        with pytest.raises(Exception) as exc_info:
            run_insert(silent=True)
            
        assert "IO Error" in str(exc_info.value)
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


def test_run_insert_seeds_success():
    """seeds/insert.py run() - 랜덤 시드 데이터 정상 추가 완료 테스트"""
    from app.manage.seeds.insert import run as run_insert_seeds
    
    mock_session = MagicMock()
    
    with patch("app.manage.seeds.insert.SessionLocal", return_value=mock_session) as mock_session_local, \
         patch("app.manage.seeds.insert._run", return_value=50) as mock_internal_run:
         
        total = run_insert_seeds(num_recommendations=20, num_users=5, silent=True)
        
        assert total == 50
        mock_session_local.assert_called_once()
        mock_internal_run.assert_called_once_with(mock_session, 20, 5, silent=True)
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()


def test_run_insert_seeds_failure():
    """seeds/insert.py run() - 시드 데이터 추가 중 예외 발생 시 롤백 및 세션 종료 테스트"""
    from app.manage.seeds.insert import run as run_insert_seeds
    
    mock_session = MagicMock()
    
    with patch("app.manage.seeds.insert.SessionLocal", return_value=mock_session) as mock_session_local, \
         patch("app.manage.seeds.insert._run", side_effect=Exception("Seed Error")) as mock_internal_run:
         
        with pytest.raises(Exception) as exc_info:
            run_insert_seeds(silent=True)
            
        assert "Seed Error" in str(exc_info.value)
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


def test_run_drop_seeds_success():
    """seeds/drop.py run() - 시드 데이터 정상 일괄 삭제 완료 테스트"""
    from app.manage.seeds.drop import run as run_drop_seeds
    
    mock_session = MagicMock()
    
    with patch("app.manage.seeds.drop.SessionLocal", return_value=mock_session) as mock_session_local:
        run_drop_seeds()
        
        mock_session_local.assert_called_once()
        assert mock_session.query.call_count == 2
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()


def test_run_drop_seeds_failure():
    """seeds/drop.py run() - 삭제 진행 중 오류 시 롤백 및 세션 정상 종료 테스트"""
    from app.manage.seeds.drop import run as run_drop_seeds
    
    mock_session = MagicMock()
    mock_session.query.side_effect = Exception("Drop Query Failed")
    
    with patch("app.manage.seeds.drop.SessionLocal", return_value=mock_session) as mock_session_local:
        with pytest.raises(Exception) as exc_info:
            run_drop_seeds()
            
        assert "Drop Query Failed" in str(exc_info.value)
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
