@echo off
echo Mengupload perubahan ke GitHub...

:: Menambahkan semua file yang berubah
git add .

:: Membuat commit dengan pesan otomatis menggunakan tanggal & waktu saat ini
git commit -m "Auto-upload: %date% %time%"

:: Melakukan push ke GitHub (pastikan branch utama bernama 'main' atau ganti sesuai kebutuhan)
git push origin main

echo.
echo Selesai! Kode berhasil diupload.
pause
