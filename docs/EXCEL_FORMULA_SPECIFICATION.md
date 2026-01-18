# Excel Formula Specification

## Complete Technical Reference for 225 Worth Ave Financial Model

**Source File:** `/Users/tooeycourtemanche/Desktop/Models XLS/225 Worth Ave_Model(revised).xlsx`
**Last Audit:** 2026-01-17
**Document Version:** 1.0

---

## Table of Contents

1. [Workbook Structure](#1-workbook-structure)
2. [Input Parameters](#2-input-parameters)
3. [Escalation Factors](#3-escalation-factors)
4. [Revenue Calculations](#4-revenue-calculations)
5. [Operating Expense Calculations](#5-operating-expense-calculations)
6. [NOI Calculations](#6-noi-calculations)
7. [Exit Value Calculations](#7-exit-value-calculations)
8. [Debt Service Calculations](#8-debt-service-calculations)
9. [Cash Flow Calculations](#9-cash-flow-calculations)
10. [Waterfall Distribution Calculations](#10-waterfall-distribution-calculations)
11. [Lease Commission Calculations](#11-lease-commission-calculations)
12. [Formula Dependency Map](#12-formula-dependency-map)
13. [Implementation Notes](#13-implementation-notes)

---

## 1. Workbook Structure

### 1.1 Worksheets

| Tab | Purpose | Key Rows/Columns | Relationship |
|-----|---------|------------------|--------------|
| **Assumptions** | All model inputs | B1:AN94 | Primary input source |
| **Model** | Monthly cash flow projections | A1:LS191 | Main calculation engine |
| **Waterfall** | LP/GP distribution calculations | B2:EN143 | Reads from Model tab |
| **LCs** | Lease commission calculations | B2:O26 | Reads from Assumptions |
| **Debt** | Amortization schedules | B2:T1066 | Reads from Assumptions |
| **SOFR** | Forward rate curves | M2:N125 | Lookup table for floating rates |
| **Comps** | Comparable properties | B2:BK101 | Reference data |
| **Charts** | Visualizations | A2:AH47 | Display only |

### 1.2 Column Structure (Model Tab)

| Column | Purpose |
|--------|---------|
| A-D | Row labels |
| E-H | Input parameters (RSF, lease end, rent PSF, flags) |
| I | Totals (SUMIF over hold period) |
| J | Period before Month 0 |
| K | Month 0 (Acquisition) |
| L | Month 1 |
| M-EN | Months 2-120+ |

### 1.3 Key Row Reference (Model Tab)

| Row | Description |
|-----|-------------|
| 2 | Rent escalation factor |
| 3 | Expense escalation factor |
| 4 | Property tax escalation |
| 10 | Month number (0, 1, 2, ...) |
| 11 | Year number |
| 12 | Date |
| 46-48 | Tenant base rent (Spaces A, B, C) |
| 49-51 | Free rent deductions |
| 52-53 | Parking/Storage income |
| 54-55 | Reimbursement revenue |
| 56-59 | Total revenue, vacancy, collection loss |
| 61-67 | Operating expenses |
| 69 | Retail NOI |
| 72 | Total Actual NOI |
| 74 | Net Exit Proceeds |
| 81 | Unleveraged Cash Flow |
| 85 | Unleveraged IRR |
| 119-127 | Acquisition debt schedule |
| 186 | Leveraged Cash Flow |
| 190 | Leveraged IRR |

---

## 2. Input Parameters

### 2.1 Acquisition Inputs (Assumptions Tab)

| Parameter | Cell | Value | Description |
|-----------|------|-------|-------------|
| Purchase Price | C13 | $41,500K | Property purchase price |
| Closing Costs | C14 | $500K | Transaction costs |
| Total Acquisition | C15 | =SUM(C13:C14) | $42,000K |

### 2.2 Financing Inputs (Assumptions Tab)

| Parameter | Cell | Value | Description |
|-----------|------|-------|-------------|
| LTC | L23 | 40% | Loan-to-Cost ratio |
| Loan Amount | L24 | =L22*L23 | $16,937K |
| Fixed Interest Rate | J15 | 5.25% | Annual rate |
| I/O Period | L18 | 120 months | Interest-only period |
| Amortization | L19 | 30 years | Amort period (if applicable) |
| Loan Fees | K16 | 1.00% | Bank and broker fees |
| Loan Closing Costs | K17 | 1.00% | Legal and closing costs |

### 2.3 Tenant Data (Assumptions Tab, Rows 8-10)

| Field | Column | Space A | Space B | Space C |
|-------|--------|---------|---------|---------|
| Tenant | AD | Peter Millar | J McLaughlin | Gucci |
| RSF | AE | 2,300 | 1,868 | 5,950 |
| In-Place Rent PSF | AF | $201.45 | $200.47 | $187.65 |
| Market Rent PSF | AH | $300.00 | $300.00 | $300.00 |
| Lease End Date | AJ | 2031-12-31 | 2030-05-31 | N/A |
| Options End Date | AL | 2041-12-31 | 2030-05-31 | 2043-09-30 |
| Annual Bumps | AN | 2.5% | 2.5% | 2.5% |

### 2.4 Operating Assumptions (Assumptions Tab)

| Parameter | Cell | Value | Description |
|-----------|------|-------|-------------|
| Fixed OpEx PSF | T54 | $36.00 | Annual per SF |
| Variable OpEx PSF | T55 | $6.11 | Annual per SF |
| Management Fee | T56 | 4.00% | Of effective revenue |
| Property Tax | T57 | $622.5K | Annual |
| CapEx Reserve PSF | T59 | $5.00 | Annual per SF |
| General Vacancy | T51 | 0.00% | Vacancy factor |
| Collection Loss | T52 | 0.00% | Bad debt factor |

### 2.5 Free Rent & TI Assumptions

| Parameter | Cell | Value |
|-----------|------|-------|
| TI Buildout Period | T49 | 6 months |
| Free Rent Months | T50 | 10 months |

### 2.6 Rollover Flags (Model Tab, Column H)

The H column controls whether rollover costs apply at lease expiration:

| Row | Tenant | H Value | Meaning |
|-----|--------|---------|---------|
| 49 | Space A | 1 | NO rollover costs (direct to market rent) |
| 50 | Space B | 0 | YES apply TI buildout + free rent |
| 51 | Space C | 0 | YES apply TI buildout + free rent |

**Logic:** `H=1` means immediate transition to market rent. `H=0` means apply TI buildout gap and free rent period.

### 2.7 Exit Assumptions (Assumptions Tab)

| Parameter | Cell | Formula/Value |
|-----------|------|---------------|
| Hold Period | L9 | 120 months |
| Exit Month | X13 | 120 |
| Exit Cap Rate | AA15 | 5.00% |
| Sales Cost % | Z17 | 1.00% |

---

## 3. Escalation Factors

### 3.1 Rent Escalation (Row 2)

**Formula (Column L):**
```excel
=IF(L$10<=$E2, K2*(1+$D$2/12), K2*(1+$F$2/12))
```

**Logic:** Monthly compounding at the rent growth rate.
- Before stabilization: uses pre-stabilization rate (D2)
- After stabilization: uses post-stabilization rate (F2)

**Initial Value (K2):** 1.0

**Growth:** 2.5% annual = (1 + 0.025/12) per month = 1.002083 monthly multiplier

### 3.2 Expense Escalation (Row 3)

**Formula (Column L):**
```excel
=IF(L$10<=$E3, K3*(1+$D3)^(1/12), K3*(1+$F3)^(1/12))
```

**Logic:** Annual rate applied monthly using nth root.
- Escalation factor = (1 + annual_rate)^(1/12) per month

**Initial Value (K3):** 1.0

**Growth:** 2.5% annual = (1.025)^(1/12) = 1.002060 monthly multiplier

### 3.3 Property Tax Escalation (Row 4)

**Formula (Column L):**
```excel
=IF(AND(L$10>1, MOD(L$10-1,12)=0), K4*(1+$F4), K4)
```

**Logic:** Step increase once per year (every 12 months).

### 3.4 Cost Escalation (Row 5)

**Formula (Column L):**
```excel
=$K5*(1+$F5)^(L$10/12)
```

**Logic:** Continuous escalation from base.

---

## 4. Revenue Calculations

### 4.1 Tenant Base Rent (Rows 46-48)

**Formula (Generic for all tenants):**
```excel
=IF(period=0, 0,
   IF(period <= lease_end_month,
      RSF * in_place_rent_psf * rent_escalation / 12 / 1000,
      IF(period > lease_end_month + TI_buildout,
         RSF * market_rent_psf * rent_escalation / 12 / 1000,
         0)))
```

**Space A (Row 46) - No Rollover Costs (H=1):**
```excel
=IF(K$10=0, 0,
   IF(K$10<=$F46,
      $E46*$G46*Model!K$2/12/1000,
      IF(K$10>$F46,
         Model!$E46*Model!$H46*Model!K$2/12/1000,
         0)))
```

**Space B (Row 47) - With Rollover Costs (H=0):**
```excel
=IF(K$10=0, 0,
   IF(K$10<=$F47,
      $E47*$G47*Model!K$2/12/1000,
      IF(K$10>$F47+Assumptions!$T$49,
         Model!$E47*Model!$H47*Model!K$2/12/1000,
         0)))
```

**Variables:**
- `$E46-48`: RSF (tenant square footage)
- `$F46-48`: Lease end month
- `$G46-48`: In-place rent PSF
- `$H46-48`: Market rent PSF
- `K$2`: Rent escalation factor for period
- `Assumptions!$T$49`: TI buildout months (6)

### 4.2 Free Rent Deductions (Rows 49-51)

**Formula:**
```excel
=IF(AND(period < free_rent_end, period >= free_rent_start, H=0), -base_rent, 0)
```

**Actual Formula (Row 49):**
```excel
=+IF(AND(K$10<$G49, K$10>=$E49, $H49=0), -K46, 0)
```

**Variables:**
- `$E49`: Free rent start month (= lease_end + TI_buildout + 1)
- `$G49`: Free rent end month (= start + free_rent_months)
- `$H49`: Rollover flag (0 = apply free rent, 1 = skip)
- `K46`: Base rent for the period

### 4.3 Parking Income (Row 52)

**Formula:**
```excel
=+$F52*$G52/1000*K$2
```

**Variables:**
- `$F52`: Number of stalls
- `$G52`: Monthly rate per stall
- `K$2`: Rent escalation factor

### 4.4 Storage Revenue (Row 53)

**Formula:**
```excel
=$F53*$G53/1000*K$2
```

**Variables:**
- `$F53`: Number of units
- `$G53`: Monthly rate per unit
- `K$2`: Rent escalation factor

### 4.5 Reimbursement Revenue - Fixed (Row 54)

**Formula:**
```excel
=SUM(K61, K65)
```

**Logic:** Sum of Fixed OpEx and Property Tax (both reimbursable under NNN).

### 4.6 Reimbursement Revenue - Variable (Row 55)

**Formula:**
```excel
=+SUM(K62:K64)
```

**Logic:** Sum of Variable OpEx, Parking Expense, and Management Fee.

### 4.7 Total Potential Revenue (Row 56)

**Formula:**
```excel
=+SUM(K46:K55)
```

**Components:**
- Rows 46-48: Base rent (3 tenants)
- Rows 49-51: Free rent deductions (3 tenants)
- Row 52: Parking income
- Row 53: Storage revenue
- Row 54: Fixed reimbursements
- Row 55: Variable reimbursements

### 4.8 General Vacancy (Row 57)

**Formula:**
```excel
=+-$F57*SUM(K$46:K$55)
```

**Logic:** Vacancy percentage applied to total potential revenue.

### 4.9 Collection Loss (Row 58)

**Formula:**
```excel
=+-$F58*SUM(K$46:K$53)
```

**Logic:** Collection loss applied to rental income only (excludes reimbursements).

### 4.10 Effective Retail Revenue (Row 59)

**Formula:**
```excel
=+SUM(K56:K58)
```

**Logic:** Total Potential Revenue + Vacancy + Collection Loss (vacancy/loss are negative).

---

## 5. Operating Expense Calculations

### 5.1 Fixed Operating Expenses (Row 61)

**Formula:**
```excel
=IF(K$10=0, 0, $F61*SUM($E$46:$E$48)/12/1000*K$3)
```

**Variables:**
- `$F61`: Fixed OpEx PSF ($36.00)
- `SUM($E$46:$E$48)`: Total RSF (9,932)
- `K$3`: Expense escalation factor

**Calculation:** $36.00 × 9,932 SF / 12 / 1000 × escalation = ~$29.8K/month base

### 5.2 Variable Operating Expenses (Row 62)

**Formula:**
```excel
=IF(K$10=0, 0, $F62*SUM($E$46:$E$48)/12/1000*K$3)
```

**Variables:**
- `$F62`: Variable OpEx PSF ($6.11)
- Same structure as Fixed OpEx

### 5.3 Parking Expense (Row 63)

**Formula:**
```excel
=+$F63*K52
```

**Logic:** Percentage of parking income (expense offset).

### 5.4 Management Fees (Row 64)

**Formula:**
```excel
=IF(Assumptions!$C$1=0, 0, +$F64*K59)
```

**Variables:**
- `$F64`: Management fee percentage (4%)
- `K59`: Effective retail revenue

### 5.5 Property Taxes (Row 65)

**Formula:**
```excel
=IF(Assumptions!$C$1=0, 0,
   IF(AND(K$10<$G65+12, K$10>=$G65),
      $F65/12,
      IF(MOD(K$10-$G65,12)=0,
         J65*(1+$F4),
         J65)))
```

**Logic:**
- First 12 months after start: Base annual tax / 12
- Every 12 months thereafter: Previous month × (1 + tax escalation)
- Other months: Same as previous month

**Variables:**
- `$F65`: Annual property tax ($622.5K)
- `$G65`: Tax start month
- `$F4`: Tax escalation rate

### 5.6 CapEx Reserves (Row 66)

**Formula:**
```excel
=+$F66*SUM($E$46:$E$48)*K$3/1000/12
```

**Variables:**
- `$F66`: CapEx reserve PSF ($5.00)
- `SUM($E$46:$E$48)`: Total RSF
- `K$3`: Expense escalation

### 5.7 Total Operating Expenses (Row 67)

**Formula:**
```excel
=+SUM(K61:K66)
```

**Components:** Fixed OpEx + Variable OpEx + Parking Expense + Mgmt Fee + Property Tax + CapEx

---

## 6. NOI Calculations

### 6.1 Retail Potential NOI (Row 69)

**Formula:**
```excel
=+K59-K67
```

**Logic:** Effective Revenue - Total Operating Expenses

### 6.2 Total Actual NOI (Row 72)

**Formula:**
```excel
=+IF(K$10<=Assumptions!$L$9, Model!K71, 0)
```

**Logic:** NOI is only recognized within the hold period.

---

## 7. Exit Value Calculations

### 7.1 Forward NOI (Assumptions!AA14)

**CRITICAL FORMULA:**
```excel
=IFERROR(SUM(OFFSET(Model!K69,0,Assumptions!X13+1,1,12)) +
         SUM(OFFSET(Model!K66,0,Assumptions!X13+1,1,12)), 0)
```

**Logic:** Sum of:
1. **Row 69 (NOI):** Months 121-132 (forward 12 months)
2. **Row 66 (CapEx):** Months 121-132 (ADD BACK for valuation)

**Important:** CapEx is added back because the buyer will establish their own reserves.

**Value:** $3,079.84K

### 7.2 Gross Exit Value (Assumptions!AA16)

**Formula:**
```excel
=IFERROR(+AA14/AA15, 0)
```

**Logic:** Forward NOI / Exit Cap Rate = $3,079.84K / 5.00% = $61,596.78K

### 7.3 Sales Costs (Assumptions!AA17)

**Formula:**
```excel
=+-Z17*AA16
```

**Logic:** Sales Cost % × Gross Value = 1.00% × $61,596.78K = $615.97K

### 7.4 Net Exit Proceeds (Assumptions!AA18)

**Formula:**
```excel
=SUM(AA16:AA17)
```

**Logic:** Gross Value - Sales Costs = $61,596.78K - $615.97K = $60,980.82K

### 7.5 Net Exit Proceeds (Model Row 74)

**Formula:**
```excel
=+IF(K10=Assumptions!$X$13, Assumptions!$AA$18, 0)
```

**Logic:** Exit proceeds only appear in the exit month (Month 120).

---

## 8. Debt Service Calculations

### 8.1 Interest Rate (Row 116)

**Formula:**
```excel
=IF($G$114=1, SUM(K114:K115), K115)
```

**Logic:**
- If floating rate (G114=1): SOFR + Spread
- If fixed rate: Just the fixed spread/rate

### 8.2 Interest Expense (Row 122)

**CRITICAL FORMULA:**
```excel
=IF(Assumptions!$C$1=0, 0,
    AVERAGE(L119, L119+L120) * L116 * (L12-K12)/365)
```

**Logic:** Uses AVERAGE of beginning and ending balance × rate × (actual days / 365)

**Components:**
- `L119`: Beginning balance
- `L120`: Debt draws (if any)
- `L116`: Effective interest rate
- `(L12-K12)`: Days in month (actual/365)

### 8.3 Amortization (Row 121)

**Formula:**
```excel
=IF(AND(K10>$G$121, K10<Assumptions!$L$9),
    INDEX(Debt!$G$8:$G$67, MATCH(K$10, Debt!$C$8:$C$67, 0)),
    0)
```

**Logic:** During amortization period, looks up principal payment from Debt tab.

### 8.4 Total Debt Service (Row 123)

**Formula:**
```excel
=SUM(K121:K122)
```

**Logic:** Amortization + Interest

### 8.5 Capitalized Interest (Row 125)

**Formula:**
```excel
=IF(Assumptions!$C$1=0, 0, SUM(K123:K124))
```

**Logic:** Debt service that isn't paid from NOI gets capitalized.

### 8.6 Ending Balance (Row 127)

**Formula:**
```excel
=+K119+K120+K126-K121
```

**Logic:** Beginning + Draws + Paydown - Amortization

---

## 9. Cash Flow Calculations

### 9.1 Unleveraged Cash Flow (Row 81)

**Formula:**
```excel
=+IF(K$10<=Assumptions!$L$9, SUM(K74,K72,-K43), 0)
```

**Components:**
- `K74`: Exit proceeds (only in exit month)
- `K72`: NOI
- `-K43`: Less total unlevered costs

### 9.2 Unleveraged IRR (Row 85)

**Formula:**
```excel
=XIRR(K81:KZ81, K12:KZ12)
```

**Logic:** XIRR of unleveraged cash flows using actual dates.

### 9.3 Leveraged Cash Flow (Row 186)

**Formula:**
```excel
=SUM(K177:K185)
```

**Components:**
- Row 177: Unleveraged Cash Flow
- Row 178: + Construction Loan Draws
- Row 179: + Perm Loan Draws
- Row 180: - Construction Loan Debt Service
- Row 181: - Perm Loan Debt Service
- Row 182: - Construction Loan Closing Costs
- Row 183: - Perm Loan Closing Costs
- Row 184: - Construction Loan Principal Paydown
- Row 185: - Perm Loan Principal Paydown

### 9.4 Leveraged IRR (Row 190)

**Formula:**
```excel
=(1+IRR(K186:EN186, 0.01))^12-1
```

**Logic:** Monthly IRR annualized.

---

## 10. Waterfall Distribution Calculations

### 10.1 Structure Overview

The waterfall has 3 hurdles:

| Hurdle | Pref Rate | LP Split | GP Split | GP Promote |
|--------|-----------|----------|----------|------------|
| I | 5% | 90% | 10% | Calculated |
| II | 5% | 75% | 8.33% | 16.67% |
| III | 5% | 75% | 8.33% | 16.67% |

### 10.2 Equity Investment (Row 11)

**Formula:**
```excel
=MIN(Model!L186, 0)
```

**Logic:** Negative cash flows represent equity contributions.

### 10.3 Cash Flow to Equity (Row 13)

**Formula:**
```excel
=MAX(0, Model!L186) - L12
```

**Logic:** Positive cash flow less asset management fee.

### 10.4 Cash Flow Available for Hurdle I (Row 28)

**Formula:**
```excel
=+L13+L19+L25
```

**Components:**
- Cash Flow to Equity
- LP Equity Paydown
- Sponsor Equity Paydown

### 10.5 Hurdle I Accrual (Row 32 for LP, Row 43 for Sponsor)

**Formula:**
```excel
=+L31*$H32
```

**Logic:** Beginning balance × pref rate (monthly)

### 10.6 Hurdle I Pref Payment (Row 36)

**Formula:**
```excel
=-MIN(SUM(L34:L35), L$28*$H36)
```

**Logic:** Minimum of available cash and accrued pref × LP share.

### 10.7 Sponsor Promote (Row 50)

**Formula:**
```excel
=-(L36+L47)/SUM($H36+$H47)*$H50
```

**Logic:** Promote based on pref payments to LP and Sponsor.

### 10.8 LP IRR Calculation

**Source:** Waterfall!I139 (referenced in Assumptions!AA7)

### 10.9 GP IRR Calculation

**Source:** Waterfall!I142 (referenced in Assumptions!AA10)

---

## 11. Lease Commission Calculations

### 11.1 LCs Tab Structure

| Row | Column | Description |
|-----|--------|-------------|
| 3 | D | SF (from Assumptions) |
| 4 | D | Rent PSF (Market/12 for monthly) |
| 6 | D | Months Abated |
| 8 | D | Lease Term |
| 9 | D | Annual Growth Rate |
| 10 | D | LC % Years 1-5 (6%) |
| 11 | D | LC % Years 6+ (3%) |
| 16-25 | B-O | Year-by-year calculation |

### 11.2 Annual Rent Calculation (Column D)

**Year 1:**
```excel
=+D3*D4*12
```

**Year 2+:**
```excel
=IF(B17>D8, 0, D16*(1+D9)^(B17-1))
```

**Logic:** Annual rent = Year 1 rent × (1 + growth)^(year-1)

### 11.3 Net Rent (Column G)

**Formula:**
```excel
=IF(D5=1, D16*((12-E16)/12), D16-F16)
```

**Logic:** Adjusts for abated months in Year 1.

### 11.4 LC Amount (Column I)

**Formula:**
```excel
=$G16*H16
```

**Logic:** Net Rent × LC %

**LC %:**
- Years 1-5: 6% (H16=D10)
- Years 6+: 3% (H21=D11)

### 11.5 Total LC (Column O)

**Formula:**
```excel
=SUM(O16:O25)
```

**Logic:** Sum of all year LC amounts / SF.

---

## 12. Formula Dependency Map

### 12.1 Revenue Flow

```
Assumptions (Tenant Data)
    ↓
Model Row 46-48 (Base Rent)
    ↓
Model Row 49-51 (Free Rent Deductions)
    ↓
Model Row 52-53 (Parking/Storage)
    ↓
Model Row 54-55 (Reimbursements) ← Model Row 61-66 (Expenses)
    ↓
Model Row 56 (Total Potential Revenue)
    ↓
Model Row 57-58 (Vacancy/Collection Loss)
    ↓
Model Row 59 (Effective Revenue)
```

### 12.2 NOI Flow

```
Model Row 59 (Effective Revenue)
    ↓
Model Row 61-66 (Operating Expenses)
    ↓
Model Row 67 (Total Operating Expenses)
    ↓
Model Row 69 (Retail NOI)
    ↓
Model Row 72 (Total Actual NOI)
```

### 12.3 Exit Value Flow

```
Model Row 69 (NOI, Months 121-132)
    +
Model Row 66 (CapEx, Months 121-132)
    ↓
Assumptions AA14 (Forward NOI)
    ↓
Assumptions AA15 (Exit Cap Rate)
    ↓
Assumptions AA16 (Gross Exit Value)
    ↓
Assumptions AA17 (Sales Costs)
    ↓
Assumptions AA18 (Net Exit Proceeds)
    ↓
Model Row 74 (Exit Proceeds in Month 120)
```

### 12.4 Cash Flow Flow

```
Model Row 72 (NOI)
    +
Model Row 74 (Exit Proceeds)
    -
Model Row 43 (Unlevered Costs)
    ↓
Model Row 81 (Unleveraged Cash Flow)
    ↓
Model Row 85 (Unleveraged IRR via XIRR)
```

### 12.5 Leveraged Flow

```
Model Row 81 (Unleveraged CF)
    +
Model Row 120 (Debt Draws)
    -
Model Row 123 (Debt Service)
    -
Model Row 96 (Loan Closing Costs)
    +
Model Row 126 (Principal Paydown)
    ↓
Model Row 186 (Leveraged Cash Flow)
    ↓
Model Row 190 (Leveraged IRR)
    ↓
Waterfall Tab (Distribution)
    ↓
Waterfall Row 139 (LP IRR)
Waterfall Row 142 (GP IRR)
```

---

## 13. Implementation Notes

### 13.1 Critical Formulas to Match

1. **Rent Escalation:** `(1 + rate/12)^period` - monthly compounding
2. **Expense Escalation:** `(1 + rate)^(period/12)` - annual rate applied monthly
3. **Interest:** `AVERAGE(begin, begin+draws) × rate × days/365`
4. **Forward NOI:** Include CapEx add-back
5. **Free Rent:** Negative deduction line, controlled by H column flag

### 13.2 Known Differences from PRD

| Item | PRD Value | Actual Excel Value |
|------|-----------|-------------------|
| Closing Costs | $950K | $500K |
| LTC | 55.5% | 40% |
| Loan Amount | $23,535K | $16,937K |
| Space A Lease End | 83 | 69 (Dec 2031) |

### 13.3 Test Benchmarks

| Metric | Excel Value | Tolerance |
|--------|-------------|-----------|
| Unleveraged IRR | 8.57% | ±0.30% |
| Leveraged IRR | 10.09% | ±0.30% |
| LP IRR | 9.39% | ±0.30% |
| GP IRR | 15.02% | ±0.30% |
| Month 1 NOI | $158.97K | ±$0.5K |
| Month 1 Interest | $73.09K | ±$0.5K |
| Month 120 NOI | $247.80K | ±$0.5K |
| Forward NOI | $3,079.84K | ±$5K |
| Exit Proceeds | $60,980.82K | ±$50K |

---

## Appendix A: Cell Reference Quick Lookup

### Assumptions Tab

| Cell | Description | Value |
|------|-------------|-------|
| C13 | Purchase Price | $41,500K |
| C14 | Closing Costs | $500K |
| J15 | Fixed Interest Rate | 5.25% |
| L18 | I/O Period | 120 months |
| L23 | LTC | 40% |
| L24 | Loan Amount | $16,937K |
| T49 | TI Buildout | 6 months |
| T50 | Free Rent | 10 months |
| T54 | Fixed OpEx PSF | $36.00 |
| T56 | Mgmt Fee % | 4% |
| T57 | Property Tax | $622.5K |
| T59 | CapEx PSF | $5.00 |
| AA14 | Forward NOI | $3,079.84K |
| AA15 | Exit Cap Rate | 5% |
| AA18 | Net Exit Proceeds | $60,980.82K |
| AE8-10 | Tenant RSF | 2300, 1868, 5950 |
| AF8-10 | In-Place Rent | $201.45, $200.47, $187.65 |
| AH8-10 | Market Rent | $300 (all) |
| AN8-10 | Annual Bumps | 2.5% (all) |

### Model Tab

| Cell | Description |
|------|-------------|
| K2 | Rent escalation base (1.0) |
| K3 | Expense escalation base (1.0) |
| K10 | Month 0 |
| K12 | Acquisition date |
| K46-48 | Base rent by tenant |
| K49-51 | Free rent deductions |
| K59 | Effective revenue |
| K67 | Total operating expenses |
| K69 | Retail NOI |
| K72 | Total actual NOI |
| K74 | Exit proceeds |
| K81 | Unleveraged cash flow |
| I85 | Unleveraged IRR |
| K122 | Interest expense |
| K186 | Leveraged cash flow |
| I190 | Leveraged IRR |

---

*Document generated: 2026-01-17*
*Source: 225 Worth Ave_Model(revised).xlsx*
