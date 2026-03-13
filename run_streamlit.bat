@echo off
echo Starting Audit AI - Streamlit App...
cd /d "%~dp0"

REM Dung venv cua backend (da co day du thu vien)
call backend\venv\Scripts\activate

REM Cai streamlit va plotly neu chua co
pip install streamlit plotly -q

echo.
echo ========================================
echo  Audit AI dang khoi dong tai port 8501
echo  Mo trinh duyet: http://localhost:8501
echo ========================================
echo.
streamlit run streamlit_app.py --server.port 8501
pause
