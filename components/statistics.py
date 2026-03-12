import streamlit as st

def render_stats_cards(stats_list):
    """
    stats_list: List of dicts with keys 'label', 'value', 'icon', 'color'
    """
    cols = st.columns(len(stats_list))
    for i, stat in enumerate(stats_list):
        with cols[i]:
            st.markdown(f"""
                <div style="
                    background-color: white;
                    padding: 15px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    border-left: 5px solid {stat.get('color', '#000080')};
                    margin-bottom: 20px;
                    text-align: center;
                ">
                    <div style="font-size: 24px; margin-bottom: 5px;">{stat.get('icon', '📊')}</div>
                    <div style="font-size: 14px; color: #666; font-weight: 600;">{stat.get('label', '')}</div>
                    <div style="font-size: 20px; color: {stat.get('color', '#000080')}; font-weight: 800;">{stat.get('value', '')}</div>
                </div>
            """, unsafe_allow_html=True)
