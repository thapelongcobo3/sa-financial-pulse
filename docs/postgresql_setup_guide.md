# PostgreSQL Setup Guide — Terminal Only (WSL)
**Written by:** Thapelo  
**Environment:** WSL (Ubuntu), VS Code, PostgreSQL 18  
**Who this is for:** Anyone coming from SQLite3 who wants to use PostgreSQL properly from the terminal without touching pgAdmin

---

## Before Anything — Understand What's Actually Different

If you've used SQLite3 before, the first thing you need to understand is that PostgreSQL works completely differently. With SQLite3 your database is just a `.sqlite` file sitting in your project folder — your Python script opens it like any other file. Simple.

PostgreSQL is not a file. It's a **server** that runs in the background on your machine. Your Python scripts don't open a file — they *connect* to that server over a port, the same way a browser connects to a website. The server manages all the data and storage on its own, and you talk to it through connections.

```
SQLite3:    your script → opens a .sqlite file directly
PostgreSQL: your script → connects to a running server → server handles everything
```

This changes two things practically:
- The server has to actually be running before anything can connect to it
- You need a username and password to connect, every time

Once that clicks, everything else makes sense.

---

## Step 1 — Install PostgreSQL (once ever on this machine)

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

The `postgresql-contrib` package adds extra utilities and extensions on top of the base install. You won't need them right now but you'll want them later — just always install both together.

When it's done, confirm it worked:
```bash
psql --version
```

You should see something like `psql (PostgreSQL) 18.4`. That's it, installed.

---

## Step 2 — Start the Server (every time you open a new WSL session)

```bash
sudo service postgresql start
```

This is the step that catches people out the most. In WSL, PostgreSQL doesn't start automatically when you open your terminal. The server has to be manually started each session, otherwise nothing can connect to it — not your terminal, not Python, not anything. You'll just get a connection error and wonder what went wrong.

Check that it actually started:
```bash
sudo service postgresql status
```

Look for `Active: active` somewhere in the output. If your terminal gets stuck showing a long output and you can't type, press `q` — that exits the pager view and gives you your terminal back.

---

## Step 3 — Get Into the PostgreSQL Shell

```bash
sudo -u postgres psql
```

This opens the psql shell — the PostgreSQL equivalent of your bash terminal, except it only speaks SQL and PostgreSQL commands. When you're inside it, your prompt changes from your username to this:

```
postgres=#
```

That means you're no longer in bash. You're talking directly to PostgreSQL now.

**Why `sudo -u postgres` and not just `psql -U postgres`?**  
This one confused me at first. PostgreSQL has a security feature called peer authentication. By default it checks that the Linux user running the command matches the PostgreSQL user being used. Your Linux username is something like `thapelongcobo` — not `postgres`. So if you just run `psql -U postgres`, PostgreSQL sees a mismatch and rejects you with "Peer authentication failed." Running `sudo -u postgres psql` tells Linux to run that command *as* the postgres system user, which PostgreSQL then accepts. That's the difference.

---

## Step 4 — Set a Password (once ever)

You're now inside the psql shell. Run this:

```sql
ALTER USER postgres PASSWORD 'yourpassword';
```

Replace `yourpassword` with something you'll actually remember — your Python scripts will need this later to connect. When it works you'll see `ALTER ROLE` printed back.

**Why set a password at all?** When your Python scripts connect to PostgreSQL using psycopg2, they can't use the `sudo -u postgres` trick — they connect over a normal network connection that requires a password. No password means Python can't connect.

---

## Step 5 — Create Your Database

Still inside psql, run:

```sql
CREATE DATABASE your_database_name;
```

For this project:
```sql
CREATE DATABASE sa_financial_pulse;
```

You'll see `CREATE DATABASE` printed back confirming it worked.

**Why a separate database per project?** One PostgreSQL server can hold many databases at once — think of it like one server running many completely separate projects. Each project gets its own database, and databases don't share tables or schemas with each other. Keeping them separate means nothing bleeds across projects.

---

## Step 6 — Exit the psql Shell

```sql
\q
```

Your prompt goes back to your normal bash username. You're out of psql and back in bash.

---

## Step 7 — Write Your Schema in a SQL File

Don't type your `CREATE TABLE` statements directly into psql. Instead, create a file called `setup_db.sql` in your project root and write all your SQL in there. Here's why that matters:

