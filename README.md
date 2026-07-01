# manco-risk

[![Tests](https://github.com/mrspatbile/manco-risk/actions/workflows/tests.yml/badge.svg)](https://github.com/mrspatbile/manco-risk/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/Python-3.13-blue)](https://www.python.org/)
![Status](https://img.shields.io/badge/Status-Active%20development-2563eb)
![Domain](https://img.shields.io/badge/Domain-Fund%20Risk-334155)
[![Reg AIFMD II](https://img.shields.io/badge/Reg-AIFMD%20II-7c3aed?labelColor=555555)](https://eur-lex.europa.eu/eli/dir/2024/927/oj/eng)
[![Reg UCITS VI](https://img.shields.io/badge/Reg-UCITS%20VI-0f766e?labelColor=555555)](https://eur-lex.europa.eu/eli/dir/2024/927/oj/eng)
[![Reg ESMA LMT](https://img.shields.io/badge/Reg-ESMA%20LMT-0891b2?labelColor=555555)](https://www.esma.europa.eu/document/guidelines-liquidity-management-tools-ucits-and-open-ended-aifs)
![QuantLib](https://img.shields.io/badge/QuantLib-optional-f97316)

---

`manco-risk` is a Python analytics repository for investment fund risk, covering AIFM / ManCo workflows, regulatory methodology, portfolio risk, leverage, stress testing, derivative exposure and liquidity risk.

This repository implements the analytics layer for selected ManCo risk workflows. The current focus is on core risk modules, with reporting outputs and review interfaces planned as the analytics components mature.

> This repository is for analytical and methodological purposes. It is not a production ManCo system, regulatory reporting engine, legal interpretation tool or valuation platform.

---

## Project objective

The repository was created to implement selected fund risk, valuation and regulatory analytics topics in Python:

* AIFMD and UCITS risk concepts
* market risk analytics
* VaR and Expected Shortfall
* stress testing
* leverage exposure under gross and commitment methods
* derivative valuation inputs and Greeks-based exposure
* collateral and securities financing transaction treatment
* liquidity stress testing and LMT methodology
* reporting-oriented risk outputs

The main emphasis is on finance, modelling and risk methodology, supported by a modular Python implementation.

---

## Current status

The repository is under active development.

Implemented areas include:

* project architecture and package structure
* market-data schemas and provider abstraction
* ETL and validation foundations
* SQLite persistence layer
* Historical VaR, parametric VaR and Expected Shortfall
* VaR backtesting
* equity and fixed-income stress testing
* AIFMD and UCITS leverage analytics
* derivative pricing interface
* QuantLib-based European option pricing
* Greeks-to-exposure conversion
* leverage limit monitoring
* liquidity and LMT methodology design
* **Management reporting** (Fund Summary, Market Risk, Stress Testing, Liquidity, Leverage, Exception Summary)
* **Annex IV reporting** (Fund Identification, Asset Breakdown, Risk Measures, Leverage, Liquidity Profile)
* **PRIIPs result objects** (for UCITS reporting)
* **UCITS monitoring** (SRRI, VaR, leverage, liquidity tracking)

Planned areas include:

* liquidity taxonomy and bucket model
* time-to-liquidation analytics
* redemption and asset liquidation stress testing
* LMT inventory and calibration models
* Streamlit review interface
* export-ready report formats (Excel, PDF)

---

## Architecture

```text
src/manco_risk/
├── common/              Shared types, exceptions and utilities
├── market_data/         Market data schemas and provider interfaces
├── etl/                 Position ingestion, validation and enrichment
├── database/            SQLite persistence and query layer
├── risk/                VaR, stress, leverage, derivatives and liquidity engines
├── reporting/           Reporting outputs
└── ui/                  Streamlit review interface