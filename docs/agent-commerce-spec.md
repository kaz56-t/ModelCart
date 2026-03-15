# Agent Commerce API — 仕様書 v0.1
> LLM/AIエージェント特化型 通販API  
> 更新日: 2026-03-14

---

## 目次

1. [プロジェクト概要](#1-プロジェクト概要)
2. [技術スタック](#2-技術スタック)
3. [インフラ構成](#3-インフラ構成)
4. [システムアーキテクチャ](#4-システムアーキテクチャ)
5. [DBスキーマ](#5-dbスキーマ)
6. [API仕様](#6-api仕様)
7. [ポリシーエンジン](#7-ポリシーエンジン)
8. [管理UI](#8-管理ui)
9. [ディレクトリ構成](#9-ディレクトリ構成)
10. [開発ロードマップ](#10-開発ロードマップ)
11. [Phase 2 以降（参考）](#11-phase-2-以降参考)

---

## 1. プロジェクト概要

### コンセプト

「人間ではなくLLMが顧客」という設計原則の通販API。  
APIキーとポリシー設定だけで、AIエージェントが自律的に商品を検索・注文できる。

### 設計原則

- **Agent-First**: 全エンドポイントはLLMが呼びやすい構造に最適化
- **ポリシー制御**: エージェントの行動範囲はAPIキー単位でコントロール
- **dry-run対応**: 本注文前にシミュレーションして安全確認できる
- **agent_hint**: 全レスポンスにLLMが次アクションを判断するためのヒントを返す

### MVPスコープ

| 機能 | 状態 |
|------|------|
| 商品検索API（シンプルFiltering） | ✅ MVP対象 |
| 商品詳細API | ✅ MVP対象 |
| 注文API（dry-run対応） | ✅ MVP対象 |
| 注文状況確認API | ✅ MVP対象 |
| APIキー認証 + ポリシーエンジン | ✅ MVP対象 |
| 管理UI（商品登録・APIキー・ポリシー設定） | ✅ MVP対象 |
| MCP Server化 | 🔜 Phase 2 |
| 自然言語検索（LLM変換） | 🔜 Phase 2 |
| Webhook通知 | 🔜 Phase 2 |
| マルチテナント（マーケットプレイス化） | 🔜 Phase 3 |

---

## 2. 技術スタック

| レイヤー | 技術 | 備考 |
|---------|------|------|
| API フレームワーク | FastAPI | Python 3.12 |
| DB | PostgreSQL | JSONB活用（ポリシー・注文items） |
| ORM | SQLAlchemy（async） | asyncpg ドライバ |
| マイグレーション | Alembic | |
| バリデーション | Pydantic v2 | |
| 認証 | Bearer Token（APIキー） | SHA256ハッシュで保存 |
| 管理UI | Next.js | 管理・設定のみ、注文操作なし |
| コンテナ | Docker + docker-compose | ローカル開発用 |

---

## 3. インフラ構成

### MVP: Railway

```
GitHub (コード管理)
    │
    └─ push → 自動デプロイ
         │
       Railway
       ├── FastAPI サービス  [Web]
       │   └── uvicorn, PORT=$PORT, 環境変数注入
       └── PostgreSQL        [Database]
           └── DATABASE_URL が自動で環境変数に注入
```

**選定理由:**
- `railway.toml` 1ファイルで設定完結 → Claude Codeが生成・管理しやすい
- GitHubへのpushで自動デプロイ → AI駆動開発ワークフローと親和性が高い
- PostgreSQLがワンクリックで追加可能、接続文字列が自動注入
- 無料枠: $5クレジット/月（MVPトラフィックなら実質無料）

**スケールアップ路線:**

```
MVP        → Railway（$0〜5/月）
成長期     → Railway Pro or Fly.io（$20〜/月）
本格運用   → AWS ECS + RDS（必要になってから移行）
```

### railway.toml

```toml
[build]
builder = "DOCKERFILE"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
```

### 環境変数

```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
SECRET_KEY=your-secret-key-here
API_KEY_PREFIX=sk-agent-
ALLOWED_ORIGINS=https://your-admin-ui.vercel.app
```

---

## 4. システムアーキテクチャ

```
┌─────────────────────────────────────────────────┐
│               LLM / AI Agent                     │
│     (Claude, GPT, カスタムAgent など)             │
└──────────────────┬──────────────────────────────┘
                   │  REST API
                   │  Authorization: Bearer sk-agent-xxxx
                   ▼
┌─────────────────────────────────────────────────┐
│            Agent Commerce API (FastAPI)          │
│                                                 │
│  POST /v1/search          商品検索               │
│  GET  /v1/products/:id    商品詳細               │
│  POST /v1/orders          注文作成               │
│  GET  /v1/orders/:id      注文状況確認           │
│  GET  /health             ヘルスチェック          │
└──────────┬──────────────────────────────────────┘
           │
    ┌──────┴───────┐
    ▼              ▼
┌────────┐   ┌───────────────────────┐
│  PgSQL │   │  管理UI (Next.js)      │
│        │   │  ブラウザからのみ       │
│ 商品   │   │  - 商品登録・編集       │
│ 注文   │   │  - APIキー発行          │
│ APIキー│   │  - ポリシー設定         │
│ ログ   │   │  - 注文監査ログ確認     │
└────────┘   └───────────────────────┘
```

---

## 5. DBスキーマ

```sql
-- 商品
CREATE TABLE products (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          TEXT NOT NULL,
    description   TEXT,
    price         INTEGER NOT NULL,          -- 円（税抜）
    category      TEXT NOT NULL,
    in_stock      BOOLEAN DEFAULT true,
    stock_qty     INTEGER DEFAULT 0,
    delivery_days INTEGER DEFAULT 3,         -- 最短配送日数
    attributes    JSONB DEFAULT '{}',        -- {"color":"black","weight_g":15}
    created_at    TIMESTAMPTZ DEFAULT now(),
    updated_at    TIMESTAMPTZ DEFAULT now()
);

-- APIキー（エージェントの認証情報）
CREATE TABLE api_keys (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash     TEXT UNIQUE NOT NULL,       -- SHA256ハッシュで保存（平文は返却時のみ）
    name         TEXT NOT NULL,              -- "home-agent" など識別名
    owner_email  TEXT NOT NULL,
    policy       JSONB NOT NULL DEFAULT '{}',
    is_active    BOOLEAN DEFAULT true,
    created_at   TIMESTAMPTZ DEFAULT now(),
    last_used_at TIMESTAMPTZ
);

-- ポリシーJSONBスキーマ（api_keys.policy）
-- {
--   "auto_approve_under": 5000,       // 円以下は自動決済
--   "allowed_categories": ["food"],   // 許可カテゴリ（空=全許可）
--   "max_orders_per_day": 3,          // 1日の注文上限
--   "max_items_per_order": 10,        // 1注文あたりの商品種数上限
--   "require_dry_run": false          // 本注文前にdry-run必須か
-- }

-- 配送先プロファイル
CREATE TABLE delivery_profiles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id  UUID REFERENCES api_keys(id),
    label       TEXT NOT NULL,              -- "home", "office"
    name        TEXT NOT NULL,              -- 受取人名
    postal_code TEXT NOT NULL,
    address     TEXT NOT NULL,
    is_default  BOOLEAN DEFAULT false
);

-- 注文
CREATE TABLE orders (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id       UUID REFERENCES api_keys(id),
    status           TEXT NOT NULL DEFAULT 'confirmed',
    -- confirmed / shipped / delivered / cancelled
    items            JSONB NOT NULL,
    -- [{"product_id":"...","qty":2,"price":220,"name":"..."}]
    subtotal         INTEGER NOT NULL,
    delivery_profile JSONB NOT NULL,        -- 注文時点のスナップショット
    estimated_delivery DATE,
    created_at       TIMESTAMPTZ DEFAULT now(),
    updated_at       TIMESTAMPTZ DEFAULT now()
);

-- 注文ログ（エージェントの行動監査用）
CREATE TABLE order_logs (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id UUID REFERENCES api_keys(id),
    action     TEXT NOT NULL,               -- "search" / "dry_run" / "order"
    request    JSONB,
    response   JSONB,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- インデックス
CREATE INDEX idx_products_category      ON products(category);
CREATE INDEX idx_products_price         ON products(price);
CREATE INDEX idx_products_delivery_days ON products(delivery_days);
CREATE INDEX idx_orders_api_key         ON orders(api_key_id);
CREATE INDEX idx_order_logs_api_key     ON order_logs(api_key_id, created_at);
```

---

## 6. API仕様

### 共通仕様

- **ベースURL**: `https://api.your-domain.com`
- **認証**: 全エンドポイントで `Authorization: Bearer sk-agent-xxxxxxxx` が必須
- **Content-Type**: `application/json`
- **レスポンス共通フィールド**: `agent_hint`（LLMが次アクションを判断するためのヒント文字列）

---

### `GET /health` — ヘルスチェック

Railway用。認証不要。

```json
// Response 200
{ "status": "ok" }
```

---

### `POST /v1/search` — 商品検索

**Request**

```json
{
  "filters": {
    "category": "office",       // optional: カテゴリ絞り込み
    "max_price": 500,           // optional: 最大価格（円）
    "max_delivery_days": 1,     // optional: 最大配送日数
    "in_stock_only": true       // optional: default true
  },
  "limit": 10,                  // default: 10, max: 50
  "offset": 0
}
```

**Response 200**

```json
{
  "products": [
    {
      "id": "prod_uuid",
      "name": "ジェットストリーム 0.7mm",
      "price": 220,
      "category": "office",
      "in_stock": true,
      "stock_qty": 150,
      "delivery_days": 1,
      "attributes": {"color": "black", "type": "ballpoint"}
    }
  ],
  "total": 3,
  "agent_hint": "3件見つかりました。翌日配送・在庫あり。"
}
```

---

### `GET /v1/products/{product_id}` — 商品詳細

**Response 200**

```json
{
  "id": "prod_uuid",
  "name": "ジェットストリーム 0.7mm",
  "description": "なめらかな書き心地のボールペン",
  "price": 220,
  "category": "office",
  "in_stock": true,
  "stock_qty": 150,
  "delivery_days": 1,
  "attributes": {"color": "black", "type": "ballpoint", "weight_g": 12}
}
```

**Response 404**

```json
{
  "error": "not_found",
  "agent_hint": "指定されたproduct_idが見つかりません。/v1/searchで再検索してください。"
}
```

---

### `POST /v1/orders` — 注文作成

**Request**

```json
{
  "items": [
    {"product_id": "prod_uuid", "qty": 2}
  ],
  "delivery_profile_id": "profile_uuid",
  "dry_run": false              // true: シミュレーションのみ（DBに保存しない）
}
```

**Response 200（dry_run: false — 注文確定）**

```json
{
  "order_id": "ord_uuid",
  "status": "confirmed",
  "items": [
    {"product_id": "prod_uuid", "name": "ジェットストリーム", "qty": 2, "price": 220}
  ],
  "subtotal": 440,
  "estimated_delivery": "2026-03-15",
  "dry_run": false,
  "agent_hint": "注文確定。GET /v1/orders/ord_uuid で配送状況を確認できます。"
}
```

**Response 200（dry_run: true — シミュレーション）**

```json
{
  "order_id": null,
  "status": "dry_run_ok",
  "subtotal": 440,
  "estimated_delivery": "2026-03-15",
  "dry_run": true,
  "policy_check": {
    "passed": true,
    "auto_approved": true,
    "reason": "合計440円 < ポリシー上限5000円"
  },
  "agent_hint": "シミュレーション成功。dry_run:falseで実際に注文できます。"
}
```

**Response 403（ポリシー違反）**

```json
{
  "error": "policy_violation",
  "reason": "合計6000円はポリシー上限5000円を超えています",
  "agent_hint": "注文額を下げるか、管理者にポリシー上限変更を依頼してください。"
}
```

**Response 409（在庫不足）**

```json
{
  "error": "out_of_stock",
  "product_id": "prod_uuid",
  "requested_qty": 10,
  "available_qty": 3,
  "agent_hint": "在庫が不足しています。qtyを3以下にするか別商品を検索してください。"
}
```

---

### `GET /v1/orders/{order_id}` — 注文状況確認

**Response 200**

```json
{
  "order_id": "ord_uuid",
  "status": "shipped",
  "items": [
    {"name": "ジェットストリーム", "qty": 2, "price": 220}
  ],
  "subtotal": 440,
  "estimated_delivery": "2026-03-15",
  "tracking_number": "1234-5678-9012",
  "created_at": "2026-03-14T10:00:00Z",
  "agent_hint": "発送済み。明日配達予定です。"
}
```

---

## 7. ポリシーエンジン

APIキーごとに設定し、エージェントの行動範囲を制限する。

### ポリシー項目

| フィールド | 型 | 説明 | デフォルト |
|-----------|-----|------|----------|
| `auto_approve_under` | integer | この金額（円）以下は自動決済 | 無制限 |
| `allowed_categories` | string[] | 許可カテゴリ一覧（空=全許可） | [] (全許可) |
| `max_orders_per_day` | integer | 1日の注文上限件数 | 無制限 |
| `max_items_per_order` | integer | 1注文あたりの商品種数上限 | 無制限 |
| `require_dry_run` | boolean | 本注文前にdry-runを必須とする | false |

### 検証ロジック（疑似コード）

```python
def check_policy(api_key: APIKey, order_request: OrderRequest) -> PolicyResult:
    policy = api_key.policy
    subtotal = calculate_subtotal(order_request.items)

    # 1. カテゴリ制限チェック
    if policy.get("allowed_categories"):
        for item in order_request.items:
            product = get_product(item.product_id)
            if product.category not in policy["allowed_categories"]:
                return PolicyResult(passed=False,
                    reason=f"カテゴリ'{product.category}'は許可されていません")

    # 2. 金額上限チェック
    limit = policy.get("auto_approve_under", float("inf"))
    if subtotal > limit:
        return PolicyResult(passed=False,
            reason=f"合計{subtotal}円はポリシー上限{limit}円を超えています")

    # 3. 1日の注文数チェック
    max_per_day = policy.get("max_orders_per_day", float("inf"))
    today_count = count_orders_today(api_key.id)
    if today_count >= max_per_day:
        return PolicyResult(passed=False,
            reason=f"本日の注文上限({max_per_day}件)に達しています")

    return PolicyResult(passed=True, auto_approved=True)
```

---

## 8. 管理UI

### 対象ユーザー: 人間（管理者）のみ

ブラウザからのみアクセス可能。エージェントによる注文操作は不可。

### 画面一覧

| 画面 | 機能 |
|------|------|
| 商品一覧 / 登録 / 編集 | 商品マスタ管理 |
| APIキー一覧 / 発行 | APIキーの作成・無効化 |
| ポリシー設定 | APIキーごとのポリシー編集 |
| 配送先プロファイル管理 | 配送先の登録・編集 |
| 注文一覧 | 全注文の確認・ステータス更新 |
| 監査ログ | エージェントの行動ログ確認 |

---

## 9. ディレクトリ構成

```
agent-commerce/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app・router登録・CORS設定
│   │   ├── database.py           # SQLAlchemy async engine
│   │   ├── models/
│   │   │   ├── product.py
│   │   │   ├── order.py
│   │   │   ├── api_key.py
│   │   │   ├── delivery_profile.py
│   │   │   └── order_log.py
│   │   ├── routers/
│   │   │   ├── search.py         # POST /v1/search
│   │   │   ├── products.py       # GET  /v1/products/:id
│   │   │   └── orders.py         # POST/GET /v1/orders
│   │   ├── services/
│   │   │   ├── policy_engine.py  # ポリシー検証ロジック
│   │   │   ├── auth.py           # APIキー認証ミドルウェア
│   │   │   └── inventory.py      # 在庫チェック・引き当て
│   │   └── schemas/
│   │       ├── search.py
│   │       ├── orders.py
│   │       └── products.py
│   ├── migrations/               # Alembic
│   │   ├── versions/
│   │   └── env.py
│   ├── Dockerfile
│   ├── railway.toml
│   ├── pyproject.toml
│   └── .env.example
├── admin-ui/                     # Next.js（管理画面）
│   ├── app/
│   │   ├── products/
│   │   ├── api-keys/
│   │   ├── orders/
│   │   └── logs/
│   └── package.json
├── docker-compose.yml            # ローカル開発用
└── README.md
```

---

## 10. 開発ロードマップ

| Week | タスク | 完了条件 |
|------|--------|---------|
| Week 1 | DB設計・Alembicマイグレーション・商品CRUD | マイグレーション完了、商品の登録・取得が動く |
| Week 2 | 商品検索API + APIキー認証ミドルウェア | `POST /v1/search` がcurlで動作確認できる |
| Week 3 | 注文API + ポリシーエンジン実装 | dry_run・ポリシー違反レスポンスが正しく返る |
| Week 4 | 管理UI（商品登録・APIキー発行・ポリシー設定） | ブラウザから全設定が操作できる |
| Week 5 | Railwayへのデプロイ・統合テスト | 本番URLでcurlが通る |
| Week 6 | デモエージェント作成 | ClaudeまたはGPTから実際に注文できるデモ動画 |

### Claude Codeへの投げ方（参考）

```
# Week 1 の例
このFastAPIプロジェクトのDB層を作って。
仕様書のスキーマに従ってAlembicマイグレーションと
SQLAlchemyモデルを生成し、docker-compose.ymlも作成して。
```

```
# デプロイ時の例
このFastAPIをRailwayにデプロイできるよう、
Dockerfile・railway.toml・.env.exampleを作成して。
GET /health エンドポイントも追加して。
```

---

## 11. Phase 2 以降（参考）

### Phase 2: MCPサーバー化・自然言語検索

- **MCP Server**: `search_products` / `create_order` をMCPツールとして公開  
  → ClaudeのDesktop / Claude Codeから直接呼び出し可能に
- **自然言語検索**: `POST /v1/search` に `query` フィールドを追加、内部でLLMが構造化フィルタに変換
- **Webhook**: 注文ステータス変化をエージェントのエンドポイントにPOST通知

### Phase 3: マーケットプレイス化

- **マルチテナント**: 複数の販売者が商品を登録できるプラットフォーム化
- **Agent間取引**: エージェントがエージェントに発注するB2B的なユースケース対応
- **使用量ダッシュボード**: エージェントごとのAPI使用量・注文金額の可視化
