@REM
@REM kyt_render-enlighten2.cmd Copyright (C) 2020 You-Cast on Earth, Moon and Mars 2020
@REM This file is part of com.castsoftware.uc.kyt extension
@REM which is released under GNU GENERAL PUBLIC LICENS v3, Version 3, 29 June 2007.
@REM See file LICENCE or go to https://www.gnu.org/licenses/ for full license details.
@REM
@ECHO OFF

TITLE %~n0
%~d0
PUSHD %~p0
CD ..\kyt

CALL "%~dp0_asetenv.cmd"

SET V_SCRIPT_PY=runner.py
SET V_CONFIG_JSON=%KYT_CONFIG_FILEPATH%
SET V_OPTIONS=enlighten2

SET V_CMD=python %V_SCRIPT_PY% %V_OPTIONS% "%V_CONFIG_JSON%"

:L_LOOP
ECHO.^>^>^>^>^>^> %V_CMD%
%V_CMD%

POPD

:L_END
IF /I [%1] NEQ [-NoPause] PAUSE

:L_END_NOPAUSE