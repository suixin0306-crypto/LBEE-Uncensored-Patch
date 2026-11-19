@echo off
chcp 936 >nul
cd /d "%~dp0"
if exist "LBEE_中文H内容补丁_v1.2.7z" (
  echo 已经合并过了：LBEE_中文H内容补丁_v1.2.7z
  pause
  exit /b 0
)
echo 正在合并 4 个分卷...
copy /b "LBEE_中文H内容补丁_v1.2.7z.001"+"LBEE_中文H内容补丁_v1.2.7z.002"+"LBEE_中文H内容补丁_v1.2.7z.003"+"LBEE_中文H内容补丁_v1.2.7z.004" "LBEE_中文H内容补丁_v1.2.7z"
if errorlevel 1 (
  echo 合并失败：请确认 4 个分卷都在当前文件夹
  pause
  exit /b 1
)
echo.
echo 合并完成！SHA256 应为：
echo 299A5E96C15DD97C2C9DAFA7FFECC5AED3B4A860E71F549B66552F5A59010C7B
echo.
echo 下一步：用 7-Zip/WinRAR 解压 .7z，双击解压出来的 安装.exe
pause
