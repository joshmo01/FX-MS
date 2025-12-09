# FX Smart Routing - Complete Route Summary

## All 9 Conversion Types with Routes

### Overview

```
┌───────────────────────────────────────────────────────────────────────────┐
│                    CONVERSION MATRIX (9 Types)                            │
├───────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│              FIAT ─────────────────► CBDC ──────────────► STABLECOIN     │
│                │                      │                        │          │
│                │                      │                        │          │
│              FIAT ◄───────────────── CBDC ◄────────────── STABLECOIN     │
│                │                      │                        │          │
│                │                      │                        │          │
│              FIAT ◄─────────────────► FIAT                    │          │
│                                       │                        │          │
│                                     CBDC ◄─────────────► CBDC │          │
│                                                                │          │
│                                     STABLECOIN ◄─────► STABLECOIN        │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 1️⃣ FIAT → FIAT (4 Routes)

| Route | Legs | Fee (bps) | Settlement | Regulated |
|-------|------|-----------|------------|-----------|
| **SWIFT Direct** | 1 | 25 | 1-3 days | ✅ |
| **Local Rails (RTGS)** | 1 | 15 | 4 hours | ✅ |
| **USD Triangulation** | 2 | 30 | 4-8 hours | ✅ |
| **Fintech Rail (Wise)** | 1 | 6 | 12 hours | ✅ |

---

## 2️⃣ FIAT → CBDC (3 Routes)

| Route | Legs | Fee (bps) | Settlement | Regulated | Notes |
|-------|------|-----------|------------|-----------|-------|
| **Direct Mint** ⭐ | 1 | 0 | 5 seconds | ✅ | Same currency only |
| **FX + Mint** | 2 | 20 | 4 hours | ✅ | Cross-currency |
| **mBridge Route** 🔥 | 3 | 13 | 30 seconds | ✅ | Recommended for mBridge CBDCs |

---

## 3️⃣ CBDC → FIAT (2 Routes)

| Route | Legs | Fee (bps) | Settlement | Regulated |
|-------|------|-----------|------------|-----------|
| **Direct Redeem** ⭐ | 1 | 0 | 5 seconds | ✅ |
| **Redeem + FX** | 2 | 20 | 4 hours | ✅ |

---

## 4️⃣ CBDC → CBDC (3 Routes)

| Route | Legs | Fee (bps) | Settlement | Regulated | Notes |
|-------|------|-----------|------------|-----------|-------|
| **mBridge PvP** ⭐🔥 | 1 | 13 | 15 seconds | ✅ | Atomic settlement |
| **Project Nexus** | 1 | 35 | 60 seconds | ✅ | Interlinked IPS |
| **Fiat Bridge** | 4 | 40 | 8 hours | ✅ | Fallback option |

### mBridge Supported Pairs
- e-CNY ↔ e-HKD
- e-CNY ↔ e-THB
- e-CNY ↔ e-AED
- e-HKD ↔ e-THB
- e-HKD ↔ e-AED
- e-THB ↔ e-AED

---

## 5️⃣ FIAT → STABLECOIN (3 Routes)

| Route | Legs | Fee (bps) | Settlement | Regulated | Stablecoins |
|-------|------|-----------|------------|-----------|-------------|
| **Circle On-Ramp** ⭐ | 1 | 0 | 1 hour | ✅ | USDC, EURC |
| **CEX On-Ramp** | 1 | 25 | 2 hours | ✅ | USDC, USDT, PYUSD |
| **FX + On-Ramp** | 2 | 50 | 5 hours | ✅ | All |

---

## 6️⃣ STABLECOIN → FIAT (3 Routes)

| Route | Legs | Fee (bps) | Settlement | Regulated |
|-------|------|-----------|------------|-----------|
| **Circle Off-Ramp** ⭐ | 1 | 0 | 1 hour | ✅ |
| **CEX Off-Ramp** | 1 | 25 | 2 hours | ✅ |
| **Off-Ramp + FX** | 2 | 50 | 5 hours | ✅ |

---

## 7️⃣ STABLECOIN → STABLECOIN (3 Routes)

| Route | Legs | Fee (bps) | Settlement | Regulated | Notes |
|-------|------|-----------|------------|-----------|-------|
| **Curve DEX** ⭐ | 1 | 4 | 1 minute | ❌ | Lowest fees |
| **Uniswap V3** | 1 | 30 | 1 minute | ❌ | Multi-network |
| **CEX Trade** | 1 | 20 | 10 seconds | ✅ | Fastest |

---

## 8️⃣ CBDC → STABLECOIN (5 Routes) ⭐ NEW

| Route | Legs | Fee (bps) | Settlement | Regulated | Path |
|-------|------|-----------|------------|-----------|------|
| **Fiat Intermediary** | 2 | 25 | 5 hours | ✅ | CBDC → FIAT → STABLE |
| **CEX Bridge** | 2 | 50 | 2 hours | ✅ | CBDC → FIAT → STABLE |
| **mBridge Hybrid** 🔥 | 3 | 38 | 1 hour | ✅ | CBDC → CBDC → FIAT → STABLE |
| **DEX Liquidity** 🧪 | 2 | 35 | 10 min | ❌ | CBDC → FIAT → STABLE |
| **Atomic Swap** ⭐🧪 | 1 | 5 | 5 min | ❌ | CBDC → STABLE (direct) |

### Example: e-INR → USDC

```
Option 1: Fiat Intermediary (Regulated, 5 hours)
┌───────┐   Redeem   ┌───────┐  On-Ramp  ┌───────┐
│ e-INR │ ─────────► │  INR  │ ────────► │ USDC  │
└───────┘   0 bps    └───────┘  25 bps   └───────┘

