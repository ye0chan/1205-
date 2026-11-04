"""Streamlit Community Cloud: app.py + requirements.txt.
실행: streamlit run app.py
환산은 공식 입시 환산이 아닌 선형 참고 지표입니다.
"""
from __future__ import annotations

import math
import pandas as pd
import streamlit as st

SEMESTERS = ["1학년 1학기", "1학년 2학기", "2학년 1학기", "2학년 2학기", "3학년 1학기"]
MODES = [
    ("⚖️ 꾸준히 페이스", "남은 학기마다 같은 평균등급을 목표로 해요.", 0),
    ("🚀 차근차근 레벨업", "첫 학기의 부담을 줄이고, 이후 학기마다 더 좋은 등급에 도전해요.", -1),
    ("🔥 먼저 달리고 여유롭게", "초반에 좋은 등급을 확보하고, 뒤 학기의 부담을 줄여요.", 1),
]


def to_nine(grade: float) -> float:
    return 2.0 * grade - 1.0


def to_five(grade: float) -> float:
    return (grade + 1.0) / 2.0


def make_plan(mean: float, count: int, direction: int) -> list[float]:
    """Bounded monotone plans with the exact requested mean, without rounding.

    direction -1: grades decrease (improve); +1: grades increase (ease).
    A fixed 0.5-grade/semester slope is projected onto [1,5] by shifting
    and clipping. Saturation can produce equal neighboring grades.
    """
    if count <= 0:
        return []
    if not 1.0 - 1e-9 <= mean <= 5.0 + 1e-9:
        raise ValueError("필요 평균은 1~5등급이어야 합니다.")
    mean = min(5.0, max(1.0, mean))
    if direction == 0 or count == 1:
        return [mean] * count
    offsets = [direction * 0.5 * (i - (count - 1) / 2) for i in range(count)]
    lo, hi = -10.0, 10.0
    for _ in range(100):
        mid = (lo + hi) / 2
        values = [min(5.0, max(1.0, mid + offset)) for offset in offsets]
        if sum(values) / count < mean:
            lo = mid
        else:
            hi = mid
    return [min(5.0, max(1.0, (lo + hi) / 2 + offset)) for offset in offsets]


