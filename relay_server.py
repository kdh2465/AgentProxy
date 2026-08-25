# -*- coding: utf-8 -*-
"""중계서버 (Relay server) 실행 진입점

- 브라우저 UI      : /                  (relay_app.py — 접속 성공/실패만 표시)
- JSON API 엔드포인트: /api/get-app-link  (에이전트 등 외부 프로그램용, 순수 json 반환)

실행:  python relay_server.py
  - streamlit ip / port 는 config.ini 에서 읽는다 (기본 port 8002)
  - Streamlit Community Cloud 에서는 이 파일을 메인 파일로 지정하면
    streamlit run 이 st.App 래퍼를 자동 인식하여 실행한다.
"""

import configparser
import socket
import sys
from pathlib import Path

import streamlit as st
from starlette.responses import JSONResponse
from starlette.routing import Route

from relay_core import fetch_relay_data

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


def get_app_link(request):
    """JSON API: AccessURLServer 에서 읽어온 json 을 그대로 반환한다.

    접속 실패 시에도 HTTP 200 으로 fallback json 을 반환한다.
    """
    data, _success = fetch_relay_data()
    return JSONResponse(data)


app = st.App(
    str(BASE_DIR / "relay_app.py"),
    routes=[Route("/api/get-app-link", get_app_link)],
)


if __name__ == "__main__":
    ip, port = load_streamlit_config()
    display_host = "localhost" if ip in ("", "0.0.0.0") else ip

    print("=" * 60)
    print(" 중계서버 (Streamlit) 시작")
    print(f"  - Local URL   : http://{display_host}:{port}")
    if ip in ("", "0.0.0.0"):
        print(f"  - Network URL : http://{get_local_ip()}:{port}")
    print(f"  - JSON API    : http://{display_host}:{port}/api/get-app-link")
    print("=" * 60, flush=True)

    sys.exit(
        app.run(
            config={
                "server.address": ip,
                "server.port": port,
                "server.headless": True,
                "browser.gatherUsageStats": False,
            }
        )
    )
