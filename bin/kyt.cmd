@REM
@REM kyt.cmd Copyright (C) 2020 You-Cast on Earth, Moon and Mars 2020
@REM This file is part of com.castsoftware.uc.kyt extension
@REM which is released under GNU GENERAL PUBLIC LICENS v3, Version 3, 29 June 2007.
@REM See file LICENCE or go to https://www.gnu.org/licenses/ for full license details.
@REM
@echo OFF

TITLE %~n0
%~d0
pushd %~p0
cd ..\kyt

CALL "%~dp0_asetenv.cmd" %1 %2 %3 %4 %5 %6 %7 %8 %9

set V_CONFIG_JSON=%KYT_CONFIG_FILEPATH%

set V_SCRIPT_PY=runner.py
set V_OPTIONS=extract process render

set V_CMD=python "%V_SCRIPT_PY%" %V_OPTIONS% "%V_CONFIG_JSON%"

:L_Loop
echo.^>^>^>^>^>^> %V_CMD%
%V_CMD%

if /I [%O_LOOP%] neq [true] goto L_End
set V_A=
set /P V_A=Continue ? 
if /I [%V_A%] equ [x] cls
if /I [%V_A%] neq [n] goto L_Loop

:L_End
popd
if /I [%1] neq [-NoPause] pause
