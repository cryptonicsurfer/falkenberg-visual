import streamlit as st

st.header('En sida med visualiseringar av data för olika områden')


st.image('chart3.png')


col1, col2 = st.columns([0.4, 0.6])



with col1:
    st.subheader(':rainbow[Falkenberg], *presenterat visuellt*')
    st.image('fbg2.jpg')
    st.image('fbg1.jpg')

with col2:
    st.image('chart1.png')

