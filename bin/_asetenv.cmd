@echo off

if /I [%1] equ [] goto L_Without_Arg
:L_With_Arg
set KYT_CONFIG_FILEPATH=%1
goto L_Go
:L_Without_Arg
SET KYT_CONFIG_FILEPATH=%~dp0%KYT_CONFIG_FILENAME%
goto L_Go



@echo.Setting KyT environment:
@echo.  Configuration file: [%KYT_CONFIG_FILEPATH%]
@echo.

set O_LOOP=False

