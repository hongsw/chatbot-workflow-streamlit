import streamlit as st
from openai import OpenAI
import pandas as pd
import json

MODEL = "gpt-4o-mini"  # 필요시 "gpt-3.5-turbo" 로 변경 가능

st.title("💬 Chatbot + CSV 상품 매출 분석 (Function Calling Workflow)")
st.write(
    "CSV를 업로드한 뒤, 채팅창에 **'상품매출분석 해줘'** 같은 요청을 하면\n"
    "Function Calling으로 Intent를 판별하고, LLM이 CSV 일부를 보고 매출 분석 + 워크플로우를 작성합니다."
)

# 1. API 키 입력
openai_api_key = st.text_input("OpenAI API Key", type="password")

# 2. CSV 업로드
uploaded_file = st.file_uploader("CSV 파일 업로드", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.session_state["sales_df"] = df
    st.caption(f"업로드된 CSV 컬럼: {list(df.columns)}")
    st.dataframe(df.head())
else:
    df = st.session_state.get("sales_df", None)

if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
    st.stop()

client = OpenAI(api_key=openai_api_key)

# 3. 대화 상태
if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. 기존 메시지 렌더링
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 5. Function 정의 (Intent 판별용)
tools = [
    {
        "type": "function",
        "function": {
            "name": "sales_analysis_intent",
            "description": "사용자의 입력이 상품 매출 분석(업로드된 CSV 기반)을 요구하는지 판별한다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "is_sales_analysis": {
                        "type": "boolean",
                        "description": "요청이 상품 매출 분석이면 true, 그렇지 않으면 false."
                    },
                    "reason": {
                        "type": "string",
                        "description": "그렇게 판단한 이유를 한국어로 간단히 설명."
                    }
                },
                "required": ["is_sales_analysis"]
            },
        },
    }
]

# 6. 새 입력
if prompt := st.chat_input("메시지를 입력하세요"):
    # 사용자 메시지 저장/표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # ① Intent 판별용 Function Calling 호출
    intent_resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "너는 Intent 분류기다. 사용자가 업로드한 CSV 기반으로 "
                    "'상품 매출 분석', '상품 매출 요약', '매출 현황 분석' 등을 요청하면 "
                    "sales_analysis_intent 함수를 호출해서 is_sales_analysis=true 로 설정해라. "
                    "일반 잡담이면 false."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        tools=tools,
        tool_choice="auto",
    )

    is_sales_analysis = False
    tool_calls = intent_resp.choices[0].message.tool_calls
    if tool_calls:
        for tc in tool_calls:
            if tc.function.name == "sales_analysis_intent":
                args = json.loads(tc.function.arguments)
                is_sales_analysis = bool(args.get("is_sales_analysis", False))

    # ② Intent 결과에 따라 분기
    if is_sales_analysis:
        # --- 상품 매출 분석 워크플로우 (LLM 프롬프트 기반 분석) ---
        with st.chat_message("assistant"):
            if df is None:
                # CSV 없음
                msg = (
                    "CSV 파일이 업로드되지 않아 상품 매출 분석을 할 수 없습니다.\n\n"
                    "1. CSV 파일을 업로드한다.\n"
                    "2. 파일 구조(상품명, 매출액 등)를 확인한다.\n"
                    "3. 다시 '상품매출분석 해줘' 라고 요청한다."
                )
                st.markdown(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})
            else:
                # CSV 일부만 프롬프트로 전달 (토큰 절약)
                preview_rows = min(len(df), 50)
                preview_md = df.head(preview_rows).to_markdown(index=False)

                analysis_messages = [
                    {
                        "role": "system",
                        "content": (
                            "너는 데이터 분석가다. 사용자가 업로드한 CSV의 일부를 보고 "
                            "상품 매출 분석을 수행한다. 답변은 한국어로 한다.\n\n"
                            "반드시 아래 두 섹션을 포함해서 답해라:\n"
                            "## 분석 결과\n"
                            "- 상위 매출 상품 요약\n"
                            "- 매출 분포/특징\n"
                            "- 눈에 띄는 인사이트\n\n"
                            "## Workflow\n"
                            "너가 내부적으로 수행했다고 가정하는 단계들을 4~7단계 정도로 번호 매겨 적어라.\n"
                            "예) 1) 데이터 구조 파악, 2) 상품/매출 컬럼 식별, 3) 그룹화 및 합계 계산, ..."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            "다음은 업로드된 상품 매출 CSV의 일부입니다 "
                            f"(상위 {preview_rows}행만 포함):\n\n"
                            f"{preview_md}\n\n"
                            "이 데이터를 기반으로 상품 매출 분석을 해줘."
                        ),
                    },
                ]

                analysis_stream = client.chat.completions.create(
                    model=MODEL,
                    messages=analysis_messages,
                    stream=True,
                )

                analysis_text = st.write_stream(analysis_stream)
                st.session_state.messages.append(
                    {"role": "assistant", "content": analysis_text}
                )
    else:
        # --- 일반 대화: 기존 GPT 스트리밍 ---
        stream = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )
        with st.chat_message("assistant"):
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})
