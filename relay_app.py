# -*- coding: utf-8 -*-
"""중계서버 Streamlit UI 스크립트

브라우저에 서비스 이름, 접속 성공/실패 여부, DynamicAccess 서버 자체의 URL
(secrets 의 AccessURLServerIP:Port)을 표시한다.
DynamicAccess 로부터 받아온 json(access_url)은 화면에 노출하지 않고
터미널(콘솔)에만 출력한다.
"""

import json

import streamlit as st

from relay_core import fetch_relay_data, get_target_url, log

st.set_page_config(page_title="HYW RelayServer", page_icon=":material/hub:")
st.title("HYW RelayServer")

data, success = fetch_relay_data()

if success:
    st.success("AccessURLServer 접속 성공", icon=":material/link:")
else:
    st.error("AccessURLServer 접속 실패", icon=":material/link_off:")

target_url = get_target_url()
st.subheader("DynamicAccess 서버 URL")
if target_url:
    st.code(target_url, language=None)
else:
    st.warning("secrets 미설정 — `.streamlit/secrets.toml` 을 먼저 작성해 주세요.")

log("응답 결과 (json)")
print(json.dumps(data, ensure_ascii=False, indent=2), flush=True)
