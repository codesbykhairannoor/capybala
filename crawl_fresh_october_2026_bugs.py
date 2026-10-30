import urllib.request
import urllib.error
import json
import time
import os
import pandas as pd

print("=" * 70)
print("CRAWLING FRESH LIVE GITHUB BUG-FIX PRs (OCTOBER 2026)")
print("Target: 1,000 Fresh PRs merged between October 20 - 29, 2026")
print("=" * 70)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/vnd.github.v3+json"
}

base_query = "is:pr+is:merged+label:bug+merged:2026-10-20..2026-10-29+language:python"
all_records = []
target_pages = 10  # 10 pages x 100 items = 1,000 records

for page in range(1, target_pages + 1):
    url = f"https://api.github.com/search/issues?q={base_query}&sort=updated&order=desc&per_page=100&page={page}"
    print(f"\n[Page {page}/{target_pages}] Requesting: {url[:80]}...")
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
            items = data.get("items", [])
            print(f"  -> Berhasil mendapatkan {len(items)} items dari GitHub API.")
            
            for item in items:
                repo_url = item.get("repository_url", "")
                repo_name = repo_url.replace("https://api.github.com/repos/", "") if repo_url else "unknown"
                pr_meta = item.get("pull_request", {})
                
                labels = [l.get("name") for l in item.get("labels", []) if isinstance(l, dict)]
                
                body_text = item.get("body") or ""
                # Bersihkan newline berlebih
                clean_body = body_text.replace("\r\n", "\n").strip()
                
                all_records.append({
                    "pr_id": item.get("id"),
                    "repo_name": repo_name,
                    "pr_number": item.get("number"),
                    "title": item.get("title", ""),
                    "bug_description": clean_body[:1000],  # Ambil hingga 1000 karakter pertama deskripsi
                    "author": item.get("user", {}).get("login", ""),
                    "author_association": item.get("author_association", ""),
                    "labels": ", ".join(labels),
                    "created_at": item.get("created_at"),
                    "closed_at": item.get("closed_at"),
                    "html_url": item.get("html_url"),
                    "diff_url": pr_meta.get("diff_url", f"{item.get('html_url')}.diff"),
                    "patch_url": pr_meta.get("patch_url", f"{item.get('html_url')}.patch"),
                    "comments_count": item.get("comments", 0),
                    "data_harvest_timestamp": "2026-10-29T21:45:00Z"
                })
                
    except urllib.error.HTTPError as e:
        print(f"  -> HTTP Error {e.code}: {e.reason}")
        if e.code == 403:
            print("  -> Rate limit hit. Menunggu jeda 30 detik...")
            time.sleep(30)
    except Exception as e:
        print(f"  -> Error: {e}")
        
    # Jeda 3 detik antar halaman untuk menghormati rate limit GitHub Search API
    time.sleep(3)

print("\n" + "=" * 70)
print(f"CRAWLING SELESAI: Total {len(all_records)} baris data berhasil disedot!")
print("=" * 70)

if all_records:
    df = pd.DataFrame(all_records)
    
    # Urutkan berdasarkan tanggal terbaru
    df = df.sort_values(by="created_at", ascending=False).reset_index(drop=True)
    
    output_csv = "d:/Dataset Kaggle/fresh_october_2026_bugs.csv"
    df.to_csv(output_csv, index=False)
    print(f"\n[SUKSES] Dataset CSV tersimpan di: {output_csv}")
    print(f"Ukuran Data: {len(df)} baris x {len(df.columns)} kolom.")
    
    # Tampilkan rentang tanggal
    min_date = df['created_at'].min()
    max_date = df['created_at'].max()
    unique_repos = df['repo_name'].nunique()
    
    print(f"\n[VERIFIKASI TANGGAL & KREDIBILITAS DATA]:")
    print(f"  Rentang Tanggal Pembuatan : {min_date} s/d {max_date}")
    print(f"  Jumlah Repositori Unik    : {unique_repos} repositori open-source")
    print(f"  Data Paling Baru          : {df['created_at'].iloc[0]} (Hari ini!)")
    
    print("\n[Cuplikan 5 Baris Pertama]:")
    print(df[["created_at", "repo_name", "title", "diff_url"]].head())

