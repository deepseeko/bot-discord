# 7YAS Wallet Bot

**7YAS Wallet Bot** is a powerful Discord bot designed to manage wallets, handle currency conversions, and facilitate gambling activities using the **7YAS coin**.

## 🚀 Features

- 💰 **Wallet Management** – Track balances and transactions.
- 🔄 **Currency Conversion** – Convert between 7YAS and ProBot credits.
- 🎰 **Gambling System** – Engage in casino-style games.
- 🔔 **send a message to members**
- 📊 **Transaction Logging** – Keep records of all exchanges.
- 🔔 **Webhook Notifications** – Get instant updates.
- !! :
```
The gambling system includes many psychological tricks that make people gamble without realizing it!

I originally created it for my friend, who was addicted to gambling and constantly betting. (99% of gamblers don’t gamble to win; they do it for the dopamine rush their body gets when they place a bet.)

So, I built this system to let him gamble but made it **easy** for him to acquire 7YAS. I set it so that **1 YAS = 1 DH**, ensuring he felt the real value of his transactions.

Over time, I gradually **made it easier** for him to obtain 7YAS, and eventually, he started noticing that gambling had become boring. **Alhamdulillah, he recovered!** i gave him back the money he had lost (obviously, he wasn’t winning, haha!).

I sincerely hope this system is **not used in any way that is haram**. Please!


```
---

## 📈 7YAS Coin Pricing

The price of **7YAS** is calculated similarly to popular cryptocurrencies like **Bitcoin, Solana, and Ethereum**.

You can control coin-related data from:

```
/data/bank_data.json
```

### JSON Structure:
```json
{
    "credits": 20000950,  // Total credits in the bank account
    "total_7yas": 670.8746518843577,  // Total 7YAS currently held by users
    "max_7yas_supply": 2000000000,  // Maximum supply of 7YAS
    "exchange_rate": 50.00000167718694  // Exchange rate (automatically calculated)
}
```

---

## ⚙️ Installation

1. **Clone the repository:**
    ```sh
    git clone https://github.com/yourusername/7YAS-Wallet-Bot.git
    cd 7YAS-Wallet-Bot
    ```

2. **Install dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

3. **Configure environment variables:**
   - Create a `.env` file in the root directory and add:
    ```env
    BANK_JSON_FILE="data/bank_data.json"
    BANK_WALLET_ID=x
    YOUR_SERVER_ID=x
    LOG_WIN_WEBHOOK="x"
    SEND7_WEBHOOK="x"
    BUY_WEBHOOK="x"
    AUCTION_WEBHOOK="x"
    WALLET_WEBHOOK="x"
    ID_CASINO=x
    LOG_CHANNEL_ID=x
    USER_TOKEN="x"
    BANK_TOKEN="x"
    TOKEN="x"
    ```

4. **Edit some data in .py files & the last line in yas.py**
	```
	"An update is coming; I'll make the setup easier! I don't have time right now."
	```

5. **Run the bot:**
    ```sh
    python yas.py
    ```
## Need Help?

📸 **Instagram**: [@deepseeko](https://www.instagram.com/deepseeko)
💬 **Discord**: @deepseeko

---

## 📌 Usage

### 💵 Wallet & Transactions
- `/c7` – View your 7YAS balance and stats.
- `/convertc` – Convert 7YAS to ProBot credits.
- `/convert7` – Get conversion instructions.
- `/buy` – Purchase items with 7YAS.
- `/auction` – Start an auction.
- `/value7` – Check the value of 7YAS in ProBot credits.
- `/daily7` – Claim your daily reward.

---

## 🔑 Environment Variables

| Variable | Description |
|----------|-------------|
| `BANK_JSON_FILE` | Path to the bank data file |
| `BANK_WALLET_ID` | Bank wallet ID |
| `YOUR_SERVER_ID` | Discord server ID |
| `LOG_WIN_WEBHOOK` | Webhook for logging wins |
| `SEND7_WEBHOOK` | Webhook for 7YAS transactions |
| `BUY_WEBHOOK` | Webhook for purchases |
| `AUCTION_WEBHOOK` | Webhook for auctions |
| `WALLET_WEBHOOK` | Webhook for wallet notifications |
| `ID_CASINO` | Casino ID |
| `LOG_CHANNEL_ID` | Log channel ID |
| `USER_TOKEN` | Bot BANK TOKEN |
| `BANK_TOKEN` | USER_TOKEN |
| `TOKEN` | USER_TOKEN |
```
USER_TOKEN = BANK_TOKEB = TOKEN
The variable you need to set in (`USER_TOKEN`) is the token of the account you want to use as your bank is crucial because this account will handle converting ProBot credits when a user wants to buy 7YAS coins. Why? Focus with me: You have a bot, but a bot cannot directly interact with another bot!

So? This means your bot cannot have a wallet in ProBot! Aha! Now, to make the process fully automatic without our manual intervention, we need to create a bank account. This account will be used to store, send, and receive credits.

Now, think about this idea:

When our bank account tries to transfer, say, 1000 credits to a user, a CAPTCHA will appear! Hahaha, don’t worry! With Yassine, there’s always a solution! My code ensures that when a CAPTCHA appears, it is sent to the user so they can solve it!

How? Well, the code is right in front of you—learn from it!

-
```
---

## 🤖 How the Bank System Works

Since bots **cannot interact directly with other bots**, the system requires a **bank account** to store and transfer credits.

### 🔄 Automatic Transactions with CAPTCHA Handling

- When a user converts **ProBot credits** to **7YAS**, a **CAPTCHA** is triggered.
- The bot **forwards** the CAPTCHA to the user for verification.
- Once verified, the transaction **automatically completes**.

---

## 📜 License

This project is licensed under the **GNU Affero General Public License v3.0**.
See the [LICENSE](LICENSE) file for details.
```
