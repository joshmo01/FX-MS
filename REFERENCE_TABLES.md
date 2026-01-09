# FX Smart Routing Engine v2.0 - Reference Tables & Data Dictionary

## Table of Contents
1. [Routing Objectives](#1-routing-objectives)
2. [FX Providers](#2-fx-providers)
3. [Customer Tiers](#3-customer-tiers)
4. [Treasury Rates](#4-treasury-rates)
5. [CBDC Currencies](#5-cbdc-currencies)
6. [Stablecoins](#6-stablecoins)
7. [Digital Rails](#7-digital-rails)
8. [On/Off Ramp Providers](#8-onoff-ramp-providers)
9. [Conversion Matrix](#9-conversion-matrix)
10. [Route Definitions](#10-route-definitions)
11. [Atomic Swap Pairs](#11-atomic-swap-pairs)
12. [Volume-Based Pricing](#12-volume-based-pricing)

---

## 1. Routing Objectives

**Table: `routing_objectives`**

| Field | Type | Description |
|-------|------|-------------|
| `objective_id` | STRING | Primary key (BEST_RATE, OPTIMUM, FASTEST_EXECUTION, MAX_STP) |
| `description` | STRING | Human-readable description |
| `priority_weights.rate` | DECIMAL | Weight for rate optimization (0-1) |
| `priority_weights.provider_reliability` | DECIMAL | Weight for provider reliability (0-1) |
| `priority_weights.settlement_speed` | DECIMAL | Weight for settlement speed (0-1) |
| `priority_weights.stp_capability` | DECIMAL | Weight for STP capability (0-1) |

**Data:**

| Objective | Description | Rate | Reliability | Speed | STP |
|-----------|-------------|------|-------------|-------|-----|
| `BEST_RATE` | Lowest cost for customer | 0.70 | 0.15 | 0.10 | 0.05 |
| `OPTIMUM` | Balanced - cost, speed, reliability | 0.40 | 0.25 | 0.20 | 0.15 |
| `FASTEST_EXECUTION` | Fastest settlement priority | 0.20 | 0.25 | 0.45 | 0.10 |
| `MAX_STP` | Maximum straight-through processing | 0.25 | 0.20 | 0.15 | 0.40 |

---

## 2. FX Providers

**Table: `fx_providers`**

| Field | Type | Description |
|-------|------|-------------|
| `provider_id` | STRING | Primary key |
| `name` | STRING | Display name |
| `type` | ENUM | MARKET_DATA, INTERNAL, CORRESPONDENT_BANK, LOCAL_BANK, FINTECH, FOREX_DEALER |
| `is_active` | BOOLEAN | Provider enabled status |
| `capabilities.real_time_rates` | BOOLEAN | Supports real-time rates |
| `capabilities.executable_quotes` | BOOLEAN | Provides executable quotes |
| `capabilities.settlement` | BOOLEAN | Can settle transactions |
| `capabilities.stp_enabled` | BOOLEAN | Supports straight-through processing |
| `supported_pairs` | ARRAY[STRING] | Currency pairs supported |
| `reliability_score` | DECIMAL | 0-1 reliability rating |
| `avg_latency_ms` | INTEGER | Average response time |
| `settlement_hours` | INTEGER | Settlement time in hours |
| `daily_limit_usd` | INTEGER | Daily transaction limit |
| `markup_bps` | INTEGER | Markup in basis points |
| `min_amount_usd` | INTEGER | Minimum transaction amount |
| `operating_hours.start` | TIME | Operating window start |
| `operating_hours.end` | TIME | Operating window end |
| `operating_hours.timezone` | STRING | Operating timezone |

**Data:**

| Provider | Type | Reliability | Latency | Settlement | Limit (USD) | Markup |
|----------|------|-------------|---------|------------|-------------|--------|
| `REFINITIV` | MARKET_DATA | 0.98 | 50ms | - | - | 0 bps |
| `TREASURY_INTERNAL` | INTERNAL | 0.99 | 10ms | 4h | 50M | 15 bps |
| `BANK_OF_AMERICA` | CORRESPONDENT_BANK | 0.97 | 100ms | 24h | 100M | 8 bps |
| `CITI` | CORRESPONDENT_BANK | 0.96 | 120ms | 24h | 150M | 10 bps |
| `HDFC_BANK` | LOCAL_BANK | 0.95 | 80ms | 4h | 25M | 18 bps |
| `ICICI_BANK` | LOCAL_BANK | 0.94 | 90ms | 4h | 20M | 20 bps |
| `WISE` | FINTECH | 0.92 | 200ms | 12h | 1M | 4 bps |

---

## 3. Customer Tiers

**Table: `customer_tiers`**

| Field | Type | Description |
|-------|------|-------------|
| `tier_id` | STRING | Primary key (PLATINUM, GOLD, SILVER, BRONZE, RETAIL) |
| `name` | STRING | Display name |
| `description` | STRING | Tier description |
| `min_annual_volume_usd` | INTEGER | Minimum annual volume |
| `markup_discount_pct` | INTEGER | Discount on markup (%) |
| `spread_reduction_bps` | INTEGER | Spread reduction (bps) |
| `priority_routing` | BOOLEAN | Priority routing enabled |
| `dedicated_treasury` | BOOLEAN | Dedicated treasury access |
| `max_transaction_usd` | INTEGER | Maximum transaction size |
| `stp_threshold_usd` | INTEGER | Auto-STP threshold |
| `providers_allowed` | ARRAY[STRING] | Allowed provider list |
| `default_objective` | STRING | Default routing objective |

**Data:**

| Tier | Min Volume | Markup Disc. | Spread Red. | Priority | Max Txn | Default Obj. |
|------|------------|--------------|-------------|----------|---------|--------------|
| `PLATINUM` | $100M | 50% | 10 bps | ✓ | $50M | BEST_RATE |
| `GOLD` | $10M | 30% | 5 bps | ✓ | $10M | OPTIMUM |
| `SILVER` | $1M | 15% | 2 bps | ✗ | $1M | OPTIMUM |
| `BRONZE` | $100K | 5% | 0 bps | ✗ | $100K | OPTIMUM |
| `RETAIL` | $0 | 0% | 0 bps | ✗ | $25K | BEST_RATE |

---

## 4. Treasury Rates

**Table: `treasury_rates`**

| Field | Type | Description |
|-------|------|-------------|
| `pair` | STRING | Currency pair (e.g., USDINR) |
| `bid` | DECIMAL | Bid rate |
| `ask` | DECIMAL | Ask rate |
| `mid` | DECIMAL | Mid-market rate |
| `internal_cost` | DECIMAL | Internal cost rate |
| `min_margin_bps` | INTEGER | Minimum margin required |
| `target_margin_bps` | INTEGER | Target margin |
| `max_exposure_usd` | INTEGER | Maximum exposure limit |
| `current_exposure_usd` | INTEGER | Current exposure |
| `position` | ENUM | LONG, SHORT, NEUTRAL |
| `valid_until` | TIMESTAMP | Rate validity expiry |

**Data:**

| Pair | Bid | Ask | Mid | Min Margin | Target Margin | Max Exposure | Position |
|------|-----|-----|-----|------------|---------------|--------------|----------|
| `USDINR` | 84.42 | 84.58 | 84.50 | 10 bps | 20 bps | $10M | LONG |
| `EURINR` | 89.10 | 89.30 | 89.20 | 12 bps | 25 bps | $8M | NEUTRAL |
| `GBPINR` | 106.35 | 106.65 | 106.50 | 15 bps | 28 bps | $5M | SHORT |
| `EURUSD` | 1.0550 | 1.0564 | 1.0557 | 5 bps | 12 bps | $20M | LONG |
| `AEDINR` | 22.98 | 23.04 | 23.01 | 18 bps | 32 bps | $3M | NEUTRAL |

**Position Adjustment Rules:**

| Position | Sell Adj. | Buy Adj. | Description |
|----------|-----------|----------|-------------|
| `LONG` | -3 bps | +3 bps | Encourage selling to reduce position |
| `SHORT` | +3 bps | -3 bps | Encourage buying to cover position |
| `NEUTRAL` | 0 bps | 0 bps | No position bias |

---

## 5. CBDC Currencies

**Table: `cbdc`**

| Field | Type | Description |
|-------|------|-------------|
| `code` | STRING | CBDC code (e.g., e-INR) |
| `name` | STRING | Display name |
| `issuer` | STRING | Issuing central bank |
| `country` | STRING | Country of issuance |
| `fiat_currency` | STRING | Linked fiat currency |
| `status` | ENUM | PILOT, EXPERIMENTAL, PRODUCTION |
| `technology` | STRING | Underlying technology |
| `is_active` | BOOLEAN | Active status |
| `decimal_places` | INTEGER | Decimal precision |
| `wallet_types` | ARRAY[STRING] | Supported wallet types |
| `balance_limit` | INTEGER | Maximum wallet balance |
| `transaction_limit` | INTEGER | Maximum transaction size |
| `settlement_type` | STRING | Settlement mechanism |
| `settlement_seconds` | INTEGER | Settlement time |
| `operating_hours` | STRING | Operating schedule |
| `cross_border_enabled` | BOOLEAN | Cross-border support |
| `mbridge_participant` | BOOLEAN | mBridge member |
| `fees.issuance_bps` | INTEGER | Minting fee |
| `fees.redemption_bps` | INTEGER | Redemption fee |
| `fees.transfer_bps` | INTEGER | Transfer fee |
| `compliance.kyc_required` | BOOLEAN | KYC requirement |
| `compliance.aml_screening` | STRING | AML screening level |

**Data:**

| Code | Name | Issuer | Status | Technology | Settlement | mBridge | Cross-Border |
|------|------|--------|--------|------------|------------|---------|--------------|
| `e-INR` | Digital Rupee | RBI | PILOT | R3 Corda | 5s | ✗ | ✗ |
| `e-CNY` | Digital Yuan | PBoC | PILOT | Proprietary DLT | 3s | ✓ | ✓ |
| `e-HKD` | Digital HKD | HKMA | PILOT | R3 Corda | 5s | ✓ | ✓ |
| `e-THB` | Digital Baht | BoT | PILOT | Hyperledger | 5s | ✓ | ✓ |
| `e-AED` | Digital Dirham | CBUAE | PILOT | R3 Corda | 5s | ✓ | ✓ |
| `e-SGD` | Digital SGD | MAS | EXPERIMENTAL | ETH/Hyperledger | 10s | ✗ | ✓ |

---

## 6. Stablecoins

**Table: `stablecoins`**

| Field | Type | Description |
|-------|------|-------------|
| `code` | STRING | Stablecoin code |
| `name` | STRING | Display name |
| `issuer` | STRING | Issuing organization |
| `type` | ENUM | FIAT_BACKED, CRYPTO_BACKED, ALGORITHMIC |
| `pegged_currency` | STRING | Pegged fiat currency |
| `peg_ratio` | DECIMAL | Peg ratio (1.0 = 1:1) |
| `is_active` | BOOLEAN | Active status |
| `decimal_places` | INTEGER | Decimal precision |
| `networks` | ARRAY[OBJECT] | Supported blockchain networks |
| `networks[].chain` | STRING | Blockchain name |
| `networks[].contract` | STRING | Smart contract address |
| `networks[].settlement_seconds` | INTEGER | Settlement time |
| `networks[].fee_usd` | DECIMAL | Network fee |
| `market_cap_usd` | INTEGER | Market capitalization |
| `daily_volume_usd` | INTEGER | 24h trading volume |
| `reserve_attestation` | STRING | Reserve attestation frequency |
| `regulatory_status` | STRING | Regulatory status |
| `regulated_by` | ARRAY[STRING] | Regulatory bodies |
| `liquidity_score` | INTEGER | Liquidity score (0-100) |
| `fees.mint_bps` | INTEGER | Minting fee |
| `fees.redeem_bps` | INTEGER | Redemption fee |
| `fees.transfer_bps` | INTEGER | Transfer fee |
| `compliance.kyc_required` | BOOLEAN | KYC requirement |
| `compliance.travel_rule_applicable` | BOOLEAN | Travel Rule applies |

**Data:**

| Code | Issuer | Peg | Regulatory | Liquidity | Mint Fee | Redeem Fee |
|------|--------|-----|------------|-----------|----------|------------|
| `USDT` | Tether | USD | UNREGULATED | 100 | 10 bps | 10 bps |
| `USDC` | Circle | USD | REGULATED_US | 95 | 0 bps | 0 bps |
| `EURC` | Circle | EUR | MICA_COMPLIANT | 60 | 0 bps | 0 bps |
| `PYUSD` | Paxos | USD | REGULATED_US | 50 | 0 bps | 0 bps |
| `XSGD` | StraitsX | SGD | MAS_LICENSED | 40 | 0 bps | 10 bps |

**Stablecoin Networks:**

| Stablecoin | Chain | Settlement | Fee (USD) |
|------------|-------|------------|-----------|
| `USDT` | ETHEREUM | 180s | $15.00 |
| `USDT` | TRON | 10s | $1.00 |
| `USDT` | SOLANA | 5s | $0.01 |
| `USDT` | POLYGON | 10s | $0.10 |
| `USDC` | ETHEREUM | 180s | $15.00 |
| `USDC` | SOLANA | 5s | $0.01 |
| `USDC` | POLYGON | 10s | $0.10 |
| `USDC` | AVALANCHE | 5s | $0.10 |
| `EURC` | ETHEREUM | 180s | $15.00 |
| `EURC` | AVALANCHE | 5s | $0.10 |
| `PYUSD` | ETHEREUM | 180s | $15.00 |
| `PYUSD` | SOLANA | 5s | $0.01 |
| `XSGD` | ETHEREUM | 180s | $15.00 |
| `XSGD` | POLYGON | 10s | $0.10 |

---

## 7. Digital Rails

**Table: `digital_rails`**

| Field | Type | Description |
|-------|------|-------------|
| `rail_id` | STRING | Primary key |
| `name` | STRING | Display name |
| `type` | ENUM | CBDC, CBDC_CROSS_BORDER, FAST_PAYMENT_LINKAGE, STABLECOIN, HYBRID |
| `description` | STRING | Rail description |
| `is_active` | BOOLEAN | Active status |
| `participants` | ARRAY[STRING] | Participating currencies/systems |
| `supported_operations` | ARRAY[STRING] | Supported operation types |
| `settlement_type` | ENUM | INSTANT, ATOMIC, NEAR_INSTANT, VARIABLE |
| `avg_settlement_seconds` | INTEGER | Average settlement time |
| `operating_hours` | STRING | Operating schedule |
| `min_amount_usd` | INTEGER | Minimum transaction amount |
| `fee_structure.cross_border_bps` | INTEGER | Cross-border fee |
| `fee_structure.fx_spread_bps` | INTEGER | FX spread |
| `compliance.kyc_level` | STRING | KYC requirement level |
| `compliance.aml_screening` | STRING | AML screening approach |

**Data:**

| Rail ID | Name | Type | Settlement | Avg Time | Fee (bps) |
|---------|------|------|------------|----------|-----------|
| `CBDC_DOMESTIC` | Domestic CBDC | CBDC | INSTANT | 5s | 0 |
| `MBRIDGE` | mBridge | CBDC_CROSS_BORDER | ATOMIC | 10s | 13 |
| `PROJECT_NEXUS` | Project Nexus | FAST_PAYMENT_LINKAGE | NEAR_INSTANT | 60s | 35 |
| `STABLECOIN_BRIDGE` | Stablecoin Bridge | STABLECOIN | VARIABLE | 5-180s | 50-100 |
| `HYBRID_CBDC_STABLE` | Hybrid Bridge | HYBRID | VARIABLE | TBD | TBD |

**mBridge Participants:**

| CBDC | Central Bank | Status |
|------|--------------|--------|
| `e-CNY` | PBoC | Active |
| `e-HKD` | HKMA | Active |
| `e-THB` | BoT | Active |
| `e-AED` | CBUAE | Active |

**Project Nexus Participants:**

| Country | System | Currency | Future CBDC |
|---------|--------|----------|-------------|
| India | UPI | INR | e-INR |
| Singapore | PayNow | SGD | e-SGD |
| Malaysia | DuitNow | MYR | - |
| Thailand | PromptPay | THB | e-THB |
| Philippines | InstaPay | PHP | - |

---

## 8. On/Off Ramp Providers

**Table: `on_off_ramp_providers`**

| Field | Type | Description |
|-------|------|-------------|
| `provider_id` | STRING | Primary key |
| `name` | STRING | Display name |
| `type` | ENUM | REGULATED_ISSUER, EXCHANGE, CBDC_ISSUER |
| `is_active` | BOOLEAN | Active status |
| `supported_stablecoins` | ARRAY[STRING] | Supported stablecoins |
| `supported_cbdc` | ARRAY[STRING] | Supported CBDCs |
| `supported_fiat` | ARRAY[STRING] | Supported fiat currencies |
| `on_ramp.methods` | ARRAY[STRING] | Deposit methods |
| `on_ramp.min_amount_usd` | INTEGER | Minimum on-ramp amount |
| `on_ramp.max_amount_usd` | INTEGER | Maximum on-ramp amount |
| `on_ramp.settlement_hours` | INTEGER | On-ramp settlement time |
| `on_ramp.fee_bps` | INTEGER | On-ramp fee |
| `off_ramp.methods` | ARRAY[STRING] | Withdrawal methods |
| `off_ramp.min_amount_usd` | INTEGER | Minimum off-ramp amount |
| `off_ramp.max_amount_usd` | INTEGER | Maximum off-ramp amount |
| `off_ramp.settlement_hours` | INTEGER | Off-ramp settlement time |
| `off_ramp.fee_bps` | INTEGER | Off-ramp fee |
| `compliance.kyc_required` | BOOLEAN | KYC requirement |
| `compliance.institutional_only` | BOOLEAN | Institutional only |
| `compliance.jurisdictions` | ARRAY[STRING] | Supported jurisdictions |
| `reliability_score` | DECIMAL | Provider reliability (0-1) |
| `stp_enabled` | BOOLEAN | STP support |

**Data:**

| Provider | Type | On-Ramp Fee | Off-Ramp Fee | Settlement | Reliability |
|----------|------|-------------|--------------|------------|-------------|
| `CIRCLE` | REGULATED_ISSUER | 0 bps | 0 bps | 1h / 1h | 0.99 |
| `COINBASE_PRIME` | EXCHANGE | 20 bps | 25 bps | 4h / 24h | 0.97 |
| `KRAKEN_INSTITUTIONAL` | EXCHANGE | 15 bps | 20 bps | 2h / 24h | 0.95 |
| `STRAITSX` | REGULATED_ISSUER | 0 bps | 10 bps | 1h / 1h | 0.94 |
| `RBI_PARTNER_BANK` | CBDC_ISSUER | 0 bps | 0 bps | Instant | 0.99 |

---

## 9. Conversion Matrix

**Table: `conversion_matrix`**

| Field | Type | Description |
|-------|------|-------------|
| `conversion_type` | STRING | Primary key |
| `enabled` | BOOLEAN | Conversion enabled |
| `routes` | ARRAY[STRING] | Available routes |
| `description` | STRING | Conversion description |
| `route_details[route].legs` | INTEGER | Number of legs |
| `route_details[route].fee_bps` | INTEGER | Total fee in bps |
| `route_details[route].settlement` | STRING | Settlement time |
| `route_details[route].regulated` | BOOLEAN | Is regulated path |
| `route_details[route].experimental` | BOOLEAN | Is experimental |
| `route_details[route].recommended` | BOOLEAN | Is recommended |
| `route_details[route].best` | BOOLEAN | Is best option |

**Conversion Types:**

| Type | Routes | Fee Range | Settlement | Status |
|------|--------|-----------|------------|--------|
| `FIAT_TO_FIAT` | DIRECT, TRIANGULATED, CORRESPONDENT | 8-25 bps | 4h-3d | Production |
| `FIAT_TO_CBDC` | DIRECT_MINT, FX_THEN_MINT | 0-20 bps | 5s-4h | Production |
| `CBDC_TO_FIAT` | DIRECT_REDEEM, REDEEM_THEN_FX | 0-20 bps | 5s-4h | Production |
| `CBDC_TO_CBDC` | MBRIDGE, REDEEM_FX_MINT, PROJECT_NEXUS | 13-40 bps | 15s-8h | Pilot |
| `FIAT_TO_STABLECOIN` | DIRECT_MINT, ON_RAMP_EXCHANGE | 0-50 bps | 1-4h | Production |
| `STABLECOIN_TO_FIAT` | DIRECT_REDEEM, OFF_RAMP_EXCHANGE | 0-50 bps | 1-24h | Production |
| `STABLECOIN_TO_STABLECOIN` | DEX_SWAP, CEX_SWAP, BRIDGE_PROTOCOL | 20-50 bps | 30s-5m | Production |
| `CBDC_TO_STABLECOIN` | CBDC_FIAT_STABLE, CEX_BRIDGE, MBRIDGE_HYBRID, DEX_LIQUIDITY, ATOMIC_SWAP | 5-50 bps | 5m-5h | Experimental |
| `STABLECOIN_TO_CBDC` | STABLE_FIAT_CBDC, CEX_BRIDGE, OTC_TRADE, LIQUIDITY_POOL, ATOMIC_SWAP | 5-50 bps | 5m-5h | Experimental |

---

## 10. Route Definitions

**Table: `route_definitions`**

| Route ID | Legs | Description |
|----------|------|-------------|
| `DIRECT` | 1 | Direct conversion without intermediary |
| `TRIANGULATED` | 2 | Via bridge currency (USD/EUR) for better rate |
| `CORRESPONDENT` | 1 | Via correspondent bank |
| `DIRECT_MINT` | 1 | Direct minting of digital currency |
| `FX_THEN_MINT` | 2 | FX conversion then mint digital currency |
| `DIRECT_REDEEM` | 1 | Direct redemption to fiat |
| `REDEEM_THEN_FX` | 2 | Redeem then FX conversion |
| `MBRIDGE` | 2 | Cross-border CBDC via mBridge platform |
| `REDEEM_FX_MINT` | 3 | Redeem source CBDC, FX, mint target CBDC |
| `PROJECT_NEXUS` | 2 | Via Project Nexus fast payment linkage |
| `ON_RAMP_EXCHANGE` | 2 | Fiat deposit then purchase stablecoin |
| `OFF_RAMP_EXCHANGE` | 2 | Sell stablecoin then fiat withdrawal |
| `DEX_SWAP` | 1 | Decentralized exchange swap |
| `CEX_SWAP` | 1 | Centralized exchange swap |
| `BRIDGE_PROTOCOL` | 2 | Cross-chain bridge protocol |
| `CBDC_FIAT_STABLE` | 3 | CBDC → Fiat → Stablecoin |
| `STABLE_FIAT_CBDC` | 3 | Stablecoin → Fiat → CBDC |
| `CEX_BRIDGE` | 2 | Via centralized exchange bridge |
| `MBRIDGE_HYBRID` | 3 | mBridge + Stablecoin mint |
| `DEX_LIQUIDITY` | 2 | Via DeFi liquidity pool |
| `OTC_TRADE` | 1 | Over-the-counter trade |
| `LIQUIDITY_POOL` | 2 | Via liquidity pool |
| `ATOMIC_SWAP` | 1 | HTLC atomic swap (trustless) |

---

## 11. Atomic Swap Pairs

**Table: `atomic_swap_pairs`**

| Field | Type | Description |
|-------|------|-------------|
| `pair_id` | STRING | Unique pair identifier |
| `source` | STRING | Source currency (CBDC or Stablecoin) |
| `target` | STRING | Target currency (CBDC or Stablecoin) |
| `status` | ENUM | PILOT, EXPERIMENTAL, PLANNED |
| `risk_level` | ENUM | LOW, MEDIUM, HIGH |
| `fee_bps` | INTEGER | Fee in basis points |
| `settlement_seconds` | INTEGER | Settlement time |
| `min_amount_usd` | INTEGER | Minimum amount |
| `max_amount_usd` | INTEGER | Maximum amount |
| `daily_limit_usd` | INTEGER | Daily volume limit |
| `protocol` | STRING | HTLC protocol |
| `hash_function` | STRING | Hash function used |
| `timelock_hours` | INTEGER | HTLC timelock period |

**Data:**

| Pair | Source | Target | Status | Risk | Fee | Settlement |
|------|--------|--------|--------|------|-----|------------|
| `eINR-USDC` | e-INR | USDC | EXPERIMENTAL | Medium | 15 bps | 5 min |
| `USDC-eINR` | USDC | e-INR | EXPERIMENTAL | Medium | 15 bps | 5 min |
| `eSGD-XSGD` | e-SGD | XSGD | PILOT | Low | 15 bps | 5 min |
| `XSGD-eSGD` | XSGD | e-SGD | PILOT | Low | 15 bps | 5 min |
| `eCNY-USDT` | e-CNY | USDT | PLANNED | High | 15 bps | 5 min |
| `eAED-USDC` | e-AED | USDC | PLANNED | Medium | 15 bps | 5 min |

---

## 12. Volume-Based Pricing

**Table: `volume_pricing_tiers`**

| Min USD | Max USD | Additional Markup (bps) |
|---------|---------|------------------------|
| 0 | 10,000 | +10 bps |
| 10,000 | 100,000 | +5 bps |
| 100,000 | 1,000,000 | +2 bps |
| 1,000,000 | 10,000,000 | 0 bps |
| 10,000,000 | Unlimited | -2 bps |

**Table: `tenure_discount`**

| Tenure | Discount (bps) |
|--------|---------------|
| 1 year | 0 bps |
| 2 years | 2 bps |
| 5 years | 5 bps |
| 10 years | 10 bps |

---

## Path Optimization Rules

| Parameter | Value |
|-----------|-------|
| `max_legs` | 4 |
| `max_intermediaries` | 2 |
| `prefer_regulated_paths` | true |
| `avoid_unregulated_stablecoins` | false |
| `min_liquidity_score` | 40 |

---

## Route Preferences

| Preference | Order | Use Case |
|------------|-------|----------|
| `CBDC_PREFERRED` | CBDC_DOMESTIC → MBRIDGE → PROJECT_NEXUS → STABLECOIN_BRIDGE → FIAT | When CBDC rails available |
| `STABLECOIN_PREFERRED` | STABLECOIN_BRIDGE → CBDC_DOMESTIC → FIAT | Cost optimization |
| `FIAT_PREFERRED` | FIAT → CBDC_DOMESTIC → STABLECOIN_BRIDGE | Traditional approach |
| `FASTEST` | CBDC_DOMESTIC → STABLECOIN_BRIDGE → MBRIDGE → FIAT | Speed priority |
| `LOWEST_COST` | CBDC_DOMESTIC → MBRIDGE → STABLECOIN_BRIDGE → FIAT | Cost priority |

---

*Document Version: 2.0.0*
*Last Updated: 2025-12-09*
*Author: Fintaar.ai*
