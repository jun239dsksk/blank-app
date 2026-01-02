import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="报数助手", layout="centered")

def process_data(df, time_range):
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

    valid_df = df[df['分类'].isin(['现金', '微信', '签单'])]
    
    res = []
    res.append(f"{time_range}")
    res.append(f"{len(valid_df)}车{valid_df['净重'].sum():.2f}吨{int(valid_df['金额'].sum())}元")
    res.append("")

    for cat in ['现金', '微信', '签单']:
        sub = df[df['分类'] == cat]
        if sub.empty:
            res.append(f"{cat}:无\n")
            continue
        
        # 板块标题
        c_cars, c_tons, c_money = len(sub), sub['净重'].sum(), int(sub['金额'].sum())
        title = f"{cat}:{c_cars}车{c_tons:.2f}吨" + (f"{c_money}元" if cat != '签单' else "")
        res.append(title)

        # 按收货单位分组统计
        unit_groups = sub.groupby('收货单位', sort=False)
        for unit_name, unit_df in unit_groups:
            u_cars, u_tons = len(unit_df), unit_df['净重'].sum()
            res.append(f"{unit_name}:{u_cars}车{u_tons:.2f}吨")
            
            # 统计具体货物
            cargo_groups = unit_df.groupby(['货物名称', '型号规格'], sort=False)
            for (cargo, spec), c_df in cargo_groups:
                spec_str = f"({spec})" if spec else ""
                cg_money = f"{int(c_df['金额'].sum())}元" if cat != '签单' else ""
                res.append(f"{cargo}{spec_str}:{len(c_df)}车{c_df['净重'].sum():.2f}吨{cg_money}")
            
            # --- 关键修改：收货方之间增加空行 ---
            res.append("") 

    res.append("。")
    return "\n".join(res)

st.title("🚛 报数汇总助手")
time_input = st.text_input("1. 输入时间段：", value="26年1月1日07:00-18:00")
uploaded_file = st.file_uploader("2. 上传 Excel (.xls/xlsx)", type=["xlsx", "xls"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        result_text = process_data(df, time_input)
        
        st.success("汇总成功！点击下方黑框右上角图标即可复制：")
        
        # 使用 st.code 会自动在右上角显示复制按钮
        st.code(result_text, language="markdown")
        
    except Exception as e:
        st.error(f"处理出错: {e}")