def main() -> None:
    st.set_page_config(page_title="내신 페이스메이커", page_icon="🎯", layout="wide")
    st.markdown("""
    <style>
    .stApp {background: #f7f9fc;}
    .block-container {max-width: 1120px; padding-top: 1.8rem;}
    h1, h2, h3 {letter-spacing: -0.04em;}
    div[data-testid="stMetric"] {background: white; border: 1px solid #e2e8f0;
        padding: 18px; border-radius: 16px;}
    div[data-testid="stMetricValue"] {color: #2563eb;}
    .hero {position: sticky; top: 3.75rem; z-index: 50; background: #102344;
        color: white; border-radius: 18px; padding: 18px 24px; margin: 8px 0 18px;
        box-shadow: 0 8px 24px rgba(16,35,68,.12);}
    .hero small {color: #cbd5e1;}
    .hero strong {font-size: 2rem; color: #93c5fd; margin-right: 8px;}
    @media (max-width: 640px) {
        .hero {top: 3.5rem; padding: 14px 16px;}
        .hero strong {font-size: 1.55rem;}
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("🎯 내신 페이스메이커")
    st.caption("지금의 성적을 확인하고, 3학년 1학기까지 나만의 목표 페이스를 찾아보세요.")
    st.info("참고용 시뮬레이터입니다. 9등급제 참고값 = 5등급제 평균 × 2 − 1. "
            "실제 석차·대학별 환산등급이 아니며, 각 학기는 같은 비중으로 계산합니다.")

    with st.sidebar:
        st.header("📝 성적 입력")
        st.caption("성적이 확정된 마지막 학기까지만 입력하세요. 등급은 숫자가 작을수록 좋습니다.")
        latest = st.selectbox("성적이 나온 마지막 학기", SEMESTERS, index=1)
        completed = SEMESTERS.index(latest) + 1
        current: list[float] = []
        for i, label in enumerate(SEMESTERS[:completed]):
            current.append(st.number_input(
                f"{label} 평균 · 5등급제", min_value=1.0, max_value=5.0,
                value=3.0, step=0.01, format="%.2f", key=f"semester_{i}",
                help="해당 학기의 평균등급을 입력하세요. 예: 2.35",
            ))
        st.divider()
        target9 = st.number_input("최종 목표 평균 · 9등급제 참고값", min_value=1.0,
                                  max_value=9.0, value=4.0, step=0.01, format="%.2f",
                                  help="3학년 1학기까지 총 5개 학기의 최종 평균 목표입니다.")
        st.caption(f"5등급제 목표로는 {to_five(target9):.2f}등급에 해당합니다.")
        st.caption("입력값은 별도로 저장하지 않습니다. 공용 기기에서는 사용 후 창을 닫으세요.")

    mean5 = sum(current) / completed
    mean9 = to_nine(mean5)
    remaining = 5 - completed
    # Native HTML only contains numbers calculated locally, never user text.
    st.markdown(f"""<div class="hero"><small>현재 누적 평균 · 9등급제 참고값</small><br>
        <strong>{mean9:.2f}등급</strong> <span>5등급제 {mean5:.2f} · {completed}개 학기 반영</span>
        </div>""", unsafe_allow_html=True)

    left, middle, right = st.columns(3)
    left.metric("최종 목표 · 9등급제 참고값", f"{target9:.2f}등급")
    middle.metric("남은 학기", f"{remaining}개")
    best9 = to_nine((sum(current) + remaining) / 5)
    worst9 = to_nine((sum(current) + remaining * 5) / 5)
    right.metric("전 학기 1등급 시 최종 참고값", f"{best9:.2f}등급")

    st.subheader("🧭 나의 목표 로드맵")
    if remaining == 0:
        if mean9 <= target9 + 1e-9:
            st.success(f"5개 학기 입력이 완료되었고, 목표를 충족했습니다! 최종 참고값은 {mean9:.2f}등급입니다.")
        else:
            st.warning(f"입력이 완료되었습니다. 최종 참고값은 {mean9:.2f}등급이며 목표보다 {mean9-target9:.2f}등급 높습니다. 남은 학기가 없어 로드맵을 만들지 않습니다.")
    else:
        required = (5 * to_five(target9) - sum(current)) / remaining
        if required < 1.0 - 1e-9:
            st.error(f"입력한 조건에서 목표 달성은 어렵습니다. 남은 학기를 모두 1.00등급으로 받아도 최종 참고값은 {best9:.2f}등급입니다.")
            st.caption("아래 3가지 모드는 모두 최선의 성적인 1.00등급으로 안내합니다. 입력한 목표를 달성하는 계획은 아닙니다.")
            plan_mean = 1.0
        elif required > 5.0 + 1e-9:
            st.success(f"이미 충분한 여유가 있어요! 남은 학기를 모두 5.00등급으로 받아도 최종 참고값 {worst9:.2f}등급으로 목표를 충족합니다.")
            st.caption("목표와 정확히 같은 평균은 만들 수 없어, 아래에는 목표를 충족하는 가장 여유로운 계획을 표시합니다.")
            plan_mean = 5.0
        else:
            plan_mean = min(5.0, max(1.0, required))
            st.success(f"목표 달성에 필요한 남은 학기 평균: 5등급제 {plan_mean:.2f}등급 · 9등급제 참고값 {to_nine(plan_mean):.2f}등급")

        tabs = st.tabs([mode[0] for mode in MODES])
        for tab, (title, description, direction) in zip(tabs, MODES):
            with tab:
                st.markdown(f"### {title}")
                st.write(description)
                plan = make_plan(plan_mean, remaining, direction)
                # Round DOWN (better grade) so displayed 2-decimal targets do not
                # accidentally miss the target due to conventional rounding.
                shown = [math.floor((value + 1e-9) * 100) / 100 for value in plan]
                final9 = to_nine((sum(current) + sum(shown)) / 5)
                rows = []
                cumulative = sum(current)
                for j, value in enumerate(shown):
                    cumulative += value
                    rows.append({
                        "학기": SEMESTERS[completed + j],
                        "목표 평균 · 5등급제": value,
                        "9등급제 참고값": to_nine(value),
                        "달성 시 누적 · 9등급제 참고값": to_nine(cumulative / (completed + j + 1)),
                    })
                st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True,
                             column_config={col: st.column_config.NumberColumn(format="%.2f")
                                            for col in rows[0] if col != "학기"})
                st.metric("이 계획대로 달성할 때 최종 · 9등급제 참고값", f"{final9:.2f}등급")
                chart = pd.DataFrame({
                    "학기": SEMESTERS,
                    "현재 성적": current + [None] * remaining,
                    "계획": [None] * (completed - 1) + [current[-1]] + shown,
                }).set_index("학기")
                st.line_chart(chart, y_label="5등급제 평균 (낮을수록 우수)", color=["#94a3b8", "#2563eb"])
                if remaining == 1:
                    st.caption("남은 학기가 1개이므로 세 모드의 목표가 같습니다.")
                elif max(shown) - min(shown) < 0.01:
                    st.caption("등급의 최솟값·최댓값 제약으로 세 모드의 목표가 같을 수 있습니다.")
                st.caption("표의 목표 평균 또는 그보다 더 좋은 성적을 목표로 하세요. 목표 미달을 방지하도록 소수 셋째 자리 이하는 버렸습니다. 차트는 위쪽일수록 등급 숫자가 크므로, 성적 향상은 선이 내려가는 모습입니다.")

    with st.expander("계산 방식과 꼭 알아둘 점"):
        st.markdown("""
- **공식 환산이 아닙니다.** 학기 평균만으로 실제 석차 분포를 복원할 수 없습니다. 이 앱은 학습 계획용 선형 참고 지표를 사용합니다.
- **환산식:** 9등급제 참고값 = 2 × 5등급제 평균 − 1. 예: 1 → 1, 2 → 3, 3 → 5, 4 → 7, 5 → 9.
- **반영 범위:** 1학년 1학기부터 3학년 1학기까지 총 5개 학기. 학기별 동일 비중이며 과목별 단위수나 대학별 가중치는 반영하지 않습니다.
- **필요 평균:** (목표 5등급제 평균 × 5 − 입력한 학기 평균의 합) ÷ 남은 학기 수.
- **목표 충족:** 최종 평균이 목표 숫자 이하이면 충족입니다. 1등급이 가장 좋습니다.
- **모드:** 균등 / 점진적 향상 / 초반 집중. 변화형은 기본적으로 학기당 0.50등급 차이를 주고, 1~5 범위를 벗어나면 경계에서 제한한 뒤 전체 평균을 다시 맞춥니다. 경계에서는 일부 학기의 목표가 같아질 수 있습니다.
- 성적이나 목표를 바꾸면 즉시 다시 계산합니다. 마지막 학기를 바꾸면 그 이후 성적은 계산에서 제외됩니다.
- 실제 대학 지원에는 대학이 발표한 성적 산출 방식과 모집요강을 확인하세요.
        """)
    st.caption("내신 페이스메이커 · 성적은 판단이 아니라, 다음 계획을 위한 출발점입니다.")


if __name__ == "__main__":
    main()
