
# Regulatory Variables, Reporting Fields and Data Architecture Inputs for an AIFM / ManCo Risk Platform

## 1. Purpose

This document identifies regulatory, supervisory, methodology and industry-standard inputs that have direct implications for the design of a modular Python risk platform for AIFM and ManCo workflows.

The focus is not a legal summary. The focus is system design.

The platform must support:

- domain models
- database schemas
- configuration models
- risk engines
- valuation engines
- liquidity stress testing
- leverage calculations
- fund-level methodology frameworks
- regulatory reporting modules
- investor reporting modules
- ESG and sustainability data models
- Annex IV reporting architecture
- audit trail and regulator feedback workflows

The document distinguishes:

- prescribed regulatory variables
- prescribed reporting fields
- configurable methodology settings
- internal risk limits
- derived outputs
- industry-standard valuation inputs
- supervisory expectations
- national implementation requirements

---

## 2. Design principles

### 2.1 Regulation is not one type of input

The platform should not treat all regulatory references in the same way.

Some sources prescribe exact values, formulas, templates or XML fields.

Other sources require a framework, but leave calibration to the AIFM, ManCo or fund.

Other sources, such as IPEV, are not regulation but are market-standard methodology inputs used in private capital valuation.

| Type | Example | System treatment |
|---|---|---|
| Prescribed legal classification | UCITS, AIF, MMF, ELTIF, SFDR Article 6 / 8 / 9 | Fund-level reference data |
| Prescribed formula | PRIIPs SRI, UCITS global exposure, AIFMD gross / commitment leverage | Calculation engine |
| Prescribed reporting field | Annex IV field, EMIR field, SFTR field, MiFIR transaction field | Versioned regulatory schema |
| Prescribed allowed value | Country code, instrument code, strategy code, PAI indicator ID | Regulatory reference data |
| Framework requirement | AIFMD risk management, liquidity management, LST, LMT calibration | Fund methodology configuration |
| Internal limit | Counterparty limit, concentration limit, liquidity alert threshold | Internal risk configuration |
| Industry best practice | IPEV valuation methodology | Valuation methodology and governance framework |
| Derived output | Leverage ratio, SRI, Taxonomy alignment rate, liquidity shortfall | Calculation output with lineage |

---

### 2.2 The platform needs a layered architecture

The platform should not be built as one large table of regulatory fields.

The recommended architecture is:

```text
Regulatory sources
        ↓
Variable definitions and reporting schemas
        ↓
Fund-level methodology settings
        ↓
Operational source data
        ↓
Calculation runs and derived outputs
        ↓
Regulatory field mapping
        ↓
Annex IV / SFDR / PRIIPs / EMIR / SFTR / MiFIR report generation
        ↓
Submission and regulator feedback
```

The core metadata chain should be:

```text
RegulationSource
  └── RegulatoryRequirement
        └── VariableDefinition
              ├── AllowedValueSet
              ├── ValidationRule
              ├── CalculationMethod
              └── SourceMapping
```

The core reporting chain should be:

```text
RegulatoryFiling
  ├── ReportSchemaVersion
  ├── FieldValue
  ├── RepeatedBlockValue
  ├── ValidationResult
  ├── GeneratedXML
  └── RegulatorFeedback
```

---

## 3. Regulatory and methodology source register

### 3.1 AIFMD and AIFMD II

| Source               | Article / section / annex            | Requirement                                    | System implication                                                                                                                                    |
| -------------------- | ------------------------------------ | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| Directive 2011/61/EU | Article 3                            | Registered AIFM thresholds and reporting scope | Store AIFM status, authorisation / registration status, reporting threshold category and AIFM reporting obligation.                                   |
| Directive 2011/61/EU | Article 15                           | Risk management                                | Store risk policy, risk categories, risk limits, separation of functions, monitoring controls, breach workflow and review frequency.                  |
| Directive 2011/61/EU | Article 16                           | Liquidity management                           | Store liquidity framework, redemption terms, asset liquidity methodology, liability profile, LST framework and liquidity risk controls.               |
| Directive 2011/61/EU | Article 19                           | Valuation                                      | Store valuation policy, valuation frequency, independent valuation arrangements, methodology and approval workflow.                                   |
| Directive 2011/61/EU | Article 23                           | Investor disclosure                            | Store investor disclosure fields covering investment strategy, liquidity, leverage, risk profile, valuation procedure, fees and special arrangements. |
| Directive 2011/61/EU | Article 24(1)                        | AIFM regular reporting                         | Store principal markets, principal instruments, exposures and concentrations.                                                                         |
| Directive 2011/61/EU | Article 24(2)                        | Additional AIF reporting                       | Store illiquid assets, special arrangements, risk profile, risk management systems, main asset categories and stress testing data.                    |
| Directive 2011/61/EU | Article 24(3)                        | List of AIFs managed                           | Store AIF master data and AIFM-AIF relationship.                                                                                                      |
| Directive 2011/61/EU | Article 24(4)                        | Leverage reporting                             | Store leverage level, leverage method, sources of leverage, gross and commitment exposure and reuse / rehypothecation inputs where relevant.          |
| Directive 2011/61/EU | Article 25                           | Supervisory leverage limits                    | Store leverage limits, limit source, supervisory override and breach workflow.                                                                        |
| Directive 2024/927   | Amendments to AIFMD and UCITS        | AIFMD II / UCITS VI changes                    | Store delegation fields, LMT framework, loan-originating AIF fields, depositary / custody fields and enhanced reporting readiness.                    |
| Directive 2024/927   | Liquidity risk management amendments | LMT selection and activation                   | Store selected LMTs, activation status, calibration, governance, board approval and investor disclosure.                                              |
| Directive 2024/927   | Loan origination by AIFs             | Loan-originating AIF requirements              | Store loan-originating AIF flag, loan book, borrower data, concentration, retention, leverage, open-ended / closed-ended status and risk framework.   |

Reference URLs:

