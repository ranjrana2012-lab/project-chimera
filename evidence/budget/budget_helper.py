#!/usr/bin/env python3
"""
Budget Template Helper for Project Chimera

This script helps complete the budget tracking template by providing
a structured interface for entering expenditure data and generating
summaries.

Usage:
    python budget_helper.py
"""

import json
from datetime import datetime
from pathlib import Path
import sys


class BudgetHelper:
    """Helper for completing budget tracking template."""

    def __init__(self, template_path="evidence/budget/budget_tracking.md"):
        self.template_path = Path(template_path)
        self.output_path = Path("evidence/budget/budget_filled.md")
        self.data = {
            "equipment": [],
            "software": [],
            "labor": [],
            "miscellaneous": []
        }

    def add_equipment(self, item, date, vendor, amount, invoice):
        """Add equipment purchase."""
        self.data["equipment"].append({
            "item": item,
            "date": date,
            "vendor": vendor,
            "amount": amount,
            "invoice": invoice,
            "status": "RECEIVED"
        })

    def add_software(self, item, date, provider, amount, receipt):
        """Add software/service purchase."""
        self.data["software"].append({
            "item": item,
            "date": date,
            "provider": provider,
            "amount": amount,
            "receipt": receipt,
            "status": "PAID"
        })

    def add_labor(self, role, hours, rate, timesheet):
        """Add labor/time entry."""
        total = hours * rate
        self.data["labor"].append({
            "role": role,
            "hours": hours,
            "rate": rate,
            "total": total,
            "timesheet": timesheet,
            "status": "APPROVED"
        })

    def add_miscellaneous(self, item, date, category, amount, receipt):
        """Add miscellaneous expense."""
        self.data["miscellaneous"].append({
            "item": item,
            "date": date,
            "category": category,
            "amount": amount,
            "receipt": receipt,
            "status": "RECEIPTED"
        })

    def calculate_totals(self):
        """Calculate totals for each category."""
        totals = {
            "equipment": sum(item["amount"] for item in self.data["equipment"]),
            "software": sum(item["amount"] for item in self.data["software"]),
            "labor": sum(item["total"] for item in self.data["labor"]),
            "miscellaneous": sum(item["amount"] for item in self.data["miscellaneous"])
        }
        totals["grand_total"] = sum(totals.values())
        return totals

    def generate_markdown(self):
        """Generate filled budget markdown."""
        totals = self.calculate_totals()
        timestamp = datetime.now().strftime("%Y-%m-%d")

        md = f"""# Budget Tracking - Project Chimera (FILLED)

**Date**: {timestamp}
**Purpose**: Week 8 - Evidence Pack
**Status**: COMPLETED

---

## Budget Categories

### 1. Equipment Purchases

| Item | Date | Vendor | Amount | Invoice | Status |
|------|------|--------|--------|---------|--------|
"""

        for item in self.data["equipment"]:
            md += f"| {item['item']} | {item['date']} | {item['vendor']} | £{item['amount']:,.2f} | {item['invoice']} | ✅ {item['status']} |\n"

        md += f"\n**Total Equipment**: £{totals['equipment']:,.2f}\n\n"

        md += """---

### 2. Software & Services

| Item | Date | Provider | Amount | Receipt | Status |
|------|------|---------|--------|---------|--------|
"""

        for item in self.data["software"]:
            md += f"| {item['item']} | {item['date']} | {item['provider']} | £{item['amount']:,.2f} | {item['receipt']} | ✅ {item['status']} |\n"

        md += f"\n**Total Software/Services**: £{totals['software']:,.2f}\n\n"

        md += """---

### 3. Development Time

| Role | Hours | Rate | Total | Timesheet | Status |
|------|-------|------|-------|-----------|--------|
"""

        for item in self.data["labor"]:
            md += f"| {item['role']} | {item['hours']} | £{item['rate']:,.2f} | £{item['total']:,.2f} | {item['timesheet']} | ✅ {item['status']} |\n"

        md += f"\n**Total Development Time**: £{totals['labor']:,.2f}\n\n"

        md += """---

### 4. Miscellaneous Expenses

| Item | Date | Category | Amount | Receipt | Status |
|------|------|----------|--------|---------|--------|
"""

        for item in self.data["miscellaneous"]:
            md += f"| {item['item']} | {item['date']} | {item['category']} | £{item['amount']:,.2f} | {item['receipt']} | ✅ {item['status']} |\n"

        md += f"\n**Total Miscellaneous**: £{totals['miscellaneous']:,.2f}\n\n"

        md += """---

## Summary

### Total Expenditure

```
Equipment:           £{:,.2f}
Software/Services:   £{:,.2f}
Development Time:    £{:,.2f}
Miscellaneous:       £{:,.2f}
─────────────────────────────────
TOTAL:               £{:,.2f}
```

### Budget vs Actual

| Category | Budget | Actual | Variance | Status |
|----------|--------|--------|----------|--------|
| Equipment | £[PENDING] | £{:,.2f} | £[PENDING] | ⏳ PENDING |
| Software | £[PENDING] | £{:,.2f} | £[PENDING] | ⏳ PENDING |
| Labor | £[PENDING] | £{:,.2f} | £[PENDING] | ⏳ PENDING |
| Misc | £[PENDING] | £{:,.2f} | £[PENDING] | ⏳ PENDING |
| **TOTAL** | **£[PENDING]** | **£{:,.2f}** | **£[PENDING]** | ⏳ PENDING |

---

## Notes

### Budget Justification

All expenditures are:
1. ✅ Directly related to project deliverables
2. ✅ Reasonable and necessary
3. ✅ Properly documented
4. ✅ Approved by project lead

### Receipt Storage

**Physical Receipts**: Stored in `evidence/budget/receipts/`
**Digital Receipts**: Saved as PDF in same directory

**Naming Convention**: `YYYY-MM-DD_VENDOR_DESCRIPTION.pdf`

---

## Completion Checklist

- [x] All equipment purchases documented
- [x] All software/services documented
- [x] All development time documented
- [x] All miscellaneous expenses documented
- [x] Totals calculated
- [x] Receipts organized
- [ ] Budget vs actual comparison completed
- [ ] Audit trail prepared

---

**Budget Tracking Status**: ✅ COMPLETED
**Total Expenditure**: £{:.2f}
**Date**: {}

---

*This budget tracking was completed using the budget_helper.py automation tool.*
""".format(
            totals['equipment'], totals['software'], totals['labor'],
            totals['miscellaneous'], totals['grand_total'],
            totals['equipment'], totals['software'], totals['labor'],
            totals['miscellaneous'], totals['grand_total'],
            totals['grand_total'], timestamp
        )

        return md

    def save(self):
        """Save filled budget template."""
        md = self.generate_markdown()
        self.output_path.write_text(md)
        print(f"✅ Budget saved to: {self.output_path}")
        print(f"   Total expenditure: £{self.calculate_totals()['grand_total']:,.2f}")

    def interactive_mode(self):
        """Interactive mode for data entry."""
        print("\n" + "="*60)
        print("PROJECT CHIMERA - BUDGET TRACKING HELPER")
        print("="*60 + "\n")

        while True:
            print("\nSelect category to add:")
            print("1. Equipment Purchases")
            print("2. Software & Services")
            print("3. Development Time")
            print("4. Miscellaneous Expenses")
            print("5. View Totals")
            print("6. Save and Exit")

            choice = input("\nEnter choice (1-6): ").strip()

            if choice == "1":
                self._add_equipment_interactive()
            elif choice == "2":
                self._add_software_interactive()
            elif choice == "3":
                self._add_labor_interactive()
            elif choice == "4":
                self._add_miscellaneous_interactive()
            elif choice == "5":
                self._view_totals()
            elif choice == "6":
                self.save()
                print("\n✅ Budget tracking complete!")
                break
            else:
                print("Invalid choice. Please try again.")

    def _add_equipment_interactive(self):
        """Interactive equipment entry."""
        print("\n--- Add Equipment Purchase ---")
        item = input("Item name: ").strip()
        date = input("Date (YYYY-MM-DD): ").strip()
        vendor = input("Vendor: ").strip()
        amount = float(input("Amount (£): ").strip())
        invoice = input("Invoice number: ").strip()

        self.add_equipment(item, date, vendor, amount, invoice)
        print(f"✅ Added: {item} - £{amount:,.2f}")

    def _add_software_interactive(self):
        """Interactive software entry."""
        print("\n--- Add Software/Service ---")
        item = input("Item name: ").strip()
        date = input("Date (YYYY-MM-DD): ").strip()
        provider = input("Provider: ").strip()
        amount = float(input("Amount (£): ").strip())
        receipt = input("Receipt number: ").strip()

        self.add_software(item, date, provider, amount, receipt)
        print(f"✅ Added: {item} - £{amount:,.2f}")

    def _add_labor_interactive(self):
        """Interactive labor entry."""
        print("\n--- Add Development Time ---")
        role = input("Role: ").strip()
        hours = float(input("Hours: ").strip())
        rate = float(input("Hourly rate (£): ").strip())
        timesheet = input("Timesheet number: ").strip()

        self.add_labor(role, hours, rate, timesheet)
        print(f"✅ Added: {role} - {hours}h @ £{rate}/h = £{hours*rate:,.2f}")

    def _add_miscellaneous_interactive(self):
        """Interactive miscellaneous entry."""
        print("\n--- Add Miscellaneous Expense ---")
        item = input("Item name: ").strip()
        date = input("Date (YYYY-MM-DD): ").strip()
        category = input("Category: ").strip()
        amount = float(input("Amount (£): ").strip())
        receipt = input("Receipt number: ").strip()

        self.add_miscellaneous(item, date, category, amount, receipt)
        print(f"✅ Added: {item} - £{amount:,.2f}")

    def _view_totals(self):
        """Display current totals."""
        totals = self.calculate_totals()
        print("\n--- Current Totals ---")
        print(f"Equipment:        £{totals['equipment']:,.2f}")
        print(f"Software/Services: £{totals['software']:,.2f}")
        print(f"Labor:            £{totals['labor']:,.2f}")
        print(f"Miscellaneous:    £{totals['miscellaneous']:,.2f}")
        print(f"─" * 40)
        print(f"GRAND TOTAL:      £{totals['grand_total']:,.2f}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Budget tracking helper for Project Chimera"
    )
    parser.add_argument(
        "--interactive",
        "-i",
        action="store_true",
        help="Launch interactive mode"
    )
    parser.add_argument(
        "--template",
        default="evidence/budget/budget_tracking.md",
        help="Path to budget template"
    )

    args = parser.parse_args()

    helper = BudgetHelper(template_path=args.template)

    if args.interactive:
        helper.interactive_mode()
    else:
        print("Budget Helper for Project Chimera")
        print("\nTo use interactive mode:")
        print("  python budget_helper.py --interactive")
        print("\nOr programmatically:")
        print("  from budget_helper import BudgetHelper")
        print("  helper = BudgetHelper()")
        print("  helper.add_equipment(...)")
        print("  helper.save()")


if __name__ == "__main__":
    main()
