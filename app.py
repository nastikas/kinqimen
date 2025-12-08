import urllib.request
import streamlit as st
import pendulum as pdlm
import datetime, pytz
from io import StringIO
from contextlib import contextmanager, redirect_stdout

import kinqimen
from kinliuren import kinliuren
import config

# ------------------- 工具 -------------------
@contextmanager
def st_capture(output_func):
    with StringIO() as stdout, redirect_stdout(stdout):
        old_write = stdout.write
        def new_write(string):
            ret = old_write(string)
            output_func(stdout.getvalue())
            return ret
        stdout.write = new_write
        yield

def fetch_md(file):
    url = f'https://raw.githubusercontent.com/kentang2017/kinliuren/master/{file}'
    return urllib.request.urlopen(url).read().decode("utf-8")

# ------------------- 頁面設定 -------------------
st.set_page_config(page_title="堅奇門 - 奇門排盤", page_icon="🧮", layout="wide")
pan, example, guji, log, links = st.tabs(['🧮 排盤', '📜 案例', '📚 古籍', '🆕 更新', '🔗 連結'])

with links:
    st.markdown(fetch_md("update.md"), unsafe_allow_html=True)
with log:
    st.markdown(fetch_md("log.md"), unsafe_allow_html=True)

# ------------------- 側邊欄 -------------------
with st.sidebar:
    pp_date = st.date_input("日期", pdlm.now(tz='Asia/Shanghai').date())
    pp_time = st.text_input('時間 (如 18:30)', '')
    method = st.selectbox('起盤方式', ('時家奇門', '刻家奇門'))
    paipan = st.selectbox('排盤方式', ('置閏', '拆補'))
    manual = st.button('手動起盤')
    instant = st.button('即時起盤')

    is_shijia = method == '時家奇門'
    pai = 2 if paipan == '置閏' else 1   # 1=拆補 2=置閏

# ------------------- 共用函數 -------------------
eg = list("巽離坤震兌艮坎乾")

def render_pan(y, m, d, h, minute, is_shijia=True):
    gz = config.gangzhi(y, m, d, h, minute)
    jq = config.jq(y, m, d, h,minute)
    lunar_mon = dict(zip(range(1,13), config.cmonth)).get(config.lunar_date_d(y,m,d)["月"])

    if is_shijia:
        q = kinqimen.Qimen(y, m, d, h, minute).pan(pai)
        lr = kinliuren.Liuren(q["節氣"], lunar_mon, gz[2], gz[3]).result(0)
    else:
        q = kinqimen.Qimen(y, m, d, h, minute).pan_minute(pai)
        lr = kinliuren.Liuren(q["節氣"], lunar_mon, gz[3], gz[4]).result(0)

    # 提取資料
    qd = [q["地盤"][k] for k in eg]
    qt = [q.get("天盤", {}).get(k, "") for k in eg]
    god = [q["神"][k] for k in eg]
    door = [q["門"][k] for k in eg]
    star = [q["星"][k] for k in eg]
    mid = q["地盤"]["中"]
    es, egod = lr["地轉天盤"], lr["地轉天將"]

    # 輸出文字盤面
    print(f"{'時家奇門' if is_shijia else '刻家奇門'} | {q['排盤方式']}")
    print(f"{y}年{m}月{d}日 {h}時{minute}分\n")
    print(f"{q['干支']} | {q['排局']} | 節氣：{jq}")
    print(f"值符星宮：天{zf_xing}宮　　值使門宮：{zm_men}門{zm_gong}宮")
    print(f"農曆月：{config.lunar_date_d(y,m,d)['農曆月']}  |  "
          f"距節氣：{config.qimen_ju_name_zhirun_raw(y,m,d,h,minute)['距節氣差日數']}天\n")

    # 九宮格 ASCII 藝術（共用）
    lines = [
        f"＼ {es['巳']}{egod['巳']} 　 │ {es['午']}{egod['午']}　 │ {es['未']}{egod['未']}　 │ 　 {es['申']}{egod['申']}　 ／",
        " ＼────────┴──┬─────┴─────┬──┴────────／",
        f" 　│　　{god[0]}　　　 │　　{god[1]}　　　 │　　{god[2]}　　　 │",
        f" 　│　　{door[0]}　　{qt[0]} │　　{door[1]}　　{qt[1]} │　　{door[2]}　　{qt[2]} │",
        f" 　│　　{star[0]}　　{qd[0]} │　　{star[1]}　　{qd[1]} │　　{star[2]}　　{qd[2]} │",
        f" {es['辰']}├───────────┼───────────┼───────────┤{es['酉']}",
        f" {egod['辰']}│　　{god[3]}　　　 │　　　　　　 │　　{god[4]}　　　 │{egod['酉']}",
        f"　─┤　　{door[3]}　　{qt[3]} │　　　　　　 │　　{door[4]}　　{qt[4]} ├─",
        f" 　│　　{star[3]}　　{qd[3]} │　　　　　{mid} │　　{star[4]}　　{qd[4]} │",
        " 　├───────────┼───────────┼───────────┤",
        f"　 │　　{god[5]}　　　 │　　{god[6]}　　　 │　　{god[7]}　　　 │",
        f" {es['卯']}│　　{door[5]}　　{qt[5]} │　　{door[6]}　　{qt[6]} │　　{door[7]}　　{qt[7]} │{es['戌']}",
        f" {egod['卯']}│　　{star[5]}　　{qd[5]} │　　{star[6]}　　{qd[6]} │　　{star[7]}　　{qd[7]} │{egod['戌']}",
        " ／────────┬──┴─────┬─────┴──┬────────＼",
        f"／ {es['寅']}{egod['寅']} 　 │ {es['丑']}{egod['丑']}　 │ {es['子']}{egod['子']}　 │ 　 {es['亥']}{egod['亥']}　 ＼",
    ]
    for line in lines:
        print(line)

    st.expander("原始資料").write(q)

# 顯示原始 dict

# ------------------- 主畫面 -------------------
with pan:
    st.header('堅奇門排盤')

    output = st.empty()
    with st_capture(output.code):
        # 即時盤（預設）
        if instant or (not manual and not instant):  # 頁面初載也顯示即時
            now = datetime.datetime.now(pytz.timezone('Asia/Hong_Kong'))
            render_pan(now.year, now.month, now.day, now.hour, now.minute, is_shijia=True)

        # 手動盤
        if manual and pp_time:
            try:
                h, mnt = map(int, pp_time.split(':'))
                render_pan(pp_date.year, pp_date.month, pp_date.day, h, mnt, is_shijia)
            except:
                st.error("時間格式錯誤，請輸入如 18:30")

