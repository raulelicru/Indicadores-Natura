"""Entry-point alterno para Streamlit Community Cloud.

Streamlit Cloud usa por defecto `streamlit_app.py`. La app real vive en
`dashboard.py`; este archivo solo delega en su router principal.
"""
from dashboard import main

if __name__ == "__main__":
    main()
