import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="报数汇总助手", layout="centered")

def process_data(df, time_range):
    df.columns = [str(c).strip() for c in df.columns]
    
    # 转换逻辑
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
    df['车数'] = 1

    # 只统计目标类型
    valid_df = df[df['分类'].isin(['现金', '微信', '签单'])]
    
    # --- 拼装输出文本 ---
    res = []
    res.append(f"{time_range}")
    res.append(f"{len(valid_df)}车{valid_df['净重'].sum():.2f}吨{int(valid_df['金额'].sum())}元")
    res.append("")

    for cat in ['现金', '微信', '签单']:
        sub = df[df['分类'] == cat]
        if sub.empty:
            res.append(f"{cat}:无\n")
            continue
        
        # 版块小计
        cat_cars = len(sub)
        cat_tons = sub['净重'].sum()
        cat_money = int(sub['金额'].sum())
        
        if cat == '签单':
            res.append(f"{cat}:{cat_cars}车{cat_tons:.2f}吨")
        else:
            res.append(f"{cat}:{cat_cars}车{cat_tons:.2f}吨{cat_money}元")

        # --- 按“收货单位”汇总 ---
        unit_groups = sub.groupby('收货单位')
        for unit_name, unit_df in unit_groups:
            if unit_name: # 如果收货单位不为空
                res.append(f"{unit_name}:{len(unit_df)}车{unit_df['净重'].sum():.2f}吨")
            
            # --- 按“货物+规格”汇总 ---
            cargo_groups = unit_df.groupby(['货物名称', '型号规格'])
            for (cargo, spec), c_df in cargo_groups:
                spec_str = f"({spec})" if spec else ""
                c_money_str = f"{int(c_df['金额'].sum())}元" if cat != '签单' else ""
                res.append(f"{cargo}{spec_str}:{len(c_df)}车{c_df['净重'].sum():.2f}吨{c_money_str}")
        res.append("") # 版块间空行

    res.append("。")
    return "\n".join(res)

# --- 界面 ---
st.title("🚛 报数汇总助手")

# 侧边栏或顶部设置时间
time_input = st.text_input("请输入报数时间段：", value="26年1月1日07:00-18:00")

uploaded_file = st.file_uploader("选择 Excel 文件 (.xls 或 .xlsx)", type=["xlsx", "xls"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        if '过磅类型' not in df.columns:
            st.error("表格格式不正确，没找到【过磅类型】列")
        else:
            result_text = process_data(df, time_input)
            st.success("汇总成功！")
            # Streamlit 的 text_area 右上角自带一键复制按钮
            st.text_area("直接点击右上角图标复制：", value=result_text, height=450)
    except Exception as e:
        st.error(f"处理出错: {e}")