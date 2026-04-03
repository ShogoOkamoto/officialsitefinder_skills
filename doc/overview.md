# officialsitefinder_skills — プログラム概要

## 1. 目的

施設名と住所を入力として、その施設の **公式サイトのトップページURL** を自動発見するシステム。

住所照合によって「本当にその施設のサイトか」を検証することで、ポータルサイトや予約サイトを除外し、精度を高めている。

---

## 2. コンポーネント構成

```
officialsitefinder_skills/
│
├── officialsite_finder_tool/   ← メイン統合ツール（本ドキュメントの主題）
├── google_search_tool/         ← Google Custom Search API ラッパー
├── extract_full_address_tool/  ← 日本語テキストから住所を抽出
├── extract_address_tool/       ← 市区町村レベル住所抽出（検索クエリ生成用）
├── compare_address_tool/       ← 住所の正規化・比較
├── playwright_download_tool/   ← JavaScriptレンダリング済みHTML取得
│
└── .claude/skills/
    └── officialsite_finder_skill/  ← Claude Code スキル（対話ループ制御）
```

各ツールは独立したCLIサブプロセスとして呼び出される。`officialsite_finder_tool` がオーケストレーターとして他ツールを順番に呼び出す。

---

## 3. 全体処理フロー

```
ユーザー入力
  施設名: "札幌医科大学附属病院"
  住所:   "北海道札幌市中央区南１条西１６丁目２９１番地"
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│                 officialsite_finder_tool                  │
│                                                           │
│  手順1  入力検証                                          │
│          └─ 施設名・住所が空でないかチェック              │
│                                                           │
│  手順2  住所の2段階抽出                                   │
│          ├─ 2-A: extract_full_address_tool                │
│          │        → "北海道札幌市中央区南1条西16丁目291番地"│
│          │          （手順6の住所照合に使用）              │
│          └─ 2-B: extract_address_tool                     │
│                   → "北海道札幌市中央区"                  │
│                     （手順3の検索クエリに使用）            │
│                                                           │
│  手順3  Google検索                                        │
│          └─ クエリ: "札幌医科大学附属病院 北海道札幌市中央区"│
│             → 最大5件のURLを取得                          │
│                                                           │
│  ┌── 各URLに対してループ（手順4〜9）──────────────────┐  │
│  │                                                     │  │
│  │  手順4  HTMLダウンロード                            │  │
│  │          └─ playwright_download_tool でJS描画後テキスト│
│  │                                                     │  │
│  │  手順5  ページ内住所の抽出                          │  │
│  │          └─ extract_full_address_tool               │  │
│  │                                                     │  │
│  │  手順6  住所照合                                    │  │
│  │          └─ compare_address_full (前方一致・表記ゆれ対応)│
│  │             一致しなければ次のURLへ                 │  │
│  │                                                     │  │
│  │  手順7  収集対象判定 ─── criteria.txt がある場合    │  │
│  │          └─ サブエージェントに判定依頼              │  │
│  │             → "eligible" / "not_eligible"           │  │
│  │             not_eligible → 次のURLへ                │  │
│  │                                                     │  │
│  │  手順8  トップページ判定                            │  │
│  │          ├─ URL構造チェック（ドメイン直下ならOK）   │  │
│  │          └─ サブエージェントに判定依頼              │  │
│  │             → "Yes" / "No"                         │  │
│  │             No → 手順9へ                           │  │
│  │                                                     │  │
│  │  手順9  ドメインルートに遷移して再判定              │  │
│  │                                                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                           │
│  手順10 失敗終了: {"success": false, ...}                 │
│  手順11 成功終了: {"success": true,                       │
│                    "official_site_url": "https://...",   │
│                    "matched_address": "..."}              │
└─────────────────────────────────────────────────────────┘
```

---

## 4. ステートフルな判定ループ

`officialsite_finder_tool` は **1回の実行で完結しない**。サブエージェント（人間またはLLM）に判定を委ねる必要がある場合、途中結果をJSONで出力して終了し、呼び出し元が判定結果を付けて再実行する設計になっている。

### 出力パターン

| `action` フィールド | 意味 | 次のアクション |
|---|---|---|
| `request_criteria_judgment` | 収集対象かの判定を依頼 | `--criteria-judgment eligible/not_eligible` で再実行 |
| `request_judgment` | トップページかの判定を依頼 | `--judgment Yes/No` で再実行 |
| （なし）`success: true` | 公式サイト発見 | 終了 |
| （なし）`success: false` | 発見失敗 | 終了 |

