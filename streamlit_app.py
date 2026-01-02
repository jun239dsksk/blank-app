import streamlit as st
import pandas as pd
from datetime import datetime

# 设置网页标题
st.set_page_config(page_title="报数助手", layout="centered")

def process_data(df):
    # 自动对齐你图片里的列名
    df.columns = [str(c).strip() for c in df.columns]
    
    # 映射表
    col_map = {
        '过磅类型': '过磅类型', # N列
        '收货单位': '收货单位', # K列
        '货物名称': '货物名称', # E列
        '型号规格': '型号规格', # L列
        '净重': '净重',         # H列
        '金额': '金额'          # J列
    }

    # 转换分类
    def get_cat(x):
        val = str(x).strip()
        if '零售（现金）' in val: return '现金'
        if '零售（微信）' in val: return '微信'
        if '签单' in val: return '签单'
        return '其他'

    df['分类'] = df['过磅类型'].apply(get_cat)
    df['车数'] = 1
    df = df.fillna('')
    df['净重'] = pd.to_numeric(df['净重'], errors='coerce').fillna(0)
    df['金额'] = pd.to_numeric(df['金额'], errors='coerce').fillna(0)

    # 汇总
    valid_df = df[df['分类'] != '其他']
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    res = [f"{now}", f"今日车数 {len(valid_df)} 今日吨数 {valid_df['净重'].sum():.2f} 金额 {valid_df['金额'].sum():.2f}", "-"*25]

    for cat in ['现金', '微信', '签单']:
        sub = df[df['分类'] == cat]
        if sub.empty: continue
        
        if cat == '签单':
            res.append(f"\n{cat}: 车数 {len(sub)} 吨数 {sub['净重'].sum():.2f}")
        else:
            res.append(f"\n{cat}: 车数 {len(sub)} 吨数 {sub['净重'].sum():.2f} 金额 {sub['金额'].sum():.2f}")
        
        for _, row in sub.iterrows():
            if str(row['收货单位']).strip():
                res.append(f"{row['收货单位']}")
            res.append(f"{row['货物名称']} {row['型号规格']} 1 {row['净重']:.2f} {row['金额']:.2f}")

    return "\n".join(res)

st.title("🚛 报数汇总助手")
st.write("上传你的 Excel 表格，自动生成汇总文本")

uploaded_file = st.file_uploader("选择文件", type=["xlsx", "xls"])

if uploaded_file:
    try:
        df = pd.read_excel(uploaded_file)
        if '过磅类型' not in df.columns:
            st.error("表格格式不正确，没找到【过磅类型】列")
        else:
            result = process_data(df)
            st.success("汇总成功！")
            st.text_area("复制结果：", value=result, height=400)
    except Exception as e:
        st.error(f"出错啦: {e}")