1. It lives in your GitHub repo — anyone who clones your project gets the exact same database structure by running one command
2. If something breaks and you need to rebuild from scratch, you just run the file again
3. It's readable, editable, and version controlled — just like your Python scripts

The file looks like this (simplified example):

```sql
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS raw.daily_prices (
    id          SERIAL PRIMARY KEY,
    ticker      VARCHAR(20)    NOT NULL,
    trade_date  DATE           NOT NULL,
    UNIQUE (ticker, trade_date)
);

CREATE TABLE IF NOT EXISTS analytics.company_daily (
    id          SERIAL PRIMARY KEY,
    ticker      VARCHAR(20)    NOT NULL
);
```

**Why `IF NOT EXISTS` on everything?** So the file is safe to run more than once. If the schema or table already exists, it skips it instead of throwing an error. This means you can run `setup_db.sql` again after making changes and it won't break anything that already exists.

---

## Step 8 — Run the SQL File Against Your Database

```bash
sudo -u postgres psql -d your_database_name -f setup_db.sql
```

For this project:
```bash
sudo -u postgres psql -d sa_financial_pulse -f setup_db.sql
```

Breaking down what the flags do:
- `-d sa_financial_pulse` — which database to run the file against
- `-f setup_db.sql` — which SQL file to run

If everything works you'll see one confirmation line per statement:
```
CREATE SCHEMA
CREATE SCHEMA
CREATE TABLE
CREATE TABLE
CREATE TABLE
```

---

## Step 9 — Verify Everything Was Created

Check your schemas exist:
```bash
sudo -u postgres psql -d sa_financial_pulse -c "\dn"
```

Check the tables inside each schema:
```bash
sudo -u postgres psql -d sa_financial_pulse -c "\dt raw.*"
sudo -u postgres psql -d sa_financial_pulse -c "\dt analytics.*"
```

The `-c` flag means "run this one command and exit" — so you don't have to enter the psql shell just to check something quickly. The `\dn` and `\dt` are psql shortcut commands, not SQL — they just list schemas and tables respectively.

---

## The Full Sequence — Every New Project

```
1.  sudo apt install postgresql postgresql-contrib     ← once ever on this machine
2.  sudo service postgresql start                      ← every WSL session
3.  sudo -u postgres psql                              ← enter the psql shell
4.    ALTER USER postgres PASSWORD 'yourpassword';     ← once ever on this machine
5.    CREATE DATABASE your_database_name;              ← once per project
6.    \q                                               ← exit the psql shell
7.  create setup_db.sql in your project root           ← once per project
8.  sudo -u postgres psql -d your_db -f setup_db.sql  ← once per project
9.  verify with \dn and \dt commands                   ← confirm it worked
```

---

## Useful psql Commands

These are all run inside the psql shell (after `sudo -u postgres psql`):

| Command | What it does |
|---------|--------------|
| `\q` | Exit psql back to bash |
| `\l` | List all databases on the server |
| `\c dbname` | Switch to a different database |
| `\dn` | List all schemas in the current database |
| `\dt schema.*` | List all tables in a schema |
| `\d tablename` | Show a table's columns and types |
| `\i file.sql` | Run a SQL file from inside psql |

---

## How Python Connects to PostgreSQL

Once your server is running and your database and tables exist, your Python scripts connect like this using psycopg2:

```python
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="sa_financial_pulse",
    user="postgres",
    password="yourpassword"    # the password you set in Step 4
)
```

`localhost` means the server running on your own machine. Port `5432` is the default PostgreSQL port. This is exactly what pgAdmin's "connect to server" screen asks for — same information, just written in Python instead of typed into a form.

---

## Errors You Will Definitely See and What They Mean

**`Command 'psql' not found`**  
PostgreSQL isn't installed yet. Go back to Step 1.

**`connection to server failed: No such file or directory`**  
The server isn't running. Go back to Step 2 and start it.

**`FATAL: Peer authentication failed for user "postgres"`**  
You ran `psql -U postgres` from your own Linux user instead of using `sudo -u postgres psql`. Use the sudo version, or connect from Python with a password.

**`FATAL: database "name" does not exist`**  
The database hasn't been created yet, or you've got a typo. Run `sudo -u postgres psql -c "\l"` to list all databases and check what's actually there.

**Terminal is stuck and you can't type**  
You're in a pager view. Press `q` to get out.