### 再実行の仕組み

```
Run 1: python -m officialsite_finder_tool --name "A" --address "B"
       → {"action": "request_criteria_judgment", "url": "https://x.com/", ...}

           ↓ サブエージェントが判定: "eligible"

Run 2: python -m officialsite_finder_tool --name "A" --address "B"
            --criteria-judgment "eligible"
            --criteria-pending-url "https://x.com/"
            --matched-address "..."
       → {"action": "request_judgment", "url": "https://x.com/", ...}

           ↓ URL構造チェック or サブエージェントが判定: "Yes"

Run 3: python -m officialsite_finder_tool --name "A" --address "B"
            --judgment "Yes"
            --pending-url "https://x.com/"
            --matched-address "..."
       → {"success": true, "official_site_url": "https://x.com/", ...}
```

`not_eligible` の場合は `--search-results` と `--skip-urls` を渡すことで、Google検索を再実行せずに次のURLの処理を継続できる。

---

## 5. Claude Code スキルの役割

`officialsite_finder_skill`（`.claude/skills/officialsite_finder_skill/SKILL.md`）はこのループ制御ロジックを Claude Code に指示する。

```
ユーザー「東京タワーの公式サイトを探して」
    │
    ▼
officialsite_finder_skill が起動
    │
    ├─ python -m officialsite_finder_tool を実行
    │
    ├─ action フィールドを確認
    │   ├─ request_criteria_judgment → Task サブエージェントで判定
    │   │    └─ 結果を --criteria-judgment で渡して再実行
    │   ├─ request_judgment → Task サブエージェントで判定
    │   │    └─ 結果を --judgment で渡して再実行
    │   └─ success → ユーザーに結果報告
    │
    └─ success が現れるまでループ
```

---

## 6. テスト構成

### 6.1 バッチ統合テスト（`tests/test_officialsite_finder_batch.py`）

`tests/resource/sample_from_scuel_10.tsv` の10施設を1件ずつ実行し、発見されたURLが期待値と一致するかを検証する。

```
TSV列: 施設名 | 都道府県 | 住所 | HP_改行削除（期待URL）
         ↓
  address = 都道府県 + 住所
         ↓
  run_loop(name, address)
         ↓
  output["official_site_url"] == expected_url ?
```

判定ループは自動化されており：
- `request_criteria_judgment` → 常に `"eligible"` で応答
- `request_judgment` → URLが `/` 直下なら `"Yes"`、それ以外は `"No"`

Google検索は施設1件につき1回（合計10回）。

### 6.2 URL比較の正規化

```python
def _normalize_url(url):
    # 末尾スラッシュを除去
    # http:// → https:// に統一（スキームの違いを無視）
    normalized = url.strip().rstrip("/")
    if normalized.startswith("http://"):
        normalized = "https://" + normalized[len("http://"):]
    return normalized
```

### 6.3 実行コマンド

```bash
# プロジェクトルートから実行
pytest tests/test_officialsite_finder_batch.py -m integration -v
```

VS Code でのデバッグ実行は `.vscode/launch.json` の `"pytest: batch integration test"` 構成を使用する。

---

## 7. 環境変数

| 変数名 | 説明 |
|---|---|
| `GOOGLE_API_KEY` | Google Cloud の API キー（Custom Search API を有効化） |
| `GOOGLE_CSE_ID` | Programmable Search Engine の ID |

`.env` ファイルをプロジェクトルートに配置して設定する。

---

## 8. 住所比較の仕組み

`compare_address_full_skill`（`.claude/skills/compare_address_full_skill/compare_address_full.py`）が住所比較を担当する。

正規化の手順：

1. NFKC正規化（全角→半角）
2. マイナス記号統一（U+2212 → `-`）
3. 空白除去
4. 漢数字→アラビア数字（一→1、十一→11）
5. 番地表記統一（1丁目2番3号 → 1-2-3）
6. 小文字化

マッチング戦略：

| パターン | 判定 | 用途 |
|---|---|---|
| 正規化後が完全一致 | 一致 | 標準ケース |
| 一方が他方のプレフィックス | 一致 | ページに市区町村レベルしか載っていない場合 |
| どちらでもない | 不一致 | — |
