# BDC XBRL Elements Reference

Complete reference for US GAAP Taxonomy elements used in BDC Schedule of Investments.

Source: FASB GAAP Taxonomy Implementation Guide - Financial Services - Investment Companies (June 2024)

## Important: Namespace Handling

XBRL concepts may or may not include namespace prefixes:
- `us-gaap:InvestmentOwnedAtFairValue`
- `InvestmentOwnedAtFairValue`
- `arcc:CustomExtension`

**Always normalize by stripping the prefix before matching:**

```python
def normalize_concept(concept: str) -> str:
    if not concept:
        return concept
    if ':' in concept:
        return concept.split(':', 1)[1]
    return concept
```

Elements below are listed WITHOUT namespace prefix.

## SEC Regulation S-X Schedules

BDC Schedule of Investments combines data from multiple Reg S-X Article 12 schedules:

| Schedule | Name | Content |
|----------|------|---------|
| 12-12 | Investments in Securities of Unaffiliated Issuers | All debt AND equity in non-affiliates |
| 12-13 | Investments in and Advances to Affiliates | All debt AND equity in affiliates (with roll-forward) |
| 12-14 | Investments Other Than Securities | Real estate, mortgage loans, other non-security investments |

**Note**: Schedules are split by AFFILIATION, not by debt vs equity.

## Data Location in XBRL

**Critical**: SOI data is split across multiple statements:

| Data | Statement Location |
|------|-------------------|
| Interest rates, spreads | Schedule of Investments |
| Fair values | Balance Sheet |
| Cost basis | Balance Sheet Parenthetical |

Must query all statements and join by investment ID.

## Core Investment Elements (Both Debt and Equity)

| Element Name | Standard Label | Balance | Period | Description |
|--------------|----------------|---------|--------|-------------|
| `InvestmentOwnedAtFairValue` | Investment Owned, Fair Value | Debit | Instant | Fair value of investment |
| `InvestmentOwnedAtCost` | Investment Owned, Cost | Debit | Instant | Amortized cost of investment |
| `InvestmentOwnedPercentOfNetAssets` | Investment Owned, Net Assets, Percentage | - | Instant | % of total net assets |
| `InvestmentAcquisitionDate` | Investment, Acquisition Date | - | Duration | Date investment acquired |

## Debt-Specific Elements

These elements apply primarily to debt investments (loans, bonds, notes):

| Element Name | Standard Label | Period | Description |
|--------------|----------------|--------|-------------|
| `InvestmentOwnedBalancePrincipalAmount` | Investment Owned, Balance, Principal Amount | Instant | Outstanding principal |
| `InvestmentInterestRate` | Investment Interest Rate | Instant | Stated/effective interest rate |
| `InvestmentBasisSpreadVariableRate` | Investment, Basis Spread, Variable Rate | Instant | Spread over base rate (e.g., SOFR + 500bps) |
| `InvestmentInterestRateFloor` | Investment, Interest Rate, Floor | Instant | Minimum interest rate floor |
| `InvestmentInterestRatePaidInKind` | Investment, Interest Rate, Paid in Kind | Instant | PIK portion of rate |
| `InvestmentInterestRatePaidInCash` | Investment, Interest Rate, Paid in Cash | Instant | Cash pay portion of rate |
| `InvestmentMaturityDate` | Investment Maturity Date | Instant | Maturity/due date |
| `InvestmentVariableInterestRateTypeExtensibleEnumeration` | Investment, Variable Interest Rate, Type | Instant | Base rate type (SOFR, Prime, etc.) |

## Equity-Specific Elements

These elements apply primarily to equity investments (stock, units, warrants):

| Element Name | Standard Label | Period | Description |
|--------------|----------------|--------|-------------|
| `InvestmentOwnedBalanceShares` | Investment Owned, Balance, Shares | Instant | Number of shares/units held |

## Boolean Flags

| Element Name | Standard Label | Description |
|--------------|----------------|-------------|
| `InvestmentRestrictionStatus` | Investment, Restriction Status [true false] | Restricted security flag |
| `InvestmentSignificantUnobservableInput` | Investment, Significant Unobservable Input [true false] | Level 3 fair value flag |
| `InvestmentNonIncomeProducing` | Investment, Nonincome Producing [true false] | Non-income producing flag |

## Extensible Enumerations

These elements contain URI references to taxonomy members or custom extensions:

| Element Name | Standard Label | Description |
|--------------|----------------|-------------|
| `InvestmentIssuerNameExtensibleEnumeration` | Investment, Issuer Name [Extensible Enumeration] | Portfolio company name |
| `InvestmentIssuerAffiliationExtensibleEnumeration` | Investment, Issuer Affiliation [Extensible Enumeration] | Affiliated/Unaffiliated |
| `InvestmentTypeExtensibleEnumeration` | Investment, Type [Extensible Enumeration] | Senior loan, equity, etc. |
| `InvestmentIndustrySectorExtensibleEnumeration` | Investment, Industry Sector [Extensible Enumeration] | Industry classification |
| `InvestmentVariableInterestRateTypeExtensibleEnumeration` | Investment, Variable Interest Rate, Type [Extensible Enumeration] | SOFR, LIBOR, Prime, etc. |

