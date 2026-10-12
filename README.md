# BakeSync - Bakery POS, Inventory & Financial Management

A desktop application built with PyQt6 and SQLite for running a bakery: point of sale, inventory, recipes and costing, waste control, sales history, finance, reports, user accounts, an audit log and backups. The app is written for non-technical staff: simple English, icons with short (i) explanations, and one-click quick actions.

## Features

### Main sidebar
| Module | What it does |
|--------|--------------|
| **Dashboard** | Today at a glance: sales, profit, customers, waste, hourly chart, a to-do list, bread left and best sellers |
| **POS** | Cashier screen: one-click Fast Pay (exact or a bill), change shown with a 10 second Undo, held orders, discounts, voids with a reason |
| **Inventory** | Bread and retail products only: add items, add stock after baking or delivery, batches with expiry dates |
| **Pricing** | Enter the puhunan (cost) and the patong (markup in pesos or %); the selling price and tubo (profit) are worked out. Archived products can be restored |
| **Waste Control** | Today's Bread: how many were stocked, sold, wasted and left unsold today; waste history and performance |
| **Sales** | Sales, profit, waste and average sale for any period, a chart, highlights, best sellers and day or month breakdown; PDF and Excel export |

### Settings
Administrators see everything below. Managers see Finance and Reports only.
| Module | What it does |
|--------|--------------|
| **User Management** | Approve sign-ups, assign roles, reset passwords, archive accounts |
| **Finance** | Summary, cash count (with filters), expenses by category, voids and refunds by reason |
| **Reports** | One period at a time: key numbers, sales by day, busy hours, products, cashiers, money summary and highlights; PDF and Excel export |
| **Audit Log** | Tamper-evident record (hash chain) of sign-ins, price changes, voids, account changes and more, grouped by day |
| **Backup** | Automatic daily backup (last 14 kept), back up now, copy to a USB drive, restore from a file |
| **Store Hours** | Weekly opening hours, closed days and a closing reminder |

Cashier and Baker accounts cannot open Settings.

After 3 wrong passwords an account is locked for 5 minutes (this survives restarting the app). An Administrator resetting the password unlocks it. Admin PINs and mastery keys are stored hashed, like passwords.

## Running the App

### Option A: the packaged app (no Python needed)
Open **`release/BakeSync.lnk`**, or `release/BakeSync/BakeSync.exe`.

The `release/BakeSync/` folder is self-contained: copy the whole folder to another Windows PC and it runs there. Double-click **`Create Desktop Shortcut.bat`** inside it to put a BakeSync icon on that PC's desktop.

### Option B: from source (for development)
Requires **Python 3.10+**.

```bash
pip install -r requirements.txt
python run.py
```

## Building BakeSync.exe

```bash
pip install pyinstaller
packaging\build.bat
```

The build puts the finished app in `release/BakeSync/` and creates the `release/BakeSync.lnk` shortcut. On the **first** build it copies `data/bakesync.db` and the product photos into the app. On later builds the app's own `release/BakeSync/data/` folder is **never overwritten**, so rebuilding is safe.

> The packaged app and the source code each have their own `data/` folder. `release/BakeSync/data/` is the real shop data once you start using the .exe.

## Default Accounts

A fresh database is created with these accounts. On the **first login** each one must set its own password (BakeSync asks automatically). The same happens after an Administrator resets someone's password.

| Username | Password | Role |
|----------|----------|------|
| admin | password123 | Administrator |
| baker | password123 | Baker |
| cashier | password123 | Cashier |

New users can also sign up from the login screen; their accounts stay *Pending* until an Administrator approves them in User Management.

Passwords are stored hashed (PBKDF2-SHA256 with a per-user salt). New passwords need at least 8 characters with uppercase and lowercase letters, a number and a special character.

## Configuration

Secrets are **not** stored in the source code. Copy `config.example.json` to `config.local.json` (ignored by git) and fill it in, or set the same names as environment variables (environment variables win). Put `config.local.json` in the project root when running from source, or next to `BakeSync.exe` for the packaged app.

| Setting | Purpose |
|---------|---------|
| `BAKESYNC_SMTP_EMAIL` | Gmail address that sends password-reset codes |
| `BAKESYNC_SMTP_PASSWORD` | Gmail **App Password** for that address (not the normal password) |
| `BAKESYNC_DB` | Database file inside `data/` to open. Default `bakesync.db`; use `bakesync_demo.db` for demo data |

Without the SMTP settings the app still runs, but "Forgot Password" emails will not send. The environment variable `BAKESYNC_DATA_DIR` can point the app at a different data folder.

## Project Structure

```
BakeSync/
├── run.py                       # Start from source: python run.py
├── bakesync/                    # Application code (Python package)
│   ├── main.py                  # Main window, sidebar, page switching
│   ├── paths.py                 # Every file location (source vs. packaged .exe)
│   ├── core/                    # database.py, auth_utils.py, app_config.py
│   ├── auth/                    # login, sign-up, admin registration, forgot password
│   ├── modules/                 # dashboard, pos, inventory, recipe, quality_control, sales,
│   │                            # settings, financial, reports, user_management, profile,
│   │                            # audit_logs, backup
│   └── widgets/                 # Shared dialogs and alerts
├── assets/images/               # Icons and logos (bundled into the .exe)
├── data/                        # User data, not in git (auto-created)
│   ├── bakesync.db              # Live database
│   ├── bakesync_demo.db         # Demo database with sample sales
│   ├── backups/                 # Backups made from Settings
│   ├── product_images/          # Product photos
│   └── cache/                   # Temporary images
├── tools/                       # Demo-data scripts + bakesync_console.bat
├── packaging/                   # build.bat, BakeSync.spec, app icon
├── release/                     # Built app (BakeSync/ + BakeSync.lnk), not in git
├── config.example.json
└── requirements.txt
```

## Demo Data

The scripts in `tools/` generate sample products, sales, waste and reconciliation records. They **only write to `data/bakesync_demo.db`**, never the live database. `inject_90_days_data.py` deletes the existing sales history in the demo database before generating new data.

```bash
python tools/inject_90_days_data.py
```

To run the app against the demo data, set `"BAKESYNC_DB": "bakesync_demo.db"` in `config.local.json`.

### Clearing practice data before going live

`tools/clear_test_data.py` deletes sales, POS sessions, reconciliations, waste logs, expenses, voids and audit logs, but keeps accounts, products, ingredients, recipes and stock. It shows what will be deleted, asks you to type `YES`, and saves a backup first. Close BakeSync before running it.

```bash
python tools/clear_test_data.py
```

With no argument it cleans the packaged app's database (`release/BakeSync/data/bakesync.db`); pass a path to clean another one.

## Backups

Use **Settings → Backup & Restore**. Restoring always makes a `pre_restore` safety copy first and then closes the app so every screen reloads. Backups are plain SQLite files in `data/backups/`, so you can also copy them to a USB drive or cloud folder.

To reset everything, close the app and delete `data/bakesync.db`. A new empty database with the default accounts is created on the next start.

## Troubleshooting

The packaged app has no console window; errors are written to `data/bakesync.log` inside the app folder.

## Known Limitations

- Single computer, single user at a time (SQLite file, no server).
- Sales History has CSV export only; PDF export is available in Reports Config.
- All dates and times use the computer's clock and time zone, so set the PC to the correct Philippine time.

## Version

v1.0 (Pilot Build) - Internal Use Only
