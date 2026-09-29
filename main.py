import os
import sys
from datetime import datetime
import flet as ft
import gspread
from google.oauth2.service_account import Credentials

# Force terminal outputs to flush instantly for real-time diagnostic logging
sys.stdout.reconfigure(line_buffering=True)

# ==============================================================================
# 🚀 UNIVERSAL PORTABLE PATH ENGINE
# ==============================================================================
CURRENT_FOLDER = os.path.dirname(os.path.abspath(__file__)) if __file__ else os.getcwd()
TARGET_JSON_PATH = os.path.join(CURRENT_FOLDER, "service_account.json")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Global sheets handles to be initialized safely inside the Flet app thread
income_sheet = None
expense_sheet = None
committee_sheet = None


# ==============================================================================
# 🛕 MAIN USER INTERFACE LIFECYCLE
# ==============================================================================
def main(page: ft.Page):
    global income_sheet, expense_sheet, committee_sheet

    # Application Window Property Setup
    page.title = "🛕 Temple Income & Expenditure Tracker"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.scroll = ft.ScrollMode.AUTO
    page.theme_mode = ft.ThemeMode.LIGHT

    # Core Metric Tracking Elements (Drawn placeholder first to prevent thread freezes)
    balance_text = ft.Text(
        value="Balance: Synchronizing...",
        size=20,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.ORANGE_700,
    )
    status_snack = ft.SnackBar(ft.Text(""))

    def show_status(message, is_error=False):
        status_snack.content.value = message
        status_snack.bgcolor = ft.Colors.RED_ACCENT if is_error else ft.Colors.GREEN_700
        page.open(status_snack)

    def get_sheet_rows(sheet_obj):
        try:
            if sheet_obj is None:
                return []
            return sheet_obj.get_all_records()
        except Exception:
            return []

    def update_global_balance():
        if income_sheet is None or expense_sheet is None:
            return
        incomes = get_sheet_rows(income_sheet)
        expenses = get_sheet_rows(expense_sheet)

        total_inc = sum(float(row.get("Amount", 0) or 0) for row in incomes)
        total_exp = sum(float(row.get("Amount", 0) or 0) for row in expenses)
        net_balance = total_inc - total_exp

        balance_text.value = f"Current Cash Balance: ₹{net_balance:,.2f}"
        balance_text.color = ft.Colors.GREEN
        page.update()

    # ==============================================================================
    # 💰 FEATURE TAB 1: RECORD INCOME WORKSPACE
    # ==============================================================================
    inc_date_input = ft.TextField(
        label="Date (YYYY-MM-DD)",
        value=datetime.now().strftime("%Y-%m-%d"),
        width=300,
    )
    inc_source_dropdown = ft.Dropdown(
        label="Source Type",
        options=[
            ft.dropdown.Option("Devotee"),
            ft.dropdown.Option("Committee"),
        ],
        value="Devotee",
        width=300,
    )
    inc_name_input = ft.TextField(label="Devotee / Contributor Name", width=300)
    inc_comm_dropdown = ft.Dropdown(
        label="Select Committee Member", width=300, visible=False
    )
    inc_amount_input = ft.TextField(label="Amount (₹)", width=300)
    inc_desc_input = ft.TextField(label="Purpose / Description", width=300)

    def handle_source_change(e):
        if inc_source_dropdown.value == "Committee":
            members = get_sheet_rows(committee_sheet)
            member_names = [m.get("Name") for m in members if m.get("Name")]
            if member_names:
                inc_comm_dropdown.options = [
                    ft.dropdown.Option(name) for name in member_names
                ]
                inc_comm_dropdown.value = member_names[0]
                inc_comm_dropdown.visible = True
                inc_name_input.visible = False
            else:
                show_status(
                    "No committee members found! Add them in Tab 4 first.",
                    is_error=True,
                )
                inc_source_dropdown.value = "Devotee"
        else:
            inc_comm_dropdown.visible = False
            inc_name_input.visible = True
        page.update()

    inc_source_dropdown.on_change = handle_source_change

    def save_income(e):
        try:
            if income_sheet is None:
                show_status("Database connection offline!", is_error=True)
                return
            amt = float(inc_amount_input.value or 0)
            final_name = (
                inc_comm_dropdown.value
                if inc_source_dropdown.value == "Committee"
                else inc_name_input.value
            )

            if not final_name or amt <= 0:
                show_status(
                    "Please fill out name and enter a valid amount!",
                    is_error=True,
                )
                return

            income_sheet.append_row(
                [
                    inc_date_input.value,
                    inc_source_dropdown.value,
                    final_name,
                    amt,
                    inc_desc_input.value,
                ]
            )
            show_status("Income logged successfully!")
            inc_name_input.value = ""
            inc_amount_input.value = ""
            inc_desc_input.value = ""
            update_global_balance()
        except Exception as err:
            show_status(f"Save Error: {err}", is_error=True)

    btn_save_income = ft.Button(on_click=save_income)
    btn_save_income.content = ft.Text("Save Income Record")

    tab1_view = ft.Column(
        [
            ft.Text(
                "Log New Income / Contribution", size=18, weight=ft.FontWeight.W_600
            ),
            inc_date_input,
            inc_source_dropdown,
            inc_name_input,
            inc_comm_dropdown,
            inc_amount_input,
            inc_desc_input,
            btn_save_income,
        ],
        spacing=15,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # ==============================================================================
    # 📉 FEATURE TAB 2: RECORD EXPENSE WORKSPACE
    # ==============================================================================
    exp_date_input = ft.TextField(
        label="Date (YYYY-MM-DD)",
        value=datetime.now().strftime("%Y-%m-%d"),
        width=300,
    )
    exp_cat_dropdown = ft.Dropdown(
        label="Expense Category",
        options=[
            ft.dropdown.Option("Pooja Materials"),
            ft.dropdown.Option("Maintenance & Repairs"),
            ft.dropdown.Option("Salaries / Dakshina"),
            ft.dropdown.Option("Electricity / Utilities"),
            ft.dropdown.Option("Festivals & Events"),
            ft.dropdown.Option("Other"),
        ],
        width=300,
    )
    exp_amount_input = ft.TextField(label="Amount Spent (₹)", width=300)
    exp_desc_input = ft.TextField(
        label="Details / Voucher Information", width=300
    )

    def save_expense(e):
        try:
            if expense_sheet is None:
                show_status("Database connection offline!", is_error=True)
                return
            amt = float(exp_amount_input.value or 0)
            if not exp_cat_dropdown.value or amt <= 0:
                show_status(
                    "Please select category and enter valid spent amount!",
                    is_error=True,
                )
                return

            expense_sheet.append_row(
                [
                    exp_date_input.value,
                    exp_cat_dropdown.value,
                    amt,
                    exp_desc_input.value,
                ]
            )
            show_status("Expense logged successfully!")
            exp_amount_input.value = ""
            exp_desc_input.value = ""
            update_global_balance()
        except Exception as err:
            show_status(f"Save Error: {err}", is_error=True)

    btn_save_expense = ft.Button(on_click=save_expense)
    btn_save_expense.content = ft.Text("Save Expense Record")

    tab2_view = ft.Column(
        [
            ft.Text("Log Temple Expenditure", size=18, weight=ft.FontWeight.W_600),
            exp_date_input,
            exp_cat_dropdown,
            exp_amount_input,
            exp_desc_input,
            btn_save_expense,
        ],
        spacing=15,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )
    # ==============================================================================
    # 📊 FEATURE TAB 3: MONTHLY ACCOUNT STATEMENTS
    # ==============================================================================
    rep_month_drop = ft.Dropdown(
        label="Select Month",
        options=[ft.dropdown.Option(f"{i:02d}") for i in range(1, 13)],
        value=datetime.now().strftime("%m"),
        width=150,
    )
    rep_year_input = ft.TextField(
        label="Year (YYYY)", value=str(datetime.now().year), width=150
    )
    rep_summary_label = ft.Text(
        value="Hit generate overview to retrieve data.",
        size=16,
        weight=ft.FontWeight.BOLD,
    )
    inc_report_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Date")),
            ft.DataColumn(ft.Text("Name")),
            ft.DataColumn(ft.Text("Amount")),
        ]
    )
    exp_report_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Date")),
            ft.DataColumn(ft.Text("Category")),
            ft.DataColumn(ft.Text("Amount")),
        ]
    )

    def generate_report(e):
        if income_sheet is None or expense_sheet is None:
            show_status("Database connection offline!", is_error=True)
            return
        target_prefix = f"{rep_year_input.value}-{rep_month_drop.value}"
        incomes = get_sheet_rows(income_sheet)
        expenses = get_sheet_rows(expense_sheet)

        m_inc = [
            r for r in incomes if str(r.get("Date", "")).startswith(target_prefix)
        ]
        m_exp = [
            r for r in expenses if str(r.get("Date", "")).startswith(target_prefix)
        ]

        m_total_inc = sum(float(r.get("Amount", 0) or 0) for r in m_inc)
        m_total_exp = sum(float(r.get("Amount", 0) or 0) for r in m_exp)

        rep_summary_label.value = (
            f"Total Income: ₹{m_total_inc:,.2f}  |  "
            f"Total Expense: ₹{m_total_exp:,.2f}  |  "
            f"Net: ₹{(m_total_inc - m_total_exp):,.2f}"
        )

        inc_report_table.rows.clear()
        for r in m_inc:
            inc_report_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(r.get("Date")))),
                        ft.DataCell(ft.Text(str(r.get("Name")))),
                        ft.DataCell(ft.Text(str(r.get("Amount")))),
                    ]
                )
            )

        exp_report_table.rows.clear()
        for r in m_exp:
            exp_report_table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(r.get("Date")))),
                        ft.DataCell(ft.Text(str(r.get("Category")))),
                        ft.DataCell(ft.Text(str(r.get("Amount")))),
                    ]
                )
            )
        page.update()

    btn_gen_rep = ft.Button(on_click=generate_report)
    btn_gen_rep.content = ft.Text("Generate Accounts Overview")

    tab3_view = ft.Column(
        [
            ft.Text("Monthly Statement Generator", size=18, weight=ft.FontWeight.W_600),
            ft.Row(
                [rep_month_drop, rep_year_input],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            btn_gen_rep,
            rep_summary_label,
            ft.Text("📥 Income Breakdown:", weight=ft.FontWeight.BOLD),
            inc_report_table,
            ft.Text("📤 Expense Breakdown:", weight=ft.FontWeight.BOLD),
            exp_report_table,
        ],
        spacing=15,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # ==============================================================================
    # ⚠️ FEATURE TAB 4: COMMITTEE ROSTER & DEFICIT TRACKER
    # ==============================================================================
    comm_name_input = ft.TextField(label="Committee Member Name", width=300)
    comm_pledge_input = ft.TextField(
        label="Mandatory Monthly Pledge Amount (₹)", width=300
    )
    due_month_drop = ft.Dropdown(
        label="Target Month",
        options=[ft.dropdown.Option(f"{i:02d}") for i in range(1, 13)],
        value=datetime.now().strftime("%m"),
        width=150,
    )
    due_year_input = ft.TextField(
        label="Year (YYYY)", value=str(datetime.now().year), width=150
    )
    dues_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Member Name")),
            ft.DataColumn(ft.Text("Pledge")),
            ft.DataColumn(ft.Text("Paid")),
            ft.DataColumn(ft.Text("Pending Balance")),
        ]
    )

    def calculate_dues(e=None):
        if committee_sheet is None or income_sheet is None:
            return
        target_prefix = f"{due_year_input.value}-{due_month_drop.value}"
        members = get_sheet_rows(committee_sheet)
        incomes = get_sheet_rows(income_sheet)
        payments = {}

        for r in incomes:
            if str(r.get("Source Type")) == "Committee" and str(
                r.get("Date", "")
            ).startswith(target_prefix):
                name = r.get("Name")
                payments[name] = payments.get(name, 0.0) + float(
                    r.get("Amount", 0) or 0
                )

        dues_table.rows.clear()
        for m in members:
            name = m.get("Name")
            pledge = float(m.get("Monthly Pledge", 0) or 0)
            paid = payments.get(name, 0.0)
            balance = pledge - paid

            if balance > 0:
                dues_table.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(str(name))),
                            ft.DataCell(ft.Text(f"₹{pledge:,.2f}")),
                            ft.DataCell(ft.Text(f"₹{paid:,.2f}")),
                            ft.DataCell(
                                ft.Text(f"₹{balance:,.2f}", color=ft.Colors.RED)
                            ),
                        ]
                    )
                )
        page.update()

    def add_committee_member(e):
        try:
            if committee_sheet is None:
                return
            pledge = float(comm_pledge_input.value or 0)
            if not comm_name_input.value or pledge <= 0:
                show_status(
                    "Enter a clean name and valid pledge value!", is_error=True
                )
                return

            existing_records = committee_sheet.get_all_values()
            found_index = -1
            for idx, row in enumerate(existing_records):
                if row and row == comm_name_input.value:
                    found_index = idx + 1
                    break

            if found_index > -1:
                committee_sheet.update_cell(found_index, 2, pledge)
                show_status(f"Updated {comm_name_input.value}'s pledge settings.")
            else:
                committee_sheet.append_row([comm_name_input.value, pledge])
                show_status(f"Added member {comm_name_input.value} successfully!")

            comm_name_input.value = ""
            comm_pledge_input.value = ""
            calculate_dues(None)
        except Exception as err:
            show_status(f"Roster Error: {err}", is_error=True)

    btn_add_member = ft.Button(on_click=add_committee_member)
    btn_add_member.content = ft.Text("Add / Update Member")

    btn_calc_dues = ft.Button(on_click=calculate_dues)
    btn_calc_dues.content = ft.Text("Calculate Deficits")

    tab4_view = ft.Column(
        [
            ft.Text(
                "Manage Committee Roster & Pledges", size=16, weight=ft.FontWeight.W_600
            ),
            comm_name_input,
            comm_pledge_input,
            btn_add_member,
            ft.Divider(),
            ft.Text(
                "Committee Monthly Deficit Tracker", size=16, weight=ft.FontWeight.W_600
            ),
            ft.Row(
                [due_month_drop, due_year_input],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
            btn_calc_dues,
            dues_table,
        ],
        spacing=15,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # --------------------------------------------------------------------------
    # 🗂️ MAIN TABS NAVIGATOR & MASTER ASSEMBLY (COMPATIBLE WITH FLET 0.86.5)
    # --------------------------------------------------------------------------
    tab1 = ft.Tab()
    tab1.text="Record Income"
    tab1.content = ft.Container(content=tab1_view, padding=20)

    tab2 = ft.Tab()
    tab2.text="📉 Record Expense"
    tab2.content = ft.Container(content=tab2_view, padding=20)

    tab3 = ft.Tab()
    tab3.text="📊 Monthly Accounts"
    tab3.content = ft.Container(content=tab3_view, padding=20)

    tab4 = ft.Tab()
    tab4.text="⚠️ Pending Dues"
    tab4.content = ft.Container(content=tab4_view, padding=20)

    # ==============================================================================
    # 📑 ASSEMBLE WORKSPACE TABS (MODERN FLET v1.0+ COMPATIBLE)
    # ==============================================================================
    tabs_navigator = ft.Tabs(
        length=4,  # MANDATORY: Explicitly declare the total number of tabs
        selected_index=0,
        animation_duration=300,
        expand=1,
        content=ft.Column(
            expand=True,
            controls=[
                # The upper clickable navigation headers
                ft.TabBar(
                    tabs=[
                        ft.Tab(label="💰 Income Logger"),
                        ft.Tab(label="📉 Expense Logger"),
                        ft.Tab(label="📊 Accounts Breakdown"),
                        ft.Tab(label="⚠️ Deficit Tracker"),
                    ]
                ),
                # The actual content panels that switch dynamically
                ft.TabBarView(
                    expand=True,
                    controls=[
                        tab1_view,  # Content for Tab 0
                        tab2_view,  # Content for Tab 1
                        tab3_view,  # Content for Tab 2
                        tab4_view,  # Content for Tab 3
                    ],
                ),
            ],
        ),
    )

    # tabs_navigator = ft.Tabs(
    #     selected_index=0,
    #     animation_duration=300,
    #     expand=1,
    # )

    # tabs_navigator.controls = [tab1, tab2, tab3, tab4]

    # Render primary placeholder interface controls instantly to prevent black hangs
    page.add(
        ft.Text(
            "🛕 Temple Income & Expenditure Tracker",
            size=24,
            weight=ft.FontWeight.BOLD,
        ),
        balance_text,
        ft.Divider(),
        tabs_navigator,
    )
    page.update()

    # --------------------------------------------------------------------------
    # 🌐 POST-RENDER LAZY DATABASE HANDSHAKE INTERCEPT
    # --------------------------------------------------------------------------
    try:
        if not os.path.exists(TARGET_JSON_PATH):
            raise FileNotFoundError(
                f"Missing credential file 'service_account.json'."
            )

        creds = Credentials.from_service_account_file(TARGET_JSON_PATH)
        scoped_creds = creds.with_scopes(SCOPES)
        client = gspread.authorize(scoped_creds)

        spreadsheet = client.open("FletDataSheet")
        income_sheet = spreadsheet.worksheet("income")
        expense_sheet = spreadsheet.worksheet("expenses")
        committee_sheet = spreadsheet.worksheet("committee")
        # Hydrate financial records smoothly now that the layout is on monitor
        update_global_balance()
        calculate_dues(None)
    except Exception as sync_err:
        balance_text.value = f"Offline Sync Failure: {sync_err}"
        balance_text.color = ft.Colors.RED_700page.update()
ft.run(main)