* [https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32011L0061](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32011L0061)
* [https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=OJ:L_202400927](https://eur-lex.europa.eu/legal-content/EN/ALL/?uri=OJ:L_202400927)

---

### 3.2 AIFMD Level 2 and AIFMD LMT RTS

| Source                                           | Article / section / annex    | Requirement                        | System implication                                                                                                                     |
| ------------------------------------------------ | ---------------------------- | ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| Commission Delegated Regulation (EU) No 231/2013 | Articles 2-5                 | Definitions and general provisions | Store AIF, AIFM, leverage, exposure and valuation reference concepts.                                                                  |
| Commission Delegated Regulation (EU) No 231/2013 | Articles 6-11                | AUM calculation                    | Store AUM methodology, calculation date, assets under management, leverage inclusion, derivative treatment and cross-investment logic. |
| Commission Delegated Regulation (EU) No 231/2013 | Articles 40-45               | Risk management systems            | Store risk policy, risk limits, risk measurement, risk monitoring, review process and functional separation controls.                  |
| Commission Delegated Regulation (EU) No 231/2013 | Articles 46-49               | Liquidity management               | Store liquidity risk management framework, redemption policy, monitoring procedures, stress tests and special arrangements.            |
| Commission Delegated Regulation (EU) No 231/2013 | Articles 110-112 and Annexes | Leverage calculation and reporting | Store gross method, commitment method, exposure conversion, NAV denominator, netting and hedging treatment.                            |
| Commission Delegated Regulation (EU) 2026/465    | AIFMD LMT RTS                | Characteristics of LMTs for AIFMs  | Store LMT reference data for open-ended AIFs, including tool type, characteristics, calibration inputs and activation logic.           |

Reference URLs:

* [https://eur-lex.europa.eu/eli/reg_del/2013/231/oj/eng](https://eur-lex.europa.eu/eli/reg_del/2013/231/oj/eng)
* [https://eur-lex.europa.eu/eli/reg_del/2026/465/oj/eng](https://eur-lex.europa.eu/eli/reg_del/2026/465/oj/eng)

---

### 3.3 UCITS and UCITS LMT RTS

| Source                                        | Article / section / annex                   | Requirement                                                                | System implication                                                                                                                                |
| --------------------------------------------- | ------------------------------------------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Directive 2009/65/EC                          | Article 50                                  | Eligible assets                                                            | Store eligible asset classification and instrument eligibility flags.                                                                             |
| Directive 2009/65/EC                          | Article 51                                  | Risk management and global exposure                                        | Store global exposure method, derivative exposure, commitment approach, VaR approach and risk process.                                            |
| Directive 2009/65/EC                          | Article 52                                  | Issuer and counterparty limits                                             | Store issuer exposure, group exposure, deposit exposure, OTC counterparty exposure and UCITS limit engine.                                        |
| Directive 2009/65/EC                          | Article 53                                  | Index replication and concentration rules                                  | Store index replication flag, index composition and concentration limits.                                                                         |
| Directive 2009/65/EC                          | Article 56                                  | Acquisition limits                                                         | Store issuer voting and non-voting security limits where relevant.                                                                                |
| Directive 2007/16/EC                          | Eligible Assets Directive                   | Eligible asset categories                                                  | Store transferable security, money market instrument, derivative, deposit, financial index and collective investment undertaking classifications. |
| CESR / ESMA Guidelines 10-788                 | UCITS global exposure and counterparty risk | Commitment method, relative VaR, absolute VaR, backtesting, stress testing | Store confidence level, holding period, observation period, VaR method, reference portfolio and counterparty risk inputs.                         |
| Commission Delegated Regulation (EU) 2026/466 | UCITS LMT RTS                               | Characteristics of LMTs for UCITS                                          | Store LMT reference data for UCITS, including tool type, characteristics, calibration inputs and activation logic.                                |

Reference URLs:

* [https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32009L0065](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32009L0065)
* [https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32007L0016](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32007L0016)
* [https://www.esma.europa.eu/document/guidelines-risk-measurement-and-calculation-global-exposure-and-counterparty-risk-ucits](https://www.esma.europa.eu/document/guidelines-risk-measurement-and-calculation-global-exposure-and-counterparty-risk-ucits)
* [https://eur-lex.europa.eu/eli/reg_del/2026/466/oj/eng](https://eur-lex.europa.eu/eli/reg_del/2026/466/oj/eng)

---

### 3.4 ESMA LST and LMT guidance

| Source                                                                     | Article / section / annex                  | Requirement                                                    | System implication                                                                                                                                                |
| -------------------------------------------------------------------------- | ------------------------------------------ | -------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| ESMA Guidelines on Liquidity Stress Testing in UCITS and AIFs              | Guidelines 1-16                            | LST design, governance and application                         | Store LST programme, frequency, scenario type, historical / hypothetical shocks, reverse stress tests, redemption shocks, asset liquidation model and governance. |
| ESMA Guidelines on Liquidity Management Tools of UCITS and open-ended AIFs | ESMA34-671404336-1364                      | Selection and calibration of LMTs                              | Store selected LMTs, calibration, governance, fairness controls, operational readiness, activation / deactivation logic and evidence.                             |
| CSSF Circular 26/910                                                       | Luxembourg adoption of ESMA LMT Guidelines | Applies ESMA LMT Guidelines in Luxembourg supervisory practice | Store Luxembourg LMT compliance status, selected tools, eDesk procedure references, CSSF communication records and transition deadlines.                          |

Reference URLs:

* [https://www.esma.europa.eu/sites/default/files/library/esma34-39-897_guidelines_on_liquidity_stress_testing_in_ucits_and_aifs_en.pdf](https://www.esma.europa.eu/sites/default/files/library/esma34-39-897_guidelines_on_liquidity_stress_testing_in_ucits_and_aifs_en.pdf)
* [https://www.esma.europa.eu/document/guidelines-liquidity-management-tools-ucits-and-open-ended-aifs](https://www.esma.europa.eu/document/guidelines-liquidity-management-tools-ucits-and-open-ended-aifs)
* [https://www.esma.europa.eu/sites/default/files/2026-03/ESMA34-671404336-1364_Guidelines_on_liquidity_management_tools_of_UCITS_and_open-ended_AIFs.pdf](https://www.esma.europa.eu/sites/default/files/2026-03/ESMA34-671404336-1364_Guidelines_on_liquidity_management_tools_of_UCITS_and_open-ended_AIFs.pdf)
* [https://www.cssf.lu/en/Document/circular-cssf-26-910/](https://www.cssf.lu/en/Document/circular-cssf-26-910/)
* [https://www.cssf.lu/en/2026/03/communication-to-the-investment-fund-industry/](https://www.cssf.lu/en/2026/03/communication-to-the-investment-fund-industry/)
* [https://www.cssf.lu/en/2026/04/communication-to-the-investment-fund-industry-2/](https://www.cssf.lu/en/2026/04/communication-to-the-investment-fund-industry-2/)

---

### 3.5 Annex IV and AIFMD reporting technical guidance

| Source                                           | Article / section / annex                                    | Requirement                                      | System implication                                                                                                    |
| ------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| Directive 2011/61/EU                             | Article 24                                                   | Legal reporting duty                             | Store reporting obligation, reporting level, reporting frequency and filing scope.                                    |
| Commission Delegated Regulation (EU) No 231/2013 | Reporting and leverage provisions                            | More detailed reporting and leverage calculation | Store reportable exposure, leverage and risk data.                                                                    |
| ESMA AIFMD Reporting Technical Guidance          | XML schema, IT guidance, validation rules, data point tables | Annex IV reporting schema                        | Store field definitions, XML tags, data types, mandatory status, conditionality, validation rules and allowed values. |
| CSSF AIFM Reporting Technical Guidance           | Luxembourg reporting instructions                            | Local file, identifier and submission controls   | Store CSSF national codes, reporting member state, file structure, submission status and feedback.                    |

Reference URLs:

* [https://www.esma.europa.eu/document/aifmd-reporting-it-technical-guidance-rev-6-updated](https://www.esma.europa.eu/document/aifmd-reporting-it-technical-guidance-rev-6-updated)
* [https://www.cssf.lu/wp-content/uploads/AIFM_Reporting_Technical_Guidance.pdf](https://www.cssf.lu/wp-content/uploads/AIFM_Reporting_Technical_Guidance.pdf)

---

### 3.6 PRIIPs

| Source                                         | Article / section / annex | Requirement                              | System implication                                                                                                   |
| ---------------------------------------------- | ------------------------- | ---------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| Regulation (EU) No 1286/2014                   | Article 8                 | KID content                              | Store product identity, risk indicator, performance scenarios, costs, recommended holding period and complaint data. |
| Commission Delegated Regulation (EU) 2017/653  | Annex II                  | Market risk measure                      | Store MRM class, VaR-equivalent volatility, price history, product category and calculation assumptions.             |
| Commission Delegated Regulation (EU) 2017/653  | Annex III                 | Credit risk measure                      | Store CRM class, obligor / guarantor credit quality, maturity and credit risk inputs.                                |
| Commission Delegated Regulation (EU) 2017/653  | Annex IV / V              | Performance scenarios                    | Store stress, unfavourable, moderate and favourable scenario outputs and methodology inputs.                         |
| Commission Delegated Regulation (EU) 2017/653  | Annex VI / VII            | Cost calculation and presentation        | Store one-off costs, recurring costs, incidental costs, transaction costs, RIY and cost table outputs.               |
| Commission Delegated Regulation (EU) 2021/2268 | RTS amendments            | Updated PRIIPs methodology and templates | Store PRIIPs methodology version and effective date.                                                                 |

Reference URLs:

* [https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014R1286](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014R1286)
* [https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32017R0653](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32017R0653)
* [https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32021R2268](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32021R2268)

---

### 3.7 SFDR

| Source                                         | Article / section / annex | Requirement                            | System implication                                                                                   |
| ---------------------------------------------- | ------------------------- | -------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Regulation (EU) 2019/2088                      | Article 3                 | Sustainability risk policy             | Store sustainability risk integration at entity level.                                               |
| Regulation (EU) 2019/2088                      | Article 4                 | PAI statement                          | Store PAI considered flag, entity-level PAI reporting and explain / comply logic.                    |
| Regulation (EU) 2019/2088                      | Article 6                 | Article 6 product disclosure           | Store sustainability risk relevance and likely impact.                                               |
| Regulation (EU) 2019/2088                      | Article 8                 | Article 8 product classification       | Store environmental / social characteristics and good governance checks.                             |
| Regulation (EU) 2019/2088                      | Article 9                 | Article 9 product classification       | Store sustainable investment objective and benchmark relationship where relevant.                    |
| Regulation (EU) 2019/2088                      | Articles 10 and 11        | Website and periodic disclosures       | Store website disclosure fields, periodic report fields and template status.                         |
| Commission Delegated Regulation (EU) 2022/1288 | Annex I                   | PAI indicators                         | Store PAI indicator reference data, mandatory / optional flag, metric formula, unit and data source. |
| Commission Delegated Regulation (EU) 2022/1288 | Product templates         | Pre-contractual and periodic templates | Store template fields for Article 8 and Article 9 products.                                          |

Reference URLs:

* [https://eur-lex.europa.eu/eli/reg/2019/2088/oj/eng](https://eur-lex.europa.eu/eli/reg/2019/2088/oj/eng)
* [https://eur-lex.europa.eu/eli/reg_del/2022/1288/oj/eng](https://eur-lex.europa.eu/eli/reg_del/2022/1288/oj/eng)

---

### 3.8 Taxonomy Regulation

| Source                              | Article / section / annex | Requirement                                                  | System implication                                                                                    |
| ----------------------------------- | ------------------------- | ------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------- |
| Regulation (EU) 2020/852            | Article 3                 | Conditions for environmentally sustainable economic activity | Store substantial contribution, DNSH, minimum safeguards and technical screening criteria pass flags. |
| Regulation (EU) 2020/852            | Article 9                 | Six environmental objectives                                 | Store environmental objective reference data.                                                         |
| Regulation (EU) 2020/852            | Article 17                | DNSH                                                         | Store DNSH checks and evidence.                                                                       |
| Regulation (EU) 2020/852            | Article 18                | Minimum safeguards                                           | Store safeguards checks and evidence.                                                                 |
| Regulation (EU) 2020/852            | Article 8                 | Disclosure obligation                                        | Store taxonomy eligibility and alignment metrics.                                                     |
| Delegated Regulation (EU) 2021/2178 | Annexes                   | Article 8 KPI templates                                      | Store turnover, CapEx, OpEx, eligible and aligned KPIs, issuer source and portfolio aggregation.      |

Reference URLs:

* [https://eur-lex.europa.eu/eli/reg/2020/852/oj/eng](https://eur-lex.europa.eu/eli/reg/2020/852/oj/eng)
* [https://eur-lex.europa.eu/eli/reg_del/2021/2178/oj/eng](https://eur-lex.europa.eu/eli/reg_del/2021/2178/oj/eng)

---

### 3.9 EMIR

| Source                                            | Article / section / annex | Requirement                         | System implication                                                                                       |
| ------------------------------------------------- | ------------------------- | ----------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Regulation (EU) No 648/2012                       | Article 4                 | Clearing obligation                 | Store clearing status, CCP, clearing member and product eligibility.                                     |
| Regulation (EU) No 648/2012                       | Article 9                 | Derivative reporting                | Store derivative report fields, UTI, counterparty data, common data, valuation and lifecycle event data. |
| Regulation (EU) No 648/2012                       | Article 11                | Risk mitigation for OTC derivatives | Store collateral, margin, valuation, reconciliation, dispute and portfolio compression data.             |
| Commission Delegated Regulation (EU) 2022/1855    | Annex tables              | EMIR Refit reporting fields         | Store field catalogue, validation rules and allowed values.                                              |
| Commission Implementing Regulation (EU) 2022/1860 | Reporting format          | EMIR reporting format and standards | Store reporting format, XML / ISO format and submission rules.                                           |

Reference URLs:

* [https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32012R0648](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32012R0648)
* [https://eur-lex.europa.eu/eli/reg_del/2022/1855/oj/eng](https://eur-lex.europa.eu/eli/reg_del/2022/1855/oj/eng)
* [https://eur-lex.europa.eu/eli/reg_impl/2022/1860/oj/eng](https://eur-lex.europa.eu/eli/reg_impl/2022/1860/oj/eng)

---

### 3.10 SFTR

| Source                                           | Article / section / annex | Requirement               | System implication                                                                    |
| ------------------------------------------------ | ------------------------- | ------------------------- | ------------------------------------------------------------------------------------- |
| Regulation (EU) 2015/2365                        | Article 4                 | SFT reporting             | Store SFT type, counterparty, collateral, maturity, reuse, margin and valuation data. |
| Regulation (EU) 2015/2365                        | Article 15                | Reuse conditions          | Store collateral reuse flag, consent status, risk disclosure and reuse value.         |
| Commission Delegated Regulation (EU) 2019/356    | Annex tables              | SFTR reporting fields     | Store SFT reporting schema, allowed values and validation rules.                      |
| Commission Implementing Regulation (EU) 2019/363 | Reporting format          | SFTR format and frequency | Store reporting format and lifecycle action type.                                     |

Reference URLs:

* [https://eur-lex.europa.eu/eli/reg/2015/2365/oj/eng](https://eur-lex.europa.eu/eli/reg/2015/2365/oj/eng)
* [https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019R0356](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019R0356)
* [https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019R0363](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32019R0363)

---

### 3.11 MMFR

| Source                          | Article / section / annex | Requirement              | System implication                                                                                   |
| ------------------------------- | ------------------------- | ------------------------ | ---------------------------------------------------------------------------------------------------- |
| Regulation (EU) 2017/1131       | Articles 9-17             | Eligible assets          | Store MMF eligible asset type, maturity, credit quality, securitisation / ABCP flag and issuer data. |
| Regulation (EU) 2017/1131       | Articles 24-28            | Portfolio rules          | Store daily liquidity, weekly liquidity, WAM, WAL, issuer limits and concentration limits.           |
| Regulation (EU) 2017/1131       | Article 28                | Stress testing           | Store MMF stress testing scenarios and results.                                                      |
| Regulation (EU) 2017/1131       | Article 37                | Reporting                | Store MMF reporting fields and frequency.                                                            |
| ESMA MMF stress test guidelines | Current annual updates    | Common stress parameters | Store dated ESMA stress parameter sets as reference data.                                            |

Reference URLs:

* [https://eur-lex.europa.eu/eli/reg/2017/1131/oj/eng](https://eur-lex.europa.eu/eli/reg/2017/1131/oj/eng)
* [https://www.esma.europa.eu/sites/default/files/2026-01/ESMA50-481369926-30585_Final_Report_-_Guidelines_on_stress_test_scenarios_under_the_MMF_Regulation.pdf](https://www.esma.europa.eu/sites/default/files/2026-01/ESMA50-481369926-30585_Final_Report_-_Guidelines_on_stress_test_scenarios_under_the_MMF_Regulation.pdf)

---

### 3.12 Benchmark Regulation

| Source                    | Article / section / annex | Requirement                              | System implication                                                                                                  |
| ------------------------- | ------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Regulation (EU) 2016/1011 | Article 28(2)             | Written benchmark fallback plan          | Store benchmark ID, benchmark administrator, use case, fallback benchmark, cessation plan and material change plan. |
| Regulation (EU) 2016/1011 | Benchmark use provisions  | Benchmark administrator and use controls | Store benchmark permission, supervised user status and benchmark reference data.                                    |

Reference URL:

* [https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R1011](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32016R1011)

---

### 3.13 CRR / EBA frameworks

| Source                        | Article / section / annex                                 | Requirement                      | System implication                                                                                                           |
| ----------------------------- | --------------------------------------------------------- | -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Regulation (EU) No 575/2013   | Counterparty, collateral and exposure provisions          | Exposure and collateral concepts | Store exposure class, counterparty credit exposure, collateral type, eligible collateral, CRM recognition and concentration. |
| Regulation (EU) 2024/1623     | CRR III amendments                                        | Updated prudential framework     | Store versioned prudential treatment where the platform feeds bank-facing or collateral risk outputs.                        |
| EBA guidelines where relevant | Counterparty, collateral, concentration, risk methodology | Supervisory methodology inputs   | Use where the fund platform interfaces with bank-style risk engines or prudential reporting.                                 |

Reference URLs:

* [https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32013R0575](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32013R0575)
* [https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1623](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1623)

---

### 3.14 MiFID II / MiFIR

| Source                      | Article / section / annex | Requirement                            | System implication                                                                                                                   |
| --------------------------- | ------------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Directive 2014/65/EU        | Article 16(3)             | Product governance                     | Store target market, product approval, review frequency and distribution strategy.                                                   |
| Directive 2014/65/EU        | Articles 24-25            | Costs, suitability and appropriateness | Store client category, suitability inputs, costs and charges and target-market matching.                                             |
| Regulation (EU) No 600/2014 | Article 26                | Transaction reporting                  | Store transaction-reporting obligation and field mapping.                                                                            |
| RTS 22                      | Annex I Table 2           | Transaction reporting fields           | Store buyer, seller, decision maker, trader, instrument, price, quantity, venue, short-sale flag and commodity derivative indicator. |

Reference URLs:

* [https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014L0065](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014L0065)
* [https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014R0600](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32014R0600)
* [https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32017R0590](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32017R0590)

---

### 3.15 CSDR

| Source                      | Article / section / annex | Requirement           | System implication                                                                                                            |
| --------------------------- | ------------------------- | --------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| Regulation (EU) No 909/2014 | Articles 6-7              | Settlement discipline | Store intended settlement date, actual settlement date, fail reason, settlement status, penalty rate and cash penalty amount. |

Reference URL:

* [https://eur-lex.europa.eu/eli/reg/2014/909/oj/eng](https://eur-lex.europa.eu/eli/reg/2014/909/oj/eng)

---

### 3.16 Securitisation Regulation

| Source                    | Article / section / annex | Requirement                     | System implication                                                                                  |
| ------------------------- | ------------------------- | ------------------------------- | --------------------------------------------------------------------------------------------------- |
| Regulation (EU) 2017/2402 | Article 5                 | Investor due diligence          | Store due-diligence checks, exposure data, stress tests and monitoring evidence.                    |
| Regulation (EU) 2017/2402 | Articles 6-7              | Risk retention and transparency | Store originator, sponsor, SSPE, retention percentage, transparency source and reporting documents. |
| Regulation (EU) 2017/2402 | Article 18                | STS designation                 | Store STS flag, notification, verification and classification evidence.                             |

Reference URL:

* [https://eur-lex.europa.eu/eli/reg/2017/2402/oj/eng](https://eur-lex.europa.eu/eli/reg/2017/2402/oj/eng)

---

### 3.17 ELTIF

| Source                   | Article / section / annex | Requirement                            | System implication                                                                                                    |
| ------------------------ | ------------------------- | -------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Regulation (EU) 2015/760 | ELTIF framework           | ELTIF eligibility and investment rules | Store ELTIF flag, eligible investment assets, portfolio composition, borrowing, diversification and redemption rules. |
| Regulation (EU) 2023/606 | ELTIF 2.0 amendments      | Revised ELTIF rules                    | Store amended eligibility, liquidity, redemption, investor and portfolio composition fields.                          |

Reference URLs:

* [https://eur-lex.europa.eu/eli/reg/2015/760/oj/eng](https://eur-lex.europa.eu/eli/reg/2015/760/oj/eng)
* [https://eur-lex.europa.eu/eli/reg/2023/606/oj/eng](https://eur-lex.europa.eu/eli/reg/2023/606/oj/eng)

---

### 3.18 EuVECA and EuSEF

| Source                      | Article / section / annex | Requirement                                           | System implication                                                                                                        |
| --------------------------- | ------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| Regulation (EU) No 345/2013 | EuVECA framework          | EuVECA label and qualifying investments               | Store EuVECA flag, qualifying portfolio undertaking, eligible investment type and qualifying investment percentage.       |
| Regulation (EU) No 346/2013 | EuSEF framework           | EuSEF label and social entrepreneurship fund criteria | Store EuSEF flag, qualifying portfolio undertaking, social objective classification and qualifying investment percentage. |

Reference URLs:

* [https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32013R0345](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32013R0345)
* [https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32013R0346](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32013R0346)

---

### 3.19 AML / KYC

| Source                          | Article / section / annex                       | Requirement                                      | System implication                                                                                                                                                                    |
| ------------------------------- | ----------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Directive (EU) 2015/849         | Customer due diligence and beneficial ownership | AML / CFT data model                             | Store investor identity, beneficial owner, ownership / control percentage, PEP flag, sanctions result, source of funds, source of wealth, AML risk rating and enhanced due diligence. |
| Luxembourg AML / CSSF framework | Local AML controls                              | Fund, investor and counterparty operational data | Store AML risk scoring, periodic review date, screening result, remediation and evidence.                                                                                             |

Reference URL:

* [https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32015L0849](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32015L0849)

---

### 3.20 Luxembourg and CSSF implementation

| Source                                 | Article / section / annex               | Requirement                                             | System implication                                                                                                     |
| -------------------------------------- | --------------------------------------- | ------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Luxembourg Law of 12 July 2013         | AIFM law                                | AIFMD implementation                                    | Store Luxembourg AIFM authorisation, reporting, risk management, delegation, marketing and CSSF filing fields.         |
| Luxembourg Law of 17 December 2010     | UCI law                                 | UCITS and UCI implementation                            | Store Luxembourg UCITS / UCI status, global exposure, risk process and local filing requirements.                      |
| Luxembourg Law of 3 March 2026         | Transposition of Directive 2024/927     | AIFMD II / UCITS VI Luxembourg implementation           | Store LMT selection, activation, calibration, procedure and amended Luxembourg legal references.                       |
| CSSF Circular 18/698                   | IFM organisation                        | Governance, risk, delegation, AML and internal controls | Store conducting officers, central administration, control functions, delegation oversight and risk governance fields. |
| CSSF Circular 26/910                   | ESMA LMT Guidelines                     | LMT selection and calibration supervisory practice      | Store LMT procedure, compliance evidence and CSSF eDesk process references.                                            |
| CSSF AIFM Reporting Technical Guidance | Annex IV Luxembourg reporting           | XML submission controls                                 | Store reporting member state, national codes, file naming, XML structure, ZIP submission and feedback.                 |
| CSSF Circular 24/856                   | NAV errors and investment-rule breaches | Operational breach workflow                             | Store NAV error type, breach type, materiality, correction, compensation, CSSF notification and remediation status.    |

Reference URLs:

* [https://www.cssf.lu/wp-content/uploads/L_120713_AIFM_eng.pdf](https://www.cssf.lu/wp-content/uploads/L_120713_AIFM_eng.pdf)
* [https://www.cssf.lu/wp-content/uploads/L_171210_UCI.pdf](https://www.cssf.lu/wp-content/uploads/L_171210_UCI.pdf)
* [https://www.cssf.lu/en/2026/03/communication-to-the-investment-fund-industry/](https://www.cssf.lu/en/2026/03/communication-to-the-investment-fund-industry/)
* [https://www.cssf.lu/wp-content/uploads/cssf26_910eng.pdf](https://www.cssf.lu/wp-content/uploads/cssf26_910eng.pdf)
* [https://www.cssf.lu/wp-content/uploads/cssf18_698eng.pdf](https://www.cssf.lu/wp-content/uploads/cssf18_698eng.pdf)
* [https://www.cssf.lu/wp-content/uploads/AIFM_Reporting_Technical_Guidance.pdf](https://www.cssf.lu/wp-content/uploads/AIFM_Reporting_Technical_Guidance.pdf)
* [https://www.cssf.lu/en/Document/circular-cssf-24-856/](https://www.cssf.lu/en/Document/circular-cssf-24-856/)

---

### 3.21 IPEV valuation guidelines

| Source                    | Article / section / annex                         | Requirement                            | System implication                                                                                                                                                                                   |
| ------------------------- | ------------------------------------------------- | -------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| IPEV Valuation Guidelines | Fair value valuation guidance for private capital | Industry best practice, not regulation | Store IPEV version, valuation technique, calibration, comparable set, multiple, DCF inputs, scenario probabilities, capital structure method, adjustments, approval workflow and valuation evidence. |

Reference URL:

* [https://www.privateequityvaluation.com/Valuation-Guidelines](https://www.privateequityvaluation.com/Valuation-Guidelines)

Classification:

| Source                    | Classification                            | Notes                                                                                                                                                                       |
| ------------------------- | ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| IPEV Valuation Guidelines | Industry best practice / fund methodology | Not Level 1 legislation, not Level 2 regulation, not ESMA guideline, not CSSF rule. It is relevant because it is widely used for fair-value methodology in private capital. |

---

## 4. Regulatory authority classification

| Variable family             | Authority classification                                                   | System treatment                            |
| --------------------------- | -------------------------------------------------------------------------- | ------------------------------------------- |
| AIFMD risk management       | Level 1 directive, Level 2 delegated regulation, CSSF where Luxembourg     | Fund methodology plus risk framework        |
| AIFMD liquidity management  | Level 1 directive, Level 2 delegated regulation, ESMA LST guideline        | Fund liquidity methodology                  |
| AIFMD leverage              | Level 1 directive, Level 2 delegated regulation                            | Calculation engine                          |
| Annex IV fields             | Level 1 directive plus ESMA technical guidance plus CSSF local guidance    | Reporting schema                            |
| AIFMD II / UCITS VI LMTs    | Level 1 directive, 2026 LMT RTS, ESMA LMT Guidelines, CSSF Circular 26/910 | LMT framework and regulatory reference data |
| UCITS investment limits     | Level 1 directive plus ESMA / CESR guideline                               | Rule engine                                 |
| PRIIPs SRI and scenarios    | Level 1 regulation plus Level 2 RTS                                        | Formula engine                              |
| SFDR classification and PAI | Level 1 regulation plus Level 2 RTS                                        | ESG reporting schema                        |
| Taxonomy alignment          | Level 1 regulation plus delegated acts                                     | ESG data engine and disclosure outputs      |
| EMIR reporting              | Level 1 regulation plus RTS / ITS                                          | Trade-reporting schema                      |
| SFTR reporting              | Level 1 regulation plus RTS / ITS                                          | SFT reporting schema                        |
| MMFR WAM / WAL / liquidity  | Level 1 regulation plus ESMA stress parameters                             | MMF rule engine                             |
| Benchmark fallback          | Level 1 regulation                                                         | Benchmark reference and fallback plan       |
| CSDR settlement discipline  | Level 1 regulation                                                         | Settlement workflow and penalty calculation |
| IPEV valuation variables    | Industry best practice / fund methodology                                  | Private asset valuation framework           |
| Internal risk limits        | Internal risk limit                                                        | Configurable risk rules                     |
| Derived outputs             | Derived output                                                             | Calculation snapshots                       |

---

## 5. System variable inventory

| Variable                              | Meaning                                                                                                                                                        | Source                                   | Applies to                    | Prescribed or configurable                               | Data treatment                               |
| ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- | ----------------------------- | -------------------------------------------------------- | -------------------------------------------- |
| `fund_regime`                         | AIF, UCITS, MMF, ELTIF, EuVECA, EuSEF                                                                                                                          | AIFMD, UCITS, MMFR, ELTIF, EuVECA, EuSEF | Fund                          | Prescribed classification                                | Database field and regulatory reference data |
| `aifm_authorisation_status`           | Authorised or registered AIFM                                                                                                                                  | AIFMD                                    | AIFM                          | Prescribed classification                                | Database field                               |
| `open_ended_flag`                     | Open-ended or closed-ended                                                                                                                                     | AIFMD II, UCITS VI, fund documents       | Fund                          | Legal / fund classification                              | Database field                               |
| `loan_originating_aif_flag`           | AIF originates loans                                                                                                                                           | AIFMD II                                 | AIF                           | Prescribed classification                                | Database field                               |
| `reporting_frequency`                 | Annual, half-yearly, quarterly or other required frequency                                                                                                     | AIFMD Annex IV, MMFR, other regimes      | Filing                        | Prescribed by regime and thresholds                      | Reporting configuration                      |
| `aum`                                 | Assets under management                                                                                                                                        | AIFMD Level 2                            | AIFM / fund                   | Derived output                                           | Calculation output and filing field          |
| `nav`                                 | Net asset value                                                                                                                                                | AIFMD, UCITS, PRIIPs, reporting          | Fund / share class            | Derived / accounting output                              | Database snapshot                            |
| `gross_asset_value`                   | Gross asset value                                                                                                                                              | AIFMD reporting                          | Fund                          | Derived output                                           | Calculation output                           |
| `leverage_method`                     | Gross, commitment, UCITS commitment, VaR                                                                                                                       | AIFMD Level 2, UCITS guidelines          | AIF / UCITS                   | Prescribed method choices                                | Methodology setting                          |
| `gross_leverage_ratio`                | Gross exposure divided by NAV                                                                                                                                  | AIFMD Level 2                            | AIF                           | Derived output                                           | Calculation output                           |
| `commitment_leverage_ratio`           | Commitment exposure divided by NAV                                                                                                                             | AIFMD Level 2                            | AIF                           | Derived output                                           | Calculation output                           |
| `global_exposure_method`              | Commitment, relative VaR or absolute VaR                                                                                                                       | UCITS                                    | UCITS                         | Prescribed choices                                       | Fund-level setting                           |
| `global_exposure_value`               | Derivative global exposure                                                                                                                                     | UCITS                                    | UCITS                         | Derived output                                           | Calculation output                           |
| `var_confidence_level`                | VaR confidence level                                                                                                                                           | UCITS CESR / ESMA                        | UCITS VaR funds               | Methodology parameter within supervisory expectations    | Configuration parameter                      |
| `var_holding_period_days`             | VaR holding period                                                                                                                                             | UCITS CESR / ESMA                        | UCITS VaR funds               | Methodology parameter                                    | Configuration parameter                      |
| `var_observation_period_days`         | VaR lookback period                                                                                                                                            | UCITS CESR / ESMA, PRIIPs RTS            | UCITS / PRIIPs                | Prescribed or methodology-based depending on calculation | Configuration parameter                      |
| `lst_frequency`                       | Liquidity stress testing frequency                                                                                                                             | AIFMD, ESMA LST                          | AIF / UCITS                   | Framework required, value fund-defined                   | Fund methodology setting                     |
| `lst_scenario_type`                   | Historical, hypothetical, combined, reverse                                                                                                                    | ESMA LST                                 | AIF / UCITS                   | Fund methodology                                         | Scenario configuration                       |
| `redemption_frequency`                | Frequency of dealing / redemption                                                                                                                              | Fund documents, liquidity rules          | Fund / share class            | Fund-level setting                                       | Database field                               |
| `redemption_notice_period_days`       | Notice period                                                                                                                                                  | Fund documents                           | Fund / share class / investor | Fund-level or investor-level setting                     | Database field                               |
| `lockup_period_days`                  | Lock-up period                                                                                                                                                 | Fund documents                           | Fund / share class / investor | Fund-level or investor-level setting                     | Database field                               |
| `liquidity_bucket_scheme`             | Bucket definitions for liquidity profile                                                                                                                       | ESMA LST, Annex IV reporting             | Fund                          | Framework required, fund-defined                         | Methodology setting                          |
| `portfolio_liquidity_bucket`          | Bucket for asset liquidity                                                                                                                                     | ESMA LST, Annex IV                       | Position / aggregate          | Methodology-derived                                      | Calculation output                           |
| `investor_redemption_bucket`          | Investor liquidity bucket                                                                                                                                      | Annex IV, liquidity framework            | Investor aggregate            | Derived output                                           | Repeated reporting block                     |
| `time_to_liquidate_days`              | Estimated time to liquidate position                                                                                                                           | ESMA LST                                 | Position / portfolio          | Derived from methodology                                 | Calculation output                           |
| `lmt_type`                            | Redemption gate, suspension, swing pricing, anti-dilution levy, redemption fee, side pocket, extension of notice period, in-kind redemption, other listed tool | Directive 2024/927, 2026 LMT RTS         | Open-ended AIF / UCITS        | Prescribed reference list                                | Regulatory reference data                    |
| `lmt_selected_flag`                   | Whether the LMT is selected for the fund                                                                                                                       | AIFMD II / UCITS VI, CSSF LMT procedure  | Fund                          | Required selection, fund-specific                        | Fund-level setting                           |
| `lmt_activation_status`               | Available, active, deactivated, suspended                                                                                                                      | ESMA LMT Guidelines                      | Fund                          | Operational state                                        | Database field and event history             |
| `lmt_activation_threshold`            | Trigger for activation                                                                                                                                         | ESMA LMT Guidelines                      | Fund                          | Fund methodology                                         | Configuration parameter                      |
| `swing_pricing_factor`                | NAV swing factor                                                                                                                                               | LMT framework                            | Fund / share class            | Methodology parameter                                    | Configuration and calculation output         |
| `anti_dilution_levy_rate`             | Levy applied to protect remaining investors                                                                                                                    | LMT framework                            | Fund / share class            | Methodology parameter                                    | Configuration and calculation output         |
| `redemption_gate_threshold`           | Threshold for redemption gate                                                                                                                                  | LMT framework                            | Fund / share class            | Methodology parameter                                    | Configuration parameter                      |
| `issuer_exposure_pct`                 | Exposure to issuer as % NAV                                                                                                                                    | UCITS, MMFR, internal AIF risk policy    | Fund / issuer                 | Prescribed for UCITS / configurable for AIFs             | Calculation output                           |
| `counterparty_exposure_pct`           | Exposure to counterparty as % NAV                                                                                                                              | UCITS, EMIR, internal policy             | Fund / counterparty           | Prescribed or internal depending on regime               | Calculation output                           |
| `collateral_type`                     | Type of collateral                                                                                                                                             | EMIR, SFTR, UCITS, internal policy       | Collateral                    | Reporting field                                          | Regulatory reference data                    |
| `collateral_value`                    | Market value of collateral                                                                                                                                     | EMIR, SFTR                               | Collateral                    | Reporting / derived                                      | Database field                               |
| `collateral_haircut`                  | Valuation haircut                                                                                                                                              | Collateral policy, EMIR / UCITS context  | Collateral                    | Configurable unless prescribed by specific policy        | Configuration parameter                      |
| `collateral_reuse_flag`               | Whether collateral is reused                                                                                                                                   | SFTR                                     | Collateral / SFT              | Prescribed reporting field                               | Database and reporting field                 |
| `clearing_status`                     | Cleared, bilateral, exchange-traded                                                                                                                            | EMIR                                     | Derivative                    | Reporting field                                          | Database field                               |
| `ccp_lei`                             | CCP identifier                                                                                                                                                 | EMIR                                     | Derivative                    | Reporting field                                          | Reference data                               |
| `margin_type`                         | Initial or variation margin                                                                                                                                    | EMIR                                     | Derivative / collateral       | Reporting field                                          | Database field                               |
| `sft_type`                            | Repo, reverse repo, securities lending, securities borrowing, buy-sell back, margin lending                                                                    | SFTR                                     | SFT                           | Prescribed enum                                          | Regulatory reference data                    |
| `sftr_action_type`                    | New, modification, correction, termination, collateral update                                                                                                  | SFTR RTS / ITS                           | SFT report                    | Prescribed enum                                          | Reporting field                              |
| `emir_action_type`                    | Trade lifecycle event type                                                                                                                                     | EMIR RTS / ITS                           | Derivative report             | Prescribed enum                                          | Reporting field                              |
| `priips_sri`                          | Summary risk indicator                                                                                                                                         | PRIIPs RTS                               | PRIIP / share class           | Derived from prescribed method                           | Calculation output                           |
| `priips_mrm_class`                    | Market risk measure class                                                                                                                                      | PRIIPs RTS                               | PRIIP                         | Derived output                                           | Calculation output                           |
| `priips_crm_class`                    | Credit risk measure class                                                                                                                                      | PRIIPs RTS                               | PRIIP                         | Derived output                                           | Calculation output                           |
| `performance_scenario_type`           | Stress, unfavourable, moderate, favourable                                                                                                                     | PRIIPs RTS                               | PRIIP                         | Prescribed scenario type                                 | Regulatory reference data                    |
| `recommended_holding_period`          | PRIIPs recommended holding period                                                                                                                              | PRIIPs Regulation / RTS                  | PRIIP                         | Product setting                                          | Product field                                |
| `summary_cost_indicator`              | Aggregated cost output                                                                                                                                         | PRIIPs RTS                               | PRIIP                         | Derived output                                           | Calculation output                           |
| `sfdr_article_classification`         | Article 6, 8 or 9                                                                                                                                              | SFDR                                     | Fund / product                | Fund disclosure classification                           | Fund-level setting                           |
| `pai_indicator_id`                    | PAI indicator code                                                                                                                                             | SFDR RTS                                 | Entity / fund                 | Prescribed reference data                                | Regulatory reference data                    |
| `pai_indicator_value`                 | PAI metric value                                                                                                                                               | SFDR RTS                                 | Issuer / portfolio            | Derived or external data                                 | ESG metric field                             |
| `sustainable_investment_flag`         | Investment counted as sustainable                                                                                                                              | SFDR                                     | Position / issuer / fund      | Methodology output                                       | ESG calculation output                       |
| `taxonomy_environmental_objective`    | Taxonomy objective                                                                                                                                             | Taxonomy Regulation                      | Issuer / activity             | Prescribed reference data                                | Regulatory reference data                    |
| `substantial_contribution_flag`       | Substantial contribution test                                                                                                                                  | Taxonomy Regulation                      | Activity / issuer             | Methodology input / output                               | ESG data field                               |
| `dnsh_pass_flag`                      | Do no significant harm test                                                                                                                                    | Taxonomy Regulation, SFDR RTS            | Issuer / activity             | Methodology input / output                               | ESG data field                               |
| `minimum_safeguards_pass_flag`        | Minimum safeguards test                                                                                                                                        | Taxonomy Regulation                      | Issuer / activity             | Methodology input / output                               | ESG data field                               |
| `taxonomy_eligible_pct`               | Eligible exposure percentage                                                                                                                                   | Taxonomy Article 8                       | Fund / issuer                 | Derived output                                           | ESG calculation output                       |
| `taxonomy_aligned_pct`                | Aligned exposure percentage                                                                                                                                    | Taxonomy Article 8                       | Fund / issuer                 | Derived output                                           | ESG calculation output                       |
| `benchmark_id`                        | Benchmark identifier                                                                                                                                           | Benchmark Regulation, PRIIPs, SFDR       | Fund / share class            | Reporting / reference field                              | Reference data                               |
| `benchmark_fallback_id`               | Replacement benchmark                                                                                                                                          | Benchmark Regulation                     | Fund / share class            | Fund methodology                                         | Fund-level setting                           |
| `settlement_fail_flag`                | Failed settlement status                                                                                                                                       | CSDR                                     | Trade                         | Derived / operational                                    | Database field                               |
| `cash_penalty_amount`                 | CSDR cash penalty                                                                                                                                              | CSDR                                     | Trade                         | Derived output                                           | Calculation output                           |
| `sts_flag`                            | STS securitisation status                                                                                                                                      | Securitisation Regulation                | Instrument                    | Prescribed classification                                | Instrument field                             |
| `risk_retention_pct`                  | Retained net economic interest                                                                                                                                 | Securitisation Regulation                | Securitisation exposure       | Prescribed / reported                                    | Instrument / exposure field                  |
| `target_market`                       | Product governance target market                                                                                                                               | MiFID II                                 | Product / share class         | Framework required, manufacturer-defined                 | Product governance field                     |
| `client_category`                     | Retail, professional, eligible counterparty                                                                                                                    | MiFID II                                 | Investor / client             | Prescribed enum                                          | Investor field                               |
| `beneficial_owner_id`                 | UBO identity                                                                                                                                                   | AMLD / CSSF AML                          | Investor / counterparty       | Mandatory data                                           | Restricted database field                    |
| `aml_risk_rating`                     | AML risk score                                                                                                                                                 | AMLD / CSSF AML                          | Investor / counterparty       | Framework required, firm-defined                         | KYC configuration and database field         |
| `valuation_guideline_source`          | IPEV, IFRS 13, ASC 820 or internal policy                                                                                                                      | IPEV / valuation policy                  | Private assets                | Fund methodology                                         | Valuation reference data                     |
| `ipev_guideline_version`              | IPEV version used                                                                                                                                              | IPEV                                     | Private assets                | Methodology setting                                      | Valuation methodology field                  |
| `valuation_technique`                 | Market, income, transaction or other approach                                                                                                                  | IPEV                                     | Private assets                | Methodology setting                                      | Valuation input                              |
| `calibration_reference_date`          | Date used for calibration                                                                                                                                      | IPEV                                     | Private assets                | Methodology input                                        | Valuation input                              |
| `selected_multiple`                   | Multiple applied                                                                                                                                               | IPEV                                     | Private assets                | Methodology input                                        | Valuation input                              |
| `discount_rate`                       | DCF discount rate                                                                                                                                              | IPEV                                     | Private assets                | Methodology input                                        | Valuation input                              |
| `scenario_probability`                | Probability assigned to valuation scenario                                                                                                                     | IPEV                                     | Private assets                | Methodology input                                        | Valuation input                              |
| `valuation_committee_approval_status` | Draft, reviewed, approved, challenged                                                                                                                          | IPEV / valuation governance              | Private assets                | Governance field                                         | Workflow field                               |

---

## 6. Prescriptive vs principles-based requirements

### 6.1 Prescriptive requirements

| Variable / area                    | Prescribed element                                               | System implication                   |
| ---------------------------------- | ---------------------------------------------------------------- | ------------------------------------ |
| Annex IV reporting                 | Field schema, XML structure, validation rules and allowed values | Versioned reporting schema           |
| AIFMD leverage                     | Gross and commitment methods                                     | Calculation engine                   |
| UCITS global exposure              | Commitment, relative VaR or absolute VaR method                  | Methodology selector and rule engine |
| UCITS issuer / counterparty limits | Legal concentration limits                                       | Rule engine                          |
| PRIIPs SRI                         | Formula and risk classes                                         | Calculation engine                   |
| PRIIPs performance scenarios       | Scenario types and methodology                                   | Calculation engine                   |
| PRIIPs cost tables                 | Cost categories and presentation                                 | Reporting engine                     |
| SFDR PAI                           | Indicator list and templates                                     | ESG schema                           |
| Taxonomy alignment                 | Conditions for alignment and KPI templates                       | ESG data engine                      |
| EMIR reporting                     | Derivative field schema                                          | Trade reporting module               |
| SFTR reporting                     | SFT field schema                                                 | SFT reporting module                 |
| MiFIR reporting                    | Transaction-reporting fields                                     | Transaction reporting module         |
| MMFR WAM / WAL / liquidity         | Legal liquidity and maturity metrics                             | MMF rule engine                      |
| CSDR settlement discipline         | Settlement fail and penalty mechanics                            | Operations risk module               |

---

### 6.2 Framework-required but fund-defined variables

| Variable / area              | Regulation requires               | Fund / AIFM defines                                  | System implication               |
| ---------------------------- | --------------------------------- | ---------------------------------------------------- | -------------------------------- |
| AIFMD risk limits            | Risk management framework         | Limit values and escalation thresholds               | Store as fund methodology        |
| Liquidity buckets            | Liquidity monitoring framework    | Bucket definitions                                   | Configurable bucket scheme       |
| LST assumptions              | Regular stress testing            | Scenario severity and assumptions                    | Scenario configuration           |
| LST frequency                | Regular testing                   | Exact operational cadence unless otherwise specified | Fund-level setting               |
| LMT activation               | LMT framework and governance      | Activation thresholds and operational rules          | Configurable rules and event log |
| Swing pricing calibration    | Tool characteristics and fairness | Factor and calibration logic                         | Methodology versioning           |
| Counterparty limits for AIFs | Monitoring                        | Internal limit values                                | Internal risk limit engine       |
| Valuation methodology        | Valuation policy and process      | Method, inputs, overrides and governance             | Valuation methodology module     |
| IPEV valuation inputs        | Industry best practice framework  | Peer set, multiple, discount rate, scenarios         | Private asset valuation engine   |
| ESG estimates                | Disclosure and data needs         | Estimation method and provider                       | ESG data lineage model           |

---

## 7. Annex IV reporting architecture

### 7.1 Legal basis

AIFMD Article 24 is the legal basis for AIFMD supervisory reporting.

| Paragraph     | Meaning for system design                                                                                                                    |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| Article 24(1) | AIFM-level reporting: principal markets, instruments, exposures and concentrations.                                                          |
| Article 24(2) | AIF-level reporting: illiquid assets, special arrangements, risk profile, risk management systems, main asset categories and stress testing. |
| Article 24(3) | List of AIFs managed.                                                                                                                        |
| Article 24(4) | Leverage level and sources of leverage for substantially leveraged AIFs.                                                                     |

Article 24 creates the reporting duty. The detailed field names, XML tags, data types, conditionality and validation rules are handled by ESMA AIFMD Reporting Technical Guidance and national reporting instructions such as the CSSF AIFM Reporting Technical Guidance.

---

### 7.2 Main design conclusion

Annex IV is not a position-level holdings report.

Annex IV is an aggregated supervisory report generated from detailed source data.

The database must be more detailed than Annex IV.

Annex IV consumes:

* positions
* instruments
* derivatives
* SFTs
* collateral
* counterparty exposures
* NAV snapshots
* investor data
* liquidity terms
* stress testing results
* leverage calculations
* PE valuations
* strategy classifications

Annex IV submits:

* fund-level fields
* AIFM-level fields
* aggregated exposure blocks
* top concentration blocks
* liquidity buckets
* investor redemption buckets
* strategy allocations
* leverage measures
* counterparty summaries
* risk profile fields
* validation-controlled XML values

---

### 7.3 Annex IV hierarchy

Annex IV should be modelled as hierarchical reporting data.

```text
AnnexIVReport
  ├── ReportMetadata
  ├── AIFMIdentification
  ├── AIFIdentification
  ├── AIFMPrincipalMarkets[]
  ├── AIFMPrincipalInstruments[]
  ├── AIFStrategyAllocation[]
  ├── AIFPrincipalExposure[]
  ├── AIFConcentration[]
  ├── AIFLiquidityProfile[]
  ├── AIFInvestorLiquidityProfile[]
  ├── AIFSpecialArrangements[]
  ├── AIFBorrowing[]
  ├── AIFLeverage[]
  ├── AIFCounterpartyExposure[]
  ├── AIFDerivativeExposure[]
  ├── AIFCollateral[]
  ├── AIFRiskProfile[]
  ├── AIFStressTesting[]
  ├── AIFPerformanceAndFlows[]
  ├── ValidationResult[]
  └── SubmissionFeedback[]
```

The `[]` means a repeated child block.

---

### 7.4 Annex IV field definition layer

`AnnexIVFieldDefinition` should be a central metadata table.

Suggested columns:

| Column                   | Meaning                                                       |
| ------------------------ | ------------------------------------------------------------- |
| `field_id`               | Internal field identifier                                     |
| `esma_field_name`        | ESMA field name                                               |
| `xml_tag`                | Exact XML tag                                                 |
| `xsd_file`               | AIFM XSD or AIF XSD                                           |
| `report_level`           | AIFM or AIF                                                   |
| `section`                | Identification, leverage, liquidity, exposure, risk, etc.     |
| `parent_block`           | Parent XML / reporting block                                  |
| `repeating_block_flag`   | Whether field belongs to a repeated block                     |
| `sequence_number`        | XML sequence                                                  |
| `data_type`              | String, decimal, integer, date, boolean, enum                 |
| `unit`                   | Currency, percentage, amount, days, count                     |
| `currency_required_flag` | Whether paired currency is required                           |
| `mandatory_status`       | Mandatory, optional or conditional                            |
| `conditionality_rule_id` | Rule making the field mandatory                               |
| `allowed_value_table_id` | Link to allowed values                                        |
| `validation_rule_ids`    | Linked validation controls                                    |
| `source_system`          | PMS, accounting, risk engine, investor register, manual input |
| `source_table`           | Internal source table                                         |
| `source_field`           | Internal source field                                         |
| `calculation_method_id`  | Method if derived                                             |
| `override_allowed_flag`  | Whether override is allowed                                   |
| `audit_required_flag`    | Whether supporting evidence is required                       |
| `valid_from`             | Schema start date                                             |
| `valid_to`               | Schema end date                                               |
| `source_reference`       | ESMA / CSSF source and version                                |

---

### 7.5 Annex IV report instance layer

`AnnexIVReport` suggested columns:

| Column                   | Meaning                                                    |
| ------------------------ | ---------------------------------------------------------- |
| `report_id`              | Internal report ID                                         |
| `report_level`           | AIFM or AIF                                                |
| `aifm_id`                | AIFM identifier                                            |
| `aif_id`                 | AIF identifier                                             |
| `reporting_period_start` | Period start                                               |
| `reporting_period_end`   | Period end                                                 |
| `reporting_year`         | Reporting year                                             |
| `reporting_quarter`      | Reporting quarter                                          |
| `reporting_frequency`    | Annual, half-yearly, quarterly                             |
| `reporting_member_state` | Member state of submission                                 |
| `schema_version`         | ESMA schema version                                        |
| `cssf_guidance_version`  | CSSF guidance version                                      |
| `report_status`          | Draft, validated, submitted, accepted, rejected, corrected |
| `correction_flag`        | Correction of previous report                              |
| `cancellation_flag`      | Cancellation of previous report                            |
| `previous_report_id`     | Previous report reference                                  |
| `created_at`             | Creation timestamp                                         |
| `submitted_at`           | Submission timestamp                                       |
| `accepted_at`            | Acceptance timestamp                                       |

---

### 7.6 Annex IV repeated block layer

`AnnexIVRepeatedBlock` suggested columns:

| Column                   | Meaning                                                             |
| ------------------------ | ------------------------------------------------------------------- |
| `block_id`               | Internal block ID                                                   |
| `report_id`              | Linked report                                                       |
| `block_type`             | Liquidity bucket, exposure, counterparty, strategy, leverage source |
| `block_rank`             | Ranking where relevant                                              |
| `block_code`             | ESMA or internal code                                               |
| `block_label`            | Label                                                               |
| `amount_value`           | Monetary value                                                      |
| `percentage_value`       | Percentage value                                                    |
| `currency`               | Currency                                                            |
| `as_of_date`             | Snapshot date                                                       |
| `period_start`           | Flow period start                                                   |
| `period_end`             | Flow period end                                                     |
| `calculation_run_id`     | Source calculation                                                  |
| `methodology_version_id` | Methodology used                                                    |
| `source_snapshot_id`     | Source data snapshot                                                |

---

### 7.7 Annex IV source data vs output data

| Source data                | Annex IV output                                                                                  |
| -------------------------- | ------------------------------------------------------------------------------------------------ |
| Every position             | Aggregated exposure by asset class, country, currency, issuer or strategy                        |
| Every derivative trade     | Aggregated derivative exposure, clearing status, counterparty exposure and leverage contribution |
| Every investor             | Investor concentration and investor redemption buckets                                           |
| Every PE portfolio company | Aggregated PE strategy, geography, sector, concentration and valuation exposure                  |
| Every collateral record    | Collateral summaries and counterparty exposure mitigation                                        |
| Every SFT                  | Financing, collateral, leverage and counterparty summaries                                       |
| Every valuation model      | Fair-value exposure and valuation-derived position values                                        |
| Every stress scenario      | Latest or relevant stress testing outputs                                                        |
| Every borrowing facility   | Borrowing and source-of-leverage reporting                                                       |

---

### 7.8 Bucket design

Bucket fields should be child rows, not scalar fields.

`LiquidityBucketResult` suggested columns:

| Column                   | Meaning                                                                   |
| ------------------------ | ------------------------------------------------------------------------- |
| `bucket_result_id`       | Internal ID                                                               |
| `fund_id`                | Fund                                                                      |
| `as_of_date`             | Snapshot date                                                             |
| `bucket_type`            | Portfolio liquidity, investor liquidity, notice period, time to liquidate |
| `bucket_code`            | Regulatory or internal code                                               |
| `bucket_label`           | Bucket label                                                              |
| `percentage_value`       | Percentage in bucket                                                      |
| `amount_value`           | Amount in bucket                                                          |
| `calculation_basis`      | NAV, AUM, investor value or gross exposure                                |
| `methodology_version_id` | Bucket methodology                                                        |
| `source_snapshot_id`     | Source data snapshot                                                      |

Investor redemption buckets should be generated from investor register, share-class terms and side-letter terms where relevant.

---

### 7.9 Derivative and clearing design

Internal derivative source layer:

| Field                     | Meaning                                             |
| ------------------------- | --------------------------------------------------- |
| `trade_id`                | Internal trade ID                                   |
| `uti`                     | Unique trade identifier                             |
| `fund_id`                 | Fund                                                |
| `instrument_id`           | Instrument                                          |
| `counterparty_id`         | Counterparty                                        |
| `derivative_type`         | Swap, future, option, forward, CDS, IRS, etc.       |
| `underlying_asset_class`  | Equity, interest rate, credit, FX, commodity, other |
| `underlying_identifier`   | ISIN, index, currency pair or other identifier      |
| `notional_amount`         | Trade notional                                      |
| `market_value`            | Fair value                                          |
| `delta_adjusted_exposure` | Delta-adjusted exposure                             |
| `maturity_date`           | Maturity date                                       |
| `clearing_status`         | Cleared, bilateral, exchange-traded                 |
| `ccp_lei`                 | CCP LEI where relevant                              |
| `clearing_member_id`      | Clearing member                                     |
| `execution_venue`         | Execution venue                                     |
| `hedging_flag`            | Hedging purpose                                     |
| `currency_hedging_flag`   | Currency hedge                                      |
| `leverage_contribution`   | Contribution to leverage                            |

Annex IV output layer:

| Output                              | Meaning                                       |
| ----------------------------------- | --------------------------------------------- |
| `derivative_exposure_by_type`       | Aggregated exposure by derivative type        |
| `derivative_exposure_by_underlying` | Aggregated exposure by underlying asset class |
| `cleared_derivative_exposure`       | Aggregated cleared exposure                   |
| `bilateral_derivative_exposure`     | Aggregated bilateral exposure                 |
| `counterparty_derivative_exposure`  | Aggregated exposure by counterparty           |
| `leverage_from_derivatives`         | Derivative contribution to leverage           |

Design conclusion:

* Source layer can have one row per derivative trade or position.
* Annex IV usually receives aggregated derivative reporting blocks.
* Do not model Annex IV as one row per derivative unless the field schema explicitly requires it.

---

### 7.10 Private equity and Annex IV

Private equity data should be detailed internally.

Annex IV usually consumes PE data through aggregated exposure, concentration, geography, sector, strategy and valuation outputs.

| Data                      | Store internally | Annex IV treatment                                                      |
| ------------------------- | ---------------: | ----------------------------------------------------------------------- |
| Portfolio company name    |              Yes | Not normally full list unless required by specific field or NCA request |
| Portfolio company country |              Yes | Aggregated geography exposure                                           |
| Portfolio company sector  |              Yes | Aggregated sector / strategy exposure                                   |
| Fair value per company    |              Yes | Aggregated NAV, exposure and concentration                              |
| IPEV methodology          |              Yes | Valuation governance, not usually direct Annex IV field                 |
| Control flag              |              Yes | Relevant for private equity monitoring and AIFMD control analysis       |
| Unrealised gain / loss    |              Yes | Valuation / investor reporting, not usually a core Annex IV field       |

Design conclusion:

* PE company data is source data.
* IPEV belongs to valuation governance and private asset methodology.
* Annex IV pulls the resulting fair values, exposures and concentration outputs.

---

## 8. Annex IV data tables

### 8.1 Source tables

| Source table             | Granularity                                       | Consumed by Annex IV for                               |
| ------------------------ | ------------------------------------------------- | ------------------------------------------------------ |
| `Fund`                   | One row per fund                                  | Fund identity, regime, reporting scope                 |
| `AIFM`                   | One row per manager                               | AIFM identity and reporting obligation                 |
| `ShareClass`             | One row per share class                           | Currency, investor terms, PRIIPs / investor reporting  |
| `Position`               | One row per position per valuation date           | Exposures, asset class, geography, concentration       |
| `Instrument`             | One row per instrument                            | Classification, asset eligibility, derivative flag     |
| `Issuer`                 | One row per issuer                                | Issuer concentration, country, sector                  |
| `Counterparty`           | One row per counterparty                          | Counterparty exposure                                  |
| `DerivativePosition`     | One row per derivative trade or position          | Derivative exposure, leverage, counterparty risk       |
| `SFTPosition`            | One row per SFT                                   | Financing, leverage, collateral, counterparty exposure |
| `CollateralBalance`      | One row per collateral item or agreement          | Collateral value, reuse, haircut                       |
| `InvestorHolding`        | One row per investor / investor group             | Investor concentration and profile                     |
| `InvestorLiquidityTerms` | One row per investor, share class or dealing term | Redemption profile                                     |
| `PortfolioCompany`       | One row per private company                       | PE exposure and valuation source                       |
| `PrivateAssetValuation`  | One row per investment / valuation date           | Fair value and PE valuation output                     |
| `NAVSnapshot`            | One row per fund / share class / date             | NAV and AUM                                            |
| `RiskCalculationRun`     | One row per risk run                              | Leverage, exposure, stress outputs                     |
| `LiquidityBucketResult`  | One row per bucket / fund / date                  | Liquidity profile                                      |
| `StressTestResult`       | One row per scenario / fund / date                | Stress testing fields                                  |
| `BorrowingFacility`      | One row per facility                              | Borrowing and leverage                                 |
| `FundFlow`               | One row per subscription / redemption period      | Flows and redemption pressure                          |

---

### 8.2 Reporting tables

| Reporting table             | Purpose                         |
| --------------------------- | ------------------------------- |
| `AnnexIVReport`             | One filing instance             |
| `AnnexIVFieldDefinition`    | ESMA / CSSF field metadata      |
| `AnnexIVFieldValue`         | Submitted value per field       |
| `AnnexIVAllowedValue`       | Allowed values                  |
| `AnnexIVValidationRule`     | Technical validation rules      |
| `AnnexIVRepeatedBlock`      | Repeated block values           |
| `AnnexIVSourceMapping`      | Mapping to internal source data |
| `AnnexIVCalculationRun`     | Calculation snapshot            |
| `AnnexIVSubmission`         | XML / ZIP submission record     |
| `AnnexIVSubmissionFeedback` | CSSF / NCA response             |

---

## 9. IPEV and private asset valuation framework

### 9.1 Classification

IPEV should be classified as industry best practice and fund methodology.

It should not be placed in the regulatory source hierarchy as Level 1, Level 2, ESMA or CSSF.

| Source                    | Authority classification                  | Platform treatment                                                                       |
| ------------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------------- |
| IPEV Valuation Guidelines | Industry best practice / fund methodology | Private asset valuation methodology, valuation policy, governance and evidence framework |

---

### 9.2 Private asset valuation entities

| Entity                     | Key fields                                                                                                                   |
| -------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `PortfolioCompany`         | company name, country, sector, stage, control flag, acquisition date, exit date, ownership percentage                        |
| `PrivateAssetPosition`     | fund ID, company ID, instrument type, investment date, cost, fair value, ownership percentage, currency                      |
| `PrivateAssetValuation`    | valuation date, fair value, valuation technique, IPEV version, valuation method, unrealised gain / loss, methodology version |
| `ValuationInputSet`        | revenue, EBITDA, EBIT, ARR, net debt, cash, forecasts, multiples, comparable companies, discount rate, terminal value        |
| `ValuationScenario`        | scenario name, probability, exit value, downside case, base case, upside case                                                |
| `CapitalStructureModel`    | security class, preference, conversion, liquidation preference, allocation method                                            |
| `ValuationGovernanceEvent` | reviewer, committee date, approval status, challenge comment, override reason                                                |

---

### 9.3 IPEV variables

| Variable                                    | Meaning                                                       | Data treatment                |
| ------------------------------------------- | ------------------------------------------------------------- | ----------------------------- |
| `valuation_guideline_source`                | IPEV, IFRS 13, ASC 820 or internal policy                     | Valuation reference data      |
| `ipev_guideline_version`                    | IPEV version used                                             | Methodology reference         |
| `fair_value_basis`                          | Fair value basis                                              | Methodology field             |
| `valuation_technique`                       | Market, income, transaction, replacement-cost or other method | Methodology enum              |
| `calibration_reference_date`                | Calibration date                                              | Valuation input               |
| `calibration_basis`                         | Entry price / transaction price calibration                   | Valuation input               |
| `known_or_knowable_information_cutoff`      | Information cut-off date                                      | Governance field              |
| `comparable_company_set_id`                 | Peer set                                                      | Valuation input               |
| `valuation_multiple_type`                   | EBITDA, revenue, ARR, book value or other multiple            | Valuation input               |
| `selected_multiple`                         | Selected multiple                                             | Valuation input               |
| `multiple_adjustment`                       | Premium or discount to peer multiple                          | Valuation input               |
| `maintainable_earnings_metric`              | Earnings or revenue base                                      | Valuation input               |
| `enterprise_value`                          | Value before debt / cash adjustments                          | Derived output                |
| `net_debt_adjustment`                       | Debt, cash and debt-like adjustments                          | Valuation input / derived     |
| `equity_value`                              | Equity value                                                  | Derived output                |
| `capital_structure_method`                  | Allocation across securities                                  | Methodology choice            |
| `option_pricing_method_flag`                | OPM used                                                      | Methodology flag              |
| `probability_weighted_scenario_method_flag` | PWERM used                                                    | Methodology flag              |
| `scenario_probability`                      | Scenario weight                                               | Valuation input               |
| `discount_rate`                             | DCF discount rate                                             | Valuation input               |
| `terminal_value_method`                     | Exit multiple or terminal growth                              | Methodology input             |
| `terminal_growth_rate`                      | Terminal growth assumption                                    | Valuation input               |
| `illiquidity_discount`                      | Discount for lack of liquidity                                | Valuation input               |
| `control_premium_or_discount`               | Control / minority adjustment                                 | Valuation input               |
| `esg_valuation_adjustment_flag`             | ESG adjustment used in valuation                              | Methodology flag              |
| `valuation_uncertainty_flag`                | Valuation uncertainty marker                                  | Governance / disclosure field |
| `valuation_override_flag`                   | Manual override applied                                       | Governance field              |
| `valuation_committee_approval_status`       | Draft, reviewed, approved, challenged                         | Workflow field                |

---

## 10. ESG and sustainability variables

| Variable                                  | Meaning                                | Source                         | Classification                        | Data treatment         |
| ----------------------------------------- | -------------------------------------- | ------------------------------ | ------------------------------------- | ---------------------- |
| `sfdr_article_classification`             | Article 6, 8 or 9                      | SFDR Articles 6, 8, 9          | Fund-level disclosure classification  | Fund-level setting     |
| `sustainability_risk_integration_flag`    | Sustainability risks considered        | SFDR Article 6                 | Mandatory disclosure                  | Product field          |
| `pai_considered_flag`                     | PAI considered                         | SFDR Article 4                 | Mandatory entity / product disclosure | Entity and fund field  |
| `pai_indicator_id`                        | PAI indicator code                     | SFDR RTS Annex I               | Regulatory reference data             | ESG reference table    |
| `pai_indicator_value`                     | Measured PAI value                     | SFDR RTS                       | Derived / external data               | ESG metric field       |
| `environmental_or_social_characteristics` | Article 8 promoted characteristics     | SFDR Article 8                 | Mandatory disclosure for Article 8    | Disclosure object      |
| `sustainable_investment_objective`        | Article 9 objective                    | SFDR Article 9                 | Mandatory disclosure for Article 9    | Disclosure object      |
| `sustainable_investment_percentage`       | Share of sustainable investments       | SFDR RTS                       | Derived output                        | ESG calculation output |
| `taxonomy_environmental_objective`        | One of six objectives                  | Taxonomy Article 9             | Regulatory reference data             | Enum                   |
| `substantial_contribution_flag`           | Activity contributes to objective      | Taxonomy Article 3             | Methodology input / output            | ESG data field         |
| `dnsh_pass_flag`                          | Do no significant harm                 | Taxonomy Article 17            | Mandatory input / output              | ESG data field         |
| `minimum_safeguards_pass_flag`            | Minimum safeguards                     | Taxonomy Article 18            | Mandatory input / output              | ESG data field         |
| `taxonomy_eligible_value`                 | Exposure to eligible activities        | Taxonomy Article 8             | Derived output                        | ESG calculation output |
| `taxonomy_aligned_value`                  | Exposure to aligned activities         | Taxonomy Article 8             | Derived output                        | ESG calculation output |
| `taxonomy_alignment_rate`                 | Aligned exposure / denominator         | Taxonomy Article 8             | Derived output                        | ESG calculation output |
| `turnover_kpi`                            | Taxonomy turnover KPI                  | Delegated Regulation 2021/2178 | Third-party data / reporting input    | Issuer metric          |
| `capex_kpi`                               | Taxonomy CapEx KPI                     | Delegated Regulation 2021/2178 | Third-party data / reporting input    | Issuer metric          |
| `opex_kpi`                                | Taxonomy OpEx KPI                      | Delegated Regulation 2021/2178 | Third-party data / reporting input    | Issuer metric          |
| `good_governance_pass_flag`               | SFDR good governance test              | SFDR                           | Methodology input                     | Issuer ESG control     |
| `esg_data_provider_id`                    | ESG data source                        | Implementation need            | Third-party dependency                | Data lineage           |
| `esg_estimate_flag`                       | Reported or estimated data             | Implementation need            | Methodology input                     | ESG audit field        |
| `data_coverage_ratio`                     | Share of portfolio covered by ESG data | Implementation need            | Derived output                        | Control metric         |

---

## 11. Recommended domain entities

| Entity                  | Key fields                                                                                                                                            |
| ----------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `Fund`                  | fund ID, name, domicile, legal form, regime, AIF / UCITS / MMF / ELTIF flag, open-ended flag, base currency, NAV, AUM, SFDR classification, benchmark |
| `AIFM`                  | AIFM name, LEI, national code, domicile, authorisation status, registration status, reporting scope                                                   |
| `ShareClass`            | ISIN, currency, distribution / accumulation flag, PRIIPs KID flag, target market, fees, redemption terms                                              |
| `Position`              | fund, instrument, quantity, market value, NAV percentage, exposure, liquidity bucket                                                                  |
| `Instrument`            | ISIN, asset class, eligible asset classification, derivative flag, SFT flag, securitisation flag, benchmark exposure                                  |
| `Issuer`                | LEI, country, sector, group, credit quality, ESG metrics, taxonomy metrics                                                                            |
| `Counterparty`          | LEI, country, counterparty type, exposure, collateral, EMIR classification                                                                            |
| `DerivativePosition`    | UTI, derivative type, underlying, notional, market value, clearing status, counterparty, maturity, hedge flag                                         |
| `SFTPosition`           | SFT type, counterparty, collateral, reuse flag, maturity, market value                                                                                |
| `CollateralBalance`     | collateral type, value, haircut, currency, issuer, reuse flag, eligibility                                                                            |
| `InvestorHolding`       | investor type, country, holding value, share class, concentration, liquidity terms                                                                    |
| `PortfolioCompany`      | name, country, sector, stage, control flag, ownership percentage                                                                                      |
| `PrivateAssetValuation` | fair value, IPEV version, valuation technique, multiples, DCF inputs, scenario probabilities, approval status                                         |
| `LiquidityFramework`    | buckets, redemption terms, LST assumptions, liquidity limits                                                                                          |
| `LeverageFramework`     | gross method, commitment method, netting rules, hedging rules, leverage limits                                                                        |
| `RiskMethodology`       | VaR parameters, stress scenarios, counterparty limits, concentration limits                                                                           |
| `LMTFramework`          | selected tools, calibration, activation trigger, activation status, governance                                                                        |
| `ValuationPolicy`       | valuation frequency, valuation technique, IPEV source, pricing source, override policy, approval workflow                                             |
| `ESGProfile`            | SFDR classification, PAI indicators, Taxonomy alignment, DNSH, safeguards                                                                             |
| `ReportingFramework`    | report type, schema version, authority, filing frequency, validation rules                                                                            |
| `RegulatoryFiling`      | report type, period, schema version, validation status, submission status                                                                             |
| `BreachEvent`           | breach type, rule, detected date, corrected date, materiality, notification status                                                                    |
| `SubmissionFeedback`    | authority, file, status, error code, error message, correction workflow                                                                               |

---

## 12. Data model implications

| Variable group              | Representation                                      | Rationale                                                              |
| --------------------------- | --------------------------------------------------- | ---------------------------------------------------------------------- |
| Fund legal regime           | Database field plus reference data                  | Drives rule selection                                                  |
| AIFMD Annex IV fields       | Regulatory schema and reporting field               | Field definitions are versioned and validation-controlled              |
| EMIR / SFTR / MiFIR fields  | Regulatory schema                                   | Field lists and validations change over time                           |
| PRIIPs calculations         | Formula engine and calculation snapshot             | Outputs depend on prescribed method and source data                    |
| SFDR / Taxonomy data        | ESG data model and reporting schema                 | Requires external data, methodology and audit trail                    |
| AIF risk limits             | Fund-level configuration                            | AIFMD requires a framework, not fixed values                           |
| Liquidity buckets           | Methodology configuration and repeated output table | Buckets are repeated reporting blocks                                  |
| LMTs                        | Regulatory reference data plus fund configuration   | Tool list is prescribed, calibration is fund-specific                  |
| UCITS limits                | Rule engine                                         | Limits are prescriptive                                                |
| IPEV valuation inputs       | Valuation methodology and evidence model            | Industry best practice, not reporting schema                           |
| NAV error / breach workflow | Workflow entity                                     | Requires detection, correction, compensation and notification tracking |
| Derived outputs             | Calculation snapshot                                | Need reproducibility and audit trail                                   |

---

## 13. Data lineage requirements

Every reported or disclosed value should include:

| Field                    | Purpose                              |
| ------------------------ | ------------------------------------ |
| `source_snapshot_id`     | Data extract used                    |
| `calculation_run_id`     | Calculation that generated the value |
| `methodology_version_id` | Methodology applied                  |
| `as_of_date`             | Snapshot date                        |
| `period_start`           | Start date for flow fields           |
| `period_end`             | End date for flow fields             |
| `override_flag`          | Whether manual override occurred     |
| `override_reason`        | Why override occurred                |
| `approver_id`            | Approval evidence                    |
| `evidence_uri`           | Link to supporting file              |
| `schema_version`         | Regulatory schema version            |
| `submission_id`          | Link to submitted report             |
| `regulator_feedback_id`  | Link to feedback or rejection        |

---

## 14. Architecture recommendation

The platform should support these modules:

| Module                         | Main purpose                                                                  |
| ------------------------------ | ----------------------------------------------------------------------------- |
| Regulatory metadata module     | Store source documents, articles, fields, allowed values and validation rules |
| Fund master module             | Store fund, share class, regime and legal structure                           |
| Position and instrument module | Store holdings, instruments, issuer data and exposures                        |
| Derivatives and SFT module     | Store derivative trades, SFTs, collateral and counterparty exposure           |
| Liquidity module               | Store liquidity methodology, buckets, LST and LMT framework                   |
| Leverage module                | Calculate gross and commitment leverage                                       |
| UCITS rule engine              | Calculate global exposure and investment-limit compliance                     |
| PRIIPs module                  | Calculate SRI, scenarios and costs                                            |
| ESG module                     | Store SFDR, PAI and Taxonomy data                                             |
| Private asset valuation module | Store IPEV methodology, valuation inputs and governance                       |
| Annex IV module                | Generate AIFMD XML reports from source data and calculation outputs           |
| Reporting submission module    | Store generated XML, ZIP files, CSSF / NCA submissions and feedback           |
| Breach workflow module         | Track NAV errors, investment breaches and remediation                         |
| Audit trail module             | Store lineage, approvals, overrides and evidence                              |

---

## 15. Final diagnostic conclusion

The platform should not be designed as a static collection of regulatory fields.

It should be designed as a layered regulatory data platform.

The main design rule is:

```text
The database must be more detailed than the regulatory report.
The regulatory report is an output, not the operating model.
```

For Annex IV:

* ESMA and CSSF field definitions belong in the regulatory metadata layer.
* Positions, derivatives, investors, collateral and PE companies belong in source tables.
* Liquidity buckets, exposure rankings and concentration blocks belong in calculation output tables.
* XML tags and validation rules belong in the reporting schema layer.
* Submitted values belong in a filing snapshot.
* CSSF feedback belongs in a regulator feedback workflow.

For AIFMD:

* Many fields are framework-driven.
* The fund defines many values through methodology, policy and internal risk limits.
* The system must support configurable methodologies with versioning and approval.

For UCITS, PRIIPs, SFDR, Taxonomy, EMIR, SFTR, MMFR and MiFIR:

* Many fields are schema-driven or formula-driven.
* The system must store versioned regulatory field definitions, allowed values and calculation logic.

For private equity:

* Full portfolio-company and valuation data should be stored internally.
* IPEV should be integrated into the private asset valuation framework as industry best practice.
* IPEV variables are methodology and governance inputs.
* Annex IV consumes PE data mainly through aggregated exposure, strategy, geography, concentration and valuation outputs.

The recommended core pattern is:

```text
RegulationSource
  → RegulatoryRequirement
  → VariableDefinition
  → FundMethodology
  → SourceDataSnapshot
  → CalculationRun
  → ReportingFieldValue
  → RegulatoryFiling
  → RegulatorFeedback
```

```
```