Option 2: mBridge Hybrid (Recommended, 1 hour)
┌───────┐  mBridge  ┌───────┐  Redeem  ┌───────┐ On-Ramp ┌───────┐
│ e-CNY │ ────────► │ e-HKD │ ───────► │  HKD  │ ──────► │ USDC  │
└───────┘  13 bps   └───────┘  0 bps   └───────┘ 25 bps  └───────┘

Option 3: Atomic Swap (Experimental, 5 minutes)
┌───────┐  HTLC Swap  ┌───────┐
│ e-INR │ ──────────► │ USDC  │
└───────┘    5 bps    └───────┘
```

---

## 9️⃣ STABLECOIN → CBDC (5 Routes) ⭐ NEW

| Route | Legs | Fee (bps) | Settlement | Regulated | Path |
|-------|------|-----------|------------|-----------|------|
| **Fiat Intermediary** | 2 | 25 | 5 hours | ✅ | STABLE → FIAT → CBDC |
| **CEX Bridge** | 2 | 50 | 2 hours | ✅ | STABLE → FIAT → CBDC |
| **OTC Trade** | 1 | 15 | T+1 | ✅ | STABLE → CBDC (large trades) |
| **Liquidity Pool** 🧪 | 2 | 40 | 15 min | ❌ | STABLE → FIAT → CBDC |
| **Atomic Swap** ⭐🧪 | 1 | 5 | 5 min | ❌ | STABLE → CBDC (direct) |

### Example: USDC → e-INR

```
Option 1: Fiat Intermediary (Regulated, 5 hours)
┌───────┐  Off-Ramp  ┌───────┐   Mint   ┌───────┐
│ USDC  │ ─────────► │  INR  │ ───────► │ e-INR │
└───────┘   0 bps    └───────┘  0 bps   └───────┘

Option 2: OTC Trade (Large amounts, T+1)
┌───────┐    OTC Desk    ┌───────┐
│ USDC  │ ─────────────► │ e-INR │
└───────┘    15 bps      └───────┘

Option 3: Atomic Swap (Experimental, 5 minutes)
┌───────┐  HTLC Swap  ┌───────┐
│ USDC  │ ──────────► │ e-INR │
└───────┘    5 bps    └───────┘
```

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total Conversion Types | 9 |
| Total Routes | 35 |
| Regulated Routes | 26 |
| Experimental Routes | 6 |
| mBridge-enabled Routes | 5 |
| Zero-fee Routes | 4 |

---

## Compliance Matrix

| Rail Type | KYC Level | Travel Rule | Sanctions |
|-----------|-----------|-------------|-----------|
| Fiat | Bank KYC | No | Provider |
| CBDC Domestic | Aadhaar eKYC | No | Central Bank |
| CBDC mBridge | CB Validated | No | Both Jurisdictions |
| Stablecoin | Exchange KYC | Yes (>$3K) | Chainalysis |
| CBDC ↔ Stable | Full KYC | Yes (>$3K) | Both |

---

## Legend

- ⭐ **BEST** - Lowest cost option
- 🔥 **RECOMMENDED** - Best balance of cost/speed/reliability
- 🧪 **EXPERIMENTAL** - Future/pilot capability
- ✅ **Regulated** - Full regulatory compliance
- ❌ **Unregulated** - DeFi/DEX routes

---

## Quick Start

```bash
# Run demo
cd fx_smart_routing
python run_demo.py

# Interactive mode
python run_demo.py --interactive

# Export results
python run_demo.py --export json --output results.json
```

---

*Fintaar.ai | FX Smart Routing Engine v2.0*
