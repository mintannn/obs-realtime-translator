@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo    Real-time Translation Tool Setup
echo ========================================
echo.

echo Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python OK!
echo.
echo Checking required libraries...

echo Current OpenAI version:
python -c "import openai; print('OpenAI version:', openai.__version__)" 2>nul
if errorlevel 1 echo OpenAI not installed

REM Check if OpenAI version is compatible
python -c "import openai; assert openai.__version__.startswith('0.28')" >nul 2>&1
if errorlevel 1 (
    echo Libraries not found or incompatible version. Installing...
    echo This may take a few minutes...
    
    REM Force uninstall and reinstall OpenAI with specific version
    echo Uninstalling existing OpenAI...
    pip uninstall openai -y >nul 2>&1
    python -m pip uninstall openai -y >nul 2>&1
    
    REM Try different pip methods
    echo Installing OpenAI v0.28.1 and PyAudio...
    pip install "openai==0.28.1" pyaudio >nul 2>&1
    if errorlevel 1 (
        echo Method 1 failed. Trying method 2: python -m pip...
        python -m pip install "openai==0.28.1" pyaudio >nul 2>&1
        if errorlevel 1 (
            echo Method 2 failed. Trying method 3: ensurepip + install...
            python -m ensurepip --upgrade >nul 2>&1
            python -m pip install "openai==0.28.1" pyaudio >nul 2>&1
            if errorlevel 1 (
                echo.
                echo ERROR: All installation methods failed.
                echo Please try one of these solutions:
                echo 1. Run this bat file as administrator
                echo 2. Install Python from Microsoft Store
                echo 3. Reinstall Python from python.org with "Add to PATH" checked
                pause
                exit /b 1
            )
        )
    )
    echo Libraries installed successfully!
) else (
    echo Libraries already installed!
)

echo.
echo Starting translation tool...

copy translate.py rt_temp.py 2>nul
if exist rt_temp.py (
    python rt_temp.py
    del rt_temp.py 2>nul
) else (
    echo ERROR: translate.py not found!
    echo Please place translate.py in the same folder as this bat file.
    pause
)

pause