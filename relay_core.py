# -*- coding: utf-8 -*-
"""중계서버 공용 로직

secrets.toml 의 AccessURLServerIP / AccessURLServerPort 서버에 접속해
json 을 읽어온다. UI(relay_app.py)와 API 라우트(relay_server.py)가 공용으로 사용한다.
"""

import configparser
from datetime import datetime
from pathlib import Path

import requests
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.ini"

# DynamicAccess 조회 timeout 기본값 (초). config.ini [relay] timeout 으로 변경 가능.
DEFAULT_TIMEOUT = 5

# 접속 실패 시 반환할 기본(fallback) json
FALLBACK_DATA = {
    "access_url": "http://127.0.0.1:8000/access/access_url_server_connecting_fail"
}


def log(message):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {message}", flush=True)


def get_request_timeout():
    """config.ini [relay] timeout (초). 없거나 잘못된 값이면 기본값 사용."""
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE, encoding="utf-8")
    try:
        timeout = config.getfloat("relay", "timeout", fallback=DEFAULT_TIMEOUT)
    except ValueError:
        log(f"config.ini 의 [relay] timeout 값이 숫자가 아닙니다. 기본값 {DEFAULT_TIMEOUT}초 사용.")
        return DEFAULT_TIMEOUT
    if timeout <= 0:
        log(f"config.ini 의 [relay] timeout 은 0보다 커야 합니다. 기본값 {DEFAULT_TIMEOUT}초 사용.")
        return DEFAULT_TIMEOUT
    return timeout


def _read_access_server_secrets():
    """secrets 에서 AccessURLServer(DynamicAccess) ip / port 를 읽는다."""
    try:
        access_ip = str(st.secrets.get("AccessURLServerIP", "")).strip()
        access_port = str(st.secrets.get("AccessURLServerPort", "")).strip()
    except FileNotFoundError:
        access_ip = access_port = ""
    return access_ip, access_port


def get_target_url():
    """DynamicAccess(AccessURLServer) 조회 URL. secrets 미설정 시 빈 문자열."""
    access_ip, access_port = _read_access_server_secrets()
    if not access_ip or not access_port:
        return ""
    return f"http://{access_ip}:{access_port}/get-app-link"


def fetch_relay_data():
    """AccessURLServer 에서 json 을 읽어온다.

    반환: (data, success)
      - 성공: (받아온 json, True)
      - 실패: (FALLBACK_DATA, False)  # 서버 미응답, json 형식 오류, secrets 미설정 포함
    """
    target_url = get_target_url()

    if not target_url:
        log("AccessURLServerIP / AccessURLServerPort 값이 없습니다.")
        log("`.streamlit/secrets.toml` 파일을 먼저 작성해 주세요. 예:")
        log('  AccessURLServerIP = "127.0.0.1"')
        log('  AccessURLServerPort = "8001"')
        return FALLBACK_DATA, False

    timeout = get_request_timeout()
    log(f"요청 수신 -> 대상 서버 조회: {target_url} (timeout {timeout:g}초)")

    try:
        response = requests.get(target_url, timeout=timeout)
        response.raise_for_status()
        return response.json(), True
    except requests.exceptions.RequestException as exc:
        log(f"대상 서버 접속 실패: {exc}")
    except ValueError:
        log("대상 서버 응답이 json 형식이 아닙니다.")

    return FALLBACK_DATA, False
