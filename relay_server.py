# -*- coding: utf-8 -*-
"""중계서버 (Relay server)

요청이 들어오면 secrets.toml 의 AccessURLServerIP / AccessURLServerPort 서버에 접속해
json 정보를 읽어 요청한 곳으로 그대로 반환(표시)한다.
(Streamlit Community Cloud 배포 시 앱 설정 > Secrets 에 두 키를 등록한다)

실행:  python relay_server.py
  - streamlit ip / port 는 config.ini 에서 읽는다 (기본 port 8002)
"""

import configparser
import socket
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.ini"

DEFAULT_IP = "0.0.0.0"
DEFAULT_PORT = 8002


def load_streamlit_config():
    """config.ini 에서 streamlit 서비스 ip / port 를 읽는다."""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE, encoding="utf-8")
    ip = config.get("streamlit", "ip", fallback=DEFAULT_IP).strip()
    port = config.getint("streamlit", "port", fallback=DEFAULT_PORT)
    return ip, port


def get_local_ip():
    """외부 접속용 로컬 네트워크 IP를 조회한다."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


# ---------------------------------------------------------------------------
# Streamlit 앱 본문 (streamlit 런타임에서 실행될 때)
# ---------------------------------------------------------------------------
def run_app():
    # 보안상 브라우저에는 서비스 이름만 표시하고,
    # 조회된 내용은 터미널(콘솔)에만 출력한다.
    import json
    from datetime import datetime

    import requests
    import streamlit as st

    st.set_page_config(page_title="HYW RelayServer", page_icon=":material/hub:")
    st.title("HYW RelayServer")

    def log(message):
        print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {message}", flush=True)

    try:
        access_ip = str(st.secrets.get("AccessURLServerIP", "")).strip()
        access_port = str(st.secrets.get("AccessURLServerPort", "")).strip()
    except FileNotFoundError:
        access_ip = access_port = ""

    if not access_ip or not access_port:
        log("secrets.toml 에 AccessURLServerIP / AccessURLServerPort 가 설정되어 있지 않습니다.")
        st.error("AccessURLServer 접속 실패", icon=":material/link_off:")
        st.stop()

    target_url = f"http://{access_ip}:{access_port}/get-app-link"
    log(f"요청 수신 -> 대상 서버 조회: {target_url}")

    try:
        response = requests.get(target_url, timeout=5)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as exc:
        log(f"대상 서버 접속 실패: {exc}")
        st.error("AccessURLServer 접속 실패", icon=":material/link_off:")
        st.stop()
    except ValueError:
        log("대상 서버 응답이 json 형식이 아닙니다.")
        st.error("AccessURLServer 접속 실패", icon=":material/link_off:")
        st.stop()

    st.success("AccessURLServer 접속 성공", icon=":material/link:")

    log("응답 결과 (json)")
    print(json.dumps(data, ensure_ascii=False, indent=2), flush=True)


# ---------------------------------------------------------------------------
# 직접 실행 진입점: python relay_server.py
# ---------------------------------------------------------------------------
def main():
    ip, port = load_streamlit_config()
    display_host = "localhost" if ip in ("", "0.0.0.0") else ip

    print("=" * 60)
    print(" 중계서버 (Streamlit) 시작")
    print(f"  - Local URL   : http://{display_host}:{port}")
    if ip in ("", "0.0.0.0"):
        print(f"  - Network URL : http://{get_local_ip()}:{port}")
    print("=" * 60, flush=True)

    from streamlit.web import cli as stcli

    sys.argv = [
        "streamlit",
        "run",
        str(Path(__file__).resolve()),
        f"--server.address={ip}",
        f"--server.port={port}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ]
    sys.exit(stcli.main())


if __name__ == "__main__":
    from streamlit import runtime

    if runtime.exists():
        run_app()
    else:
        main()
