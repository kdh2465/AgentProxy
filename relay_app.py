# -*- coding: utf-8 -*-
"""중계서버 Streamlit UI 스크립트

브라우저에 서비스 이름, 접속 성공/실패 여부, DynamicAccess 호출 URL(access_url)을
표시한다. 조회된 전체 json 은 터미널(콘솔)에도 출력한다.
"""

import json

import streamlit as st

from relay_core import fetch_relay_data, log

st.set_page_config(page_title="HYW RelayServer", page_icon=":material/hub:")
st.title("HYW RelayServer")

data, success = fetch_relay_data()

if success:
    st.success("AccessURLServer 접속 성공", icon=":material/link:")
else:
    st.error("AccessURLServer 접속 실패", icon=":material/link_off:")

access_url = data.get("access_url", "")
if access_url:
    st.subheader("DynamicAccess 호출 URL")
    st.code(access_url, language=None)

log("응답 결과 (json)")
print(json.dumps(data, ensure_ascii=False, indent=2), flush=True)