## Affiliated Investment Elements (Schedule 12-13)

For the Investments in Affiliates roll-forward schedule:

| Element Name | Standard Label | Balance | Period |
|--------------|----------------|---------|--------|
| `InvestmentsInAndAdvancesToAffiliatesAtFairValueGrossAdditions` | Investments in and Advances to Affiliates, Gross Additions | Debit | Duration |
| `InvestmentsInAndAdvancesToAffiliatesAtFairValueGrossReductions` | Investments in and Advances to Affiliates, Gross Reductions | Credit | Duration |
| `DebtAndEquitySecuritiesRealizedGainLoss` | Debt and Equity Securities, Realized Gain (Loss) | Credit | Duration |
| `DebtAndEquitySecuritiesUnrealizedGainLoss` | Debt and Equity Securities, Unrealized Gain (Loss) | Credit | Duration |
| `InterestIncomeOperating` | Interest Income, Operating | Credit | Duration |
| `DividendIncomeOperating` | Dividend Income, Operating | Credit | Duration |

## Common Investment Type Members

Standard taxonomy members for `InvestmentTypeExtensibleEnumeration`:

| Member | Standard Label |
|--------|----------------|
| `SeniorLoansMember` | Senior Loans |
| `SeniorSubordinatedLoansMember` | Senior Subordinated Loans |
| `SubordinatedDebtMember` | Subordinated Debt |
| `UnsecuredDebtMember` | Unsecured Debt |
| `ConvertibleDebtMember` | Convertible Debt |
| `CommonStockMember` | Common Stock |
| `CommonClassAMember` | Class A Common Stock |
| `CommonClassBMember` | Class B Common Stock |
| `PreferredStockMember` | Preferred Stock |
| `WarrantMember` | Warrants |

## Common Industry Sector Members

| Member | Standard Label |
|--------|----------------|
| `TechnologySectorMember` | Technology Sector |
| `HealthcareSectorMember` | Healthcare Sector |
| `FinancialServicesSectorMember` | Financial Services Sector |
| `RealEstateSectorMember` | Real Estate Sector |
| `InsuranceSectorMember` | Insurance Sector |
| `AutomotiveSectorMember` | Automotive Sector |
| `ConsumerDiscretionarySectorMember` | Consumer Discretionary |
| `IndustrialsSectorMember` | Industrials Sector |
| `EnergySectorMember` | Energy Sector |

## Variable Rate Type Members

| Member | Standard Label |
|--------|----------------|
| `SecuredOvernightFinancingRateSofrMember` | SOFR |
| `LondonInterbankOfferedRateLiborMember` | LIBOR (legacy) |
| `PrimeRateMember` | Prime Rate |
| `EurodollarRateMember` | Eurodollar Rate |

## Affiliation Members

| Member | Standard Label | Description |
|--------|----------------|-------------|
| `InvestmentUnaffiliatedIssuerMember` | Investment, Unaffiliated Issuer | <5% ownership |
| `InvestmentAffiliatedIssuerMember` | Investment, Affiliated Issuer | 5-25% ownership |
| `InvestmentAffiliatedIssuerControlledMember` | Investment, Affiliated Issuer, Controlled | >25% ownership |
| `InvestmentAffiliatedIssuerNoncontrolledMember` | Investment, Affiliated Issuer, Noncontrolled | 5-25% ownership |

## Data Coverage Expectations

Based on testing across ARCC, MAIN, FSK, HTGC:

| Element | Expected Coverage |
|---------|-------------------|
| InvestmentOwnedAtFairValue | 100% |
| InvestmentOwnedAtCost | 97-100% |
| InvestmentOwnedBalancePrincipalAmount | 70-75% (debt only) |
| InvestmentOwnedBalanceShares | 25-30% (equity only) |
| InvestmentInterestRate | 65-70% (debt only) |

## Notes on Element Usage

1. **Always normalize concept names** - Strip namespace prefixes before matching

2. **Query all statements** - Data is spread across SOI, Balance Sheet, and Parenthetical

3. **Investment IDs in contexts** - Access via `xbrl.contexts[context_ref].dimensions['InvestmentIdentifierAxis']`

4. **Custom extensions common** - BDCs create custom members for company names, investment types, industries

5. **Balance Types**: 
   - `Debit` = Asset-like (Fair Value, Cost, Principal)
   - `Credit` = Liability/Equity-like (Gains, Income)
   - No balance = Non-monetary (rates, percentages, counts)
