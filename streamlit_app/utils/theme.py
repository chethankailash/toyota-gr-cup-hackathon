import streamlit as st

def apply_toyota_theme():
    """Injects global Toyota styling into the Streamlit app."""

    st.markdown(
        """
        <style>
            /* Light Mode Override */
            :root {
                --primary-color: #EB0A1E; /* Toyota Red */
                --text-color: #000000;
                --background-color: #FFFFFF;
                --secondary-background-color: #F5F5F5;
            }

            /* Global background */
            .main {
                background-color: #FFFFFF !important;
            }

            /* Sidebar styling */
            section[data-testid="stSidebar"] {
                background-color: #000000 !important;  /* black */
            }

            /* Sidebar text to white */
            section[data-testid="stSidebar"] * {
                color: #FFFFFF !important;
            }

            /* Header */
            header[data-testid="stHeader"] {
                background-color: #FFFFFF !important;
            }
            header[data-testid="stHeader"] * {
                color: #000000 !important;
            }

            /* Remove weird borders */
            div[data-testid="stSidebarNav"] {
                border-right: none !important;
            }

            /* Buttons in Toyota red */
            .stButton>button {
                background-color: #EB0A1E !important;
                color: white !important;
                border-radius: 6px;
                border: none;
                font-weight: bold;
            }

            /* Selectbox label color fix */
            .stSelectbox label, .stMultiSelect label {
                color: #000000 !important;
            }

            /* DataFrames border styling */
            .stDataFrame {
                border: 2px solid #58595B !important;  /* Toyota Gray */
                border-radius: 6px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
