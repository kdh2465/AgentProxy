# AgentProxy — HYW RelayServer (중계서버)

Streamlit 기반의 **중계서버(Relay Server)** 입니다.
요청이 들어오면 secrets에 등록된 **AccessURLServer**(`AccessURLServerIP:AccessURLServerPort`)의
`/get-app-link` 엔드포인트에 접속하여 json을 읽어오고, 그 값을 요청한 곳으로 반환합니다.

- 로컬 실행: `python relay_server.py` 한 줄로 바로 실행
- 클라우드 서비스: Streamlit Community Cloud 배포 지원
  (서비스 주소: https://agentproxy-dyvnlgzif2bmxrt4tacamw.streamlit.app/)

---

## 1. 전체 동작 구조

```
[에이전트 / 외부 프로그램]                [사람 (브라우저)]
        │                                     │
        │ GET /api/get-app-link               │ GET /  (Network URL)
        ▼                                     ▼
┌─────────────────────────────────────────────────────────┐
│              HYW RelayServer (Streamlit, st.App)        │
│                                                         │
│   /api/get-app-link ──► get_app_link()   (순수 JSON 응답)│
│   /                 ──► relay_app.py     (UI 화면 표시) │
│                └── 둘 다 relay_core.fetch_relay_data() 사용│
└──────────────────────────┬──────────────────────────────┘
                           │ GET http://{IP}:{PORT}/get-app-link
                           ▼
                  [AccessURLServer]
                  json 반환 예: {"access_url": "http://127.0.0.1:8000/access/..."}
```

1. 요청이 들어오면 중계서버가 secrets의 `AccessURLServerIP` / `AccessURLServerPort`로
   대상 서버(`http://IP:PORT/get-app-link`)에 접속해 json을 읽습니다.
2. **접속 성공** 시: AccessURLServer에서 받아온 json을 그대로 반환합니다.
3. **접속 실패** 시(서버 미응답, json 형식 오류, secrets 미설정 포함): 아래의 fallback json을 반환합니다.
   ```json
   {"access_url": "http://127.0.0.1:8000/access/access_url_server_connecting_fail"}
   ```
4. 보안상 브라우저 화면에는 json 내용을 표시하지 않고, 서버 터미널(콘솔)에만 출력합니다.

---

## 2. 접속 주소별 기능 (Network URL vs JSON API URL)

서버 실행 시 터미널에 두 종류의 접속 정보가 출력됩니다.

| 구분 | 주소 (로컬 실행 기준) | 대상 | 기능 |
|------|----------------------|------|------|
| **Local / Network URL** | `http://localhost:8002/`, `http://<내부IP>:8002/` | 사람 (브라우저) | UI 화면. "HYW RelayServer" 제목과 AccessURLServer **접속 성공/실패 여부만** 표시. json 내용은 화면에 노출하지 않음 (터미널에만 출력) |
| **JSON API URL** | `http://localhost:8002/api/get-app-link` | 에이전트, 외부 프로그램 | HTML이 아닌 **순수 json**을 HTTP 응답으로 반환. 접속 실패 시에도 HTTP 200으로 fallback json 반환 |

두 주소는 **완전히 독립적**입니다. JSON API만 호출해도 되며, UI(Network URL)를 먼저 접속할 필요가
없습니다. 각 요청마다 AccessURLServer를 새로 조회하므로 호출 시점마다 최신 값을 받습니다.

- Network URL은 같은 네트워크(공유기/사내망)의 다른 기기에서 접속할 때 사용합니다.
- Streamlit Cloud 배포 시 JSON API 주소는
  `https://agentproxy-dyvnlgzif2bmxrt4tacamw.streamlit.app/api/get-app-link` 입니다.

### JSON API 응답 예시

```bash
$ curl http://localhost:8002/api/get-app-link
{"access_url":"http://127.0.0.1:8000/access/9pKiBM2BDefLZRe..."}   # 성공: 받아온 json 그대로

# AccessURLServer가 꺼져 있는 경우
{"access_url":"http://127.0.0.1:8000/access/access_url_server_connecting_fail"}   # 실패: fallback
```

---

## 3. 파일 구성

| 파일 | 역할 |
|------|------|
| `relay_server.py` | **실행 진입점**. st.App 래퍼로 UI와 JSON API 라우트를 함께 서비스 |
| `relay_app.py` | Streamlit **UI 스크립트** (브라우저 화면) |
| `relay_core.py` | **공용 중계 로직** (AccessURLServer 조회). UI와 API가 함께 사용 |
| `config.ini` | 중계서버(Streamlit) 서비스 **ip / port 설정** (기본 port 8002) |
| `.streamlit/secrets.toml` | **AccessURLServer 접속 정보** (git에 커밋되지 않음) |
| `requirements.txt` | 의존 패키지 (`streamlit`, `requests`) |
| `system_prompt.md` | 외부 에이전트 플랫폼용 시스템 프롬프트 |

---

## 4. 함수별 상세 설명

### relay_core.py — 공용 중계 로직

#### `FALLBACK_DATA` (상수)
접속 실패 시 반환할 기본 json.
`{"access_url": "http://127.0.0.1:8000/access/access_url_server_connecting_fail"}`
호출한 쪽(에이전트)은 `access_url` 값에 `access_url_server_connecting_fail` 문자열이
포함되어 있는지로 성공/실패를 구분할 수 있습니다.

#### `log(message)`
터미널(콘솔)에 `[YYYY-MM-DD HH:MM:SS] 메시지` 형식으로 타임스탬프를 붙여 출력합니다.
보안 요구사항에 따라 조회 내용/에러는 화면이 아닌 터미널에만 남기며, 모든 기록이 이 함수를 거칩니다.
`flush=True`로 즉시 출력을 보장합니다.

#### `fetch_relay_data() -> (data, success)`
중계 동작의 핵심 함수. AccessURLServer에서 json을 읽어옵니다.

처리 순서:
1. `st.secrets`에서 `AccessURLServerIP`, `AccessURLServerPort`를 읽습니다.
   secrets.toml 파일이 없으면(`FileNotFoundError`) 빈 값으로 처리합니다.
2. 두 값 중 하나라도 없으면 터미널에 안내를 남기고 `(FALLBACK_DATA, False)` 반환.
3. `http://{IP}:{PORT}/get-app-link`로 GET 요청 (timeout 5초).
4. HTTP 에러 상태코드는 `raise_for_status()`로 예외 처리.
5. 응답을 json으로 파싱해 성공 시 `(받아온 json, True)` 반환.
6. 실패(접속 불가, 타임아웃, HTTP 에러, json 파싱 실패) 시 원인을 터미널에 남기고
   `(FALLBACK_DATA, False)` 반환.

어떤 경우에도 예외를 밖으로 던지지 않고 항상 `(json, 성공여부)` 튜플을 반환하므로,
호출하는 쪽(UI/API)은 별도의 예외 처리가 필요 없습니다.

### relay_app.py — 브라우저 UI 스크립트

Streamlit이 페이지 요청마다 위에서 아래로 실행하는 스크립트입니다.

1. `st.set_page_config(...)` — 브라우저 탭 제목("HYW RelayServer")과 아이콘 설정.
2. `st.title("HYW RelayServer")` — 화면에 서비스 이름 표시.
3. `fetch_relay_data()` 호출 후:
   - 성공: `st.success("AccessURLServer 접속 성공")` (초록색 표시)
   - 실패: `st.error("AccessURLServer 접속 실패")` (빨간색 표시)
4. json 반환값은 화면에 표시하지 않고 `log()` + `print()`로 **터미널에만** 들여쓰기된
   json 형태로 출력합니다 (보안 요구사항).

### relay_server.py — 실행 진입점

#### `load_streamlit_config() -> (ip, port)`
`config.ini`의 `[streamlit]` 섹션에서 서비스 `ip` / `port`를 읽습니다.
파일이 없거나 값이 빠진 경우 기본값(`0.0.0.0`, `8002`)을 사용하므로 config.ini 없이도 동작합니다.

#### `get_local_ip() -> str`
Network URL 안내용 내부 네트워크 IP를 조회합니다.
UDP 소켓으로 외부 주소(8.8.8.8)에 connect하여 OS가 선택한 출구 인터페이스의 IP를 얻는
방식이며, 실제 패킷은 전송되지 않습니다. 실패 시 `127.0.0.1`을 반환합니다.

#### `get_app_link(request) -> JSONResponse`
`/api/get-app-link` 경로의 HTTP 핸들러 (Starlette 라우트).
요청이 올 때마다 `fetch_relay_data()`를 호출해 결과 json을 **순수 json 응답**으로 반환합니다.
접속 실패 시에도 HTTP 200으로 fallback json을 반환하므로, 호출 측은 상태코드가 아닌
`access_url` 값으로 성공/실패를 판단합니다. Streamlit 세션/쿠키와 무관하게 단독 호출 가능합니다.

#### `app = st.App(...)` (모듈 레벨)
Streamlit 1.57+의 ASGI 래퍼. UI 스크립트(`relay_app.py`)와 커스텀 라우트
(`/api/get-app-link`)를 하나의 서버로 묶습니다.
- `python relay_server.py` 직접 실행과
- `streamlit run relay_server.py` (Streamlit Cloud 방식) 모두 이 객체를 인식해 동작합니다.

#### `_runtime_exists() -> bool`
Streamlit 런타임이 이미 실행 중인지 확인합니다.
`streamlit run`(클라우드 포함)으로 실행되면 파일이 `__name__ == "__main__"` 상태로 실행되는데,
이때 `app.run()`을 또 호출하면 `StreamlitAPIException`이 발생합니다.
이를 막기 위해 main 가드에서 이 함수로 이중 실행을 차단합니다.

#### `if __name__ == "__main__" and not _runtime_exists():` (main 가드)
`python relay_server.py` 직접 실행 시에만 동작:
1. `load_streamlit_config()`로 ip/port를 읽고,
2. 터미널에 접속 정보(Local URL / Network URL / JSON API URL)를 출력한 뒤,
3. `app.run(config=...)`으로 서버를 기동합니다 (headless 모드, 사용 통계 수집 끔).

---

## 5. 설치 및 실행

### 로컬 실행

```bash
# 1) 가상환경 생성 및 패키지 설치
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 2) 대상 서버 정보 등록 (.streamlit/secrets.toml)
#    AccessURLServerIP = "127.0.0.1"
#    AccessURLServerPort = "8001"

# 3) 실행
.venv\Scripts\python.exe relay_server.py
```

실행하면 터미널에 접속 정보가 출력됩니다:

```
============================================================
 중계서버 (Streamlit) 시작
  - Local URL   : http://localhost:8002
  - Network URL : http://192.168.0.60:8002
  - JSON API    : http://localhost:8002/api/get-app-link
============================================================
```

### 설정 변경

- 서비스 포트/IP 변경: `config.ini`
  ```ini
  [streamlit]
  ip = 0.0.0.0
  port = 8002
  ```
- 대상(AccessURL) 서버 변경: `.streamlit/secrets.toml`
  ```toml
  AccessURLServerIP = "127.0.0.1"
  AccessURLServerPort = "8001"
  ```

### Streamlit Community Cloud 배포

1. GitHub 저장소를 연결하고 **메인 파일을 `relay_server.py`로 지정**합니다.
2. 앱 대시보드 **Settings > Secrets**에 아래 내용을 등록합니다.
   ```toml
   AccessURLServerIP = "실제서버IP"
   AccessURLServerPort = "포트"
   ```
3. 외부 에이전트가 접근해야 하면 **Settings > Sharing에서 공개(public)** 로 설정합니다.
   (비공개 상태면 접속 시 로그인 페이지로 303 리다이렉트되어 에이전트가 값을 읽지 못합니다.)
4. 클라우드에서는 ip/port를 플랫폼이 관리하므로 `config.ini`는 로컬 직접 실행에서만 적용됩니다.

---

## 6. 에이전트 연동

외부 에이전트 플랫폼에서는 JSON API URL 하나만 GET 하면 됩니다.

```
https://agentproxy-dyvnlgzif2bmxrt4tacamw.streamlit.app/api/get-app-link
```

- 응답 json의 `access_url` 값을 추출해 사용합니다.
- `access_url`에 `access_url_server_connecting_fail`이 포함되어 있으면 접속 실패로 처리합니다.
- 에이전트용 시스템 프롬프트는 `system_prompt.md`를 참고하세요.
- 도구 설정 시 base URL과 path를 분리해 받는 플랫폼이라면, path 칸에는
  `/api/get-app-link`처럼 **경로만** 넣어야 합니다 (전체 URL을 path에 넣으면
  "Path contains protocol ..." 류의 검증 에러가 발생).

---

## 7. 보안 참고사항

- json 반환값(접속 URL 등)은 브라우저 화면에 노출하지 않고 서버 터미널에만 출력합니다.
- `.streamlit/secrets.toml`과 `.env`는 `.gitignore`에 등록되어 git에 커밋되지 않습니다.
- Streamlit의 사용 통계 수집(`browser.gatherUsageStats`)을 끄고 실행합니다.
