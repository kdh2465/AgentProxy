# -*- coding: utf-8 -*-
"""중계서버 Streamlit UI 스크립트

보안상 브라우저에는 서비스 이름과 접속 성공/실패 여부만 표시하고,
조회된 json 은 터미널(콘솔)에만 출력한다.
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

log("응답 결과 (json)")
print(json.dumps(data, ensure_ascii=False, indent=2), flush=True)
