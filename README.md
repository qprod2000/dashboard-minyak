# Dashboard Alokasi Volume Minyak — Geragai / PHEJM / FSO

## Isi dashboard
- **Volume & Produksi** — tren Net Volume harian tiap sumber, kontribusi per sumber, Shipping 1 vs 2.
- **Kualitas (API/Suhu)** — tren API gravity & temperature, distribusi API.
- **Losses & Shrinkage** — Emulsi, Evaporasi, Shrinkage Lv1/Lv2, % loss terhadap gross volume.
- **Alokasi & Diskrepansi** — Alokasi Factor harian (target ≈1.0000), Diskrepansi (%), flag hari outlier.
- **FSO & Ringkasan** — volume diterima FSO harian & rekap bulanan.
- **Data Mentah** — tabel lengkap tiap sheet, siap difilter berdasarkan tanggal (sidebar).

---

## Opsi A — Deploy ke homelab pakai Docker (rekomendasi)

Urutan langkahnya:

1. **Copy folder ini ke homelab kamu** (scp, rsync, git clone, atau drag lewat Samba/NFS share):
   ```
   scp -r dashboard_streamlit/ user@homelab-ip:/opt/dashboard-minyak
   ```

2. **SSH ke homelab, masuk folder-nya:**
   ```
   ssh user@homelab-ip
   cd /opt/dashboard-minyak
   ```

3. **Build & jalankan container:**
   ```
   docker compose up -d --build
   ```
   (kalau versi docker lama, pakai `docker-compose up -d --build`)

4. **Cek jalan atau tidak:**
   ```
   docker compose ps
   docker compose logs -f
   ```

5. **Akses dashboard-nya:**
   ```
   http://<ip-homelab>:8501
   ```

6. **(Opsional) Taruh di belakang reverse proxy** kalau kamu pakai Nginx Proxy Manager / Traefik / Caddy,
   supaya bisa diakses via domain sendiri (mis. `dashboard.homelab.local`) dan/atau HTTPS. Cukup arahkan
   proxy ke `container:8501` seperti service lain di homelab kamu.

7. **Update data ke depannya:** ganti file CSV di folder `data/` di homelab (via scp/rsync), lalu:
   ```
   docker compose restart
   ```
   Tidak perlu rebuild image karena folder `data/` di-mount sebagai volume.

### Perintah harian yang berguna
```
docker compose stop            # matikan sementara
docker compose start           # nyalakan lagi
docker compose down            # hapus container (data tetap aman, cuma di-mount)
docker compose up -d --build   # rebuild kalau app.py berubah
```

---

## Opsi B — Tanpa Docker (jalankan langsung dengan Python)

1. Pastikan Python 3.9+ terinstal di server homelab.
2. ```
   pip install -r requirements.txt
   streamlit run app.py --server.port=8501 --server.address=0.0.0.0
   ```
3. Supaya tetap jalan setelah SSH ditutup dan otomatis start ulang saat reboot, jalankan sebagai
   `systemd` service. Contoh unit (`/etc/systemd/system/dashboard-minyak.service`):
   ```ini
   [Unit]
   Description=Dashboard Alokasi Volume Minyak
   After=network.target

   [Service]
   WorkingDirectory=/opt/dashboard-minyak
   ExecStart=/usr/bin/streamlit run app.py --server.port=8501 --server.address=0.0.0.0
   Restart=always
   User=youruser

   [Install]
   WantedBy=multi-user.target
   ```
   Lalu:
   ```
   sudo systemctl enable --now dashboard-minyak
   ```

---

## Update data
Ganti file-file di folder `data/` (format sama: kolom `Tanggal` + kolom numerik),
lalu restart service (`docker compose restart` atau `systemctl restart dashboard-minyak`).
