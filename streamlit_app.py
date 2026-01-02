import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="报数助手", layout="centered")

def process_data(df, time_range_str):
    df.columns = [str(c).strip() for c in df.columns]
    
    def get_cat(x):
        val = str(x).strip()
        if '零售（现金）' in val: return '现金'
        if '零售（微信）' in val: return '微信'
        if '签单' in val: return '签单'
        return '其他'

    df['分类'] = df['过磅类型'].apply(get_cat)
    df = df.fillna('')
    df['净重'] = pd.to_numeric(df['净重'], errors='coerce').fillna(0)
    df['金额'] = pd.to_numeric(df['金额'], errors='coerce').fillna(0)

    money_df = df[df['分类'].isin(['现金', '微信'])]
    all_valid_df = df[df['分类'].isin(['现金', '微信', '签单'])]
    
    res = []
    res.append(f"{time_range_str}")
    total_money = int(money_df['金额'].sum())
    res.append(f"{len(all_valid_df)}车{all_valid_df['净重'].sum():.2f}吨{total_money}元")
    res.append("")

    for cat in ['现金', '微信', '签单']:
        sub = df[df['分类'] == cat]
        if sub.empty:
            res.append(f"{cat}:无\n")
            continue
        
        c_cars, c_tons = len(sub), sub['净重'].sum()
        if cat == '签单':
            res.append(f"{cat}:{c_cars}车{c_tons:.2f}吨")
        else:
            c_money = int(sub['金额'].sum())
            res.append(f"{cat}:{c_cars}车{c_tons:.2f}吨{c_money}元")

        unit_groups = sub.groupby('收货单位', sort=False)
        for unit_name, unit_df in unit_groups:
            if cat == '签单':
                res.append(f"{unit_name}:{len(unit_df)}车{unit_df['净重'].sum():.2f}吨")
            elif str(unit_name).strip():
                res.append(f"{unit_name}:") 

            cargo_groups = unit_df.groupby(['货物名称', '型号规格'], sort=False)
            for (cargo, spec), c_df in cargo_groups:
                spec_str = f"({spec})" if spec else ""
                if cat == '签单':
                    res.append(f"{cargo}{spec_str}:{len(c_df)}车{c_df['净重'].sum():.2f}吨")
                else:
                    cg_money = f"{int(c_df['金额'].sum())}元"
                    res.append(f"{cargo}{spec_str}:{len(c_df)}车{c_df['净重'].sum():.2f}吨{cg_money}")
            res.append("") 

    res.append("。")
    return "\n".join(res)

st.title("🚛 报数汇总助手")

# --- 修改后的时间选择区域 ---
st.subheader("1. 选择报数时间段")
col1, col2 = st.columns(2)
with col1:
    d = st.date_input("选择日期", datetime.now())
with col2:
    t_start, t_end = st.select_slider(
        '时间范围',
        options=[f"{i:02d}:00" for i in range(24)] + ["23:59"],
        value=("07:00", "18:00")
    )

# 自动转换格式：26年1月2日07:00-18:00
time_range_str = f"{d.strftime('%y')}年{d.month}月{d.day}日{t_start}-{t_end}"
st.info(f"当前选择：{time_range_str}")

# --- 文件上传 ---
uploaded_file = st.file_uploader("2. 上传 Excel (.xls/xlsx)", type=["xlsx", "xls"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        result_text = process_data(df, time_range_str)
        st.success("汇总成功！")
        st.code(result_text, language="markdown")
    except Exception as e:
        st.error(f"处理出错: {e}")
