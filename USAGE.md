# USAGE — HYW RelayServer 사용 방법

중계서버의 설치 후 사용 절차를 정리한 문서입니다.
전체 구조와 함수 상세는 [README.md](README.md)를 참고하세요.

---

## 1. 사전 준비 — secrets.toml 생성

`.streamlit/secrets.toml` 파일을 만들고 대상 서버(AccessURLServer) 접속 정보를 등록합니다.

```toml
AccessURLServerIP = "127.0.0.1"
AccessURLServerPort = "8001"
```

- 이 파일은 `.gitignore`에 등록되어 있어 git에 커밋되지 않습니다.
- 값이 없거나 파일이 없어도 서버는 실행되지만, 모든 요청이 fallback json
  (`access_url_server_connecting_fail`)으로 응답됩니다.
- Streamlit Community Cloud 배포 시에는 파일 대신
  앱 대시보드의 **Settings > Secrets**에 같은 내용을 등록합니다.

---

## 2. 서버 실행 — 진입점은 relay_server.py 하나

실행 파일은 `relay_server.py` **하나뿐**입니다.
`relay_app.py`는 직접 실행하는 파일이 아니라, `relay_server.py`의 `st.App(...)`이
`/` 경로의 UI 스크립트로 불러다 쓰는 파일입니다.

```bash
.venv\Scripts\python.exe relay_server.py
```

실행하면 터미널에 접속 정보가 출력됩니다.

```
============================================================
 중계서버 (Streamlit) 시작
  - Local URL   : http://localhost:8002
  - Network URL : http://192.168.0.60:8002
  - JSON API    : http://localhost:8002/api/get-app-link
============================================================
```

서비스 ip/port 변경은 `config.ini`에서 합니다 (기본 `0.0.0.0:8002`).

---

## 3. 사용 방법 — 접속하는 URL로 갈린다

서버는 한 번만 띄우고, **접속하는 경로에 따라 사용 방법이 나뉩니다.**
두 경로 모두 내부적으로 같은 `relay_core.fetch_relay_data()`를 호출합니다.

| 구분 | 접속 주소 | 대상 | 동작 |
|------|-----------|------|------|
| 사용방법 1 — 브라우저 화면 | `http://localhost:8002/` | 사람 (브라우저) | `relay_app.py`가 UI로 렌더링. AccessURLServer **접속 성공/실패 여부만** 표시 (json 내용은 터미널에만 출력) |
| 사용방법 2 — 순수 json | `http://localhost:8002/api/get-app-link` | 에이전트, 외부 프로그램 | 화면 없이 **순수 json**만 HTTP 응답으로 반환 |

두 주소는 완전히 독립적입니다. JSON API만 호출해도 되며,
UI를 먼저 접속할 필요가 없습니다.

### 사용방법 1 — 브라우저 화면 (접속 여부 확인)

브라우저에서 `http://localhost:8002/` (또는 Network URL)에 접속합니다.

- 접속 성공: 초록색 "AccessURLServer 접속 성공"
- 접속 실패: 빨간색 "AccessURLServer 접속 실패"
- 보안상 json 내용(접속 URL 등)은 화면에 표시하지 않고 서버 터미널에만 출력됩니다.

### 사용방법 2 — JSON API (에이전트 / 외부 프로그램)

`/api/get-app-link`를 GET 하면 화면 없이 json만 반환됩니다.

```bash
$ curl http://localhost:8002/api/get-app-link
{"access_url":"http://127.0.0.1:8000/access/9pKiBM2BDefLZRe..."}   # 성공

# AccessURLServer가 꺼져 있는 경우 (HTTP 200 + fallback json)
{"access_url":"http://127.0.0.1:8000/access/access_url_server_connecting_fail"}
```

- 접속 실패 시에도 HTTP 200으로 응답하므로, 상태코드가 아니라
  `access_url` 값에 `access_url_server_connecting_fail` 포함 여부로 성공/실패를 판단합니다.
- 매 요청마다 AccessURLServer를 새로 조회하므로 호출 시점마다 최신 값을 받습니다.
- Streamlit Cloud 배포 시 주소:
  `https://agentproxy-dyvnlgzif2bmxrt4tacamw.streamlit.app/api/get-app-link`

---

## 4. 주의사항

- `relay_app.py`를 `streamlit run relay_app.py`로 단독 실행하면 UI는 뜨지만
  `/api/get-app-link` 라우트가 없어 JSON API는 동작하지 않습니다.
  반드시 `relay_server.py`를 실행하세요.
- secrets.toml의 키 이름은 `AccessURLServerIP` / `AccessURLServerPort`입니다
  (URL 철자 주의 — `AccessULServerIP` 등 오타 시 fallback으로 동작).

## 5. 통신 구간별 프로토콜 (HTTP / HTTPS)

| 구간 | 프로토콜 |
|------|----------|
| 외부 → 중계서버 (Streamlit Cloud 배포) | **HTTPS** (플랫폼이 TLS 처리) |
| 외부 → 중계서버 (로컬 직접 실행) | **HTTP** (`http://<IP>:8002`, TLS 설정 없음) |
| 중계서버 → AccessURLServer | **항상 HTTP** (`relay_core.py`에서 `http://` 고정) |
